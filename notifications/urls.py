"""
URL configuration for notifications app.
"""

from django.urls import path
from . import views
from . import enhanced_views

app_name = 'notifications'

urlpatterns = [
    # Dashboard and logs
    path('', views.notification_dashboard, name='dashboard'),
    path('logs/', views.notification_logs, name='logs'),
    path('logs/<int:log_id>/', views.notification_detail, name='detail'),
    path('analytics/', views.notification_analytics, name='analytics'),
    # Template editing
    path('templates/<int:template_id>/edit/', views.edit_notification_template, name='template-edit'),
    path('templates/<int:template_id>/preview/', views.preview_notification_template, name='template-preview'),
    
    # API endpoints
    path('api/analytics/', views.notification_analytics_api, name='analytics-api'),
    path('api/retry-failed/', views.retry_failed_notifications, name='retry-failed'),
    path('api/bulk-actions/', views.bulk_notification_actions, name='bulk-actions'),
    
    # Tracking endpoints (for email tracking)
    path('track/<uuid:tracking_id>/', views.track_notification, name='track'),
    path('track/<uuid:tracking_id>/open/', views.track_open, name='track-open'),
    path('track/<uuid:tracking_id>/click/<path:link_url>/', views.track_click, name='track-click'),
    
    # Enhanced notification features
    path('services/', enhanced_views.service_dashboard, name='service-dashboard'),
    path('services/<int:service_id>/<str:action>/', enhanced_views.service_control, name='service-control'),
    path('services/<int:service_id>/health-check/', enhanced_views.service_health_check, name='service-health-check'),
    path('services/monitoring/', enhanced_views.service_monitoring, name='service-monitoring'),
    
    # Bulk notification campaigns
    path('campaigns/', enhanced_views.bulk_campaigns, name='bulk-campaigns'),
    path('campaigns/create/', enhanced_views.create_bulk_campaign, name='create-bulk-campaign'),
    path('campaigns/<int:campaign_id>/<str:action>/', enhanced_views.bulk_campaign_control, name='bulk-campaign-control'),
    
    # Notification queue management
    path('queue/', enhanced_views.queue_dashboard, name='queue-dashboard'),
    path('queue/<int:item_id>/<str:action>/', enhanced_views.queue_item_control, name='queue-item-control'),
]