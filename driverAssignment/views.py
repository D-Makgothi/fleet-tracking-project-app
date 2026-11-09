from django.shortcuts import render, redirect, get_object_or_404
from register_login.models import RegistryModel, ControllerModel
from register_login.views import log_controller_activity, update_daily_shift_status
from .models import RouteManager, DriverRouteAssignment, DriverVehicleAssignment, VehicleRouteAssignment, CompleteAssignment
from main.models import Route, Vehicle
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from functools import wraps
from .forms import AddRouteForm, RouteFilterForm, DriverRouteAssignmentForm, RouteDriverManagementForm, DriverVehicleAssignmentForm, VehicleRouteAssignmentForm, CompleteAssignmentForm


# Custom decorator to ensure only controllers and admins can access assignment views
def admin_or_controller_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is admin (staff)
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a controller
        try:
            ControllerModel.objects.get(user=request.user)
            return view_func(request, *args, **kwargs)
        except ControllerModel.DoesNotExist:
            pass
        
        # User is neither admin nor controller
        return HttpResponseForbidden(
            "<h1>Access Denied</h1>"
            "<p>Only administrators and controllers can access this page.</p>"
            "<p>Please contact your system administrator if you believe this is an error.</p>"
        )
    return _wrapped_view

def all_routes(request):
    # Initialize the filter form with GET data
    form = RouteFilterForm(request.GET or None)
    
    # Start with all routes
    route_data = RouteManager.objects.all()
    
    # Apply filters if form is valid
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        if search_query:
            route_data = route_data.filter(route_name__icontains=search_query)  # Case-insensitive search
    
    context = {
        'form': form,
        'route_data': route_data
    }
    
    return render(request, 'driverAssignment/all_routes.html', context)



def route_details(request, pk):
    route_data = get_object_or_404(RouteManager, id=pk)
    context = {
        'route_data': route_data,
        'title': f"Route Details - {route_data.route_name}"
    }
    return render(request, 'driverAssignment/route_details.html', context)


def delete_route(request, pk):
    delete_route = RouteManager.objects.get(id=pk)
    delete_route.delete()

    return render(request, 'driverAssignment/delete_route.html')

def add_route(request):
    if request.method == "POST":
        form = AddRouteForm(request.POST)
        if form.is_valid():
            add_record = form.save()
            messages.success(request, "Route Added")
            return redirect('driverAssignment:all_routes')
    else:
        form = AddRouteForm()
    return render(request, 'driverAssignment/add_route.html', {'form': form})

def update_route(request, pk):

    route = get_object_or_404(RouteManager, pk=pk)
    if request.method == "POST":
        form = AddRouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f"Route '{route.route_name}' updated successfully with assigned drivers.")
            return redirect('driverAssignment:all_routes')  # Or redirect to a routes list view
    else:
        form = AddRouteForm(instance=route)
    
    context = {
        'form': form,
        'route': route
    }
    return render(request, 'driverAssignment/update_route.html', context)


def drivers_assigned(request, pk):
    route = get_object_or_404(RouteManager, pk=pk)
    
    context = {
        'route': route,
        'drivers': route.drivers.all(),  # Get all assigned drivers
    }
    return render(request, 'driverAssignment/drivers_assigned.html', context)

def fleetcam_view(request, driver_id):
    driver = get_object_or_404(RegistryModel, id=driver_id)
    driver_link = driver.fleetcam_link

    if driver_link:
        return redirect(driver_link)
    else:
        # Find a route associated with the driver (assuming ManyToManyField)
        try:
            route = RouteManager.objects.filter(drivers=driver).first()
            if route:
                messages.error(request, "No FleetCam link available for this driver.")
                return redirect('driverAssignment:drivers_assigned', pk=route.pk)
            else:
                messages.error(request, "No route assigned to this driver.")
                return redirect('driverAssignment:all_routes')  # Fallback redirect
        except RouteManager.DoesNotExist:
            messages.error(request, "No route assigned to this driver.")
            return redirect('driverAssignment:all_routes')  # Fallback redirect
        
    # return render(request, 'driverAssignment/fleetcam_view', {'driver_link': driver_link})


# New integrated views for working with main app routes

def integrated_routes_view(request):
    """Display all routes from main app with driver assignment capabilities"""
    search_query = request.GET.get('search', '')
    routes = Route.objects.filter(is_active=True)
    
    if search_query:
        routes = routes.filter(route_name__icontains=search_query)
    
    # Add assignment counts to each route
    routes_with_assignments = []
    for route in routes:
        assigned_drivers_count = DriverRouteAssignment.objects.filter(
            route=route, is_active=True
        ).count()
        routes_with_assignments.append({
            'route': route,
            'assigned_drivers_count': assigned_drivers_count
        })
    
    context = {
        'routes_with_assignments': routes_with_assignments,
        'search_query': search_query,
    }
    return render(request, 'driverAssignment/integrated_routes.html', context)

