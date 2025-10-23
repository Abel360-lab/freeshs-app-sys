"""
URL configuration for accounts app.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import password_views
from . import auth_views as custom_auth_views
from . import password_reset_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', custom_auth_views.SupplierLoginView.as_view(), name='login'),
    path('admin/login/', custom_auth_views.AdminLoginView.as_view(), name='admin_login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Password management
    path('change-password/', password_views.change_password, name='change_password'),
    path('required-password-change/', password_views.RequiredPasswordChangeView.as_view(), name='required_password_change'),
    
    # Password reset URLs (using NotificationTemplate system)
    path('password-reset/', password_reset_views.CustomPasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),
    
    path('password-reset/done/', password_reset_views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    
    path('password-reset/confirm/<uidb64>/<token>/', password_reset_views.CustomPasswordResetConfirmView.as_view(
        success_url='/accounts/password-reset/complete/'
    ), name='password_reset_confirm'),
    
    path('password-reset/complete/', password_reset_views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # API endpoints for password reset
    path('api/password-reset/', password_reset_views.APIPasswordResetView.as_view(), name='api_password_reset'),
    path('api/test-password-reset/', password_reset_views.test_password_reset_notification, name='test_password_reset'),
    
    # Supplier dashboard
    path('dashboard/', views.supplier_dashboard, name='dashboard'),
    
    # SOP Starter Pack
    path('sop-starter-pack/', views.sop_starter_pack, name='sop_starter_pack'),
]
