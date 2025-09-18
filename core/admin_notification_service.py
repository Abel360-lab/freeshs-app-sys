"""
Admin notification service for sending notifications to administrators.
"""
import logging
from django.conf import settings
from core.template_notification_service import send_template_notification
from core.models import SystemSettings

logger = logging.getLogger(__name__)

def send_admin_new_application_notification(application):
    """
    Send notification to admin when a new application is submitted.
    
    Args:
        application: SupplierApplication instance
        
    Returns:
        dict: Result of the notification sending
    """
    try:
        # Get system settings to get admin email
        settings_instance = SystemSettings.get_settings()
        admin_email = settings_instance.admin_notification_email
        
        if not admin_email:
            logger.warning("No admin notification email configured in system settings")
            return {"success": False, "message": "No admin notification email configured"}
        
        # Prepare context data for the admin notification template
        context_data = {
            'application': application,
            'business_name': application.business_name,
            'contact_person': application.signer_name,  # Use signer_name instead of contact_person
            'email': application.email,
            'telephone': application.telephone,
            'tracking_code': application.tracking_code,
            'application_date': application.submitted_at.strftime('%B %d, %Y at %I:%M %p') if application.submitted_at else 'Not available',
            'submitted_at': application.submitted_at,
            'status': application.get_status_display(),
            'registration_number': application.registration_number,
            'business_type': application.business_type,
            'region': application.region.name if application.region else 'Not specified',
            'tin_number': application.tin_number,
            'years_in_business': getattr(application, 'years_in_business', None),  # Safe access
            'other_commodities': application.other_commodities,
            'review_url': f"{settings.FRONTEND_PUBLIC_URL}/backoffice/applications/{application.id}/",
            'approve_url': f"{settings.FRONTEND_PUBLIC_URL}/backoffice/applications/{application.id}/approve/",
            'reject_url': f"{settings.FRONTEND_PUBLIC_URL}/backoffice/applications/{application.id}/reject/",
        }
        
        # Get commodities
        commodities = []
        if hasattr(application, 'commodities_to_supply'):
            commodities = list(application.commodities_to_supply.all())
        context_data['commodities'] = commodities
        
        # Get document status
        from documents.models import DocumentUpload, DocumentRequirement
        document_uploads = DocumentUpload.objects.filter(application=application)
        required_documents = DocumentRequirement.objects.filter(is_active=True, is_required=True)
        
        documents_uploaded_count = document_uploads.count()
        total_required_documents = required_documents.count()
        
        missing_documents = []
        for req_doc in required_documents:
            uploaded_doc = document_uploads.filter(requirement=req_doc).first()
            if not uploaded_doc:
                missing_documents.append({'name': req_doc.label})
        
        context_data.update({
            'uploaded_documents_count': documents_uploaded_count,
            'total_documents_count': total_required_documents,
            'missing_documents_count': len(missing_documents),
            'missing_documents': missing_documents,
        })
        
        # Send the admin notification
        result = send_template_notification(
            template_name="Admin New Application Notification",
            recipient_email=admin_email,
            application=application,
            context_data=context_data,
            channel='EMAIL'
        )
        
        if result['success']:
            logger.info(f"Admin notification sent successfully for application {application.tracking_code}")
        else:
            logger.error(f"Failed to send admin notification for application {application.tracking_code}: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending admin notification for application {application.tracking_code}: {str(e)}")
        return {"success": False, "message": f"Error sending admin notification: {str(e)}"}

def send_admin_application_status_change_notification(application, old_status, new_status, changed_by=None):
    """
    Send notification to admin when application status changes.
    
    Args:
        application: SupplierApplication instance
        old_status: Previous status
        new_status: New status
        changed_by: User who made the change (optional)
        
    Returns:
        dict: Result of the notification sending
    """
    try:
        # Get system settings to get admin email
        settings_instance = SystemSettings.get_settings()
        admin_email = settings_instance.admin_notification_email
        
        if not admin_email:
            logger.warning("No admin notification email configured in system settings")
            return {"success": False, "message": "No admin notification email configured"}
        
        # Prepare context data
        context_data = {
            'application': application,
            'business_name': application.business_name,
            'tracking_code': application.tracking_code,
            'old_status': old_status,
            'new_status': new_status,
            'changed_by': changed_by.username if changed_by else 'System',
            'changed_at': application.updated_at,
            'admin_url': f"{settings.FRONTEND_PUBLIC_URL}/backoffice/applications/{application.id}/",
        }
        
        # Send notification (you might want to create a separate template for status changes)
        result = send_template_notification(
            template_name="Admin New Application Notification",  # Using same template for now
            recipient_email=admin_email,
            application=application,
            context_data=context_data,
            channel='EMAIL'
        )
        
        if result['success']:
            logger.info(f"Admin status change notification sent for application {application.tracking_code}")
        else:
            logger.error(f"Failed to send admin status change notification: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending admin status change notification: {str(e)}")
        return {"success": False, "message": f"Error sending admin status change notification: {str(e)}"}
