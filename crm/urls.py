from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # CRM Dashboard
    path('', views.crm_dashboard, name='dashboard'),
    
    # Agent Management
    path('agents/', views.agent_list, name='agents'),
    path('agents/add/', views.agent_add, name='agent_add'),
    path('agents/<int:agent_id>/', views.agent_detail, name='agent_detail'),
    path('agents/<int:agent_id>/edit/', views.agent_edit, name='agent_edit'),
    path('agents/<int:agent_id>/delete/', views.agent_delete, name='agent_delete'),
    
    # Client Management
    path('clients/', views.client_list, name='clients'),
    path('clients/add/', views.client_add, name='client_add'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:client_id>/delete/', views.client_delete, name='client_delete'),
    
    # Client Interactions
    path('interactions/', views.interaction_list, name='interactions'),
    path('interactions/add/', views.interaction_add, name='interaction_add'),
    path('interactions/<int:interaction_id>/', views.interaction_detail, name='interaction_detail'),
    path('interactions/<int:interaction_id>/edit/', views.interaction_edit, name='interaction_edit'),
    
    # Agent Performance
    path('performance/', views.performance_dashboard, name='performance'),
    path('performance/<int:agent_id>/', views.agent_performance_detail, name='agent_performance_detail'),
    
    # AI Hunting Logs
    path('hunting-logs/', views.hunting_logs, name='hunting_logs'),
    path('hunting-logs/<int:log_id>/', views.hunting_log_detail, name='hunting_log_detail'),
    path('hunting-logs/<str:session_id>/cancel/', views.cancel_hunting_session, name='cancel_hunting_session'),
    
    # Prospect Approval Workflow
    path('prospects/', views.prospect_approval_list, name='prospect_approval_list'),
    path('prospects/<int:prospect_id>/', views.prospect_detail, name='prospect_detail'),
    path('prospects/<int:prospect_id>/approve/', views.approve_prospect, name='approve_prospect'),
    path('prospects/<int:prospect_id>/reject/', views.reject_prospect, name='reject_prospect'),
    
    # AI Hunting Actions
    path('simulate-hunting/', views.simulate_ai_hunting, name='simulate_hunting'),
    path('start-daily-hunting/', views.start_daily_hunting, name='start_daily_hunting'),
    
    # AJAX endpoints
    path('ajax/client-status/', views.update_client_status, name='update_client_status'),
    path('ajax/start-hunting/', views.start_ai_hunting, name='start_ai_hunting'),
    path('ajax/toggle-agent-status/<int:agent_id>/', views.toggle_agent_status, name='toggle_agent_status'),
    path('ajax/toggle-agent-hunting/<int:agent_id>/', views.toggle_agent_hunting, name='toggle_agent_hunting'),
]