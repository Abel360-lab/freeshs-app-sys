"""
Immediate email service using notification API with enhanced delivery tracking.
"""
import logging
import requests
from django.conf import settings
from django.template.loader import render_to_string
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class ImmediateEmailService:
    """Service for sending emails immediately with enhanced tracking."""
    
    def __init__(self):
        self.base_url = settings.NOTIFICATION_API_BASE_URL
        self.timeout = 30  # seconds
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def send_email_immediate(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = True,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        priority: str = "high"  # high, normal, low
    ) -> Dict[str, Any]:
        """
        Send email immediately with enhanced delivery tracking.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default: True)
            from_email: Override sender email (optional)
            from_name: Override sender name (optional)
            priority: Email priority (high, normal, low)
            
        Returns:
            Dict with success status and detailed message
        """
        try:
            url = f"{self.base_url}/api/email"
            
            # Enhanced payload with priority and tracking
            payload = {
                "to": to,
                "subject": subject,
                "body": body,
                "isHtml": is_html,
                "priority": priority,  # Add priority for immediate delivery
                "tracking": True,      # Enable tracking
                "immediate": True      # Request immediate delivery
            }
            
            # Add optional sender overrides
            if from_email:
                payload["fromEmail"] = from_email
            if from_name:
                payload["fromName"] = from_name
            
            headers = {
                "Content-Type": "application/json",
                "X-Priority": priority.upper(),
                "X-Immediate": "true"
            }
            
            # Try sending with retries for immediate delivery
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Sending immediate email to {to} (attempt {attempt + 1})")
                    
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"Immediate email sent successfully to {to}")
                            return {
                                "success": True,
                                "message": "Email sent immediately",
                                "method": "immediate_api",
                                "attempt": attempt + 1,
                                "data": result
                            }
                        else:
                            logger.warning(f"API returned error for {to}: {result.get('message', 'Unknown error')}")
                            if attempt < self.max_retries - 1:
                                time.sleep(self.retry_delay)
                                continue
                    else:
                        logger.warning(f"API request failed with status {response.status_code} for {to}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"Email API request timed out for {to} (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Email API request failed for {to} (attempt {attempt + 1}): {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
            
            # If all retries failed
            logger.error(f"Failed to send immediate email to {to} after {self.max_retries} attempts")
            return {
                "success": False,
                "message": f"Failed after {self.max_retries} attempts",
                "method": "immediate_api"
            }
                
        except Exception as e:
            logger.error(f"Unexpected error sending immediate email to {to}: {str(e)}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "method": "immediate_api"
            }


# Global instance
immediate_email_service = ImmediateEmailService()


def send_immediate_email(
    to: str,
    subject: str,
    body: str,
    is_html: bool = True,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    priority: str = "high"
) -> Dict[str, Any]:
    """
    Convenience function to send immediate email notifications.
    """
    return immediate_email_service.send_email_immediate(
        to, subject, body, is_html, from_email, from_name, priority
    )


def send_application_confirmation_email_immediate(application):
    """
    Send immediate confirmation email to applicant after submission.
    """
    try:
        subject = f"Application Submitted - GCX Supplier Portal (Tracking: {application.tracking_code})"
        
        context = {
            'application': application,
            'tracking_code': application.tracking_code,
            'business_name': application.business_name,
            'submitted_at': application.submitted_at,
            'status_url': f"{settings.FRONTEND_PUBLIC_URL}/api/applications/{application.tracking_code}/status/"
        }
        
        html_message = render_to_string('emails/application_confirmation.html', context)
        
        result = send_immediate_email(
            to=application.email,
            subject=subject,
            body=html_message,
            is_html=True,
            from_name="GCX eServices",
            priority="high"  # High priority for immediate delivery
        )
        
        if result['success']:
            logger.info(f"Immediate confirmation email sent to {application.email} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send immediate confirmation email to {application.email}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send immediate confirmation email to {application.email}: {str(e)}")
        return False
