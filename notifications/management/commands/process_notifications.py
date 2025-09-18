"""
Management command to process queued notifications.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import NotificationLog
from core.notification_service import send_notification_email, send_notification_sms
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process queued notifications and send them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of notifications to process (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Processing up to {limit} queued notifications...")
        
        # Get pending notifications
        pending_notifications = NotificationLog.objects.filter(
            status=NotificationLog.Status.PENDING
        ).select_related('application', 'template')[:limit]
        
        if not pending_notifications.exists():
            self.stdout.write(self.style.SUCCESS("No pending notifications found."))
            return
        
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                self.stdout.write(f"Processing notification {notification.id} to {notification.recipient_email}...")
                
                if dry_run:
                    self.stdout.write(f"  [DRY RUN] Would send: {notification.subject}")
                    sent_count += 1
                    continue
                
                # Send using notification API
                if notification.channel == NotificationLog.Channel.EMAIL:
                    result = send_notification_email(
                        to=notification.recipient_email,
                        subject=notification.subject,
                        body=notification.body_html,
                        is_html=True,
                        from_name="GCX eServices",
                        application=notification.application,
                        template_name=notification.template.name if notification.template else None
                    )
                elif notification.channel == NotificationLog.Channel.SMS:
                    result = send_notification_sms(
                        number=notification.recipient_phone,
                        message=notification.body_text,
                        application=notification.application,
                        template_name=notification.template.name if notification.template else None
                    )
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ Unsupported channel: {notification.channel}"))
                    failed_count += 1
                    continue
                
                if result['success']:
                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Sent notification {notification.id} via {notification.channel}"))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed to send notification {notification.id}: {result['message']}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Failed to send notification {notification.id}: {str(e)}"))
                
                # Mark as failed
                notification.status = NotificationLog.Status.FAILED
                notification.failed_at = timezone.now()
                notification.retry_count += 1
                notification.save()
                
                failed_count += 1
        
        # Summary
        total_processed = sent_count + failed_count
        self.stdout.write(f"\nProcessed {total_processed} notifications:")
        self.stdout.write(f"  ✓ Sent: {sent_count}")
        self.stdout.write(f"  ✗ Failed: {failed_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run - no emails were actually sent."))
        else:
            self.stdout.write(self.style.SUCCESS("Notification processing completed!"))
