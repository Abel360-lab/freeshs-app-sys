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