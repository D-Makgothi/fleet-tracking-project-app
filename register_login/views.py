from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages 
from django.contrib.auth import authenticate, login as auth_login
from .forms import RegistryModelForm, LoginForm, ClientModelForm, EditClientForm, SiteModelForm, EditSiteForm, ControllerRegistrationForm
from django.contrib.auth.models import User
from .models import RegistryModel, ClientModel, SiteModel, ControllerModel, ControllerActivityLog, DailyShiftStatus
from datetime import datetime, timedelta
from decimal import Decimal

# Registration view. Allows users to register their data into the database
def register(request):
    if request.method == 'POST':
        form = RegistryModelForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create new  Registration instances that will be appended to database 
            RegistryModel.objects.create(
                user=user,
                mine = form.cleaned_data.get('mine'),
                driver_license_no=form.cleaned_data.get('driver_license_no'),
                driver_license_expiry=form.cleaned_data.get('driver_license_expiry'),
                induction_license_no=form.cleaned_data.get('induction_license_no'),
                induction_license_expiry=form.cleaned_data.get('induction_license_expiry')
            )
            messages.success(request, 'You have successfully registered. Please proceed to login.')
            return redirect('register_login:login')
    else:
        form = RegistryModelForm()
    return render(request, 'register_login/register.html', {'form': form})


# CLIENT STUFF

#Register Client
def register_client(request):
    if request.method == 'POST':
        form = ClientModelForm(request.POST) 
        if form.is_valid():
            # user = form.save()
            # # Create new  Registration instances that will be appended to database 
            ClientModel.objects.create(
                manager = form.cleaned_data.get('manager'),
                site= form.cleaned_data.get('site'),
                date_created = form.cleaned_data.get('date_created'), # Model We are referncing NOT MODEL FORM
               
            )
            messages.success(request, 'You have successfully registered a Client. Please proceed to login.')
            return redirect('main:home')
    else:
        form = ClientModelForm()
    return render(request, 'register_login/register_client.html', {'form': form})



#Edit Clients

def edit_client(request, pk):
    client = get_object_or_404(ClientModel, pk=pk) #created_by=request.user - Removed beccause we don't have a field called "created_by" in the ClientModel
    if request.method == "POST":
        form = EditClientForm(request.POST, request.FILES, instance=client) 
        if form.is_valid():
            form.save()
            return redirect('main:client')
    else:
        form = EditClientForm(instance=client)
    
    context = {
        'form': form,
        'title': 'Client'
    }
    return render(request, 'register_login/edit_client_form.html', context)




#Delete Clients
def delete_client(request, pk):
    client = get_object_or_404(ClientModel, pk=pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, f'Client {client} has been deleted successfully.')
        return redirect('main:client')
    
    # For GET requests, render a confirmation template
    context = {
        'client': client
    }
    return render(request, 'register_login/delete_client_form.html', context)


#SITE STUFF

#Register Site

def register_site(request):
    if request.method == 'POST':
        form = SiteModelForm(request.POST) 
        if form.is_valid():
            # user = form.save()
            # # Create new  Registration instances that will be appended to database 
            SiteModel.objects.create(
                site_reference = form.cleaned_data.get('site_reference'),
                responsible_user = form.cleaned_data.get('responsible_user'), # Model We are referncing NOT MODEL FORM
                site_coordinator_email = form.cleaned_data.get('site_coordinator_email'), # Model We are referncing NOT MODEL FORM
                status = form.cleaned_data.get('status'),
                site_category = form.cleaned_data.get('category')
               
            )
            messages.success(request, 'You have successfully registered a Site. Please proceed to login.')
            return redirect('main:home')
    else:
        form = SiteModelForm()
    return render(request, 'register_login/register_site.html', {'form': form})

# Edit Site
def edit_site(request, pk):
    site = get_object_or_404(SiteModel, pk=pk) #created_by=request.user - Removed beccause we don't have a field called "created_by" in the ClientModel
    if request.method == "POST":
        form = EditSiteForm(request.POST, request.FILES, instance=site) 
        if form.is_valid():
            form.save()
            return redirect('main:site')
    else:
        form = EditSiteForm(instance=site)
    
    context = {
        'form': form,
        'title': 'Site'
    }
    return render(request, 'register_login/edit_site_form.html', context)

#Delete Clients
def delete_site(request, pk):
    site = get_object_or_404(SiteModel, pk=pk)
    
    if request.method == 'POST':
        site.delete()
        messages.success(request, f'Client {site} has been deleted successfully.')
        return redirect('main:site')
    
    # For GET requests, render a confirmation template
    context = {
        'site': site
    }
    return render(request, 'register_login/delete_site_form.html', context)



# Login view, deals with login page
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('main:home')
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid submission')
    else:
        form = LoginForm()
    return render(request, 'register_login/login.html', {'form': form})


