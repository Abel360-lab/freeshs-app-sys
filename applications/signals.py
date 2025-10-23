"""
Signals for the applications app.
"""
import logging
import secrets
import string
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import SupplierApplication
from notifications.models import NotificationTemplate
from core.notification_service import notification_service

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=SupplierApplication)
def send_application_submission_notification(sender, instance, created, **kwargs):
    """
    Send notification when a new application is submitted.
    """
    if created and instance.status == SupplierApplication.ApplicationStatus.PENDING_REVIEW:
        try:
            # Generate temporary password
            def generate_temp_password(length=12):
                characters = string.ascii_letters + string.digits + "!@#$%^&*"
                return ''.join(secrets.choice(characters) for _ in range(length))
            
            temp_password = generate_temp_password()
            
            # Create user account
            user = User.objects.create_user(
                username=instance.email,  # Use email as username
                email=instance.email,
                password=temp_password,
                first_name=instance.signer_name.split(' ')[0] if instance.signer_name else '',
                last_name=' '.join(instance.signer_name.split(' ')[1:]) if instance.signer_name and len(instance.signer_name.split(' ')) > 1 else '',
                is_supplier=True,
                must_change_password=True
            )
            
            # Link user to application
            instance.user = user
            instance.save()
            
            # Send notification using template notification service
            try:
                from core.template_notification_service import send_template_notification
                
                # Context data with the actual temporary password
                context_data = {
                    'business_name': instance.business_name,
                    'tracking_code': instance.tracking_code,
                    'user_created': True,
                    'user_email': user.email,
                    'temporary_password': temp_password,  # This will override the default '******'
                    'user': user,
                }
                
                result = send_template_notification(
                    template_name="Application Submission Confirmation",
                    recipient_email=user.email,
                    context_data=context_data,
                    application=instance,
                    channel='EMAIL'
                )
                
                if result.get('success'):
                    logger.info(f"Application submission notification sent to {user.email}")
                else:
                    logger.error(f"Failed to send application submission notification: {result.get('message')}")
                
            except Exception as e:
                logger.error(f"Failed to send application submission notification: {e}")
                
        except Exception as e:
            logger.error(f"Failed to create user account and send notification: {e}")
