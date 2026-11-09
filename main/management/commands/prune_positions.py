"""Delete old GPS fixes so the positions table doesn't grow without bound.

    python manage.py prune_positions --days 7

The latest fix per vehicle is always kept so the map can show a last-known position.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from main.models import VehiclePosition


class Command(BaseCommand):
    help = 'Delete GPS positions older than N days (keeps each vehicle\'s latest fix).'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7)

    def handle(self, *args, **opts):
        cutoff = timezone.now() - timedelta(days=opts['days'])
        keep = VehiclePosition.objects.values('vehicle_id').annotate(m=Max('id')).values_list('m', flat=True)
        deleted, _ = (VehiclePosition.objects.filter(received_at__lt=cutoff)
                      .exclude(id__in=list(keep)).delete())
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} position(s) older than {opts["days"]} day(s).'))
