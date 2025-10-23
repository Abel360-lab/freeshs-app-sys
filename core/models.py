from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class Region(models.Model):
    """Region model for storing regional information."""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Regions"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Commodity(models.Model):
    """Commodity model for storing commodity information."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    unit_of_measure = models.CharField(max_length=50, default="kg")
    image = models.ImageField(upload_to='commodities/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_processed_food = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commodity"
        verbose_name_plural = "Commodities"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.unit_of_measure})"

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
    sms_provider = models.CharField(
        max_length=50,
        default="twilio",
        choices=[
            ('twilio', 'Twilio'),
            ('africas_talking', "Africa's Talking"),
            ('custom', 'Custom API'),
        ],
        help_text="SMS service provider"
    )
    sms_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMS API key or username"
    )
    sms_api_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMS API secret or password"
    )
    sms_sender_id = models.CharField(
        max_length=20,
        blank=True,
        help_text="SMS sender ID or phone number"
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
        help_text="Automatically approve applications without manual review"
    )
    application_approval_days = models.PositiveIntegerField(
        default=7,
        help_text="Number of days to wait before auto-approving applications"
    )
    document_verification_required = models.BooleanField(
        default=True,
        help_text="Require document verification before application approval"
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
        help_text="Maximum login attempts before account lockout"
    )
    
    # File Upload Settings
    max_file_size = models.PositiveIntegerField(
        default=10,
        help_text="Maximum file size in MB"
    )
    allowed_file_types = models.TextField(
        default="pdf,doc,docx,jpg,jpeg,png",
        help_text="Comma-separated list of allowed file types"
    )
    
    # Audit Settings
    audit_log_retention_days = models.PositiveIntegerField(
        default=365,
        help_text="Number of days to retain audit logs"
    )
    audit_log_enabled = models.BooleanField(
        default=True,
        help_text="Enable audit logging for system activities"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"System Settings ({self.site_name})"
    
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
                'sms_provider': 'twilio',
                'sms_api_key': '',
                'sms_api_secret': '',
                'sms_sender_id': '',
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
                'audit_log_enabled': True,
            }
        )
        return settings


class AuditLog(models.Model):
    """
    Audit log for tracking all system activities.
    """
    
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Create Record'),
        ('UPDATE', 'Update Record'),
        ('DELETE', 'Delete Record'),
        ('VIEW', 'View Record'),
        ('DOWNLOAD', 'Download File'),
        ('UPLOAD', 'Upload File'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('SEND_EMAIL', 'Send Email'),
        ('SEND_SMS', 'Send SMS'),
        ('EXPORT', 'Export Data'),
        ('IMPORT', 'Import Data'),
        ('SETTINGS_CHANGE', 'Settings Change'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('SYSTEM_ERROR', 'System Error'),
        ('SECURITY_EVENT', 'Security Event'),
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Basic Information
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Action Details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='LOW')
    description = models.TextField()
    
    # Object Information
    object_type = models.CharField(max_length=100, blank=True)  # e.g., 'Application', 'User', 'Contract'
    object_id = models.CharField(max_length=100, blank=True)    # ID of the affected object
    object_name = models.CharField(max_length=200, blank=True)   # Human-readable name
    
    # Request Information
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_data = models.JSONField(null=True, blank=True)      # Request payload
    
    # Response Information
    response_status = models.IntegerField(null=True, blank=True)
    response_message = models.TextField(blank=True)
    
    # Additional Context
    metadata = models.JSONField(null=True, blank=True)          # Additional context data
    tags = models.CharField(max_length=500, blank=True)       # Comma-separated tags
    
    # System Information
    server_name = models.CharField(max_length=100, blank=True)
    process_id = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['severity', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.get_action_display()} - {self.description[:50]}"
    
    @classmethod
    def log_action(cls, action, description, user=None, object_type=None, object_id=None, 
                   object_name=None, request=None, severity='LOW', metadata=None, tags=None):
        """
        Create an audit log entry.
        """
        if not cls._should_log():
            return None
            
        # Extract request information
        ip_address = None
        user_agent = ''
        session_key = ''
        request_path = ''
        request_method = ''
        request_data = None
        
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            session_key = request.session.session_key or ''
            request_path = request.path
            request_method = request.method
            
            # Capture request data (excluding sensitive fields)
            if request.method in ['POST', 'PUT', 'PATCH']:
                request_data = cls._sanitize_request_data(request)
        
        return cls.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            severity=severity,
            description=description,
            object_type=object_type,
            object_id=str(object_id) if object_id else '',
            object_name=object_name or '',
            request_path=request_path,
            request_method=request_method,
            request_data=request_data,
            metadata=metadata,
            tags=','.join(tags) if tags else '',
        )
    
    @classmethod
    def _should_log(cls):
        """Check if audit logging is enabled."""
        try:
            settings = SystemSettings.get_settings()
            return settings.audit_log_enabled
        except:
            return True  # Default to enabled if settings not available
    
    @classmethod
    def _get_client_ip(cls, request):
        """Get the client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def _sanitize_request_data(cls, request):
        """Sanitize request data to remove sensitive information."""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
        
        if hasattr(request, 'POST'):
            data = dict(request.POST)
        elif hasattr(request, 'data'):
            data = dict(request.data)
        else:
            return None
        
        # Remove sensitive fields
        for field in sensitive_fields:
            if field in data:
                data[field] = '[REDACTED]'
        
        return data
    
    def get_metadata_display(self):
        """Get formatted metadata for display."""
        if not self.metadata:
            return ''
        return json.dumps(self.metadata, indent=2)
    
    def get_tags_list(self):
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]