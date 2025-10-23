"""
Django management command to activate supplier accounts.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from applications.models import SupplierApplication

User = get_user_model()


class Command(BaseCommand):
    help = 'Activate supplier accounts for approved applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--application-id',
            type=int,
            help='ID of the application to activate account for',
        )
        parser.add_argument(
            '--tracking-code',
            type=str,
            help='Tracking code of the application to activate account for',
        )
        parser.add_argument(
            '--all-pending',
            action='store_true',
            help='Activate all pending supplier accounts',
        )

    def handle(self, *args, **options):
        if options['all_pending']:
            self.activate_all_pending()
        elif options['application_id']:
            self.activate_by_application_id(options['application_id'])
        elif options['tracking_code']:
            self.activate_by_tracking_code(options['tracking_code'])
        else:
            raise CommandError('Please specify --application-id, --tracking-code, or --all-pending')

    def activate_by_application_id(self, application_id):
        try:
            application = SupplierApplication.objects.get(id=application_id)
            self.activate_account(application)
        except SupplierApplication.DoesNotExist:
            raise CommandError(f'Application with ID {application_id} not found')

    def activate_by_tracking_code(self, tracking_code):
        try:
            application = SupplierApplication.objects.get(tracking_code=tracking_code)
            self.activate_account(application)
        except SupplierApplication.DoesNotExist:
            raise CommandError(f'Application with tracking code {tracking_code} not found')

    def activate_all_pending(self):
        """Activate all supplier accounts for approved applications."""
        applications = SupplierApplication.objects.filter(
            status=SupplierApplication.ApplicationStatus.APPROVED,
            user__isnull=False,
            user__is_active=False
        )
        
        activated_count = 0
        for application in applications:
            if self.activate_account(application):
                activated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully activated {activated_count} supplier accounts')
        )

    def activate_account(self, application):
        """Activate a single supplier account."""
        if not application.user:
            self.stdout.write(
                self.style.WARNING(f'No user account found for application {application.tracking_code}')
            )
            return False
        
        if application.user.is_active:
            self.stdout.write(
                self.style.WARNING(f'Account for application {application.tracking_code} is already active')
            )
            return False
        
        if application.status != SupplierApplication.ApplicationStatus.APPROVED:
            self.stdout.write(
                self.style.WARNING(f'Application {application.tracking_code} is not approved yet')
            )
            return False
        
        # Activate the user account
        application.user.is_active = True
        application.user.save()
        
        # Log the activation
        from core.models import AuditLog
        AuditLog.objects.create(
            user=None,  # System action
            action='ACCOUNT_ACTIVATED',
            model_name='User',
            object_id=str(application.user.id),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'user_email': application.user.email,
                'activated_by': 'admin_command'
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully activated account for {application.business_name} ({application.tracking_code})')
        )
        return True
