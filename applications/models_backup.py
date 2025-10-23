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


class StoreReceiptVoucher(models.Model):
    """
    Model for storing Store Receipt Voucher (SRV) details.
    """
    
    class SRVStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        PROCESSED = 'PROCESSED', 'Processed'
    
    # Related contract
    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        related_name='srvs',
        help_text="Associated contract"
    )
    
    # SRV details
    srv_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique SRV number"
    )
    srv_date = models.DateField(
        help_text="SRV date"
    )
    description = models.TextField(
        help_text="SRV description"
    )
    
    # Delivery details
    delivery_location = models.CharField(
        max_length=200,
        help_text="Delivery location"
    )
    delivery_date = models.DateField(
        help_text="Expected delivery date"
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual delivery date"
    )
    
    # Items and quantities
    items_description = models.TextField(
        help_text="Description of items"
    )
    total_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total quantity"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure"
    )
    
    # Financial details
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total amount"
    )
    currency = models.CharField(
        max_length=3,
        default='GHS',
        help_text="Currency"
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=SRVStatus.choices,
        default=SRVStatus.PENDING,
        help_text="SRV status"
    )
    
    # Supporting documents
    srv_document = models.FileField(
        upload_to='srvs/%Y/%m/',
        null=True,
        blank=True,
        help_text="SRV document"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_srvs',
        help_text="Admin who created the SRV"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Store Receipt Voucher"
        verbose_name_plural = "Store Receipt Vouchers"
    
    def __str__(self):
        return f"SRV {self.srv_number} - {self.contract.contract_number}"
    
    def save(self, *args, **kwargs):
        """Calculate total amount before saving."""
        if self.unit_price and self.total_quantity:
            self.total_amount = self.unit_price * self.total_quantity
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """
    Model for storing invoice details.
    """
    
    class InvoiceStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent'
        PAID = 'PAID', 'Paid'
        OVERDUE = 'OVERDUE', 'Overdue'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class PaymentTerms(models.TextChoices):
        NET_15 = 'NET_15', 'Net 15'
        NET_30 = 'NET_30', 'Net 30'
        NET_45 = 'NET_45', 'Net 45'
        NET_60 = 'NET_60', 'Net 60'
        IMMEDIATE = 'IMMEDIATE', 'Immediate'
    
    # Related SRV
    srv = models.ForeignKey(
        StoreReceiptVoucher,
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Associated SRV"
    )
    
    # Invoice details
    invoice_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique invoice number"
    )
    invoice_date = models.DateField(
        help_text="Invoice date"
    )
    due_date = models.DateField(
        help_text="Payment due date"
    )
    
    # Financial details
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Subtotal amount"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tax rate percentage"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Tax amount"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total invoice amount"
    )
    currency = models.CharField(
        max_length=3,
        default='GHS',
        help_text="Currency"
    )
    
    # Payment details
    payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.choices,
        default=PaymentTerms.NET_30,
        help_text="Payment terms"
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Amount paid"
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date payment was received"
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        help_text="Invoice status"
    )
    
    # Supporting documents
    invoice_document = models.FileField(
        upload_to='invoices/%Y/%m/',
        null=True,
        blank=True,
        help_text="Invoice document"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        help_text="Admin who created the invoice"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.srv.srv_number}"
    
    def save(self, *args, **kwargs):
        """Calculate amounts before saving."""
        # Calculate tax amount
        if self.subtotal and self.tax_rate:
            self.tax_amount = self.subtotal * (self.tax_rate / 100)
        
        # Calculate total amount
        self.total_amount = self.subtotal + self.tax_amount
        
        # Check if invoice is overdue
        if self.due_date and timezone.now().date() > self.due_date and self.status != self.InvoiceStatus.PAID:
            self.status = self.InvoiceStatus.OVERDUE
        
        super().save(*args, **kwargs)
    
    def is_overdue(self):
        """Check if invoice is overdue."""
        if self.due_date and self.status != self.InvoiceStatus.PAID:
            return timezone.now().date() > self.due_date
        return False
    
    def remaining_amount(self):
        """Calculate remaining amount to be paid."""
        return self.total_amount - self.paid_amount


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
    
    # Delivery location - can be either from contract or direct selection
    contract_commodity = models.ForeignKey(
        ContractCommodity,
        on_delete=models.CASCADE,
        related_name='deliveries',
        null=True,
        blank=True,
        help_text="Associated contract commodity (if from contract)"
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
    delivery_commodity = models.ForeignKey(
        'core.Commodity',
        on_delete=models.PROTECT,
        related_name='deliveries',
        null=True,
        blank=True,
        help_text="Commodity that was delivered"
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
    
    # Quantities delivered
    quantity_delivered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Actual quantity delivered"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        help_text="Unit of measure"
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
            return f"Delivery {self.serial_number} - {self.delivery_commodity.name} to {self.delivery_school.name}"
    
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
        """Get the commodity name for this delivery."""
        if self.contract_commodity:
            return self.contract_commodity.commodity.name
        else:
            return self.delivery_commodity.name


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
        help_text="Supplier who created the SRV"
    )
    
    # Delivery Information
    delivery_region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        help_text="Region where goods were delivered"
    )
    delivery_school = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        help_text="School where goods were delivered"
    )
    
    # Commodity Information
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
        help_text="Name of person who received the goods"
    )
    received_by_designation = models.CharField(
        max_length=100,
        help_text="Designation of person who received the goods"
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
        help_text="Supplier who created the invoice"
    )
    
    # Client Information
    client_region = models.ForeignKey(
        'core.Region',
        on_delete=models.PROTECT,
        help_text="Client region"
    )
    client_school = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        help_text="Client school"
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
        help_text="Commodity invoiced"
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
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price"
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
