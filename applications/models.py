"""
Application models for GCX Supplier Application Portal.
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class SupplierApplication(models.Model):
    """
    Main supplier application model.
    """
    
    class ApplicationStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        NEEDS_MORE_DOCS = 'NEEDS_MORE_DOCS', 'Needs More Documents'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    
    # User Account (created upon application submission)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User account created for this application"
    )
    
    # Basic Information
    business_name = models.CharField(
        max_length=200,
        help_text="Official business name"
    )
    business_type = models.CharField(
        max_length=50,
        choices=[
            ('sole', 'Sole Proprietorship'),
            ('partnership', 'Partnership'),
            ('limited', 'Limited Liability Company'),
            ('corporation', 'Corporation'),
            ('other', 'Other'),
        ],
        default='sole',
        help_text="Type of business entity"
    )
    registration_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Business registration number"
    )
    tin_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Tax Identification Number (TIN)"
    )
    physical_address = models.TextField(
        help_text="Physical address of the business"
    )
    city = models.CharField(
        max_length=100,
        help_text="City where the business is located"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Postal/ZIP code"
    )
    country = models.CharField(
        max_length=100,
        default='Ghana',
        help_text="Country where the business is located"
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        related_name='applications',
        help_text="Region where the business is located"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^(\+?233|0?233|0)[1-9]\d{8}$',
        message="Phone number must be in Ghana format: 0243123456, +233243123456, or 233243123456"
    )
    telephone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        help_text="Business telephone number in Ghana format (0243123456, +233243123456, or 233243123456)"
    )
    email = models.EmailField(
        help_text="Business email address"
    )
    
    # Business Details
    commodities_to_supply = models.ManyToManyField(
        'core.Commodity',
        related_name='applications',
        help_text="Commodities the business intends to supply",
        blank=True
    )
    other_commodities = models.TextField(
        blank=True,
        null=True,
        help_text="Other commodities not in the predefined list"
    )
    warehouse_location = models.TextField(
        help_text="Location of warehouse/storage facility"
    )
    
    # Declaration
    declaration_agreed = models.BooleanField(
        default=False,
        help_text="Whether the applicant agrees to the terms and conditions"
    )
    data_consent = models.BooleanField(
        default=False,
        help_text="Whether the applicant consents to data processing"
    )
    signer_name = models.CharField(
        max_length=200,
        help_text="Name of the person signing the application"
    )
    signer_designation = models.CharField(
        max_length=200,
        help_text="Designation/position of the signer"
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the application was signed"
    )
    
    # Document Fields
    business_registration = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="Business registration documents"
    )
    vat_certificate = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="VAT registration certificate"
    )
    ppa_certificate = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="PPA certificate"
    )
    tax_clearance = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="Tax clearance certificate"
    )
    proof_of_office = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="Proof of office documents"
    )
    id_directors = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="ID cards of directors"
    )
    gcx_registration = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="GCX registration documents"
    )
    team_member_id = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="Team member ID documents"
    )
    fda_certificate = models.FileField(
        upload_to='applications/documents/',
        null=True,
        blank=True,
        help_text="FDA certificate for processed food"
    )
    pdf_file = models.FileField(
        upload_to='applications/pdfs/',
        null=True,
        blank=True,
        help_text="Generated PDF of application details"
    )
    
    # Tracking and Status
    tracking_code = models.SlugField(
        unique=True,
        help_text="Unique tracking code for the application"
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING_REVIEW,
        help_text="Current status of the application"
    )
    
    # Review Information
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the application was submitted"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the application was last reviewed"
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the final decision was made"
    )
    reviewer_comment = models.TextField(
        blank=True,
        help_text="Comments from the reviewer"
    )
    
    # Document completion tracking
    completion_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Secure token for document completion"
    )
    missing_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of missing document types"
    )
    gcx_registration_proof_uploaded = models.BooleanField(
        default=False,
        help_text="Whether GCX Registration Proof has been uploaded"
    )
    document_completion_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline for completing missing documents"
    )
    
    # User Account (created after approval)
    supplier_user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_application',
        help_text="User account created for approved supplier"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    
    class Meta:
        db_table = 'applications_supplier_application'
        verbose_name = 'Supplier Application'
        verbose_name_plural = 'Supplier Applications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.business_name} - {self.get_status_display()}"
    
    def get_completion_percentage(self):
        """Calculate application completion percentage."""
        total_fields = 10  # Basic required fields
        completed_fields = 0
        
        # Check basic fields
        if self.business_name: completed_fields += 1
        if self.email: completed_fields += 1
        if self.telephone: completed_fields += 1
        if self.physical_address: completed_fields += 1
        if self.city: completed_fields += 1
        if self.region: completed_fields += 1
        if self.warehouse_location: completed_fields += 1
        if self.commodities_to_supply.exists(): completed_fields += 1
        if self.team_members.exists(): completed_fields += 1
        if self.bank_accounts.exists(): completed_fields += 1
        
        return round((completed_fields / total_fields) * 100)
    
    def get_priority(self):
        """Determine application priority based on various factors."""
        from django.utils import timezone
        days_since_submission = (timezone.now() - self.created_at).days
        
        if days_since_submission > 7:
            return 'high'
        elif days_since_submission > 3:
            return 'medium'
        else:
            return 'low'
    
    def get_missing_documents_count(self):
        """Get count of missing required documents."""
        from documents.models import DocumentRequirement
        required_docs = DocumentRequirement.objects.filter(is_required=True, is_active=True)
        uploaded_docs = self.document_uploads.values_list('requirement_id', flat=True)
        return required_docs.exclude(id__in=uploaded_docs).count()
    
    def get_missing_documents_list(self):
        """Get list of missing required documents."""
        from documents.models import DocumentRequirement
        required_docs = DocumentRequirement.objects.filter(is_required=True, is_active=True)
        uploaded_docs = self.document_uploads.values_list('requirement_id', flat=True)
        missing_docs = required_docs.exclude(id__in=uploaded_docs)
        return [doc.label for doc in missing_docs]
    
    def supplies_processed_foods(self):
        """Check if this application supplies processed foods that require FDA certificate."""
        from core.models import Commodity
        
        # Check predefined commodities
        processed_commodities = self.commodities_to_supply.filter(is_processed_food=True)
        if processed_commodities.exists():
            return True
        
        # Check other commodities text for processed food mentions
        if self.other_commodities:
            other_commodities_lower = self.other_commodities.lower()
            processed_food_names = ['tom brown', 'palm oil']
            return any(food in other_commodities_lower for food in processed_food_names)
        
        return False
    
    def check_document_completeness(self):
        """Check if all required documents are uploaded and update status accordingly."""
        from documents.models import DocumentRequirement
        
        # Get all required documents
        required_docs = DocumentRequirement.objects.filter(is_required=True, is_active=True)
        
        # Check which documents are uploaded based on the model's file fields
        uploaded_docs = []
        missing_docs = []
        
        # Map document requirements to model fields
        doc_field_mapping = {
            'Business Registration': 'business_registration',
            'VAT Certificate': 'vat_certificate', 
            'PPA Certificate': 'ppa_certificate',
            'Tax Clearance': 'tax_clearance',
            'Proof of Office': 'proof_of_office',
            'ID of Directors': 'id_directors',
            'GCX Registration Proof': 'gcx_registration',
            'Team Member ID': 'team_member_id',
            'FDA Certificate': 'fda_certificate',
        }
        
        for doc in required_docs:
            field_name = doc_field_mapping.get(doc.label)
            if field_name:
                field_value = getattr(self, field_name, None)
                if field_value:
                    uploaded_docs.append(doc.label)
                else:
                    missing_docs.append(doc.label)
        
        # Check for GCX Registration Proof specifically
        if 'GCX Registration Proof' in uploaded_docs:
            self.gcx_registration_proof_uploaded = True
        else:
            self.gcx_registration_proof_uploaded = False
        
        self.missing_documents = missing_docs
        
        # Update status based on document completeness
        if missing_docs:
            # Keep status as PENDING_REVIEW if documents are missing
            # Set deadline for document completion (30 days from now)
            from datetime import timedelta
            self.document_completion_deadline = timezone.now() + timedelta(days=30)
        else:
            # All required documents are uploaded
            if self.status == self.ApplicationStatus.PENDING_REVIEW:
                self.missing_documents = []
                self.document_completion_deadline = None
        
        return len(missing_docs) == 0
    
    def get_completion_url(self):
        """Get the secure URL for completing missing documents."""
        from django.urls import reverse
        try:
            return reverse('applications:complete-documents', kwargs={'token': str(self.completion_token)})
        except:
            # Fallback URL if the view doesn't exist yet
            return f"/complete-documents/{self.completion_token}/"
    
    def is_completion_token_valid(self):
        """Check if the completion token is still valid (not expired)."""
        if not self.document_completion_deadline:
            return True
        return timezone.now() <= self.document_completion_deadline
    
    @classmethod
    def generate_unique_reference_number(cls):
        """Generate a unique reference number in format GCX-YYYY-NNNNNN."""
        from django.utils import timezone
        import random
        
        current_year = timezone.now().year
        
        # Try to generate a unique reference number
        max_attempts = 100
        for attempt in range(max_attempts):
            # Generate a 6-digit random number
            random_number = random.randint(100000, 999999)
            reference_number = f"GCX-{current_year}-{random_number}"
            
            # Check if this reference number already exists
            if not cls.objects.filter(tracking_code=reference_number).exists():
                return reference_number
        
        # Fallback to UUID if we can't generate a unique number
        return f"GCX-{current_year}-{uuid.uuid4().hex[:6].upper()}"
    
    def clean(self):
        """Validate the application data."""
        super().clean()
        
        if self.status == self.ApplicationStatus.PENDING_REVIEW and not self.declaration_agreed:
            raise ValidationError("Declaration must be agreed to before submission.")
        
        if self.status in [self.ApplicationStatus.APPROVED, self.ApplicationStatus.REJECTED]:
            if not self.decided_at:
                self.decided_at = timezone.now()
    
    def save(self, *args, **kwargs):
        """Override save to handle status changes and generate tracking code."""
        # Generate human-readable tracking code if not set
        if not self.tracking_code:
            self.tracking_code = self.generate_unique_reference_number()
        
        # Set submitted_at when application is first submitted
        if self.status == self.ApplicationStatus.PENDING_REVIEW and not self.submitted_at:
            self.submitted_at = timezone.now()
        
        # Set reviewed_at when status changes to UNDER_REVIEW (admin opens the application)
        if self.status == self.ApplicationStatus.UNDER_REVIEW and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        
        # Set decided_at when application is approved or rejected
        if self.status in [self.ApplicationStatus.APPROVED, self.ApplicationStatus.REJECTED] and not self.decided_at:
            self.decided_at = timezone.now()
        
        # Save first to get primary key
        super().save(*args, **kwargs)
        
        # Check document completeness and update status accordingly after saving
        # Only check if status is PENDING_REVIEW (not when admin changes to UNDER_REVIEW)
        if self.status == self.ApplicationStatus.PENDING_REVIEW:
            self.check_document_completeness()
            # Save again if status was updated
            super().save(update_fields=['status', 'missing_documents', 'gcx_registration_proof_uploaded', 'document_completion_deadline'])


class TeamMember(models.Model):
    """
    Team member with food supply and distribution experience.
    """
    
    class IDCardType(models.TextChoices):
        GHANA_CARD = 'GHANA_CARD', 'Ghana Card'
        PASSPORT = 'PASSPORT', 'Passport'
        VOTER_ID = 'VOTER_ID', 'Voter ID'
        OTHER = 'OTHER', 'Other'
    
    application = models.ForeignKey(
        SupplierApplication,
        on_delete=models.CASCADE,
        related_name='team_members',
        help_text="Application this team member belongs to"
    )
    
    # Personal Information
    full_name = models.CharField(
        max_length=200,
        help_text="Full name of the team member"
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Position/role of the team member"
    )
    years_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Years of experience in food supply/distribution"
    )
    address = models.TextField(
        help_text="Address of the team member"
    )
    city = models.CharField(
        max_length=100,
        help_text="City where the team member lives"
    )
    country = models.CharField(
        max_length=100,
        default='Ghana',
        help_text="Country where the team member lives"
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        related_name='team_members',
        help_text="Region where the team member lives"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^(\+?233|0?233|0)[1-9]\d{8}$',
        message="Phone number must be in Ghana format: 0243123456, +233243123456, or 233243123456"
    )
    telephone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        help_text="Telephone number in Ghana format (0243123456, +233243123456, or 233243123456)"
    )
    email = models.EmailField(
        blank=True,
        help_text="Email address"
    )
    
    # ID Information
    id_card_type = models.CharField(
        max_length=20,
        choices=IDCardType.choices,
        blank=True,
        help_text="Type of ID card"
    )
    id_card_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID card number"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications_team_member'
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.application.business_name}"
    
    def clean(self):
        """Validate team member data."""
        super().clean()
        
        if not self.telephone and not self.email:
            raise ValidationError("Either telephone or email must be provided.")
        
        if self.id_card_type and not self.id_card_number:
            raise ValidationError("ID card number is required when ID card type is specified.")


class NextOfKin(models.Model):
    """
    Next of kin information for the application.
    """
    
    class IDCardType(models.TextChoices):
        GHANA_CARD = 'GHANA_CARD', 'Ghana Card'
        PASSPORT = 'PASSPORT', 'Passport'
        VOTER_ID = 'VOTER_ID', 'Voter ID'
        OTHER = 'OTHER', 'Other'
    
    application = models.ForeignKey(
        SupplierApplication,
        on_delete=models.CASCADE,
        related_name='next_of_kin',
        help_text="Application this next of kin belongs to"
    )
    
    # Personal Information
    full_name = models.CharField(
        max_length=200,
        help_text="Full name of the next of kin"
    )
    relationship = models.CharField(
        max_length=100,
        help_text="Relationship to the applicant"
    )
    address = models.TextField(
        help_text="Address of the next of kin"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^(\+?233|0?233|0)[1-9]\d{8}$',
        message="Phone number must be in Ghana format: 0243123456, +233243123456, or 233243123456"
    )
    mobile = models.CharField(
        validators=[phone_regex],
        max_length=15,
        help_text="Mobile number in Ghana format (0243123456, +233243123456, or 233243123456)"
    )
    
    # ID Information
    id_card_type = models.CharField(
        max_length=20,
        choices=IDCardType.choices,
        blank=True,
        help_text="Type of ID card"
    )
    id_card_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID card number"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications_next_of_kin'
        verbose_name = 'Next of Kin'
        verbose_name_plural = 'Next of Kin'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.application.business_name}"


class BankAccount(models.Model):
    """
    Bank account information for the application.
    """
    
    application = models.ForeignKey(
        SupplierApplication,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        help_text="Application this bank account belongs to"
    )
    
    # Bank Information
    bank_name = models.CharField(
        max_length=200,
        help_text="Name of the bank"
    )
    branch = models.CharField(
        max_length=200,
        help_text="Branch of the bank"
    )
    account_name = models.CharField(
        max_length=200,
        help_text="Name on the account (must match business name)"
    )
    account_number = models.CharField(
        max_length=50,
        help_text="Account number"
    )
    account_index = models.PositiveSmallIntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2')],
        help_text="Account option (1 or 2)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications_bank_account'
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        ordering = ['account_index']
        unique_together = ['application', 'account_index']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_name} ({self.application.business_name})"
    
    def clean(self):
        """Validate bank account data."""
        super().clean()
        
        # Check if account name matches business name (case-insensitive, allowing for punctuation differences)
        business_name_clean = ''.join(c.lower() for c in self.application.business_name if c.isalnum())
        account_name_clean = ''.join(c.lower() for c in self.account_name if c.isalnum())
        
        if business_name_clean != account_name_clean:
            raise ValidationError(
                f"Account name '{self.account_name}' must match business name '{self.application.business_name}'"
            )


class SupplierContract(models.Model):
    """
    Model for storing supplier contracts uploaded by admins.
    """
    
    class ContractStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        TERMINATED = 'TERMINATED', 'Terminated'
    
    class ContractType(models.TextChoices):
        SUPPLY_AGREEMENT = 'SUPPLY_AGREEMENT', 'Supply Agreement'
        FRAMEWORK_AGREEMENT = 'FRAMEWORK_AGREEMENT', 'Framework Agreement'
        SERVICE_AGREEMENT = 'SERVICE_AGREEMENT', 'Service Agreement'
        OTHER = 'OTHER', 'Other'
    
    # Related application/supplier
    application = models.ForeignKey(
        SupplierApplication,
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text="Associated supplier application"
    )
    
    # Contract details
    contract_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique contract number"
    )
    contract_type = models.CharField(
        max_length=50,
        choices=ContractType.choices,
        default=ContractType.SUPPLY_AGREEMENT,
        help_text="Type of contract"
    )
    title = models.CharField(
        max_length=200,
        help_text="Contract title"
    )
    description = models.TextField(
        blank=True,
        help_text="Contract description"
    )
    
    # Contract file
    contract_file = models.FileField(
        upload_to='contracts/%Y/%m/',
        help_text="Uploaded contract document"
    )
    
    # Contract dates
    start_date = models.DateField(
        help_text="Contract start date"
    )
    end_date = models.DateField(
        help_text="Contract end date"
    )
    
    # Financial terms
    contract_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total contract value"
    )
    currency = models.CharField(
        max_length=3,
        default='GHS',
        help_text="Contract currency"
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT,
        help_text="Contract status"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contracts',
        help_text="Admin who created the contract"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Supplier Contract"
        verbose_name_plural = "Supplier Contracts"
    
    def __str__(self):
        return f"{self.contract_number} - {self.title}"
    
    def is_active(self):
        """Check if contract is currently active."""
        today = timezone.now().date()
        return (
            self.status == self.ContractStatus.ACTIVE and
            self.start_date <= today <= self.end_date
        )
    
    def days_remaining(self):
        """Calculate days remaining until contract expires."""
        if self.end_date:
            today = timezone.now().date()
            remaining = (self.end_date - today).days
            return max(0, remaining)
        return None




class School(models.Model):
    """
    Model for schools in different regions.
    """
    
    name = models.CharField(
        max_length=200,
        help_text="School name"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique school code"
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.CASCADE,
        related_name='schools',
        help_text="Region where the school is located"
    )
    district = models.CharField(
        max_length=100,
        help_text="District name"
    )
    address = models.TextField(
        help_text="School address"
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Contact person name"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Contact email address"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the school is active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "School"
        verbose_name_plural = "Schools"
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ContractCommodity(models.Model):
    """
    Model for specifying commodity quantities per school/region in contracts.
    """
    
    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        related_name='contract_commodities',
        help_text="Associated contract"
    )
    commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.CASCADE,
        help_text="Commodity to be supplied"
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific school (if applicable)"
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Region (if not specific to a school)"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity to be supplied"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total amount for this commodity"
    )
    delivery_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Delivery deadline"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['commodity__name', 'school__name']
        verbose_name = "Contract Commodity"
        verbose_name_plural = "Contract Commodities"
        unique_together = ['contract', 'commodity', 'school']
    
    def __str__(self):
        school_info = f" - {self.school.name}" if self.school else f" - {self.region.name}" if self.region else ""
        return f"{self.commodity.name}{school_info} ({self.quantity} {self.unit_of_measure})"
    
    def save(self, *args, **kwargs):
        """Calculate total amount before saving."""
        if self.quantity and self.unit_price:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class ContractAcceptance(models.Model):
    """
    Model for tracking supplier contract acceptance.
    """
    
    class AcceptanceStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
    
    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        related_name='acceptances',
        help_text="Associated contract"
    )
    supplier_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contract_acceptances',
        help_text="Supplier user who accepted/rejected the contract"
    )
    status = models.CharField(
        max_length=20,
        choices=AcceptanceStatus.choices,
        default=AcceptanceStatus.PENDING,
        help_text="Acceptance status"
    )
    acceptance_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when contract was accepted"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if applicable)"
    )
    terms_accepted = models.BooleanField(
        default=False,
        help_text="Whether supplier accepted the terms"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes from supplier"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contract Acceptance"
        verbose_name_plural = "Contract Acceptances"
        unique_together = ['contract', 'supplier_user']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.supplier_user.get_full_name() or self.supplier_user.username} ({self.get_status_display()})"


class DeliveryCommodity(models.Model):
    """
    Model for tracking individual commodities within a delivery.
    """
    delivery = models.ForeignKey(
        'DeliveryTracking',
        on_delete=models.CASCADE,
        related_name='commodities',
        help_text="Associated delivery"
    )
    commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.PROTECT,
        help_text="Commodity delivered"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity of commodity delivered"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure for the quantity (e.g., '100kg bag', '1 crate', '50kg sack')"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Unit price of the commodity"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount for this commodity"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['delivery', 'commodity']
        verbose_name = 'Delivery Commodity'
        verbose_name_plural = 'Delivery Commodities'
    
    def __str__(self):
        return f"{self.delivery.serial_number} - {self.commodity.name} ({self.quantity} {self.unit_of_measure})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total amount if unit_price is provided
        if self.unit_price and self.quantity:
            self.total_amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class DeliveryTracking(models.Model):
    """
    Model for tracking commodity deliveries to schools.
    """
    
    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        DELIVERED = 'DELIVERED', 'Delivered'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
    
    # Contract relationship - direct link to contract (optional)
    contract = models.ForeignKey(
        'SupplierContract',
        on_delete=models.CASCADE,
        related_name='deliveries',
        null=True,
        blank=True,
        help_text="Associated contract (if delivery is for a contract)"
    )
    
    # Delivery location - can be either from contract or direct selection
    contract_commodity = models.ForeignKey(
        ContractCommodity,
        on_delete=models.CASCADE,
        related_name='deliveries',
        null=True,
        blank=True,
        help_text="Associated contract commodity (if from contract) - DEPRECATED"
    )
    
    # Direct delivery location selection
    delivery_region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        related_name='deliveries',
        null=True,
        blank=True,
        help_text="Region where delivery was made"
    )
    delivery_school = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        related_name='deliveries',
        null=True,
        blank=True,
        help_text="School where delivery was made"
    )
    # Keep the old field for backward compatibility, but it's now optional
    delivery_commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.PROTECT,
        related_name='legacy_deliveries',
        null=True,
        blank=True,
        help_text="Legacy single commodity field (deprecated - use commodities relationship)"
    )
    supplier_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='deliveries',
        help_text="Supplier who made the delivery"
    )
    
    # Delivery details
    serial_number = models.CharField(
        max_length=100,
        help_text="Serial number for this delivery"
    )
    delivery_date = models.DateField(
        help_text="Date of delivery"
    )
    srv_number = models.CharField(
        max_length=100,
        help_text="Store Receipt Voucher number"
    )
    waybill_number = models.CharField(
        max_length=100,
        help_text="Waybill number"
    )
    invoice_number = models.CharField(
        max_length=100,
        help_text="Invoice number",
        null=True,
        blank=True
    )
    
    # Quantities delivered (legacy fields - now handled by DeliveryCommodity)
    quantity_delivered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Actual quantity delivered (legacy field)",
        null=True,
        blank=True
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure (legacy field)",
        null=True,
        blank=True
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        help_text="Delivery status"
    )
    
    # Supporting documents
    srv_document = models.FileField(
        upload_to='deliveries/srv/%Y/%m/',
        null=True,
        blank=True,
        help_text="SRV document"
    )
    waybill_document = models.FileField(
        upload_to='deliveries/waybill/%Y/%m/',
        null=True,
        blank=True,
        help_text="Waybill document"
    )
    invoice_document = models.FileField(
        upload_to='deliveries/invoice/%Y/%m/',
        null=True,
        blank=True,
        help_text="Invoice document"
    )
    
    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_deliveries',
        help_text="Admin who verified the delivery"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when delivery was verified"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Verification notes"
    )
    
    # Rejection
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_deliveries',
        help_text="Admin who rejected the delivery"
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when delivery was rejected"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="Additional delivery notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Delivery Tracking"
        verbose_name_plural = "Delivery Tracking"
    
    def __str__(self):
        if self.contract_commodity:
            return f"Delivery {self.serial_number} - {self.contract_commodity.commodity.name} to {self.contract_commodity.school.name if self.contract_commodity.school else self.contract_commodity.region.name}"
        else:
            commodity_name = self.delivery_commodity.name if self.delivery_commodity else "Unknown Commodity"
            school_name = self.delivery_school.name if self.delivery_school else "Unknown School"
            return f"Delivery {self.serial_number} - {commodity_name} to {school_name}"
    
    def get_school_name(self):
        """Get the school name for this delivery."""
        if self.contract_commodity:
            if self.contract_commodity.school:
                return self.contract_commodity.school.name
            elif self.contract_commodity.region:
                return f"Region: {self.contract_commodity.region.name}"
        else:
            return self.delivery_school.name
        return "Unknown"
    
    def get_region_name(self):
        """Get the region name for this delivery."""
        if self.contract_commodity:
            if self.contract_commodity.school:
                return self.contract_commodity.school.region.name
            elif self.contract_commodity.region:
                return self.contract_commodity.region.name
        else:
            return self.delivery_region.name
        return "Unknown"
    
    def get_commodity_name(self):
        """Get the commodity names for this delivery."""
        if self.contract_commodity:
            return self.contract_commodity.commodity.name
        elif self.commodities.exists():
            # Return comma-separated list of commodity names
            commodity_names = [commodity.commodity.name for commodity in self.commodities.all()]
            return ', '.join(commodity_names)
        else:
            return 'No commodities'


class StoreReceiptVoucher(models.Model):
    """
    Model for Store Receipt Vouchers (SRV) created by suppliers.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    # Basic Information
    srv_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique SRV number"
    )
    supplier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_srvs',
        help_text="Supplier who created the SRV",
        null=True,
        blank=True
    )
    
    # Delivery Information
    delivery_region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        help_text="Region where goods were delivered",
        null=True,
        blank=True
    )
    delivery_school = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        help_text="School where goods were delivered",
        null=True,
        blank=True
    )
    
    # Commodity Information
    commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.PROTECT,
        help_text="Commodity delivered",
        null=True,
        blank=True
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity of commodity delivered",
        null=True,
        blank=True
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price of the commodity"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount for this SRV"
    )
    
    # Delivery Details
    delivery_date = models.DateField(
        help_text="Date of delivery"
    )
    received_by = models.CharField(
        max_length=200,
        help_text="Name of person who received the goods",
        null=True,
        blank=True
    )
    received_by_designation = models.CharField(
        max_length=100,
        help_text="Designation of person who received the goods",
        null=True,
        blank=True
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="SRV status"
    )
    
    # Documents
    document = models.FileField(
        upload_to='srvs/%Y/%m/',
        null=True,
        blank=True,
        help_text="SRV document"
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Store Receipt Voucher"
        verbose_name_plural = "Store Receipt Vouchers"
    
    def __str__(self):
        return f"SRV {self.srv_number} - {self.commodity.name} to {self.delivery_school.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Waybill(models.Model):
    """
    Model for Waybill documents created by suppliers.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    # Basic Information
    waybill_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique waybill number"
    )
    supplier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_waybills',
        help_text="Supplier who created the waybill"
    )
    
    # Transport Information
    transporter_name = models.CharField(
        max_length=200,
        help_text="Name of the transporter"
    )
    vehicle_number = models.CharField(
        max_length=50,
        help_text="Vehicle registration number"
    )
    driver_name = models.CharField(
        max_length=200,
        help_text="Name of the driver"
    )
    driver_license = models.CharField(
        max_length=50,
        blank=True,
        help_text="Driver's license number"
    )
    
    # Route Information
    origin = models.CharField(
        max_length=200,
        help_text="Origin of the goods"
    )
    destination_region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        help_text="Destination region"
    )
    destination_school = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        help_text="Destination school"
    )
    
    # Commodity Information
    commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.PROTECT,
        help_text="Commodity being transported"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity of commodity"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure"
    )
    
    # Dates
    loading_date = models.DateTimeField(
        help_text="Date and time of loading"
    )
    expected_delivery_date = models.DateTimeField(
        help_text="Expected delivery date and time"
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Waybill status"
    )
    
    # Documents
    document = models.FileField(
        upload_to='waybills/%Y/%m/',
        null=True,
        blank=True,
        help_text="Waybill document"
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Waybill"
        verbose_name_plural = "Waybills"
    
    def __str__(self):
        return f"Waybill {self.waybill_number} - {self.commodity.name} to {self.destination_school.name}"


class Invoice(models.Model):
    """
    Model for Invoice documents created by suppliers.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        APPROVED = 'APPROVED', 'Approved'
        PAID = 'PAID', 'Paid'
        REJECTED = 'REJECTED', 'Rejected'
    
    # Basic Information
    invoice_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique invoice number"
    )
    supplier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_invoices',
        help_text="Supplier who created the invoice",
        null=True,
        blank=True
    )
    
    # Client Information
    client_region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        help_text="Client region",
        null=True,
        blank=True
    )
    client_school = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        help_text="Client school",
        null=True,
        blank=True
    )
    
    # Invoice Details
    invoice_date = models.DateField(
        help_text="Invoice date"
    )
    due_date = models.DateField(
        help_text="Payment due date"
    )
    
    # Commodity Information
    commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.PROTECT,
        help_text="Commodity invoiced",
        null=True,
        blank=True
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity of commodity",
        null=True,
        blank=True
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure",
        null=True,
        blank=True
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price",
        null=True,
        blank=True
    )
    
    # Amounts
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Subtotal amount"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Tax rate percentage"
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Tax amount"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount"
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Invoice status"
    )
    
    # Documents
    document = models.FileField(
        upload_to='invoices/%Y/%m/',
        null=True,
        blank=True,
        help_text="Invoice document"
    )
    
    # Payment Information
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment reference number"
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of payment"
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.commodity.name} to {self.client_school.name}"
    
    def save(self, *args, **kwargs):
        # Calculate amounts
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total_amount = self.subtotal + self.tax_amount
        super().save(*args, **kwargs)


