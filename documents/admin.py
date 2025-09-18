"""
Admin configuration for documents app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import DocumentRequirement, DocumentUpload, OutstandingDocumentRequest


@admin.register(DocumentRequirement)
class DocumentRequirementAdmin(admin.ModelAdmin):
    """Admin for DocumentRequirement model."""
    
    list_display = [
        'label', 'code', 'is_required', 'max_file_size_mb', 'is_active', 'created_at'
    ]
    list_filter = ['is_required', 'is_active', 'created_at']
    search_fields = ['label', 'code', 'description']
    ordering = ['label']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'label', 'description')
        }),
        ('Requirements', {
            'fields': ('is_required', 'condition_note')
        }),
        ('File Settings', {
            'fields': ('allowed_extensions', 'max_file_size_mb')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    """Admin for DocumentUpload model."""
    
    list_display = [
        'requirement', 'application', 'original_filename', 'file_size_mb', 
        'verified', 'verified_by', 'uploaded_at'
    ]
    list_filter = [
        'verified', 'requirement', 'uploaded_at', 'verified_at'
    ]
    search_fields = [
        'original_filename', 'application__business_name', 
        'application__tracking_code', 'verifier_note'
    ]
    ordering = ['-uploaded_at']
    readonly_fields = [
        'original_filename', 'file_size', 'mime_type', 'uploaded_at', 'updated_at'
    ]
    
    fieldsets = (
        ('File Information', {
            'fields': (
                'application', 'requirement', 'file', 'original_filename', 
                'file_size', 'mime_type'
            )
        }),
        ('Verification', {
            'fields': (
                'verified', 'verified_by', 'verified_at', 'verifier_note'
            )
        }),
        ('Audit Information', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb(self, obj):
        """Display file size in MB."""
        return f"{obj.file_size_mb} MB"
    file_size_mb.short_description = 'File Size (MB)'
    file_size_mb.admin_order_field = 'file_size'
    
    def get_queryset(self, request):
        """Filter uploads based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(application__is_deleted=False)
    
    actions = ['verify_documents', 'unverify_documents']
    
    def verify_documents(self, request, queryset):
        """Action to verify documents."""
        for upload in queryset:
            if not upload.verified:
                upload.verified = True
                upload.verified_by = request.user
                upload.verified_at = timezone.now()
                upload.save()
                
                admin.site.message_user(
                    request, 
                    f"Verified document: {upload.original_filename}"
                )
    verify_documents.short_description = "Verify Selected Documents"
    
    def unverify_documents(self, request, queryset):
        """Action to unverify documents."""
        for upload in queryset:
            if upload.verified:
                upload.verified = False
                upload.verified_by = None
                upload.verified_at = None
                upload.verifier_note = ''
                upload.save()
                
                admin.site.message_user(
                    request, 
                    f"Unverified document: {upload.original_filename}"
                )
    unverify_documents.short_description = "Unverify Selected Documents"


@admin.register(OutstandingDocumentRequest)
class OutstandingDocumentRequestAdmin(admin.ModelAdmin):
    """Admin for OutstandingDocumentRequest model."""
    
    list_display = [
        'application', 'requirements_count', 'requested_by', 'is_resolved', 'created_at'
    ]
    list_filter = ['is_resolved', 'created_at', 'requested_by']
    search_fields = [
        'application__business_name', 'application__tracking_code', 'message'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('application', 'requirements', 'message', 'requested_by')
        }),
        ('Status', {
            'fields': ('is_resolved', 'resolved_at')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['requirements']
    
    def requirements_count(self, obj):
        """Display count of required documents."""
        return obj.requirements.count()
    requirements_count.short_description = 'Requirements Count'
    
    def get_queryset(self, request):
        """Filter requests based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(application__is_deleted=False)