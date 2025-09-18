"""
Serializers for notifications app.
"""

from rest_framework import serializers
from .models import NotificationTemplate, NotificationLog, SMSNotification


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'subject', 'body_html',
            'body_text', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for NotificationLog model."""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_type = serializers.CharField(source='template.notification_type', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'template', 'template_name', 'template_type', 'recipient_email',
            'recipient_name', 'subject', 'status', 'error_message', 'sent_at',
            'delivered_at', 'context_data', 'created_at'
        ]
        read_only_fields = [
            'id', 'template', 'recipient_email', 'recipient_name', 'subject',
            'body_html', 'body_text', 'status', 'error_message', 'sent_at',
            'delivered_at', 'context_data', 'created_at'
        ]


class SMSNotificationSerializer(serializers.ModelSerializer):
    """Serializer for SMSNotification model."""
    
    class Meta:
        model = SMSNotification
        fields = [
            'id', 'recipient_phone', 'message', 'status', 'error_message',
            'sent_at', 'delivered_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'error_message', 'sent_at', 'delivered_at', 'created_at'
        ]


class NotificationSendSerializer(serializers.Serializer):
    """Serializer for sending notifications."""
    
    template_id = serializers.IntegerField()
    recipient_email = serializers.EmailField()
    recipient_name = serializers.CharField(max_length=200, required=False)
    context_data = serializers.JSONField(default=dict)
    
    def validate_template_id(self, value):
        """Validate template ID."""
        try:
            template = NotificationTemplate.objects.get(id=value, is_active=True)
            return value
        except NotificationTemplate.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive template ID")


class SMSSendSerializer(serializers.Serializer):
    """Serializer for sending SMS."""
    
    recipient_phone = serializers.CharField(max_length=20)
    message = serializers.CharField(max_length=160)
    
    def validate_recipient_phone(self, value):
        """Validate phone number format."""
        if not value.startswith('+233'):
            raise serializers.ValidationError("Phone number must be in Ghana format (+233XXXXXXXXX)")
        return value
