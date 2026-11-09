from django.db import models
from django.db.models import Avg
from decimal import Decimal
from register_login.models import RegistryModel

# Cost Model Report Section

#Fuel Rate Model
class FuelRateModel(models.Model):
    fuel_rate = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=60, default="Fuel Rate")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Set created_at if it's a new record
        if not self.pk and not self.created_at:
            from django.utils import timezone
            self.created_at = timezone.now()
        
        # If this rate is being set as active, deactivate all others
        if self.is_active:
            FuelRateModel.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_rate(cls):
        """Get the currently active fuel rate"""
        return cls.objects.filter(is_active=True).first()
    
    class Meta:
        ordering = ['-created_at']


#Daily Report Model for Cost
class DailyReportModel_Cost(models.Model):
    driver = models.ForeignKey(RegistryModel, on_delete=models.CASCADE, null=True, blank=True)
    fleet_no = models.CharField(max_length=60)
    fuel_requested = models.IntegerField()
    date= models.DateField(null=True, blank=True)
    slip_no = models.CharField(max_length=60, blank=True, null=True)
    fuel_rate_set = models.ForeignKey(FuelRateModel, on_delete=models.CASCADE, null=True, blank=True)
    imported_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) #This is field that the Admin will have acess to add any miscellaneous costs at the end of the month
    predicted_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Running cumulative predicted cost")
    
     #Fuel Cost method
    def fuel_cost(self):
        if self.fuel_rate_set:
            return Decimal(str(self.fuel_rate_set.fuel_rate)) * Decimal(str(self.fuel_requested))
        else:
            # Use active fuel rate if available, otherwise return 0
            active_rate = FuelRateModel.get_active_rate()
            if active_rate:
                return Decimal(str(active_rate.fuel_rate)) * Decimal(str(self.fuel_requested))
            return Decimal('0.00')
    
    #Total Cost method (fuel + imported costs)
    def total_cost(self):
        fuel_cost = self.fuel_cost()
        imported_cost = Decimal(str(self.imported_costs)) if self.imported_costs else Decimal('0.00')
        return fuel_cost + imported_cost
    
    def save(self, *args, **kwargs):
        """Override save to calculate running predicted cost"""
        # Calculate current total cost
        current_total_cost = self.total_cost()
        
        # Get previous cost entry for this driver/fleet combination
        previous_entry = None
        if self.driver and self.fleet_no:
            previous_entry = DailyReportModel_Cost.objects.filter(
                driver=self.driver,
                fleet_no=self.fleet_no
            ).exclude(id=self.id).order_by('-date', '-id').first()
        
        if previous_entry and previous_entry.predicted_cost is not None:
            # For subsequent entries: 
            # New predicted cost = Previous predicted cost + Average(current total, previous total)
            previous_total_cost = previous_entry.total_cost()
            previous_predicted = Decimal(str(previous_entry.predicted_cost))
            average_cost = (current_total_cost + previous_total_cost) / Decimal('2')
            self.predicted_cost = previous_predicted + average_cost
        else:
            # For first entry: predicted cost = current total cost
            self.predicted_cost = current_total_cost
        
        # Round to 2 decimal places
        self.predicted_cost = round(self.predicted_cost, 2)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_latest_predicted_cost(cls, fleet_no=None, driver=None):
        """Get the most recent predicted cost for a driver/fleet combination"""
        query_filter = {}
        if fleet_no:
            query_filter['fleet_no'] = fleet_no
        if driver:
            query_filter['driver'] = driver
            
        latest_entry = cls.objects.filter(**query_filter).order_by('-date', '-id').first()
        if latest_entry and latest_entry.predicted_cost is not None:
            return latest_entry.predicted_cost
        return Decimal('0.00')
    
    def get_predicted_cost(self):
        """Instance method to get the stored predicted cost for this entry"""
        return self.predicted_cost or Decimal('0.00')
    
    






# Vehicle Management Section

class Vehicle(models.Model):
    vehicle_make = models.CharField(max_length=100)
    vehicle_registration_no = models.CharField(max_length=60, unique=True)
    vehicle_registration_expiry = models.DateField()
    fleetcam_link = models.URLField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.vehicle_make} - {self.vehicle_registration_no} ({status})"
    
    class Meta:
        ordering = ['vehicle_make', 'vehicle_registration_no']


#Route Management Section

class Route(models.Model):
    route_name = models.CharField(max_length=100)
    start = models.CharField(max_length=100)
    finish = models.CharField(max_length=100)
    transport_rate = models.DecimalField(max_digits=10, decimal_places=2)
    planned_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Expected revenue per load for this route")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.route_name} ({self.start} to {self.finish}) - {status}"
    
    def get_variance_per_load(self):
        """Calculate variance between transport rate and planned revenue"""
        return self.transport_rate - self.planned_revenue
    
    class Meta:
        ordering = ['route_name']


#Revenue Report Model Section


#Planned Revenue Model
class PlannedRevenueModel(models.Model):
    planned_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=60, default="Planned Revenue")
    
    def __str__(self):
        return self.name
    
 
    
    
#Transport Rate Models     
class TransportRateModel_1(models.Model):
    transport_rate_1 = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=60, default="Transport Rate 1")
    
    def __str__(self):
        return self.name
    
class TransportRateModel_2(models.Model):
    transport_rate_2 = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=60, default="Transport Rate 2")
    
    def __str__(self):
        return self.name
    
class TransportRateModel_3(models.Model):
    transport_rate_3 = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=60, default="Transport Rate 3")
    
    def __str__(self):
        return self.name
    
class TransportRateModel_4(models.Model):
    transport_rate_4 = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=60, default="Transport Rate 4")
    
    def __str__(self):
        return self.name
    
    
    
