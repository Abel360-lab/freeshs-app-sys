"""
Notification views for GCX Supplier Application Portal.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Q, Avg, Max
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import json

from .models import (
    NotificationLog, SMSNotification, NotificationAnalytics, NotificationTemplate,
    NotificationService, BulkNotification, NotificationQueue
)


@staff_member_required
def notification_dashboard(request):
    """
    Dashboard for viewing notification logs and analytics.
    """
    # Get date range
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get notification logs
    notification_logs = NotificationLog.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('template', 'application', 'user').order_by('-created_at')
    
    # Get SMS notifications
    sms_notifications = SMSNotification.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('application', 'user').order_by('-created_at')
    
    # Get analytics
    analytics = NotificationAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date', 'channel')
    
    # Calculate summary statistics
    total_emails = notification_logs.count()
    total_sms = sms_notifications.count()
    
    email_stats = {
        'sent': notification_logs.filter(status='SENT').count(),
        'delivered': notification_logs.filter(status='DELIVERED').count(),
        'opened': notification_logs.filter(status='OPENED').count(),
        'clicked': notification_logs.filter(status='CLICKED').count(),
        'failed': notification_logs.filter(status='FAILED').count(),
        'bounced': notification_logs.filter(status='BOUNCED').count(),
    }
    
    sms_stats = {
        'sent': sms_notifications.filter(status='SENT').count(),
        'delivered': sms_notifications.filter(status='DELIVERED').count(),
        'opened': sms_notifications.filter(status='OPENED').count(),
        'clicked': sms_notifications.filter(status='CLICKED').count(),
        'failed': sms_notifications.filter(status='FAILED').count(),
        'bounced': sms_notifications.filter(status='BOUNCED').count(),
    }
    
    # Calculate rates
    email_rates = {}
    if email_stats['sent'] > 0:
        email_rates['delivery_rate'] = (email_stats['delivered'] / email_stats['sent']) * 100
        email_rates['failure_rate'] = ((email_stats['failed'] + email_stats['bounced']) / email_stats['sent']) * 100
    
    if email_stats['delivered'] > 0:
        email_rates['open_rate'] = (email_stats['opened'] / email_stats['delivered']) * 100
    
    if email_stats['opened'] > 0:
        email_rates['click_rate'] = (email_stats['clicked'] / email_stats['opened']) * 100
    
    sms_rates = {}
    if sms_stats['sent'] > 0:
        sms_rates['delivery_rate'] = (sms_stats['delivered'] / sms_stats['sent']) * 100
        sms_rates['failure_rate'] = ((sms_stats['failed'] + sms_stats['bounced']) / sms_stats['sent']) * 100
    
    # Get top templates
    top_templates = notification_logs.values('template__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Get recent notifications
    recent_notifications = notification_logs[:20]
    
    # Paginate notification logs
    paginator = Paginator(notification_logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notification_logs': page_obj,
        'sms_notifications': sms_notifications[:20],
        'analytics': analytics,
        'total_emails': total_emails,
        'total_sms': total_sms,
        'email_stats': email_stats,
        'sms_stats': sms_stats,
        'email_rates': email_rates,
        'sms_rates': sms_rates,
        'top_templates': top_templates,
        'recent_notifications': recent_notifications,
        'start_date': start_date,
        'end_date': end_date,
        'days': days,
    }
    
    return render(request, 'notifications/dashboard.html', context)


@staff_member_required
def notification_logs(request):
    """
    Detailed view of notification logs.
    """
    # Get filters
    status = request.GET.get('status')
    channel = request.GET.get('channel')
    template = request.GET.get('template')
    search = request.GET.get('search')
    
    # Build queryset
    logs = NotificationLog.objects.select_related('template', 'application', 'user').order_by('-created_at')
    
    if status:
        logs = logs.filter(status=status)
    
    if channel:
        logs = logs.filter(channel=channel)
    
    if template:
        logs = logs.filter(template__name__icontains=template)
    
    if search:
        logs = logs.filter(
            Q(recipient_email__icontains=search) |
            Q(recipient_name__icontains=search) |
            Q(subject__icontains=search)
        )
    
    # Paginate
    paginator = Paginator(logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    status_choices = NotificationLog.Status.choices
    channel_choices = NotificationLog.Channel.choices
    template_choices = NotificationTemplate.objects.values_list('name', 'name').distinct()
    
    context = {
        'logs': page_obj,
        'status_choices': status_choices,
        'channel_choices': channel_choices,
        'template_choices': template_choices,
        'current_filters': {
            'status': status,
            'channel': channel,
            'template': template,
            'search': search,
        }
    }
    
    return render(request, 'notifications/logs.html', context)


@staff_member_required
def notification_detail(request, log_id):
    """
    Detailed view of a specific notification log.
    """
    log = get_object_or_404(NotificationLog, id=log_id)
    
    context = {
        'log': log,
    }
    
    return render(request, 'notifications/detail.html', context)


@staff_member_required
def notification_analytics(request):
    """
    Detailed analytics view for notifications.
    """
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get all notifications in date range
    notifications = NotificationLog.objects.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    # Email statistics
    email_notifications = notifications.filter(channel='EMAIL')
    email_stats = {
        'total': email_notifications.count(),
        'sent': email_notifications.filter(status='SENT').count(),
        'delivered': email_notifications.filter(status='DELIVERED').count(),
        'opened': email_notifications.filter(status='OPENED').count(),
        'clicked': email_notifications.filter(status='CLICKED').count(),
        'failed': email_notifications.filter(status='FAILED').count(),
        'bounced': email_notifications.filter(status='BOUNCED').count(),
    }
    
    # Calculate rates
    if email_stats['total'] > 0:
        email_stats['delivery_rate'] = round((email_stats['delivered'] / email_stats['total']) * 100, 2)
        email_stats['open_rate'] = round((email_stats['opened'] / email_stats['delivered']) * 100, 2) if email_stats['delivered'] > 0 else 0
        email_stats['click_rate'] = round((email_stats['clicked'] / email_stats['opened']) * 100, 2) if email_stats['opened'] > 0 else 0
        email_stats['failure_rate'] = round((email_stats['failed'] / email_stats['total']) * 100, 2)
    else:
        email_stats.update({
            'delivery_rate': 0, 'open_rate': 0, 'click_rate': 0, 'failure_rate': 0
        })
    
    # SMS statistics
    sms_notifications = notifications.filter(channel='SMS')
    sms_stats = {
        'total': sms_notifications.count(),
        'sent': sms_notifications.filter(status='SENT').count(),
        'delivered': sms_notifications.filter(status='DELIVERED').count(),
        'opened': sms_notifications.filter(status='OPENED').count(),
        'clicked': sms_notifications.filter(status='CLICKED').count(),
        'failed': sms_notifications.filter(status='FAILED').count(),
        'bounced': sms_notifications.filter(status='BOUNCED').count(),
    }
    
    # Calculate rates
    if sms_stats['total'] > 0:
        sms_stats['delivery_rate'] = round((sms_stats['delivered'] / sms_stats['total']) * 100, 2)
        sms_stats['open_rate'] = round((sms_stats['opened'] / sms_stats['delivered']) * 100, 2) if sms_stats['delivered'] > 0 else 0
        sms_stats['click_rate'] = round((sms_stats['clicked'] / sms_stats['opened']) * 100, 2) if sms_stats['opened'] > 0 else 0
        sms_stats['failure_rate'] = round((sms_stats['failed'] / sms_stats['total']) * 100, 2)
    else:
        sms_stats.update({
            'delivery_rate': 0, 'open_rate': 0, 'click_rate': 0, 'failure_rate': 0
        })
    
    # Overall statistics
    total_notifications = notifications.count()
    total_sent = notifications.filter(status='SENT').count()
    total_delivered = notifications.filter(status='DELIVERED').count()
    total_failed = notifications.filter(status='FAILED').count()
    
    overall_stats = {
        'total': total_notifications,
        'sent': total_sent,
        'delivered': total_delivered,
        'failed': total_failed,
        'delivery_rate': round((total_delivered / total_notifications) * 100, 2) if total_notifications > 0 else 0,
        'success_rate': round(((total_notifications - total_failed) / total_notifications) * 100, 2) if total_notifications > 0 else 0,
    }
    
    # Daily statistics for chart
    daily_stats = []
    for i in range(days):
        date = end_date - timedelta(days=i)
        day_notifications = notifications.filter(created_at__date=date)
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'emails': day_notifications.filter(channel='EMAIL').count(),
            'sms': day_notifications.filter(channel='SMS').count(),
            'total': day_notifications.count(),
        })
    daily_stats.reverse()
    
    # Top templates with success rate and last used
    top_templates = (
        NotificationTemplate.objects
        .annotate(
            sent_count=Count('logs'),
            success_count=Count('logs', filter=Q(logs__status__in=['SENT','DELIVERED','OPENED','CLICKED'])),
            last_used_ts=Max('logs__created_at')
        )
        .order_by('-sent_count')[:10]
    )
    # attach computed fields for display (avoid division by zero)
    for template in top_templates:
        total = template.sent_count or 0
        template.success_rate = round((template.success_count / total) * 100, 2) if total > 0 else 0
        template.last_used = template.last_used_ts
    
    context = {
        'email_stats': email_stats,
        'sms_stats': sms_stats,
        'overall_stats': overall_stats,
        'daily_stats': daily_stats,
        'top_templates': top_templates,
        'status_distribution': {
            'sent': notifications.filter(status='SENT').count(),
            'delivered': notifications.filter(status='DELIVERED').count(),
            'opened': notifications.filter(status='OPENED').count(),
            'clicked': notifications.filter(status='CLICKED').count(),
            'failed': notifications.filter(status='FAILED').count(),
            'bounced': notifications.filter(status='BOUNCED').count(),
        },
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'notifications/analytics.html', context)


@staff_member_required
def notification_analytics_api(request):
    """
    API endpoint for notification analytics data.
    """
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get daily analytics
    daily_data = NotificationAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).values('date', 'channel').annotate(
        total_sent=Count('total_sent'),
        total_delivered=Count('total_delivered'),
        total_opened=Count('total_opened'),
        total_clicked=Count('total_clicked'),
        total_failed=Count('total_failed'),
    ).order_by('date')
    
    # Get template performance
    template_data = NotificationAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).values('template_name', 'channel').annotate(
        total_sent=Count('total_sent'),
        total_delivered=Count('total_delivered'),
        total_opened=Count('total_opened'),
        total_clicked=Count('total_clicked'),
        avg_delivery_rate=Avg('delivery_rate'),
        avg_open_rate=Avg('open_rate'),
        avg_click_rate=Avg('click_rate'),
    ).order_by('-total_sent')
    
    return JsonResponse({
        'daily_data': list(daily_data),
        'template_data': list(template_data),
    })


@staff_member_required
def edit_notification_template(request, template_id):
    """Edit a notification template with live preview."""
    template = get_object_or_404(NotificationTemplate, id=template_id)
    if request.method == 'POST':
        # Basic save without custom forms to keep minimal
        template.name = request.POST.get('name', template.name)
        template.subject = request.POST.get('subject', template.subject)
        template.body_html = request.POST.get('body_html', template.body_html)
        template.body_text = request.POST.get('body_text', template.body_text)
        is_active = request.POST.get('is_active')
        template.is_active = True if is_active in ['on', 'true', '1'] else False
        template.save()
        return JsonResponse({'success': True}) if request.headers.get('x-requested-with') == 'XMLHttpRequest' else render(request, 'notifications/template_edit.html', {'tmpl': template, 'saved': True})
    return render(request, 'notifications/template_edit.html', {'tmpl': template})


@staff_member_required
@require_POST
def preview_notification_template(request, template_id):
    """Return a rendered HTML preview using posted subject/body and sample context."""
    _ = get_object_or_404(NotificationTemplate, id=template_id)
    data = request.POST
    subject = data.get('subject', '')
    body_html = data.get('body_html', '')
    body_text = data.get('body_text', '')

    # Provide sample context similar to what the app might send
    sample = {
        'supplier_name': 'Acme Supplies Ltd.',
        'tracking_code': 'GCX-APP-001234',
        'business_name': 'Acme Supplies',
        'support_email': 'support@gcx.com.gh',
        'current_date': timezone.now().strftime('%B %d, %Y')
    }

    # Render by simple substitution of {{ var }} where possible
    # Minimalistic, since full templating is handled elsewhere in the app
    def render_vars(s: str) -> str:
        out = s or ''
        for k, v in sample.items():
            out = out.replace('{{ ' + k + ' }}', str(v))
        return out

    rendered_subject = render_vars(subject)
    rendered_html = render_vars(body_html)
    rendered_text = render_vars(body_text)

    html = f"""
    <div style=\"font-family: Inter, Arial, sans-serif; padding:16px;\">
      <h2 style=\"margin-top:0;\">{rendered_subject}</h2>
      <div style=\"border:1px solid #e5e7eb; border-radius:8px; padding:16px;\">{rendered_html}</div>
      <pre style=\"background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:12px; margin-top:12px; white-space:pre-wrap;\">{rendered_text}</pre>
    </div>
    """
    return JsonResponse({'html': html})


@staff_member_required
@require_POST
def retry_failed_notifications(request):
    """
    Retry failed notifications.
    """
    try:
        data = json.loads(request.body or '{}')
    except Exception:
        data = {}
    notification_ids = data.get('notification_ids') or request.POST.getlist('notification_ids')

    if not notification_ids:
        # Retry all failed notifications
        notifications = NotificationLog.objects.filter(status='FAILED')
        notification_ids = list(notifications.values_list('id', flat=True))

    retried_count = 0
    for notification_id in notification_ids:
        try:
            notification = NotificationLog.objects.get(id=notification_id)
            if notification.can_retry():
                notification.schedule_retry()
                retried_count += 1
        except NotificationLog.DoesNotExist:
            continue

        # Kick off async task to send pending notifications
        try:
            from .tasks import send_pending_notifications
            send_pending_notifications.delay()
        except Exception:
            pass
        return JsonResponse({'success': True, 'message': f'Successfully scheduled {retried_count} notifications for retry'})


@staff_member_required
def bulk_notification_actions(request):
    """
    Handle bulk actions on notifications (retry, pause, resume, delete).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    action = request.POST.get('action')
    notification_ids = request.POST.getlist('notification_ids')
    
    if not action or not notification_ids:
        return JsonResponse({'success': False, 'message': 'Missing action or notification IDs'})
    
    processed_count = 0
    errors = []
    
    for notification_id in notification_ids:
        try:
            notification = NotificationLog.objects.get(id=notification_id)
            
            if action == 'retry':
                if notification.can_retry():
                    notification.schedule_retry()
                    processed_count += 1
                else:
                    errors.append(f'Notification {notification_id} cannot be retried')
                    
            elif action == 'pause':
                if notification.status == 'PENDING':
                    notification.status = 'PAUSED'
                    notification.save()
                    processed_count += 1
                else:
                    errors.append(f'Notification {notification_id} cannot be paused')
                    
            elif action == 'resume':
                if notification.status == 'PAUSED':
                    notification.status = 'PENDING'
                    notification.save()
                    processed_count += 1
                else:
                    errors.append(f'Notification {notification_id} cannot be resumed')
                    
            elif action == 'delete':
                notification.delete()
                processed_count += 1
                
            else:
                errors.append(f'Unknown action: {action}')
                
        except NotificationLog.DoesNotExist:
            errors.append(f'Notification {notification_id} not found')
        except Exception as e:
            errors.append(f'Error processing notification {notification_id}: {str(e)}')
    
    if errors:
        return JsonResponse({
            'success': False,
            'message': f'Processed {processed_count} notifications. Errors: {"; ".join(errors)}'
        })
    
    action_messages = {
        'retry': 'scheduled for retry',
        'pause': 'paused',
        'resume': 'resumed',
        'delete': 'deleted'
    }
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully {action_messages.get(action, "processed")} {processed_count} notifications'
    })


def track_notification(request, tracking_id):
    """
    Track notification access (general tracking).
    """
    try:
        notification = NotificationLog.objects.get(tracking_id=tracking_id)
        
        # Log the access
        notification.mark_opened(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Return a 1x1 pixel image
        from django.http import HttpResponse
        response = HttpResponse(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png'
        )
        return response
        
    except NotificationLog.DoesNotExist:
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound('Notification not found')


def track_open(request, tracking_id):
    """
    Track email open events.
    """
    try:
        notification = NotificationLog.objects.get(tracking_id=tracking_id)
        
        # Mark as opened
        notification.mark_opened(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Return a 1x1 pixel image
        from django.http import HttpResponse
        response = HttpResponse(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png'
        )
        return response
        
    except NotificationLog.DoesNotExist:
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound('Notification not found')


def track_click(request, tracking_id, link_url):
    """
    Track email click events.
    """
    try:
        notification = NotificationLog.objects.get(tracking_id=tracking_id)
        
        # Mark as clicked
        notification.mark_clicked(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Redirect to the actual link
        from django.shortcuts import redirect
        from urllib.parse import unquote
        return redirect(unquote(link_url))
        
    except NotificationLog.DoesNotExist:
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound('Notification not found')