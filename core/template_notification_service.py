"""
Template-based notification service using NotificationTemplate models.
"""

import logging
from django.template import Template, Context
from django.conf import settings
from typing import Dict, Any, Optional
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class TemplateNotificationService:
    """Service for sending notifications using NotificationTemplate models."""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def send_template_notification(
        self,
        template_name: str,
        recipient_email: str,
        recipient_phone: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        application=None,
        channel: str = 'EMAIL'  # 'EMAIL' or 'SMS'
    ) -> Dict[str, Any]:
        """
        Send notification using a template from the database.
        
        Args:
            template_name: Name of the template to use
            recipient_email: Email address to send to
            recipient_phone: Phone number for SMS (optional)
            context_data: Context data for template rendering
            application: Application object for logging
            channel: 'EMAIL' or 'SMS'
            
        Returns:
            Dict with success status and details
        """
        try:
            from notifications.models import NotificationTemplate
            
            # Get the template
            try:
                template = NotificationTemplate.objects.get(
                    name=template_name,
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                logger.error(f"Template '{template_name}' not found or inactive")
                return {
                    "success": False,
                    "message": f"Template '{template_name}' not found or inactive"
                }
            
            # Prepare context
            context = context_data or {}
            if application:
                # Use the application's completion token for document submission
                if hasattr(application, 'completion_token') and application.completion_token:
                    upload_url = f"{settings.FRONTEND_PUBLIC_URL}/submit/{application.completion_token}/"
                else:
                    # Fallback: generate a signed token from tracking code
                    from django.core.signing import Signer
                    signer = Signer()
                    upload_token = signer.sign(application.tracking_code)
                    upload_url = f"{settings.FRONTEND_PUBLIC_URL}/submit/{upload_token}/"
                
                # Only add temporary_password if it's not already in context_data
                default_context = {
                    'application': application,
                    'tracking_code': application.tracking_code,
                    'business_name': application.business_name,
                    'contact_person': application.business_name,  # Use business_name as contact_person
                    'email': application.email,
                    'phone': application.telephone,
                    'submitted_at': application.submitted_at,
                    'status': application.status,
                    'status_url': f"{settings.FRONTEND_PUBLIC_URL}/applications/{application.tracking_code}/status/",
                    'upload_url': upload_url,  # Add upload URL for document submission
                    'user_created': application.user is not None,
                    'user_email': application.user.email if application.user else None,
                    'login_url': f"{settings.FRONTEND_PUBLIC_URL}/accounts/login/"
                }
                
                # Only add temporary_password if it's not already provided in context_data
                if 'temporary_password' not in context_data:
                    default_context['temporary_password'] = '******'  # Don't include actual password in email for security
                
                context.update(default_context)
            
            # Render template
            if channel == 'EMAIL':
                subject_template = Template(template.subject)
                body_template = Template(template.body_html)
                
                subject = subject_template.render(Context(context))
                body = body_template.render(Context(context))
                
                # Send email
                result = self.notification_service.send_email(
                    to=recipient_email,
                    subject=subject,
                    body=body,
                    is_html=True,
                    from_name="GCX eServices",
                    application=application,
                    template_name=template_name
                )
                
            elif channel == 'SMS':
                # For SMS, use the text version or create a simple message
                if template.body_text:
                    body_template = Template(template.body_text)
                else:
                    # Fallback to HTML template with basic text conversion
                    body_template = Template(template.body_html)
                
                body = body_template.render(Context(context))
                
                # Send SMS - ensure we have a valid phone number
                if not recipient_phone:
                    return {
                        "success": False,
                        "message": "Phone number required for SMS notifications"
                    }
                
                result = self.notification_service.send_sms(
                    number=recipient_phone,
                    message=body,
                    application=application,
                    template_name=template_name
                )
            else:
                return {
                    "success": False,
                    "message": f"Unsupported channel: {channel}"
                }
            
            if result.get('success'):
                logger.info(f"Template notification sent successfully: {template_name} to {recipient_email}")
                return {
                    "success": True,
                    "message": "Template notification sent successfully",
                    "template_used": template_name,
                    "channel": channel,
                    "data": result
                }
            else:
                logger.error(f"Failed to send template notification: {result.get('message')}")
                return {
                    "success": False,
                    "message": f"Failed to send notification: {result.get('message')}",
                    "template_used": template_name,
                    "channel": channel
                }
                
        except Exception as e:
            logger.error(f"Error sending template notification: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending template notification: {str(e)}"
            }
    
    def send_application_confirmation(self, application) -> Dict[str, Any]:
        """Send application confirmation using template."""
        return self.send_template_notification(
            template_name="application submission",
            recipient_email=application.email,
            application=application,
            channel='EMAIL'
        )
    
    def send_document_request(self, application, missing_docs) -> Dict[str, Any]:
        """Send document request using template."""
        context_data = {
            'missing_documents': missing_docs,
            'document_list': [doc.name for doc in missing_docs]
        }
        return self.send_template_notification(
            template_name="Document Request Notification",
            recipient_email=application.email,
            application=application,
            context_data=context_data,
            channel='EMAIL'
        )
    
    def send_application_approval(self, application) -> Dict[str, Any]:
        """Send application approval using template."""
        return self.send_template_notification(
            template_name="Application Approval with Credentials",
            recipient_email=application.email,
            application=application,
            channel='EMAIL'
        )
    
    def send_application_rejection(self, application, reason=None) -> Dict[str, Any]:
        """Send application rejection using template."""
        context_data = {
            'rejection_reason': reason or 'Application did not meet requirements'
        }
        return self.send_template_notification(
            template_name="Application Rejection",
            recipient_email=application.email,
            application=application,
            context_data=context_data,
            channel='EMAIL'
        )


# Global instance
template_notification_service = TemplateNotificationService()


def send_template_notification(
    template_name: str,
    recipient_email: str,
    recipient_phone: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
    application=None,
    channel: str = 'EMAIL'
) -> Dict[str, Any]:
    """
    Convenience function to send template notifications.
    """
    return template_notification_service.send_template_notification(
        template_name, recipient_email, recipient_phone, 
        context_data, application, channel
    )
