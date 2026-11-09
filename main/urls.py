from django.urls import path
from . import views 
from . import tracking

app_name = 'main'

urlpatterns = [
    path('', views.home_view, name = 'home'),
    path('active_users/', views.active_users_view, name="active_users"),
    path('users/<int:user_id>/edit/', views.edit_user_view, name="edit_user"),
    path('users/<int:user_id>/delete/', views.delete_user_view, name="delete_user"),
    path('daily_cost_report/', views.daily_cost_report_form_view, name="daily_cost_report"),
    path('daily_rev_report/', views.daily_rev_report_form_view, name="daily_rev_report"),
    path('revenue/',views.revenue_view, name="revenue" ),
    path('cost/',views.cost_view, name="cost" ),
    path('drivers/costs/', views.driver_cost_list_view, name="driver_cost_list"),
    path('drivers/<int:driver_id>/costs/', views.driver_cost_view, name="driver_cost"),
    path('drivers/revenue/', views.driver_revenue_list_view, name="driver_revenue_list"),
    path('drivers/<int:driver_id>/revenue/', views.driver_revenue_view, name="driver_revenue"),

    # Route Management Patterns
    path('routes/', views.route_list_view, name="route_list"),
    path('routes/add/', views.route_add_view, name="route_add"),
    path('routes/<int:route_id>/edit/', views.route_edit_view, name="route_edit"),
    path('routes/<int:route_id>/delete/', views.route_delete_view, name="route_delete"),
    path('routes/<int:route_id>/toggle/', views.route_toggle_status_view, name="route_toggle"),
    path('routes/<int:route_id>/vehicles/', views.route_vehicle_assignments_view, name="route_vehicle_assignments"),

    # Fuel Rate Management Patterns
    path('fuel-rate-management/', views.fuel_rate_management_view, name="fuel_rate_management"),
    path('fuel-rate/<int:rate_id>/activate/', views.activate_fuel_rate_view, name="activate_fuel_rate"),
    path('fuel-rate/<int:rate_id>/delete/', views.delete_fuel_rate_view, name="delete_fuel_rate"),

    # Driver Expiry Warning Patterns
    path('driver-expiry-warnings/', views.driver_expiry_warnings_view, name="driver_expiry_warnings"),
    path('driver-expiry/<int:driver_id>/', views.driver_expiry_detail_view, name="driver_expiry_detail"),

    # Analytics and Finance Patterns
    path('analytics/', views.analytics_dashboard_view, name="analytics_dashboard"),
    path('analytics/consolidated/', views.consolidated_analytics_view, name="consolidated_analytics"),
    path('analytics/fuel-prices/', views.fuel_prices_analytics_view, name="fuel_prices_analytics"),
    path('analytics/cost-revenue/', views.cost_revenue_analytics_view, name="cost_revenue_analytics"),
    path('weather/', views.weather_data_view, name="weather_data"),
    path('live-map/', tracking.live_map_view, name="live_map"),
    path('live-map/api/positions/', tracking.positions_api, name="live_map_positions"),
    path('live-map/api/ingest/', tracking.ingest_api, name="live_map_ingest"),
    path('live-map/trackers/<int:vehicle_id>/enable/', tracking.enable_tracker_view, name="live_map_enable_tracker"),
    path('live-map/track/<str:token>/', tracking.tracker_page_view, name="live_map_tracker"),
    
    # AI Assistant Pattern
    path('ai-assistant/', views.ai_assistant_view, name="ai_assistant"),

    # Vehicle Management Patterns
    path('vehicles/', views.vehicle_list_view, name="vehicle_list"),
    path('vehicles/add/', views.vehicle_add_view, name="vehicle_add"),
    path('vehicles/<int:vehicle_id>/edit/', views.vehicle_edit_view, name="vehicle_edit"),
    path('vehicles/<int:vehicle_id>/delete/', views.vehicle_delete_view, name="vehicle_delete"),
    path('vehicles/<int:vehicle_id>/detail/', views.vehicle_detail_view, name="vehicle_detail"),
    path('vehicles/<int:vehicle_id>/fleetcam/', views.vehicle_fleetcam_view, name="vehicle_fleetcam"),

    # Drag and Drop Assignment Patterns
    path('assignments/drag-drop/', views.drag_drop_assignments_view, name="drag_drop_assignments"),
    path('ajax/assign-driver-vehicle/', views.ajax_assign_driver_vehicle, name="ajax_assign_driver_vehicle"),
    path('ajax/assign-vehicle-route/', views.ajax_assign_vehicle_route, name="ajax_assign_vehicle_route"),
    path('ajax/remove-driver-vehicle/', views.ajax_remove_driver_vehicle, name="ajax_remove_driver_vehicle"),
    path('ajax/remove-vehicle-route/', views.ajax_remove_vehicle_route, name="ajax_remove_vehicle_route"),
    path('ajax/remove-complete-assignment/', views.ajax_remove_complete_assignment, name="ajax_remove_complete_assignment"),

    # Bookkeeping Patterns
    path('bookkeeping/', views.bookkeeping_view, name="bookkeeping"),
    path('export/bookkeeping/', views.export_bookkeeping_excel, name="export_bookkeeping_excel"),

    # Excel Export Patterns
    path('export/costs/all/', views.export_all_costs_excel, name="export_all_costs_excel"),
    path('export/costs/driver/<int:driver_id>/', views.export_driver_costs_excel, name="export_driver_costs_excel"),
    path('export/revenue/all/', views.export_all_revenue_excel, name="export_all_revenue_excel"),
    path('export/revenue/driver/<int:driver_id>/', views.export_driver_revenue_excel, name="export_driver_revenue_excel"),

    #Admin Patterns
    path('client/',views.client_view, name="client" ), #NAME is the variable name we gave that allows us to refernce this URL pattern
    path('site/',views.site_view, name="site" ),
]

