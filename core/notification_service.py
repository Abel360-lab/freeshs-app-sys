"""
Notification service for integrating with GCX Notification API.
"""
import requests
import logging
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via GCX Notification API."""
    
    def __init__(self):
        self.base_url = settings.NOTIFICATION_API_BASE_URL
        self.timeout = 30  # seconds
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = True,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        application=None,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via notification API and log it.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default: True)
            from_email: Override sender email (optional)
            from_name: Override sender name (optional)
            application: Related application object (optional)
            template_name: Template name for logging (optional)
            
        Returns:
            Dict with success status and message
        """
        # Create notification log entry
        notification_log = None
        try:
            from notifications.models import NotificationLog, NotificationTemplate
            
            # Get existing template based on template_name or use APPLICATION_SUBMITTED as default
            template = None
            if template_name:
                template = NotificationTemplate.objects.filter(
                    name=template_name,
                    is_active=True
                ).first()
            
            if not template:
                template = NotificationTemplate.objects.filter(
                    notification_type=NotificationTemplate.NotificationType.APPLICATION_SUBMITTED
                ).first()
            
            # If no template exists, create one
            if not template:
                template = NotificationTemplate.objects.create(
                    name="Application Submitted Email Template",
                    notification_type=NotificationTemplate.NotificationType.APPLICATION_SUBMITTED,
                    subject="Application Notification",
                    body_html="",
                    body_text="",
                    is_active=True
                )
            
            # Create notification log
            notification_log = NotificationLog.objects.create(
                template=template,
                channel=NotificationLog.Channel.EMAIL,
                recipient_email=to,
                recipient_name="",  # Will be updated if we have application
                subject=subject,
                body_html=body if is_html else "",
                body_text=body if not is_html else "",
                status=NotificationLog.Status.PENDING,
                application=application,
                context_data={}
            )
            
            # Update recipient name if we have application
            if application:
                notification_log.recipient_name = application.business_name or application.contact_person
                notification_log.save()
                
        except Exception as e:
            logger.error(f"Failed to create notification log: {str(e)}")
        
        try:
            url = f"{self.base_url}/api/email"
            
            payload = {
                "to": to,
                "subject": subject,
                "body": body,
                "isHtml": is_html
            }
            
            # Add optional sender overrides
            if from_email:
                payload["fromEmail"] = from_email
            if from_name:
                payload["fromName"] = from_name
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"Email sent successfully to {to}")
                    
                    # Update notification log on success
                    if notification_log:
                        notification_log.status = NotificationLog.Status.SENT
                        notification_log.sent_at = timezone.now()
                        notification_log.external_id = result.get('message_id', '')
                        notification_log.save()
                    
                    return {
                        "success": True,
                        "message": "Email sent successfully",
                        "data": result
                    }
                else:
                    logger.error(f"Email API returned error: {result.get('message', 'Unknown error')}")
                    
                    # Update notification log on failure
                    if notification_log:
                        notification_log.status = NotificationLog.Status.FAILED
                        notification_log.error_message = result.get('message', 'Unknown error')
                        notification_log.save()
                    
                    return {
                        "success": False,
                        "message": result.get('message', 'Email sending failed'),
                        "data": result
                    }
            else:
                logger.error(f"Email API request failed with status {response.status_code}: {response.text}")
                
                # Update notification log on failure
                if notification_log:
                    notification_log.status = NotificationLog.Status.FAILED
                    notification_log.error_message = f"API request failed with status {response.status_code}"
                    notification_log.save()
                
                return {
                    "success": False,
                    "message": f"API request failed with status {response.status_code}",
                    "data": {"status_code": response.status_code, "response": response.text}
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Email API request timed out for {to}")
            
            # Update notification log on timeout
            if notification_log:
                notification_log.status = NotificationLog.Status.FAILED
                notification_log.error_message = "Request timed out"
                notification_log.save()
            
            return {
                "success": False,
                "message": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Email API request failed for {to}: {str(e)}")
            
            # Update notification log on request exception
            if notification_log:
                notification_log.status = NotificationLog.Status.FAILED
                notification_log.error_message = f"Request failed: {str(e)}"
                notification_log.save()
            
            return {
                "success": False,
                "message": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to}: {str(e)}")
            
            # Update notification log on unexpected error
            if notification_log:
                notification_log.status = NotificationLog.Status.FAILED
                notification_log.error_message = f"Unexpected error: {str(e)}"
                notification_log.save()
            
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def send_sms(
        self,
        number: str,
        message: str,
        application=None,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS via notification API and log it.
        
        Args:
            number: Phone number (Ghana format: 0541234567)
            message: SMS message content
            application: Related application object (optional)
            template_name: Template name for logging (optional)
            
        Returns:
            Dict with success status and message
        """
        # Create notification log entry
        notification_log = None
        sms_notification = None
        try:
            from notifications.models import NotificationLog, NotificationTemplate, SMSNotification
            
            # Get existing template based on template_name or use APPLICATION_SUBMITTED as default
            template = None
            if template_name:
                template = NotificationTemplate.objects.filter(
                    name=template_name,
                    is_active=True
                ).first()
            
            if not template:
                template = NotificationTemplate.objects.filter(
                    notification_type=NotificationTemplate.NotificationType.APPLICATION_SUBMITTED
                ).first()
            
            # If no template exists, create one
            if not template:
                template = NotificationTemplate.objects.create(
                    name="Application Submitted SMS Template",
                    notification_type=NotificationTemplate.NotificationType.APPLICATION_SUBMITTED,
                    subject="Application Notification",
                    body_html="",
                    body_text="",
                    is_active=True
                )
            
            # Create notification log
            notification_log = NotificationLog.objects.create(
                template=template,
                channel=NotificationLog.Channel.SMS,
                recipient_email="",  # SMS doesn't have email
                recipient_name="",  # Will be updated if we have application
                recipient_phone=number,
                subject=message[:100],  # Use first 100 chars as subject
                body_html="",
                body_text=message,
                status=NotificationLog.Status.PENDING,
                application=application,
                context_data={}
            )
            
            # Create SMS notification record
            sms_notification = SMSNotification.objects.create(
                recipient_phone=number,
                recipient_name="",  # Will be updated if we have application
                message=message,
                template_name=template_name or "Application Submitted SMS Template",
                status=SMSNotification.Status.PENDING,
                application=application
            )
            
            # Update recipient name if we have application
            if application:
                recipient_name = application.business_name or application.contact_person
                notification_log.recipient_name = recipient_name
                notification_log.save()
                sms_notification.recipient_name = recipient_name
                sms_notification.save()
                
        except Exception as e:
            logger.error(f"Failed to create SMS notification log: {str(e)}")
        
        try:
            url = f"{self.base_url}/api/sms"
            
            payload = {
                "number": number,
                "message": message
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"SMS sent successfully to {number}")
                    
                    # Update notification log on success
                    if notification_log:
                        notification_log.status = NotificationLog.Status.SENT
                        notification_log.sent_at = timezone.now()
                        notification_log.external_id = result.get('message_id', '')
                        notification_log.save()
                    
                    # Update SMS notification on success
                    if sms_notification:
                        sms_notification.status = SMSNotification.Status.SENT
                        sms_notification.sent_at = timezone.now()
                        sms_notification.external_id = result.get('message_id', '')
                        sms_notification.save()
                    
                    return {
                        "success": True,
                        "message": "SMS sent successfully",
                        "data": result
                    }
                else:
                    logger.error(f"SMS API returned error: {result.get('message', 'Unknown error')}")
                    
                    # Update notification log on failure
                    if notification_log:
                        notification_log.status = NotificationLog.Status.FAILED
                        notification_log.error_message = result.get('message', 'Unknown error')
                        notification_log.save()
                    
                    # Update SMS notification on failure
                    if sms_notification:
                        sms_notification.status = SMSNotification.Status.FAILED
                        sms_notification.error_message = result.get('message', 'Unknown error')
                        sms_notification.save()
                    
                    return {
                        "success": False,
                        "message": result.get('message', 'SMS sending failed'),
                        "data": result
                    }
            else:
                logger.error(f"SMS API request failed with status {response.status_code}: {response.text}")
                
                # Update notification log on failure
                if notification_log:
                    notification_log.status = NotificationLog.Status.FAILED
                    notification_log.error_message = f"API request failed with status {response.status_code}"
                    notification_log.save()
                
                # Update SMS notification on failure
                if sms_notification:
                    sms_notification.status = SMSNotification.Status.FAILED
                    sms_notification.error_message = f"API request failed with status {response.status_code}"
                    sms_notification.save()
                
                return {
                    "success": False,
                    "message": f"API request failed with status {response.status_code}",
                    "data": {"status_code": response.status_code, "response": response.text}
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"SMS API request timed out for {number}")
            
            # Update notification log on timeout
            if notification_log:
                notification_log.status = NotificationLog.Status.FAILED
                notification_log.error_message = "Request timed out"
                notification_log.save()
            
            # Update SMS notification on timeout
            if sms_notification:
                sms_notification.status = SMSNotification.Status.FAILED
                sms_notification.error_message = "Request timed out"
                sms_notification.save()
            
            return {
                "success": False,
                "message": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"SMS API request failed for {number}: {str(e)}")
            
            # Update notification log on request exception
            if notification_log:
                notification_log.status = NotificationLog.Status.FAILED
                notification_log.error_message = f"Request failed: {str(e)}"
                notification_log.save()
            
            # Update SMS notification on request exception
            if sms_notification:
                sms_notification.status = SMSNotification.Status.FAILED
                sms_notification.error_message = f"Request failed: {str(e)}"
                sms_notification.save()
            
            return {
                "success": False,
                "message": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {number}: {str(e)}")
            
            # Update notification log on unexpected error
            if notification_log:
                notification_log.status = NotificationLog.Status.FAILED
                notification_log.error_message = f"Unexpected error: {str(e)}"
                notification_log.save()
            
            # Update SMS notification on unexpected error
            if sms_notification:
                sms_notification.status = SMSNotification.Status.FAILED
                sms_notification.error_message = f"Unexpected error: {str(e)}"
                sms_notification.save()
            
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def send_notification(
        self,
        recipient_email: str = None,
        recipient_phone: str = None,
        template=None,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Send notification using a NotificationTemplate.
        
        Args:
            recipient_email: Recipient email address (optional)
            recipient_phone: Recipient phone number (optional)
            template: NotificationTemplate object
            context: Template context variables
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not template:
            logger.error("No template provided to send_notification")
            return False
        
        if not recipient_email and not recipient_phone:
            logger.error("No recipient provided to send_notification")
            return False
        
        context = context or {}
        
        try:
            # Render template with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_template = Template(template.body)
            
            template_context = Context(context)
            rendered_subject = subject_template.render(template_context)
            rendered_body = body_template.render(template_context)
            
            success = False
            
            # Send email if recipient_email is provided
            if recipient_email:
                email_result = self.send_email(
                    to=recipient_email,
                    subject=rendered_subject,
                    body=rendered_body,
                    is_html=True,
                    template_name=template.name
                )
                success = email_result.get('success', False)
            
            # Send SMS if recipient_phone is provided
            if recipient_phone:
                sms_result = self.send_sms(
                    number=recipient_phone,
                    message=rendered_body,
                    template_name=template.name
                )
                success = success or sms_result.get('success', False)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification with template {template.name}: {str(e)}")
            return False


# Global instance
notification_service = NotificationService()


def send_notification_email(
    to: str,
    subject: str,
    body: str,
    is_html: bool = True,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    application=None,
    template_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send email notifications.
    """
    return notification_service.send_email(to, subject, body, is_html, from_email, from_name, application, template_name)


def send_notification_sms(
    number: str, 
    message: str, 
    application=None, 
    template_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send SMS notifications.
    """
    return notification_service.send_sms(number, message, application, template_name)
