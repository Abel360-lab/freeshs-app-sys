"""
Notification models for GCX Supplier Application Portal.
"""

from django.db import models
from django.utils import timezone
from django.conf import settings


class NotificationTemplate(models.Model):
    """
    Email notification templates.
    """
    
    class NotificationType(models.TextChoices):
        APPLICATION_SUBMITTED = 'APPLICATION_SUBMITTED', 'Application Submitted'
        DOCUMENTS_REQUESTED = 'DOCUMENTS_REQUESTED', 'Documents Requested'
        APPLICATION_APPROVED = 'APPLICATION_APPROVED', 'Application Approved'
        APPLICATION_REJECTED = 'APPLICATION_REJECTED', 'Application Rejected'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        ACCOUNT_CREATED = 'ACCOUNT_CREATED', 'Account Created'
        ADMIN_NOTIFICATION = 'ADMIN_NOTIFICATION', 'Admin Notification'
        CONTRACT_AWARDED = 'CONTRACT_AWARDED', 'Contract Awarded'
        DELIVERY_SUBMITTED = 'DELIVERY_SUBMITTED', 'Delivery Submitted'
        DELIVERY_VERIFIED = 'DELIVERY_VERIFIED', 'Delivery Verified'
        DELIVERY_REJECTED = 'DELIVERY_REJECTED', 'Delivery Rejected'
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Template name"
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        unique=True,
        help_text="Type of notification"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Email subject template"
    )
    body_html = models.TextField(
        help_text="HTML email body template"
    )
    body_text = models.TextField(
        help_text="Plain text email body template"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_template'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"


class NotificationLog(models.Model):
    """
    Log of sent notifications with comprehensive tracking.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAUSED = 'PAUSED', 'Paused'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        DELIVERED = 'DELIVERED', 'Delivered'
        BOUNCED = 'BOUNCED', 'Bounced'
        OPENED = 'OPENED', 'Opened'
        CLICKED = 'CLICKED', 'Clicked'
    
    class Channel(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        PUSH = 'PUSH', 'Push Notification'
        IN_APP = 'IN_APP', 'In-App Notification'
    
    # Template and Content
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="Template used for this notification"
    )
    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
        default=Channel.EMAIL,
        help_text="Notification channel used"
    )
    
    # Recipient Information
    recipient_email = models.EmailField(
        help_text="Email address of the recipient"
    )
    recipient_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the recipient"
    )
    recipient_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number of the recipient (for SMS)"
    )
    
    # Content
    subject = models.CharField(
        max_length=200,
        help_text="Actual subject sent"
    )
    body_html = models.TextField(
        blank=True,
        help_text="Actual HTML body sent"
    )
    body_text = models.TextField(
        blank=True,
        help_text="Actual text body sent"
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Status of the notification"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if sending failed"
    )
    
    # Timestamps
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was sent"
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was delivered"
    )
    opened_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was opened"
    )
    clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When a link in the notification was clicked"
    )
    
    # Tracking Data
    tracking_id = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        help_text="Unique tracking ID for this notification"
    )
    external_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External service ID (e.g., SendGrid message ID)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the recipient"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent of the recipient"
    )
    
    # Context and Metadata
    context_data = models.JSONField(
        default=dict,
        help_text="Context data used to render the template"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the notification"
    )
    
    # Related Objects
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
        help_text="Related application (if applicable)"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
        help_text="Related user (if applicable)"
    )
    
    # Retry Information
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to retry sending (if failed)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_log'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['channel']),
            models.Index(fields=['recipient_email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['tracking_id']),
            models.Index(fields=['application']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.template.name} to {self.recipient_email} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to generate tracking ID if not present."""
        if not self.tracking_id:
            import uuid
            self.tracking_id = uuid.uuid4()
        super().save(*args, **kwargs)
    
    def mark_sent(self, external_id=None):
        """Mark notification as sent."""
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save()
    
    def mark_delivered(self):
        """Mark notification as delivered."""
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_opened(self, ip_address=None, user_agent=None):
        """Mark notification as opened."""
        self.status = self.Status.OPENED
        self.opened_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save()
    
    def mark_clicked(self, ip_address=None, user_agent=None):
        """Mark notification as clicked."""
        self.status = self.Status.CLICKED
        self.clicked_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save()
    
    def mark_failed(self, error_message):
        """Mark notification as failed."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.save()
    
    def mark_bounced(self, error_message=None):
        """Mark notification as bounced."""
        self.status = self.Status.BOUNCED
        if error_message:
            self.error_message = error_message
        self.save()
    
    def can_retry(self):
        """Check if notification can be retried."""
        return (
            self.status == self.Status.FAILED and 
            self.retry_count < self.max_retries and
            (not self.next_retry_at or timezone.now() >= self.next_retry_at)
        )
    
    def schedule_retry(self, delay_minutes=30):
        """Schedule a retry for failed notification."""
        if self.can_retry():
            self.retry_count += 1
            self.next_retry_at = timezone.now() + timezone.timedelta(minutes=delay_minutes)
            self.status = self.Status.PENDING
            self.save()
            return True
        return False
    
    def get_tracking_url(self):
        """Get tracking URL for this notification."""
        if self.tracking_id:
            from django.urls import reverse
            return reverse('notifications:track', kwargs={'tracking_id': self.tracking_id})
        return None
    
    def get_open_tracking_url(self):
        """Get open tracking URL for this notification."""
        if self.tracking_id:
            from django.urls import reverse
            return reverse('notifications:track-open', kwargs={'tracking_id': self.tracking_id})
        return None
    
    def get_click_tracking_url(self, link_url):
        """Get click tracking URL for a specific link."""
        if self.tracking_id:
            from django.urls import reverse
            from urllib.parse import quote
            return reverse('notifications:track-click', kwargs={
                'tracking_id': self.tracking_id,
                'link_url': quote(link_url, safe='')
            })
        return link_url
    
    @property
    def is_successful(self):
        """Check if notification was successful."""
        return self.status in [self.Status.SENT, self.Status.DELIVERED, self.Status.OPENED, self.Status.CLICKED]
    
    @property
    def is_failed(self):
        """Check if notification failed."""
        return self.status in [self.Status.FAILED, self.Status.BOUNCED]
    
    @property
    def delivery_time(self):
        """Get delivery time in seconds."""
        if self.sent_at and self.delivered_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None


class SMSNotification(models.Model):
    """
    SMS notification log with enhanced tracking.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        DELIVERED = 'DELIVERED', 'Delivered'
        BOUNCED = 'BOUNCED', 'Bounced'
    
    # Recipient Information
    recipient_phone = models.CharField(
        max_length=20,
        help_text="Phone number of the recipient"
    )
    recipient_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the recipient"
    )
    
    # Content
    message = models.TextField(
        help_text="SMS message content"
    )
    template_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Template name used for this SMS"
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Status of the SMS"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if sending failed"
    )
    
    # Timestamps
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the SMS was sent"
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the SMS was delivered"
    )
    
    # Tracking Data
    external_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External service ID (e.g., Twilio message ID)"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost of sending the SMS"
    )
    
    # Related Objects
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_notifications',
        help_text="Related application (if applicable)"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_notifications',
        help_text="Related user (if applicable)"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the SMS"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_sms_notification'
        verbose_name = 'SMS Notification'
        verbose_name_plural = 'SMS Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['recipient_phone']),
            models.Index(fields=['created_at']),
            models.Index(fields=['application']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"SMS to {self.recipient_phone} - {self.get_status_display()}"
    
    def mark_sent(self, external_id=None, cost=None):
        """Mark SMS as sent."""
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        if cost is not None:
            self.cost = cost
        self.save()
    
    def mark_delivered(self):
        """Mark SMS as delivered."""
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark SMS as failed."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.save()
    
    def mark_bounced(self, error_message=None):
        """Mark SMS as bounced."""
        self.status = self.Status.BOUNCED
        if error_message:
            self.error_message = error_message
        self.save()
    
    @property
    def is_successful(self):
        """Check if SMS was successful."""
        return self.status in [self.Status.SENT, self.Status.DELIVERED]
    
    @property
    def is_failed(self):
        """Check if SMS failed."""
        return self.status in [self.Status.FAILED, self.Status.BOUNCED]
    
    @property
    def delivery_time(self):
        """Get delivery time in seconds."""
        if self.sent_at and self.delivered_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None


class NotificationAnalytics(models.Model):
    """
    Analytics and statistics for notifications.
    """
    
    date = models.DateField(
        help_text="Date for this analytics record"
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationLog.Channel.choices,
        help_text="Notification channel"
    )
    template_name = models.CharField(
        max_length=100,
        help_text="Template name"
    )
    
    # Counts
    total_sent = models.PositiveIntegerField(
        default=0,
        help_text="Total notifications sent"
    )
    total_delivered = models.PositiveIntegerField(
        default=0,
        help_text="Total notifications delivered"
    )
    total_opened = models.PositiveIntegerField(
        default=0,
        help_text="Total notifications opened"
    )
    total_clicked = models.PositiveIntegerField(
        default=0,
        help_text="Total notifications clicked"
    )
    total_failed = models.PositiveIntegerField(
        default=0,
        help_text="Total notifications failed"
    )
    total_bounced = models.PositiveIntegerField(
        default=0,
        help_text="Total notifications bounced"
    )
    
    # Rates (calculated fields)
    delivery_rate = models.FloatField(
        default=0.0,
        help_text="Delivery rate (delivered/sent)"
    )
    open_rate = models.FloatField(
        default=0.0,
        help_text="Open rate (opened/delivered)"
    )
    click_rate = models.FloatField(
        default=0.0,
        help_text="Click rate (clicked/opened)"
    )
    failure_rate = models.FloatField(
        default=0.0,
        help_text="Failure rate (failed/sent)"
    )
    
    # Costs
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Total cost for this period"
    )
    average_cost_per_notification = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.0,
        help_text="Average cost per notification"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_analytics'
        verbose_name = 'Notification Analytics'
        verbose_name_plural = 'Notification Analytics'
        ordering = ['-date', 'channel']
        unique_together = ['date', 'channel', 'template_name']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['channel']),
            models.Index(fields=['template_name']),
        ]
    
    def __str__(self):
        return f"{self.template_name} ({self.channel}) - {self.date}"
    
    def calculate_rates(self):
        """Calculate all rates based on counts."""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.failure_rate = ((self.total_failed + self.total_bounced) / self.total_sent) * 100
        
        if self.total_delivered > 0:
            self.open_rate = (self.total_opened / self.total_delivered) * 100
        
        if self.total_opened > 0:
            self.click_rate = (self.total_clicked / self.total_opened) * 100
        
        if self.total_sent > 0:
            self.average_cost_per_notification = self.total_cost / self.total_sent
        
        self.save()
    
    @classmethod
    def generate_daily_analytics(cls, date=None):
        """Generate analytics for a specific date."""
        if date is None:
            date = timezone.now().date()
        
        # Get all notifications for the date
        notifications = NotificationLog.objects.filter(
            created_at__date=date
        ).values('channel', 'template__name').annotate(
            total_sent=models.Count('id'),
            total_delivered=models.Count('id', filter=models.Q(status__in=['DELIVERED', 'OPENED', 'CLICKED'])),
            total_opened=models.Count('id', filter=models.Q(status__in=['OPENED', 'CLICKED'])),
            total_clicked=models.Count('id', filter=models.Q(status='CLICKED')),
            total_failed=models.Count('id', filter=models.Q(status='FAILED')),
            total_bounced=models.Count('id', filter=models.Q(status='BOUNCED')),
        )
        
        for notification in notifications:
            analytics, created = cls.objects.get_or_create(
                date=date,
                channel=notification['channel'],
                template_name=notification['template__name'],
                defaults={
                    'total_sent': notification['total_sent'],
                    'total_delivered': notification['total_delivered'],
                    'total_opened': notification['total_opened'],
                    'total_clicked': notification['total_clicked'],
                    'total_failed': notification['total_failed'],
                    'total_bounced': notification['total_bounced'],
                }
            )
            
            if not created:
                analytics.total_sent = notification['total_sent']
                analytics.total_delivered = notification['total_delivered']
                analytics.total_opened = notification['total_opened']
                analytics.total_clicked = notification['total_clicked']
                analytics.total_failed = notification['total_failed']
                analytics.total_bounced = notification['total_bounced']
            
            analytics.calculate_rates()


