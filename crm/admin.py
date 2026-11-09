from django.contrib import admin
from .models import AgentModel, CRMClient, CRMSite, ClientInteraction, AIHuntingLog, AgentPerformance, AIHuntedProspect


@admin.register(AgentModel)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        'agent_id', 'full_name', 'agent_type', 'email', 'status', 
        'total_clients_acquired', 'total_commission_earned', 'created_at'
    )
    list_filter = ('agent_type', 'status', 'department', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'agent_id')
    readonly_fields = ('agent_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('agent_id', 'agent_type', 'user')
        }),
        ('Personal Details', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'age', 'profile_picture')
        }),
        ('Professional Details', {
            'fields': ('department', 'hire_date', 'salary', 'commission_rate', 'status')
        }),
        ('Performance', {
            'fields': ('total_clients_acquired', 'total_commission_earned')
        }),
        ('AI Agent Settings', {
            'fields': ('ai_model_version', 'target_region', 'hunting_frequency_hours', 'last_hunting_session'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'


@admin.register(CRMClient)
class CRMClientAdmin(admin.ModelAdmin):
    list_display = (
        'client_name', 'company_name', 'status', 'priority', 'agent',
        'potential_value', 'last_contact_date', 'created_at'
    )
    list_filter = ('status', 'priority', 'company_size', 'industry', 'agent', 'created_at')
    search_fields = ('client_name', 'company_name', 'email', 'city')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('client_name', 'company_name', 'client_contact', 'email')
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'province_state', 'postal_code', 'country')
        }),
        ('Business Information', {
            'fields': ('industry', 'company_size', 'annual_revenue', 'website')
        }),
        ('CRM Status', {
            'fields': ('status', 'priority', 'agent', 'potential_value')
        }),
        ('Fleet Services', {
            'fields': ('requires_fleet_services', 'estimated_vehicles_needed', 'preferred_routes')
        }),
        ('Tracking', {
            'fields': ('date_acquired', 'last_contact_date', 'next_follow_up', 'source', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CRMSite)
class CRMSiteAdmin(admin.ModelAdmin):
    list_display = (
        'site_name', 'client', 'site_manager', 'status', 
        'required_vehicles', 'estimated_monthly_revenue', 'created_at'
    )
    list_filter = ('status', 'site_type', 'created_at')
    search_fields = ('site_name', 'site_manager', 'client__client_name', 'client__company_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ClientInteraction)
class ClientInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'client', 'agent', 'interaction_type', 'subject', 
        'interaction_date', 'next_action_date', 'satisfaction_rating'
    )
    list_filter = ('interaction_type', 'satisfaction_rating', 'interaction_date', 'agent')
    search_fields = ('client__client_name', 'subject', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Interaction Details', {
            'fields': ('client', 'agent', 'interaction_type', 'interaction_date')
        }),
        ('Content', {
            'fields': ('subject', 'description', 'outcome')
        }),
        ('Follow-up', {
            'fields': ('next_action', 'next_action_date')
        }),
        ('Metrics', {
            'fields': ('duration_minutes', 'satisfaction_rating', 'created_at')
        })
    )


@admin.register(AIHuntingLog)
class AIHuntingLogAdmin(admin.ModelAdmin):
    list_display = (
        'hunting_session_id', 'agent', 'target_region', 'status',
        'prospects_found', 'clients_created', 'start_time'
    )
    list_filter = ('status', 'target_region', 'start_time')
    search_fields = ('hunting_session_id', 'agent__first_name', 'agent__last_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Session Info', {
            'fields': ('hunting_session_id', 'agent', 'status')
        }),
        ('Configuration', {
            'fields': ('target_region', 'search_keywords', 'max_results')
        }),
        ('Results', {
            'fields': ('prospects_found', 'valid_contacts', 'clients_created')
        }),
        ('Technical Details', {
            'fields': ('start_time', 'end_time', 'api_calls_made', 'api_quota_used', 'error_log'),
            'classes': ('collapse',)
        })
    )


@admin.register(AgentPerformance)
class AgentPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'agent', 'month', 'year', 'prospects_hunted', 'prospects_approved', 'clients_converted',
        'approval_rate_display', 'conversion_rate_display'
    )
    list_filter = ('year', 'month', 'agent')
    search_fields = ('agent__first_name', 'agent__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def approval_rate_display(self, obj):
        return f"{obj.approval_rate:.1f}%"
    approval_rate_display.short_description = 'Approval Rate'
    
    def conversion_rate_display(self, obj):
        return f"{obj.conversion_rate:.1f}%"
    conversion_rate_display.short_description = 'Conversion Rate'


@admin.register(AIHuntedProspect)
class AIHuntedProspectAdmin(admin.ModelAdmin):
    list_display = (
        'business_name', 'contact_person', 'email', 'agent', 'hunt_source',
        'confidence_score', 'approval_status', 'discovered_at'
    )
    list_filter = ('approval_status', 'hunt_source', 'needs_fleet_management', 'agent', 'discovered_at')
    search_fields = ('business_name', 'contact_person', 'email', 'city', 'industry')
    readonly_fields = ('discovered_at', 'created_at', 'updated_at', 'conversion_date')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('business_name', 'contact_person', 'email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'province_state', 'country')
        }),
        ('Business Details', {
            'fields': ('industry', 'business_description', 'estimated_fleet_size', 'annual_revenue_estimate')
        }),
        ('Fleet Management Assessment', {
            'fields': ('needs_fleet_management', 'fleet_management_indicators')
        }),
        ('Hunting Details', {
            'fields': ('agent', 'hunting_session', 'hunt_source', 'confidence_score', 'search_keywords_used')
        }),
        ('Approval Workflow', {
            'fields': ('approval_status', 'approved_by', 'approval_date', 'rejection_reason')
        }),
        ('Conversion', {
            'fields': ('converted_to_client', 'conversion_date')
        }),
        ('Timestamps', {
            'fields': ('discovered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_prospects', 'reject_prospects']
    
    def approve_prospects(self, request, queryset):
        for prospect in queryset.filter(approval_status='pending'):
            prospect.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} prospects.")
    approve_prospects.short_description = "Approve selected prospects"
    
    def reject_prospects(self, request, queryset):
        for prospect in queryset.filter(approval_status='pending'):
            prospect.reject(request.user, "Bulk rejection")
        self.message_user(request, f"Rejected {queryset.count()} prospects.")
    reject_prospects.short_description = "Reject selected prospects"


# Customize admin site
admin.site.site_header = "Fleet Management CRM Admin"
admin.site.site_title = "CRM Admin Portal"
admin.site.index_title = "Welcome to Fleet Management CRM Administration"
