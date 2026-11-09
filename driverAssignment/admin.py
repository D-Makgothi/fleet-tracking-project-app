from django.contrib import admin
from .models import RouteManager, DriverRouteAssignment, DriverVehicleAssignment, VehicleRouteAssignment, CompleteAssignment

@admin.register(RouteManager)
class RouteManagerAdmin(admin.ModelAdmin):
    list_display = ['route_name', 'start', 'finish', 'created_at']
    list_filter = ['created_at']
    search_fields = ['route_name', 'start', 'finish']
    filter_horizontal = ['drivers']

@admin.register(DriverRouteAssignment)
class DriverRouteAssignmentAdmin(admin.ModelAdmin):
    list_display = ['driver', 'route', 'assigned_date', 'is_active']
    list_filter = ['is_active', 'assigned_date', 'route']
    search_fields = ['driver__user__username', 'route__route_name']
    raw_id_fields = ['driver', 'route']
    readonly_fields = ['assigned_date']


@admin.register(DriverVehicleAssignment)
class DriverVehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['driver', 'vehicle', 'assigned_date', 'is_active']
    list_filter = ['is_active', 'assigned_date', 'vehicle__vehicle_make']
    search_fields = ['driver__user__username', 'vehicle__vehicle_registration_no', 'vehicle__vehicle_make']
    raw_id_fields = ['driver', 'vehicle']
    readonly_fields = ['assigned_date']


@admin.register(VehicleRouteAssignment)
class VehicleRouteAssignmentAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'route', 'assigned_date', 'is_active']
    list_filter = ['is_active', 'assigned_date', 'route']
    search_fields = ['vehicle__vehicle_registration_no', 'route__route_name']
    raw_id_fields = ['vehicle', 'route']
    readonly_fields = ['assigned_date']


@admin.register(CompleteAssignment)
class CompleteAssignmentAdmin(admin.ModelAdmin):
    list_display = ['driver', 'vehicle', 'route', 'created_date', 'is_active']
    list_filter = ['is_active', 'created_date', 'route', 'vehicle__vehicle_make']
    search_fields = ['driver__user__username', 'vehicle__vehicle_registration_no', 'route__route_name']
    raw_id_fields = ['driver', 'vehicle', 'route']
    readonly_fields = ['created_date']
