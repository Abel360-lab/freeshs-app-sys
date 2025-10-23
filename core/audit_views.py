from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

from .models import AuditLog, SystemSettings


@staff_member_required
def audit_logs(request):
    """
    Display audit logs with filtering and search capabilities.
    """
    # Get filter parameters
    search = request.GET.get('search', '')
    action = request.GET.get('action', '')
    severity = request.GET.get('severity', '')
    user_id = request.GET.get('user', '')
    object_type = request.GET.get('object_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get logs queryset
    logs = AuditLog.objects.all()
    
    # Apply filters
    if search:
        logs = logs.filter(
            Q(description__icontains=search) |
            Q(object_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(tags__icontains=search)
        )
    
    if action:
        logs = logs.filter(action=action)
    
    if severity:
        logs = logs.filter(severity=severity)
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if object_type:
        logs = logs.filter(object_type=object_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except ValueError:
            pass
    
    # Order by timestamp (newest first)
    logs = logs.order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs, 50)  # 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    actions = AuditLog.ACTION_CHOICES
    severities = AuditLog.SEVERITY_CHOICES
    users = AuditLog.objects.values_list('user__id', 'user__username').distinct().exclude(user__isnull=True)
    object_types = AuditLog.objects.values_list('object_type', flat=True).distinct().exclude(object_type='')
    
    # Get statistics
    stats = {
        'total_logs': AuditLog.objects.count(),
        'today_logs': AuditLog.objects.filter(timestamp__date=timezone.now().date()).count(),
        'critical_logs': AuditLog.objects.filter(severity='CRITICAL').count(),
        'high_severity_logs': AuditLog.objects.filter(severity='HIGH').count(),
    }
    
    # Get recent activity
    recent_activity = AuditLog.objects.order_by('-timestamp')[:10]
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj,
        'search': search,
        'action': action,
        'severity': severity,
        'user_id': user_id,
        'object_type': object_type,
        'date_from': date_from,
        'date_to': date_to,
        'actions': actions,
        'severities': severities,
        'users': users,
        'object_types': object_types,
        'stats': stats,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'backoffice/audit_logs.html', context)


@staff_member_required
def audit_log_detail(request, log_id):
    """
    Display detailed information about a specific audit log entry.
    """
    log = get_object_or_404(AuditLog, id=log_id)
    
    # Get related logs (same user, same object, etc.)
    related_logs = AuditLog.objects.filter(
        Q(user=log.user) | 
        Q(object_type=log.object_type, object_id=log.object_id)
    ).exclude(id=log.id).order_by('-timestamp')[:10]
    
    context = {
        'log': log,
        'related_logs': related_logs,
    }
    
    return render(request, 'backoffice/audit_log_detail.html', context)


@staff_member_required
def audit_log_export(request):
    """
    Export audit logs to CSV.
    """
    # Get filter parameters (same as audit_logs view)
    search = request.GET.get('search', '')
    action = request.GET.get('action', '')
    severity = request.GET.get('severity', '')
    user_id = request.GET.get('user', '')
    object_type = request.GET.get('object_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply same filters as audit_logs view
    logs = AuditLog.objects.all()
    
    if search:
        logs = logs.filter(
            Q(description__icontains=search) |
            Q(object_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(tags__icontains=search)
        )
    
    if action:
        logs = logs.filter(action=action)
    
    if severity:
        logs = logs.filter(severity=severity)
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if object_type:
        logs = logs.filter(object_type=object_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except ValueError:
            pass
    
    logs = logs.order_by('-timestamp')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Timestamp', 'User', 'Action', 'Severity', 'Description', 'Object Type', 
        'Object ID', 'Object Name', 'IP Address', 'Request Path', 'Request Method',
        'Response Status', 'Tags'
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'System',
            log.get_action_display(),
            log.get_severity_display(),
            log.description,
            log.object_type,
            log.object_id,
            log.object_name,
            log.ip_address,
            log.request_path,
            log.request_method,
            log.response_status,
            log.tags
        ])
    
    return response


@staff_member_required
def audit_log_statistics(request):
    """
    Display audit log statistics and analytics.
    """
    # Date range (default to last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get logs in date range
    logs = AuditLog.objects.filter(timestamp__range=[start_date, end_date])
    
    # Action statistics
    action_stats = logs.values('action').annotate(count=Count('id')).order_by('-count')
    
    # Severity statistics
    severity_stats = logs.values('severity').annotate(count=Count('id')).order_by('-count')
    
    # User statistics
    user_stats = logs.filter(user__isnull=False).values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    # Object type statistics
    object_stats = logs.exclude(object_type='').values('object_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Daily activity
    daily_activity = []
    for i in range(days):
        date = end_date - timedelta(days=i)
        count = logs.filter(timestamp__date=date.date()).count()
        daily_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Hourly activity (last 24 hours)
    hourly_activity = []
    for i in range(24):
        hour = end_date - timedelta(hours=i)
        count = logs.filter(
            timestamp__gte=hour,
            timestamp__lt=hour + timedelta(hours=1)
        ).count()
        hourly_activity.append({
            'hour': hour.strftime('%H:00'),
            'count': count
        })
    
    context = {
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'action_stats': action_stats,
        'severity_stats': severity_stats,
        'user_stats': user_stats,
        'object_stats': object_stats,
        'daily_activity': daily_activity,
        'hourly_activity': hourly_activity,
        'total_logs': logs.count(),
    }
    
    return render(request, 'backoffice/audit_statistics.html', context)


@staff_member_required
def audit_log_cleanup(request):
    """
    Clean up old audit logs based on retention policy.
    """
    if request.method == 'POST':
        try:
            settings = SystemSettings.get_settings()
            retention_days = settings.audit_log_retention_days
            
            # Calculate cutoff date
            cutoff_date = timezone.now() - timedelta(days=retention_days)
            
            # Count logs to be deleted
            old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date)
            count = old_logs.count()
            
            # Delete old logs
            old_logs.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {count} audit log entries older than {retention_days} days.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error cleaning up audit logs: {str(e)}'
            })
    
    # Get current retention settings
    settings = SystemSettings.get_settings()
    cutoff_date = timezone.now() - timedelta(days=settings.audit_log_retention_days)
    old_logs_count = AuditLog.objects.filter(timestamp__lt=cutoff_date).count()
    
    context = {
        'retention_days': settings.audit_log_retention_days,
        'old_logs_count': old_logs_count,
        'cutoff_date': cutoff_date,
    }
    
    return render(request, 'backoffice/audit_cleanup.html', context)
