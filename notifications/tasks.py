from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import NotificationLog, NotificationTemplate
from .services import NotificationService
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_pending_notifications():
    """Send all pending notifications"""
    try:
        pending_notifications = NotificationLog.objects.filter(
            status=NotificationLog.Status.PENDING
        ).select_related('application', 'template')
        
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                # Send the actual email
                send_mail(
                    subject=notification.subject,
                    message=notification.body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient_email],
                    html_message=notification.body_html,
                    fail_silently=False,
                )
                
                notification.mark_sent()
                sent_count += 1
                logger.info(f"Sent notification {notification.id} to {notification.recipient_email}")
                
            except Exception as e:
                logger.error(f"Failed to send notification {notification.id}: {str(e)}")
                notification.mark_failed()
                failed_count += 1
        
        logger.info(f"Notification task completed: {sent_count} sent, {failed_count} failed")
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': sent_count + failed_count
        }
        
    except Exception as e:
        logger.error(f"Error in send_pending_notifications task: {str(e)}")
        return {'error': str(e)}

@shared_task
def cleanup_old_notifications():
    """Clean up old notification logs"""
    try:
        from datetime import timedelta
        
        # Delete notifications older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = NotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return f"Cleaned up {deleted_count} notifications"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def send_notification_async(notification_id):
    """Send a single notification asynchronously"""
    try:
        notification = NotificationLog.objects.get(id=notification_id)
        
        # Send the email
        send_mail(
            subject=notification.subject,
            message=notification.body_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient_email],
            html_message=notification.body_html,
            fail_silently=False,
        )
        
        notification.mark_sent()
        logger.info(f"Sent notification {notification_id} to {notification.recipient_email}")
        return f"Notification {notification_id} sent successfully"
        
    except NotificationLog.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return f"Notification {notification_id} not found"
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def retry_failed_notifications():
    """Retry failed notifications that can be retried"""
    try:
        failed_notifications = NotificationLog.objects.filter(
            status=NotificationLog.Status.FAILED
        ).filter(
            retry_count__lt=3  # Max 3 retries
        )
        
        retried_count = 0
        for notification in failed_notifications:
            if notification.can_retry():
                try:
                    send_mail(
                        subject=notification.subject,
                        message=notification.body_text,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[notification.recipient_email],
                        html_message=notification.body_html,
                        fail_silently=False,
                    )
                    
                    notification.mark_sent()
                    retried_count += 1
                    logger.info(f"Retried notification {notification.id}")
                    
                except Exception as e:
                    notification.schedule_retry()
                    logger.error(f"Retry failed for notification {notification.id}: {str(e)}")
        
        logger.info(f"Retried {retried_count} failed notifications")
        return f"Retried {retried_count} notifications"
        
    except Exception as e:
        logger.error(f"Error in retry_failed_notifications: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def send_application_status_update(application_id, status, message=None):
    """Send application status update notification"""
    try:
        from applications.models import SupplierApplication
        
        application = SupplierApplication.objects.get(id=application_id)
        
        # Create notification based on status
        if status == 'APPROVED':
            NotificationService.send_application_approval_notification(application)
        elif status == 'REJECTED':
            NotificationService.send_application_rejection_notification(application, message)
        elif status == 'NEEDS_MORE_DOCS':
            NotificationService.send_document_request_notification(application, message)
        
        logger.info(f"Sent status update notification for application {application_id}")
        return f"Status update notification sent for application {application_id}"
        
    except Exception as e:
        logger.error(f"Error sending status update notification: {str(e)}")
        return f"Error: {str(e)}"
