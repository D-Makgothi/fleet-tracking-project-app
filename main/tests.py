import json
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Vehicle, VehiclePosition, VehicleTracker


class LiveTrackingTests(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            vehicle_make='Scania', vehicle_registration_no='TEST-001',
            vehicle_registration_expiry=date.today() + timedelta(days=365))
        self.tracker = VehicleTracker.objects.create(vehicle=self.vehicle)
        self.ingest_url = reverse('main:live_map_ingest')
        self.positions_url = reverse('main:live_map_positions')

    def ingest(self, body, token=None):
        return self.client.post(
            self.ingest_url, data=json.dumps(body), content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token or self.tracker.token}')

    # --- ingest -------------------------------------------------------------

    def test_ingest_requires_valid_token(self):
        self.assertEqual(self.ingest({'lat': -26.2, 'lng': 28.0}, token='nope').status_code, 401)
        resp = self.client.post(self.ingest_url, data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(VehiclePosition.objects.exists())

    def test_disabled_tracker_is_rejected(self):
        self.tracker.is_enabled = False
        self.tracker.save()
        self.assertEqual(self.ingest({'lat': -26.2, 'lng': 28.0}).status_code, 403)

    def test_ingest_single_and_batch(self):
        self.assertEqual(self.ingest({'lat': -26.2, 'lng': 28.0, 'speed_kmh': 80}).status_code, 201)
        resp = self.ingest({'points': [{'lat': -26.21, 'lng': 28.01}, {'lat': -26.22, 'lng': 28.02}]})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['accepted'], 2)
        self.assertEqual(VehiclePosition.objects.filter(vehicle=self.vehicle).count(), 3)
        self.tracker.refresh_from_db()
        self.assertIsNotNone(self.tracker.last_seen_at)

    def test_ingest_validation(self):
        for bad in ({'lat': 91, 'lng': 0}, {'lat': 0}, {'lat': 'x', 'lng': 0},
                    {'lat': 0, 'lng': 0, 'speed_kmh': -5}, {'points': []},
                    {'lat': 0, 'lng': 0, 'recorded_at': (timezone.now() + timedelta(hours=1)).isoformat()}):
            self.assertEqual(self.ingest(bad).status_code, 400, bad)
        self.assertFalse(VehiclePosition.objects.exists())

    def test_ingest_rejects_get(self):
        self.assertEqual(self.client.get(self.ingest_url).status_code, 405)

    def test_speed_and_heading_derived_when_missing(self):
        t0 = timezone.now() - timedelta(seconds=60)
        self.ingest({'points': [
            {'lat': -26.0, 'lng': 28.0, 'recorded_at': t0.isoformat()},
            # ~1.11 km due north, 60 s later -> ~67 km/h, heading ~0
            {'lat': -25.99, 'lng': 28.0, 'recorded_at': (t0 + timedelta(seconds=60)).isoformat()},
        ]})
        last = VehiclePosition.objects.latest('id')
        self.assertAlmostEqual(last.speed_kmh, 66.7, delta=1)
        self.assertLess(min(last.heading, 360 - last.heading), 1)

    # --- polling feed -------------------------------------------------------

    def test_snapshot_then_incremental_cursor(self):
        self.ingest({'lat': -26.2, 'lng': 28.0})
        snap = self.client.get(self.positions_url).json()
        self.assertEqual(len(snap['points']), 1)
        self.assertIn(str(self.vehicle.id), snap['vehicles'])
        cursor = snap['cursor']

        empty = self.client.get(self.positions_url, {'since': cursor}).json()
        self.assertEqual(empty['points'], [])
        self.assertEqual(empty['cursor'], cursor)

        self.ingest({'lat': -26.3, 'lng': 28.1})
        new = self.client.get(self.positions_url, {'since': cursor}).json()
        self.assertEqual([p['lat'] for p in new['points']], [-26.3])
        self.assertGreater(new['cursor'], cursor)

    def test_not_modified_when_nothing_new(self):
        self.ingest({'lat': -26.2, 'lng': 28.0})
        first = self.client.get(self.positions_url)
        cursor, etag = first.json()['cursor'], first['ETag']
        resp = self.client.get(self.positions_url, {'since': cursor}, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(resp.status_code, 304)

        self.ingest({'lat': -26.3, 'lng': 28.1})
        resp = self.client.get(self.positions_url, {'since': cursor}, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(resp.status_code, 200)

    def test_snapshot_includes_last_known_fix_of_quiet_vehicle(self):
        self.ingest({'lat': -26.2, 'lng': 28.0})
        VehiclePosition.objects.update(received_at=timezone.now() - timedelta(days=2))
        snap = self.client.get(self.positions_url).json()
        self.assertEqual(len(snap['points']), 1)

    def test_bad_cursor(self):
        self.assertEqual(self.client.get(self.positions_url, {'since': 'abc'}).status_code, 400)

    # --- pages --------------------------------------------------------------

    def test_pages_render(self):
        self.assertEqual(self.client.get(reverse('main:live_map')).status_code, 200)
        resp = self.client.get(reverse('main:live_map_tracker', args=[self.tracker.token]))
        self.assertContains(resp, 'TEST-001')
        self.assertEqual(self.client.get(reverse('main:live_map_tracker', args=['bad'])).status_code, 404)
