#URLS.PY

from django.urls import path
from . import views

app_name = 'driverAssignment'

urlpatterns = [
    # Legacy RouteManager URLs (for backward compatibility)
    path('route_details/<int:pk>', views.route_details, name='route_details'),
    path('all_routes/', views.all_routes, name='all_routes'),
    path('delete_route/<int:pk>', views.delete_route, name='delete_route'),
    path('add_route/', views.add_route, name='add_route'),
    path('update_route/<int:pk>', views.update_route, name='update_route'),
    path('<int:pk>/drivers_assigned/', views.drivers_assigned, name='drivers_assigned'),
    path('fleetcam_view/<int:driver_id>/', views.fleetcam_view, name='fleetcam_view'),
    
    # New integrated URLs for main app routes
    path('integrated-routes/', views.integrated_routes_view, name='integrated_routes'),
    path('assign-driver/', views.assign_driver_to_route_view, name='assign_driver'),
    path('assign-driver/<int:route_id>/', views.assign_driver_to_route_view, name='assign_driver_to_route'),
    path('manage-drivers/<int:route_id>/', views.route_driver_management_view, name='manage_route_drivers'),
    path('route-drivers/<int:route_id>/', views.route_assigned_drivers_view, name='route_assigned_drivers'),
    path('driver-assignments/<int:driver_id>/', views.driver_assignments_view, name='driver_assignments'),
    path('driver-detail/<int:driver_id>/', views.driver_detail_view, name='driver_detail'),
    path('remove-assignment/<int:assignment_id>/', views.remove_driver_assignment_view, name='remove_assignment'),
    
    # New Hierarchical Assignment URLs (Driver → Vehicle → Route)
    path('assign-driver-vehicle/', views.assign_driver_to_vehicle_view, name='assign_driver_vehicle'),
    path('assign-vehicle-route/', views.assign_vehicle_to_route_view, name='assign_vehicle_route'),
    path('complete-assignment/', views.complete_assignment_view, name='complete_assignment'),
    path('driver-vehicle-assignments/', views.driver_vehicle_assignments_view, name='driver_vehicle_assignments'),
    path('vehicle-route-assignments/', views.vehicle_route_assignments_view, name='vehicle_route_assignments'),
    path('complete-assignments/', views.complete_assignments_view, name='complete_assignments'),
    path('remove-driver-vehicle/<int:assignment_id>/', views.remove_driver_vehicle_assignment, name='remove_driver_vehicle'),
    path('remove-vehicle-route/<int:assignment_id>/', views.remove_vehicle_route_assignment, name='remove_vehicle_route'),
    path('remove-complete/<int:assignment_id>/', views.remove_complete_assignment, name='remove_complete'),
]
