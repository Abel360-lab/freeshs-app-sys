"""
Enhanced notification views for service management and bulk notifications.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django import forms
import json

from .models import (
    NotificationLog, SMSNotification, NotificationAnalytics, NotificationTemplate,
    NotificationService, BulkNotification, NotificationQueue
)


@staff_member_required
def service_dashboard(request):
    """Enhanced notification dashboard with service management."""
    
    # Get date range
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get services
    services = NotificationService.objects.all().order_by('service_type', 'name')
    
    # Get service statistics
    service_stats = {}
    for service in services:
        service_stats[service.id] = {
            'uptime': service.uptime,
            'success_rate': service.success_rate,
            'is_healthy': service.is_healthy,
            'processed_today': NotificationLog.objects.filter(
                created_at__date=timezone.now().date(),
                channel=service.service_type
            ).count(),
        }
    
    # Get bulk campaigns
    bulk_campaigns = BulkNotification.objects.all().order_by('-created_at')[:10]
    
    # Get queue statistics
    queue_stats = {
        'pending': NotificationQueue.objects.filter(status='PENDING').count(),
        'processing': NotificationQueue.objects.filter(status='PROCESSING').count(),
        'failed': NotificationQueue.objects.filter(status='FAILED').count(),
        'completed_today': NotificationQueue.objects.filter(
            processed_at__date=timezone.now().date(),
            status='COMPLETED'
        ).count(),
    }
    
    # Get recent notifications
    recent_notifications = NotificationLog.objects.select_related(
        'template', 'application', 'user'
    ).order_by('-created_at')[:20]
    
    # Calculate overall statistics
    total_notifications = NotificationLog.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).count()
    
    email_stats = NotificationLog.objects.filter(
        created_at__date__range=[start_date, end_date],
        channel='EMAIL'
    ).aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='SENT')),
        delivered=Count('id', filter=Q(status__in=['DELIVERED', 'OPENED', 'CLICKED'])),
        failed=Count('id', filter=Q(status='FAILED')),
    )
    
    sms_stats = SMSNotification.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='SENT')),
        delivered=Count('id', filter=Q(status='DELIVERED')),
        failed=Count('id', filter=Q(status='FAILED')),
    )
    
    # Calculate rates
    email_rates = {}
    if email_stats['total'] > 0:
        email_rates['delivery_rate'] = (email_stats['delivered'] / email_stats['total']) * 100
        email_rates['failure_rate'] = (email_stats['failed'] / email_stats['total']) * 100
    
    sms_rates = {}
    if sms_stats['total'] > 0:
        sms_rates['delivery_rate'] = (sms_stats['delivered'] / sms_stats['total']) * 100
        sms_rates['failure_rate'] = (sms_stats['failed'] / sms_stats['total']) * 100
    
    context = {
        'services': services,
        'service_stats': service_stats,
        'bulk_campaigns': bulk_campaigns,
        'queue_stats': queue_stats,
        'recent_notifications': recent_notifications,
        'total_notifications': total_notifications,
        'email_stats': {**email_stats, **email_rates},
        'sms_stats': {**sms_stats, **sms_rates},
        'days': days,
    }
    
    return render(request, 'notifications/dashboard_enhanced.html', context)


@staff_member_required
def service_control(request, service_id, action):
    """Control notification services (start, stop, pause, restart)."""
    try:
        service = NotificationService.objects.get(id=service_id)
    except NotificationService.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Service not found'})
    
    success = False
    message = ''
    
    if action == 'start':
        success = service.start_service()
        message = 'Service started successfully' if success else 'Service cannot be started in current state'
    elif action == 'stop':
        success = service.stop_service()
        message = 'Service stopped successfully' if success else 'Service cannot be stopped in current state'
    elif action == 'pause':
        success = service.pause_service()
        message = 'Service paused successfully' if success else 'Service cannot be paused in current state'
    elif action == 'resume':
        success = service.resume_service()
        message = 'Service resumed successfully' if success else 'Service cannot be resumed in current state'
    elif action == 'restart':
        success = service.restart_service()
        message = 'Service restarted successfully' if success else 'Service cannot be restarted in current state'
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    return JsonResponse({
        'success': success,
        'message': message,
        'service_status': service.status,
        'service_status_display': service.get_status_display()
    })


@staff_member_required
def service_health_check(request, service_id):
    """Perform health check on a service."""
    try:
        service = NotificationService.objects.get(id=service_id)
    except NotificationService.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Service not found'})
    
    # Simulate health check (in real implementation, this would call the actual service)
    import random
    is_healthy = random.choice([True, True, True, False])  # 75% success rate
    
    if is_healthy:
        service.update_health(is_healthy=True)
        message = 'Service is healthy'
    else:
        error_message = 'Connection timeout'
        service.update_health(is_healthy=False, error_message=error_message)
        message = f'Service health check failed: {error_message}'
    
    return JsonResponse({
        'success': True,
        'is_healthy': is_healthy,
        'message': message,
        'last_health_check': service.last_health_check.isoformat() if service.last_health_check else None,
        'error_count': service.error_count,
        'last_error': service.last_error
    })


@staff_member_required
def bulk_campaigns(request):
    """Bulk notification campaigns management."""
    campaigns = BulkNotification.objects.select_related(
        'template', 'created_by'
    ).prefetch_related(
        'recipient_users', 'recipient_applications'
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)
    
    # Paginate
    paginator = Paginator(campaigns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_campaigns = BulkNotification.objects.count()
    active_campaigns = BulkNotification.objects.filter(status='RUNNING').count()
    completed_campaigns = BulkNotification.objects.filter(status='COMPLETED').count()
    
    # Calculate total recipients across all campaigns
    total_recipients = 0
    for campaign in campaigns:
        total_recipients += campaign.total_recipients
    
    context = {
        'campaigns': page_obj,
        'status_choices': BulkNotification.CampaignStatus.choices,
        'current_status': status_filter,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'completed_campaigns': completed_campaigns,
        'total_recipients': total_recipients,
    }
    
    return render(request, 'notifications/bulk_campaigns.html', context)


@staff_member_required
def create_bulk_campaign(request):
    """Create a new bulk notification campaign."""
    
    class BulkCampaignForm(forms.ModelForm):
        class Meta:
            model = BulkNotification
            fields = [
                'name', 'description', 'template', 'channel', 'priority', 'scheduled_at'
            ]
            widgets = {
                'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                'description': forms.Textarea(attrs={'rows': 3}),
            }
    
    if request.method == 'POST':
        form = BulkCampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            
            # Set additional fields from form data
            try:
                campaign.batch_size = int(request.POST.get('batch_size', 100))
                campaign.delay_between_batches = int(request.POST.get('delay_between_batches', 5))
                campaign.max_retries = int(request.POST.get('max_retries', 3))
            except (ValueError, TypeError):
                # Use defaults if conversion fails
                campaign.batch_size = 100
                campaign.delay_between_batches = 5
                campaign.max_retries = 3
            
            campaign.personalize_by_recipient = request.POST.get('personalize_by_recipient') == 'on'
            campaign.context_data = {}
            
            campaign.save()
            
            # Handle recipients
            recipient_emails_text = request.POST.get('recipient_emails', '')
            recipient_phones_text = request.POST.get('recipient_phones', '')
            recipient_user_ids = request.POST.getlist('recipient_users')
            recipient_app_ids = request.POST.getlist('recipient_applications')
            
            # Process email list (split by newlines)
            if recipient_emails_text.strip():
                recipient_emails = [email.strip() for email in recipient_emails_text.split('\n') if email.strip()]
            else:
                recipient_emails = []
            
            # Process phone list (split by newlines)
            if recipient_phones_text.strip():
                recipient_phones = [phone.strip() for phone in recipient_phones_text.split('\n') if phone.strip()]
            else:
                recipient_phones = []
            
            campaign.recipient_emails = recipient_emails
            campaign.recipient_phones = recipient_phones
            campaign.save()
            
            if recipient_user_ids:
                campaign.recipient_users.set(recipient_user_ids)
            if recipient_app_ids:
                campaign.recipient_applications.set(recipient_app_ids)
            
            campaign.calculate_recipients()
            
            return JsonResponse({
                'success': True,
                'message': 'Campaign created successfully',
                'campaign_id': campaign.id
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    # GET request - show form
    form = BulkCampaignForm()
    templates = NotificationTemplate.objects.filter(is_active=True)
    
    # Get available recipients
    from accounts.models import User
    from applications.models import SupplierApplication
    
    users = User.objects.filter(role=User.Role.SUPPLIER, is_active=True)
    applications = SupplierApplication.objects.filter(status='APPROVED')
    
    context = {
        'form': form,
        'templates': templates,
        'users': users,
        'applications': applications,
    }
    
    return render(request, 'notifications/create_bulk_campaign.html', context)


@staff_member_required
def bulk_campaign_control(request, campaign_id, action):
    """Control bulk notification campaigns."""
    try:
        campaign = BulkNotification.objects.get(id=campaign_id)
    except BulkNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Campaign not found'})
    
    success = False
    message = ''
    
    if action == 'start':
        success = campaign.start_campaign()
        message = 'Campaign started successfully' if success else 'Campaign cannot be started in current state'
    elif action == 'pause':
        success = campaign.pause_campaign()
        message = 'Campaign paused successfully' if success else 'Campaign cannot be paused in current state'
    elif action == 'resume':
        success = campaign.resume_campaign()
        message = 'Campaign resumed successfully' if success else 'Campaign cannot be resumed in current state'
    elif action == 'cancel':
        success = campaign.cancel_campaign()
        message = 'Campaign cancelled successfully' if success else 'Campaign cannot be cancelled in current state'
    elif action == 'complete':
        success = campaign.complete_campaign()
        message = 'Campaign completed successfully' if success else 'Campaign cannot be completed in current state'
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    return JsonResponse({
        'success': success,
        'message': message,
        'campaign_status': campaign.status,
        'campaign_status_display': campaign.get_status_display(),
        'progress_percentage': campaign.get_progress_percentage(),
        'estimated_completion': campaign.get_estimated_completion().isoformat() if campaign.get_estimated_completion() else None
    })


@staff_member_required
def queue_dashboard(request):
    """Notification queue dashboard."""
    # Get queue statistics
    queue_stats = {
        'pending': NotificationQueue.objects.filter(status='PENDING').count(),
        'processing': NotificationQueue.objects.filter(status='PROCESSING').count(),
        'completed': NotificationQueue.objects.filter(status='COMPLETED').count(),
        'failed': NotificationQueue.objects.filter(status='FAILED').count(),
        'cancelled': NotificationQueue.objects.filter(status='CANCELLED').count(),
    }
    
    # Get priority breakdown
    priority_stats = NotificationQueue.objects.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    # Get recent queue items
    recent_items = NotificationQueue.objects.select_related(
        'notification_log', 'notification_log__template', 'bulk_campaign'
    ).order_by('-created_at')[:50]
    
    # Get failed items that can be retried
    retryable_items = NotificationQueue.objects.filter(
        status='FAILED',
        retry_count__lt=F('max_retries')
    ).order_by('next_retry_at')[:20]
    
    context = {
        'queue_stats': queue_stats,
        'priority_stats': priority_stats,
        'recent_items': recent_items,
        'retryable_items': retryable_items,
    }
    
    return render(request, 'notifications/queue_dashboard.html', context)


@staff_member_required
def queue_item_control(request, item_id, action):
    """Control individual queue items."""
    try:
        item = NotificationQueue.objects.get(id=item_id)
    except NotificationQueue.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Queue item not found'})
    
    success = False
    message = ''
    
    if action == 'retry':
        if item.can_retry:
            success = item.schedule_retry()
            message = 'Item scheduled for retry' if success else 'Item cannot be retried'
        else:
            message = 'Item cannot be retried (max retries reached or not failed)'
    elif action == 'cancel':
        item.cancel()
        success = True
        message = 'Item cancelled successfully'
    elif action == 'assign':
        worker_id = request.POST.get('worker_id', 'manual')
        item.assign_to_worker(worker_id)
        success = True
        message = f'Item assigned to worker {worker_id}'
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    return JsonResponse({
        'success': success,
        'message': message,
        'item_status': item.status,
        'item_status_display': item.get_status_display(),
        'retry_count': item.retry_count,
        'can_retry': item.can_retry
    })


@staff_member_required
def service_monitoring(request):
    """Real-time service monitoring dashboard."""
    services = NotificationService.objects.all().order_by('service_type', 'name')
    
    # Get real-time metrics
    monitoring_data = []
    for service in services:
        # Get recent performance data
        recent_logs = NotificationLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1),
            channel=service.service_type
        ).aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(status__in=['SENT', 'DELIVERED', 'OPENED', 'CLICKED'])),
            failed=Count('id', filter=Q(status='FAILED'))
        )
        
        # Calculate throughput per minute
        throughput = recent_logs['total'] / 60 if recent_logs['total'] > 0 else 0
        
        monitoring_data.append({
            'service': service,
            'is_healthy': service.is_healthy,
            'uptime': service.uptime,
            'success_rate': service.success_rate,
            'throughput_per_minute': throughput,
            'recent_total': recent_logs['total'],
            'recent_successful': recent_logs['successful'],
            'recent_failed': recent_logs['failed'],
            'cpu_usage': service.cpu_usage_percent,
            'memory_usage': service.memory_usage_mb,
        })
    
    # Generate chart data
    # Throughput over time (last 24 hours)
    throughput_labels = []
    throughput_data = []
    for i in range(24):
        hour = timezone.now() - timedelta(hours=i)
        throughput_labels.insert(0, hour.strftime('%H:00'))
        count = NotificationLog.objects.filter(
            created_at__hour=hour.hour,
            created_at__date=hour.date()
        ).count()
        throughput_data.insert(0, count)
    
    # Error rate by service
    error_rate_labels = []
    error_rate_data = []
    for service in services:
        total = NotificationLog.objects.filter(
            channel=service.service_type,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        failed = NotificationLog.objects.filter(
            channel=service.service_type,
            status='FAILED',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if total > 0:
            error_rate_labels.append(service.name)
            error_rate_data.append((failed / total) * 100)
    
    # Response time trend (mock data for now)
    response_time_labels = throughput_labels[-12:]  # Last 12 hours
    response_time_data = [100, 120, 110, 95, 130, 115, 105, 125, 110, 100, 115, 105]
    
    # Queue size distribution
    queue_size_data = [
        NotificationQueue.objects.filter(status='PENDING').count(),
        NotificationQueue.objects.filter(status='PROCESSING').count(),
        NotificationQueue.objects.filter(status='COMPLETED').count(),
        NotificationQueue.objects.filter(status='FAILED').count(),
    ]
    
    # System alerts (mock data for now)
    alerts = [
        {
            'level': 'INFO',
            'title': 'System Status',
            'message': 'All services are running normally',
            'created_at': timezone.now() - timedelta(minutes=5)
        }
    ]
    
    context = {
        'services': services,
        'monitoring_data': monitoring_data,
        'throughput_labels': json.dumps(throughput_labels),
        'throughput_data': json.dumps(throughput_data),
        'error_rate_labels': json.dumps(error_rate_labels),
        'error_rate_data': json.dumps(error_rate_data),
        'response_time_labels': json.dumps(response_time_labels),
        'response_time_data': json.dumps(response_time_data),
        'queue_size_data': json.dumps(queue_size_data),
        'alerts': alerts,
    }
    
    return render(request, 'notifications/service_monitoring.html', context)
