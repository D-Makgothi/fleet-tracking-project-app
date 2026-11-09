from django.shortcuts import render, redirect
from .models import ManageDeliveryModel
from .forms import ManageDeliveryForm

# Manage Delivery Form

# Create a Delivery
def create_delivery(request):
    if request.method == "POST":
        form = ManageDeliveryForm(request.POST)
        if form.is_valid():
            form.save()  # This line already saves the instance with all valid data
            return redirect('main:home')
    else:
        form = ManageDeliveryForm()

    context = {
        'form': form
    }

    return render(request, 'logistics/create_delivery.html', context)

# Display All Delivery Details
def all_deliveries(request):
    delivery_data = ManageDeliveryModel.objects.all()
    context = {
        'delivery_data': delivery_data
    }
    
    return render(request, 'logistics/all_deliveries.html', context)