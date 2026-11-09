from django.shortcuts import render, redirect, get_object_or_404
from register_login.models import RegistryModel, ClientModel, SiteModel, ControllerModel
from register_login.views import log_controller_activity, update_daily_shift_status
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from .models import DailyReportModel_Revenue, DailyReportModel_Cost, Route, FuelRateModel, Vehicle
from .forms import DailyReportModelForm_Revenue, DailyReportModelForm_Cost, RouteForm, FuelRateForm, VehicleForm
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows


#Admin Section 

#Active Clients in System

#Display Clients
def client_view(request):
    all_clients = ClientModel.objects.all()
    context={
        'all_clients':all_clients
    }
    return render(request, 'main/active_clients.html', context)

#Display Sites
def site_view(request):
    all_sites = SiteModel.objects.all()
    context={
        'all_sites':all_sites
    }
    return render(request, 'main/active_sites.html', context)




#Users in database
def active_users_view(request):
    search_query = request.GET.get('search', '')
    user_type_filter = request.GET.get('user_type', 'all')
    
    # Get all drivers and controllers
    drivers = RegistryModel.objects.select_related('user').all()
    controllers = ControllerModel.objects.select_related('user').all()
    
    # Create unified user data structure
    all_users_data = []
    
    # Add drivers
    for driver in drivers:
        user_data = {
            'user': driver.user,
            'type': 'Driver',
            'profile': driver,
            'mine': driver.mine,
            'driver_license_no': driver.driver_license_no,
            'driver_license_expiry': driver.driver_license_expiry,
            'induction_license_no': driver.induction_license_no,
            'induction_license_expiry': driver.induction_license_expiry,
            'phone_number': None,
            'department': None,
            'employee_id': None,
        }
        all_users_data.append(user_data)
    
    # Add controllers
    for controller in controllers:
        user_data = {
            'user': controller.user,
            'type': 'Controller',
            'profile': controller,
            'mine': None,
            'driver_license_no': None,
            'driver_license_expiry': None,
            'induction_license_no': None,
            'induction_license_expiry': None,
            'phone_number': controller.phone_number,
            'department': controller.department,
            'employee_id': controller.employee_id,
        }
        all_users_data.append(user_data)
    
    # Apply user type filter
    if user_type_filter == 'drivers':
        all_users_data = [u for u in all_users_data if u['type'] == 'Driver']
    elif user_type_filter == 'controllers':
        all_users_data = [u for u in all_users_data if u['type'] == 'Controller']
    elif user_type_filter == 'admin':
        # Add admin users (users with is_staff=True)
        from django.contrib.auth.models import User
        admin_users = User.objects.filter(is_staff=True)
        admin_users_data = []
        for admin in admin_users:
            # Check if admin is not already included as driver or controller
            is_driver = RegistryModel.objects.filter(user=admin).exists()
            is_controller = ControllerModel.objects.filter(user=admin).exists()
            if not is_driver and not is_controller:
                user_data = {
                    'user': admin,
                    'type': 'Admin',
                    'profile': None,
                    'mine': None,
                    'driver_license_no': None,
                    'driver_license_expiry': None,
                    'induction_license_no': None,
                    'induction_license_expiry': None,
                    'phone_number': None,
                    'department': None,
                    'employee_id': None,
                }
                admin_users_data.append(user_data)
        all_users_data = admin_users_data
    
    # Apply search filters if search query exists
    if search_query:
        filtered_users = []
        for user_data in all_users_data:
            user = user_data['user']
            if (search_query.lower() in (user.username or '').lower() or
                search_query.lower() in (user.first_name or '').lower() or
                search_query.lower() in (user.last_name or '').lower() or
                search_query.lower() in (user_data.get('mine') or '').lower() or
                search_query.lower() in (user_data.get('driver_license_no') or '').lower() or
                search_query.lower() in (user_data.get('phone_number') or '').lower() or
                search_query.lower() in (user_data.get('department') or '').lower() or
                search_query.lower() in (user_data.get('employee_id') or '').lower()):
                filtered_users.append(user_data)
        all_users_data = filtered_users
    
    # Sort by username for consistent display
    all_users_data.sort(key=lambda x: x['user'].username)
    
    context = {
        'all_users_data': all_users_data,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'total_users': len(all_users_data),
        'driver_count': len([u for u in all_users_data if u['type'] == 'Driver']),
        'controller_count': len([u for u in all_users_data if u['type'] == 'Controller']),
        'admin_count': len([u for u in all_users_data if u['type'] == 'Admin']),
    }
    return render(request, 'main/active_users.html', context)


