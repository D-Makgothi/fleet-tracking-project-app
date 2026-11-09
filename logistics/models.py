from django.db import models

# Manage Delivery Model

class ManageDeliveryModel(models.Model):

    client = models.CharField(max_length=60)
    load_dateline = models.CharField(max_length=60)

    ROUTE_CHOICES = [
        ('Route 1', 'Route 1'),
        ('Route 2', 'Route 2'),
        ('Route 3', 'Route 3'),
        ('Route 4', 'Route 4'),
    ]

    route_taken = models.CharField(max_length=60, choices=ROUTE_CHOICES, default='Route 1')
    vehicle_registration = models.CharField(max_length=60)

    vehicle_driver = models.CharField(max_length=60)
    load_quantity = models.IntegerField()
    order_number = models.CharField(max_length=60)

