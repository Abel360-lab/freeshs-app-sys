from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging

from .models import SystemSettings

logger = logging.getLogger(__name__)


@staff_member_required
def system_settings(request):
    """
    System settings management page.
    """
    settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update general settings
            settings.site_name = request.POST.get('site_name', settings.site_name)
            settings.site_description = request.POST.get('site_description', settings.site_description)
            settings.maintenance_mode = 'maintenance_mode' in request.POST
            settings.maintenance_message = request.POST.get('maintenance_message', settings.maintenance_message)
            
            # Update email settings
            settings.email_from_name = request.POST.get('email_from_name', settings.email_from_name)
            settings.email_from_address = request.POST.get('email_from_address', settings.email_from_address)
            settings.email_reply_to = request.POST.get('email_reply_to', settings.email_reply_to)
            settings.admin_notification_email = request.POST.get('admin_notification_email', settings.admin_notification_email)
            
            # Update SMS settings
            settings.sms_from_name = request.POST.get('sms_from_name', settings.sms_from_name)
            
            # Update notification settings
            settings.notification_api_url = request.POST.get('notification_api_url', settings.notification_api_url)
            settings.notification_timeout = int(request.POST.get('notification_timeout', settings.notification_timeout))
            
            # Update application settings
            settings.application_auto_approve = 'application_auto_approve' in request.POST
            settings.application_approval_days = int(request.POST.get('application_approval_days', settings.application_approval_days))
            settings.document_verification_required = 'document_verification_required' in request.POST
            
            # Update security settings
            settings.password_min_length = int(request.POST.get('password_min_length', settings.password_min_length))
            settings.password_require_special = 'password_require_special' in request.POST
            settings.session_timeout = int(request.POST.get('session_timeout', settings.session_timeout))
            settings.max_login_attempts = int(request.POST.get('max_login_attempts', settings.max_login_attempts))
            
            # Update file upload settings
            settings.max_file_size = int(request.POST.get('max_file_size', settings.max_file_size))
            settings.allowed_file_types = request.POST.get('allowed_file_types', settings.allowed_file_types)
            
            # Update audit settings
            settings.audit_log_retention_days = int(request.POST.get('audit_log_retention_days', settings.audit_log_retention_days))
            settings.log_level = request.POST.get('log_level', settings.log_level)
            
            # Update metadata
            settings.updated_by = request.user
            settings.updated_at = timezone.now()
            
            settings.save()
            
            messages.success(request, 'System settings updated successfully!')
            logger.info(f"System settings updated by {request.user.username}")
            
            return redirect('core:system-settings')
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
            logger.error(f"Error updating system settings: {str(e)}")
    
    context = {
        'settings': settings,
        'log_level_choices': SystemSettings._meta.get_field('log_level').choices,
    }
    
    return render(request, 'backoffice/system_settings.html', context)


@staff_member_required
@require_POST
def reset_settings(request):
    """
    Reset settings to default values.
    """
    try:
        settings = SystemSettings.get_settings()
        
        # Reset to defaults
        settings.site_name = 'GCX Admin Portal'
        settings.site_description = 'Ghana Commodity Exchange Admin Portal'
        settings.maintenance_mode = False
        settings.maintenance_message = ''
        settings.email_from_name = 'GCX eServices'
        settings.email_from_address = 'noreply@gcx.com.gh'
        settings.email_reply_to = ''
        settings.admin_notification_email = 'admin@gcx.com.gh'
        settings.sms_from_name = 'GCX'
        settings.notification_api_url = 'https://api.gcx.com.gh/notification-api/public'
        settings.notification_timeout = 30
        settings.application_auto_approve = False
        settings.application_approval_days = 7
        settings.document_verification_required = True
        settings.password_min_length = 8
        settings.password_require_special = True
        settings.session_timeout = 480
        settings.max_login_attempts = 5
        settings.max_file_size = 10
        settings.allowed_file_types = 'pdf,doc,docx,jpg,jpeg,png'
        settings.audit_log_retention_days = 365
        settings.log_level = 'INFO'
        settings.updated_by = request.user
        settings.updated_at = timezone.now()
        
        settings.save()
        
        messages.success(request, 'Settings reset to default values successfully!')
        logger.info(f"System settings reset to defaults by {request.user.username}")
        
    except Exception as e:
        messages.error(request, f'Error resetting settings: {str(e)}')
        logger.error(f"Error resetting system settings: {str(e)}")
    
    return redirect('core:system-settings')


@staff_member_required
@require_POST
def test_notification_api(request):
    """
    Test the notification API connection.
    """
    try:
        import requests
        from django.conf import settings
        
        settings_obj = SystemSettings.get_settings()
        
        # Test email endpoint
        email_url = f"{settings_obj.notification_api_url}/api/email"
        test_payload = {
            "to": "test@example.com",
            "subject": "API Test",
            "body": "This is a test message from GCX Admin Portal",
            "isHtml": False,
            "fromName": settings_obj.email_from_name,
            "priority": "normal",
            "tracking": False,
            "immediate": True
        }
        
        response = requests.post(
            email_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=settings_obj.notification_timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return JsonResponse({
                    'success': True,
                    'message': 'Notification API is working correctly!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'API returned error: {result.get("message", "Unknown error")}'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': f'API request failed with status {response.status_code}'
            })
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'message': 'API request timed out'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error testing API: {str(e)}'
        })


@staff_member_required
def settings_export(request):
    """
    Export current settings as JSON.
    """
    try:
        settings = SystemSettings.get_settings()
        
        # Create export data (exclude sensitive fields)
        export_data = {
            'site_name': settings.site_name,
            'site_description': settings.site_description,
            'maintenance_mode': settings.maintenance_mode,
            'maintenance_message': settings.maintenance_message,
            'email_from_name': settings.email_from_name,
            'email_from_address': settings.email_from_address,
            'email_reply_to': settings.email_reply_to,
            'admin_notification_email': settings.admin_notification_email,
            'sms_from_name': settings.sms_from_name,
            'notification_api_url': settings.notification_api_url,
            'notification_timeout': settings.notification_timeout,
            'application_auto_approve': settings.application_auto_approve,
            'application_approval_days': settings.application_approval_days,
            'document_verification_required': settings.document_verification_required,
            'password_min_length': settings.password_min_length,
            'password_require_special': settings.password_require_special,
            'session_timeout': settings.session_timeout,
            'max_login_attempts': settings.max_login_attempts,
            'max_file_size': settings.max_file_size,
            'allowed_file_types': settings.allowed_file_types,
            'audit_log_retention_days': settings.audit_log_retention_days,
            'log_level': settings.log_level,
            'exported_at': timezone.now().isoformat(),
            'exported_by': request.user.username
        }
        
        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = 'attachment; filename="gcx_system_settings.json"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting settings: {str(e)}')
        return redirect('core:system-settings')