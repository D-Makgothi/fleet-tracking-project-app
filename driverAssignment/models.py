from django.db import models
from register_login.models import RegistryModel  # Import from the other app
from main.models import Route, Vehicle  # Import Route and Vehicle from main app

class RouteManager(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    route_name = models.CharField(max_length=50)
    start = models.CharField(max_length=50)
    finish = models.CharField(max_length=100)
    drivers = models.ManyToManyField(RegistryModel, blank=True, related_name='assigned_routes')  # Many-to-many with drivers

    def __str__(self):
        return f"{self.route_name} {self.start} {self.finish}"

# New model to integrate with main app routes
class DriverRouteAssignment(models.Model):
    """Links drivers to routes from the main app's route management"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='driver_assignments')
    driver = models.ForeignKey(RegistryModel, on_delete=models.CASCADE, related_name='route_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('route', 'driver')  # Prevent duplicate assignments
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.driver.user.username} assigned to {self.route.route_name}"


# Driver to Vehicle Assignment
class DriverVehicleAssignment(models.Model):
    """Assigns a driver to a specific vehicle"""
    driver = models.ForeignKey(RegistryModel, on_delete=models.CASCADE, related_name='vehicle_assignments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='driver_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('driver', 'vehicle')  # One driver per vehicle at a time
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.driver.user.username} assigned to {self.vehicle.vehicle_registration_no}"


# Vehicle to Route Assignment
class VehicleRouteAssignment(models.Model):
    """Assigns a vehicle (with driver) to a specific route"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='route_assignments')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='vehicle_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('vehicle', 'route')  # Prevent duplicate vehicle-route assignments
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.vehicle.vehicle_registration_no} assigned to {self.route.route_name}"
    
    @property
    def assigned_driver(self):
        """Get the driver currently assigned to this vehicle"""
        driver_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=self.vehicle, 
            is_active=True
        ).first()
        return driver_assignment.driver if driver_assignment else None


# Complete Assignment View (Driver → Vehicle → Route)
class CompleteAssignment(models.Model):
    """A read-only view of complete assignments showing driver → vehicle → route chain"""
    SHIFT_CHOICES = [
        ('D/S', 'Day Shift'),
        ('N/S', 'Night Shift'),
    ]
    
    driver = models.ForeignKey(RegistryModel, on_delete=models.CASCADE, related_name='complete_assignments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='complete_assignments')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='complete_assignments')
    shift_type = models.CharField(max_length=3, choices=SHIFT_CHOICES, default='D/S', verbose_name='Shift Type')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('driver', 'vehicle', 'route')
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.driver.user.username} → {self.vehicle.vehicle_registration_no} → {self.route.route_name} ({self.shift_type})"
    
    @classmethod
    def create_complete_assignment(cls, driver, vehicle, route, shift_type='D/S', notes=None):
        """
        Helper method to create a complete assignment by setting up all necessary relationships
        """
        # Create or update driver-vehicle assignment
        driver_vehicle, created = DriverVehicleAssignment.objects.get_or_create(
            driver=driver,
            vehicle=vehicle,
            defaults={'is_active': True, 'notes': notes}
        )
        if not created:
            driver_vehicle.is_active = True
            driver_vehicle.save()
        
        # Create or update vehicle-route assignment
        vehicle_route, created = VehicleRouteAssignment.objects.get_or_create(
            vehicle=vehicle,
            route=route,
            defaults={'is_active': True, 'notes': notes}
        )
        if not created:
            vehicle_route.is_active = True
            vehicle_route.save()
        
        # Create the complete assignment record
        complete_assignment, created = cls.objects.get_or_create(
            driver=driver,
            vehicle=vehicle,
            route=route,
            defaults={'is_active': True, 'shift_type': shift_type, 'notes': notes}
        )
        if not created:
            complete_assignment.is_active = True
            complete_assignment.shift_type = shift_type
            complete_assignment.notes = notes
            complete_assignment.save()
        
        return complete_assignment
