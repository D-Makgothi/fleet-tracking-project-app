from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


# CRM Agent System - AI Agents Only
class AgentModel(models.Model):
    AGENT_TYPES = [
        ('ai', 'AI Agent'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='crm_agent')
    agent_type = models.CharField(max_length=10, choices=AGENT_TYPES, default='ai')
    agent_id = models.CharField(max_length=20, unique=True)
    
    # Personal Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='agent_profiles/', blank=True, null=True)
    
    # Professional Details
    department = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(default=timezone.now)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    
    # Status and Performance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_clients_acquired = models.PositiveIntegerField(default=0)
    total_commission_earned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # AI Agent Specific Fields
    ai_model_version = models.CharField(max_length=50, default='GPT-4')
    last_hunting_session = models.DateTimeField(blank=True, null=True)
    hunting_frequency_hours = models.PositiveIntegerField(default=24)  # Daily hunting
    target_regions = models.TextField(default='Local, Regional, Global', help_text="Comma-separated regions to hunt in")
    google_api_key = models.CharField(max_length=200, blank=True, null=True)
    linkedin_api_key = models.CharField(max_length=200, blank=True, null=True)
    
    # Fleet Management Hunting Configuration
    fleet_keywords = models.TextField(
        default='fleet management, logistics, transport, delivery, trucking, vehicle tracking, dispatch',
        help_text="Keywords to hunt for fleet management prospects"
    )
    max_daily_prospects = models.PositiveIntegerField(default=1, help_text="Maximum prospects to hunt per day")
    is_auto_hunting = models.BooleanField(default=True, help_text="Enable automatic daily hunting")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.agent_type.title()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_ai_agent(self):
        return True  # All agents are AI agents now
    
    def should_hunt_today(self):
        """Check if this agent should hunt today"""
        if not self.is_auto_hunting or self.status != 'active':
            return False
        
        if not self.last_hunting_session:
            return True
        
        # Check if 24 hours have passed since last hunt
        from datetime import timedelta
        time_since_last_hunt = timezone.now() - self.last_hunting_session
        return time_since_last_hunt.total_seconds() >= (self.hunting_frequency_hours * 3600)
    
    def get_daily_hunt_count(self):
        """Get number of prospects hunted today"""
        today = timezone.now().date()
        return self.hunted_prospects.filter(discovered_at__date=today).count()
    
    def calculate_commission(self, amount):
        """Calculate commission for this agent"""
        return amount * (self.commission_rate / 100)
    
    def save(self, *args, **kwargs):
        if not self.agent_id:
            self.agent_id = f"AGT{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


# Enhanced CRM Clients Model
class CRMClient(models.Model):
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
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    client_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    client_contact = models.CharField(max_length=60)
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
    agent = models.ForeignKey(AgentModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_clients')
    potential_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Tracking
    date_acquired = models.DateField(blank=True, null=True)
    last_contact_date = models.DateField(blank=True, null=True)
    next_follow_up = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Source Tracking
    source = models.CharField(max_length=100, blank=True, null=True, help_text="How was this client acquired?")
    referral_source = models.CharField(max_length=200, blank=True, null=True)
    
    # Fleet Management Connection
    requires_fleet_services = models.BooleanField(default=True)
    estimated_vehicles_needed = models.PositiveIntegerField(blank=True, null=True)
    preferred_routes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.client_name} - {self.company_name or 'Individual'}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [self.address_line_1, self.address_line_2, self.city, self.province_state, self.postal_code, self.country]
        return ', '.join([part for part in parts if part])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "CRM Client"
        verbose_name_plural = "CRM Clients"


# Client Sites for CRM
class CRMSite(models.Model):
    SITE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Setup'),
        ('closed', 'Closed'),
    ]
    
    client = models.ForeignKey(CRMClient, on_delete=models.CASCADE, related_name='sites')
    site_name = models.CharField(max_length=200)
    site_manager = models.CharField(max_length=100)
    
    # Site Contact Information
    site_address = models.CharField(max_length=200, blank=True, null=True)
    site_phone = models.CharField(max_length=20, blank=True, null=True)
    site_email = models.EmailField(blank=True, null=True)
    site_type = models.CharField(max_length=100, blank=True, null=True)
    operational_hours = models.CharField(max_length=100, blank=True, null=True)
    
    # Fleet Service Requirements
    required_vehicles = models.PositiveIntegerField(default=1)
    preferred_routes = models.TextField(blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    estimated_monthly_revenue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=SITE_STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.site_name} - {self.client.company_name or self.client.client_name}"
    
    class Meta:
        ordering = ['-created_at']