@admin_or_controller_required
def assign_driver_to_route_view(request, route_id=None):
    """Assign a driver to a route from the main app - Only for admins and controllers"""
    route = None
    if route_id:
        route = get_object_or_404(Route, id=route_id)
    
    if request.method == "POST":
        form = DriverRouteAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            
            # Log controller activity
            log_controller_activity(
                controller_user=request.user,
                action_type='driver_route_assign',
                description=f'Assigned driver {assignment.driver.user.username} to route {assignment.route.route_name}',
                target_driver=assignment.driver,
                target_route_id=str(assignment.route.id),
                details={
                    'driver_username': assignment.driver.user.username,
                    'route_name': assignment.route.route_name,
                    'route_details': f'{assignment.route.start} to {assignment.route.finish}'
                }
            )
            update_daily_shift_status(request.user)
            
            messages.success(request, f"Driver {assignment.driver.user.username} assigned to route {assignment.route.route_name} successfully!")
            return redirect('driverAssignment:integrated_routes')
    else:
        form = DriverRouteAssignmentForm()
        if route:
            form.initial['route'] = route
    
    context = {
        'form': form,
        'route': route,
        'title': f'Assign Driver to Route{f" - {route.route_name}" if route else ""}'
    }
    return render(request, 'driverAssignment/assign_driver.html', context)

@admin_or_controller_required
def route_driver_management_view(request, route_id):
    """Manage driver assignments for a specific route - Only for admins and controllers"""
    route = get_object_or_404(Route, id=route_id)
    
    if request.method == "POST":
        form = RouteDriverManagementForm(request.POST, route=route)
        if form.is_valid():
            selected_drivers = form.cleaned_data['drivers']
            
            # Deactivate all current assignments
            DriverRouteAssignment.objects.filter(route=route, is_active=True).update(is_active=False)
            
            # Create new assignments for selected drivers
            for driver in selected_drivers:
                assignment, created = DriverRouteAssignment.objects.get_or_create(
                    route=route,
                    driver=driver,
                    defaults={'is_active': True}
                )
                if not created:
                    assignment.is_active = True
                    assignment.save()
            
            # Log controller activity
            driver_names = [driver.user.username for driver in selected_drivers]
            log_controller_activity(
                controller_user=request.user,
                action_type='assignment_modify',
                description=f'Updated driver assignments for route {route.route_name}: {", ".join(driver_names)}',
                target_route_id=str(route.id),
                details={
                    'route_name': route.route_name,
                    'assigned_drivers': driver_names,
                    'total_drivers': len(selected_drivers)
                }
            )
            update_daily_shift_status(request.user)
            
            messages.success(request, f"Driver assignments for route '{route.route_name}' updated successfully!")
            return redirect('driverAssignment:integrated_routes')
    else:
        form = RouteDriverManagementForm(route=route)
    
    # Get current assignments
    current_assignments = DriverRouteAssignment.objects.filter(
        route=route, is_active=True
    ).select_related('driver')
    
    context = {
        'form': form,
        'route': route,
        'current_assignments': current_assignments,
        'title': f'Manage Drivers for {route.route_name}'
    }
    return render(request, 'driverAssignment/manage_route_drivers.html', context)

def driver_assignments_view(request, driver_id):
    """View all route assignments for a specific driver"""
    driver = get_object_or_404(RegistryModel, id=driver_id)
    assignments = DriverRouteAssignment.objects.filter(
        driver=driver, is_active=True
    ).select_related('route')
    
    context = {
        'driver': driver,
        'assignments': assignments,
        'title': f'Driver Assignments - {driver.user.username}'
    }
    return render(request, 'driverAssignment/driver_detail.html', context)

def remove_driver_assignment_view(request, assignment_id):
    """Remove a driver from a route assignment"""
    assignment = get_object_or_404(DriverRouteAssignment, id=assignment_id)
    
    if request.method == "POST":
        driver_name = assignment.driver.user.username
        route_name = assignment.route.route_name
        assignment.is_active = False
        assignment.save()
        
        messages.success(request, f"Removed {driver_name} from route {route_name}")
        return redirect('driverAssignment:integrated_routes')
    
    context = {
        'assignment': assignment,
    }
    return render(request, 'driverAssignment/confirm_remove_assignment.html', context)

