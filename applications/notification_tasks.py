"""
Background notification tasks for application processing.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_admin_notification_task(application_id):
    """Send admin notification for new application."""
    try:
        from applications.models import SupplierApplication
        from core.admin_notification_service import send_admin_new_application_notification
        
        application = SupplierApplication.objects.get(id=application_id)
        result = send_admin_new_application_notification(application)
        
        logger.info(f"Admin notification sent for application {application.tracking_code}: {result.get('success', False)}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to send admin notification for application {application_id}: {str(e)}")
        raise


def send_confirmation_notifications_task(application_id):
    """Send confirmation email and SMS to applicant."""
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
        logger.info(f"Application confirmation email sent using template: {email_result.get('success', False)}")
        
        # Send SMS
        send_application_confirmation_sms(application)
        logger.info(f"Confirmation SMS sent to {application.telephone} for application {application.tracking_code}")
        
        return {
            'email_result': email_result,
            'sms_sent': True
        }
        
    except Exception as e:
        logger.error(f"Failed to send confirmation notifications for application {application_id}: {str(e)}")
        raise


def send_document_request_notification_task(application_id):
    """Send document request notification if documents are missing."""
    try:
        from applications.models import SupplierApplication
        from core.utils import check_missing_documents
        from core.template_notification_service import send_template_notification
        
        application = SupplierApplication.objects.get(id=application_id)
        
        # Check for missing documents
        missing_docs = check_missing_documents(application)
        
        if missing_docs:
            logger.info(f"Application {application.tracking_code} has missing documents but status remains PENDING_REVIEW")
            
            # Convert DocumentRequirement objects to dict format expected by template
            missing_docs_dict = [{'name': doc.label} for doc in missing_docs]
            
            # Send document request using template
            doc_result = send_template_notification(
                template_name="Document Request Notification",
                recipient_email=application.email,
                application=application,
                context_data={'missing_documents': missing_docs_dict},
                channel='EMAIL'
            )
            logger.info(f"Document request email sent using template: {doc_result.get('success', False)}")
            
            return {
                'documents_requested': True,
                'missing_docs_count': len(missing_docs),
                'email_result': doc_result
            }
        else:
            logger.info(f"Application {application.tracking_code} has all required documents")
            return {
                'documents_requested': False,
                'missing_docs_count': 0
            }
        
    except Exception as e:
        logger.error(f"Failed to send document request notification for application {application_id}: {str(e)}")
        raise


def send_all_notifications_task(application_id):
    """Send all notifications for an application in sequence."""
    try:
        # Send admin notification
        admin_result = send_admin_notification_task(application_id)
        
        # Send confirmation notifications
        confirmation_result = send_confirmation_notifications_task(application_id)
        
        # Send document request if needed
        doc_request_result = send_document_request_notification_task(application_id)
        
        return {
            'admin_notification': admin_result,
            'confirmation_notifications': confirmation_result,
            'document_request': doc_request_result
        }
        
    except Exception as e:
        logger.error(f"Failed to send all notifications for application {application_id}: {str(e)}")
        raise
