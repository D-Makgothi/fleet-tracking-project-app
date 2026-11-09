from django.urls import path 
from . import views 

app_name = 'register_login'

urlpatterns = [
    path('register/', views.register, name="register"),
    path('login/', views.login_view, name="login"), 

    #Register Clients
    path('register_client/', views.register_client, name="register_client"),
    path('<int:pk>/edit_client/', views.edit_client, name='edit_client'),
    path('<int:pk>/delete_client/', views.delete_client, name='delete_client'), # URL Patterns aren't necessarily pages. They are bridges that allow us to acess the functionality of a view. Such as deletion, creation or editing.

    #Register Sites
    path('register_site/', views.register_site, name="register_site"),
    path('<int:pk>/edit_site/', views.edit_site, name='edit_site'), #Something's Fishy here
    path('<int:pk>/delete_site/', views.delete_site, name='delete_site'), # URL Patterns aren't necessarily pages. They are bridges that allow us to acess the functionality of a view. Such as deletion, creation or editing.

    #Register Controllers
    path('register_controller/', views.register_controller, name="register_controller"),
    path('<int:pk>/edit_controller/', views.edit_controller, name='edit_controller'),
    path('<int:pk>/delete_controller/', views.delete_controller, name='delete_controller'),
    
    #Controller Activity and Shift Management
    path('controller-activity-log/', views.controller_activity_log_view, name='controller_activity_log'),
    path('shift-handover-dashboard/', views.shift_handover_dashboard, name='shift_handover_dashboard'),

]