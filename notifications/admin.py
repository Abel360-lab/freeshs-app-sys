"""
Admin configuration for notifications app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import NotificationTemplate, NotificationLog, SMSNotification


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin for NotificationTemplate model."""
    
    list_display = [
        'name', 'notification_type', 'is_active', 'usage_count', 'created_at'
    ]
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    actions = ['test_template', 'activate_templates', 'deactivate_templates']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'notification_type', 'is_active', 'usage_count')
        }),
        ('Email Content', {
            'fields': ('subject', 'body_html', 'body_text')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_count(self, obj):
        """Show how many times this template has been used."""
        count = obj.logs.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: gray;">{}</span>',
            count
        )
    usage_count.short_description = 'Usage Count'
    
    def test_template(self, request, queryset):
        """Test selected templates."""
        from django.template import Template, Context
        
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
        
        for template in queryset:
            try:
                # Test subject
                subject_template = Template(template.subject)
                rendered_subject = subject_template.render(Context(context_data))
                
                # Test HTML body
                html_template = Template(template.body_html)
                rendered_html = html_template.render(Context(context_data))
                
                self.message_user(
                    request,
                    f"Template '{template.name}' rendered successfully. Subject: {rendered_subject[:50]}...",
                    level='SUCCESS'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error testing template '{template.name}': {str(e)}",
                    level='ERROR'
                )
    
    test_template.short_description = "Test selected templates"
    
    def activate_templates(self, request, queryset):
        """Activate selected templates."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Successfully activated {count} template(s).",
            level='SUCCESS'
        )
    
    activate_templates.short_description = "Activate selected templates"
    
    def deactivate_templates(self, request, queryset):
        """Deactivate selected templates."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully deactivated {count} template(s).",
            level='SUCCESS'
        )
    
    deactivate_templates.short_description = "Deactivate selected templates"


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin for NotificationLog model."""
    
    list_display = [
        'template', 'recipient_email', 'recipient_name', 'status', 'sent_at', 'created_at'
    ]
    list_filter = ['status', 'template__notification_type', 'sent_at', 'created_at']
    search_fields = [
        'recipient_email', 'recipient_name', 'subject', 'template__name'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'template', 'recipient_email', 'recipient_name', 'subject',
        'body_html', 'body_text', 'status', 'error_message', 'sent_at',
        'delivered_at', 'context_data', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Recipient Information', {
            'fields': ('recipient_email', 'recipient_name')
        }),
        ('Email Content', {
            'fields': ('template', 'subject', 'body_html', 'body_text')
        }),
        ('Status Information', {
            'fields': ('status', 'error_message', 'sent_at', 'delivered_at')
        }),
        ('Context Data', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding notification logs through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing notification logs through admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting notification logs through admin."""
        return False


@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    """Admin for SMSNotification model."""
    
    list_display = [
        'recipient_phone', 'message_preview', 'status', 'sent_at', 'created_at'
    ]
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['recipient_phone', 'message']
    ordering = ['-created_at']
    readonly_fields = [
        'recipient_phone', 'message', 'status', 'error_message', 
        'sent_at', 'delivered_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('SMS Information', {
            'fields': ('recipient_phone', 'message')
        }),
        ('Status Information', {
            'fields': ('status', 'error_message', 'sent_at', 'delivered_at')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """Display message preview."""
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message
    message_preview.short_description = 'Message Preview'
    
    def has_add_permission(self, request):
        """Disable adding SMS notifications through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing SMS notifications through admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting SMS notifications through admin."""
        return False