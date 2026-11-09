"""Drive fake GPS units through the real ingest API.

Each vehicle with a recognisable route gets a tracker (created if missing). The
command then moves a virtual truck along the road between the route's start and
finish and POSTs its position to /live-map/api/ingest/ over HTTP, exactly as a
hardware unit or the phone tracker page would. Run it next to `runserver`:

    python manage.py simulate_fleet
    python manage.py simulate_fleet --speedup 20 --interval 2 --url http://127.0.0.1:8000
"""
import random
import signal
import time
from datetime import datetime, timezone

import requests
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from main.models import Vehicle, VehicleTracker
from main.tracking import bearing_deg, haversine_km, lookup_place, vehicle_meta


def road_path(a, b):
    """Road geometry from OSRM, or a straight line if it can't be reached."""
    try:
        r = requests.get(
            f'https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}',
            params={'overview': 'full', 'geometries': 'geojson'}, timeout=8)
        r.raise_for_status()
        pts = [(c[1], c[0]) for c in r.json()['routes'][0]['geometry']['coordinates']]
        if len(pts) >= 2:
            return pts, 'road'
    except (requests.RequestException, KeyError, IndexError, ValueError):
        pass
    return [a, b], 'straight'


class Truck:
    DWELL_SECONDS = 15 * 60  # loading / offloading time (simulated)

    def __init__(self, meta, token, path):
        self.meta, self.token, self.path = meta, token, path
        self.cum = [0.0]
        for p, q in zip(path, path[1:]):
            self.cum.append(self.cum[-1] + haversine_km(*p, *q))
        self.km = self.cum[-1] or 0.001
        self.cruise = random.uniform(72, 92)
        self.dist = random.uniform(0, self.km)     # start somewhere along the route
        self.direction = random.choice([1, -1])
        self.dwell_left = 0.0

    def point_at(self, d):
        d = max(0.0, min(self.km, d))
        lo, hi = 0, len(self.cum) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.cum[mid] <= d:
                lo = mid
            else:
                hi = mid
        seg = (self.cum[hi] - self.cum[lo]) or 1
        t = (d - self.cum[lo]) / seg
        (a0, a1), (b0, b1) = self.path[lo], self.path[hi]
        return a0 + (b0 - a0) * t, a1 + (b1 - a1) * t

    def step(self, sim_seconds):
        """Advance the truck and return the fix to report."""
        if self.dwell_left > 0:
            self.dwell_left -= sim_seconds
            lat, lng = self.point_at(self.dist)
            return {'lat': lat, 'lng': lng, 'speed_kmh': 0}

        edge = min(self.dist, self.km - self.dist)
        ramp = min(1.0, 0.35 + edge / 3)                       # slow near depots
        speed = max(5.0, (self.cruise + random.uniform(-6, 6)) * ramp)
        self.dist += self.direction * speed * sim_seconds / 3600
        if self.dist >= self.km or self.dist <= 0:
            self.dist = min(self.km, max(0.0, self.dist))
            self.direction *= -1
            self.dwell_left = self.DWELL_SECONDS
            speed = 0.0

        lat, lng = self.point_at(self.dist)
        ahead = self.point_at(self.dist + self.direction * 0.3)
        heading = bearing_deg(lat, lng, *ahead) if speed else None
        return {'lat': lat, 'lng': lng, 'speed_kmh': round(speed, 1), 'heading': heading}


class Command(BaseCommand):
    help = 'Simulate GPS trackers for vehicles with known routes by POSTing to the ingest API.'

    def add_arguments(self, parser):
        parser.add_argument('--url', default='http://127.0.0.1:8000', help='Base URL of the running server')
        parser.add_argument('--interval', type=float, default=2.0, help='Real seconds between reports')
        parser.add_argument('--speedup', type=float, default=10.0, help='Simulated seconds per real second')
        parser.add_argument('--vehicles', nargs='*', help='Only these registrations')
        parser.add_argument('--drop', type=float, default=0.0,
                            help='Fraction of reports to skip, to exercise offline detection (0-1)')

    def handle(self, *opts, **o):
        ingest = o['url'].rstrip('/') + reverse('main:live_map_ingest')
        vehicles = Vehicle.objects.filter(is_active=True)
        if o['vehicles']:
            vehicles = vehicles.filter(vehicle_registration_no__in=o['vehicles'])

        meta = vehicle_meta([v.id for v in vehicles])
        trucks = []
        for v in vehicles:
            m = meta[v.id]
            if not m['start'] or not m['finish'] or m['start'] == m['finish']:
                self.stdout.write(self.style.WARNING(
                    f"  skip {v.vehicle_registration_no}: no route with recognised start/finish"))
                continue
            tracker, _ = VehicleTracker.objects.get_or_create(vehicle=v)
            if not tracker.is_enabled:
                tracker.is_enabled = True
                tracker.save(update_fields=['is_enabled'])
            path, kind = road_path(m['start'], m['finish'])
            truck = Truck(m, tracker.token, path)
            trucks.append(truck)
            self.stdout.write(f"  {v.vehicle_registration_no}: {m['start_name']} -> {m['finish_name']} "
                              f"({truck.km:.0f} km, {kind})")

        if not trucks:
            raise CommandError('No active vehicles have a route whose start/finish places are recognised. '
                               'Assign a route (e.g. Johannesburg -> Durban) to a vehicle first.')

        self.stdout.write(self.style.SUCCESS(
            f'Simulating {len(trucks)} unit(s) -> {ingest} every {o["interval"]}s at {o["speedup"]}x. Ctrl+C to stop.'))

        running = True

        def _stop(*_):
            nonlocal running
            running = False
        signal.signal(signal.SIGINT, _stop)

        session = requests.Session()
        sim_step = o['interval'] * o['speedup']
        sent = errors = 0
        while running:
            tick = time.monotonic()
            now = datetime.now(timezone.utc).isoformat()
            for t in trucks:
                fix = t.step(sim_step)
                if o['drop'] and random.random() < o['drop']:
                    continue
                fix['recorded_at'] = now
                fix['accuracy_m'] = round(random.uniform(4, 15), 1)
                try:
                    r = session.post(ingest, json=fix, timeout=5,
                                     headers={'Authorization': f'Bearer {t.token}'})
                    if r.status_code == 201:
                        sent += 1
                    else:
                        errors += 1
                        self.stderr.write(f"{t.meta['registration']}: HTTP {r.status_code} {r.text[:120]}")
                except requests.RequestException as exc:
                    errors += 1
                    self.stderr.write(f'POST failed ({exc.__class__.__name__}); is the server running at {o["url"]}?')
                    break
            self.stdout.write(f'\rsent {sent}  errors {errors}', ending='')
            self.stdout.flush()
            time.sleep(max(0.0, o['interval'] - (time.monotonic() - tick)))

        self.stdout.write('\nStopped.')