def route_assigned_drivers_view(request, route_id):
    """Display detailed table of all drivers assigned to a specific route"""
    route = get_object_or_404(Route, id=route_id)
    
    # Get all active assignments for this route
    assignments = DriverRouteAssignment.objects.filter(
        route=route, is_active=True
    ).select_related('driver', 'driver__user').order_by('driver__user__username')
    
    # Prepare driver data with all required information
    drivers_data = []
    for assignment in assignments:
        driver = assignment.driver
        drivers_data.append({
            'assignment': assignment,
            'driver': driver,
            'username': driver.user.username,
            'mine': driver.mine or 'Not assigned',
            'vehicle_registration': driver.vehicle_registration_no or 'Not provided',
            'fleetcam_link': driver.fleetcam_link,
            'driver_license': driver.driver_license_no or 'Not provided',
            'assigned_date': assignment.assigned_date,
            'notes': assignment.notes
        })
    
    context = {
        'route': route,
        'drivers_data': drivers_data,
        'total_drivers': len(drivers_data),
    }
    return render(request, 'driverAssignment/route_assigned_drivers.html', context)

def driver_detail_view(request, driver_id):
    """Display driver detail page with hero section"""
    driver = get_object_or_404(RegistryModel, id=driver_id)
    
    # Get driver's current route assignments from both assignment types
    # First check for complete assignments (preferred method)
    complete_assignments = CompleteAssignment.objects.filter(
        driver=driver, is_active=True
    ).select_related('route', 'vehicle').order_by('-created_date')
    
    # Also check for direct driver-route assignments (legacy method)
    driver_route_assignments = DriverRouteAssignment.objects.filter(
        driver=driver, is_active=True
    ).select_related('route').order_by('-assigned_date')
    
    # Combine both types of assignments
    assignments = []
    
    # Add complete assignments (with additional vehicle info)
    for assignment in complete_assignments:
        assignments.append({
            'route': assignment.route,
            'assigned_date': assignment.created_date,
            'notes': assignment.notes,
            'assignment_type': 'complete',
            'vehicle': assignment.vehicle,
            'shift_type': assignment.shift_type,
        })
    
    # Add direct route assignments (legacy)
    for assignment in driver_route_assignments:
        assignments.append({
            'route': assignment.route,
            'assigned_date': assignment.assigned_date,
            'notes': assignment.notes,
            'assignment_type': 'route_only',
            'vehicle': None,
            'shift_type': None,
        })
    
    # Sort combined assignments by date (most recent first)
    assignments.sort(key=lambda x: x['assigned_date'], reverse=True)
    
    context = {
        'driver': driver,
        'assignments': assignments,
        'title': f'Driver Details - {driver.user.username}'
    }
    return render(request, 'driverAssignment/driver_detail.html', context)


# NEW HIERARCHICAL ASSIGNMENT VIEWS (Driver → Vehicle → Route)

@admin_or_controller_required
def assign_driver_to_vehicle_view(request):
    """Assign a driver to a vehicle - Only for admins and controllers"""
    if request.method == 'POST':
        form = DriverVehicleAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Driver {assignment.driver.user.username} assigned to vehicle {assignment.vehicle.vehicle_registration_no} successfully.')
            return redirect('driverAssignment:driver_vehicle_assignments')
    else:
        form = DriverVehicleAssignmentForm()
    
    context = {
        'form': form,
        'title': 'Assign Driver to Vehicle'
    }
    return render(request, 'driverAssignment/assign_driver_vehicle.html', context)


@admin_or_controller_required
def assign_vehicle_to_route_view(request):
    """Assign a vehicle to a route - Only for admins and controllers"""
    if request.method == 'POST':
        form = VehicleRouteAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Vehicle {assignment.vehicle.vehicle_registration_no} assigned to route {assignment.route.route_name} successfully.')
            return redirect('driverAssignment:vehicle_route_assignments')
    else:
        form = VehicleRouteAssignmentForm()
    
    context = {
        'form': form,
        'title': 'Assign Vehicle to Route'
    }
    return render(request, 'driverAssignment/assign_vehicle_route.html', context)


