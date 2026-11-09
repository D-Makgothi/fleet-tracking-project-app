from django.contrib import admin
from .models import (FuelRateModel, PlannedRevenueModel, TransportRateModel_1, 
                     TransportRateModel_2, TransportRateModel_3, TransportRateModel_4, DailyReportModel_Revenue, DailyReportModel_Cost, Vehicle, Route)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'start', 'finish', 'transport_rate', 'planned_revenue', 'get_variance_per_load', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('route_name', 'start', 'finish')
    readonly_fields = ('created_at',)
    
    def get_variance_per_load(self, obj):
        return f"R{obj.get_variance_per_load():.2f}"
    get_variance_per_load.short_description = 'Variance per Load'
    get_variance_per_load.admin_order_field = 'transport_rate'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_registration_no', 'vehicle_make', 'vehicle_registration_expiry', 'is_active', 'created_at')
    list_filter = ('is_active', 'vehicle_make', 'created_at')
    search_fields = ('vehicle_registration_no', 'vehicle_make')
    readonly_fields = ('created_at', 'updated_at')

# Register your models here.
admin.site.register(DailyReportModel_Revenue)
admin.site.register(DailyReportModel_Cost)
admin.site.register(FuelRateModel)
admin.site.register(PlannedRevenueModel)
admin.site.register(TransportRateModel_1)
admin.site.register(TransportRateModel_2)
admin.site.register(TransportRateModel_3)
admin.site.register(TransportRateModel_4)


from .models import VehicleTracker, VehiclePosition


@admin.register(VehicleTracker)
class VehicleTrackerAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'is_enabled', 'last_seen_at', 'created_at')
    list_filter = ('is_enabled',)
    search_fields = ('vehicle__vehicle_registration_no',)
    readonly_fields = ('token', 'created_at', 'last_seen_at')
    actions = ['rotate_tokens']

    @admin.action(description='Rotate token (old phone links stop working)')
    def rotate_tokens(self, request, queryset):
        for tracker in queryset:
            tracker.rotate_token()
        self.message_user(request, f'Rotated {queryset.count()} token(s).')


@admin.register(VehiclePosition)
class VehiclePositionAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'latitude', 'longitude', 'speed_kmh', 'recorded_at', 'received_at')
    list_filter = ('vehicle',)
    date_hierarchy = 'received_at'
    list_select_related = ('vehicle',)
