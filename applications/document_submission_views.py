"""
Document submission views for completing outstanding document requests.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
import logging

from applications.models import SupplierApplication
from documents.models import DocumentRequirement, DocumentUpload, OutstandingDocumentRequest
from core.models import AuditLog

logger = logging.getLogger(__name__)


def document_submission_view(request, token):
    """
    View for submitting outstanding documents using a secure token.
    """
    try:
        # Find the application by completion token
        application = get_object_or_404(
            SupplierApplication, 
            completion_token=token,
            status__in=['PENDING_REVIEW', 'UNDER_REVIEW']
        )
        
        # Get the outstanding document request (optional)
        outstanding_request = OutstandingDocumentRequest.objects.filter(
            application=application,
            is_resolved=False
        ).first()
        
        # If no outstanding request exists, get required documents directly
        if outstanding_request:
            required_docs = outstanding_request.requirements.filter(is_active=True)
        else:
            # Get all required document requirements
            from documents.models import DocumentRequirement
            required_docs = DocumentRequirement.objects.filter(is_required=True, is_active=True)
        
        # Also include FDA certificate if the application supplies processed foods
        if application.supplies_processed_foods():
            fda_requirement = DocumentRequirement.objects.filter(
                code='FDA_CERT_PROCESSED_FOOD',
                is_active=True
            ).first()
            if fda_requirement and fda_requirement not in required_docs:
                # Check if FDA certificate is already uploaded
                fda_uploaded = application.document_uploads.filter(
                    requirement=fda_requirement
                ).exists()
                if not fda_uploaded:
                    required_docs = required_docs.union(
                        DocumentRequirement.objects.filter(id=fda_requirement.id)
                    )
        
        # Get already uploaded documents
        uploaded_docs = application.document_uploads.filter(
            requirement__in=required_docs
        ).select_related('requirement')
        
        # Create a mapping of requirement to uploaded document
        uploaded_doc_map = {doc.requirement_id: doc for doc in uploaded_docs}
        
        context = {
            'application': application,
            'outstanding_request': outstanding_request,
            'required_docs': required_docs,
            'uploaded_doc_map': uploaded_doc_map,
            'token': token,
            'has_outstanding_request': outstanding_request is not None,
        }
        
        return render(request, 'applications/document_submission.html', context)
        
    except Exception as e:
        logger.error(f"Error in document submission view: {str(e)}")
        messages.error(request, 'Invalid or expired document submission link.')
        return redirect('applications:application-form')


@method_decorator(csrf_exempt, name='dispatch')
class DocumentUploadView(View):
    """
    API view for uploading documents via AJAX.
    """
    
    def post(self, request, token):
        """Handle document upload."""
        try:
            # Find the application by completion token
            application = get_object_or_404(
                SupplierApplication, 
                completion_token=token,
                status__in=['PENDING_REVIEW', 'UNDER_REVIEW']
            )
            
            # Handle multiple file uploads from the form
            uploaded_files = []
            errors = []
            
            # Process each uploaded file
            for field_name, file in request.FILES.items():
                if not file:
                    continue
                    
                # Get the requirement by the field name (requirement code in lowercase)
                from documents.models import DocumentRequirement
                try:
                    requirement = DocumentRequirement.objects.get(
                        code__iexact=field_name.upper(),
                        is_active=True
                    )
                except DocumentRequirement.DoesNotExist:
                    errors.append(f"Unknown document type: {field_name}")
                    continue
                
                # Check file size (10MB limit)
                if file.size > 10 * 1024 * 1024:
                    errors.append(f"File {file.name} is too large. Maximum size is 10MB.")
                    continue
                
                # Check if document already exists and update or create
                existing_doc = DocumentUpload.objects.filter(
                    application=application,
                    requirement=requirement
                ).first()
                
                try:
                    if existing_doc:
                        # Update existing document
                        existing_doc.file.delete(save=False)  # Delete old file
                        existing_doc.file = file
                        existing_doc.original_filename = file.name
                        existing_doc.uploaded_at = timezone.now()
                        existing_doc.verified = False  # Reset verification status
                        existing_doc.save()
                        document = existing_doc
                        action = 'updated'
                    else:
                        # Create new document
                        document = DocumentUpload.objects.create(
                            application=application,
                            requirement=requirement,
                            file=file,
                            original_filename=file.name,
                            uploaded_at=timezone.now()
                        )
                        action = 'uploaded'
                    
                    # Log the document upload
                    AuditLog.objects.create(
                        user=None,  # No user for public upload
                        action='DOCUMENT_UPLOADED',
                        model_name='DocumentUpload',
                        object_id=str(document.pk),
                        details={
                            'application_tracking_code': application.tracking_code,
                            'business_name': application.business_name,
                            'requirement': requirement.label,
                            'filename': file.name,
                            'file_size': file.size,
                            'action': action
                        },
                        ip_address=AuditLog.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    uploaded_files.append({
                        'requirement': requirement.label,
                        'filename': file.name,
                        'action': action
                    })
                    
                except Exception as e:
                    errors.append(f"Failed to upload {file.name}: {str(e)}")
            
            if not uploaded_files and not errors:
                return JsonResponse({
                    'success': False,
                    'message': 'No files were uploaded'
                }, status=400)
            
            # Check if all required documents are now uploaded
            self._check_document_completion(application, request)
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'uploaded_files': uploaded_files,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error uploading document: {str(e)}'
            }, status=500)
    
    def _check_document_completion(self, application, request):
        """Check if all required documents are uploaded and update status."""
        # Get the outstanding request
        outstanding_request = OutstandingDocumentRequest.objects.filter(
            application=application,
            is_resolved=False
        ).first()
        
        if not outstanding_request:
            return
        
        # Get all required documents for this request
        required_docs = outstanding_request.requirements.filter(is_active=True)
        uploaded_docs = application.document_uploads.filter(
            requirement__in=required_docs
        )
        
        # Check if all required documents are uploaded
        uploaded_requirement_ids = set(uploaded_docs.values_list('requirement_id', flat=True))
        required_requirement_ids = set(required_docs.values_list('id', flat=True))
        
        if uploaded_requirement_ids.issuperset(required_requirement_ids):
            # All documents uploaded, mark request as resolved
            outstanding_request.is_resolved = True
            outstanding_request.resolved_at = timezone.now()
            outstanding_request.save()
            
            # Update application status to SUBMITTED
            old_status = application.status
            application.status = 'SUBMITTED'
            application.save()
            
            # Log the status change
            AuditLog.objects.create(
                user=None,
                action='STATUS_CHANGED',
                model_name='SupplierApplication',
                object_id=str(application.pk),
                details={
                    'application_tracking_code': application.tracking_code,
                    'business_name': application.business_name,
                    'old_status': old_status,
                    'new_status': application.status,
                    'reason': 'all_documents_uploaded',
                    'outstanding_request_resolved': True
                },
                ip_address=AuditLog.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )


def document_submission_success(request, token):
    """
    Success page after document submission.
    """
    try:
        application = get_object_or_404(
            SupplierApplication, 
            completion_token=token
        )
        
        context = {
            'application': application,
            'token': token,
        }
        
        return render(request, 'applications/document_submission_success.html', context)
        
    except Exception as e:
        logger.error(f"Error in document submission success view: {str(e)}")
        messages.error(request, 'Invalid or expired document submission link.')
        return redirect('applications:application-form')
