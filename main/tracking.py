"""Live vehicle tracking: GPS ingest API, polling feed, and map/tracker pages.

Data flow
---------
    GPS source (phone page / hardware / simulate_fleet command)
        --POST /live-map/api/ingest/  (Bearer token)-->  VehiclePosition rows
    Live map page
        --GET  /live-map/api/positions/?since=<cursor>-->  new fixes since cursor

The cursor is the auto-increment ``VehiclePosition.id``: the client remembers the
highest id it has seen and asks only for newer rows, so each poll is a single
indexed range scan no matter how much history is stored. When nothing is new
the server answers ``304 Not Modified`` via ETag.
"""
import json
import math
from datetime import datetime, timedelta, timezone as dt_timezone

from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseNotAllowed, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Vehicle, VehiclePosition, VehicleTracker

# A unit with no fix for this long is shown as offline.
OFFLINE_AFTER_SECONDS = 120
# Speeds below this are treated as stationary (GPS jitter).
MOVING_THRESHOLD_KMH = 3
# How much history the first poll returns, to draw breadcrumb trails.
SNAPSHOT_TRAIL_MINUTES = 30
SNAPSHOT_TRAIL_MAX_POINTS = 300
# Upper bounds that keep requests cheap.
MAX_POINTS_PER_POLL = 2000
MAX_POINTS_PER_INGEST = 500
# Reject fixes claiming to be from the future (bad device clock).
MAX_CLOCK_SKEW = timedelta(minutes=5)

# Approximate coordinates (lat, lng) for route start/finish names, used to draw
# the planned route line and by the simulate_fleet command.
PLACES = {
    'maseru': (-29.3151, 27.4869),
    'johannesburg': (-26.2041, 28.0473),
    'jozi': (-26.2041, 28.0473),
    'jhb': (-26.2041, 28.0473),
    'pretoria': (-25.7479, 28.2293),
    'tshwane': (-25.7479, 28.2293),
    'bloemfontein': (-29.0852, 26.1596),
    'durban': (-29.8587, 31.0218),
    'harrismith': (-28.2728, 29.1294),
    'cape town': (-33.9249, 18.4241),
    'gqeberha': (-33.9608, 25.6022),
    'port elizabeth': (-33.9608, 25.6022),
    'east london': (-33.0153, 27.9116),
    'polokwane': (-23.9045, 29.4689),
    'mbombela': (-25.4753, 30.9694),
    'nelspruit': (-25.4753, 30.9694),
    'kimberley': (-28.7282, 24.7499),
    'pietermaritzburg': (-29.6006, 30.3794),
    'ladysmith': (-28.5539, 29.7808),
    'richards bay': (-28.7807, 32.0383),
    'rustenburg': (-25.6672, 27.2424),
    'welkom': (-27.9774, 26.7351),
    'kroonstad': (-27.6503, 27.2349),
    'ficksburg': (-28.8742, 27.8786),
    'bethlehem': (-28.2308, 28.3071),
    'witbank': (-25.8713, 29.2332),
    'emalahleni': (-25.8713, 29.2332),
    'secunda': (-26.5504, 29.1781),
    'vereeniging': (-26.6731, 27.9261),
}