# Controller Registration view
def register_controller(request):
    if request.method == 'POST':
        form = ControllerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Controller {user.username} has been successfully registered.')
            return redirect('register_login:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ControllerRegistrationForm()
    return render(request, 'register_login/register_controller.html', {'form': form})


# Edit Controller
def edit_controller(request, pk):
    controller = get_object_or_404(ControllerModel, pk=pk)
    if request.method == "POST":
        # Update user fields
        user = controller.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update controller fields
        controller.phone_number = request.POST.get('phone_number', '')
        controller.department = request.POST.get('department', '')
        controller.employee_id = request.POST.get('employee_id', '')
        controller.save()
        
        messages.success(request, f'Controller {user.username} has been updated successfully.')
        return redirect('main:active_users')
    
    context = {
        'controller': controller,
        'title': 'Edit Controller'
    }
    return render(request, 'register_login/edit_controller_form.html', context)


# Delete Controller
def delete_controller(request, pk):
    controller = get_object_or_404(ControllerModel, pk=pk)
    
    if request.method == 'POST':
        username = controller.user.username
        controller.user.delete()  # This will also delete the controller due to CASCADE
        messages.success(request, f'Controller {username} has been deleted successfully.')
        return redirect('main:active_users')
    
    context = {
        'controller': controller
    }
    return render(request, 'register_login/delete_controller_form.html', context)


# Activity Logging Utility Functions
def log_controller_activity(controller_user, action_type, description, target_driver=None, target_vehicle_id=None, target_route_id=None, details=None):
    """Utility function to log controller activities"""
    try:
        controller = ControllerModel.objects.get(user=controller_user)
        ControllerActivityLog.objects.create(
            controller=controller,
            action_type=action_type,
            description=description,
            target_driver=target_driver,
            target_vehicle_id=target_vehicle_id,
            target_route_id=target_route_id,
            details=details or {}
        )
    except ControllerModel.DoesNotExist:
        # If not a controller, only log if admin
        if controller_user.is_staff:
            # Create a temporary activity log entry for admin actions
            ControllerActivityLog.objects.create(
                controller=None,  # Admin action
                action_type=action_type,
                description=f"ADMIN: {description}",
                target_driver=target_driver,
                target_vehicle_id=target_vehicle_id,
                target_route_id=target_route_id,
                details=details or {}
            )


def update_daily_shift_status(controller_user):
    """Update daily shift status and track controllers"""
    try:
        controller = ControllerModel.objects.get(user=controller_user)
        today = datetime.now().date()
        
        shift_status, created = DailyShiftStatus.objects.get_or_create(
            date=today,
            defaults={
                'active_assignments_count': 0,
                'last_updated_by': controller
            }
        )
        
        # Add controller to worked list if not already there
        if not shift_status.controllers_worked.filter(id=controller.id).exists():
            shift_status.controllers_worked.add(controller)
        
        shift_status.last_updated_by = controller
        shift_status.save()
        
        return shift_status
    except ControllerModel.DoesNotExist:
        return None


# Controller Activity Log View
def controller_activity_log_view(request):
    """View to display controller activity logs for shift handover"""
    # Get filter parameters
    date_filter = request.GET.get('date', datetime.now().date().isoformat())
    controller_filter = request.GET.get('controller', 'all')
    action_filter = request.GET.get('action', 'all')
    
    # Build query
    logs = ControllerActivityLog.objects.select_related('controller', 'target_driver').all()
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            logs = logs.filter(shift_date=filter_date)
        except ValueError:
            pass
    
    if controller_filter != 'all':
        logs = logs.filter(controller__user__username=controller_filter)
    
    if action_filter != 'all':
        logs = logs.filter(action_type=action_filter)
    
    # Get today's shift status
    today = datetime.now().date()
    try:
        today_shift = DailyShiftStatus.objects.get(date=today)
    except DailyShiftStatus.DoesNotExist:
        today_shift = None
    
    # Get all controllers for filter dropdown
    controllers = ControllerModel.objects.select_related('user').all()
    
    context = {
        'logs': logs[:100],  # Limit to 100 recent entries
        'controllers': controllers,
        'action_choices': ControllerActivityLog.ACTION_CHOICES,
        'today_shift': today_shift,
        'date_filter': date_filter,
        'controller_filter': controller_filter,
        'action_filter': action_filter,
    }
    
    return render(request, 'register_login/controller_activity_log.html', context)


# Shift Handover Dashboard
def shift_handover_dashboard(request):
    """Dashboard showing current shift status and handover information"""
    today = datetime.now().date()
    
    # Get today's shift status
    try:
        today_shift = DailyShiftStatus.objects.get(date=today)
    except DailyShiftStatus.DoesNotExist:
        today_shift = DailyShiftStatus.objects.create(date=today)
    
    # Get recent activity (last 4 hours)
    four_hours_ago = datetime.now() - timedelta(hours=4)
    recent_activity = ControllerActivityLog.objects.filter(
        timestamp__gte=four_hours_ago
    ).select_related('controller', 'target_driver')[:20]
    
    # Get active assignments for today
    from driverAssignment.models import CompleteAssignment, DriverRouteAssignment
    
    active_complete_assignments = CompleteAssignment.objects.filter(
        is_active=True,
        created_date=today
    ).select_related('driver', 'vehicle', 'route')
    
    active_route_assignments = DriverRouteAssignment.objects.filter(
        is_active=True,
        assigned_date=today
    ).select_related('driver', 'route')
    
    # Update assignment count
    total_assignments = active_complete_assignments.count() + active_route_assignments.count()
    if today_shift.active_assignments_count != total_assignments:
        today_shift.active_assignments_count = total_assignments
        today_shift.save()
    
    context = {
        'today_shift': today_shift,
        'recent_activity': recent_activity,
        'active_complete_assignments': active_complete_assignments,
        'active_route_assignments': active_route_assignments,
        'total_assignments': total_assignments,
    }
    
    return render(request, 'register_login/shift_handover_dashboard.html', context)