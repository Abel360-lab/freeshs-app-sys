"""
Review models for GCX Supplier Application Portal.
"""

from django.db import models
from django.core.exceptions import ValidationError


class ReviewComment(models.Model):
    """
    Comments made during application review.
    """
    
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.CASCADE,
        related_name='review_comments',
        help_text="Application being reviewed"
    )
    reviewer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='review_comments',
        help_text="User who made the comment"
    )
    comment = models.TextField(
        help_text="Review comment"
    )
    is_internal = models.BooleanField(
        default=True,
        help_text="Whether this is an internal comment (not visible to applicant)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_review_comment'
        verbose_name = 'Review Comment'
        verbose_name_plural = 'Review Comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.reviewer} on {self.application.business_name}"


class ReviewChecklist(models.Model):
    """
    Checklist items for application review.
    """
    
    class ChecklistItem(models.TextChoices):
        BUSINESS_REGISTRATION = 'BUSINESS_REGISTRATION', 'Business Registration Documents'
        VAT_CERTIFICATE = 'VAT_CERTIFICATE', 'VAT Certificate'
        PPA_CERTIFICATE = 'PPA_CERTIFICATE', 'PPA Certificate'
        TAX_CLEARANCE = 'TAX_CLEARANCE', 'Tax Clearance Certificate'
        PROOF_OF_OFFICE = 'PROOF_OF_OFFICE', 'Proof of Office'
        ID_DIRECTORS = 'ID_DIRECTORS', 'ID of Directors/Partners'
        GCX_REGISTRATION = 'GCX_REGISTRATION', 'GCX Registration Proof'
        TEAM_MEMBER_ID = 'TEAM_MEMBER_ID', 'Team Member ID'
        FDA_CERTIFICATE = 'FDA_CERTIFICATE', 'FDA Certificate (if applicable)'
        BANK_ACCOUNT = 'BANK_ACCOUNT', 'Bank Account Information'
        CONTACT_INFO = 'CONTACT_INFO', 'Contact Information'
        BUSINESS_DETAILS = 'BUSINESS_DETAILS', 'Business Details'
        TEAM_MEMBERS = 'TEAM_MEMBERS', 'Team Members'
        NEXT_OF_KIN = 'NEXT_OF_KIN', 'Next of Kin'
        DECLARATION = 'DECLARATION', 'Declaration Agreement'
    
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.CASCADE,
        related_name='review_checklist',
        help_text="Application being reviewed"
    )
    reviewer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='review_checklists',
        help_text="User conducting the review"
    )
    
    # Checklist items
    business_registration = models.BooleanField(default=False)
    vat_certificate = models.BooleanField(default=False)
    ppa_certificate = models.BooleanField(default=False)
    tax_clearance = models.BooleanField(default=False)
    proof_of_office = models.BooleanField(default=False)
    id_directors = models.BooleanField(default=False)
    gcx_registration = models.BooleanField(default=False)
    team_member_id = models.BooleanField(default=False)
    fda_certificate = models.BooleanField(default=False)
    bank_account = models.BooleanField(default=False)
    contact_info = models.BooleanField(default=False)
    business_details = models.BooleanField(default=False)
    team_members = models.BooleanField(default=False)
    next_of_kin = models.BooleanField(default=False)
    declaration = models.BooleanField(default=False)
    
    # Overall assessment
    is_complete = models.BooleanField(
        default=False,
        help_text="Whether all required items are complete"
    )
    overall_notes = models.TextField(
        blank=True,
        help_text="Overall review notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_review_checklist'
        verbose_name = 'Review Checklist'
        verbose_name_plural = 'Review Checklists'
        unique_together = ['application', 'reviewer']
    
    def __str__(self):
        return f"Review checklist for {self.application.business_name} by {self.reviewer}"
    
    def clean(self):
        """Validate checklist data."""
        super().clean()
        
        # Check if all required items are complete
        required_items = [
            'business_registration', 'vat_certificate', 'ppa_certificate',
            'tax_clearance', 'proof_of_office', 'id_directors',
            'gcx_registration', 'team_member_id', 'bank_account',
            'contact_info', 'business_details', 'team_members',
            'next_of_kin', 'declaration'
        ]
        
        # Check if FDA certificate is required
        if self.application.commodities_to_supply.filter(is_processed_food=True).exists():
            required_items.append('fda_certificate')
        
        all_complete = all(getattr(self, item) for item in required_items)
        self.is_complete = all_complete
    
    def get_completion_percentage(self):
        """Get the percentage of completed items."""
        required_items = [
            'business_registration', 'vat_certificate', 'ppa_certificate',
            'tax_clearance', 'proof_of_office', 'id_directors',
            'gcx_registration', 'team_member_id', 'bank_account',
            'contact_info', 'business_details', 'team_members',
            'next_of_kin', 'declaration'
        ]
        
        # Add FDA certificate if required
        if self.application.commodities_to_supply.filter(is_processed_food=True).exists():
            required_items.append('fda_certificate')
        
        completed = sum(1 for item in required_items if getattr(self, item))
        total = len(required_items)
        
        return round((completed / total) * 100, 1) if total > 0 else 0


class ReviewDecision(models.Model):
    """
    Final review decision for applications.
    """
    
    class Decision(models.TextChoices):
        APPROVE = 'APPROVE', 'Approve'
        REJECT = 'REJECT', 'Reject'
        REQUEST_MORE_DOCS = 'REQUEST_MORE_DOCS', 'Request More Documents'
        PENDING = 'PENDING', 'Pending Review'
    
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.CASCADE,
        related_name='review_decisions',
        help_text="Application being decided on"
    )
    reviewer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='review_decisions',
        help_text="User making the decision"
    )
    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
        help_text="Review decision"
    )
    reason = models.TextField(
        help_text="Reason for the decision"
    )
    is_final = models.BooleanField(
        default=False,
        help_text="Whether this is the final decision"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_review_decision'
        verbose_name = 'Review Decision'
        verbose_name_plural = 'Review Decisions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_decision_display()} for {self.application.business_name} by {self.reviewer}"
    
    def clean(self):
        """Validate decision data."""
        super().clean()
        
        if self.decision in [self.Decision.APPROVE, self.Decision.REJECT]:
            if not self.reason:
                raise ValidationError("Reason is required for approve/reject decisions.")
            
            # Check if all required documents are verified
            if self.decision == self.Decision.APPROVE:
                required_docs = self.application.document_uploads.filter(
                    requirement__is_required=True
                )
                unverified_docs = required_docs.filter(verified=False)
                if unverified_docs.exists():
                    raise ValidationError(
                        "Cannot approve application with unverified required documents."
                    )