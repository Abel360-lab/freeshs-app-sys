"""
URL configuration for notifications app.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Dashboard and logs
    path('', views.notification_dashboard, name='dashboard'),
    path('logs/', views.notification_logs, name='logs'),
    path('logs/<int:log_id>/', views.notification_detail, name='detail'),
    path('analytics/', views.notification_analytics, name='analytics'),
    
    # API endpoints
    path('api/analytics/', views.notification_analytics_api, name='analytics-api'),
    path('api/retry-failed/', views.retry_failed_notifications, name='retry-failed'),
    path('api/bulk-actions/', views.bulk_notification_actions, name='bulk-actions'),
    
    # Tracking endpoints (for email tracking)
    path('track/<uuid:tracking_id>/', views.track_notification, name='track'),
    path('track/<uuid:tracking_id>/open/', views.track_open, name='track-open'),
    path('track/<uuid:tracking_id>/click/<path:link_url>/', views.track_click, name='track-click'),
]