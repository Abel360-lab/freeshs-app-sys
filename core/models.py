from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Region(models.Model):
    """
    Ghana regions for supplier applications.
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'
    
    def __str__(self):
        return self.name


class Commodity(models.Model):
    """
    Commodities that can be supplied through GCX.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_processed_food = models.BooleanField(default=False, help_text="Is this a processed food commodity?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Commodity'
        verbose_name_plural = 'Commodities'
    
    def __str__(self):
        return self.name


class AuditLog(models.Model):
    """
    Audit log for tracking system actions and changes.
    """
    ACTION_CHOICES = [
        ('APPLICATION_CREATED', 'Application Created'),
        ('APPLICATION_UPDATED', 'Application Updated'),
        ('APPLICATION_APPROVED', 'Application Approved'),
        ('APPLICATION_REJECTED', 'Application Rejected'),
        ('DOCUMENT_UPLOADED', 'Document Uploaded'),
        ('DOCUMENT_VERIFIED', 'Document Verified'),
        ('PAYMENT_CONFIRMED', 'Payment Confirmed'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('REQUEST_DOCUMENTS', 'Request Documents'),
        ('USER_LOGIN', 'User Login'),
        ('USER_LOGOUT', 'User Logout'),
        ('SETTINGS_CHANGED', 'Settings Changed'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    description = models.TextField(
        default="System action",
        help_text="Description of the action"
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the model that was affected"
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of the affected object"
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional details about the action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SystemSettings(models.Model):
    """
    System-wide configuration settings for the GCX Admin Portal.
    """
    
    # General Settings
    site_name = models.CharField(
        max_length=200,
        default="GCX Admin Portal",
        help_text="Name of the admin portal"
    )
    site_description = models.TextField(
        blank=True,
        help_text="Description of the admin portal"
    )
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="Enable maintenance mode to restrict access"
    )
    maintenance_message = models.TextField(
        blank=True,
        help_text="Message to display during maintenance mode"
    )
    
    # Email Settings
    email_from_name = models.CharField(
        max_length=100,
        default="GCX eServices",
        help_text="Default sender name for emails"
    )
    email_from_address = models.EmailField(
        default="noreply@gcx.com.gh",
        help_text="Default sender email address"
    )
    email_reply_to = models.EmailField(
        blank=True,
        help_text="Reply-to email address"
    )
    admin_notification_email = models.EmailField(
        default="admin@gcx.com.gh",
        help_text="Email address to receive notifications for new applications"
    )
    
    # SMS Settings
    sms_from_name = models.CharField(
        max_length=100,
        default="GCX",
        help_text="Default sender name for SMS"
    )
    
    # Notification Settings
    notification_api_url = models.URLField(
        default="https://api.gcx.com.gh/notification-api/public",
        help_text="External notification API URL"
    )
    notification_timeout = models.PositiveIntegerField(
        default=30,
        help_text="Notification API timeout in seconds"
    )
    
    # Application Settings
    application_auto_approve = models.BooleanField(
        default=False,
        help_text="Automatically approve applications when all documents are verified"
    )
    application_approval_days = models.PositiveIntegerField(
        default=7,
        help_text="Days to wait before auto-approval"
    )
    document_verification_required = models.BooleanField(
        default=True,
        help_text="Require manual verification of uploaded documents"
    )
    
    # Security Settings
    password_min_length = models.PositiveIntegerField(
        default=8,
        help_text="Minimum password length"
    )
    password_require_special = models.BooleanField(
        default=True,
        help_text="Require special characters in passwords"
    )
    session_timeout = models.PositiveIntegerField(
        default=480,
        help_text="Session timeout in minutes"
    )
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        help_text="Maximum login attempts before lockout"
    )
    
    # File Upload Settings
    max_file_size = models.PositiveIntegerField(
        default=10,
        help_text="Maximum file size in MB"
    )
    allowed_file_types = models.TextField(
        default="pdf,doc,docx,jpg,jpeg,png",
        help_text="Comma-separated list of allowed file extensions"
    )
    
    # Audit Settings
    audit_log_retention_days = models.PositiveIntegerField(
        default=365,
        help_text="Number of days to retain audit logs"
    )
    log_level = models.CharField(
        max_length=20,
        choices=[
            ('DEBUG', 'Debug'),
            ('INFO', 'Info'),
            ('WARNING', 'Warning'),
            ('ERROR', 'Error'),
            ('CRITICAL', 'Critical'),
        ],
        default='INFO',
        help_text="System log level"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who last updated the settings"
    )
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
        db_table = 'core_system_settings'
    
    def __str__(self):
        return f"System Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_settings(cls):
        """Get the current system settings, creating default if none exist."""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'GCX Admin Portal',
                'site_description': 'Ghana Commodity Exchange Admin Portal',
                'email_from_name': 'GCX eServices',
                'email_from_address': 'noreply@gcx.com.gh',
                'admin_notification_email': 'admin@gcx.com.gh',
                'sms_from_name': 'GCX',
                'notification_api_url': 'https://api.gcx.com.gh/notification-api/public',
                'notification_timeout': 30,
                'application_auto_approve': False,
                'application_approval_days': 7,
                'document_verification_required': True,
                'password_min_length': 8,
                'password_require_special': True,
                'session_timeout': 480,
                'max_login_attempts': 5,
                'max_file_size': 10,
                'allowed_file_types': 'pdf,doc,docx,jpg,jpeg,png',
                'audit_log_retention_days': 365,
                'log_level': 'INFO',
            }
        )
        return settings
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one settings instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)