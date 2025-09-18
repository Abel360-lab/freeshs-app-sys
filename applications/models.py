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
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
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
        default='',
        help_text="Business registration number"
    )
    tin_number = models.CharField(
        max_length=20,
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
        unique=True,
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
