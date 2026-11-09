from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import RegistryModel, ClientModel, SiteModel, ControllerModel

# Sign Up/ Registry Form
class RegistryModelForm(UserCreationForm):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'First name_Last Name'}))
    mine = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Name of mine'}))
    
    # Driver License Fields
    driver_license_no = forms.CharField(max_length=60, required=True, widget=forms.TextInput(attrs={'placeholder': 'Driver\'s License'}))
    driver_license_expiry = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'}))
    
    # Induction License Fields
    induction_license_no = forms.CharField(max_length=60, required=True, widget=forms.TextInput(attrs={'placeholder': 'Induction License'}))
    induction_license_expiry = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'}))
    

    class Meta:
        model = User
        fields = ['username', 'mine', 'password1', 'password2', 'driver_license_no', 'driver_license_expiry', 'induction_license_no', 'induction_license_expiry']

# Login Form with auto Authentication
class LoginForm(forms.Form):
    username = forms.CharField(max_length=60)
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)



# CLIENT STUFF

class ClientModelForm(forms.ModelForm): #Custom Client Creation Form
    manager = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'manager'}))
    site = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'site'}))
    date_created = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'})) 

    class Meta:
        model = ClientModel #We are referncing from the client model 
        fields = ['manager', 'site', 'date_created']

#Edit Client Form
class EditClientForm(forms.ModelForm): #Custom Client Creation Form
    manager = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'manager'}))
    site = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'site'}))
    date_created = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'})) 

    class Meta:
        model = ClientModel #We are referncing from the client model 
        fields = ['manager', 'site', 'date_created']


# SITE STUFF

class SiteModelForm(forms.ModelForm):
    # Custom Client Creation Form
    site_reference = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'manager'}))
    site_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'site'}))
    responsible_user = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Guy in charge of site'}))
    site_coordinator_email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'banele@gmail.com'}))
    
    ACTIVE_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    status = forms.ChoiceField(
        choices=ACTIVE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Site Status"
    )
    
    site_category = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Coal Site/Textile Site'}))

    class Meta:
        model = SiteModel
        fields = ['site_reference', 'site_name', 'responsible_user', 'site_coordinator_email', 'status', 'site_category']

class EditSiteForm(forms.ModelForm):
    # Custom Site Editing Form
    site_reference = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'manager'}))
    site_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'site'}))
    responsible_user = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Guy in charge of site'}))
    site_coordinator_email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'banele@gmail.com'}))
    
    ACTIVE_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    status = forms.ChoiceField(
        choices=ACTIVE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Site Status"
    )
    
    site_category = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Coal Site/Textile Site'}))

    class Meta:
        model = SiteModel
        fields = ['site_reference', 'site_name', 'responsible_user', 'site_coordinator_email', 'status', 'site_category']


# DRIVER EDIT FORM
class EditDriverForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    
    # Registry fields
    mine = forms.CharField(
        max_length=60, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mine Assignment'})
    )
    
    # Driver License Fields
    driver_license_no = forms.CharField(
        max_length=60, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Driver License Number'})
    )
    driver_license_expiry = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Induction License Fields
    induction_license_no = forms.CharField(
        max_length=60, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Induction License Number'})
    )
    induction_license_expiry = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    

    class Meta:
        model = RegistryModel
        fields = [
            'mine', 'driver_license_no', 'driver_license_expiry', 
            'induction_license_no', 'induction_license_expiry'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        registry_instance = super().save(commit=False)
        
        if commit and self.user:
            # Update user fields
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            self.user.save()
            
            # Save registry instance
            registry_instance.save()
        
        return registry_instance


# Controller Registration Form
class ControllerRegistrationForm(UserCreationForm):
    # User fields
    username = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Controller Username'})
    )
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    first_name = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    
    # Controller-specific fields
    phone_number = forms.CharField(
        max_length=20, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    department = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'})
    )
    employee_id = forms.CharField(
        max_length=50, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
            # Create controller profile
            ControllerModel.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', ''),
                department=self.cleaned_data.get('department', ''),
                employee_id=self.cleaned_data.get('employee_id', '')
            )
        
        return user



