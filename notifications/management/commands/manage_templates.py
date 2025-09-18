"""
Django management command to manage notification templates.
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate
import json


class Command(BaseCommand):
    help = 'Manage notification templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all notification templates'
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create a new template interactively'
        )
        parser.add_argument(
            '--test',
            type=str,
            help='Test a template by name'
        )
        parser.add_argument(
            '--activate',
            type=str,
            help='Activate a template by name'
        )
        parser.add_argument(
            '--deactivate',
            type=str,
            help='Deactivate a template by name'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_templates()
        elif options['create']:
            self.create_template()
        elif options['test']:
            self.test_template(options['test'])
        elif options['activate']:
            self.activate_template(options['activate'])
        elif options['deactivate']:
            self.deactivate_template(options['deactivate'])
        else:
            self.stdout.write("Use --help to see available options")

    def list_templates(self):
        """List all notification templates."""
        templates = NotificationTemplate.objects.all()
        
        if not templates:
            self.stdout.write("No notification templates found.")
            return
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("NOTIFICATION TEMPLATES")
        self.stdout.write("="*80)
        
        for template in templates:
            status = "✓ Active" if template.is_active else "✗ Inactive"
            self.stdout.write(f"\nID: {template.id}")
            self.stdout.write(f"Name: {template.name}")
            self.stdout.write(f"Type: {template.notification_type}")
            self.stdout.write(f"Status: {status}")
            self.stdout.write(f"Subject: {template.subject[:50]}...")
            self.stdout.write(f"Created: {template.created_at}")
            self.stdout.write("-" * 40)

    def create_template(self):
        """Create a new template interactively."""
        self.stdout.write("\nCreating new notification template...")
        
        name = input("Template name: ")
        notification_type = input("Notification type (APPLICATION_SUBMITTED, DOCUMENTS_REQUESTED, etc.): ")
        subject = input("Email subject: ")
        
        print("\nEnter HTML body (end with 'END' on a new line):")
        html_lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            html_lines.append(line)
        body_html = '\n'.join(html_lines)
        
        print("\nEnter text body (end with 'END' on a new line):")
        text_lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            text_lines.append(line)
        body_text = '\n'.join(text_lines)
        
        template = NotificationTemplate.objects.create(
            name=name,
            notification_type=notification_type,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            is_active=True
        )
        
        self.stdout.write(f"\n✓ Template '{name}' created successfully with ID {template.id}")

    def test_template(self, template_name):
        """Test a template by rendering it with sample data."""
        try:
            template = NotificationTemplate.objects.get(name=template_name)
        except NotificationTemplate.DoesNotExist:
            self.stdout.write(f"✗ Template '{template_name}' not found")
            return
        
        # Sample context data
        context_data = {
            'application': {
                'tracking_code': 'GCX-2025-TEST123',
                'business_name': 'Test Business Ltd',
                'contact_person': 'John Doe',
                'email': 'test@example.com',
                'phone': '0241234567',
                'status': 'PENDING_REVIEW'
            },
            'missing_documents': [
                {'name': 'Business Registration Certificate'},
                {'name': 'Tax Clearance Certificate'}
            ]
        }
        
        from django.template import Template, Context
        
        self.stdout.write(f"\nTesting template: {template_name}")
        self.stdout.write("="*50)
        
        # Test subject
        subject_template = Template(template.subject)
        rendered_subject = subject_template.render(Context(context_data))
        self.stdout.write(f"\nSubject: {rendered_subject}")
        
        # Test HTML body
        html_template = Template(template.body_html)
        rendered_html = html_template.render(Context(context_data))
        self.stdout.write(f"\nHTML Body:\n{rendered_html}")
        
        # Test text body
        if template.body_text:
            text_template = Template(template.body_text)
            rendered_text = text_template.render(Context(context_data))
            self.stdout.write(f"\nText Body:\n{rendered_text}")

    def activate_template(self, template_name):
        """Activate a template."""
        try:
            template = NotificationTemplate.objects.get(name=template_name)
            template.is_active = True
            template.save()
            self.stdout.write(f"✓ Template '{template_name}' activated")
        except NotificationTemplate.DoesNotExist:
            self.stdout.write(f"✗ Template '{template_name}' not found")

    def deactivate_template(self, template_name):
        """Deactivate a template."""
        try:
            template = NotificationTemplate.objects.get(name=template_name)
            template.is_active = False
            template.save()
            self.stdout.write(f"✓ Template '{template_name}' deactivated")
        except NotificationTemplate.DoesNotExist:
            self.stdout.write(f"✗ Template '{template_name}' not found")