def lookup_place(name):
    """Return (lat, lng) for a place name, or None if it isn't known."""
    if not name:
        return None
    key = name.strip().lower()
    if key in PLACES:
        return PLACES[key]
    for place, coords in PLACES.items():
        if place in key or key in place:
            return coords
    return None


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def bearing_deg(lat1, lng1, lat2, lng2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lng2 - lng1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def _epoch_ms(dt):
    return int(dt.timestamp() * 1000)


# ---------------------------------------------------------------------------
# Vehicle metadata (driver / route) for the map
# ---------------------------------------------------------------------------

def vehicle_meta(vehicle_ids=None, request=None):
    """Return {vehicle_id: {...}} with display info for the given vehicles."""
    from driverAssignment.models import (
        CompleteAssignment, DriverVehicleAssignment, VehicleRouteAssignment,
    )

    vehicles = Vehicle.objects.select_related('tracker')
    if vehicle_ids is not None:
        vehicles = vehicles.filter(id__in=vehicle_ids)
    vehicles = list(vehicles)
    ids = [v.id for v in vehicles]

    complete, dva_map, vra_map = {}, {}, {}
    for a in (CompleteAssignment.objects.filter(vehicle_id__in=ids, is_active=True)
              .select_related('driver__user', 'route')
              .order_by('route__is_active', 'created_date')):
        complete[a.vehicle_id] = a  # later rows win: active route, newest
    for a in (VehicleRouteAssignment.objects.filter(vehicle_id__in=ids, is_active=True)
              .select_related('route').order_by('route__is_active')):
        vra_map[a.vehicle_id] = a
    for a in (DriverVehicleAssignment.objects.filter(vehicle_id__in=ids, is_active=True)
              .select_related('driver__user')):
        dva_map.setdefault(a.vehicle_id, a)

    show_links = bool(request and request.user.is_authenticated)
    out = {}
    for v in vehicles:
        route, driver = None, None
        if v.id in complete:
            route, driver = complete[v.id].route, complete[v.id].driver
        else:
            route = vra_map[v.id].route if v.id in vra_map else None
            driver = dva_map[v.id].driver if v.id in dva_map else None

        tracker = getattr(v, 'tracker', None)
        tracker_url = None
        if show_links and tracker and tracker.is_enabled:
            tracker_url = request.build_absolute_uri(
                reverse('main:live_map_tracker', args=[tracker.token]))

        out[v.id] = {
            'id': v.id,
            'registration': v.vehicle_registration_no,
            'make': v.vehicle_make,
            'active': v.is_active,
            'driver': (driver.user.get_full_name() or driver.user.username) if driver else 'Unassigned',
            'route': route.route_name if route else None,
            'start_name': route.start if route else None,
            'finish_name': route.finish if route else None,
            'start': lookup_place(route.start) if route else None,
            'finish': lookup_place(route.finish) if route else None,
            'has_tracker': bool(tracker and tracker.is_enabled),
            'tracker_url': tracker_url,
            'vehicle_url': reverse('main:vehicle_detail', args=[v.id]),
        }
    return out


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def live_map_view(request):
    meta = vehicle_meta(request=request)
    return render(request, 'main/live_map.html', {
        'title': 'Live Map',
        'vehicles': list(meta.values()),
        'config': {
            'positionsUrl': reverse('main:live_map_positions'),
            'enableTrackerUrl': reverse('main:live_map_enable_tracker', args=[0]),
            'offlineAfterSeconds': OFFLINE_AFTER_SECONDS,
            'movingThresholdKmh': MOVING_THRESHOLD_KMH,
            'canManage': request.user.is_authenticated,
        },
    })


def tracker_page_view(request, token):
    """Mobile page that turns a phone into the vehicle's GPS tracker."""
    tracker = get_object_or_404(VehicleTracker.objects.select_related('vehicle'),
                                token=token, is_enabled=True)
    meta = vehicle_meta([tracker.vehicle_id])[tracker.vehicle_id]
    # Route for "Simulate drive": the vehicle's assigned route if its places are
    # known, otherwise a default corridor so the demo always works.
    if meta['start'] and meta['finish'] and meta['start'] != meta['finish']:
        sim_route = {'start': meta['start'], 'finish': meta['finish'],
                     'start_name': meta['start_name'], 'finish_name': meta['finish_name']}
    else:
        sim_route = {'start': PLACES['johannesburg'], 'finish': PLACES['durban'],
                     'start_name': 'Johannesburg', 'finish_name': 'Durban'}
    return render(request, 'main/live_map_tracker.html', {
        'vehicle': tracker.vehicle,
        'token': tracker.token,
        'ingest_url': reverse('main:live_map_ingest'),
        'sim_route': sim_route,
    })


@require_POST
def enable_tracker_view(request, vehicle_id):
    """Create (or re-enable) a tracker for a vehicle and return its phone link."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    tracker, _ = VehicleTracker.objects.get_or_create(vehicle=vehicle)
    if not tracker.is_enabled:
        tracker.is_enabled = True
        tracker.save(update_fields=['is_enabled'])
    return JsonResponse({
        'vehicle': vehicle.id,
        'tracker_url': request.build_absolute_uri(reverse('main:live_map_tracker', args=[tracker.token])),
    })


# ---------------------------------------------------------------------------
# Polling feed
# ---------------------------------------------------------------------------

def _serialize(p):
    return {
        'id': p.id,
        'v': p.vehicle_id,
        'lat': round(p.latitude, 6),
        'lng': round(p.longitude, 6),
        'speed': None if p.speed_kmh is None else round(p.speed_kmh, 1),
        'heading': None if p.heading is None else round(p.heading),
        'acc': None if p.accuracy_m is None else round(p.accuracy_m),
        't': _epoch_ms(p.recorded_at),
        'r': _epoch_ms(p.received_at),
    }


@require_GET
def positions_api(request):
    """Return GPS fixes newer than ``since`` (a position id).

    ``since`` omitted or 0 -> snapshot: the last few minutes of trail for every
    vehicle plus the last known fix of vehicles that have gone quiet.
    ``since`` > 0 -> incremental: every fix with id > since, oldest first.
    """
    try:
        since = max(0, int(request.GET.get('since', 0)))
    except ValueError:
        return JsonResponse({'error': 'since must be an integer'}, status=400)

    latest_id = VehiclePosition.objects.aggregate(m=Max('id'))['m'] or 0
    etag = f'"pos-{latest_id}"'
    now = timezone.now()

    if since and since >= latest_id and request.headers.get('If-None-Match') == etag:
        resp = HttpResponse(status=304)
        resp['ETag'] = etag
        resp['Cache-Control'] = 'no-cache'
        return resp

    has_more = False
    if since:
        rows = list(VehiclePosition.objects.filter(id__gt=since).order_by('id')[:MAX_POINTS_PER_POLL + 1])
        if len(rows) > MAX_POINTS_PER_POLL:
            rows, has_more = rows[:MAX_POINTS_PER_POLL], True
    else:
        cutoff = now - timedelta(minutes=SNAPSHOT_TRAIL_MINUTES)
        recent = {}
        for p in VehiclePosition.objects.filter(received_at__gte=cutoff).order_by('-id').iterator():
            bucket = recent.setdefault(p.vehicle_id, [])
            if len(bucket) < SNAPSHOT_TRAIL_MAX_POINTS:
                bucket.append(p)
        # Last known fix for vehicles silent longer than the trail window.
        stale_ids = (VehiclePosition.objects.exclude(vehicle_id__in=recent.keys())
                     .values('vehicle_id').annotate(m=Max('id')).values_list('m', flat=True))
        rows = [p for bucket in recent.values() for p in bucket]
        rows += list(VehiclePosition.objects.filter(id__in=list(stale_ids)))
        rows.sort(key=lambda p: p.id)

    cursor = rows[-1].id if rows else (since or latest_id)
    vehicle_ids = {p.vehicle_id for p in rows}

    resp = JsonResponse({
        'cursor': cursor,
        'has_more': has_more,
        'server_time': _epoch_ms(now),
        'points': [_serialize(p) for p in rows],
        # Display info for vehicles in this batch, so units added after the
        # page loaded still appear without a refresh.
        'vehicles': vehicle_meta(vehicle_ids, request) if vehicle_ids else {},
    })
    if not has_more:
        resp['ETag'] = etag
    resp['Cache-Control'] = 'no-cache'
    return resp


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

class IngestError(ValueError):
    pass


def _parse_time(value, now):
    if value in (None, ''):
        return now
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Epoch seconds or milliseconds.
        seconds = value / 1000 if value > 1e11 else value
        dt = datetime.fromtimestamp(seconds, tz=dt_timezone.utc)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise IngestError(f'invalid recorded_at: {value!r}')
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, dt_timezone.utc)
    else:
        raise IngestError('recorded_at must be ISO-8601 or epoch time')
    if dt > now + MAX_CLOCK_SKEW:
        raise IngestError('recorded_at is in the future')
    return dt


def _number(raw, name, lo=None, hi=None, required=False):
    if raw is None:
        if required:
            raise IngestError(f'{name} is required')
        return None
    if isinstance(raw, bool):
        raise IngestError(f'{name} must be a number')
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise IngestError(f'{name} must be a number')
    if not math.isfinite(val) or (lo is not None and val < lo) or (hi is not None and val > hi):
        raise IngestError(f'{name} out of range')
    return val


def _parse_point(raw, now):
    if not isinstance(raw, dict):
        raise IngestError('each point must be an object')
    return {
        'latitude': _number(raw.get('lat', raw.get('latitude')), 'lat', -90, 90, required=True),
        'longitude': _number(raw.get('lng', raw.get('longitude')), 'lng', -180, 180, required=True),
        'speed_kmh': _number(raw.get('speed_kmh'), 'speed_kmh', 0, 400),
        'heading': _number(raw.get('heading'), 'heading', 0, 360),
        'accuracy_m': _number(raw.get('accuracy_m'), 'accuracy_m', 0, 100000),
        'recorded_at': _parse_time(raw.get('recorded_at'), now),
    }


def _fill_motion(points, previous):
    """Derive speed/heading from consecutive fixes when the device omits them
    (browser geolocation often reports null speed and heading)."""
    prev = previous
    for p in points:
        if prev is not None:
            dt = (p['recorded_at'] - prev['recorded_at']).total_seconds()
            dist = haversine_km(prev['latitude'], prev['longitude'], p['latitude'], p['longitude'])
            if p['speed_kmh'] is None and dt > 0:
                p['speed_kmh'] = min(400.0, dist / (dt / 3600))
            if p['heading'] is None and dist > 0.005:  # ignore sub-5 m jitter
                p['heading'] = bearing_deg(prev['latitude'], prev['longitude'], p['latitude'], p['longitude'])
        prev = p


@csrf_exempt  # Token-authenticated machine endpoint; no browser session involved.
def ingest_api(request):
    """Accept GPS fixes from a tracker.

    Auth:  ``Authorization: Bearer <tracker token>``
    Body:  ``{"lat": .., "lng": .., "speed_kmh"?, "heading"?, "accuracy_m"?, "recorded_at"?}``
           or ``{"points": [ ...up to 500 of the above... ]}``
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    auth = request.headers.get('Authorization', '')
    token = auth[7:].strip() if auth.lower().startswith('bearer ') else ''
    tracker = (VehicleTracker.objects.select_related('vehicle')
               .filter(token=token).first() if token else None)
    if tracker is None:
        return JsonResponse({'error': 'invalid or missing tracker token'}, status=401)
    if not tracker.is_enabled:
        return JsonResponse({'error': 'tracker disabled'}, status=403)

    try:
        body = json.loads(request.body or b'null')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'body must be JSON'}, status=400)
    raw_points = body.get('points') if isinstance(body, dict) and 'points' in body else [body]
    if not isinstance(raw_points, list) or not raw_points:
        return JsonResponse({'error': 'no points supplied'}, status=400)
    if len(raw_points) > MAX_POINTS_PER_INGEST:
        return JsonResponse({'error': f'at most {MAX_POINTS_PER_INGEST} points per request'}, status=413)

    now = timezone.now()
    try:
        points = sorted((_parse_point(p, now) for p in raw_points), key=lambda p: p['recorded_at'])
    except IngestError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    last = (VehiclePosition.objects.filter(vehicle=tracker.vehicle)
            .order_by('-id').values('latitude', 'longitude', 'recorded_at').first())
    _fill_motion(points, last)

    with transaction.atomic():
        created = VehiclePosition.objects.bulk_create(
            [VehiclePosition(vehicle=tracker.vehicle, **p) for p in points])
        VehicleTracker.objects.filter(pk=tracker.pk).update(last_seen_at=now)

    return JsonResponse({'accepted': len(created)}, status=201)
