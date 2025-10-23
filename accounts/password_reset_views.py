"""
Custom password reset views using NotificationTemplate system.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

# Note: send_template_notification is imported locally in each function

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view that uses NotificationTemplate system.
    """
    
    def form_valid(self, form):
        """
        Override to use notification template instead of Django's email system.
        """
        email = form.cleaned_data['email']
        
        # Find users with this email
        users = User.objects.filter(email=email)
        
        if users.exists():
            for user in users:
                # Generate reset token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                # Build reset URL using configured FRONTEND_PUBLIC_URL to avoid IP addresses
                from django.conf import settings
                reset_path = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                reset_url = f"{settings.FRONTEND_PUBLIC_URL.rstrip('/')}{reset_path}"
                
                # Send notification using template system
                try:
                    from core.template_notification_service import send_template_notification
                    
                    # Get user's business information if available
                    business_name = user.email  # Default fallback
                    if hasattr(user, 'applications') and user.applications.exists():
                        latest_app = user.applications.first()
                        business_name = latest_app.business_name
                    
                    context_data = {
                        'user': user,
                        'email': user.email,
                        'business_name': business_name,
                        'reset_url': reset_url,
                        'uid': uid,
                        'token': token,
                        'protocol': self.request.scheme,
                        'domain': self.request.get_host(),
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                        'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                    }
                    
                    result = send_template_notification(
                        template_name="Password Reset Request",
                        recipient_email=user.email,
                        context_data=context_data,
                        channel='EMAIL'
                    )
                    
                    if result.get('success'):
                        logger.info(f"Password reset notification sent successfully to {user.email}")
                    else:
                        logger.error(f"Failed to send password reset notification to {user.email}: {result}")
                        
                except Exception as e:
                    logger.error(f"Error sending password reset notification to {user.email}: {str(e)}")
        
        # Always redirect to done page (for security, don't reveal if email exists)
        return redirect('accounts:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Custom password reset done view.
    """
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirm view.
    """
    template_name = 'accounts/password_reset_confirm.html'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Custom password reset complete view.
    """
    template_name = 'accounts/password_reset_complete.html'


@method_decorator(csrf_exempt, name='dispatch')
class APIPasswordResetView(PasswordResetView):
    """
    API version of password reset for AJAX requests.
    """
    
    def form_valid(self, form):
        """
        Handle AJAX password reset requests.
        """
        email = form.cleaned_data['email']
        
        # Find users with this email
        users = User.objects.filter(email=email)
        
        if users.exists():
            for user in users:
                # Generate reset token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                # Build reset URL using configured FRONTEND_PUBLIC_URL to avoid IP addresses
                from django.conf import settings
                reset_path = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                reset_url = f"{settings.FRONTEND_PUBLIC_URL.rstrip('/')}{reset_path}"
                
                # Send notification using template system
                try:
                    from core.template_notification_service import send_template_notification
                    
                    # Get user's business information if available
                    business_name = user.email  # Default fallback
                    if hasattr(user, 'applications') and user.applications.exists():
                        latest_app = user.applications.first()
                        business_name = latest_app.business_name
                    
                    context_data = {
                        'user': user,
                        'email': user.email,
                        'business_name': business_name,
                        'reset_url': reset_url,
                        'uid': uid,
                        'token': token,
                        'protocol': self.request.scheme,
                        'domain': self.request.get_host(),
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                        'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                    }
                    
                    result = send_template_notification(
                        template_name="Password Reset Request",
                        recipient_email=user.email,
                        context_data=context_data,
                        channel='EMAIL'
                    )
                    
                    if result.get('success'):
                        logger.info(f"Password reset notification sent successfully to {user.email}")
                    else:
                        logger.error(f"Failed to send password reset notification to {user.email}: {result}")
                        
                except Exception as e:
                    logger.error(f"Error sending password reset notification to {user.email}: {str(e)}")
        
        # Return JSON response for AJAX
        return JsonResponse({
            'success': True,
            'message': 'If an account with that email exists, we have sent password reset instructions.'
        })


def test_password_reset_notification(request):
    """
    Test view to verify password reset notification template.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get a test user
    test_user = User.objects.filter(is_active=True).first()
    if not test_user:
        return JsonResponse({'error': 'No test user found'}, status=404)
    
    # Generate reset token
    uid = urlsafe_base64_encode(force_bytes(test_user.pk))
    token = default_token_generator.make_token(test_user)
    
    # Build reset URL
    reset_url = request.build_absolute_uri(
        reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    try:
        from core.template_notification_service import send_template_notification
        
        # Get user's business information if available
        business_name = test_user.email  # Default fallback
        if hasattr(test_user, 'applications') and test_user.applications.exists():
            latest_app = test_user.applications.first()
            business_name = latest_app.business_name
        
        context_data = {
            'user': test_user,
            'email': test_user.email,
            'business_name': business_name,
            'reset_url': reset_url,
            'uid': uid,
            'token': token,
            'protocol': request.scheme,
            'domain': request.get_host(),
            'first_name': test_user.first_name or '',
            'last_name': test_user.last_name or '',
            'full_name': f"{test_user.first_name or ''} {test_user.last_name or ''}".strip() or test_user.email,
        }
        
        result = send_template_notification(
            template_name="Password Reset Request",
            recipient_email=test_user.email,
            context_data=context_data,
            channel='EMAIL'
        )
        
        return JsonResponse({
            'success': result.get('success', False),
            'message': f"Test notification sent to {test_user.email}",
            'result': result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
