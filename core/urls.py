from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('settings/', views.system_settings, name='system-settings'),
    path('settings/reset/', views.reset_settings, name='reset-settings'),
    path('settings/test-api/', views.test_notification_api, name='test-notification-api'),
    path('settings/export/', views.settings_export, name='settings-export'),
]