class ContractDocumentRequirement(models.Model):
    """
    Contract document requirements that define what documents are needed for contracts.
    """
    
    # Common requirement codes for reference (not enforced)
    COMMON_CODES = [
        ('CONTRACT_TEMPLATE', 'Contract Template'),
        ('TERMS_CONDITIONS', 'Terms & Conditions'),
        ('PRICING_SCHEDULE', 'Pricing Schedule'),
        ('DELIVERY_SCHEDULE', 'Delivery Schedule'),
        ('PAYMENT_TERMS', 'Payment Terms'),
        ('SPECIFICATIONS', 'Technical Specifications'),
        ('LEGAL_DOCUMENTS', 'Legal Documents'),
        ('SUPPLIER_GUIDE', 'Supplier Guide'),
        ('QUALITY_STANDARDS', 'Quality Standards'),
        ('OTHER', 'Other'),
    ]
    
    code = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Unique code for the contract document requirement (e.g., 'CONTRACT_TEMPLATE', 'CUSTOM_DOC_1')"
    )
    label = models.CharField(
        max_length=200,
        help_text="Display label for the requirement"
    )
    description = models.TextField(
        help_text="Detailed description of what documents are required"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this document is mandatory for contracts"
    )
    condition_note = models.TextField(
        blank=True,
        help_text="Additional conditions or notes (e.g., 'Required for supply agreements only')"
    )
    allowed_extensions = models.JSONField(
        default=list,
        help_text="List of allowed file extensions"
    )
    max_file_size_mb = models.PositiveIntegerField(
        default=10,
        help_text="Maximum file size in MB"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this requirement is currently active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications_contract_document_requirement'
        verbose_name = 'Contract Document Requirement'
        verbose_name_plural = 'Contract Document Requirements'
        ordering = ['label']
    
    def __str__(self):
        return f"{self.label} ({'Required' if self.is_required else 'Optional'})"
    
    def get_allowed_extensions(self):
        """Get list of allowed file extensions."""
        if not self.allowed_extensions:
            return ['.pdf', '.doc', '.docx']
        return self.allowed_extensions
    
    @classmethod
    def get_common_codes(cls):
        """Return list of common requirement codes for reference."""
        return cls.COMMON_CODES
    
    @classmethod
    def get_available_codes(cls):
        """Return list of codes that are not yet used."""
        used_codes = set(cls.objects.values_list('code', flat=True))
        return [(code, name) for code, name in cls.COMMON_CODES if code not in used_codes]
    
    def clean(self):
        """Validate the model instance."""
        from django.core.exceptions import ValidationError
        import re
        
        # Validate code format (uppercase letters, numbers, and underscores only)
        if self.code:
            if not re.match(r'^[A-Z0-9_]+$', self.code):
                raise ValidationError({
                    'code': 'Code must contain only uppercase letters, numbers, and underscores (e.g., CONTRACT_TEMPLATE, CUSTOM_DOC_1)'
                })
            
            # Ensure code doesn't start or end with underscore
            if self.code.startswith('_') or self.code.endswith('_'):
                raise ValidationError({
                    'code': 'Code cannot start or end with underscore'
                })
            
            # Ensure code doesn't have consecutive underscores
            if '__' in self.code:
                raise ValidationError({
                    'code': 'Code cannot contain consecutive underscores'
                })


class ContractDocument(models.Model):
    """
    Model for managing contract documents that are sent to suppliers.
    """
    
    class DocumentType(models.TextChoices):
        CONTRACT_TEMPLATE = 'CONTRACT_TEMPLATE', 'Contract Template'
        TERMS_CONDITIONS = 'TERMS_CONDITIONS', 'Terms & Conditions'
        PRICING_SCHEDULE = 'PRICING_SCHEDULE', 'Pricing Schedule'
        DELIVERY_SCHEDULE = 'DELIVERY_SCHEDULE', 'Delivery Schedule'
        PAYMENT_TERMS = 'PAYMENT_TERMS', 'Payment Terms'
        SPECIFICATIONS = 'SPECIFICATIONS', 'Technical Specifications'
        LEGAL_DOCUMENTS = 'LEGAL_DOCUMENTS', 'Legal Documents'
        OTHER = 'OTHER', 'Other'
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        ARCHIVED = 'ARCHIVED', 'Archived'
    
    class DocumentCategory(models.TextChoices):
        STATIC = 'STATIC', 'Static Document'
        DYNAMIC = 'DYNAMIC', 'Dynamic Document'
        CONTRACT_SPECIFIC = 'CONTRACT_SPECIFIC', 'Contract Specific'
    
    # Requirement Reference
    requirement = models.ForeignKey(
        ContractDocumentRequirement,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Document requirement this document fulfills",
        null=True,
        blank=True
    )
    
    # Document Category
    category = models.CharField(
        max_length=20,
        choices=DocumentCategory.choices,
        default=DocumentCategory.STATIC,
        help_text="Category of the document"
    )
    
    # Contract Assignment
    assigned_contracts = models.ManyToManyField(
        'SupplierContract',
        through='ContractDocumentAssignment',
        related_name='assigned_documents',
        blank=True,
        help_text="Contracts this document is assigned to"
    )
    
    # Basic Information
    title = models.CharField(
        max_length=200,
        help_text="Document title"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Document description"
    )
    
    # Document File (optional for dynamic documents)
    document_file = models.FileField(
        upload_to='contract_documents/%Y/%m/',
        help_text="Contract document file (required for static documents)",
        null=True,
        blank=True
    )
    
    # Version Control
    version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Document version"
    )
    is_current_version = models.BooleanField(
        default=True,
        help_text="Is this the current version of the document?"
    )
    
    # Status and Metadata
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Document status"
    )
    
    # Effective Dates
    effective_from = models.DateField(
        help_text="Date from which this document is effective"
    )
    effective_until = models.DateField(
        null=True,
        blank=True,
        help_text="Date until which this document is effective (optional)"
    )
    
    # Created by
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_contract_documents',
        help_text="User who created this document"
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this document"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contract Document"
        verbose_name_plural = "Contract Documents"
        unique_together = ['title', 'version']
    
    def __str__(self):
        return f"{self.title} v{self.version}"
    
    def clean(self):
        """Validate the model instance."""
        from django.core.exceptions import ValidationError
        
        # Static documents must have a file
        if self.category == self.DocumentCategory.STATIC and not self.document_file:
            raise ValidationError({
                'document_file': 'Static documents must have a file attached.'
            })
        
        # Note: Dynamic documents can have files when they are used as templates
        # The validation that prevented this has been removed to allow admin uploads
    
    def save(self, *args, **kwargs):
        # Validate the instance before saving
        self.clean()
        
        # If this is set as current version, make sure other versions of same document are not current
        if self.is_current_version:
            ContractDocument.objects.filter(
                title=self.title,
                is_current_version=True
            ).exclude(pk=self.pk).update(is_current_version=False)
        super().save(*args, **kwargs)
    
    @property
    def file_size(self):
        """Get file size in human readable format."""
        if self.document_file:
            size = self.document_file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "0 B"
    
    @property
    def file_extension(self):
        """Get file extension."""
        if self.document_file:
            return self.document_file.name.split('.')[-1].upper()
        return ""


