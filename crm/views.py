from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from .models import AgentModel, CRMClient, CRMSite, ClientInteraction, AIHuntingLog, AgentPerformance, AIHuntedProspect
from .forms import AgentRegistrationForm, CRMClientForm, ClientInteractionForm


@login_required
def crm_dashboard(request):
    """
    AI Fleet Management CRM Dashboard - Focus on prospect approval workflow
    """
    # Key Metrics
    total_agents = AgentModel.objects.filter(status='active').count()
    
    # Prospect Approval Metrics
    pending_prospects = AIHuntedProspect.objects.filter(approval_status='pending').count()
    approved_prospects = AIHuntedProspect.objects.filter(approval_status='approved').count()
    rejected_prospects = AIHuntedProspect.objects.filter(approval_status='rejected').count()
    converted_clients = AIHuntedProspect.objects.filter(converted_to_client__isnull=False).count()
    
    # Recent AI Hunted Prospects (Pending Approval)
    recent_prospects = AIHuntedProspect.objects.filter(
        approval_status='pending'
    ).select_related('agent').order_by('-discovered_at')[:10]
    
    # Today's Hunting Activity
    today = timezone.now().date()
    todays_prospects = AIHuntedProspect.objects.filter(discovered_at__date=today)
    agents_hunted_today = todays_prospects.values('agent').distinct().count()
    
    # Agent Performance Summary
    top_agents = AgentModel.objects.annotate(
        prospects_found=Count('hunted_prospects'),
        approved_count=Count('hunted_prospects', filter=Q(hunted_prospects__approval_status='approved')),
        converted_count=Count('hunted_prospects', filter=Q(hunted_prospects__converted_to_client__isnull=False))
    ).order_by('-prospects_found')[:5]
    
    # Fleet Management Focus Stats
    fleet_focused_prospects = AIHuntedProspect.objects.filter(
        needs_fleet_management=True,
        approval_status='pending'
    ).count()
    
    # AI Hunting Stats (last 7 days)
    last_7_days = timezone.now() - timedelta(days=7)
    weekly_stats = AIHuntedProspect.objects.filter(
        discovered_at__gte=last_7_days
    ).aggregate(
        total_hunted=Count('id'),
        avg_confidence=Avg('confidence_score'),
        fleet_focused=Count('id', filter=Q(needs_fleet_management=True))
    )
    
    # Agents ready for hunting today
    agents_ready_to_hunt = []
    for agent in AgentModel.objects.filter(status='active', is_auto_hunting=True):
        if agent.should_hunt_today() and agent.get_daily_hunt_count() < agent.max_daily_prospects:
            agents_ready_to_hunt.append({
                'agent': agent,
                'hunted_today': agent.get_daily_hunt_count(),
                'max_daily': agent.max_daily_prospects
            })
    
    context = {
        'total_agents': total_agents,
        'pending_prospects': pending_prospects,
        'approved_prospects': approved_prospects,
        'rejected_prospects': rejected_prospects,
        'converted_clients': converted_clients,
        'recent_prospects': recent_prospects,
        'todays_prospects_count': todays_prospects.count(),
        'agents_hunted_today': agents_hunted_today,
        'top_agents': top_agents,
        'fleet_focused_prospects': fleet_focused_prospects,
        'weekly_stats': weekly_stats,
        'agents_ready_to_hunt': agents_ready_to_hunt,
    }
    
    return render(request, 'crm/dashboard.html', context)


@login_required
def agent_list(request):
    """
    List all agents with filtering and search capabilities
    """
    agents = AgentModel.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        agents = agents.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(agent_id__icontains=search_query)
        )
    
    # Filter by agent type
    agent_type = request.GET.get('type', '')
    if agent_type:
        agents = agents.filter(agent_type=agent_type)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        agents = agents.filter(status=status)
    
    context = {
        'agents': agents,
        'search_query': search_query,
        'agent_type': agent_type,
        'status': status,
    }
    
    return render(request, 'crm/agents/agent_list.html', context)