def edit_user_view(request, user_id):
    """Edit user details"""
    from django.shortcuts import get_object_or_404, redirect
    from register_login.forms import EditDriverForm
    
    registry_user = get_object_or_404(RegistryModel, id=user_id)
    
    if request.method == 'POST':
        form = EditDriverForm(request.POST, instance=registry_user, user=registry_user.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {registry_user.user.username} updated successfully.')
            return redirect('main:active_users')
    else:
        form = EditDriverForm(instance=registry_user, user=registry_user.user)
    
    context = {
        'form': form,
        'user': registry_user,
        'title': f'Edit User: {registry_user.user.username}'
    }
    return render(request, 'main/edit_user.html', context)


def delete_user_view(request, user_id):
    """Delete user"""
    from django.shortcuts import get_object_or_404, redirect
    
    try:
        registry_user = get_object_or_404(RegistryModel, id=user_id)
    except:
        messages.error(request, f'User with ID {user_id} not found or has already been deleted.')
        return redirect('main:active_users')
    
    if request.method == 'POST':
        username = registry_user.user.username
        registry_user.user.delete()  # This will also delete the RegistryModel due to CASCADE
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('main:active_users')
    
    context = {
        'user': registry_user,
        'title': f'Delete User: {registry_user.user.username}'
    }
    return render(request, 'main/confirm_delete_user.html', context)









#Daily Report Form for Revenue
def daily_rev_report_form_view(request):
    if request.method == "POST":
        form = DailyReportModelForm_Revenue(request.POST, user=request.user)
        if form.is_valid():
            revenue_report = form.save(commit=False)
            
            # Handle driver assignment for controllers and admins
            driver_assignment = form.cleaned_data.get('driver_assignment')
            if driver_assignment:
                # Controller or admin is filling out report for a driver
                revenue_report.driver = driver_assignment
                messages.success(request, f'Revenue report submitted for driver: {driver_assignment.user.username}')
            else:
                # Try to associate with current user if they are authenticated and exist in RegistryModel
                if request.user.is_authenticated:
                    try:
                        driver = RegistryModel.objects.get(user=request.user)
                        revenue_report.driver = driver
                    except RegistryModel.DoesNotExist:
                        # If user is not in RegistryModel, leave driver as None
                        pass
            
            # First save the revenue report to get an ID (skip prediction calculation)
            revenue_report.save(skip_prediction=True)
            
            # Now that we have an ID, we can handle dynamic route selections
            active_routes = Route.objects.filter(is_active=True)
            selected_routes = []
            for route in active_routes:
                field_name = f'route_{route.id}'
                if form.cleaned_data.get(field_name):
                    selected_routes.append(route)
            
            # Add all selected routes at once
            if selected_routes:
                revenue_report.completed_routes.set(selected_routes)
            
            # Now save again with predicted revenue calculation
            revenue_report.save()
            
            # Log controller activity if applicable
            if driver_assignment:
                # Controller/admin submitted for another driver
                log_controller_activity(
                    controller_user=request.user,
                    action_type='daily_revenue_report',
                    description=f'Submitted daily revenue report for driver {driver_assignment.user.username} - Fleet: {revenue_report.fleet_no}, Loads: {revenue_report.no_of_loads}',
                    target_driver=driver_assignment,
                    details={
                        'fleet_no': revenue_report.fleet_no,
                        'vehicle_no': revenue_report.vehicle_no,
                        'no_of_loads': revenue_report.no_of_loads,
                        'routes': [route.route_name for route in selected_routes],
                        'submitted_for_driver': driver_assignment.user.username
                    }
                )
                update_daily_shift_status(request.user)
            
            return redirect('main:home')
    else:
        form = DailyReportModelForm_Revenue(user=request.user)

    context = {
        'form': form
    }

    return render(request, 'main/daily_rev_report.html', context)

#Daily Report Form for Cost - REMOVED DUPLICATE (see line ~889)
    

#Revenue method for Banele
def revenue_view(request):
    search_query = request.GET.get('search', '')
    table_data = DailyReportModel_Revenue.objects.all().order_by('date', 'id')
    
    if search_query:
        table_data = table_data.filter(
            models.Q(fleet_no__icontains=search_query) |
            models.Q(vehicle_no__icontains=search_query)
        )
    
    if request.method == "POST":
        if "clear" in request.POST:
            DailyReportModel_Revenue.objects.all().delete()  # Clear the reports
            return redirect('main:revenue')
    
    # Calculate revenue, variance and predicted revenue for each report
    total_revenue = Decimal('0.00')
    total_planned = Decimal('0.00')
    total_variance = Decimal('0.00')
    total_predicted = Decimal('0.00')
    
    previous_predicted = Decimal('0.00')
    
    for index, report in enumerate(table_data):
        # Set revenue based on completed routes
        report.revenue = report.total_revenue
        
        # Calculate predicted revenue based on new logic
        if index == 0:
            # First entry: predicted revenue = actual revenue
            report.predicted = report.revenue
        else:
            # Subsequent entries: prev_predicted + (latest_revenue + prev_predicted)/2
            report.predicted = previous_predicted + (report.revenue + previous_predicted) / 2
        
        previous_predicted = report.predicted
        
        # Calculate the planned revenue that will be displayed in the template
        if report.completed_routes.exists():
            report_planned = Decimal('0.00')
            for route in report.completed_routes.all():
                report_planned += route.planned_revenue
        else:
            report_planned = report.planned_rev
        
        # Set a new attribute for the template to display
        report.display_planned_revenue = report_planned
        
        # Calculate variance as simple Revenue - Planned Revenue
        report.variance = report.revenue - report_planned
        
        # Add to totals
        total_revenue += report.revenue
        total_planned += report_planned
        total_variance += report.variance
        total_predicted += report.predicted
    
    context = {
        'table_data': table_data,
        'total_revenue': total_revenue,
        'total_planned': total_planned,
        'total_variance': total_variance,
        'total_predicted': total_predicted,
        'search_query': search_query,
    }
    
    return render(request, 'main/revenue.html', context)

#Cost Table
def cost_view(request):
    search_query = request.GET.get('search', '')
    table_data = DailyReportModel_Cost.objects.all().order_by('date', 'id')
    
    if search_query:
        table_data = table_data.filter(
            models.Q(driver__user__username__icontains=search_query) |
            models.Q(driver__vehicle_registration_no__icontains=search_query) |
            models.Q(fleet_no__icontains=search_query)
        )
    
    if request.method == "POST":
        if "clear" in request.POST:
            DailyReportModel_Cost.objects.all().delete()  # Clear the reports
            return redirect('main:cost')
    
    # Calculate predicted costs for each report
    previous_predicted = Decimal('0.00')
    
    for index, report in enumerate(table_data):
        # Calculate actual cost (fuel cost + imported costs)
        report.actual_cost = report.fuel_cost() + (report.imported_costs or Decimal('0.00'))
        
        # Calculate predicted cost based on new logic
        if index == 0:
            # First entry: predicted cost = actual cost
            report.calculated_predicted_cost = report.actual_cost
        else:
            # Subsequent entries: prev_predicted + (latest_cost + prev_predicted)/2
            report.calculated_predicted_cost = previous_predicted + (report.actual_cost + previous_predicted) / 2
        
        previous_predicted = report.calculated_predicted_cost
    
    context ={
        'table_data':table_data,
        'search_query': search_query,
    }
    return render(request, 'main/cost.html', context)

#Individual Driver Cost View
def driver_cost_view(request, driver_id):
    driver = RegistryModel.objects.get(id=driver_id)
    table_data = DailyReportModel_Cost.objects.filter(driver=driver)
    
    if request.method == "POST":
        if "clear" in request.POST:
            DailyReportModel_Cost.objects.filter(driver=driver).delete()
            return redirect('main:driver_cost', driver_id=driver_id)
    
    context = {
        'table_data': table_data,
        'driver': driver
    }
    return render(request, 'main/driver_cost.html', context)

#Driver List for Cost Pages
def driver_cost_list_view(request):
    drivers = RegistryModel.objects.all()
    context = {
        'drivers': drivers
    }
    return render(request, 'main/driver_cost_list.html', context)
    
    

#License warning function 
def expiry_warning(request):
    profiles = RegistryModel.objects.all()  # Fetch all profiles (Profiles of all users active in the system)
    current_date = datetime.now().date()
    warnings = []

    for profile in profiles:
        # Check each license expiry date
        if profile.driver_license_expiry and profile.driver_license_expiry <= current_date + timedelta(days=30):
            warnings.append({
                'type': 'Driver License',
                'number': profile.driver_license_no,
                'expiry': profile.driver_license_expiry
            })

        if profile.induction_license_expiry and profile.induction_license_expiry <= current_date + timedelta(days=30):
            warnings.append({
                'type': 'Induction License',
                'number': profile.induction_license_no,
                'expiry': profile.induction_license_expiry
            })

        if profile.vehicle_registration_expiry and profile.vehicle_registration_expiry <= current_date + timedelta(days=30):
            warnings.append({
                'type': 'Vehicle Registration',
                'number': profile.vehicle_registration_no,
                'expiry': profile.vehicle_registration_expiry
            })

    context = {
        'warnings': warnings
    }

    return render(request, 'main/home.html', context)

#home view render 
def home_view(request):
    """Home page with summary of expiry warnings"""
    profiles = RegistryModel.objects.all()
    current_date = datetime.now().date()
    warning_count = 0
    
    # Count drivers with expiring items
    for profile in profiles:
        if profile.driver_license_expiry and profile.driver_license_expiry <= current_date + timedelta(days=30):
            warning_count += 1
        elif profile.induction_license_expiry and profile.induction_license_expiry <= current_date + timedelta(days=30):
            warning_count += 1
    
    context = {
        'warning_count': warning_count
    }
    return render(request, 'main/home.html', context)


# Route Management Views




# Driver Report Views

def driver_cost_list_view(request):
    """Display list of drivers with search functionality"""
    search_query = request.GET.get('search', '')
    drivers = RegistryModel.objects.all()
    
    if search_query:
        drivers = drivers.filter(
            models.Q(user__username__icontains=search_query) |
            models.Q(vehicle_registration_no__icontains=search_query)
        )
    
    context = {
        'drivers': drivers,
        'search_query': search_query,
    }
    return render(request, 'main/driver_cost_list.html', context)

def driver_cost_view(request, driver_id):
    """Display individual driver's cost reports"""
    driver = get_object_or_404(RegistryModel, id=driver_id)
    table_data = DailyReportModel_Cost.objects.filter(driver=driver).order_by('date', 'id')
    
    if request.method == "POST":
        if "clear" in request.POST:
            DailyReportModel_Cost.objects.filter(driver=driver).delete()
            messages.success(request, f"All cost reports for {driver.user.username} have been cleared.")
            return redirect('main:driver_cost', driver_id=driver_id)
    
    # Calculate totals and predicted costs
    total_fuel_cost = Decimal('0.00')
    total_imported_costs = Decimal('0.00')
    total_cost = Decimal('0.00')
    total_predicted_cost = Decimal('0.00')
    
    previous_predicted = Decimal('0.00')
    
    for index, report in enumerate(table_data):
        # Calculate actual cost (fuel cost + imported costs)
        fuel_cost = report.fuel_cost()
        imported_cost = report.imported_costs or Decimal('0.00')
        report.actual_cost = fuel_cost + imported_cost
        
        # Calculate predicted cost based on new logic
        if index == 0:
            # First entry: predicted cost = actual cost
            report.calculated_predicted_cost = report.actual_cost
        else:
            # Subsequent entries: prev_predicted + (latest_cost + prev_predicted)/2
            report.calculated_predicted_cost = previous_predicted + (report.actual_cost + previous_predicted) / 2
        
        previous_predicted = report.calculated_predicted_cost
        
        # Add to totals
        total_fuel_cost += fuel_cost
        total_imported_costs += imported_cost
        total_cost += report.actual_cost
        total_predicted_cost += report.calculated_predicted_cost
    
    context = {
        'driver': driver,
        'table_data': table_data,
        'total_fuel_cost': total_fuel_cost,
        'total_imported_costs': total_imported_costs,
        'total_cost': total_cost,
        'total_predicted_cost': total_predicted_cost,
    }
    return render(request, 'main/driver_cost.html', context)

def driver_revenue_list_view(request):
    """Display list of drivers for revenue reports with search functionality"""
    search_query = request.GET.get('search', '')
    drivers = RegistryModel.objects.all()
    
    if search_query:
        drivers = drivers.filter(
            models.Q(user__username__icontains=search_query) |
            models.Q(vehicle_registration_no__icontains=search_query)
        )
    
    context = {
        'drivers': drivers,
        'search_query': search_query,
    }
    return render(request, 'main/driver_revenue_list.html', context)

def driver_revenue_view(request, driver_id):
    """Display individual driver's revenue reports"""
    driver = get_object_or_404(RegistryModel, id=driver_id)
    
    # Get revenue reports for this specific driver
    # Since we now have a direct driver relationship, we can filter by driver
    table_data = DailyReportModel_Revenue.objects.filter(driver=driver).order_by('date', 'id')
    
    # If no reports found with direct driver relationship, fall back to username matching
    if not table_data.exists():
        query_filters = models.Q()
        if driver.user.username:
            # Check if any revenue reports have fleet/vehicle numbers that contain the username
            query_filters |= models.Q(fleet_no__icontains=driver.user.username)
            query_filters |= models.Q(vehicle_no__icontains=driver.user.username)
            table_data = DailyReportModel_Revenue.objects.filter(query_filters).order_by('id')
    
    if request.method == "POST":
        if "clear" in request.POST:
            table_data.delete()
            messages.success(request, f"All revenue reports for {driver.user.username} have been cleared.")
            return redirect('main:driver_revenue', driver_id=driver_id)
    
    # Calculate totals and predicted revenue
    total_revenue = Decimal('0.00')
    total_planned = Decimal('0.00')
    total_variance = Decimal('0.00')
    total_predicted = Decimal('0.00')
    
    previous_predicted = Decimal('0.00')
    
    for index, report in enumerate(table_data):
        report.revenue = report.total_revenue
        
        # Calculate predicted revenue based on new logic
        if index == 0:
            # First entry: predicted revenue = actual revenue
            report.predicted = report.revenue
        else:
            # Subsequent entries: prev_predicted + (latest_revenue + prev_predicted)/2
            report.predicted = previous_predicted + (report.revenue + previous_predicted) / 2
        
        previous_predicted = report.predicted
        
        # Calculate the planned revenue that will be displayed in the template
        if report.completed_routes.exists():
            report_planned = Decimal('0.00')
            for route in report.completed_routes.all():
                report_planned += route.planned_revenue
        else:
            report_planned = report.planned_rev
        
        # Set a new attribute for the template to display
        report.display_planned_revenue = report_planned
        
        # Calculate variance as simple Revenue - Planned Revenue
        report.variance = report.revenue - report_planned
        
        total_revenue += report.revenue
        total_planned += report_planned
        total_variance += report.variance
        total_predicted += report.predicted
    
    # Get the latest predicted revenue for this driver
    latest_predicted_revenue = DailyReportModel_Revenue.get_latest_predicted_revenue(driver=driver)
    
    context = {
        'driver': driver,
        'table_data': table_data,
        'total_revenue': total_revenue,
        'total_planned': total_planned,
        'total_variance': total_variance,
        'total_predicted': total_predicted,
        'latest_predicted_revenue': latest_predicted_revenue,
    }
    return render(request, 'main/driver_revenue.html', context)


# Form Views for Daily Reports


def daily_cost_report_form_view(request):
    """Handle daily cost report form submission"""
    if request.method == "POST":
        form = DailyReportModelForm_Cost(request.POST, user=request.user)
        if form.is_valid():
            cost_report = form.save(commit=False)
            
            # Handle driver assignment for controllers and admins
            driver_assignment = form.cleaned_data.get('driver_assignment')
            if driver_assignment:
                # Controller or admin is filling out report for a driver
                cost_report.driver = driver_assignment
                messages.success(request, f'Cost report submitted for driver: {driver_assignment.user.username}')
            else:
                # Try to associate with current user if they exist in RegistryModel
                try:
                    driver = RegistryModel.objects.get(user=request.user)
                    cost_report.driver = driver
                except RegistryModel.DoesNotExist:
                    # If user is not in RegistryModel, leave driver as None
                    pass
            
            # Ensure we have a fuel rate to use
            active_fuel_rate = FuelRateModel.get_active_rate()
            if not active_fuel_rate:
                # Create a default fuel rate if none exists
                from django.utils import timezone
                active_fuel_rate = FuelRateModel.objects.create(
                    fuel_rate=20.00,  # Default rate
                    name="Default Fuel Rate",
                    is_active=True,
                    created_at=timezone.now()
                )
                messages.info(request, "A default fuel rate was created. Please update it in Fuel Rate Management.")
            
            cost_report.fuel_rate_set = active_fuel_rate
            cost_report.save()
            
            # Log controller activity if applicable
            if driver_assignment:
                # Controller/admin submitted for another driver
                log_controller_activity(
                    controller_user=request.user,
                    action_type='daily_cost_report',
                    description=f'Submitted daily cost report for driver {driver_assignment.user.username} - Fleet: {cost_report.fleet_no}, Fuel: {cost_report.fuel_requested}L',
                    target_driver=driver_assignment,
                    details={
                        'fleet_no': cost_report.fleet_no,
                        'fuel_requested': cost_report.fuel_requested,
                        'slip_no': cost_report.slip_no,
                        'submitted_for_driver': driver_assignment.user.username
                    }
                )
                update_daily_shift_status(request.user)
            
            messages.success(request, "Cost report submitted successfully!")
            return redirect('main:cost')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = DailyReportModelForm_Cost(user=request.user)
    
    context = {
        'form': form,
        'title': 'Daily Cost Report'
    }
    return render(request, 'main/daily_cost_report.html', context)


# Fuel Rate Management Views

def fuel_rate_management_view(request):
    """Manage fuel rates for all trucks in the system"""
    current_fuel_rate = FuelRateModel.get_active_rate()
    all_fuel_rates = FuelRateModel.objects.all().order_by('-created_at')
    
    # Get statistics about trucks affected
    affected_reports_count = DailyReportModel_Cost.objects.count()
    recent_reports_count = DailyReportModel_Cost.objects.filter(
        date__gte=datetime.now().date() - timedelta(days=30)
    ).count()
    
    if request.method == "POST":
        form = FuelRateForm(request.POST)
        if form.is_valid():
            # Save the new fuel rate and set it as active
            new_fuel_rate = form.save(commit=False)
            new_fuel_rate.is_active = True
            new_fuel_rate.save()
            
            messages.success(
                request, 
                f"Fuel rate successfully updated to R{new_fuel_rate.fuel_rate} per litre. "
                f"This will apply to all new cost calculations system-wide."
            )
            return redirect('main:fuel_rate_management')
    else:
        # Pre-populate form with current fuel rate if it exists
        if current_fuel_rate:
            form = FuelRateForm(initial={
                'fuel_rate': current_fuel_rate.fuel_rate,
                'name': f"Updated Fuel Rate - {datetime.now().strftime('%Y-%m-%d')}"
            })
        else:
            form = FuelRateForm()
    
    context = {
        'form': form,
        'current_fuel_rate': current_fuel_rate,
        'all_fuel_rates': all_fuel_rates,
        'affected_reports_count': affected_reports_count,
        'recent_reports_count': recent_reports_count,
        'title': 'Fuel Rate Management'
    }
    return render(request, 'main/fuel_rate_management.html', context)

def delete_fuel_rate_view(request, rate_id):
    """Delete a specific fuel rate (admin only)"""
    fuel_rate = get_object_or_404(FuelRateModel, id=rate_id)
    
    # Check if this fuel rate is being used by any cost reports
    reports_using_rate = DailyReportModel_Cost.objects.filter(fuel_rate_set=fuel_rate).count()
    
    if request.method == "POST":
        if reports_using_rate > 0:
            messages.error(
                request, 
                f"Cannot delete fuel rate '{fuel_rate.name}' because it is being used by {reports_using_rate} cost reports."
            )
        else:
            fuel_rate_name = fuel_rate.name
            fuel_rate.delete()
            messages.success(request, f"Fuel rate '{fuel_rate_name}' has been deleted.")
        
        return redirect('main:fuel_rate_management')
    
    context = {
        'fuel_rate': fuel_rate,
        'reports_using_rate': reports_using_rate,
        'title': f'Delete Fuel Rate - {fuel_rate.name}'
    }
    return render(request, 'main/confirm_delete_fuel_rate.html', context)

def activate_fuel_rate_view(request, rate_id):
    """Activate a specific fuel rate"""
    fuel_rate = get_object_or_404(FuelRateModel, id=rate_id)
    
    if request.method == "POST":
        # Set this fuel rate as active (the model's save method will deactivate others)
        fuel_rate.is_active = True
        fuel_rate.save()
        
        messages.success(
            request, 
            f"Fuel rate '{fuel_rate.name}' (R{fuel_rate.fuel_rate} per litre) is now active and will be used for all new cost calculations."
        )
        return redirect('main:fuel_rate_management')
    
    # For GET requests, show confirmation
    context = {
        'fuel_rate': fuel_rate,
        'title': f'Activate Fuel Rate - {fuel_rate.name}'
    }
    return render(request, 'main/confirm_activate_fuel_rate.html', context)

# Driver Expiry Warning Views

def driver_expiry_warnings_view(request):
    """Display all drivers with expiring documents"""
    profiles = RegistryModel.objects.all()
    current_date = datetime.now().date()
    warning_threshold = current_date + timedelta(days=30)
    
    drivers_with_warnings = []
    
    for profile in profiles:
        warnings = []
        
        # Check driver license expiry
        if profile.driver_license_expiry and profile.driver_license_expiry <= warning_threshold:
            days_until_expiry = (profile.driver_license_expiry - current_date).days
            warnings.append({
                'type': 'Driver License',
                'number': profile.driver_license_no or 'Not provided',
                'expiry': profile.driver_license_expiry,
                'days_until': days_until_expiry,
                'is_expired': days_until_expiry < 0,
                'is_critical': days_until_expiry <= 7
            })
        
        # Check induction license expiry
        if profile.induction_license_expiry and profile.induction_license_expiry <= warning_threshold:
            days_until_expiry = (profile.induction_license_expiry - current_date).days
            warnings.append({
                'type': 'Induction License',
                'number': profile.induction_license_no or 'Not provided',
                'expiry': profile.induction_license_expiry,
                'days_until': days_until_expiry,
                'is_expired': days_until_expiry < 0,
                'is_critical': days_until_expiry <= 7
            })
        
        # Vehicle registration is not tracked in RegistryModel
        # Vehicle expiry tracking would need to be implemented in Vehicle model if needed
        
        if warnings:
            drivers_with_warnings.append({
                'driver': profile,
                'warnings': warnings,
                'total_warnings': len(warnings),
                'has_expired': any(w['is_expired'] for w in warnings),
                'has_critical': any(w['is_critical'] for w in warnings)
            })
    
    # Sort by most critical first (expired, then critical, then by expiry date)
    drivers_with_warnings.sort(key=lambda x: (
        not x['has_expired'],  # Expired first
        not x['has_critical'],  # Critical second
        min(w['days_until'] for w in x['warnings'])  # Closest expiry third
    ))
    
    context = {
        'drivers_with_warnings': drivers_with_warnings,
        'total_drivers_affected': len(drivers_with_warnings),
        'total_warnings': sum(d['total_warnings'] for d in drivers_with_warnings),
        'title': 'Driver Expiry Warnings'
    }
    return render(request, 'main/driver_expiry_warnings.html', context)

def driver_expiry_detail_view(request, driver_id):
    """Display detailed expiry information for a specific driver"""
    driver = get_object_or_404(RegistryModel, id=driver_id)
    current_date = datetime.now().date()
    warning_threshold = current_date + timedelta(days=30)
    
    all_documents = []
    
    # Driver License
    if driver.driver_license_no or driver.driver_license_expiry:
        days_until_expiry = None
        if driver.driver_license_expiry:
            days_until_expiry = (driver.driver_license_expiry - current_date).days
        
        all_documents.append({
            'type': 'Driver License',
            'number': driver.driver_license_no or 'Not provided',
            'expiry': driver.driver_license_expiry,
            'days_until': days_until_expiry,
            'days_expired': abs(days_until_expiry) if days_until_expiry is not None and days_until_expiry < 0 else 0,
            'is_expired': days_until_expiry is not None and days_until_expiry < 0,
            'is_critical': days_until_expiry is not None and days_until_expiry <= 7,
            'is_warning': days_until_expiry is not None and days_until_expiry <= 30,
            'icon': 'bi-card-text'
        })
    
    # Induction License
    if driver.induction_license_no or driver.induction_license_expiry:
        days_until_expiry = None
        if driver.induction_license_expiry:
            days_until_expiry = (driver.induction_license_expiry - current_date).days
            
        all_documents.append({
            'type': 'Induction License',
            'number': driver.induction_license_no or 'Not provided',
            'expiry': driver.induction_license_expiry,
            'days_until': days_until_expiry,
            'days_expired': abs(days_until_expiry) if days_until_expiry is not None and days_until_expiry < 0 else 0,
            'is_expired': days_until_expiry is not None and days_until_expiry < 0,
            'is_critical': days_until_expiry is not None and days_until_expiry <= 7,
            'is_warning': days_until_expiry is not None and days_until_expiry <= 30,
            'icon': 'bi-shield-check'
        })
    
    # Vehicle Registration is not tracked in RegistryModel
    # Vehicle registration tracking would need to be implemented in Vehicle model if needed
    
    context = {
        'driver': driver,
        'documents': all_documents,
        'title': f'Expiry Details - {driver.user.username}'
    }
    return render(request, 'main/driver_expiry_detail.html', context)


# AI Assistant View
def ai_assistant_view(request):
    """AI Assistant control page for Makgothi Jnr"""
    context = {
        'title': 'AI Assistant - Makgothi Jnr'
    }
    return render(request, 'main/ai_assistant.html', context)


# Vehicle Management Views

def vehicle_list_view(request):
    """Display all vehicles with search functionality"""
    search_query = request.GET.get('search', '')
    
    # Start with all vehicles and prefetch related assignments
    vehicles = Vehicle.objects.all().prefetch_related(
        'driver_assignments__driver__user',
        'route_assignments__route'
    )
    
    # Apply search filters if search query exists
    if search_query:
        vehicles = vehicles.filter(
            models.Q(vehicle_make__icontains=search_query) |
            models.Q(vehicle_registration_no__icontains=search_query)
        ).distinct()
    
    # Order by make and registration number
    vehicles = vehicles.order_by('vehicle_make', 'vehicle_registration_no')
    
    # Add assignment information to each vehicle
    from driverAssignment.models import DriverVehicleAssignment, VehicleRouteAssignment
    vehicles_with_assignments = []
    
    for vehicle in vehicles:
        # Get current driver assignment
        current_driver_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).select_related('driver__user').first()
        
        # Get current route assignment
        current_route_assignment = VehicleRouteAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).select_related('route').first()
        
        # Calculate days until registration expiry
        current_date = datetime.now().date()
        days_until_expiry = None
        if vehicle.vehicle_registration_expiry:
            days_until_expiry = (vehicle.vehicle_registration_expiry - current_date).days
        
        vehicle_data = {
            'vehicle': vehicle,
            'current_driver': current_driver_assignment.driver if current_driver_assignment else None,
            'current_route': current_route_assignment.route if current_route_assignment else None,
            'days_until_expiry': days_until_expiry,
            'days_expired': abs(days_until_expiry) if days_until_expiry is not None and days_until_expiry < 0 else 0,
            'is_expired': days_until_expiry is not None and days_until_expiry < 0,
            'is_critical': days_until_expiry is not None and days_until_expiry <= 7,
            'is_warning': days_until_expiry is not None and days_until_expiry <= 30,
        }
        vehicles_with_assignments.append(vehicle_data)
    
    context = {
        'vehicles_data': vehicles_with_assignments,
        'search_query': search_query,
        'total_vehicles': len(vehicles_with_assignments),
        'title': 'Vehicle Management'
    }
    return render(request, 'main/vehicle_list.html', context)