#Daily Report Model For Revenue   
class DailyReportModel_Revenue(models.Model):
    fleet_no = models.CharField(max_length=60)
    vehicle_no = models.CharField(max_length=60)
    no_of_loads = models.IntegerField()
    tonnage = models.IntegerField(default=33, null=False, blank=True)
    planned_rev_set = models.ForeignKey(PlannedRevenueModel, on_delete=models.CASCADE, default=1)
    
    # Dynamic route selections - stores which routes were completed
    completed_routes = models.ManyToManyField(Route, blank=True, related_name='revenue_reports')
    
    #Here I am setting up something that will help set the revenue to zero if the driver chooses 'No'
    zero_revenue = models.IntegerField(default=0)
    
    # Predicted revenue field - mirrors the predicted cost functionality
    predicted_revenue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Running cumulative predicted revenue")
    
    # Date field for tracking purposes (needed for the prediction algorithm)
    date = models.DateField(null=True, blank=True)
    
    # Driver field for tracking purposes (needed for the prediction algorithm)
    driver = models.ForeignKey(RegistryModel, on_delete=models.CASCADE, null=True, blank=True)
    
   
   #Planned Revenue Method
    @property
    def planned_rev(self):
        return self.planned_rev_set.planned_revenue
    
    #Dynamic Revenue Calculation
    @property
    def total_revenue(self):
        """Calculate total revenue from all completed routes"""
        total = Decimal('0.00')
        for route in self.completed_routes.all():
            total += route.transport_rate * self.tonnage * self.no_of_loads
        return total
    
    #Revenue variance calculation
    @property
    def revenue_variance(self):
        """Calculate variance between actual and planned revenue using route-specific planned revenue"""
        if self.completed_routes.exists():
            # Calculate total planned revenue from all completed routes
            total_planned_from_routes = Decimal('0.00')
            for route in self.completed_routes.all():
                total_planned_from_routes += route.planned_revenue * self.no_of_loads
            
            return self.total_revenue - total_planned_from_routes
        else:
            return self.zero_revenue - self.planned_rev
    
    @property
    def total_planned_revenue_from_routes(self):
        """Calculate total planned revenue from completed routes"""
        if self.completed_routes.exists():
            total_planned = Decimal('0.00')
            for route in self.completed_routes.all():
                total_planned += route.planned_revenue * self.no_of_loads
            return total_planned
        return Decimal('0.00')
    
    #Zero revenue method
    @property
    def zero_rev(self):
        return self.zero_revenue
    
    def save(self, *args, **kwargs):
        """Override save to calculate running predicted revenue - mirrors the cost model"""
        # Only calculate predicted revenue if we have the necessary data
        # On first save (before routes are added), skip prediction calculation
        skip_prediction = kwargs.pop('skip_prediction', False)
        
        if not skip_prediction:
            # Calculate current total revenue
            current_total_revenue = self.total_revenue
            
            # Get previous revenue entry for this driver/fleet combination
            previous_entry = None
            if self.driver and self.fleet_no:
                previous_entry = DailyReportModel_Revenue.objects.filter(
                    driver=self.driver,
                    fleet_no=self.fleet_no
                ).exclude(id=self.id).order_by('-date', '-id').first()
            
            if previous_entry and previous_entry.predicted_revenue is not None:
                # For subsequent entries: 
                # New predicted revenue = Previous predicted revenue + Average(current total, previous total)
                previous_total_revenue = previous_entry.total_revenue
                previous_predicted = Decimal(str(previous_entry.predicted_revenue))
                average_revenue = (current_total_revenue + previous_total_revenue) / Decimal('2')
                self.predicted_revenue = previous_predicted + average_revenue
            else:
                # For first entry: predicted revenue = current total revenue
                self.predicted_revenue = current_total_revenue
            
            # Round to 2 decimal places
            self.predicted_revenue = round(self.predicted_revenue, 2)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_latest_predicted_revenue(cls, fleet_no=None, driver=None):
        """Get the most recent predicted revenue for a driver/fleet combination"""
        query_filter = {}
        if fleet_no:
            query_filter['fleet_no'] = fleet_no
        if driver:
            query_filter['driver'] = driver
            
        latest_entry = cls.objects.filter(**query_filter).order_by('-date', '-id').first()
        if latest_entry and latest_entry.predicted_revenue is not None:
            return latest_entry.predicted_revenue
        return Decimal('0.00')
    
    def get_predicted_revenue(self):
        """Instance method to get the stored predicted revenue for this entry"""
        return self.predicted_revenue or Decimal('0.00')
    
   


# Live tracking Section

def _new_tracker_token():
    import secrets
    return secrets.token_urlsafe(24)


class VehicleTracker(models.Model):
    """A GPS source (hardware unit, phone, or simulator) bound to one vehicle.

    Devices authenticate to the ingest API with ``Authorization: Bearer <token>``.
    """
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='tracker')
    token = models.CharField(max_length=64, unique=True, default=_new_tracker_token, editable=False)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def rotate_token(self):
        self.token = _new_tracker_token()
        self.save(update_fields=['token'])

    def __str__(self):
        return f"Tracker for {self.vehicle.vehicle_registration_no}"


class VehiclePosition(models.Model):
    """One GPS fix. The auto-increment id doubles as the polling cursor."""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='positions')
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed_kmh = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    accuracy_m = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField(help_text="Time the device took the fix")
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['id']
        indexes = [models.Index(fields=['vehicle', '-id'])]

    def __str__(self):
        return f"{self.vehicle.vehicle_registration_no} @ {self.latitude:.5f},{self.longitude:.5f}"
