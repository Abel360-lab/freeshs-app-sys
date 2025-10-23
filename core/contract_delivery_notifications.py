"""
Contract and delivery notification utilities for GCX Supplier Application Portal.
"""

import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .notification_service import send_notification_email

logger = logging.getLogger(__name__)


def send_contract_awarded_notification(contract, supplier):
    """
    Send notification to supplier when a contract is awarded.
    
    Args:
        contract: SupplierContract instance
        supplier: User instance (supplier)
    """
    try:
        from notifications.models import NotificationTemplate
        
        # Get the contract awarded template
        template = NotificationTemplate.objects.filter(
            notification_type=NotificationTemplate.NotificationType.CONTRACT_AWARDED,
            is_active=True
        ).first()
        
        if not template:
            logger.error("Contract awarded template not found")
            return False
        
        # Prepare context
        context = {
            'contract': contract,
            'supplier': supplier,
            'portal_url': f"{settings.FRONTEND_PUBLIC_URL}/supplier/contracts/{contract.id}/"
        }
        
        # Render subject and body
        from django.template import Template, Context
        subject_template = Template(template.subject)
        body_template = Template(template.body_html)
        
        rendered_subject = subject_template.render(Context(context))
        rendered_body = body_template.render(Context(context))
        
        # Send email
        result = send_notification_email(
            to=supplier.email,
            subject=rendered_subject,
            body=rendered_body,
            is_html=True,
            from_name="GCX eServices",
            template_name=template.name
        )
        
        if result['success']:
            logger.info(f"Contract awarded notification sent to {supplier.email} for contract {contract.contract_number}")
            return True
        else:
            logger.error(f"Failed to send contract awarded notification to {supplier.email}: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending contract awarded notification: {str(e)}")
        return False


def send_delivery_submitted_notification(delivery):
    """
    Send notification to admin when a delivery is submitted.
    
    Args:
        delivery: DeliveryTracking instance
    """
    try:
        from notifications.models import NotificationTemplate
        from django.contrib.auth.models import User
        
        # Get the delivery submitted template
        template = NotificationTemplate.objects.filter(
            notification_type=NotificationTemplate.NotificationType.DELIVERY_SUBMITTED,
            is_active=True
        ).first()
        
        if not template:
            logger.error("Delivery submitted template not found")
            return False
        
        # Get admin users (staff members)
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        if not admin_users.exists():
            logger.warning("No admin users found to send delivery submitted notification")
            return False
        
        # Prepare context
        context = {
            'delivery': delivery,
            'admin_url': f"{settings.FRONTEND_PUBLIC_URL}/backoffice/deliveries/{delivery.id}/"
        }
        
        # Render subject and body
        from django.template import Template, Context
        subject_template = Template(template.subject)
        body_template = Template(template.body_html)
        
        rendered_subject = subject_template.render(Context(context))
        rendered_body = body_template.render(Context(context))
        
        # Send to all admin users
        success_count = 0
        for admin in admin_users:
            result = send_notification_email(
                to=admin.email,
                subject=rendered_subject,
                body=rendered_body,
                is_html=True,
                from_name="GCX eServices",
                template_name=template.name
            )
            
            if result['success']:
                success_count += 1
                logger.info(f"Delivery submitted notification sent to admin {admin.email} for delivery {delivery.serial_number}")
            else:
                logger.error(f"Failed to send delivery submitted notification to admin {admin.email}: {result['message']}")
        
        return success_count > 0
            
    except Exception as e:
        logger.error(f"Error sending delivery submitted notification: {str(e)}")
        return False


def send_delivery_verified_notification(delivery):
    """
    Send notification to supplier when a delivery is verified.
    
    Args:
        delivery: DeliveryTracking instance
    """
    try:
        from notifications.models import NotificationTemplate
        
        # Get the delivery verified template
        template = NotificationTemplate.objects.filter(
            notification_type=NotificationTemplate.NotificationType.DELIVERY_VERIFIED,
            is_active=True
        ).first()
        
        if not template:
            logger.error("Delivery verified template not found")
            return False
        
        # Prepare context
        context = {
            'delivery': delivery,
            'portal_url': f"{settings.FRONTEND_PUBLIC_URL}/supplier/deliveries/{delivery.id}/"
        }
        
        # Render subject and body
        from django.template import Template, Context
        subject_template = Template(template.subject)
        body_template = Template(template.body_html)
        
        rendered_subject = subject_template.render(Context(context))
        rendered_body = body_template.render(Context(context))
        
        # Send email
        result = send_notification_email(
            to=delivery.supplier_user.email,
            subject=rendered_subject,
            body=rendered_body,
            is_html=True,
            from_name="GCX eServices",
            template_name=template.name
        )
        
        if result['success']:
            logger.info(f"Delivery verified notification sent to {delivery.supplier_user.email} for delivery {delivery.serial_number}")
            return True
        else:
            logger.error(f"Failed to send delivery verified notification to {delivery.supplier_user.email}: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending delivery verified notification: {str(e)}")
        return False


def send_delivery_rejected_notification(delivery):
    """
    Send notification to supplier when a delivery is rejected.
    
    Args:
        delivery: DeliveryTracking instance
    """
    try:
        from notifications.models import NotificationTemplate
        
        # Get the delivery rejected template
        template = NotificationTemplate.objects.filter(
            notification_type=NotificationTemplate.NotificationType.DELIVERY_REJECTED,
            is_active=True
        ).first()
        
        if not template:
            logger.error("Delivery rejected template not found")
            return False
        
        # Prepare context
        context = {
            'delivery': delivery,
            'portal_url': f"{settings.FRONTEND_PUBLIC_URL}/supplier/deliveries/{delivery.id}/"
        }
        
        # Render subject and body
        from django.template import Template, Context
        subject_template = Template(template.subject)
        body_template = Template(template.body_html)
        
        rendered_subject = subject_template.render(Context(context))
        rendered_body = body_template.render(Context(context))
        
        # Send email
        result = send_notification_email(
            to=delivery.supplier_user.email,
            subject=rendered_subject,
            body=rendered_body,
            is_html=True,
            from_name="GCX eServices",
            template_name=template.name
        )
        
        if result['success']:
            logger.info(f"Delivery rejected notification sent to {delivery.supplier_user.email} for delivery {delivery.serial_number}")
            return True
        else:
            logger.error(f"Failed to send delivery rejected notification to {delivery.supplier_user.email}: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending delivery rejected notification: {str(e)}")
        return False
