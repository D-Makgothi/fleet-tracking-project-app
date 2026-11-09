from django.core.management.base import BaseCommand
from main.models import FuelRateModel, PlannedRevenueModel, TransportRateModel_1, TransportRateModel_2, TransportRateModel_3, TransportRateModel_4

class Command(BaseCommand):
    help = 'Create default rate values'

    def handle(self, *args, **kwargs):
        FuelRateModel.objects.get_or_create(id=1, defaults={'fuel_rate': 1.00, 'name': 'Default Fuel Rate'})
        PlannedRevenueModel.objects.get_or_create(id=1, defaults={'planned_revenue': 1.00, 'name': 'Planned Revenue'})
        TransportRateModel_1.objects.get_or_create(id=1, defaults={'transport_rate_1': 1.00, 'name': 'Transport Rate 1'})
        TransportRateModel_2.objects.get_or_create(id=1, defaults={'transport_rate_2': 1.00, 'name': 'Transport Rate 2'})
        TransportRateModel_3.objects.get_or_create(id=1, defaults={'transport_rate_3': 1.00, 'name': 'Transport Rate 3'})
        TransportRateModel_4.objects.get_or_create(id=1, defaults={'transport_rate_4': 1.00, 'name': 'Transport Rate 4'})
        
        self.stdout.write(self.style.SUCCESS('Successfully created default rates'))