@login_required
def agent_add(request):
    """
    Add new agent (real or AI)
    """
    if request.method == 'POST':
        form = AgentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f'Agent {agent.full_name} has been successfully registered!')
            return redirect('crm:agent_detail', agent_id=agent.id)
    else:
        form = AgentRegistrationForm()
    
    return render(request, 'crm/agents/agent_add.html', {'form': form})


@login_required
def agent_detail(request, agent_id):
    """
    Detailed view of a specific agent
    """
    agent = get_object_or_404(AgentModel, id=agent_id)
    
    # Agent's clients
    clients = agent.crm_clients.all().order_by('-created_at')
    
    # Recent interactions
    recent_interactions = ClientInteraction.objects.filter(
        agent=agent
    ).order_by('-interaction_date')[:10]
    
    # Performance metrics
    total_clients = clients.count()
    active_clients = clients.filter(status='active').count()
    total_potential_value = clients.aggregate(
        total=Sum('potential_value')
    )['total'] or Decimal('0.00')
    
    # AI hunting logs (if AI agent)
    hunting_logs = None
    if agent.is_ai_agent:
        hunting_logs = agent.hunting_logs.order_by('-created_at')[:5]
    
    context = {
        'agent': agent,
        'clients': clients,
        'recent_interactions': recent_interactions,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'total_potential_value': total_potential_value,
        'hunting_logs': hunting_logs,
    }
    
    return render(request, 'crm/agents/agent_detail.html', context)


@login_required
def agent_edit(request, agent_id):
    """
    Edit agent details
    """
    agent = get_object_or_404(AgentModel, id=agent_id)
    
    if request.method == 'POST':
        form = AgentRegistrationForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, f'Agent {agent.full_name} has been updated successfully!')
            return redirect('crm:agent_detail', agent_id=agent.id)
    else:
        form = AgentRegistrationForm(instance=agent)
    
    return render(request, 'crm/agents/agent_edit.html', {'form': form, 'agent': agent})


@login_required
def agent_delete(request, agent_id):
    """
    Delete agent (with confirmation)
    """
    agent = get_object_or_404(AgentModel, id=agent_id)
    
    if request.method == 'POST':
        agent_name = agent.full_name
        agent.delete()
        messages.success(request, f'Agent {agent_name} has been deleted successfully!')
        return redirect('crm:agents')
    
    return render(request, 'crm/agents/agent_delete.html', {'agent': agent})


@login_required
def client_list(request):
    """
    List all CRM clients with filtering and search
    """
    clients = CRMClient.objects.select_related('agent').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        clients = clients.filter(
            Q(client_name__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        clients = clients.filter(status=status)
    
    # Filter by priority
    priority = request.GET.get('priority', '')
    if priority:
        clients = clients.filter(priority=priority)
    
    # Filter by agent
    agent_id = request.GET.get('agent', '')
    if agent_id:
        clients = clients.filter(agent_id=agent_id)
    
    # Get all agents for filter dropdown
    agents = AgentModel.objects.filter(status='active').order_by('first_name', 'last_name')
    
    context = {
        'clients': clients,
        'search_query': search_query,
        'status': status,
        'priority': priority,
        'agent_id': agent_id,
        'agents': agents,
    }
    
    return render(request, 'crm/clients/client_list.html', context)


@login_required
def client_add(request):
    """
    Add new CRM client
    """
    if request.method == 'POST':
        form = CRMClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client {client.client_name} has been added successfully!')
            return redirect('crm:client_detail', client_id=client.id)
    else:
        form = CRMClientForm()
    
    return render(request, 'crm/clients/client_add.html', {'form': form})


@login_required
def client_detail(request, client_id):
    """
    Detailed view of a specific client
    """
    client = get_object_or_404(CRMClient, id=client_id)
    
    # Client's sites
    sites = client.sites.all().order_by('-created_at')
    
    # Client interactions
    interactions = client.interactions.select_related('agent').order_by('-interaction_date')
    
    # Summary metrics
    total_interactions = interactions.count()
    last_contact = interactions.first()
    
    context = {
        'client': client,
        'sites': sites,
        'interactions': interactions,
        'total_interactions': total_interactions,
        'last_contact': last_contact,
    }
    
    return render(request, 'crm/clients/client_detail.html', context)


@login_required
def client_edit(request, client_id):
    """
    Edit client details
    """
    client = get_object_or_404(CRMClient, id=client_id)
    
    if request.method == 'POST':
        form = CRMClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client {client.client_name} has been updated successfully!')
            return redirect('crm:client_detail', client_id=client.id)
    else:
        form = CRMClientForm(instance=client)
    
    return render(request, 'crm/clients/client_edit.html', {'form': form, 'client': client})


@login_required
def client_delete(request, client_id):
    """
    Delete client (with confirmation)
    """
    client = get_object_or_404(CRMClient, id=client_id)
    
    if request.method == 'POST':
        client_name = client.client_name
        client.delete()
        messages.success(request, f'Client {client_name} has been deleted successfully!')
        return redirect('crm:clients')
    
    return render(request, 'crm/clients/client_delete.html', {'client': client})


@login_required
def interaction_list(request):
    """
    List all client interactions
    """
    interactions = ClientInteraction.objects.select_related(
        'client', 'agent'
    ).order_by('-interaction_date')
    
    # Filter by interaction type
    interaction_type = request.GET.get('type', '')
    if interaction_type:
        interactions = interactions.filter(interaction_type=interaction_type)
    
    # Filter by agent
    agent_id = request.GET.get('agent', '')
    if agent_id:
        interactions = interactions.filter(agent_id=agent_id)
    
    # Filter by client
    client_id = request.GET.get('client', '')
    if client_id:
        interactions = interactions.filter(client_id=client_id)
    
    # Get filter options
    agents = AgentModel.objects.filter(status='active').order_by('first_name', 'last_name')
    clients = CRMClient.objects.order_by('client_name')
    
    context = {
        'interactions': interactions,
        'interaction_type': interaction_type,
        'agent_id': agent_id,
        'client_id': client_id,
        'agents': agents,
        'clients': clients,
    }
    
    return render(request, 'crm/interactions/interaction_list.html', context)


@login_required
def interaction_add(request):
    """
    Add new client interaction
    """
    if request.method == 'POST':
        form = ClientInteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save()
            messages.success(request, 'Interaction has been logged successfully!')
            return redirect('crm:interaction_detail', interaction_id=interaction.id)
    else:
        form = ClientInteractionForm()
    
    return render(request, 'crm/interactions/interaction_add.html', {'form': form})


@login_required
def interaction_detail(request, interaction_id):
    """
    Detailed view of a specific interaction
    """
    interaction = get_object_or_404(ClientInteraction, id=interaction_id)
    
    context = {
        'interaction': interaction,
    }
    
    return render(request, 'crm/interactions/interaction_detail.html', context)


@login_required
def interaction_edit(request, interaction_id):
    """
    Edit interaction details
    """
    interaction = get_object_or_404(ClientInteraction, id=interaction_id)
    
    if request.method == 'POST':
        form = ClientInteractionForm(request.POST, instance=interaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Interaction has been updated successfully!')
            return redirect('crm:interaction_detail', interaction_id=interaction.id)
    else:
        form = ClientInteractionForm(instance=interaction)
    
    return render(request, 'crm/interactions/interaction_edit.html', {'form': form, 'interaction': interaction})


@login_required
def performance_dashboard(request):
    """
    Agent performance dashboard with analytics
    """
    # Get all agents with performance metrics
    agents = AgentModel.objects.annotate(
        client_count=Count('crm_clients'),
        active_client_count=Count('crm_clients', filter=Q(crm_clients__status='active')),
        total_potential=Sum('crm_clients__potential_value'),
        avg_satisfaction=Avg('clientinteraction__satisfaction_rating')
    ).order_by('-client_count')
    
    # Monthly performance trends (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_performance = AgentPerformance.objects.filter(
        created_at__gte=six_months_ago
    ).values('month', 'year').annotate(
        total_clients_acquired=Sum('clients_converted'),
        total_revenue=Sum('total_actual_revenue'),
        total_commission=Sum('commission_earned')
    ).order_by('year', 'month')
    
    context = {
        'agents': agents,
        'monthly_performance': monthly_performance,
    }
    
    return render(request, 'crm/performance/dashboard.html', context)


@login_required
def agent_performance_detail(request, agent_id):
    """
    Detailed performance view for specific agent
    """
    agent = get_object_or_404(AgentModel, id=agent_id)
    
    # Performance records
    performance_records = agent.performance_records.order_by('-year', '-month')
    
    # Current month metrics
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    current_performance, created = AgentPerformance.objects.get_or_create(
        agent=agent,
        month=current_month,
        year=current_year
    )
    
    context = {
        'agent': agent,
        'performance_records': performance_records,
        'current_performance': current_performance,
    }
    
    return render(request, 'crm/performance/agent_detail.html', context)


@login_required
def hunting_logs(request):
    """
    List all AI hunting logs
    """
    logs = AIHuntingLog.objects.select_related('agent').order_by('-created_at')
    
    # Filter by agent
    agent_id = request.GET.get('agent', '')
    if agent_id:
        logs = logs.filter(agent_id=agent_id)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        logs = logs.filter(status=status)
    
    # Get AI agents for filter
    ai_agents = AgentModel.objects.filter(agent_type='ai', status='active')
    
    context = {
        'logs': logs,
        'agent_id': agent_id,
        'status': status,
        'ai_agents': ai_agents,
    }
    
    return render(request, 'crm/hunting/log_list.html', context)


@login_required
def hunting_log_detail(request, log_id):
    """
    Detailed view of hunting log
    """
    log = get_object_or_404(AIHuntingLog, id=log_id)
    
    context = {
        'log': log,
    }
    
    return render(request, 'crm/hunting/log_detail.html', context)


@login_required
def update_client_status(request):
    """
    AJAX endpoint to update client status
    """
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        new_status = request.POST.get('status')
        
        try:
            client = CRMClient.objects.get(id=client_id)
            client.status = new_status
            client.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Client status updated to {new_status.title()}'
            })
        except CRMClient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Client not found'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def start_ai_hunting(request):
    """
    AJAX endpoint to start AI hunting session
    """
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        target_region = request.POST.get('target_region', '')
        search_keywords = request.POST.get('search_keywords', '')
        max_results = int(request.POST.get('max_results', 50))
        
        try:
            agent = AgentModel.objects.get(id=agent_id, agent_type='ai')
            
            # Create hunting session
            session_id = f"HUNT_{uuid.uuid4().hex[:8].upper()}"
            hunting_log = AIHuntingLog.objects.create(
                agent=agent,
                hunting_session_id=session_id,
                target_region=target_region,
                search_keywords=search_keywords,
                max_results=max_results,
                start_time=timezone.now(),
                status='running'
            )
            
            # Simulate AI hunting process with realistic timing and results
            import threading
            import time
            import random

            def simulate_hunting():
                try:
                    # Simulate hunting time (2-5 minutes)
                    hunting_duration = random.randint(120, 300)  # 2-5 minutes in seconds
                    time.sleep(hunting_duration)

                    # Simulate realistic results based on max_results
                    base_prospects = min(max_results, random.randint(5, 25))
                    prospects_found = random.randint(base_prospects // 2, base_prospects)
                    valid_contacts = random.randint(prospects_found // 3, prospects_found // 2)
                    clients_created = random.randint(0, valid_contacts // 3)

                    # Simulate API usage
                    api_calls = random.randint(prospects_found * 2, prospects_found * 4)
                    api_quota_used = round(random.uniform(5.0, 25.0), 2)

                    # Update hunting log with results
                    hunting_log.refresh_from_db()
                    hunting_log.prospects_found = prospects_found
                    hunting_log.valid_contacts = valid_contacts
                    hunting_log.clients_created = clients_created
                    hunting_log.api_calls_made = api_calls
                    hunting_log.api_quota_used = api_quota_used
                    hunting_log.end_time = timezone.now()
                    hunting_log.status = 'completed'
                    hunting_log.save()

                    # Create sample AI-hunted prospects for approval
                    sample_companies = [
                        "Logistics Solutions Inc", "Transport Masters Ltd", "Freight Forward Co",
                        "Supply Chain Experts", "Cargo Connect SA", "Fleet Management Pro",
                        "Distribution Dynamics", "Shipping Solutions Ltd", "Transport Hub Co"
                    ]

                    sample_contacts = [
                        ("John", "Smith"), ("Sarah", "Johnson"), ("Mike", "Brown"),
                        ("Lisa", "Davis"), ("Tom", "Wilson"), ("Anna", "Taylor"),
                        ("David", "Anderson"), ("Maria", "Garcia"), ("Chris", "Martinez")
                    ]

                    # Create prospects for approval
                    for i in range(min(valid_contacts, 5)):  # Create up to 5 sample prospects
                        company = random.choice(sample_companies)
                        first_name, last_name = random.choice(sample_contacts)

                        AIHuntedProspect.objects.create(
                            agent=agent,
                            hunting_session=hunting_log,
                            business_name=company,
                            contact_person=f"{first_name} {last_name}",
                            email=f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
                            phone=f"+27 {random.randint(10, 99)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
                            website=f"www.{company.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
                            industry="Transportation & Logistics",
                            estimated_revenue=random.randint(50000, 500000),
                            hunt_source=random.choice(['google_search', 'business_directories', 'linkedin']),
                            confidence_score=random.randint(70, 95),
                            approval_status='pending'
                        )

                except Exception as e:
                    # Handle any errors during simulation
                    hunting_log.refresh_from_db()
                    hunting_log.status = 'failed'
                    hunting_log.error_log = str(e)
                    hunting_log.end_time = timezone.now()
                    hunting_log.save()

            # Start hunting simulation in background thread
            hunting_thread = threading.Thread(target=simulate_hunting)
            hunting_thread.daemon = True
            hunting_thread.start()

            return JsonResponse({
                'success': True,
                'message': f'AI hunting session {session_id} started successfully',
                'session_id': session_id,
                'estimated_duration': '2-5 minutes'
            })
            
        except AgentModel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'AI Agent not found'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def cancel_hunting_session(request, session_id):
    """
    Cancel a running hunting session
    """
    try:
        hunting_log = get_object_or_404(AIHuntingLog, hunting_session_id=session_id)

        if hunting_log.status == 'running':
            hunting_log.status = 'cancelled'
            hunting_log.end_time = timezone.now()
            hunting_log.error_log = 'Session cancelled by user'
            hunting_log.save()

            messages.success(request, f'Hunting session {session_id} has been cancelled.')
        else:
            messages.warning(request, f'Session {session_id} is not running and cannot be cancelled.')

    except AIHuntingLog.DoesNotExist:
        messages.error(request, 'Hunting session not found.')

    return redirect('crm:hunting_logs')


# AI Hunted Prospects Views
@login_required
def prospect_approval_list(request):
    """
    List all AI-hunted prospects for approval/rejection
    """
    prospects = AIHuntedProspect.objects.select_related('agent').order_by('-discovered_at')
    
    # Filter by status
    status = request.GET.get('status', 'pending')
    if status:
        prospects = prospects.filter(approval_status=status)
    
    # Filter by agent
    agent_id = request.GET.get('agent', '')
    if agent_id:
        prospects = prospects.filter(agent_id=agent_id)
    
    # Filter by fleet management need
    fleet_only = request.GET.get('fleet_only', '')
    if fleet_only == 'true':
        prospects = prospects.filter(needs_fleet_management=True)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        prospects = prospects.filter(
            Q(business_name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    # Get all agents for filter
    agents = AgentModel.objects.filter(status='active').order_by('first_name', 'last_name')
    
    # Get counts for dashboard cards
    all_prospects = AIHuntedProspect.objects.all()
    approved_count = all_prospects.filter(approval_status='approved').count()
    rejected_count = all_prospects.filter(approval_status='rejected').count()
    fleet_focused_count = all_prospects.filter(needs_fleet_management=True).count()
    
    context = {
        'prospects': prospects,
        'status': status,
        'agent_id': agent_id,
        'fleet_only': fleet_only,
        'search_query': search_query,
        'agents': agents,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'fleet_focused_count': fleet_focused_count,
    }
    
    return render(request, 'crm/prospects/approval_list.html', context)


@login_required
def prospect_detail(request, prospect_id):
    """
    Detailed view of a hunted prospect
    """
    prospect = get_object_or_404(AIHuntedProspect, id=prospect_id)
    
    context = {
        'prospect': prospect,
    }
    
    return render(request, 'crm/prospects/prospect_detail.html', context)


@login_required
def approve_prospect(request, prospect_id):
    """
    Approve a prospect and optionally convert to client
    """
    prospect = get_object_or_404(AIHuntedProspect, id=prospect_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            prospect.approve(request.user)
            messages.success(request, f'Prospect {prospect.business_name} has been approved!')
            
        elif action == 'approve_and_convert':
            prospect.approve(request.user)
            client = prospect.convert_to_client()
            messages.success(
                request, 
                f'Prospect {prospect.business_name} has been approved and converted to client!'
            )
            return redirect('crm:client_detail', client_id=client.id)
        
        return redirect('crm:prospect_approval_list')
    
    context = {
        'prospect': prospect,
    }
    
    return render(request, 'crm/prospects/approve_prospect.html', context)


@login_required
def reject_prospect(request, prospect_id):
    """
    Reject a prospect with reason
    """
    prospect = get_object_or_404(AIHuntedProspect, id=prospect_id)
    
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '')
        prospect.reject(request.user, reason)
        messages.success(request, f'Prospect {prospect.business_name} has been rejected.')
        return redirect('crm:prospect_approval_list')
    
    context = {
        'prospect': prospect,
    }
    
    return render(request, 'crm/prospects/reject_prospect.html', context)


@login_required
def simulate_ai_hunting(request):
    """
    Simulate AI hunting to create sample prospects for testing
    """
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        
        if not agent_id:
            messages.error(request, 'No agent selected. Please add an AI agent first.')
            return redirect('crm:prospect_approval_list')
        
        try:
            agent = AgentModel.objects.get(id=agent_id)
            
            # Create sample prospects
            sample_prospects = [
                {
                    'business_name': 'Express Logistics Solutions',
                    'contact_person': 'John Smith',
                    'email': 'john@expresslogistics.com',
                    'phone': '+27123456789',
                    'city': 'Johannesburg',
                    'province_state': 'Gauteng',
                    'country': 'South Africa',
                    'industry': 'Logistics & Transportation',
                    'estimated_fleet_size': 25,
                    'confidence_score': Decimal('0.88'),
                    'fleet_management_indicators': 'Fleet tracking, dispatch management, vehicle maintenance mentioned on website'
                },
                {
                    'business_name': 'Metro Delivery Services',
                    'contact_person': 'Sarah Johnson',
                    'email': 'sarah@metrodelivery.co.za',
                    'phone': '+27987654321',
                    'city': 'Cape Town',
                    'province_state': 'Western Cape',
                    'country': 'South Africa',
                    'industry': 'Courier & Delivery',
                    'estimated_fleet_size': 15,
                    'confidence_score': Decimal('0.92'),
                    'fleet_management_indicators': 'Looking for fleet optimization solutions, GPS tracking mentioned'
                }
            ]
            
            # Create hunting session
            session_id = f"SIM_{uuid.uuid4().hex[:8].upper()}"
            hunting_log = AIHuntingLog.objects.create(
                agent=agent,
                hunting_session_id=session_id,
                target_region='South Africa',
                search_keywords=agent.fleet_keywords,
                max_results=2,
                start_time=timezone.now(),
                end_time=timezone.now(),
                status='completed',
                prospects_found=2,
                valid_contacts=2,
                clients_created=0
            )
            
            # Create prospects
            for prospect_data in sample_prospects:
                AIHuntedProspect.objects.create(
                    agent=agent,
                    hunting_session=hunting_log,
                    **prospect_data
                )
            
            # Update agent
            agent.last_hunting_session = timezone.now()
            agent.save()
            
            messages.success(request, f'Simulated hunting session completed! Found 2 prospects.')
            
        except AgentModel.DoesNotExist:
            messages.error(request, 'Agent not found.')
    
    return redirect('crm:prospect_approval_list')


@login_required
def start_daily_hunting(request):
    """
    Start hunting for all eligible agents
    """
    if request.method == 'POST':
        eligible_agents = []
        
        for agent in AgentModel.objects.filter(status='active', is_auto_hunting=True):
            if agent.should_hunt_today() and agent.get_daily_hunt_count() < agent.max_daily_prospects:
                eligible_agents.append(agent)
        
        if eligible_agents:
            # In a real implementation, this would trigger actual AI hunting
            # For now, we'll just update the timestamp
            for agent in eligible_agents:
                agent.last_hunting_session = timezone.now()
                agent.save()
            
            messages.success(
                request, 
                f'Started hunting for {len(eligible_agents)} agents. Check back later for results.'
            )
        else:
            messages.info(request, 'No agents are eligible for hunting at this time.')
    
    return redirect('crm:dashboard')


@login_required
def toggle_agent_status(request, agent_id):
    """
    Toggle agent active/inactive status via AJAX
    """
    if request.method == 'POST':
        try:
            agent = AgentModel.objects.get(id=agent_id)
            
            # Toggle status
            if agent.status == 'active':
                agent.status = 'inactive'
                agent.is_auto_hunting = False  # Disable hunting when deactivated
                status_text = 'deactivated'
                new_status = 'inactive'
            else:
                agent.status = 'active'
                agent.is_auto_hunting = True  # Enable hunting when activated
                status_text = 'activated'
                new_status = 'active'
            
            agent.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Agent {agent.full_name} has been {status_text}',
                'new_status': new_status,
                'new_status_display': agent.get_status_display(),
                'is_hunting': agent.is_auto_hunting
            })
            
        except AgentModel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Agent not found'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def toggle_agent_hunting(request, agent_id):
    """
    Toggle agent auto hunting on/off independently of status
    """
    if request.method == 'POST':
        try:
            agent = AgentModel.objects.get(id=agent_id)
            
            # Only allow hunting toggle if agent is active
            if agent.status != 'active':
                return JsonResponse({
                    'success': False,
                    'message': 'Agent must be active to enable hunting'
                })
            
            # Toggle hunting
            agent.is_auto_hunting = not agent.is_auto_hunting
            agent.save()
            
            hunting_text = 'enabled' if agent.is_auto_hunting else 'disabled'
            
            return JsonResponse({
                'success': True,
                'message': f'Auto-hunting {hunting_text} for {agent.full_name}',
                'is_hunting': agent.is_auto_hunting
            })
            
        except AgentModel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Agent not found'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