@admin_or_controller_required
def complete_assignment_view(request):
    """Create a complete assignment (Driver → Vehicle → Route) - Only for admins and controllers"""
    if request.method == 'POST':
        form = CompleteAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            
            # Log controller activity
            log_controller_activity(
                controller_user=request.user,
                action_type='complete_assignment',
                description=f'Created complete assignment: {assignment.driver.user.username} → {assignment.vehicle.vehicle_registration_no} → {assignment.route.route_name} ({assignment.get_shift_type_display()})',
                target_driver=assignment.driver,
                target_vehicle_id=assignment.vehicle.vehicle_registration_no,
                target_route_id=str(assignment.route.id),
                details={
                    'driver_username': assignment.driver.user.username,
                    'vehicle_registration': assignment.vehicle.vehicle_registration_no,
                    'route_name': assignment.route.route_name,
                    'shift_type': assignment.get_shift_type_display(),
                    'assignment_chain': f'{assignment.driver.user.username} → {assignment.vehicle.vehicle_registration_no} → {assignment.route.route_name}'
                }
            )
            update_daily_shift_status(request.user)
            
            messages.success(request, f'Complete assignment created: {assignment.driver.user.username} → {assignment.vehicle.vehicle_registration_no} → {assignment.route.route_name}')
            return redirect('driverAssignment:complete_assignments')
    else:
        form = CompleteAssignmentForm()
    
    context = {
        'form': form,
        'title': 'Create Complete Assignment'
    }
    return render(request, 'driverAssignment/complete_assignment.html', context)


def driver_vehicle_assignments_view(request):
    """View all driver-vehicle assignments"""
    assignments = DriverVehicleAssignment.objects.filter(is_active=True).select_related('driver__user', 'vehicle').order_by('-assigned_date')
    
    context = {
        'assignments': assignments,
        'title': 'Driver-Vehicle Assignments'
    }
    return render(request, 'driverAssignment/driver_vehicle_list.html', context)


def vehicle_route_assignments_view(request):
    """View all vehicle-route assignments"""
    assignments = VehicleRouteAssignment.objects.filter(is_active=True).select_related('vehicle', 'route').order_by('-assigned_date')
    
    context = {
        'assignments': assignments,
        'title': 'Vehicle-Route Assignments'
    }
    return render(request, 'driverAssignment/vehicle_route_list.html', context)


def complete_assignments_view(request):
    """View all complete assignments (Driver → Vehicle → Route)"""
    assignments = CompleteAssignment.objects.filter(is_active=True).select_related('driver__user', 'vehicle', 'route').order_by('-created_date')
    
    context = {
        'assignments': assignments,
        'title': 'Complete Assignments'
    }
    return render(request, 'driverAssignment/complete_assignments_list.html', context)


def remove_driver_vehicle_assignment(request, assignment_id):
    """Remove a driver-vehicle assignment"""
    assignment = get_object_or_404(DriverVehicleAssignment, id=assignment_id)
    
    if request.method == 'POST':
        driver_name = assignment.driver.user.username
        vehicle_reg = assignment.vehicle.vehicle_registration_no
        assignment.is_active = False
        assignment.save()
        messages.success(request, f'Assignment removed: {driver_name} from {vehicle_reg}')
        return redirect('driverAssignment:driver_vehicle_assignments')
    
    context = {
        'assignment': assignment,
        'title': 'Remove Driver-Vehicle Assignment'
    }
    return render(request, 'driverAssignment/confirm_remove_assignment.html', context)


def remove_vehicle_route_assignment(request, assignment_id):
    """Remove a vehicle-route assignment"""
    assignment = get_object_or_404(VehicleRouteAssignment, id=assignment_id)
    
    if request.method == 'POST':
        vehicle_reg = assignment.vehicle.vehicle_registration_no
        route_name = assignment.route.route_name
        assignment.is_active = False
        assignment.save()
        messages.success(request, f'Assignment removed: {vehicle_reg} from {route_name}')
        return redirect('driverAssignment:vehicle_route_assignments')
    
    context = {
        'assignment': assignment,
        'title': 'Remove Vehicle-Route Assignment'
    }
    return render(request, 'driverAssignment/confirm_remove_assignment.html', context)


def remove_complete_assignment(request, assignment_id):
    """Remove a complete assignment"""
    assignment = get_object_or_404(CompleteAssignment, id=assignment_id)
    
    if request.method == 'POST':
        assignment_str = str(assignment)
        assignment.is_active = False
        assignment.save()
        
        # Also deactivate related assignments
        DriverVehicleAssignment.objects.filter(
            driver=assignment.driver, vehicle=assignment.vehicle, is_active=True
        ).update(is_active=False)
        
        VehicleRouteAssignment.objects.filter(
            vehicle=assignment.vehicle, route=assignment.route, is_active=True
        ).update(is_active=False)
        
        messages.success(request, f'Complete assignment removed: {assignment_str}')
        return redirect('driverAssignment:complete_assignments')
    
    context = {
        'assignment': assignment,
        'title': 'Remove Complete Assignment'
    }
    return render(request, 'driverAssignment/confirm_remove_assignment.html', context)