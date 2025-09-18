"""
Admin configuration for applications app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import SupplierApplication, TeamMember, NextOfKin, BankAccount


class TeamMemberInline(admin.TabularInline):
    """Inline admin for TeamMember."""
    model = TeamMember
    extra = 0
    fields = ['full_name', 'city', 'region', 'telephone', 'email', 'id_card_type']


class NextOfKinInline(admin.TabularInline):
    """Inline admin for NextOfKin."""
    model = NextOfKin
    extra = 0
    fields = ['full_name', 'relationship', 'mobile', 'id_card_type']


class BankAccountInline(admin.TabularInline):
    """Inline admin for BankAccount."""
    model = BankAccount
    extra = 0
    fields = ['bank_name', 'branch', 'account_name', 'account_number', 'account_index']


@admin.register(SupplierApplication)
class SupplierApplicationAdmin(admin.ModelAdmin):
    """Admin for SupplierApplication model."""
    
    list_display = [
        'business_name', 'email', 'region', 'status', 'submitted_at', 
        'reviewed_at', 'decided_at', 'has_missing_docs', 'pdf_actions'
    ]
    list_filter = [
        'status', 'region', 'submitted_at', 'reviewed_at', 'decided_at'
    ]
    search_fields = [
        'business_name', 'email', 'tracking_code', 'city', 'telephone'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'tracking_code', 'submitted_at', 'reviewed_at', 'decided_at',
        'created_at', 'updated_at'
    ]
    inlines = [TeamMemberInline, NextOfKinInline, BankAccountInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'business_name', 'physical_address', 'city', 'country', 'region',
                'telephone', 'email'
            )
        }),
        ('Business Details', {
            'fields': ('commodities_to_supply', 'other_commodities', 'warehouse_location')
        }),
        ('Declaration', {
            'fields': (
                'declaration_agreed', 'signer_name', 'signer_designation', 'signed_at'
            )
        }),
        ('Status & Tracking', {
            'fields': (
                'status', 'tracking_code', 'submitted_at', 'reviewed_at', 'decided_at'
            )
        }),
        ('Review Information', {
            'fields': ('reviewer_comment', 'supplier_user')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['commodities_to_supply']
    
    def has_missing_docs(self, obj):
        """Check if application has missing documents."""
        if obj.status == obj.ApplicationStatus.UNDER_REVIEW:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    has_missing_docs.short_description = 'Missing Docs'
    
    def pdf_actions(self, obj):
        """Display PDF generation and download actions."""
        actions = []
        
        if obj.pdf_file:
            # PDF exists, show download link - use admin action
            actions.append(
                format_html(
                    '<a href="{}" class="button" target="_blank">📄 Download PDF</a>',
                    f"/admin/applications/supplierapplication/{obj.pk}/pdf/"
                )
            )
        else:
            # PDF doesn't exist, show generate button - use admin action
            actions.append(
                format_html(
                    '<a href="{}" class="button">📄 Generate PDF</a>',
                    f"/admin/applications/supplierapplication/{obj.pk}/generate-pdf/"
                )
            )
        
        return format_html(' '.join(actions))
    pdf_actions.short_description = 'PDF Actions'
    
    def get_urls(self):
        """Add custom URLs for PDF actions."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/pdf/', self.admin_site.admin_view(self.download_pdf), name='applications_supplierapplication_pdf'),
            path('<int:pk>/generate-pdf/', self.admin_site.admin_view(self.generate_pdf), name='applications_supplierapplication_generate_pdf'),
        ]
        return custom_urls + urls
    
    def download_pdf(self, request, pk):
        """Download PDF for an application."""
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        if not application.pdf_file:
            return HttpResponse(
                'PDF not yet generated for this application',
                status=404
            )
        
        # Return the PDF file
        response = HttpResponse(
            application.pdf_file.read(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="application_{application.tracking_code}.pdf"'
        return response
    
    def generate_pdf(self, request, pk):
        """Generate PDF for an application."""
        from django.http import HttpResponse, HttpResponseRedirect
        from django.shortcuts import get_object_or_404
        from django.contrib import messages
        
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        try:
            # Generate PDF using the PDF service
            from .pdf_service import ApplicationPDFService
            pdf_service = ApplicationPDFService()
            pdf_path = pdf_service.generate_application_pdf(application)
            
            if pdf_path:
                messages.success(request, f'PDF generated successfully for application {application.tracking_code}')
                # Redirect to the download view
                return HttpResponseRedirect(f'/admin/applications/supplierapplication/{pk}/pdf/')
            else:
                messages.error(request, 'Failed to generate PDF')
                return HttpResponseRedirect(f'/admin/applications/supplierapplication/{pk}/change/')
                
        except Exception as e:
            messages.error(request, f'Error generating PDF: {str(e)}')
            return HttpResponseRedirect(f'/admin/applications/supplierapplication/{pk}/change/')

    def get_queryset(self, request):
        """Filter applications based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_deleted=False)
    
    actions = ['request_more_documents', 'approve_application', 'reject_application']
    
    def request_more_documents(self, request, queryset):
        """Action to request more documents."""
        for application in queryset:
            if application.status in [application.ApplicationStatus.PENDING_REVIEW, application.ApplicationStatus.UNDER_REVIEW]:
                application.status = application.ApplicationStatus.UNDER_REVIEW
                application.reviewed_at = timezone.now()
                application.save()
                
                # TODO: Send email notification
                messages.success(
                    request, 
                    f"Requested more documents for {application.business_name}"
                )
            else:
                messages.warning(
                    request, 
                    f"Cannot request documents for {application.business_name} (status: {application.get_status_display()})"
                )
    request_more_documents.short_description = "Request More Documents"
    
    def approve_application(self, request, queryset):
        """Action to approve applications."""
        for application in queryset:
            if application.status == application.ApplicationStatus.UNDER_REVIEW:
                # Check if all required documents are verified
                required_docs = application.document_uploads.filter(
                    requirement__is_required=True
                )
                unverified_docs = required_docs.filter(verified=False)
                
                if unverified_docs.exists():
                    messages.error(
                        request, 
                        f"Cannot approve {application.business_name}: {unverified_docs.count()} required documents not verified"
                    )
                    continue
                
                application.status = application.ApplicationStatus.APPROVED
                application.decided_at = timezone.now()
                application.save()
                
                # TODO: Create supplier user account
                # TODO: Send approval email
                messages.success(
                    request, 
                    f"Approved application for {application.business_name}"
                )
            else:
                messages.warning(
                    request, 
                    f"Cannot approve {application.business_name} (status: {application.get_status_display()})"
                )
    approve_application.short_description = "Approve Applications"
    
    def reject_application(self, request, queryset):
        """Action to reject applications."""
        for application in queryset:
            if application.status in [application.ApplicationStatus.PENDING_REVIEW, application.ApplicationStatus.UNDER_REVIEW]:
                application.status = application.ApplicationStatus.REJECTED
                application.decided_at = timezone.now()
                application.save()
                
                # TODO: Send rejection email
                messages.success(
                    request, 
                    f"Rejected application for {application.business_name}"
                )
            else:
                messages.warning(
                    request, 
                    f"Cannot reject {application.business_name} (status: {application.get_status_display()})"
                )
    reject_application.short_description = "Reject Applications"


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin for TeamMember model."""
    
    list_display = [
        'full_name', 'application', 'city', 'region', 'telephone', 'email'
    ]
    list_filter = ['region', 'id_card_type', 'created_at']
    search_fields = ['full_name', 'application__business_name', 'email', 'telephone']
    ordering = ['full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NextOfKin)
class NextOfKinAdmin(admin.ModelAdmin):
    """Admin for NextOfKin model."""
    
    list_display = [
        'full_name', 'application', 'relationship', 'mobile', 'id_card_type'
    ]
    list_filter = ['relationship', 'id_card_type', 'created_at']
    search_fields = ['full_name', 'application__business_name', 'mobile']
    ordering = ['full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin for BankAccount model."""
    
    list_display = [
        'bank_name', 'account_name', 'account_number', 'application', 'account_index'
    ]
    list_filter = ['bank_name', 'account_index', 'created_at']
    search_fields = [
        'bank_name', 'account_name', 'account_number', 'application__business_name'
    ]
    ordering = ['bank_name', 'account_name']
    readonly_fields = ['created_at', 'updated_at']