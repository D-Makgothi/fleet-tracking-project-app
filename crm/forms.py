from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import AgentModel, CRMClient, CRMSite, ClientInteraction, AIHuntingLog
import uuid


# Agent Registration Form
class AgentRegistrationForm(forms.ModelForm):
    # User account fields (for real agents)
    username = forms.CharField(
        max_length=150, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username (for real agents only)'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }),
        required=False,
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        }),
        required=False,
        label="Confirm Password"
    )
    
    # Agent type selection
    agent_type = forms.ChoiceField(
        choices=AgentModel.AGENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Agent Type"
    )
    
    # Personal details
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    age = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Age'
        })
    )
    
    # Professional details
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department'
        })
    )
    salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Salary',
            'step': '0.01'
        })
    )
    commission_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=5.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Commission Rate (%)',
            'step': '0.01'
        })
    )
    
    # AI Agent specific fields
    target_region = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Target Region (for AI agents)'
        })
    )
    hunting_frequency_hours = forms.IntegerField(
        initial=24,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hunting Frequency (hours)'
        })
    )
    ai_model_version = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'AI Model Version'
        })
    )
    
    class Meta:
        model = AgentModel
        fields = [
            'agent_type', 'first_name', 'last_name', 'email', 'phone_number', 
            'age', 'department', 'salary', 'commission_rate', 'target_region',
            'hunting_frequency_hours', 'ai_model_version'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        agent_type = cleaned_data.get('agent_type')
        username = cleaned_data.get('username')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # For real agents, require username and password
        if agent_type == 'real':
            if not username:
                raise forms.ValidationError("Username is required for real agents.")
            if not password1:
                raise forms.ValidationError("Password is required for real agents.")
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        agent = super().save(commit=False)
        
        # Generate agent ID if not exists
        if not agent.agent_id:
            agent.agent_id = f"AGT{str(uuid.uuid4())[:8].upper()}"
        
        if commit:
            # Create user account for real agents
            if agent.agent_type == 'real' and self.cleaned_data.get('username'):
                user = User.objects.create_user(
                    username=self.cleaned_data['username'],
                    email=agent.email,
                    password=self.cleaned_data['password1'],
                    first_name=agent.first_name,
                    last_name=agent.last_name
                )
                agent.user = user
            
            agent.save()
        
        return agent


# CRM Client Form
class CRMClientForm(forms.ModelForm):
    client_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Client Name'
        })
    )
    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company Name'
        })
    )
    client_contact = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Primary Phone'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    
    # Address fields
    address_line_1 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address Line 1'
        })
    )
    address_line_2 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address Line 2'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    province_state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Province/State'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code'
        })
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    
    # Business information
    industry = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Industry'
        })
    )
    company_size = forms.ChoiceField(
        choices=[('', 'Select Company Size')] + CRMClient.COMPANY_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    annual_revenue = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Annual Revenue',
            'step': '0.01'
        })
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Website URL'
        })
    )
    
    # CRM fields
    status = forms.ChoiceField(
        choices=CRMClient.CLIENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=CRMClient.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    potential_value = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Potential Value',
            'step': '0.01'
        })
    )
    
    # Fleet service fields
    estimated_vehicles_needed = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Estimated Vehicles Needed'
        })
    )
    preferred_routes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Preferred Routes',
            'rows': 3
        })
    )
    
    # Additional fields
    source = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lead Source'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notes',
            'rows': 4
        })
    )
    
    class Meta:
        model = CRMClient
        fields = [
            'client_name', 'company_name', 'client_contact', 'email',
            'address_line_1', 'address_line_2', 'city', 'province_state',
            'postal_code', 'country', 'industry', 'company_size',
            'annual_revenue', 'website', 'status', 'priority',
            'potential_value', 'estimated_vehicles_needed', 'preferred_routes',
            'source', 'notes'
        ]


# Client Interaction Form
class ClientInteractionForm(forms.ModelForm):
    interaction_type = forms.ChoiceField(
        choices=ClientInteraction.INTERACTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Interaction Subject'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Interaction Details',
            'rows': 4
        })
    )
    outcome = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Outcome/Result',
            'rows': 3
        })
    )
    next_action = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Next Action Required'
        })
    )
    next_action_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    duration_minutes = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Duration (minutes)'
        })
    )
    satisfaction_rating = forms.ChoiceField(
        choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = ClientInteraction
        fields = [
            'interaction_type', 'subject', 'description', 'outcome',
            'next_action', 'next_action_date', 'duration_minutes',
            'satisfaction_rating'
        ]


# AI Agent Search Configuration Form
class AIAgentConfigForm(forms.Form):
    target_region = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Johannesburg, South Africa'
        })
    )
    search_keywords = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'mining, transport, logistics, fleet services',
            'rows': 3
        }),
        help_text="Enter keywords separated by commas"
    )
    max_results = forms.IntegerField(
        initial=50,
        min_value=1,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum results to fetch'
        })
    )
    industry_filters = forms.MultipleChoiceField(
        choices=[
            ('mining', 'Mining'),
            ('logistics', 'Logistics'),
            ('transport', 'Transport'),
            ('construction', 'Construction'),
            ('manufacturing', 'Manufacturing'),
            ('agriculture', 'Agriculture'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )


# Quick Client Add Form (for agents hunting)
class QuickClientForm(forms.ModelForm):
    class Meta:
        model = CRMClient
        fields = [
            'client_name', 'company_name', 'client_contact', 'email',
            'city', 'industry', 'status', 'source', 'notes'
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }