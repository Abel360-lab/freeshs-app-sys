"""
Simplified background task system using threading for better performance.
"""

import threading
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def run_in_background(func):
    """Decorator to run a function in background thread."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        def run():
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Background task {func.__name__} failed: {str(e)}")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info(f"Background task {func.__name__} started")
    
    return wrapper


@run_in_background
def send_admin_notification_async(application_id):
    """Send admin notification asynchronously."""
    try:
        from applications.models import SupplierApplication
        from core.admin_notification_service import send_admin_new_application_notification
        
        application = SupplierApplication.objects.get(id=application_id)
        result = send_admin_new_application_notification(application)
        logger.info(f"Admin notification sent for application {application.tracking_code}: {result.get('success', False)}")
        
    except Exception as e:
        logger.error(f"Failed to send admin notification for application {application_id}: {str(e)}")


@run_in_background
def send_confirmation_notifications_async(application_id):
    """Send confirmation notifications asynchronously."""
    try:
        from applications.models import SupplierApplication
        from core.utils import send_application_confirmation_sms
        from core.template_notification_service import send_template_notification
        
        application = SupplierApplication.objects.get(id=application_id)
        
        # Send confirmation email using template
        email_result = send_template_notification(
            template_name="Application Submission Confirmation",
            recipient_email=application.email,
            application=application,
            channel='EMAIL'
        )
        logger.info(f"Application confirmation email sent: {email_result.get('success', False)}")
        
        # Send SMS
        send_application_confirmation_sms(application)
        logger.info(f"Confirmation SMS sent to {application.telephone}")
        
    except Exception as e:
        logger.error(f"Failed to send confirmation notifications for application {application_id}: {str(e)}")


@run_in_background
def send_document_request_async(application_id):
    """Send document request notification asynchronously."""
    try:
        from applications.models import SupplierApplication
        from core.utils import check_missing_documents
        from core.template_notification_service import send_template_notification
        
        application = SupplierApplication.objects.get(id=application_id)
        
        # Check for missing documents
        missing_docs = check_missing_documents(application)
        
        if missing_docs:
            logger.info(f"Application {application.tracking_code} has missing documents")
            
            # Convert DocumentRequirement objects to dict format
            missing_docs_dict = [{'name': doc.label} for doc in missing_docs]
            
            # Send document request using template
            doc_result = send_template_notification(
                template_name="Document Request Notification",
                recipient_email=application.email,
                application=application,
                context_data={'missing_documents': missing_docs_dict},
                channel='EMAIL'
            )
            logger.info(f"Document request email sent: {doc_result.get('success', False)}")
        
    except Exception as e:
        logger.error(f"Failed to send document request notification for application {application_id}: {str(e)}")


@run_in_background
def generate_pdf_async(application_id):
    """Generate PDF asynchronously."""
    try:
        from .tasks import generate_application_pdf_task
        generate_application_pdf_task(application_id)
        logger.info(f"PDF generated for application {application_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate PDF for application {application_id}: {str(e)}")


def enqueue_all_notifications(application_id):
    """Enqueue all notifications for an application."""
    # Send admin notification
    send_admin_notification_async(application_id)
    
    # Send confirmation notifications
    send_confirmation_notifications_async(application_id)
    
    # Send document request if needed
    send_document_request_async(application_id)
    
    # Generate PDF
    generate_pdf_async(application_id)
    
    logger.info(f"All background tasks enqueued for application {application_id}")
