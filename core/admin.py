from django.contrib import admin
from django.utils.html import format_html
from .models import SystemSettings, AuditLog, Region, Commodity


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for System Settings.
    """
    
    list_display = [
        'site_name', 'maintenance_mode', 'updated_at'
    ]
    
    list_filter = [
        'maintenance_mode', 'application_auto_approve', 'document_verification_required',
        'password_require_special', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'site_name', 'site_description', 'email_from_name', 'email_from_address'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('General Settings', {
            'fields': (
                'site_name', 'site_description', 'maintenance_mode', 'maintenance_message'
            ),
            'classes': ('wide',)
        }),
        ('Email Settings', {
            'fields': (
                'email_from_name', 'email_from_address', 'email_reply_to', 'admin_notification_email'
            ),
            'classes': ('wide',)
        }),
        ('SMS Settings', {
            'fields': (
                'sms_from_name', 'sms_provider', 'sms_api_key', 'sms_api_secret', 'sms_sender_id'
            ),
            'classes': ('wide',)
        }),
        ('Notification Settings', {
            'fields': (
                'notification_api_url', 'notification_timeout'
            ),
            'classes': ('wide',)
        }),
        ('Application Settings', {
            'fields': (
                'application_auto_approve', 'application_approval_days', 
                'document_verification_required'
            ),
            'classes': ('wide',)
        }),
        ('Security Settings', {
            'fields': (
                'password_min_length', 'password_require_special', 
                'session_timeout', 'max_login_attempts'
            ),
            'classes': ('wide',)
        }),
        ('File Upload Settings', {
            'fields': (
                'max_file_size', 'allowed_file_types'
            ),
            'classes': ('wide',)
        }),
        ('Audit Settings', {
            'fields': (
                'audit_log_retention_days', 'audit_log_enabled'
            ),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding new settings instances."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the settings instance."""
        return False
    
    def get_queryset(self, request):
        """Ensure only one settings instance exists."""
        return SystemSettings.objects.filter(pk=1)
    
    def maintenance_mode_status(self, obj):
        """Display maintenance mode status with color coding."""
        if obj.maintenance_mode:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠️ ACTIVE</span>'
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">✅ Inactive</span>'
        )
    maintenance_mode_status.short_description = 'Maintenance Mode'
    
    def site_info(self, obj):
        """Display site information."""
        return format_html(
            '<strong>{}</strong><br><small style="color: #6c757d;">{}</small>',
            obj.site_name,
            obj.site_description[:50] + '...' if len(obj.site_description) > 50 else obj.site_description
        )
    site_info.short_description = 'Site Information'
    
    def api_status(self, obj):
        """Display API status."""
        if obj.notification_api_url:
            return format_html(
                '<span style="color: #17a2b8;">🔗 {}</span>',
                obj.notification_api_url
            )
        return format_html('<span style="color: #6c757d;">Not configured</span>')
    api_status.short_description = 'Notification API'
    
    def security_summary(self, obj):
        """Display security settings summary."""
        return format_html(
            'Min Length: {} | Special Chars: {} | Session: {}min | Max Attempts: {}',
            obj.password_min_length,
            'Yes' if obj.password_require_special else 'No',
            obj.session_timeout,
            obj.max_login_attempts
        )
    security_summary.short_description = 'Security Summary'
    
    # Override the default list_display to include custom methods
    list_display = [
        'site_info', 'maintenance_mode_status', 'api_status', 'security_summary', 'updated_at'
    ]
    
    # Add custom actions
    actions = ['enable_maintenance_mode', 'disable_maintenance_mode', 'reset_to_defaults']
    
    def enable_maintenance_mode(self, request, queryset):
        """Enable maintenance mode for selected settings."""
        count = queryset.update(maintenance_mode=True)
        self.message_user(
            request,
            f"Maintenance mode enabled for {count} setting(s).",
            level='WARNING'
        )
    enable_maintenance_mode.short_description = "Enable Maintenance Mode"
    
    def disable_maintenance_mode(self, request, queryset):
        """Disable maintenance mode for selected settings."""
        count = queryset.update(maintenance_mode=False)
        self.message_user(
            request,
            f"Maintenance mode disabled for {count} setting(s).",
            level='SUCCESS'
        )
    disable_maintenance_mode.short_description = "Disable Maintenance Mode"
    
    def reset_to_defaults(self, request, queryset):
        """Reset settings to default values."""
        settings = queryset.first()
        if settings:
            # Reset to defaults
            settings.site_name = 'GCX Admin Portal'
            settings.site_description = 'Ghana Commodity Exchange Admin Portal'
            settings.maintenance_mode = False
            settings.maintenance_message = ''
            settings.email_from_name = 'GCX eServices'
            settings.email_from_address = 'noreply@gcx.com.gh'
            settings.email_reply_to = ''
            settings.admin_notification_email = 'admin@gcx.com.gh'
            settings.sms_from_name = 'GCX'
            settings.sms_provider = 'twilio'
            settings.sms_api_key = ''
            settings.sms_api_secret = ''
            settings.sms_sender_id = ''
            settings.notification_api_url = 'https://api.gcx.com.gh/notification-api/public'
            settings.notification_timeout = 30
            settings.application_auto_approve = False
            settings.application_approval_days = 7
            settings.document_verification_required = True
            settings.password_min_length = 8
            settings.password_require_special = True
            settings.session_timeout = 480
            settings.max_login_attempts = 5
            settings.max_file_size = 10
            settings.allowed_file_types = 'pdf,doc,docx,jpg,jpeg,png'
            settings.audit_log_retention_days = 365
            settings.audit_log_enabled = True
            settings.save()
            
            self.message_user(
                request,
                "Settings reset to default values successfully.",
                level='SUCCESS'
            )
    reset_to_defaults.short_description = "Reset to Default Values"


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """
    Admin interface for Regions.
    """
    
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Commodity)
class CommodityAdmin(admin.ModelAdmin):
    """
    Admin interface for Commodities.
    """
    
    list_display = ['name', 'unit_of_measure', 'is_processed_food', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_processed_food', 'unit_of_measure', 'created_at']
    search_fields = ['name', 'description', 'unit_of_measure']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'unit_of_measure', 'image', 'is_active', 'is_processed_food')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Audit Logs.
    """
    
    list_display = [
        'timestamp', 'user', 'action', 'severity', 'object_type', 'object_name', 'ip_address'
    ]
    
    list_filter = [
        'action', 'severity', 'timestamp', 'user', 'object_type'
    ]
    
    search_fields = [
        'description', 'user__username', 'object_name', 'object_type', 'ip_address', 'tags'
    ]
    
    ordering = ['-timestamp']
    readonly_fields = [
        'timestamp', 'user', 'session_key', 'ip_address', 'user_agent', 'action', 
        'severity', 'description', 'object_type', 'object_id', 'object_name',
        'request_path', 'request_method', 'request_data', 'response_status', 
        'response_message', 'metadata', 'tags', 'server_name', 'process_id'
    ]
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('timestamp', 'user', 'action', 'severity', 'description')
        }),
        ('Object Information', {
            'fields': ('object_type', 'object_id', 'object_name'),
            'classes': ('collapse',)
        }),
        ('Request Information', {
            'fields': ('request_path', 'request_method', 'request_data', 'ip_address', 'user_agent', 'session_key'),
            'classes': ('collapse',)
        }),
        ('Response Information', {
            'fields': ('response_status', 'response_message'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('metadata', 'tags', 'server_name', 'process_id'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding new audit log entries manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing audit log entries."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit log entries."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset for admin display."""
        return super().get_queryset(request).select_related('user')
    
    def action_display(self, obj):
        """Display action with color coding."""
        colors = {
            'LOGIN': '#28a745',
            'LOGOUT': '#6c757d',
            'CREATE': '#17a2b8',
            'UPDATE': '#ffc107',
            'DELETE': '#dc3545',
            'VIEW': '#007bff',
            'DOWNLOAD': '#6f42c1',
            'UPLOAD': '#20c997',
            'APPROVE': '#28a745',
            'REJECT': '#dc3545',
            'SEND_EMAIL': '#17a2b8',
            'SEND_SMS': '#fd7e14',
            'EXPORT': '#28a745',
            'IMPORT': '#ffc107',
            'SETTINGS_CHANGE': '#dc3545',
            'PASSWORD_CHANGE': '#6c757d',
            'PERMISSION_CHANGE': '#ffc107',
            'SYSTEM_ERROR': '#dc3545',
            'SECURITY_EVENT': '#dc3545',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = 'Action'
    
    def severity_display(self, obj):
        """Display severity with color coding."""
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545',
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_display.short_description = 'Severity'
    
    # Override list_display to use custom methods
    list_display = [
        'timestamp', 'user', 'action_display', 'severity_display', 'object_type', 'object_name', 'ip_address'
    ]