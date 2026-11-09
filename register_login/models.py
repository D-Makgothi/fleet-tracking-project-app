from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

# Registry Model
class RegistryModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mine= models.CharField(max_length = 60, blank=True, null=True )
    driver_license_no = models.CharField(max_length=60, blank=True, null=True)
    driver_license_expiry = models.DateField(blank=True, null=True)
    induction_license_no = models.CharField(max_length=60, blank=True, null=True)
    induction_license_expiry = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.user.username


# Controller Model
class ControllerModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Controller: {self.user.username}"



# Enhanced Clients Model
class ClientModel(models.Model):
    CLIENT_STATUS_CHOICES = [
        ('prospect', 'Prospect'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('active', 'Active Client'),
        ('inactive', 'Inactive'),
        ('lost', 'Lost'),
    ]
    
    COMPANY_SIZE_CHOICES = [
        ('small', '1-50 employees'),
        ('medium', '51-200 employees'),
        ('large', '201-1000 employees'),
        ('enterprise', '1000+ employees'),
    ]
    
    # Legacy fields (keeping for backward compatibility)
    site = models.CharField(max_length=60, blank=True, null=True)
    manager = models.CharField(max_length=60, blank=True, null=True)
    date_created = models.DateField(blank=True, null=True)
    
    # Enhanced CRM fields
    client_name = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    client_contact = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Detailed Contact Information
    phone_secondary = models.CharField(max_length=20, blank=True, null=True)
    address_line_1 = models.CharField(max_length=200, blank=True, null=True)
    address_line_2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province_state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Business Information
    industry = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, blank=True, null=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # CRM Status
    status = models.CharField(max_length=20, choices=CLIENT_STATUS_CHOICES, default='prospect')
    # agent = models.ForeignKey(AgentModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')  # Moved to CRM app
    potential_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    priority = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    
    # Tracking
    date_acquired = models.DateField(blank=True, null=True)
    last_contact_date = models.DateField(blank=True, null=True)
    next_follow_up = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Source Tracking
    source = models.CharField(max_length=100, blank=True, null=True, help_text="How was this client acquired?")
    referral_source = models.CharField(max_length=200, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f"{self.client_name or self.manager} - {self.company_name or self.site or 'Individual'}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [self.address_line_1, self.address_line_2, self.city, self.province_state, self.postal_code, self.country]
        return ', '.join([part for part in parts if part])
    
    class Meta:
        ordering = ['-created_at']


#Sites
class SiteModel(models.Model):
    # Class-level choices for status
    ACTIVE_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    site_reference = models.CharField(max_length=60, blank=True, null=True)
    responsible_user = models.CharField(max_length=60, blank=True, null=True)
    site_coordinator_email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=8, choices=ACTIVE_CHOICES, default='Active')
    site_category = models.CharField(max_length=60, blank=True, null=True)
    
    # Enhanced Site Information
    client = models.ForeignKey(ClientModel, on_delete=models.CASCADE, related_name='sites', null=True, blank=True)
    site_address = models.CharField(max_length=200, blank=True, null=True)
    site_phone = models.CharField(max_length=20, blank=True, null=True)
    site_email = models.EmailField(blank=True, null=True)
    site_type = models.CharField(max_length=100, blank=True, null=True)
    operational_hours = models.CharField(max_length=100, blank=True, null=True)
    
    # Site Details for Fleet Management
    required_vehicles = models.PositiveIntegerField(default=1)
    preferred_routes = models.CharField(max_length=500, blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.site_reference or 'Unnamed Site'


# Client Interaction Tracking moved to CRM app


# Controller Activity Logging System
class ControllerActivityLog(models.Model):
    ACTION_CHOICES = [
        ('assignment_create', 'Created Assignment'),
        ('assignment_modify', 'Modified Assignment'),
        ('assignment_delete', 'Deleted Assignment'),
        ('report_submit', 'Submitted Report'),
        ('shift_start', 'Started Shift'),
        ('shift_end', 'Ended Shift'),
        ('driver_route_assign', 'Assigned Driver to Route'),
        ('driver_vehicle_assign', 'Assigned Driver to Vehicle'),
        ('vehicle_route_assign', 'Assigned Vehicle to Route'),
        ('complete_assignment', 'Created Complete Assignment'),
        ('daily_revenue_report', 'Submitted Daily Revenue Report'),
        ('daily_cost_report', 'Submitted Daily Cost Report'),
    ]
    
    controller = models.ForeignKey(ControllerModel, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    target_driver = models.ForeignKey(RegistryModel, on_delete=models.SET_NULL, null=True, blank=True, help_text="Driver affected by this action")
    target_vehicle_id = models.CharField(max_length=100, blank=True, null=True, help_text="Vehicle ID affected")
    target_route_id = models.CharField(max_length=100, blank=True, null=True, help_text="Route ID affected")
    details = models.JSONField(default=dict, blank=True, help_text="Additional action details")
    shift_date = models.DateField(auto_now_add=True, help_text="Date of the shift when action was performed")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['controller', 'shift_date']),
            models.Index(fields=['action_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.controller.user.username} - {self.get_action_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# Daily Shift Status Tracking
class DailyShiftStatus(models.Model):
    date = models.DateField(unique=True)
    active_assignments_count = models.IntegerField(default=0)
    controllers_worked = models.ManyToManyField(ControllerModel, blank=True, help_text="Controllers who worked this day")
    shift_summary = models.JSONField(default=dict, blank=True, help_text="Summary of the day's activities")
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(ControllerModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_shifts')
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Shift Status for {self.date} - {self.active_assignments_count} assignments"
    
    def get_shift_controllers(self):
        """Get list of controllers who worked this shift"""
        return [controller.user.username for controller in self.controllers_worked.all()]


 