# Client Interaction Tracking
class ClientInteraction(models.Model):
    INTERACTION_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'In-Person Meeting'),
        ('video_call', 'Video Call'),
        ('proposal', 'Proposal Sent'),
        ('follow_up', 'Follow-up'),
        ('contract', 'Contract Discussion'),
        ('site_visit', 'Site Visit'),
        ('demo', 'Service Demo'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(CRMClient, on_delete=models.CASCADE, related_name='interactions')
    agent = models.ForeignKey(AgentModel, on_delete=models.SET_NULL, null=True, blank=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    interaction_date = models.DateTimeField(default=timezone.now)
    
    subject = models.CharField(max_length=200)
    description = models.TextField()
    outcome = models.TextField(blank=True, null=True)
    next_action = models.CharField(max_length=200, blank=True, null=True)
    next_action_date = models.DateField(blank=True, null=True)
    
    # Additional tracking
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    satisfaction_rating = models.PositiveIntegerField(blank=True, null=True, help_text="1-5 rating")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.interaction_type.title()} with {self.client.client_name} on {self.interaction_date.date()}"
    
    class Meta:
        ordering = ['-interaction_date']


# AI Agent Hunting Logs
class AIHuntingLog(models.Model):
    agent = models.ForeignKey(AgentModel, on_delete=models.CASCADE, related_name='hunting_logs')
    hunting_session_id = models.CharField(max_length=50, unique=True)
    
    # Hunt Configuration
    target_region = models.CharField(max_length=100)
    search_keywords = models.TextField(help_text="Keywords used for hunting")
    max_results = models.PositiveIntegerField(default=50)
    
    # Results
    prospects_found = models.PositiveIntegerField(default=0)
    valid_contacts = models.PositiveIntegerField(default=0)
    clients_created = models.PositiveIntegerField(default=0)
    
    # Session Details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='running')
    
    error_log = models.TextField(blank=True, null=True)
    api_calls_made = models.PositiveIntegerField(default=0)
    api_quota_used = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Hunt {self.hunting_session_id} by {self.agent.full_name}"
    
    class Meta:
        ordering = ['-created_at']


# AI-Hunted Prospects (Pending Approval)
class AIHuntedProspect(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    HUNT_SOURCE_CHOICES = [
        ('google_search', 'Google Search'),
        ('business_directories', 'Business Directories'),
        ('linkedin', 'LinkedIn'),
        ('company_websites', 'Company Websites'),
        ('social_media', 'Social Media'),
        ('other', 'Other'),
    ]
    
    # AI Agent who found this prospect
    agent = models.ForeignKey(AgentModel, on_delete=models.CASCADE, related_name='hunted_prospects')
    hunting_session = models.ForeignKey(AIHuntingLog, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Company Information
    business_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Address Information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province_state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Business Details
    industry = models.CharField(max_length=100, blank=True, null=True)
    business_description = models.TextField(blank=True, null=True)
    estimated_fleet_size = models.PositiveIntegerField(blank=True, null=True)
    annual_revenue_estimate = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Fleet Management Indicators
    needs_fleet_management = models.BooleanField(default=True)
    fleet_management_indicators = models.TextField(
        blank=True, null=True,
        help_text="Keywords/indicators that suggest they need fleet management"
    )
    
    # Hunting Details
    hunt_source = models.CharField(max_length=20, choices=HUNT_SOURCE_CHOICES, default='google_search')
    confidence_score = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.75,
        help_text="AI confidence score (0.00-1.00)"
    )
    search_keywords_used = models.CharField(max_length=500, blank=True, null=True)
    
    # Approval Workflow
    approval_status = models.CharField(max_length=15, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_prospects')
    approval_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Conversion to Client
    converted_to_client = models.ForeignKey(CRMClient, on_delete=models.SET_NULL, null=True, blank=True)
    conversion_date = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    discovered_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business_name} - {self.get_approval_status_display()}"
    
    @property
    def is_pending(self):
        return self.approval_status == 'pending'
    
    @property
    def is_approved(self):
        return self.approval_status == 'approved'
    
    @property
    def is_rejected(self):
        return self.approval_status == 'rejected'
    
    def approve(self, user):
        """Approve this prospect"""
        self.approval_status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()
    
    def reject(self, user, reason=""):
        """Reject this prospect"""
        self.approval_status = 'rejected'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def convert_to_client(self):
        """Convert approved prospect to CRM client"""
        if not self.is_approved:
            raise ValueError("Can only convert approved prospects to clients")
        
        # Create CRM client
        client = CRMClient.objects.create(
            client_name=self.contact_person or self.business_name,
            company_name=self.business_name,
            client_contact=self.phone or '',
            email=self.email,
            address_line_1=self.address,
            city=self.city,
            province_state=self.province_state,
            country=self.country,
            industry=self.industry,
            website=self.website,
            status='prospect',
            agent=self.agent,
            estimated_vehicles_needed=self.estimated_fleet_size,
            annual_revenue=self.annual_revenue_estimate,
            source='ai_hunting',
            notes=f"AI-discovered prospect. Confidence: {self.confidence_score}. "
                  f"Fleet indicators: {self.fleet_management_indicators}",
            requires_fleet_services=self.needs_fleet_management,
            date_acquired=timezone.now().date()
        )
        
        # Link conversion
        self.converted_to_client = client
        self.conversion_date = timezone.now()
        self.save()
        
        # Update agent performance
        self.agent.total_clients_acquired += 1
        self.agent.save()
        
        return client
    
    class Meta:
        ordering = ['-discovered_at']
        verbose_name = "AI Hunted Prospect"
        verbose_name_plural = "AI Hunted Prospects"


# Agent Performance Tracking
class AgentPerformance(models.Model):
    agent = models.ForeignKey(AgentModel, on_delete=models.CASCADE, related_name='performance_records')
    
    # Time Period
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    
    # Metrics
    prospects_hunted = models.PositiveIntegerField(default=0)
    prospects_approved = models.PositiveIntegerField(default=0)
    clients_converted = models.PositiveIntegerField(default=0)
    hunting_sessions = models.PositiveIntegerField(default=0)
    
    # Performance Metrics
    average_confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    approval_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Percentage
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Percentage
    
    # Revenue
    total_potential_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_actual_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.agent.full_name} - {self.month}/{self.year}"
    
    def calculate_metrics(self):
        """Calculate performance metrics for this period"""
        prospects = self.agent.hunted_prospects.filter(
            discovered_at__month=self.month,
            discovered_at__year=self.year
        )
        
        self.prospects_hunted = prospects.count()
        self.prospects_approved = prospects.filter(approval_status='approved').count()
        self.clients_converted = prospects.filter(converted_to_client__isnull=False).count()
        
        if self.prospects_hunted > 0:
            self.approval_rate = (self.prospects_approved / self.prospects_hunted) * 100
            self.conversion_rate = (self.clients_converted / self.prospects_hunted) * 100
            
            # Calculate average confidence score
            avg_confidence = prospects.aggregate(
                avg=models.Avg('confidence_score')
            )['avg']
            self.average_confidence_score = avg_confidence or 0.0
        
        self.save()
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['agent', 'month', 'year']
