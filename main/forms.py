from django import forms
from .models import DailyReportModel_Revenue, DailyReportModel_Cost, Route, FuelRateModel, Vehicle
from register_login.models import RegistryModel, ControllerModel

#Cost Model Form
class DailyReportModelForm_Cost(forms.ModelForm):

    date = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'}))

    fuel_requested = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder': 'How many litres of fuel did you request?'}))

    # Driver selection field for controllers and admins
    driver_assignment = forms.ModelChoiceField(
        queryset=RegistryModel.objects.select_related('user').all(),
        required=False,
        empty_label="Select Driver (Optional - for Admin/Controller use)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Controllers and Admins: Select a driver to fill out this report on their behalf"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Show driver assignment field only for controllers and admins
        if self.user and self.user.is_authenticated:
            is_controller = ControllerModel.objects.filter(user=self.user).exists()
            is_admin = self.user.is_staff

            if not (is_controller or is_admin):
                # Hide driver assignment field for regular drivers
                del self.fields['driver_assignment']
        else:
            # If no user provided or user is not authenticated, hide the field
            del self.fields['driver_assignment']
    
    class Meta:
        model = DailyReportModel_Cost
        fields = ['fleet_no', 'date', 'fuel_requested', 'slip_no']








#Revenue Model Form
class DailyReportModelForm_Revenue(forms.ModelForm):
   
    date = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'}))
    
    no_of_loads = forms.IntegerField(
        widget=forms.TextInput({'placeholder': 'How many loads did you make today?'}),
        required=True
    )
    
    fleet_no = forms.CharField(
        max_length=60,
        required=True
    )
    
    vehicle_no = forms.CharField(
        max_length=60,
        widget=forms.TextInput({'placeholder': 'Vehicle Registration Number'}),
        required=True
    )
    
    # Driver selection field for controllers and admins
    driver_assignment = forms.ModelChoiceField(
        queryset=RegistryModel.objects.select_related('user').all(),
        required=False,
        empty_label="Select Driver (Optional - for Admin/Controller use)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Controllers and Admins: Select a driver to fill out this report on their behalf"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Show driver assignment field only for controllers and admins
        if self.user and self.user.is_authenticated:
            is_controller = ControllerModel.objects.filter(user=self.user).exists()
            is_admin = self.user.is_staff

            if not (is_controller or is_admin):
                # Hide driver assignment field for regular drivers
                del self.fields['driver_assignment']
        else:
            # If no user provided or user is not authenticated, hide the field
            del self.fields['driver_assignment']

        # Dynamically add route fields based on active routes
        active_routes = Route.objects.filter(is_active=True)
        for route in active_routes:
            field_name = f'route_{route.id}'
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=f"{route.route_name} ({route.start} to {route.finish})",
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
    
    class Meta:
        model = DailyReportModel_Revenue
        fields = ['fleet_no', 'vehicle_no', 'no_of_loads', 'date']


#Route Management Forms
class RouteForm(forms.ModelForm):
    route_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter route name'})
    )
    
    start = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Start location'})
    )
    
    finish = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'End location'})
    )
    
    transport_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rate per ton', 'step': '0.01'}),
        help_text="Actual transport rate per ton for this route"
    )
    
    planned_revenue = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected revenue per load', 'step': '0.01'}),
        help_text="Expected revenue per load for variance calculations"
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Route
        fields = ['route_name', 'start', 'finish', 'transport_rate', 'planned_revenue', 'is_active']


#Fuel Rate Management Form
class FuelRateForm(forms.ModelForm):
    fuel_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter new fuel rate per litre',
            'step': '0.01',
            'min': '0'
        }),
        help_text="This rate will apply to all trucks in the system"
    )
    
    name = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a name for this fuel rate setting'
        }),
        initial="Current Fuel Rate",
        help_text="Optional: Give this fuel rate setting a descriptive name"
    )
    
    class Meta:
        model = FuelRateModel
        fields = ['fuel_rate', 'name']
        
    def clean_fuel_rate(self):
        fuel_rate = self.cleaned_data['fuel_rate']
        if fuel_rate <= 0:
            raise forms.ValidationError("Fuel rate must be greater than 0")
        return fuel_rate


#Vehicle Management Forms
class VehicleForm(forms.ModelForm):
    vehicle_make = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter vehicle make (e.g., Toyota, Ford, Mercedes)'
        }),
        help_text="Vehicle manufacturer or brand"
    )
    
    vehicle_registration_no = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter registration number (e.g., ABC123GP)'
        }),
        help_text="Unique vehicle registration number"
    )
    
    vehicle_registration_expiry = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="When the vehicle registration expires"
    )
    
    fleetcam_link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://fleetcam.example.com/vehicle/123'
        }),
        help_text="Optional: Link to FleetCam monitoring system for this vehicle"
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Check if vehicle is currently active"
    )
    
    class Meta:
        model = Vehicle
        fields = ['vehicle_make', 'vehicle_registration_no', 'vehicle_registration_expiry', 'fleetcam_link', 'is_active']
        
    def clean_vehicle_registration_no(self):
        registration_no = self.cleaned_data['vehicle_registration_no'].upper()
        
        # Check for uniqueness excluding current instance if editing
        queryset = Vehicle.objects.filter(vehicle_registration_no=registration_no)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise forms.ValidationError("A vehicle with this registration number already exists.")
        
        return registration_no