def vehicle_add_view(request):
    """Add a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle {vehicle.vehicle_registration_no} added successfully.')
            return redirect('main:vehicle_list')
    else:
        form = VehicleForm()
    
    context = {
        'form': form,
        'title': 'Add New Vehicle'
    }
    return render(request, 'main/vehicle_form.html', context)


def vehicle_edit_view(request, vehicle_id):
    """Edit an existing vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle {vehicle.vehicle_registration_no} updated successfully.')
            return redirect('main:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    
    context = {
        'form': form,
        'vehicle': vehicle,
        'title': f'Edit Vehicle: {vehicle.vehicle_registration_no}'
    }
    return render(request, 'main/vehicle_form.html', context)


def vehicle_delete_view(request, vehicle_id):
    """Delete a vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        vehicle_reg = vehicle.vehicle_registration_no
        vehicle.delete()
        messages.success(request, f'Vehicle {vehicle_reg} deleted successfully.')
        return redirect('main:vehicle_list')
    
    context = {
        'vehicle': vehicle,
        'title': f'Delete Vehicle: {vehicle.vehicle_registration_no}'
    }
    return render(request, 'main/vehicle_delete.html', context)


def vehicle_detail_view(request, vehicle_id):
    """View vehicle details and FleetCam link"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    # Get current driver assignment
    from driverAssignment.models import DriverVehicleAssignment, VehicleRouteAssignment
    
    current_driver_assignment = DriverVehicleAssignment.objects.filter(
        vehicle=vehicle, is_active=True
    ).first()
    
    current_route_assignment = VehicleRouteAssignment.objects.filter(
        vehicle=vehicle, is_active=True
    ).first()
    
    # Calculate days until registration expiry
    current_date = datetime.now().date()
    days_until_expiry = None
    if vehicle.vehicle_registration_expiry:
        days_until_expiry = (vehicle.vehicle_registration_expiry - current_date).days
    
    context = {
        'vehicle': vehicle,
        'current_driver': current_driver_assignment.driver if current_driver_assignment else None,
        'current_route': current_route_assignment.route if current_route_assignment else None,
        'days_until_expiry': days_until_expiry,
        'days_expired': abs(days_until_expiry) if days_until_expiry is not None and days_until_expiry < 0 else 0,
        'is_expired': days_until_expiry is not None and days_until_expiry < 0,
        'is_critical': days_until_expiry is not None and days_until_expiry <= 7,
        'is_warning': days_until_expiry is not None and days_until_expiry <= 30,
        'title': f'Vehicle Details: {vehicle.vehicle_registration_no}'
    }
    return render(request, 'main/vehicle_detail.html', context)


def vehicle_fleetcam_view(request, vehicle_id):
    """Redirect to FleetCam monitoring for specific vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if not vehicle.fleetcam_link:
        messages.error(request, f'No FleetCam link configured for vehicle {vehicle.vehicle_registration_no}')
        return redirect('main:vehicle_detail', vehicle_id=vehicle_id)
    
    # Redirect directly to the FleetCam link
    return redirect(vehicle.fleetcam_link)


# Route Management Views

def route_list_view(request):
    """Display all routes with search functionality"""
    search_query = request.GET.get('search', '')
    
    # Start with all routes
    routes = Route.objects.all()
    
    # Apply search filters if search query exists
    if search_query:
        routes = routes.filter(
            models.Q(route_name__icontains=search_query) |
            models.Q(start__icontains=search_query) |
            models.Q(finish__icontains=search_query)
        ).distinct()
    
    # Order by route name
    routes = routes.order_by('route_name')
    
    # Add assignment information to each route
    from driverAssignment.models import VehicleRouteAssignment
    routes_with_assignments = []
    
    for route in routes:
        # Get current vehicle assignments for this route
        vehicle_assignments = VehicleRouteAssignment.objects.filter(
            route=route, is_active=True
        ).select_related('vehicle').count()
        
        route_data = {
            'route': route,
            'assigned_vehicles_count': vehicle_assignments,
        }
        routes_with_assignments.append(route_data)
    
    # Calculate active and inactive counts
    active_routes_count = sum(1 for route_data in routes_with_assignments if route_data['route'].is_active)
    inactive_routes_count = len(routes_with_assignments) - active_routes_count

    context = {
        'routes_data': routes_with_assignments,
        'search_query': search_query,
        'total_routes': len(routes_with_assignments),
        'active_routes_count': active_routes_count,
        'inactive_routes_count': inactive_routes_count,
        'title': 'Route Management'
    }
    return render(request, 'main/route_list.html', context)


def route_add_view(request):
    """Add a new route"""
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f'Route {route.route_name} added successfully.')
            return redirect('main:route_list')
    else:
        form = RouteForm()
    
    context = {
        'form': form,
        'title': 'Add New Route'
    }
    return render(request, 'main/route_form.html', context)


def route_edit_view(request, route_id):
    """Edit an existing route"""
    route = get_object_or_404(Route, id=route_id)
    
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            route = form.save()
            messages.success(request, f'Route {route.route_name} updated successfully.')
            return redirect('main:route_list')
    else:
        form = RouteForm(instance=route)
    
    context = {
        'form': form,
        'route': route,
        'title': f'Edit Route: {route.route_name}'
    }
    return render(request, 'main/route_form.html', context)


def route_delete_view(request, route_id):
    """Delete a route"""
    route = get_object_or_404(Route, id=route_id)
    
    if request.method == 'POST':
        route_name = route.route_name
        route.delete()
        messages.success(request, f'Route {route_name} deleted successfully.')
        return redirect('main:route_list')
    
    context = {
        'route': route,
        'title': f'Delete Route: {route.route_name}'
    }
    return render(request, 'main/route_delete.html', context)


def route_toggle_status_view(request, route_id):
    """Toggle route active/inactive status"""
    route = get_object_or_404(Route, id=route_id)
    
    route.is_active = not route.is_active
    route.save()
    
    status = "activated" if route.is_active else "deactivated"
    messages.success(request, f'Route {route.route_name} has been {status}.')
    
    return redirect('main:route_list')


def route_vehicle_assignments_view(request, route_id):
    """View and manage vehicle assignments for a specific route"""
    route = get_object_or_404(Route, id=route_id)
    
    from driverAssignment.models import VehicleRouteAssignment, DriverVehicleAssignment, CompleteAssignment
    
    # Handle POST requests for vehicle assignment/removal
    if request.method == 'POST':
        action = request.POST.get('action')
        vehicle_id = request.POST.get('vehicle_id')
        
        if vehicle_id:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id)
            
            if action == 'assign':
                # Create vehicle-route assignment
                vehicle_route_assignment, created = VehicleRouteAssignment.objects.get_or_create(
                    vehicle=vehicle,
                    route=route,
                    defaults={'is_active': True}
                )
                
                if not created:
                    vehicle_route_assignment.is_active = True
                    vehicle_route_assignment.save()
                
                # Check if vehicle has a driver and create complete assignment
                driver_assignment = DriverVehicleAssignment.objects.filter(
                    vehicle=vehicle, is_active=True
                ).first()
                
                if driver_assignment:
                    # Create complete assignment automatically
                    CompleteAssignment.create_complete_assignment(
                        driver=driver_assignment.driver,
                        vehicle=vehicle,
                        route=route,
                        notes=f"Auto-created from route management on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                    messages.success(request, f'Vehicle {vehicle.vehicle_registration_no} with driver {driver_assignment.driver.user.username} assigned to route {route.route_name}. Complete assignment created.')
                else:
                    messages.warning(request, f'Vehicle {vehicle.vehicle_registration_no} assigned to route {route.route_name}. Note: No driver assigned to this vehicle yet.')
                
            elif action == 'remove':
                # Remove vehicle-route assignment
                vehicle_assignment = VehicleRouteAssignment.objects.filter(
                    vehicle=vehicle, route=route, is_active=True
                ).first()
                
                if vehicle_assignment:
                    vehicle_assignment.is_active = False
                    vehicle_assignment.save()
                    
                    # Also deactivate any complete assignment
                    complete_assignments = CompleteAssignment.objects.filter(
                        vehicle=vehicle, route=route, is_active=True
                    )
                    for complete_assignment in complete_assignments:
                        complete_assignment.is_active = False
                        complete_assignment.save()
                    
                    messages.success(request, f'Vehicle {vehicle.vehicle_registration_no} removed from route {route.route_name}.')
                else:
                    messages.error(request, 'Assignment not found.')
        
        return redirect('main:route_vehicle_assignments', route_id=route.id)
    
    # Handle GET request - display assignments and available vehicles
    vehicle_assignments = VehicleRouteAssignment.objects.filter(
        route=route, is_active=True
    ).select_related('vehicle').order_by('-assigned_date')
    
    # Get assignment data with driver information and complete assignment status
    assignment_data = []
    for assignment in vehicle_assignments:
        # Get the driver assigned to this vehicle
        driver_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=assignment.vehicle, is_active=True
        ).select_related('driver__user').first()
        
        # Check if there's a complete assignment
        has_complete_assignment = CompleteAssignment.objects.filter(
            vehicle=assignment.vehicle, route=route, is_active=True
        ).exists()
        
        assignment_info = {
            'assignment': assignment,
            'vehicle': assignment.vehicle,
            'driver': driver_assignment.driver if driver_assignment else None,
            'has_complete_assignment': has_complete_assignment,
        }
        assignment_data.append(assignment_info)
    
    # Get available vehicles (not assigned to this route)
    assigned_vehicle_ids = vehicle_assignments.values_list('vehicle_id', flat=True)
    available_vehicles = Vehicle.objects.filter(
        is_active=True
    ).exclude(id__in=assigned_vehicle_ids).order_by('vehicle_registration_no')
    
    # Get available vehicle data with driver information
    available_data = []
    for vehicle in available_vehicles:
        driver_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).select_related('driver__user').first()
        
        vehicle_info = {
            'vehicle': vehicle,
            'driver': driver_assignment.driver if driver_assignment else None,
        }
        available_data.append(vehicle_info)
    
    context = {
        'route': route,
        'assignment_data': assignment_data,
        'available_data': available_data,
        'total_assignments': len(assignment_data),
        'title': f'Vehicle Assignments for {route.route_name}'
    }
    return render(request, 'main/route_vehicle_assignments.html', context)


# Drag and Drop Assignment Views

def drag_drop_assignments_view(request):
    """Drag and drop interface for driver-vehicle-route assignments"""
    from driverAssignment.models import DriverVehicleAssignment, VehicleRouteAssignment, CompleteAssignment
    
    # Get unassigned drivers (not assigned to any vehicle)
    assigned_driver_ids = DriverVehicleAssignment.objects.filter(
        is_active=True
    ).values_list('driver_id', flat=True)
    
    unassigned_drivers = RegistryModel.objects.exclude(
        id__in=assigned_driver_ids
    ).select_related('user').order_by('user__username')
    
    # Get all vehicles with their current assignments
    vehicles = Vehicle.objects.filter(is_active=True).order_by('vehicle_registration_no')
    vehicles_data = []
    
    for vehicle in vehicles:
        # Get current driver assignment
        current_driver_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).select_related('driver__user').first()
        
        # Get current route assignment
        current_route_assignment = VehicleRouteAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).select_related('route').first()
        
        vehicle_data = {
            'vehicle': vehicle,
            'current_driver': current_driver_assignment.driver if current_driver_assignment else None,
            'current_route': current_route_assignment.route if current_route_assignment else None,
        }
        vehicles_data.append(vehicle_data)
    
    # Get all routes
    routes = Route.objects.filter(is_active=True).order_by('route_name')
    
    # Get complete assignments
    complete_assignments = CompleteAssignment.objects.filter(
        is_active=True
    ).select_related('driver__user', 'vehicle', 'route').order_by('-created_date')
    
    context = {
        'unassigned_drivers': unassigned_drivers,
        'vehicles_data': vehicles_data,
        'routes': routes,
        'complete_assignments': complete_assignments,
        'title': 'Drag & Drop Assignments'
    }
    return render(request, 'main/drag_drop_assignments.html', context)


# AJAX endpoints for drag and drop functionality

@require_http_methods(["POST"])
def ajax_assign_driver_vehicle(request):
    """AJAX endpoint to assign driver to vehicle"""
    try:
        data = json.loads(request.body)
        driver_id = data.get('driver_id')
        vehicle_id = data.get('vehicle_id')
        
        if not driver_id or not vehicle_id:
            return JsonResponse({'success': False, 'message': 'Driver ID and Vehicle ID are required.'})
        
        driver = get_object_or_404(RegistryModel, id=driver_id)
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Check if driver is already assigned to another vehicle
        from driverAssignment.models import DriverVehicleAssignment
        existing_assignment = DriverVehicleAssignment.objects.filter(
            driver=driver, is_active=True
        ).first()
        
        if existing_assignment:
            return JsonResponse({
                'success': False, 
                'message': f'Driver {driver.user.username} is already assigned to vehicle {existing_assignment.vehicle.vehicle_registration_no}.'
            })
        
        # Check if vehicle already has a driver
        existing_vehicle_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).first()
        
        if existing_vehicle_assignment:
            return JsonResponse({
                'success': False, 
                'message': f'Vehicle {vehicle.vehicle_registration_no} already has driver {existing_vehicle_assignment.driver.user.username} assigned.'
            })
        
        # Create the assignment
        assignment = DriverVehicleAssignment.objects.create(
            driver=driver,
            vehicle=vehicle,
            is_active=True
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Driver {driver.user.username} successfully assigned to vehicle {vehicle.vehicle_registration_no}.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_http_methods(["POST"])
def ajax_assign_vehicle_route(request):
    """AJAX endpoint to assign vehicle to route"""
    try:
        data = json.loads(request.body)
        vehicle_id = data.get('vehicle_id')
        route_id = data.get('route_id')
        
        if not vehicle_id or not route_id:
            return JsonResponse({'success': False, 'message': 'Vehicle ID and Route ID are required.'})
        
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        route = get_object_or_404(Route, id=route_id)
        
        # Check if vehicle is already assigned to another route
        from driverAssignment.models import VehicleRouteAssignment, DriverVehicleAssignment, CompleteAssignment
        existing_assignment = VehicleRouteAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).first()
        
        if existing_assignment:
            return JsonResponse({
                'success': False, 
                'message': f'Vehicle {vehicle.vehicle_registration_no} is already assigned to route {existing_assignment.route.route_name}.'
            })
        
        # Create the vehicle-route assignment
        assignment = VehicleRouteAssignment.objects.create(
            vehicle=vehicle,
            route=route,
            is_active=True
        )
        
        # Check if this vehicle has a driver assigned and create complete assignment
        driver_assignment = DriverVehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).first()
        
        if driver_assignment:
            # Create complete assignment
            complete_assignment = CompleteAssignment.objects.create(
                driver=driver_assignment.driver,
                vehicle=vehicle,
                route=route,
                is_active=True
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Vehicle {vehicle.vehicle_registration_no} successfully assigned to route {route.route_name}. Complete assignment created: {driver_assignment.driver.user.username} → {vehicle.vehicle_registration_no} → {route.route_name}.'
            })
        else:
            return JsonResponse({
                'success': True, 
                'message': f'Vehicle {vehicle.vehicle_registration_no} successfully assigned to route {route.route_name}.'
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_http_methods(["POST"])
def ajax_remove_driver_vehicle(request):
    """AJAX endpoint to remove driver-vehicle assignment"""
    try:
        data = json.loads(request.body)
        driver_id = data.get('driver_id')
        vehicle_id = data.get('vehicle_id')
        
        if not driver_id or not vehicle_id:
            return JsonResponse({'success': False, 'message': 'Driver ID and Vehicle ID are required.'})
        
        driver = get_object_or_404(RegistryModel, id=driver_id)
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Find and deactivate the assignment
        from driverAssignment.models import DriverVehicleAssignment, CompleteAssignment
        assignment = DriverVehicleAssignment.objects.filter(
            driver=driver, vehicle=vehicle, is_active=True
        ).first()
        
        if not assignment:
            return JsonResponse({'success': False, 'message': 'Assignment not found.'})
        
        assignment.is_active = False
        assignment.save()
        
        # Also deactivate any complete assignments involving this driver-vehicle pair
        CompleteAssignment.objects.filter(
            driver=driver, vehicle=vehicle, is_active=True
        ).update(is_active=False)
        
        return JsonResponse({
            'success': True, 
            'message': f'Removed driver {driver.user.username} from vehicle {vehicle.vehicle_registration_no}.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_http_methods(["POST"])
def ajax_remove_vehicle_route(request):
    """AJAX endpoint to remove vehicle-route assignment"""
    try:
        data = json.loads(request.body)
        vehicle_id = data.get('vehicle_id')
        route_id = data.get('route_id')
        
        if not vehicle_id or not route_id:
            return JsonResponse({'success': False, 'message': 'Vehicle ID and Route ID are required.'})
        
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        route = get_object_or_404(Route, id=route_id)
        
        # Find and deactivate the assignment
        from driverAssignment.models import VehicleRouteAssignment, CompleteAssignment
        assignment = VehicleRouteAssignment.objects.filter(
            vehicle=vehicle, route=route, is_active=True
        ).first()
        
        if not assignment:
            return JsonResponse({'success': False, 'message': 'Assignment not found.'})
        
        assignment.is_active = False
        assignment.save()
        
        # Also deactivate any complete assignments involving this vehicle-route pair
        CompleteAssignment.objects.filter(
            vehicle=vehicle, route=route, is_active=True
        ).update(is_active=False)
        
        return JsonResponse({
            'success': True, 
            'message': f'Removed vehicle {vehicle.vehicle_registration_no} from route {route.route_name}.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_http_methods(["POST"])
def ajax_remove_complete_assignment(request):
    """AJAX endpoint to remove complete assignment"""
    try:
        data = json.loads(request.body)
        assignment_id = data.get('assignment_id')
        
        if not assignment_id:
            return JsonResponse({'success': False, 'message': 'Assignment ID is required.'})
        
        from driverAssignment.models import CompleteAssignment, DriverVehicleAssignment, VehicleRouteAssignment
        assignment = get_object_or_404(CompleteAssignment, id=assignment_id)
        
        # Store assignment details for message
        assignment_str = f'{assignment.driver.user.username} → {assignment.vehicle.vehicle_registration_no} → {assignment.route.route_name}'
        
        # Deactivate the complete assignment
        assignment.is_active = False
        assignment.save()
        
        # Also deactivate related assignments
        DriverVehicleAssignment.objects.filter(
            driver=assignment.driver, vehicle=assignment.vehicle, is_active=True
        ).update(is_active=False)
        
        VehicleRouteAssignment.objects.filter(
            vehicle=assignment.vehicle, route=assignment.route, is_active=True
        ).update(is_active=False)
        
        return JsonResponse({
            'success': True, 
            'message': f'Complete assignment removed: {assignment_str}.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# Analytics Views

def analytics_dashboard_view(request):
    """Main analytics dashboard with tabs"""
    context = {
        'title': 'Analytics & Finance Dashboard'
    }
    return render(request, 'main/analytics_dashboard.html', context)


def weather_data_view(request):
    """Weather data for fleet operations"""
    # Mock weather data for South African cities
    weather_data = {
        'johannesburg': {
            'location': 'Johannesburg',
            'temperature': 18.5,
            'apparent_temperature': 16.8,
            'humidity': 65,
            'wind_speed': 12.3,
            'cloud_cover': 40,
            'rain': 0.0,
            'today_precip_prob': 25,
            'today_max': 22.1,
            'today_min': 12.4,
            'weather_code': 1,
            'description': 'Partly Cloudy',
            'icon': 'bi bi-cloud-sun',
            'last_updated': 'Just now',
            'error': None
        },
        'cape_town': {
            'location': 'Cape Town',
            'temperature': 16.2,
            'apparent_temperature': 15.1,
            'humidity': 72,
            'wind_speed': 18.7,
            'cloud_cover': 65,
            'rain': 0.0,
            'today_precip_prob': 45,
            'today_max': 19.3,
            'today_min': 11.8,
            'weather_code': 2,
            'description': 'Mostly Cloudy',
            'icon': 'bi bi-cloud',
            'last_updated': 'Just now',
            'error': None
        },
        'durban': {
            'location': 'Durban',
            'temperature': 22.8,
            'apparent_temperature': 25.2,
            'humidity': 78,
            'wind_speed': 8.4,
            'cloud_cover': 55,
            'rain': 2.1,
            'today_precip_prob': 85,
            'today_max': 26.7,
            'today_min': 18.9,
            'weather_code': 3,
            'description': 'Light Rain',
            'icon': 'bi bi-cloud-rain',
            'last_updated': 'Just now',
            'error': None
        },
        'pretoria': {
            'location': 'Pretoria',
            'temperature': 19.1,
            'apparent_temperature': 17.6,
            'humidity': 58,
            'wind_speed': 10.2,
            'cloud_cover': 30,
            'rain': 0.0,
            'today_precip_prob': 15,
            'today_max': 23.4,
            'today_min': 13.2,
            'weather_code': 0,
            'description': 'Clear Sky',
            'icon': 'bi bi-sun',
            'last_updated': 'Just now',
            'error': None
        }
    }
    
    # Check for rain warnings
    rain_warnings = []
    has_rain_warnings = False
    
    for city_key, weather in weather_data.items():
        if weather['rain'] > 0 or weather['today_precip_prob'] > 70:
            has_rain_warnings = True
            severity = 'high' if weather['rain'] > 5 or weather['today_precip_prob'] > 85 else 'medium'
            rain_warnings.append({
                'location': weather['location'],
                'probability': weather['today_precip_prob'],
                'expected_rainfall': weather['rain'],
                'severity': severity
            })
    
    context = {
        'weather_data': weather_data,
        'rain_warnings': rain_warnings,
        'has_rain_warnings': has_rain_warnings,
        'title': 'Weather Conditions'
    }
    
    # Check if this is an AJAX request and render content-only template
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'main/weather_content.html', context)
    else:
        return render(request, 'main/weather_widget.html', context)


def fuel_prices_analytics_view(request):
    """Fuel price analytics and trends"""
    # Mock fuel price data
    live_fuel_price = {
        'petrol_93_inland': '20.85',
        'petrol_93_coast': '20.12',
        'petrol_95_inland': '21.15',
        'petrol_95_coast': '20.42',
        'diesel_005_inland': '19.87',
        'diesel_005_coast': '19.25',
        'diesel_05_inland': '19.72',
        'diesel_05_coast': '19.10',
        'last_updated': 'Today at 10:30 AM'
    }
    
    # Get current fleet fuel rate
    current_rate = FuelRateModel.get_active_rate()
    historical_rates = FuelRateModel.objects.all().order_by('-created_at')[:10]
    
    # Mock historical price data for charts
    historical_prices = [
        {'date': '2024-01-01', 'petrol_93': 20.50, 'petrol_95': 20.80, 'diesel_005': 19.60, 'diesel_05': 19.45},
        {'date': '2024-01-08', 'petrol_93': 20.65, 'petrol_95': 20.95, 'diesel_005': 19.75, 'diesel_05': 19.60},
        {'date': '2024-01-15', 'petrol_93': 20.80, 'petrol_95': 21.10, 'diesel_005': 19.90, 'diesel_05': 19.75},
        {'date': '2024-01-22', 'petrol_93': 20.85, 'petrol_95': 21.15, 'diesel_005': 19.87, 'diesel_05': 19.72},
    ]
    
    # Fleet fuel rate data for charts
    fuel_data = []
    for rate in historical_rates:
        fuel_data.append({
            'date': rate.created_at.strftime('%Y-%m-%d'),
            'rate': float(rate.fuel_rate),
            'name': rate.name
        })
    
    context = {
        'live_fuel_price': live_fuel_price,
        'current_rate': current_rate,
        'historical_rates': historical_rates,
        'historical_prices_json': json.dumps(historical_prices),
        'fuel_data': json.dumps(fuel_data),
        'title': 'Fuel Price Analytics'
    }
    
    # Check if this is an AJAX request and render content-only template
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'main/fuel_prices_content.html', context)
    else:
        return render(request, 'main/fuel_prices_analytics.html', context)


def cost_revenue_analytics_view(request):
    """Cost and revenue analytics"""
    from decimal import Decimal
    import datetime
    
    # Get actual data from database
    # Calculate total costs manually since we need fuel_cost + imported_costs
    cost_reports = DailyReportModel_Cost.objects.all()
    total_costs = Decimal('0')
    for report in cost_reports:
        total_costs += report.total_cost()
    
    # Calculate total revenue manually using total_revenue property
    revenue_reports = DailyReportModel_Revenue.objects.all()
    total_revenue = Decimal('0')
    for report in revenue_reports:
        total_revenue += report.total_revenue
    
    # Calculate profit and margin
    total_profit = total_revenue - total_costs
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Get fuel vs imported costs breakdown
    total_fuel_cost = Decimal('0')
    total_imported_costs = Decimal('0')
    for report in cost_reports:
        total_fuel_cost += report.fuel_cost()
        total_imported_costs += report.imported_costs or Decimal('0')
    
    # Get last 7 days trends
    last_7_days = datetime.date.today() - datetime.timedelta(days=7)
    daily_trends = []
    
    for i in range(7):
        date = last_7_days + datetime.timedelta(days=i)
        
        day_cost_reports = DailyReportModel_Cost.objects.filter(date=date)
        day_costs = Decimal('0')
        for report in day_cost_reports:
            day_costs += report.total_cost()
        
        day_revenue_reports = DailyReportModel_Revenue.objects.filter(date=date)
        day_revenue = Decimal('0')
        for report in day_revenue_reports:
            day_revenue += report.total_revenue
        
        daily_trends.append({
            'date': date.strftime('%m-%d'),
            'costs': float(day_costs),
            'revenue': float(day_revenue),
            'profit': float(day_revenue) - float(day_costs)
        })
    
    # Get driver performance data
    driver_costs = {}
    driver_revenues = {}
    
    # Get all drivers
    drivers = RegistryModel.objects.all()[:10]  # Limit to top 10 for chart readability
    
    for driver in drivers:
        driver_name = driver.user.username
        
        # Calculate driver costs
        driver_cost_reports = DailyReportModel_Cost.objects.filter(driver=driver)
        driver_cost_total = Decimal('0')
        for report in driver_cost_reports:
            driver_cost_total += report.total_cost()
        
        # Calculate driver revenue
        driver_revenue_reports = DailyReportModel_Revenue.objects.filter(driver=driver)
        driver_revenue_total = Decimal('0')
        for report in driver_revenue_reports:
            driver_revenue_total += report.total_revenue
        
        if driver_cost_total > 0:
            driver_costs[driver_name] = float(driver_cost_total)
        if driver_revenue_total > 0:
            driver_revenues[driver_name] = float(driver_revenue_total)
    
    # Get route performance data
    routes = Route.objects.all()[:8]  # Limit to 8 routes for chart readability
    route_performance = []
    
    for route in routes:
        # For this example, we'll use mock data since we don't have direct route-revenue mapping
        # In a real scenario, you'd calculate based on actual route assignments
        route_performance.append({
            'name': route.route_name[:10],  # Truncate for chart
            'revenue': float(route.transport_rate) * 100  # Mock calculation
        })
    
    context = {
        'title': 'Cost & Revenue Analytics',
        'total_costs': float(total_costs),
        'total_revenue': float(total_revenue),
        'total_profit': float(total_profit),
        'profit_margin': float(profit_margin),
        'total_fuel_cost': float(total_fuel_cost),
        'total_imported_costs': float(total_imported_costs),
        'daily_trends_json': json.dumps(daily_trends),
        'driver_costs_json': json.dumps(driver_costs),
        'driver_revenues_json': json.dumps(driver_revenues),
        'route_performance_json': json.dumps(route_performance),
    }
    
    # Check if this is an AJAX request and render content-only template
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'main/cost_revenue_content.html', context)
    else:
        return render(request, 'main/cost_revenue_analytics.html', context)


def consolidated_analytics_view(request):
    """Consolidated analytics dashboard with weather and fuel data on one page"""
    # Weather data
    weather_data = {
        'johannesburg': {
            'location': 'Johannesburg',
            'temperature': 18.5,
            'apparent_temperature': 16.8,
            'humidity': 65,
            'wind_speed': 12.3,
            'cloud_cover': 40,
            'rain': 0.0,
            'today_precip_prob': 25,
            'today_max': 22.1,
            'today_min': 12.4,
            'weather_code': 1,
            'description': 'Partly Cloudy',
            'icon': 'bi bi-cloud-sun',
            'last_updated': 'Just now',
            'error': None
        },
        'cape_town': {
            'location': 'Cape Town',
            'temperature': 16.2,
            'apparent_temperature': 15.1,
            'humidity': 72,
            'wind_speed': 18.7,
            'cloud_cover': 65,
            'rain': 0.0,
            'today_precip_prob': 45,
            'today_max': 19.3,
            'today_min': 11.8,
            'weather_code': 2,
            'description': 'Mostly Cloudy',
            'icon': 'bi bi-cloud',
            'last_updated': 'Just now',
            'error': None
        },
        'durban': {
            'location': 'Durban',
            'temperature': 22.8,
            'apparent_temperature': 25.2,
            'humidity': 78,
            'wind_speed': 8.4,
            'cloud_cover': 55,
            'rain': 2.1,
            'today_precip_prob': 85,
            'today_max': 26.7,
            'today_min': 18.9,
            'weather_code': 3,
            'description': 'Light Rain',
            'icon': 'bi bi-cloud-rain',
            'last_updated': 'Just now',
            'error': None
        },
        'pretoria': {
            'location': 'Pretoria',
            'temperature': 19.1,
            'apparent_temperature': 17.6,
            'humidity': 58,
            'wind_speed': 10.2,
            'cloud_cover': 30,
            'rain': 0.0,
            'today_precip_prob': 15,
            'today_max': 23.4,
            'today_min': 13.2,
            'weather_code': 0,
            'description': 'Clear Sky',
            'icon': 'bi bi-sun',
            'last_updated': 'Just now',
            'error': None
        }
    }
    
    # Check for rain warnings
    rain_warnings = []
    has_rain_warnings = False
    
    for city_key, weather in weather_data.items():
        if weather['rain'] > 0 or weather['today_precip_prob'] > 70:
            has_rain_warnings = True
            severity = 'high' if weather['rain'] > 5 or weather['today_precip_prob'] > 85 else 'medium'
            rain_warnings.append({
                'location': weather['location'],
                'probability': weather['today_precip_prob'],
                'expected_rainfall': weather['rain'],
                'severity': severity
            })
    
    # Fuel price data
    live_fuel_price = {
        'petrol_93_inland': '20.85',
        'petrol_93_coast': '20.12',
        'petrol_95_inland': '21.15',
        'petrol_95_coast': '20.42',
        'diesel_005_inland': '19.87',
        'diesel_005_coast': '19.25',
        'diesel_05_inland': '19.72',
        'diesel_05_coast': '19.10',
        'last_updated': 'Today at 10:30 AM'
    }
    
    # Get current fleet fuel rate
    current_rate = FuelRateModel.get_active_rate()
    historical_rates = FuelRateModel.objects.all().order_by('-created_at')[:10]
    
    # Historical price data for charts
    historical_prices = [
        {'date': '2024-01-01', 'petrol_93': 20.50, 'petrol_95': 20.80, 'diesel_005': 19.60, 'diesel_05': 19.45},
        {'date': '2024-01-08', 'petrol_93': 20.65, 'petrol_95': 20.95, 'diesel_005': 19.75, 'diesel_05': 19.60},
        {'date': '2024-01-15', 'petrol_93': 20.80, 'petrol_95': 21.10, 'diesel_005': 19.90, 'diesel_05': 19.75},
        {'date': '2024-01-22', 'petrol_93': 20.85, 'petrol_95': 21.15, 'diesel_005': 19.87, 'diesel_05': 19.72},
    ]
    
    context = {
        'weather_data': weather_data,
        'rain_warnings': rain_warnings,
        'has_rain_warnings': has_rain_warnings,
        'live_fuel_price': live_fuel_price,
        'current_rate': current_rate,
        'historical_rates': historical_rates,
        'historical_prices_json': json.dumps(historical_prices),
        'title': 'Fleet Analytics Dashboard'
    }
    return render(request, 'main/consolidated_analytics.html', context)


# Excel Export Views
def export_all_costs_excel(request):
    """Export all cost reports to Excel"""
    from decimal import Decimal
    # Get all cost reports with search functionality
    search_query = request.GET.get('search', '')
    table_data = DailyReportModel_Cost.objects.all().order_by('date', 'id')

    if search_query:
        table_data = table_data.filter(
            models.Q(fleet_no__icontains=search_query) |
            models.Q(slip_no__icontains=search_query) |
            models.Q(driver__user__username__icontains=search_query)
        )

    # Calculate predicted costs for each report using same logic as display
    previous_predicted = Decimal('0.00')

    for index, report in enumerate(table_data):
        # Calculate actual cost (fuel cost + imported costs)
        report.actual_cost = report.fuel_cost() + (report.imported_costs or Decimal('0.00'))

        # Calculate predicted cost based on same logic as display
        if index == 0:
            # First entry: predicted cost = actual cost
            report.calculated_predicted_cost = report.actual_cost
        else:
            # Subsequent entries: prev_predicted + (latest_cost + prev_predicted)/2
            report.calculated_predicted_cost = previous_predicted + (report.actual_cost + previous_predicted) / 2

        previous_predicted = report.calculated_predicted_cost
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Cost Reports"
    
    # Define headers
    headers = [
        'Fleet Number', 'Driver', 'Date', 'Slip Number', 
        'Fuel Requested (L)', 'Fuel Rate', 'Fuel Cost', 
        'Imported Costs', 'Total Cost', 'Predicted Cost'
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # Add headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # Add data
    for row, cost_report in enumerate(table_data, 2):
        ws.cell(row=row, column=1, value=cost_report.fleet_no)
        ws.cell(row=row, column=2, value=cost_report.driver.user.username if cost_report.driver else 'N/A')
        ws.cell(row=row, column=3, value=cost_report.date)
        ws.cell(row=row, column=4, value=cost_report.slip_no)
        ws.cell(row=row, column=5, value=cost_report.fuel_requested)
        ws.cell(row=row, column=6, value=float(cost_report.fuel_rate_set.fuel_rate) if cost_report.fuel_rate_set else 0)
        ws.cell(row=row, column=7, value=float(cost_report.fuel_cost()))
        ws.cell(row=row, column=8, value=float(cost_report.imported_costs) if cost_report.imported_costs else 0)
        ws.cell(row=row, column=9, value=float(cost_report.total_cost()))
        ws.cell(row=row, column=10, value=float(cost_report.calculated_predicted_cost))
    
    # Auto-adjust column widths
    from openpyxl.utils import get_column_letter
    for col_idx, column in enumerate(ws.columns, 1):
        max_length = 0
        column_letter = get_column_letter(col_idx)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=all_cost_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


def export_driver_costs_excel(request, driver_id):
    """Export individual driver's cost reports to Excel"""
    driver = get_object_or_404(RegistryModel, id=driver_id)
    
    # Get cost reports for this driver
    table_data = DailyReportModel_Cost.objects.filter(driver=driver).order_by('-date')
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Cost Reports - {driver.user.username}"
    
    # Add driver info header
    ws.merge_cells('A1:J1')
    ws['A1'] = f"Cost Reports for Driver: {driver.user.username}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal="center")
    
    # Define headers
    headers = [
        'Fleet Number', 'Date', 'Slip Number', 
        'Fuel Requested (L)', 'Fuel Rate', 'Fuel Cost', 
        'Imported Costs', 'Total Cost', 'Predicted Cost'
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # Add headers (starting from row 3)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # Add data
    total_fuel_cost = 0
    total_imported_costs = 0
    total_costs = 0
    total_predicted = 0
    
    for row, cost_report in enumerate(table_data, 4):
        ws.cell(row=row, column=1, value=cost_report.fleet_no)
        ws.cell(row=row, column=2, value=cost_report.date)
        ws.cell(row=row, column=3, value=cost_report.slip_no)
        ws.cell(row=row, column=4, value=cost_report.fuel_requested)
        ws.cell(row=row, column=5, value=float(cost_report.fuel_rate_set.fuel_rate) if cost_report.fuel_rate_set else 0)
        
        fuel_cost = float(cost_report.fuel_cost())
        imported_cost = float(cost_report.imported_costs) if cost_report.imported_costs else 0
        total_cost = float(cost_report.total_cost())
        predicted_cost = float(cost_report.predicted_cost) if cost_report.predicted_cost else 0
        
        ws.cell(row=row, column=6, value=fuel_cost)
        ws.cell(row=row, column=7, value=imported_cost)
        ws.cell(row=row, column=8, value=total_cost)
        ws.cell(row=row, column=9, value=predicted_cost)
        
        total_fuel_cost += fuel_cost
        total_imported_costs += imported_cost
        total_costs += total_cost
        total_predicted += predicted_cost
    
    # Add totals row
    if table_data:
        totals_row = len(table_data) + 5
        ws.cell(row=totals_row, column=1, value="TOTALS").font = Font(bold=True)
        ws.cell(row=totals_row, column=6, value=total_fuel_cost).font = Font(bold=True)
        ws.cell(row=totals_row, column=7, value=total_imported_costs).font = Font(bold=True)
        ws.cell(row=totals_row, column=8, value=total_costs).font = Font(bold=True)
        ws.cell(row=totals_row, column=9, value=total_predicted).font = Font(bold=True)
    
    # Auto-adjust column widths
    from openpyxl.utils import get_column_letter
    for col_idx, column in enumerate(ws.columns, 1):
        max_length = 0
        column_letter = get_column_letter(col_idx)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=driver_costs_{driver.user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


def export_all_revenue_excel(request):
    """Export all revenue reports to Excel"""
    from decimal import Decimal
    # Get all revenue reports with search functionality
    search_query = request.GET.get('search', '')
    table_data = DailyReportModel_Revenue.objects.all().order_by('date', 'id')

    if search_query:
        table_data = table_data.filter(
            models.Q(fleet_no__icontains=search_query) |
            models.Q(vehicle_no__icontains=search_query)
        )

    # Calculate revenue, variance and predicted revenue using same logic as display
    previous_predicted = Decimal('0.00')

    for index, report in enumerate(table_data):
        # Set revenue based on completed routes
        report.revenue = report.total_revenue

        # Calculate predicted revenue based on same logic as display
        if index == 0:
            # First entry: predicted revenue = actual revenue
            report.predicted = report.revenue
        else:
            # Subsequent entries: prev_predicted + (latest_revenue + prev_predicted)/2
            report.predicted = previous_predicted + (report.revenue + previous_predicted) / 2

        previous_predicted = report.predicted

        # Calculate the planned revenue using same logic as display
        if report.completed_routes.exists():
            report_planned = Decimal('0.00')
            for route in report.completed_routes.all():
                report_planned += route.planned_revenue
        else:
            report_planned = report.planned_rev

        # Set attribute for consistent access
        report.display_planned_revenue = report_planned

        # Calculate variance using same logic as display
        report.variance = report.revenue - report_planned
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Revenue Reports"
    
    # Define headers
    headers = [
        'Fleet Number', 'Vehicle Number', 'Driver', 'Date',
        'Number of Loads', 'Tonnage', 'Completed Routes', 
        'Total Revenue', 'Planned Revenue', 'Variance', 'Predicted Revenue'
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="28a745", end_color="28a745", fill_type="solid")
    
    # Add headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # Add data
    for row, revenue_report in enumerate(table_data, 2):
        # Get completed routes as string
        completed_routes = ", ".join([route.route_name for route in revenue_report.completed_routes.all()])

        ws.cell(row=row, column=1, value=revenue_report.fleet_no)
        ws.cell(row=row, column=2, value=revenue_report.vehicle_no)
        ws.cell(row=row, column=3, value=revenue_report.driver.user.username if revenue_report.driver else 'N/A')
        ws.cell(row=row, column=4, value=revenue_report.date)
        ws.cell(row=row, column=5, value=revenue_report.no_of_loads)
        ws.cell(row=row, column=6, value=revenue_report.tonnage)
        ws.cell(row=row, column=7, value=completed_routes if completed_routes else 'No routes')
        ws.cell(row=row, column=8, value=float(revenue_report.revenue))
        ws.cell(row=row, column=9, value=float(revenue_report.display_planned_revenue))
        ws.cell(row=row, column=10, value=float(revenue_report.variance))
        ws.cell(row=row, column=11, value=float(revenue_report.predicted))
    
    # Auto-adjust column widths
    from openpyxl.utils import get_column_letter
    for col_idx, column in enumerate(ws.columns, 1):
        max_length = 0
        column_letter = get_column_letter(col_idx)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=all_revenue_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


def export_driver_revenue_excel(request, driver_id):
    """Export individual driver's revenue reports to Excel"""
    from decimal import Decimal
    driver = get_object_or_404(RegistryModel, id=driver_id)
    
    # Get revenue reports for this driver
    table_data = DailyReportModel_Revenue.objects.filter(driver=driver).order_by('date', 'id')
    
    # If no reports found with direct driver relationship, fall back to username matching
    if not table_data.exists():
        query_filters = models.Q()
        if driver.user.username:
            query_filters |= models.Q(fleet_no__icontains=driver.user.username)
            query_filters |= models.Q(vehicle_no__icontains=driver.user.username)
            table_data = DailyReportModel_Revenue.objects.filter(query_filters).order_by('id')
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Revenue Reports - {driver.user.username}"
    
    # Add driver info header
    ws.merge_cells('A1:K1')
    ws['A1'] = f"Revenue Reports for Driver: {driver.user.username}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal="center")
    
    # Define headers
    headers = [
        'Fleet Number', 'Vehicle Number', 'Date',
        'Number of Loads', 'Tonnage', 'Completed Routes', 
        'Total Revenue', 'Planned Revenue', 'Variance', 'Predicted Revenue'
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="28a745", end_color="28a745", fill_type="solid")
    
    # Add headers (starting from row 3)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # Add data
    total_revenue = 0
    total_planned = 0
    total_variance = 0
    total_predicted = 0
    
    for row, revenue_report in enumerate(table_data, 4):
        # Get completed routes as string
        completed_routes = ", ".join([route.route_name for route in revenue_report.completed_routes.all()])

        revenue = float(revenue_report.total_revenue)

        # Calculate planned revenue using the same logic as table display
        if revenue_report.completed_routes.exists():
            report_planned = Decimal('0.00')
            for route in revenue_report.completed_routes.all():
                report_planned += route.planned_revenue
            planned = float(report_planned)
        else:
            planned = float(revenue_report.planned_rev)

        # Calculate variance using the same logic as table display
        variance = revenue - planned
        predicted = float(revenue_report.predicted_revenue) if revenue_report.predicted_revenue else 0
        
        ws.cell(row=row, column=1, value=revenue_report.fleet_no)
        ws.cell(row=row, column=2, value=revenue_report.vehicle_no)
        ws.cell(row=row, column=3, value=revenue_report.date)
        ws.cell(row=row, column=4, value=revenue_report.no_of_loads)
        ws.cell(row=row, column=5, value=revenue_report.tonnage)
        ws.cell(row=row, column=6, value=completed_routes if completed_routes else 'No routes')
        ws.cell(row=row, column=7, value=revenue)
        ws.cell(row=row, column=8, value=planned)
        ws.cell(row=row, column=9, value=variance)
        ws.cell(row=row, column=10, value=predicted)
        
        total_revenue += revenue
        total_planned += planned
        total_variance += variance
        total_predicted += predicted
    
    # Add totals row
    if table_data:
        totals_row = len(table_data) + 5
        ws.cell(row=totals_row, column=1, value="TOTALS").font = Font(bold=True)
        ws.cell(row=totals_row, column=7, value=total_revenue).font = Font(bold=True)
        ws.cell(row=totals_row, column=8, value=total_planned).font = Font(bold=True)
        ws.cell(row=totals_row, column=9, value=total_variance).font = Font(bold=True)
        ws.cell(row=totals_row, column=10, value=total_predicted).font = Font(bold=True)
    
    # Auto-adjust column widths
    from openpyxl.utils import get_column_letter
    for col_idx, column in enumerate(ws.columns, 1):
        max_length = 0
        column_letter = get_column_letter(col_idx)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=driver_revenue_{driver.user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


# Bookkeeping Views
def bookkeeping_view(request):
    """Comprehensive bookkeeping view showing all vehicle, route, and revenue data"""
    # Get all revenue reports with related data
    revenue_reports = DailyReportModel_Revenue.objects.select_related(
        'driver', 'driver__user', 'planned_rev_set'
    ).prefetch_related('completed_routes').order_by('date', 'id')
    
    # Handle search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        revenue_reports = revenue_reports.filter(
            models.Q(fleet_no__icontains=search_query) |
            models.Q(vehicle_no__icontains=search_query) |
            models.Q(driver__user__username__icontains=search_query) |
            models.Q(driver__user__first_name__icontains=search_query) |
            models.Q(driver__user__last_name__icontains=search_query) |
            models.Q(completed_routes__route_name__icontains=search_query)
        ).distinct()
    
    # Prepare comprehensive bookkeeping data with predicted revenue calculation
    bookkeeping_data = []
    total_planned_revenue = Decimal('0.00')
    total_actual_revenue = Decimal('0.00')
    total_variance = Decimal('0.00')
    total_predicted_revenue = Decimal('0.00')
    
    previous_predicted = Decimal('0.00')
    
    for index, report in enumerate(revenue_reports):
        # Get completed routes as string
        completed_routes_str = ', '.join([
            f"{route.route_name} ({route.start} → {route.finish})" 
            for route in report.completed_routes.all()
        ]) if report.completed_routes.exists() else 'No routes completed'
        
        # Get shift information from complete assignments
        shift_type = 'D/S'  # Default value
        if report.driver:
            # Try to find the most recent complete assignment for this driver
            from driverAssignment.models import CompleteAssignment
            recent_assignment = CompleteAssignment.objects.filter(
                driver=report.driver,
                is_active=True
            ).order_by('-created_date').first()
            if recent_assignment:
                shift_type = recent_assignment.shift_type
        
        # Calculate actual revenue and planned revenue using route-specific logic
        actual_rev = report.total_revenue
        
        # Calculate planned revenue consistent with revenue reports
        if report.completed_routes.exists():
            planned_rev = Decimal('0.00')
            for route in report.completed_routes.all():
                planned_rev += route.planned_revenue
        else:
            planned_rev = report.planned_rev
        
        # Calculate predicted revenue using the same logic as revenue reports
        if index == 0:
            # First entry: predicted revenue = actual revenue
            predicted_rev = actual_rev
        else:
            # Subsequent entries: prev_predicted + (latest_revenue + prev_predicted)/2
            predicted_rev = previous_predicted + (actual_rev + previous_predicted) / 2
        
        previous_predicted = predicted_rev
        
        # Calculate variance as Revenue - Planned Revenue
        variance = actual_rev - planned_rev
        
        total_planned_revenue += planned_rev
        total_actual_revenue += actual_rev
        total_variance += variance
        total_predicted_revenue += predicted_rev
        
        # Calculate performance metrics based on planned revenue as target
        if actual_rev >= planned_rev:
            performance_badge = 'Exceeds'
            performance_class = 'bg-success'
        elif actual_rev >= planned_rev * Decimal('0.8'):
            performance_badge = 'Good'
            performance_class = 'bg-info'
        elif actual_rev >= planned_rev * Decimal('0.6'):
            performance_badge = 'Average'
            performance_class = 'bg-warning text-dark'
        else:
            performance_badge = 'Below'
            performance_class = 'bg-danger'
        
        # Calculate variance against target (planned revenue)
        vs_target = actual_rev - planned_rev
        vs_target_display = f"+R{vs_target:.2f}" if vs_target >= 0 else f"-R{abs(vs_target):.2f}"
        vs_target_class = "text-success" if vs_target >= 0 else "text-danger"
        
        bookkeeping_data.append({
            'id': report.id,
            'date': report.date,
            'driver_name': report.driver.user.get_full_name() if report.driver and (report.driver.user.first_name or report.driver.user.last_name) else (report.driver.user.username if report.driver else 'Unknown'),
            'fleet_no': report.fleet_no,
            'vehicle_no': report.vehicle_no,
            'routes_taken': completed_routes_str,
            'loads_planned': report.no_of_loads,
            'tonnage': report.tonnage,
            'planned_revenue': planned_rev,
            'actual_revenue': actual_rev,
            'variance': variance,
            'predicted_revenue': predicted_rev,
            'shift_type': shift_type,
            'performance_badge': performance_badge,
            'performance_class': performance_class,
            'vs_target': vs_target,
            'vs_target_display': vs_target_display,
            'vs_target_class': vs_target_class,
            'status': 'Completed' if report.completed_routes.exists() else 'No Routes',
        })
    
    # Calculate total vs target metrics
    total_vs_target = total_actual_revenue - total_planned_revenue
    total_vs_target_display = f"+R{total_vs_target:.2f}" if total_vs_target >= 0 else f"-R{abs(total_vs_target):.2f}"
    total_vs_target_class = "text-success" if total_vs_target >= 0 else "text-danger"
    
    # Get routes for the route planning matrix and calculate usage
    routes = Route.objects.filter(is_active=True).order_by('route_name')
    
    # Calculate route usage percentages based on how often they appear in revenue reports
    total_route_uses = 0
    for route in routes:
        route_usage_count = sum(1 for report in revenue_reports if route in report.completed_routes.all())
        total_route_uses += route_usage_count
    
    # Calculate percentage for each route
    for route in routes:
        route_usage_count = sum(1 for report in revenue_reports if route in report.completed_routes.all())
        if total_route_uses > 0:
            route.usage_percentage = min(100, int((route_usage_count / max(len(revenue_reports), 1)) * 100))
        else:
            route.usage_percentage = 0
    
    context = {
        'bookkeeping_data': bookkeeping_data,
        'search_query': search_query,
        'total_records': len(bookkeeping_data),
        'total_planned_revenue': total_planned_revenue,
        'total_actual_revenue': total_actual_revenue,
        'total_variance': total_variance,
        'total_vs_target': total_vs_target,
        'total_vs_target_display': total_vs_target_display,
        'total_vs_target_class': total_vs_target_class,
        'routes': routes,
        'title': 'Fleet Bookkeeping'
    }
    
    return render(request, 'main/bookkeeping.html', context)


def export_bookkeeping_excel(request):
    """Export comprehensive fleet management data to Excel with 5 sheets"""
    # Get data
    revenue_reports = DailyReportModel_Revenue.objects.select_related(
        'driver', 'driver__user', 'planned_rev_set'
    ).prefetch_related('completed_routes').order_by('-date', '-id')
    
    routes = Route.objects.filter(is_active=True).order_by('route_name')
    vehicles = Vehicle.objects.filter(is_active=True).order_by('vehicle_registration_no')
    
    # Handle search filter from URL
    search_query = request.GET.get('search', '').strip()
    if search_query:
        revenue_reports = revenue_reports.filter(
            models.Q(fleet_no__icontains=search_query) |
            models.Q(vehicle_no__icontains=search_query) |
            models.Q(driver__user__username__icontains=search_query) |
            models.Q(driver__user__first_name__icontains=search_query) |
            models.Q(driver__user__last_name__icontains=search_query) |
            models.Q(completed_routes__route_name__icontains=search_query)
        ).distinct()
    
    # Create workbook
    wb = Workbook()
    
    # Common styles
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    accent_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
    
    # SHEET 1: DASHBOARD
    ws_dashboard = wb.active
    ws_dashboard.title = "Dashboard"
    
    # Dashboard headers
    dashboard_headers = [
        'Vehicle Registration', 'Fleet Number', 'Current Status', 'Daily Production (R)',
        'Weekly Performance (R)', 'Month to Date (R)', 'Target Variance (R)', 
        'Load Count', 'Primary Routes', 'Driver Assigned'
    ]
    
    for col, header in enumerate(dashboard_headers, 1):
        cell = ws_dashboard.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Aggregate vehicle performance data
    vehicle_data = {}
    for report in revenue_reports:
        vehicle_key = f"{report.vehicle_no}-{report.fleet_no}"
        if vehicle_key not in vehicle_data:
            vehicle_data[vehicle_key] = {
                'vehicle_no': report.vehicle_no,
                'fleet_no': report.fleet_no,
                'daily_revenue': Decimal('0.00'),
                'weekly_revenue': Decimal('0.00'),
                'monthly_revenue': Decimal('0.00'),
                'load_count': 0,
                'routes': set(),
                'driver': report.driver.user.get_full_name() if report.driver else 'Unassigned'
            }
        
        # Calculate time-based aggregations
        if report.date:
            days_ago = (timezone.now().date() - report.date).days
            revenue = report.total_revenue
            
            if days_ago == 0:  # Today
                vehicle_data[vehicle_key]['daily_revenue'] += revenue
            if days_ago <= 7:  # Last 7 days
                vehicle_data[vehicle_key]['weekly_revenue'] += revenue
            if days_ago <= 30:  # Last 30 days
                vehicle_data[vehicle_key]['monthly_revenue'] += revenue
        
        vehicle_data[vehicle_key]['load_count'] += report.no_of_loads
        for route in report.completed_routes.all():
            vehicle_data[vehicle_key]['routes'].add(route.route_name)
    
    # Add dashboard data
    row = 2
    for vehicle_key, data in vehicle_data.items():
        target_variance = data['daily_revenue'] - Decimal('19288.50')
        status = 'Active' if data['daily_revenue'] > 0 else 'Inactive'
        routes_str = ', '.join(list(data['routes'])[:3])  # Limit to 3 routes
        
        ws_dashboard.cell(row=row, column=1, value=data['vehicle_no'])
        ws_dashboard.cell(row=row, column=2, value=data['fleet_no'])
        ws_dashboard.cell(row=row, column=3, value=status)
        ws_dashboard.cell(row=row, column=4, value=float(data['daily_revenue']))
        ws_dashboard.cell(row=row, column=5, value=float(data['weekly_revenue']))
        ws_dashboard.cell(row=row, column=6, value=float(data['monthly_revenue']))
        ws_dashboard.cell(row=row, column=7, value=float(target_variance))
        ws_dashboard.cell(row=row, column=8, value=data['load_count'])
        ws_dashboard.cell(row=row, column=9, value=routes_str)
        ws_dashboard.cell(row=row, column=10, value=data['driver'])
        row += 1
    
    # SHEET 2: PRODUCTION DETAIL
    ws_production = wb.create_sheet(title="Production Detail")
    
    production_headers = [
        'Date', 'Driver Name', 'Shift Type', 'Fleet Number', 'Vehicle Registration',
        'Routes Completed', 'Load Count', 'Tonnage', 'Revenue (R)', 'Performance Points',
        'Target Variance (R)', 'Status'
    ]
    
    for col, header in enumerate(production_headers, 1):
        cell = ws_production.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    row = 2
    for report in revenue_reports:
        completed_routes = ', '.join([
            f"{route.route_name}" for route in report.completed_routes.all()
        ]) if report.completed_routes.exists() else 'None'
        
        # Calculate performance points (simplified system)
        performance_points = 0
        if report.total_revenue >= Decimal('19288.50'):
            performance_points = 10
        elif report.total_revenue >= Decimal('15000'):
            performance_points = 7
        elif report.total_revenue >= Decimal('10000'):
            performance_points = 5
        else:
            performance_points = 2
        
        shift_type = 'D/S' if row % 2 == 0 else 'N/S'  # Alternate for demo
        target_variance = report.total_revenue - Decimal('19288.50')
        
        ws_production.cell(row=row, column=1, value=report.date.strftime('%Y-%m-%d') if report.date else 'N/A')
        ws_production.cell(row=row, column=2, value=report.driver.user.get_full_name() if report.driver else 'Unknown')
        ws_production.cell(row=row, column=3, value=shift_type)
        ws_production.cell(row=row, column=4, value=report.fleet_no)
        ws_production.cell(row=row, column=5, value=report.vehicle_no)
        ws_production.cell(row=row, column=6, value=completed_routes)
        ws_production.cell(row=row, column=7, value=report.no_of_loads)
        ws_production.cell(row=row, column=8, value=report.tonnage)
        ws_production.cell(row=row, column=9, value=float(report.total_revenue))
        ws_production.cell(row=row, column=10, value=performance_points)
        ws_production.cell(row=row, column=11, value=float(target_variance))
        ws_production.cell(row=row, column=12, value='Active' if report.completed_routes.exists() else 'Inactive')
        row += 1
    
    # SHEET 3: ROUTE CHART
    ws_routes = wb.create_sheet(title="Route Chart")
    
    route_headers = [
        'Route Name', 'Start Location', 'Destination', 'Transport Rate (R)',
        'Planned Revenue (R)', 'Daily Available', 'Weekly Usage %', 'Monthly Loads',
        'Primary Vehicles', 'Status'
    ]
    
    for col, header in enumerate(route_headers, 1):
        cell = ws_routes.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    row = 2
    for route in routes:
        # Calculate route usage statistics
        route_reports = revenue_reports.filter(completed_routes=route)
        monthly_loads = sum(report.no_of_loads for report in route_reports)
        weekly_usage = min(100, (monthly_loads / 30) * 100) if monthly_loads > 0 else 0
        
        # Get primary vehicles for this route
        primary_vehicles = set()
        for report in route_reports[:5]:  # Top 5 recent
            primary_vehicles.add(report.vehicle_no)
        vehicles_str = ', '.join(list(primary_vehicles)[:3])
        
        ws_routes.cell(row=row, column=1, value=route.route_name)
        ws_routes.cell(row=row, column=2, value=route.start)
        ws_routes.cell(row=row, column=3, value=route.finish)
        ws_routes.cell(row=row, column=4, value=float(route.transport_rate))
        ws_routes.cell(row=row, column=5, value=float(route.planned_revenue))
        ws_routes.cell(row=row, column=6, value='YES' if route.is_active else 'NO')
        ws_routes.cell(row=row, column=7, value=f"{weekly_usage:.1f}%")
        ws_routes.cell(row=row, column=8, value=monthly_loads)
        ws_routes.cell(row=row, column=9, value=vehicles_str)
        ws_routes.cell(row=row, column=10, value='Active' if route.is_active else 'Inactive')
        row += 1
    
    # SHEET 4: TARGETS
    ws_targets = wb.create_sheet(title="Targets")
    
    target_headers = [
        'Metric', 'Daily Target', 'Weekly Target', 'Monthly Target',
        'Current Achievement', 'Variance', 'Performance %', 'Status'
    ]
    
    for col, header in enumerate(target_headers, 1):
        cell = ws_targets.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Calculate current performance
    today_revenue = sum(data['daily_revenue'] for data in vehicle_data.values())
    weekly_revenue = sum(data['weekly_revenue'] for data in vehicle_data.values())
    monthly_revenue = sum(data['monthly_revenue'] for data in vehicle_data.values())
    
    targets_data = [
        ('Revenue (R)', 19288.50, 134819.50, 578655.00, float(today_revenue), float(today_revenue - Decimal('19288.50'))),
        ('Load Count', 20, 140, 600, sum(data['load_count'] for data in vehicle_data.values()), 0),
        ('Tonnage', 660, 4620, 19800, 0, 0),  # Placeholder
        ('Active Vehicles', 2, 2, 2, len([v for v in vehicle_data.values() if v['daily_revenue'] > 0]), 0)
    ]
    
    row = 2
    for metric, daily, weekly, monthly, current, variance in targets_data:
        performance_pct = (current / daily * 100) if daily > 0 else 0
        status = 'Exceeds' if performance_pct >= 100 else 'Good' if performance_pct >= 80 else 'Below'
        
        ws_targets.cell(row=row, column=1, value=metric)
        ws_targets.cell(row=row, column=2, value=daily)
        ws_targets.cell(row=row, column=3, value=weekly)
        ws_targets.cell(row=row, column=4, value=monthly)
        ws_targets.cell(row=row, column=5, value=current)
        ws_targets.cell(row=row, column=6, value=variance)
        ws_targets.cell(row=row, column=7, value=f"{performance_pct:.1f}%")
        ws_targets.cell(row=row, column=8, value=status)
        row += 1
    
    # SHEET 5: INDIVIDUAL ROUTE TRACKING (Combined for top routes)
    ws_individual = wb.create_sheet(title="Route Tracking")
    
    individual_headers = [
        'Route Name', 'Date', 'Vehicle Assignment', 'Driver', 'Shift',
        'Load Count', 'Revenue (R)', 'Performance', '30-Day Trend'
    ]
    
    for col, header in enumerate(individual_headers, 1):
        cell = ws_individual.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Get recent 30 days data for each route
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_reports = revenue_reports.filter(date__gte=thirty_days_ago).order_by('date')
    
    row = 2
    for route in routes:
        route_recent = recent_reports.filter(completed_routes=route)
        for report in route_recent:
            shift_type = 'D/S' if row % 2 == 0 else 'N/S'
            performance = 'High' if report.total_revenue >= Decimal('15000') else 'Medium' if report.total_revenue >= Decimal('10000') else 'Low'
            
            ws_individual.cell(row=row, column=1, value=route.route_name)
            ws_individual.cell(row=row, column=2, value=report.date.strftime('%Y-%m-%d') if report.date else 'N/A')
            ws_individual.cell(row=row, column=3, value=report.vehicle_no)
            ws_individual.cell(row=row, column=4, value=report.driver.user.get_full_name() if report.driver else 'Unknown')
            ws_individual.cell(row=row, column=5, value=shift_type)
            ws_individual.cell(row=row, column=6, value=report.no_of_loads)
            ws_individual.cell(row=row, column=7, value=float(report.total_revenue))
            ws_individual.cell(row=row, column=8, value=performance)
            ws_individual.cell(row=row, column=9, value='Stable')  # Placeholder for trend analysis
            row += 1
    
    # Auto-adjust column widths for all sheets
    from openpyxl.utils import get_column_letter
    for ws in [ws_dashboard, ws_production, ws_routes, ws_targets, ws_individual]:
        for col_idx, column in enumerate(ws.columns, 1):
            max_length = 0
            column_letter = get_column_letter(col_idx)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'fleet_management_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    if search_query:
        filename = f'fleet_management_filtered_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    wb.save(response)
    return response


# Route Management Views (Missing Functions)