class NotificationService(models.Model):
    """
    Background notification services management.
    """
    
    class ServiceType(models.TextChoices):
        EMAIL = 'EMAIL', 'Email Service'
        SMS = 'SMS', 'SMS Service'
        PUSH = 'PUSH', 'Push Notification Service'
        WEBHOOK = 'WEBHOOK', 'Webhook Service'
        QUEUE = 'QUEUE', 'Notification Queue'
    
    class ServiceStatus(models.TextChoices):
        RUNNING = 'RUNNING', 'Running'
        STOPPED = 'STOPPED', 'Stopped'
        PAUSED = 'PAUSED', 'Paused'
        ERROR = 'ERROR', 'Error'
        STARTING = 'STARTING', 'Starting'
        STOPPING = 'STOPPING', 'Stopping'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Service name"
    )
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        help_text="Type of service"
    )
    status = models.CharField(
        max_length=20,
        choices=ServiceStatus.choices,
        default=ServiceStatus.STOPPED,
        help_text="Current service status"
    )
    
    # Configuration
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this service is enabled"
    )
    max_concurrent_workers = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of concurrent workers"
    )
    queue_size_limit = models.PositiveIntegerField(
        default=1000,
        help_text="Maximum queue size"
    )
    retry_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Number of retry attempts"
    )
    retry_delay_seconds = models.PositiveIntegerField(
        default=60,
        help_text="Delay between retries in seconds"
    )
    
    # Service Information
    description = models.TextField(
        blank=True,
        help_text="Service description"
    )
    version = models.CharField(
        max_length=20,
        default="1.0.0",
        help_text="Service version"
    )
    endpoint_url = models.URLField(
        blank=True,
        help_text="Service endpoint URL"
    )
    health_check_url = models.URLField(
        blank=True,
        help_text="Health check endpoint URL"
    )
    
    # Monitoring
    last_health_check = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last health check timestamp"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message"
    )
    error_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of errors encountered"
    )
    processed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications processed"
    )
    failed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications failed"
    )
    
    # Performance Metrics
    average_processing_time = models.FloatField(
        default=0.0,
        help_text="Average processing time in seconds"
    )
    throughput_per_minute = models.FloatField(
        default=0.0,
        help_text="Throughput per minute"
    )
    cpu_usage_percent = models.FloatField(
        default=0.0,
        help_text="CPU usage percentage"
    )
    memory_usage_mb = models.FloatField(
        default=0.0,
        help_text="Memory usage in MB"
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the service was started"
    )
    stopped_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the service was stopped"
    )
    last_restart = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last restart timestamp"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_service'
        verbose_name = 'Notification Service'
        verbose_name_plural = 'Notification Services'
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['service_type']),
            models.Index(fields=['is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()}) - {self.get_status_display()}"
    
    def start_service(self):
        """Start the service."""
        if self.status in [self.ServiceStatus.STOPPED, self.ServiceStatus.ERROR]:
            self.status = self.ServiceStatus.STARTING
            self.started_at = timezone.now()
            self.last_error = ""
            self.save()
            return True
        return False
    
    def stop_service(self):
        """Stop the service."""
        if self.status in [self.ServiceStatus.RUNNING, self.ServiceStatus.PAUSED]:
            self.status = self.ServiceStatus.STOPPING
            self.stopped_at = timezone.now()
            self.save()
            return True
        return False
    
    def pause_service(self):
        """Pause the service."""
        if self.status == self.ServiceStatus.RUNNING:
            self.status = self.ServiceStatus.PAUSED
            self.save()
            return True
        return False
    
    def resume_service(self):
        """Resume the service."""
        if self.status == self.ServiceStatus.PAUSED:
            self.status = self.ServiceStatus.RUNNING
            self.save()
            return True
        return False
    
    def restart_service(self):
        """Restart the service."""
        if self.status in [self.ServiceStatus.RUNNING, self.ServiceStatus.PAUSED, self.ServiceStatus.ERROR]:
            self.status = self.ServiceStatus.STARTING
            self.last_restart = timezone.now()
            self.last_error = ""
            self.error_count = 0
            self.save()
            return True
        return False
    
    def update_health(self, is_healthy=True, error_message=None):
        """Update service health status."""
        self.last_health_check = timezone.now()
        
        if not is_healthy:
            self.status = self.ServiceStatus.ERROR
            self.error_count += 1
            if error_message:
                self.last_error = error_message
        elif self.status == self.ServiceStatus.ERROR:
            self.status = self.ServiceStatus.RUNNING
        
        self.save()
    
    def update_metrics(self, processing_time=None, success=True):
        """Update service performance metrics."""
        if success:
            self.processed_count += 1
        else:
            self.failed_count += 1
        
        if processing_time is not None:
            # Update average processing time (exponential moving average)
            alpha = 0.1  # Smoothing factor
            if self.average_processing_time == 0:
                self.average_processing_time = processing_time
            else:
                self.average_processing_time = (alpha * processing_time) + ((1 - alpha) * self.average_processing_time)
        
        self.save()
    
    @property
    def is_healthy(self):
        """Check if service is healthy."""
        if not self.last_health_check:
            return False
        
        # Consider unhealthy if no health check in last 5 minutes
        time_threshold = timezone.now() - timedelta(minutes=5)
        return self.last_health_check > time_threshold and self.status != self.ServiceStatus.ERROR
    
    @property
    def uptime(self):
        """Get service uptime in seconds."""
        if not self.started_at:
            return 0
        
        end_time = self.stopped_at or timezone.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def success_rate(self):
        """Get service success rate percentage."""
        total = self.processed_count + self.failed_count
        if total == 0:
            return 0
        return (self.processed_count / total) * 100


class BulkNotification(models.Model):
    """
    Bulk notification campaigns management.
    """
    
    class CampaignStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        RUNNING = 'RUNNING', 'Running'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FAILED = 'FAILED', 'Failed'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    # Campaign Information
    name = models.CharField(
        max_length=200,
        help_text="Campaign name"
    )
    description = models.TextField(
        blank=True,
        help_text="Campaign description"
    )
    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
        help_text="Campaign status"
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        help_text="Campaign priority"
    )
    
    # Template and Content
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        help_text="Notification template to use"
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationLog.Channel.choices,
        help_text="Notification channel"
    )
    
    # Recipients
    recipient_emails = models.JSONField(
        default=list,
        help_text="List of recipient email addresses"
    )
    recipient_phones = models.JSONField(
        default=list,
        help_text="List of recipient phone numbers"
    )
    recipient_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        help_text="Users to send notifications to"
    )
    recipient_applications = models.ManyToManyField(
        'applications.SupplierApplication',
        blank=True,
        help_text="Applications to send notifications to"
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to start the campaign"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the campaign was started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the campaign was completed"
    )
    
    # Progress Tracking
    total_recipients = models.PositiveIntegerField(
        default=0,
        help_text="Total number of recipients"
    )
    processed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications processed"
    )
    sent_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications sent successfully"
    )
    failed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications failed"
    )
    delivered_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications delivered"
    )
    opened_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of notifications opened"
    )
    
    # Settings
    batch_size = models.PositiveIntegerField(
        default=100,
        help_text="Number of notifications to send per batch"
    )
    delay_between_batches = models.PositiveIntegerField(
        default=5,
        help_text="Delay between batches in seconds"
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retry attempts per notification"
    )
    
    # Context and Personalization
    context_data = models.JSONField(
        default=dict,
        help_text="Global context data for all notifications"
    )
    personalize_by_recipient = models.BooleanField(
        default=False,
        help_text="Whether to personalize content by recipient"
    )
    
    # Results and Analytics
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Total cost of the campaign"
    )
    average_delivery_time = models.FloatField(
        default=0.0,
        help_text="Average delivery time in seconds"
    )
    click_through_rate = models.FloatField(
        default=0.0,
        help_text="Click-through rate percentage"
    )
    open_rate = models.FloatField(
        default=0.0,
        help_text="Open rate percentage"
    )
    
    # Error Handling
    last_error = models.TextField(
        blank=True,
        help_text="Last error message"
    )
    error_log = models.JSONField(
        default=list,
        help_text="List of error messages encountered"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_bulk_notifications',
        help_text="User who created this campaign"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_bulk_notification'
        verbose_name = 'Bulk Notification Campaign'
        verbose_name_plural = 'Bulk Notification Campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    def start_campaign(self):
        """Start the bulk notification campaign."""
        if self.status == self.CampaignStatus.SCHEDULED:
            self.status = self.CampaignStatus.RUNNING
            self.started_at = timezone.now()
            self.save()
            return True
        return False
    
    def pause_campaign(self):
        """Pause the bulk notification campaign."""
        if self.status == self.CampaignStatus.RUNNING:
            self.status = self.CampaignStatus.PAUSED
            self.save()
            return True
        return False
    
    def resume_campaign(self):
        """Resume the bulk notification campaign."""
        if self.status == self.CampaignStatus.PAUSED:
            self.status = self.CampaignStatus.RUNNING
            self.save()
            return True
        return False
    
    def cancel_campaign(self):
        """Cancel the bulk notification campaign."""
        if self.status in [self.CampaignStatus.RUNNING, self.CampaignStatus.PAUSED, self.CampaignStatus.SCHEDULED]:
            self.status = self.CampaignStatus.CANCELLED
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    def complete_campaign(self):
        """Mark campaign as completed."""
        self.status = self.CampaignStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()
        return True
    
    def calculate_recipients(self):
        """Calculate total number of recipients."""
        total = len(self.recipient_emails) + len(self.recipient_phones)
        total += self.recipient_users.count()
        total += self.recipient_applications.count()
        self.total_recipients = total
        self.save()
        return total
    
    def update_progress(self, sent=0, failed=0, delivered=0, opened=0):
        """Update campaign progress."""
        self.sent_count += sent
        self.failed_count += failed
        self.delivered_count += delivered
        self.opened_count += opened
        self.processed_count = self.sent_count + self.failed_count
        
        # Calculate rates
        if self.sent_count > 0:
            self.open_rate = (self.opened_count / self.sent_count) * 100
        
        self.save()
    
    def get_progress_percentage(self):
        """Get campaign progress percentage."""
        if self.total_recipients == 0:
            return 0
        return (self.processed_count / self.total_recipients) * 100
    
    def get_estimated_completion(self):
        """Get estimated completion time."""
        if self.processed_count == 0 or not self.started_at:
            return None
        
        elapsed = timezone.now() - self.started_at
        rate = self.processed_count / elapsed.total_seconds()
        remaining = self.total_recipients - self.processed_count
        
        if rate > 0:
            estimated_seconds = remaining / rate
            return timezone.now() + timedelta(seconds=estimated_seconds)
        return None
    
    @property
    def is_active(self):
        """Check if campaign is active."""
        return self.status in [self.CampaignStatus.RUNNING, self.CampaignStatus.PAUSED]
    
    @property
    def is_completed(self):
        """Check if campaign is completed."""
        return self.status in [self.CampaignStatus.COMPLETED, self.CampaignStatus.CANCELLED, self.CampaignStatus.FAILED]
    
    @property
    def success_rate(self):
        """Get campaign success rate."""
        if self.processed_count == 0:
            return 0
        return (self.sent_count / self.processed_count) * 100


class NotificationQueue(models.Model):
    """
    Notification queue for managing pending notifications.
    """
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    # Queue Item Information
    notification_log = models.ForeignKey(
        NotificationLog,
        on_delete=models.CASCADE,
        help_text="Related notification log"
    )
    bulk_campaign = models.ForeignKey(
        BulkNotification,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Related bulk campaign"
    )
    
    # Queue Management
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        help_text="Queue priority"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Queue item status"
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        default=timezone.now,
        help_text="When to process this item"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this item was processed"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this item expires"
    )
    
    # Retry Information
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retry attempts"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to retry processing"
    )
    
    # Processing Information
    assigned_worker = models.CharField(
        max_length=100,
        blank=True,
        help_text="Worker assigned to process this item"
    )
    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When processing started"
    )
    processing_duration = models.FloatField(
        default=0.0,
        help_text="Processing duration in seconds"
    )
    
    # Error Information
    error_message = models.TextField(
        blank=True,
        help_text="Error message if processing failed"
    )
    error_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Error code"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_queue'
        verbose_name = 'Notification Queue Item'
        verbose_name_plural = 'Notification Queue Items'
        ordering = ['priority', 'scheduled_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['bulk_campaign']),
        ]
    
    def __str__(self):
        return f"Queue Item {self.id} - {self.get_priority_display()} - {self.get_status_display()}"
    
    def assign_to_worker(self, worker_id):
        """Assign this queue item to a worker."""
        self.assigned_worker = worker_id
        self.status = self.Status.PROCESSING
        self.processing_started_at = timezone.now()
        self.save()
    
    def mark_completed(self, duration=None):
        """Mark queue item as completed."""
        self.status = self.Status.COMPLETED
        self.processed_at = timezone.now()
        if duration is not None:
            self.processing_duration = duration
        elif self.processing_started_at:
            self.processing_duration = (self.processed_at - self.processing_started_at).total_seconds()
        self.save()
    
    def mark_failed(self, error_message, error_code=None):
        """Mark queue item as failed."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.processed_at = timezone.now()
        if self.processing_started_at:
            self.processing_duration = (self.processed_at - self.processing_started_at).total_seconds()
        self.save()
    
    def schedule_retry(self, delay_seconds=60):
        """Schedule a retry for this queue item."""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.next_retry_at = timezone.now() + timedelta(seconds=delay_seconds)
            self.status = self.Status.PENDING
            self.assigned_worker = ""
            self.processing_started_at = None
            self.save()
            return True
        return False
    
    def cancel(self):
        """Cancel this queue item."""
        self.status = self.Status.CANCELLED
        self.processed_at = timezone.now()
        self.save()
    
    @property
    def is_expired(self):
        """Check if queue item is expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def can_retry(self):
        """Check if queue item can be retried."""
        return (
            self.status == self.Status.FAILED and
            self.retry_count < self.max_retries and
            (not self.next_retry_at or timezone.now() >= self.next_retry_at)
        )
    
    @property
    def age(self):
        """Get queue item age in seconds."""
        return (timezone.now() - self.created_at).total_seconds()