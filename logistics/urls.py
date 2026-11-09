from django.urls import path
from . import views 

app_name = 'logistics'

urlpatterns = [

    path('all_deliveries/', views.all_deliveries, name = 'all_deliveries'),
    path('create_delivery/', views.create_delivery, name = 'create_delivery'),

]