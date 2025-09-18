"""
Utility functions for GCX Supplier Application Portal.
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.signing import Signer
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def send_application_confirmation_email(application):
    """
    Send confirmation email to applicant after submission.
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
        
        # Use notification service for sending email
        from .notification_service import send_notification_email
        
        result = send_notification_email(
            to=application.email,
            subject=subject,
            body=html_message,
            is_html=True,
            from_name="GCX eServices",
            application=application,
            template_name="Application Confirmation Email"
        )
        
        if result['success']:
            logger.info(f"Confirmation email sent to {application.email} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send confirmation email to {application.email}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {application.email}: {str(e)}")
        return False


def send_outstanding_documents_email(application, missing_requirements):
    """
    Send email to applicant requesting outstanding documents.
    """
    try:
        subject = f"Outstanding Documents Required - GCX Supplier Portal (Tracking: {application.tracking_code})"
        
        # Generate secure link for document upload
        signer = Signer()
        token = signer.sign(application.tracking_code)
        upload_url = f"{settings.FRONTEND_PUBLIC_URL}/api/applications/{application.tracking_code}/outstanding/?token={token}"
        
        context = {
            'application': application,
            'tracking_code': application.tracking_code,
            'business_name': application.business_name,
            'missing_requirements': missing_requirements,
            'upload_url': upload_url,
            'expires_at': timezone.now() + timedelta(days=30)  # Link expires in 30 days
        }
        
        html_message = render_to_string('emails/outstanding_documents.html', context)
        
        # Use notification service for sending email
        from .notification_service import send_notification_email
        
        result = send_notification_email(
            to=application.email,
            subject=subject,
            body=html_message,
            is_html=True,
            from_name="GCX eServices",
            application=application,
            template_name="Outstanding Documents Email"
        )
        
        if result['success']:
            logger.info(f"Outstanding documents email sent to {application.email} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send outstanding documents email to {application.email}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send outstanding documents email to {application.email}: {str(e)}")
        return False


def send_approval_email(application, supplier_user, temp_password):
    """
    Send approval email with login credentials to supplier.
    """
    try:
        subject = f"Application Approved - GCX Supplier Portal (Tracking: {application.tracking_code})"
        
        login_url = f"{settings.FRONTEND_PUBLIC_URL}/admin/"
        
        context = {
            'application': application,
            'supplier_user': supplier_user,
            'temp_password': temp_password,
            'login_url': login_url,
            'business_name': application.business_name,
            'tracking_code': application.tracking_code
        }
        
        html_message = render_to_string('emails/application_approved.html', context)
        
        # Use notification service for sending email
        from .notification_service import send_notification_email
        
        result = send_notification_email(
            to=application.email,
            subject=subject,
            body=html_message,
            is_html=True,
            from_name="GCX eServices",
            application=application,
            template_name="Application Approval with Credentials"
        )
        
        if result['success']:
            logger.info(f"Approval email sent to {application.email} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send approval email to {application.email}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send approval email to {application.email}: {str(e)}")
        return False


def send_rejection_email(application, reason):
    """
    Send rejection email to applicant.
    """
    try:
        subject = f"Application Update - GCX Supplier Portal (Tracking: {application.tracking_code})"
        
        context = {
            'application': application,
            'reason': reason,
            'business_name': application.business_name,
            'tracking_code': application.tracking_code,
            'rejected_at': application.decided_at
        }
        
        html_message = render_to_string('emails/application_rejected.html', context)
        
        # Use notification service for sending email
        from .notification_service import send_notification_email
        
        result = send_notification_email(
            to=application.email,
            subject=subject,
            body=html_message,
            is_html=True,
            from_name="GCX eServices",
            application=application,
            template_name="Application Rejection Notification"
        )
        
        if result['success']:
            logger.info(f"Rejection email sent to {application.email} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send rejection email to {application.email}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send rejection email to {application.email}: {str(e)}")
        return False


def validate_ghana_phone_number(phone_number):
    """
    Validate Ghana phone number format.
    """
    import re
    pattern = r'^\+233\d{9}$'
    return bool(re.match(pattern, phone_number))


def format_ghana_phone_number(phone_number):
    """
    Format phone number to Ghana format.
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # If it starts with 233, add +
    if digits.startswith('233') and len(digits) == 12:
        return f"+{digits}"
    
    # If it starts with 0, replace with +233
    if digits.startswith('0') and len(digits) == 10:
        return f"+233{digits[1:]}"
    
    # If it's 9 digits, add +233
    if len(digits) == 9:
        return f"+233{digits}"
    
    return phone_number  # Return as-is if can't format


def format_phone_for_sms(phone_number):
    """
    Format phone number for SMS API (Ghana format: 0541234567).
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # If it starts with 233, remove it and add 0
    if digits.startswith('233') and len(digits) == 12:
        return f"0{digits[3:]}"
    
    # If it's 9 digits, add 0
    if len(digits) == 9:
        return f"0{digits}"
    
    # If it already starts with 0 and is 10 digits, return as-is
    if digits.startswith('0') and len(digits) == 10:
        return digits
    
    return phone_number  # Return as-is if can't format