class ContractDocumentAssignment(models.Model):
    """
    Through model for assigning documents to contracts.
    """
    
    contract = models.ForeignKey(
        'SupplierContract',
        on_delete=models.CASCADE,
        related_name='document_assignments'
    )
    document = models.ForeignKey(
        ContractDocument,
        on_delete=models.CASCADE,
        related_name='contract_assignments'
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this document is required for this contract"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_contract_documents'
    )
    
    class Meta:
        unique_together = ['contract', 'document']
        verbose_name = 'Contract Document Assignment'
        verbose_name_plural = 'Contract Document Assignments'
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.document.title}"


class ContractSigning(models.Model):
    """
    Model for tracking contract document signing by suppliers.
    """
    
    class SigningStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        REVIEWED = 'REVIEWED', 'Reviewed'
        SIGNED = 'SIGNED', 'Signed'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
    
    contract = models.ForeignKey(
        'SupplierContract',
        on_delete=models.CASCADE,
        related_name='signings'
    )
    supplier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contract_signings'
    )
    status = models.CharField(
        max_length=20,
        choices=SigningStatus.choices,
        default=SigningStatus.PENDING
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    signature_file = models.FileField(
        upload_to='contract_signatures/%Y/%m/',
        blank=True,
        null=True,
        help_text="Digital signature file"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['contract', 'supplier']
        verbose_name = 'Contract Signing'
        verbose_name_plural = 'Contract Signings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.supplier.get_full_name()}"
    
    @property
    def is_signed(self):
        return self.status == self.SigningStatus.SIGNED
    
    @property
    def is_pending(self):
        return self.status == self.SigningStatus.PENDING
    
    @property
    def is_reviewed(self):
        return self.status == self.SigningStatus.REVIEWED
