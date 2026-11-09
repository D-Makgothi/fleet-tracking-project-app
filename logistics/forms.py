from django import forms
from .models import ManageDeliveryModel

# Form Creation
class ManageDeliveryForm(forms.ModelForm):
    client = forms.CharField(
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter client name', 'class': 'form-control'})
    )
    
    load_dateline = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    route_taken = forms.ChoiceField(
        choices=ManageDeliveryModel.ROUTE_CHOICES,
        required=True,
        label="Route Taken",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    vehicle_registration = forms.CharField(
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Vehicle Registration Number', 'class': 'form-control'})
    )

    vehicle_driver = forms.CharField(
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter driver name', 'class': 'form-control'})
    )

    load_quantity = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Load quantity (in tonnes)', 'class': 'form-control'})
    )

    order_number = forms.CharField(
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter order number', 'class': 'form-control'})
    )

    class Meta:
        model = ManageDeliveryModel
        fields = ['client', 'load_dateline', 'route_taken', 'vehicle_registration', 'vehicle_driver', 'load_quantity', 'order_number']

    def clean_load_quantity(self):
        load_quantity = self.cleaned_data.get('load_quantity')
        if load_quantity <= 0:
            raise forms.ValidationError("Load quantity must be positive.")
        return load_quantity

    def clean_order_number(self):
        order_number = self.cleaned_data.get('order_number')
        if ManageDeliveryModel.objects.filter(order_number=order_number).exists():
            raise forms.ValidationError("Order number must be unique.")
        return order_number

# Form Editing
# class ManageDeliveryEditForm(forms.ModelForm):
#     client = forms.CharField(
#         max_length=60,
#         required=True,
#         widget=forms.TextInput(attrs={'placeholder': 'Enter client name', 'class': 'form-control'})
#     )
    
#     load_dateline = forms.DateField(
#         required=True,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )

#     route_taken = forms.ChoiceField(
#         choices=ManageDeliveryModel.ROUTE_CHOICES,
#         required=True,
#         label="Route Taken",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
    
#     vehicle_registration = forms.CharField(
#         max_length=60,
#         required=True,
#         widget=forms.TextInput(attrs={'placeholder': 'Vehicle Registration Number', 'class': 'form-control'})
#     )

#     vehicle_driver = forms.CharField(
#         max_length=60,
#         required=True,
#         widget=forms.TextInput(attrs={'placeholder': 'Enter driver name', 'class': 'form-control'})
#     )

#     load_quantity = forms.IntegerField(
#         required=True,
#         widget=forms.NumberInput(attrs={'placeholder': 'Load quantity (in tonnes)', 'class': 'form-control'})
#     )

#     order_number = forms.CharField(
#         max_length=60,
#         required=True,
#         widget=forms.TextInput(attrs={'placeholder': 'Enter order number', 'class': 'form-control'})
#     )

#     class Meta:
#         model = ManageDeliveryModel
#         fields = ['client', 'load_dateline', 'route_taken', 'vehicle_registration', 'vehicle_driver', 'load_quantity', 'order_number']

#     def clean_load_quantity(self):
#         load_quantity = self.cleaned_data.get('load_quantity')
#         if load_quantity <= 0:
#             raise forms.ValidationError("Load quantity must be positive.")
#         return load_quantity

#     def clean_order_number(self):
#         order_number = self.cleaned_data.get('order_number')
#         instance = self.instance
#         if ManageDeliveryModel.objects.filter(order_number=order_number).exclude(id=instance.id).exists():
#             raise forms.ValidationError("Order number must be unique.")
#         return order_number

# # Form Deletion
# class ManageDeliveryDeleteForm(forms.Form):
#     confirm = forms.BooleanField(
#         required=True,
#         label="Confirm deletion",
#         help_text="Check this box to confirm you want to delete this delivery record."
#     )