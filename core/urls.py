from django.urls import path
from . import views
from . import audit_views
from . import health_views

app_name = 'core'

urlpatterns = [
    path('settings/', views.system_settings, name='system-settings'),
    path('settings/reset/', views.reset_settings, name='reset-settings'),
    path('settings/test-api/', views.test_notification_api, name='test-notification-api'),
    path('settings/test-sms/', views.test_sms_service, name='test-sms-service'),
    path('settings/export/', views.settings_export, name='settings-export'),
    
    # Health Check URLs
    path('health/', health_views.health_check, name='health-check'),
    path('health/simple/', health_views.simple_health, name='simple-health'),
    
    # Audit Log URLs
    path('audit-logs/', audit_views.audit_logs, name='audit-logs'),
    path('audit-logs/<int:log_id>/', audit_views.audit_log_detail, name='audit-log-detail'),
    path('audit-logs/export/', audit_views.audit_log_export, name='audit-log-export'),
    path('audit-logs/statistics/', audit_views.audit_log_statistics, name='audit-log-statistics'),
    path('audit-logs/cleanup/', audit_views.audit_log_cleanup, name='audit-log-cleanup'),
]
