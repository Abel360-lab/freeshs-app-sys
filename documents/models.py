"""
Document models for GCX Supplier Application Portal.
"""

import os
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from PIL import Image


def document_upload_path(instance, filename):
    """Generate upload path for documents."""
    return f"documents/{instance.application.tracking_code}/{instance.requirement.code}/{filename}"


class DocumentRequirement(models.Model):
    """
    Document requirements for supplier applications.
    """
    
    class RequirementCode(models.TextChoices):
        BUSINESS_REGISTRATION_DOCS = 'BUSINESS_REGISTRATION_DOCS', 'Business Registration Documents'
        VAT_CERTIFICATE = 'VAT_CERTIFICATE', 'VAT Certificate'
        PPA_CERTIFICATE = 'PPA_CERTIFICATE', 'PPA Certificate'
        TAX_CLEARANCE_CERT = 'TAX_CLEARANCE_CERT', 'Tax Clearance Certificate'
        PROOF_OF_OFFICE = 'PROOF_OF_OFFICE', 'Proof of Office'
        ID_MD_CEO_PARTNERS = 'ID_MD_CEO_PARTNERS', 'ID of MD/CEO/Partners'
        GCX_REGISTRATION_PROOF = 'GCX_REGISTRATION_PROOF', 'GCX Registration Proof'
        TEAM_MEMBER_ID = 'TEAM_MEMBER_ID', 'Team Member ID'
        FDA_CERT_PROCESSED_FOOD = 'FDA_CERT_PROCESSED_FOOD', 'FDA Certificate for Processed Food'
    
    code = models.SlugField(
        max_length=50,
        choices=RequirementCode.choices,
        unique=True,
        help_text="Unique code for the document requirement"
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
        help_text="Whether this document is mandatory"
    )
    condition_note = models.TextField(
        blank=True,
        help_text="Additional conditions or notes (e.g., 'Required if supplying processed foods')"
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
        db_table = 'documents_document_requirement'
        verbose_name = 'Document Requirement'
        verbose_name_plural = 'Document Requirements'
        ordering = ['label']
    
    def __str__(self):
        return f"{self.label} ({'Required' if self.is_required else 'Optional'})"
    
    def get_allowed_extensions(self):
        """Get list of allowed file extensions."""
        if not self.allowed_extensions:
            return ['.pdf', '.jpg', '.jpeg', '.png']
        return self.allowed_extensions


class DocumentUpload(models.Model):
    """
    Document uploads for applications.
    """
    
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.CASCADE,
        related_name='document_uploads',
        help_text="Application this document belongs to"
    )
    requirement = models.ForeignKey(
        DocumentRequirement,
        on_delete=models.CASCADE,
        related_name='uploads',
        help_text="Document requirement this upload satisfies"
    )
    
    # File Information
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
        ],
        help_text="Uploaded document file"
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename when uploaded"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    mime_type = models.CharField(
        max_length=100,
        help_text="MIME type of the file"
    )
    
    # Verification Information
    verified = models.BooleanField(
        default=False,
        help_text="Whether this document has been verified by staff"
    )
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        help_text="Staff member who verified this document"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this document was verified"
    )
    verifier_note = models.TextField(
        blank=True,
        help_text="Notes from the verifier"
    )
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents_document_upload'
        verbose_name = 'Document Upload'
        verbose_name_plural = 'Document Uploads'
        ordering = ['-uploaded_at']
        unique_together = ['application', 'requirement']
    
    def __str__(self):
        return f"{self.requirement.label} - {self.application.business_name}"
    
    def clean(self):
        """Validate document upload."""
        super().clean()
        
        # Check file size
        if self.file and self.file.size > self.requirement.max_file_size_mb * 1024 * 1024:
            raise ValidationError(
                f"File size exceeds maximum allowed size of {self.requirement.max_file_size_mb}MB"
            )
        
        # Check file extension
        if self.file:
            file_ext = os.path.splitext(self.file.name)[1].lower()
            if file_ext not in self.requirement.get_allowed_extensions():
                raise ValidationError(
                    f"File type {file_ext} is not allowed. Allowed types: {', '.join(self.requirement.get_allowed_extensions())}"
                )
    
    def save(self, *args, **kwargs):
        """Override save to handle file metadata."""
        if self.file and not self.pk:
            self.original_filename = self.file.name
            self.file_size = self.file.size
            
            # Get content type safely
            if hasattr(self.file, 'content_type'):
                self.mime_type = self.file.content_type
            elif hasattr(self.file, 'file') and hasattr(self.file.file, 'content_type'):
                self.mime_type = self.file.file.content_type
            else:
                # Fallback to default
                self.mime_type = 'application/octet-stream'
            
            # Validate image files
            if self.mime_type.startswith('image/'):
                try:
                    with Image.open(self.file) as img:
                        img.verify()
                except Exception as e:
                    raise ValidationError(f"Invalid image file: {str(e)}")
        
        super().save(*args, **kwargs)
    
    @property
    def file_url(self):
        """Get the URL for the uploaded file."""
        if self.file:
            return self.file.url
        return None
    
    @property
    def is_image(self):
        """Check if the uploaded file is an image."""
        return self.mime_type and self.mime_type.startswith('image/')
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0


class OutstandingDocumentRequest(models.Model):
    """
    Track requests for additional documents.
    """
    
    application = models.ForeignKey(
        'applications.SupplierApplication',
        on_delete=models.CASCADE,
        related_name='outstanding_requests',
        help_text="Application this request is for"
    )
    requirements = models.ManyToManyField(
        DocumentRequirement,
        related_name='outstanding_requests',
        help_text="Document requirements that are outstanding"
    )
    message = models.TextField(
        help_text="Message to the applicant about what documents are needed"
    )
    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='document_requests',
        help_text="Staff member who made the request"
    )
    is_resolved = models.BooleanField(
        default=False,
        help_text="Whether all requested documents have been uploaded"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When all documents were uploaded"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents_outstanding_document_request'
        verbose_name = 'Outstanding Document Request'
        verbose_name_plural = 'Outstanding Document Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Document request for {self.application.business_name}"
    
    def check_resolution(self):
        """Check if all requested documents have been uploaded and verified."""
        if self.is_resolved:
            return True
        
        # Check if all required documents are uploaded and verified
        for requirement in self.requirements.all():
            try:
                upload = DocumentUpload.objects.get(
                    application=self.application,
                    requirement=requirement
                )
                if not upload.verified:
                    return False
            except DocumentUpload.DoesNotExist:
                return False
        
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()
        return True
    
    def track_document_upload(self, requirement, document_upload):
        """Track when a document is uploaded for this request."""
        from core.models import AuditLog
        
        # Log the document upload for this specific request
        AuditLog.objects.create(
            user=None,  # No user for public upload
            action='DOCUMENT_UPLOADED_FOR_REQUEST',
            model_name='OutstandingDocumentRequest',
            object_id=str(self.pk),
            details={
                'application_tracking_code': self.application.tracking_code,
                'business_name': self.application.business_name,
                'requirement_name': requirement.label,
                'requirement_code': requirement.code,
                'document_id': document_upload.pk,
                'file_name': document_upload.original_filename,
                'file_size': document_upload.file.size if document_upload.file else 0
            }
        )
        
        # Check if this upload resolves the request
        self.check_resolution()