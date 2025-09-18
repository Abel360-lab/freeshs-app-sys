"""
Admin configuration for reviews app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ReviewComment, ReviewChecklist, ReviewDecision


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    """Admin for ReviewComment model."""
    
    list_display = [
        'application', 'reviewer', 'comment_preview', 'is_internal', 'created_at'
    ]
    list_filter = ['is_internal', 'created_at', 'reviewer']
    search_fields = [
        'comment', 'application__business_name', 'reviewer__email'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('application', 'reviewer', 'comment', 'is_internal')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def comment_preview(self, obj):
        """Display comment preview."""
        if len(obj.comment) > 100:
            return f"{obj.comment[:100]}..."
        return obj.comment
    comment_preview.short_description = 'Comment Preview'
    
    def get_queryset(self, request):
        """Filter comments based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(application__is_deleted=False)


@admin.register(ReviewChecklist)
class ReviewChecklistAdmin(admin.ModelAdmin):
    """Admin for ReviewChecklist model."""
    
    list_display = [
        'application', 'reviewer', 'completion_percentage', 'is_complete', 'created_at'
    ]
    list_filter = ['is_complete', 'created_at', 'reviewer']
    search_fields = [
        'application__business_name', 'reviewer__email', 'overall_notes'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'completion_percentage', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Review Information', {
            'fields': ('application', 'reviewer')
        }),
        ('Document Checklist', {
            'fields': (
                'business_registration', 'vat_certificate', 'ppa_certificate',
                'tax_clearance', 'proof_of_office', 'id_directors',
                'gcx_registration', 'team_member_id', 'fda_certificate'
            )
        }),
        ('Application Checklist', {
            'fields': (
                'bank_account', 'contact_info', 'business_details',
                'team_members', 'next_of_kin', 'declaration'
            )
        }),
        ('Overall Assessment', {
            'fields': ('is_complete', 'completion_percentage', 'overall_notes')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def completion_percentage(self, obj):
        """Display completion percentage."""
        percentage = obj.get_completion_percentage()
        color = 'green' if percentage == 100 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, percentage
        )
    completion_percentage.short_description = 'Completion %'
    
    def get_queryset(self, request):
        """Filter checklists based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(application__is_deleted=False)


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    """Admin for ReviewDecision model."""
    
    list_display = [
        'application', 'reviewer', 'decision', 'is_final', 'created_at'
    ]
    list_filter = ['decision', 'is_final', 'created_at', 'reviewer']
    search_fields = [
        'application__business_name', 'reviewer__email', 'reason'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Decision Information', {
            'fields': ('application', 'reviewer', 'decision', 'is_final')
        }),
        ('Reason', {
            'fields': ('reason',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter decisions based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(application__is_deleted=False)