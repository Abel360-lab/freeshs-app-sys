"""
Django management command to set up default notification services.
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationService
from django.utils import timezone


class Command(BaseCommand):
    help = 'Set up default notification services'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default notification services...')
        
        # Email Service
        email_service, created = NotificationService.objects.get_or_create(
            name='Email Service',
            defaults={
                'service_type': NotificationService.ServiceType.EMAIL,
                'status': NotificationService.ServiceStatus.STOPPED,
                'description': 'Primary email notification service using SMTP',
                'version': '1.0.0',
                'endpoint_url': 'smtp://localhost:587',
                'health_check_url': '/api/health/email/',
                'max_concurrent_workers': 10,
                'queue_size_limit': 5000,
                'retry_attempts': 3,
                'retry_delay_seconds': 60,
                'is_enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Created Email Service'))
        else:
            self.stdout.write('Email Service already exists')
        
        # SMS Service
        sms_service, created = NotificationService.objects.get_or_create(
            name='SMS Service',
            defaults={
                'service_type': NotificationService.ServiceType.SMS,
                'status': NotificationService.ServiceStatus.STOPPED,
                'description': 'SMS notification service using Twilio API',
                'version': '1.0.0',
                'endpoint_url': 'https://api.twilio.com/2010-04-01/Accounts/',
                'health_check_url': '/api/health/sms/',
                'max_concurrent_workers': 5,
                'queue_size_limit': 2000,
                'retry_attempts': 3,
                'retry_delay_seconds': 30,
                'is_enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Created SMS Service'))
        else:
            self.stdout.write('SMS Service already exists')
        
        # Push Notification Service
        push_service, created = NotificationService.objects.get_or_create(
            name='Push Notification Service',
            defaults={
                'service_type': NotificationService.ServiceType.PUSH,
                'status': NotificationService.ServiceStatus.STOPPED,
                'description': 'Push notification service for mobile apps',
                'version': '1.0.0',
                'endpoint_url': 'https://fcm.googleapis.com/fcm/send',
                'health_check_url': '/api/health/push/',
                'max_concurrent_workers': 8,
                'queue_size_limit': 3000,
                'retry_attempts': 3,
                'retry_delay_seconds': 45,
                'is_enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Created Push Notification Service'))
        else:
            self.stdout.write('Push Notification Service already exists')
        
        # Webhook Service
        webhook_service, created = NotificationService.objects.get_or_create(
            name='Webhook Service',
            defaults={
                'service_type': NotificationService.ServiceType.WEBHOOK,
                'status': NotificationService.ServiceStatus.STOPPED,
                'description': 'Webhook service for external integrations',
                'version': '1.0.0',
                'endpoint_url': 'https://hooks.slack.com/services/',
                'health_check_url': '/api/health/webhook/',
                'max_concurrent_workers': 6,
                'queue_size_limit': 1000,
                'retry_attempts': 2,
                'retry_delay_seconds': 90,
                'is_enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Created Webhook Service'))
        else:
            self.stdout.write('Webhook Service already exists')
        
        # Notification Queue Service
        queue_service, created = NotificationService.objects.get_or_create(
            name='Notification Queue',
            defaults={
                'service_type': NotificationService.ServiceType.QUEUE,
                'status': NotificationService.ServiceStatus.RUNNING,
                'description': 'Background queue processor for notifications',
                'version': '1.0.0',
                'endpoint_url': 'redis://localhost:6379/0',
                'health_check_url': '/api/health/queue/',
                'max_concurrent_workers': 15,
                'queue_size_limit': 10000,
                'retry_attempts': 5,
                'retry_delay_seconds': 30,
                'is_enabled': True,
                'started_at': timezone.now(),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Created Notification Queue'))
        else:
            self.stdout.write('Notification Queue already exists')
        
        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] All notification services have been set up successfully!'))
        self.stdout.write('\nServices can be managed from the notification dashboard.')
