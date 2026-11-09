from django import forms
from .models import RouteManager, DriverRouteAssignment, DriverVehicleAssignment, VehicleRouteAssignment, CompleteAssignment
from register_login.models import RegistryModel
from main.models import Route, Vehicle


class RouteFilterForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=False,
        label="Search Route Name",
        widget=forms.TextInput(attrs={'placeholder': 'Enter route name', 'class': 'form-control'})
    )

    
class AddRouteForm(forms.ModelForm):
    route_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Route Name", "class": "form-control"}),
        label=""
    )
    start = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Starting Point", "class": "form-control"}),
        label=""
    )
    finish = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Ending Point", "class": "form-control"}),
        label=""
    )
    drivers = forms.ModelMultipleChoiceField(
        queryset=RegistryModel.objects.all(),
        required=False,  # Allow no drivers to be selected
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
        label="Assign Drivers"
    )

    class Meta:
        model = RouteManager
        fields = ['route_name', 'start', 'finish', 'drivers']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['drivers'].queryset = RegistryModel.objects.all()


# New forms for integrated route system
class DriverRouteAssignmentForm(forms.ModelForm):
    """Form for assigning drivers to routes from the main app"""
    route = forms.ModelChoiceField(
        queryset=Route.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Route"
    )
    driver = forms.ModelChoiceField(
        queryset=RegistryModel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Driver"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}),
        label="Notes (Optional)"
    )
    
    class Meta:
        model = DriverRouteAssignment
        fields = ['route', 'driver', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order routes by name for better UX
        self.fields['route'].queryset = Route.objects.filter(is_active=True).order_by('route_name')
        self.fields['driver'].queryset = RegistryModel.objects.all().order_by('user__username')


class RouteDriverManagementForm(forms.Form):
    """Form for managing multiple driver assignments for a specific route"""
    drivers = forms.ModelMultipleChoiceField(
        queryset=RegistryModel.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Assign Drivers to this Route"
    )
    
    def __init__(self, *args, **kwargs):
        route = kwargs.pop('route', None)
        super().__init__(*args, **kwargs)
        
        self.fields['drivers'].queryset = RegistryModel.objects.all().order_by('user__username')
        
        # Pre-select currently assigned drivers if route is provided
        if route:
            assigned_drivers = DriverRouteAssignment.objects.filter(
                route=route, is_active=True
            ).values_list('driver', flat=True)
            self.fields['drivers'].initial = assigned_drivers


# New forms for hierarchical assignment system

class DriverVehicleAssignmentForm(forms.ModelForm):
    """Form for assigning drivers to vehicles"""
    driver = forms.ModelChoiceField(
        queryset=RegistryModel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Driver"
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Vehicle"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}),
        label="Notes (Optional)"
    )
    
    class Meta:
        model = DriverVehicleAssignment
        fields = ['driver', 'vehicle', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = RegistryModel.objects.all().order_by('user__username')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('vehicle_make', 'vehicle_registration_no')
    
    def clean(self):
        cleaned_data = super().clean()
        driver = cleaned_data.get('driver')
        vehicle = cleaned_data.get('vehicle')
        
        if driver and vehicle:
            # Check if driver is already assigned to another active vehicle
            existing_assignment = DriverVehicleAssignment.objects.filter(
                driver=driver, is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            
            if existing_assignment:
                raise forms.ValidationError(
                    f"Driver {driver.user.username} is already assigned to vehicle {existing_assignment.vehicle.vehicle_registration_no}"
                )
            
            # Check if vehicle is already assigned to another active driver
            existing_vehicle_assignment = DriverVehicleAssignment.objects.filter(
                vehicle=vehicle, is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            
            if existing_vehicle_assignment:
                raise forms.ValidationError(
                    f"Vehicle {vehicle.vehicle_registration_no} is already assigned to driver {existing_vehicle_assignment.driver.user.username}"
                )
        
        return cleaned_data


class VehicleRouteAssignmentForm(forms.ModelForm):
    """Form for assigning vehicles to routes"""
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Vehicle"
    )
    route = forms.ModelChoiceField(
        queryset=Route.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Route"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}),
        label="Notes (Optional)"
    )
    
    class Meta:
        model = VehicleRouteAssignment
        fields = ['vehicle', 'route', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('vehicle_make', 'vehicle_registration_no')
        self.fields['route'].queryset = Route.objects.filter(is_active=True).order_by('route_name')


class CompleteAssignmentForm(forms.ModelForm):
    """Form for creating complete driver → vehicle → route assignments"""
    driver = forms.ModelChoiceField(
        queryset=RegistryModel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Driver"
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Vehicle"
    )
    route = forms.ModelChoiceField(
        queryset=Route.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Route"
    )
    shift_type = forms.ChoiceField(
        choices=CompleteAssignment.SHIFT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Shift Type",
        initial='D/S'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}),
        label="Notes (Optional)"
    )
    
    class Meta:
        model = CompleteAssignment
        fields = ['driver', 'vehicle', 'route', 'shift_type', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = RegistryModel.objects.all().order_by('user__username')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('vehicle_make', 'vehicle_registration_no')
        self.fields['route'].queryset = Route.objects.filter(is_active=True).order_by('route_name')
    
    def clean(self):
        cleaned_data = super().clean()
        driver = cleaned_data.get('driver')
        vehicle = cleaned_data.get('vehicle')
        route = cleaned_data.get('route')
        
        if driver and vehicle and route:
            # Check if this exact assignment already exists
            existing_assignment = CompleteAssignment.objects.filter(
                driver=driver, vehicle=vehicle, route=route, is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            
            if existing_assignment:
                raise forms.ValidationError(
                    f"This assignment already exists: {driver.user.username} → {vehicle.vehicle_registration_no} → {route.route_name}"
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        if commit:
            # Use the model's helper method to create all necessary relationships
            return CompleteAssignment.create_complete_assignment(
                driver=self.cleaned_data['driver'],
                vehicle=self.cleaned_data['vehicle'],
                route=self.cleaned_data['route'],
                shift_type=self.cleaned_data.get('shift_type', 'D/S'),
                notes=self.cleaned_data.get('notes', '')
            )
        return super().save(commit=False)