def send_application_confirmation_sms(application):
    """
    Send SMS confirmation to applicant after submission.
    """
    try:
        from .notification_service import send_notification_sms
        
        # Format phone number for SMS API
        phone = format_phone_for_sms(application.telephone)
        
        message = f"GCX: Your application {application.tracking_code} has been submitted successfully. Check your email for details."
        
        result = send_notification_sms(
            number=phone, 
            message=message,
            application=application,
            template_name="Application Submission Confirmation"
        )
        
        if result['success']:
            logger.info(f"Confirmation SMS sent to {phone} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send confirmation SMS to {phone}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send confirmation SMS to {application.telephone}: {str(e)}")
        return False


def send_approval_sms(application):
    """
    Send SMS notification when application is approved.
    """
    try:
        from .notification_service import send_notification_sms
        
        # Format phone number for SMS API
        phone = format_phone_for_sms(application.telephone)
        
        message = f"GCX: Congratulations! Your application {application.tracking_code} has been approved. Check your email for login details."
        
        result = send_notification_sms(
            number=phone, 
            message=message,
            application=application,
            template_name="Application Approval with Credentials"
        )
        
        if result['success']:
            logger.info(f"Approval SMS sent to {phone} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send approval SMS to {phone}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send approval SMS to {application.telephone}: {str(e)}")
        return False


def send_rejection_sms(application, reason):
    """
    Send SMS notification when application is rejected.
    """
    try:
        from .notification_service import send_notification_sms
        
        # Format phone number for SMS API
        phone = format_phone_for_sms(application.telephone)
        
        message = f"GCX: Your application {application.tracking_code} status has been updated. Check your email for details."
        
        result = send_notification_sms(
            number=phone, 
            message=message,
            application=application,
            template_name="Application Rejection Notification"
        )
        
        if result['success']:
            logger.info(f"Rejection SMS sent to {phone} for application {application.tracking_code}")
            return True
        else:
            logger.error(f"Failed to send rejection SMS to {phone}: {result['message']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send rejection SMS to {application.telephone}: {str(e)}")
        return False


def check_missing_documents(application):
    """
    Check which required documents are missing for an application.
    """
    from documents.models import DocumentRequirement, DocumentUpload
    
    # Get all required document requirements
    required_requirements = DocumentRequirement.objects.filter(is_required=True)
    
    # Check if FDA certificate is required based on commodities (Tom Brown, Palm Oil)
    processed_food_commodities = ['Tom Brown', 'Palm Oil']
    if application.commodities_to_supply.filter(name__in=processed_food_commodities).exists() or \
       (application.other_commodities and any(food in application.other_commodities for food in processed_food_commodities)):
        fda_requirement = DocumentRequirement.objects.filter(code='FDA_CERT_PROCESSED_FOOD').first()
        if fda_requirement:
            required_requirements = required_requirements | DocumentRequirement.objects.filter(id=fda_requirement.id)
    
    missing_requirements = []
    
    for requirement in required_requirements:
        # Check if document is uploaded (verification happens later by admin)
        upload = DocumentUpload.objects.filter(
            application=application,
            requirement=requirement
        ).first()
        
        if not upload:
            missing_requirements.append(requirement)
    
    return missing_requirements


def generate_secure_upload_token(tracking_code):
    """
    Generate a secure token for document upload.
    """
    signer = Signer()
    return signer.sign(tracking_code)


def verify_upload_token(token):
    """
    Verify and extract tracking code from upload token.
    """
    try:
        signer = Signer()
        tracking_code = signer.unsign(token)
        return tracking_code
    except:
        return None


def log_admin_action(user, action, model_name, object_id, details=None):
    """
    Log admin actions for audit trail.
    """
    from core.models import AuditLog
    
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            details=details or {},
            ip_address=user.last_login  # This would be better with request object
        )
    except Exception as e:
        logger.error(f"Failed to log admin action: {str(e)}")


def get_application_summary_stats():
    """
    Get summary statistics for applications.
    """
    from applications.models import SupplierApplication
    
    stats = {
        'total_applications': SupplierApplication.objects.filter(is_deleted=False).count(),
        'submitted': SupplierApplication.objects.filter(
            status=SupplierApplication.ApplicationStatus.SUBMITTED,
            is_deleted=False
        ).count(),
        'under_review': SupplierApplication.objects.filter(
            status=SupplierApplication.ApplicationStatus.UNDER_REVIEW,
            is_deleted=False
        ).count(),
        'needs_more_docs': SupplierApplication.objects.filter(
            status=SupplierApplication.ApplicationStatus.NEEDS_MORE_DOCS,
            is_deleted=False
        ).count(),
        'approved': SupplierApplication.objects.filter(
            status=SupplierApplication.ApplicationStatus.APPROVED,
            is_deleted=False
        ).count(),
        'rejected': SupplierApplication.objects.filter(
            status=SupplierApplication.ApplicationStatus.REJECTED,
            is_deleted=False
        ).count(),
    }
    
    return stats
