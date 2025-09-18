from django import forms
from .models import SystemSettings

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = '__all__'
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email_from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email_from_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_reply_to': forms.EmailInput(attrs={'class': 'form-control'}),
            'admin_notification_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'sms_from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notification_api_url': forms.URLInput(attrs={'class': 'form-control'}),
            'notification_timeout': forms.NumberInput(attrs={'class': 'form-control'}),
            'application_auto_approve': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'application_approval_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'document_verification_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'password_min_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'password_require_special': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'session_timeout': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_login_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_file_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'allowed_file_types': forms.TextInput(attrs={'class': 'form-control'}),
            'audit_log_retention_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'log_level': forms.Select(attrs={'class': 'form-select'}),
        }
