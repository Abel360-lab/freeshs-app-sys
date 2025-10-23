"""
Admin configuration for applications app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from .models import SupplierApplication, TeamMember, NextOfKin, BankAccount, ContractDocumentRequirement, ContractDocument, ContractDocumentAssignment, ContractSigning, School


class RegionNameField(Field):
    """Custom field to handle region name to region instance conversion during import."""
    
    def clean(self, data, **kwargs):
        """Convert region name to region instance during import."""
        region_name = data.get(self.column_name)
        if region_name:
            from core.models import Region
            try:
                region = Region.objects.get(name__iexact=str(region_name).strip())
                return region  # Return the Region instance, not just the ID
            except Region.DoesNotExist:
                # Create a new region if it doesn't exist
                region = Region.objects.create(
                    name=str(region_name).strip(),
                    code=str(region_name).strip().upper()[:10]
                )
                return region  # Return the Region instance, not just the ID
        return None

class SchoolResource(resources.ModelResource):
    """
    Resource for School import/export.
    """
    
    region_name = Field(attribute='region__name', column_name='Region Name')
    region = RegionNameField(attribute='region', column_name='Region Name')
    
    class Meta:
        model = School
        fields = (
            'id', 'name', 'code', 'region', 'district', 'address',
            'contact_person', 'contact_phone', 'contact_email', 'is_active'
        )
        export_order = (
            'id', 'name', 'code', 'region_name', 'district', 'address',
            'contact_person', 'contact_phone', 'contact_email', 'is_active'
        )
        import_id_fields = ['code']
        skip_unchanged = True
        report_skipped = True
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Map different column name variations for import
        self.fields['name'] = Field(attribute='name', column_name='Name')
        self.fields['code'] = Field(attribute='code', column_name='Code')
        self.fields['district'] = Field(attribute='district', column_name='District')
        self.fields['address'] = Field(attribute='address', column_name='Address')
        self.fields['contact_person'] = Field(attribute='contact_person', column_name='Contact Person')
        self.fields['contact_phone'] = Field(attribute='contact_phone', column_name='Contact Phone')
        self.fields['contact_email'] = Field(attribute='contact_email', column_name='Contact Email')
        self.fields['is_active'] = Field(attribute='is_active', column_name='Is Active')
    
    def dehydrate_region_name(self, school):
        """Get region name for export."""
        try:
            return school.region.name if school.region else ''
        except AttributeError:
            return ''
    
    def before_import_row(self, row, **kwargs):
        """Process row before import."""
        # Validate required fields
        name = row.get('Name') or row.get('name')
        if not name or not str(name).strip():
            raise ValueError("School name is required")
        
        code = row.get('Code') or row.get('code')
        if not code or not str(code).strip():
            raise ValueError("School code is required")
        
        district = row.get('District') or row.get('district')
        if not district or not str(district).strip():
            raise ValueError("District is required")
        
        address = row.get('Address') or row.get('address')
        if not address or not str(address).strip():
            raise ValueError("Address is required")
        
        region_name = row.get('Region Name')
        if not region_name or not str(region_name).strip():
            raise ValueError("Region Name is required")
    
    def after_import_row(self, row, row_result, **kwargs):
        """Process row after import."""
        if row_result.import_type == 'new':
            # Log successful import
            pass
        elif row_result.import_type == 'update':
            # Log successful update
            pass
    
    def get_import_id_fields(self):
        """Get the fields used to identify existing records."""
        return ['code']


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


@admin.register(ContractDocumentRequirement)
class ContractDocumentRequirementAdmin(admin.ModelAdmin):
    """Admin for ContractDocumentRequirement model."""
    
    list_display = [
        'label', 'code', 'is_required', 'max_file_size_mb', 'is_active', 'created_at'
    ]
    list_filter = ['is_required', 'is_active', 'created_at']
    search_fields = ['label', 'code', 'description']
    ordering = ['label']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'label', 'description'),
            'description': 'Enter a unique code for this requirement. Common codes include: CONTRACT_TEMPLATE, TERMS_CONDITIONS, PRICING_SCHEDULE, etc. You can also create custom codes like CUSTOM_DOC_1, SPECIAL_REQUIREMENT, etc.'
        }),
        ('Requirements', {
            'fields': ('is_required', 'condition_note')
        }),
        ('File Settings', {
            'fields': ('allowed_extensions', 'max_file_size_mb'),
            'description': 'Specify allowed file extensions as a JSON list (e.g., [".pdf", ".doc", ".docx"]) and maximum file size in MB.'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form to provide better help text for the code field."""
        form = super().get_form(request, obj, **kwargs)
        
        # Add custom help text for the code field
        if 'code' in form.base_fields:
            from .models import ContractDocumentRequirement
            
            # Get common codes for suggestions
            common_codes = ContractDocumentRequirement.get_common_codes()
            code_suggestions = ', '.join([code for code, _ in common_codes[:5]])
            
            form.base_fields['code'].help_text = (
                f"Enter a unique code for this requirement. "
                f"Common examples: {code_suggestions}, or create custom codes like CUSTOM_DOC_1, SPECIAL_REQUIREMENT, etc. "
                f"Use uppercase letters, numbers, and underscores only."
            )
            form.base_fields['code'].widget.attrs.update({
                'placeholder': 'e.g., CONTRACT_TEMPLATE or CUSTOM_DOC_1',
                'style': 'text-transform: uppercase;',
                'list': 'code-suggestions'
            })
        
        return form
    
    def get_changelist_form(self, request, **kwargs):
        """Add code suggestions to the changelist form as well."""
        form = super().get_changelist_form(request, **kwargs)
        if form and 'code' in form.base_fields:
            form.base_fields['code'].widget.attrs.update({
                'style': 'text-transform: uppercase;'
            })
        return form


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    """Admin for ContractDocument model."""
    
    list_display = [
        'title', 'category', 'requirement', 'version', 'status', 'is_current_version', 'created_at'
    ]
    list_filter = ['category', 'status', 'is_current_version', 'requirement', 'created_at']
    search_fields = ['title', 'description', 'requirement__label']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'file_extension']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'requirement', 'title', 'description'),
            'description': 'Select STATIC for pre-uploaded documents (terms, conditions, etc.) or DYNAMIC for contract templates that will be filled during contract awarding.'
        }),
        ('Document File', {
            'fields': ('document_file', 'file_size', 'file_extension'),
            'description': 'Upload files for STATIC documents. Leave empty for DYNAMIC documents (they serve as templates).'
        }),
        ('Version Control', {
            'fields': ('version', 'is_current_version')
        }),
        ('Status & Dates', {
            'fields': ('status', 'effective_from', 'effective_until')
        }),
        ('Metadata', {
            'fields': ('notes', 'created_by')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('requirement', 'created_by').prefetch_related('assigned_contracts')


@admin.register(ContractDocumentAssignment)
class ContractDocumentAssignmentAdmin(admin.ModelAdmin):
    """Admin for ContractDocumentAssignment model."""
    
    list_display = [
        'contract', 'document', 'is_required', 'assigned_by', 'assigned_at'
    ]
    list_filter = ['is_required', 'assigned_at', 'contract__status']
    search_fields = ['contract__contract_number', 'document__title', 'assigned_by__username']
    ordering = ['-assigned_at']
    readonly_fields = ['assigned_at']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('contract', 'document', 'is_required')
        }),
        ('Assignment Info', {
            'fields': ('assigned_by', 'assigned_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContractSigning)
class ContractSigningAdmin(admin.ModelAdmin):
    """Admin for ContractSigning model."""
    
    list_display = [
        'contract', 'supplier', 'status', 'reviewed_at', 'signed_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'reviewed_at', 'signed_at']
    search_fields = ['contract__contract_number', 'supplier__username', 'supplier__first_name', 'supplier__last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Contract & Supplier', {
            'fields': ('contract', 'supplier')
        }),
        ('Signing Status', {
            'fields': ('status', 'reviewed_at', 'signed_at')
        }),
        ('Signing Details', {
            'fields': ('signature_file', 'rejection_reason', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('contract', 'supplier')


@admin.register(School)
class SchoolAdmin(ImportExportModelAdmin):
    """
    Admin interface for School model with import/export functionality.
    """
    
    resource_class = SchoolResource
    
    list_display = [
        'name', 'code', 'region', 'district', 'contact_person', 
        'contact_phone', 'is_active', 'created_at'
    ]
    list_filter = [
        'region', 'district', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'code', 'district', 'contact_person', 'contact_phone', 'contact_email'
    ]
    ordering = ['region', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'code', 'region', 'district', 'address'
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_person', 'contact_phone', 'contact_email'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('region')