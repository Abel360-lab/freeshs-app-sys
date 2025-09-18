"""
Views for applications app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import SupplierApplication
from .serializers import (
    SupplierApplicationSerializer, ApplicationStatusSerializer,
    OutstandingDocumentsSerializer, ApplicationSubmitSerializer
)

User = get_user_model()


class SupplierApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing supplier applications (admin only).
    """
    queryset = SupplierApplication.objects.filter(is_deleted=False)
    serializer_class = SupplierApplicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'region', 'submitted_at']
    search_fields = ['business_name', 'email', 'tracking_code']
    ordering_fields = ['created_at', 'submitted_at', 'reviewed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter applications based on user permissions."""
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(is_deleted=False)
        return qs


def application_form_view(request):
    """
    View to display the application form.
    """
    from core.models import Region, Commodity
    from documents.models import DocumentRequirement
    
    regions = Region.objects.all().order_by('name')
    commodities = Commodity.objects.all().order_by('name')
    document_requirements = DocumentRequirement.objects.filter(is_active=True).order_by('code')
    
    context = {
        'regions': regions,
        'commodities': commodities,
        'document_requirements': document_requirements,
    }
    
    return render(request, 'application_form.html', context)


class ApplicationSubmitView(APIView):
    """
    Public view for submitting applications.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Submit a new application."""
        # Handle both form data and JSON data
        if request.content_type == 'application/json':
            data = request.data
        else:
            # Handle multipart form data
            data = request.data.copy()
            
            # Convert QueryDict to regular dict first to avoid nested lists, but preserve multiple values for commodities
            if hasattr(data, 'getlist'):
                # Debug: Check original data before conversion
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"DEBUG: Original data type: {type(data)}")
                logger.info(f"DEBUG: Original commodities getlist: {data.getlist('commodities')}")
                logger.info(f"DEBUG: Original commodities get: {data.get('commodities')}")
                
                # Create a new dict from the QueryDict
                clean_data = {}
                for key, value in data.items():
                    if key == 'commodities':
                        # Use getlist to preserve all values
                        clean_data[key] = data.getlist(key)
                    elif isinstance(value, list) and len(value) == 1 and not isinstance(value[0], (list, dict)):
                        clean_data[key] = value[0]
                    else:
                        clean_data[key] = value
                data = clean_data
                
                # Debug: Check if commodities were preserved
                if 'commodities' in data:
                    logger.info(f"DEBUG: Commodities after conversion: {data['commodities']}, type: {type(data['commodities'])}")
            
            # Convert team member data
            if 'team_member_name' in data:
                team_member_region = data.get('team_member_region')
                try:
                    team_member_region_id = int(team_member_region) if team_member_region else None
                except (ValueError, TypeError):
                    team_member_region_id = team_member_region
                
                team_member_data = {
                    'full_name': data.get('team_member_name'),
                    'address': data.get('team_member_address'),
                    'city': data.get('team_member_city'),
                    'country': data.get('team_member_country', 'Ghana'),
                    'region_id': team_member_region_id,
                    'telephone': data.get('team_member_telephone'),
                    'email': data.get('team_member_email'),
                    'id_card_type': data.get('team_member_id_type'),
                    'id_card_number': data.get('team_member_id_number')
                }
                data['team_members'] = [team_member_data]
            
            # Convert next of kin data
            if 'next_of_kin_name' in data:
                next_of_kin_data = {
                    'full_name': data.get('next_of_kin_name'),
                    'relationship': data.get('next_of_kin_relationship'),
                    'address': data.get('next_of_kin_address'),
                    'mobile': data.get('next_of_kin_mobile'),
                    'id_card_type': data.get('next_of_kin_id_type'),
                    'id_card_number': data.get('next_of_kin_id_number')
                }
                data['next_of_kin'] = [next_of_kin_data]
            
            # Convert bank account data
            bank_accounts = []
            
            # Primary bank account (required)
            if 'primary_bank_name' in data:
                primary_bank_data = {
                    'bank_name': data.get('primary_bank_name'),
                    'branch': data.get('primary_bank_branch'),
                    'account_name': data.get('primary_account_name'),
                    'account_number': data.get('primary_account_number'),
                    'account_index': 1
                }
                bank_accounts.append(primary_bank_data)
            
            # Secondary bank account (optional)
            if 'secondary_bank_name' in data and data.get('secondary_bank_name'):
                secondary_bank_data = {
                    'bank_name': data.get('secondary_bank_name'),
                    'branch': data.get('secondary_bank_branch'),
                    'account_name': data.get('secondary_account_name'),
                    'account_number': data.get('secondary_account_number'),
                    'account_index': 2
                }
                bank_accounts.append(secondary_bank_data)
            
            if bank_accounts:
                data['bank_accounts'] = bank_accounts
            
            # Convert commodity data
            commodity_ids = []
            # Check for both 'commodities' and 'commodity_ids' fields
            commodity_field = 'commodity_ids' if 'commodity_ids' in data else 'commodities'
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"DEBUG: Available fields in data: {list(data.keys())}")
            logger.info(f"DEBUG: commodity_field selected: {commodity_field}")
            logger.info(f"DEBUG: 'commodities' in data: {'commodities' in data}")
            logger.info(f"DEBUG: 'commodity_ids' in data: {'commodity_ids' in data}")
            
            if commodity_field in data:
                try:
                    # Handle both QueryDict and regular dict
                    if hasattr(data, 'getlist'):
                        raw_commodities = data.getlist(commodity_field)
                        logger.info(f"DEBUG: Using getlist() - raw_commodities: {raw_commodities}")
                    else:
                        # For regular dict, commodities might be a single value or list
                        commodities_value = data.get(commodity_field)
                        logger.info(f"DEBUG: Using get() - commodities_value: {commodities_value}, type: {type(commodities_value)}")
                        if isinstance(commodities_value, list):
                            raw_commodities = commodities_value
                        else:
                            raw_commodities = [commodities_value] if commodities_value else []
                    
                    commodity_ids = [int(x) for x in raw_commodities if x and str(x).strip()]
                    # Log for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Raw commodities: {raw_commodities}")
                    logger.info(f"Processed commodity_ids: {commodity_ids}")
                    logger.info(f"DEBUG: Final commodity_ids count: {len(commodity_ids)}")
                    
                    # Debug: Check if we're losing multiple values
                    if len(commodity_ids) == 1 and isinstance(commodities_value, str):
                        logger.warning(f"DEBUG: Only one commodity received, but frontend might have sent multiple. Check frontend FormData.")
                except (ValueError, TypeError) as e:
                    commodity_ids = []
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error processing commodities: {e}")
            
            # Handle other commodities
            other_commodities = data.get('other_commodities', '').strip()
            if other_commodities:
                # Store other commodities as a custom field
                data['other_commodities'] = other_commodities
            
            # Handle file fields - remove empty files and None values
            # Get dynamic file fields from document requirements
            from documents.models import DocumentRequirement
            file_fields = [req.code.lower() for req in DocumentRequirement.objects.filter(is_active=True)]
            logger.info(f"DEBUG: Available file fields: {file_fields}")
            logger.info(f"DEBUG: File fields in data: {[f for f in file_fields if f in data]}")
            
            # Check if FDA certificate is required based on commodities
            fda_required = False
            if 'commodity_ids' in data:
                from core.models import Commodity
                selected_commodities = Commodity.objects.filter(id__in=data['commodity_ids'])
                processed_food_commodities = selected_commodities.filter(is_processed_food=True)
                fda_required = processed_food_commodities.exists()
                
                # Also check other_commodities for processed foods
                if not fda_required and 'other_commodities' in data:
                    other_commodities = data['other_commodities'].lower()
                    processed_food_names = ['tom brown', 'palm oil']
                    fda_required = any(food in other_commodities for food in processed_food_names)
            
            logger.info(f"DEBUG: FDA certificate required: {fda_required}")
            
            for field in file_fields:
                if field in data:
                    file_value = data[field]
                    logger.info(f"DEBUG: Processing file field {field}: {type(file_value)}")
                    if hasattr(file_value, 'name'):
                        logger.info(f"DEBUG: File {field} name: {file_value.name}")
                    if hasattr(file_value, 'size'):
                        logger.info(f"DEBUG: File {field} size: {file_value.size}")
                    
                    # Special handling for FDA certificate - always keep the field, but only validate if required
                    if field == 'fda_cert_processed_food':
                        if not fda_required:
                            logger.info(f"DEBUG: FDA certificate optional, keeping field: {field}")
                            # Keep the field but don't validate it
                        elif isinstance(file_value, str) and file_value.strip() == '':
                            logger.info(f"DEBUG: FDA certificate required but not provided, keeping field for validation: {field}")
                            # Keep the field so validation can catch it
                    
                    # Check if it's an empty file (size 0 or empty name)
                    if hasattr(file_value, 'size') and file_value.size == 0:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Removing empty file field: {field} (size: {file_value.size})")
                        data.pop(field, None)
                    elif isinstance(file_value, str) and file_value.strip() == '':
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Removing empty string field: {field}")
                        data.pop(field, None)
                    elif file_value is None:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Removing None field: {field}")
                        data.pop(field, None)
                    else:
                        logger.info(f"DEBUG: Keeping file field {field}")
                else:
                    logger.info(f"DEBUG: File field {field} not in data")
            
            # Set commodity_ids if we have valid ones
            if commodity_ids:
                data['commodity_ids'] = commodity_ids
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Set commodity_ids in data: {data.get('commodity_ids')}")
            
            # Remove the original commodities field to avoid conflicts
            data.pop('commodities', None)
            
            # Fix field name mismatches and convert to integer
            if 'region' in data and 'region_id' not in data:
                region_value = data.pop('region')
                try:
                    data['region_id'] = int(region_value)
                except (ValueError, TypeError):
                    data['region_id'] = region_value  # Keep as string if conversion fails
            
            # Set default country if not provided
            if 'country' not in data:
                data['country'] = 'Ghana'
            
            # Fix terms_accepted to declaration_agreed
            if 'terms_accepted' in data and 'declaration_agreed' not in data:
                data['declaration_agreed'] = data.get('terms_accepted')
            
            # Log final data for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Final commodity_ids: {data.get('commodity_ids')}")
            logger.info(f"Final other_commodities: {data.get('other_commodities')}")
            logger.info(f"Final declaration_agreed: {data.get('declaration_agreed')}")
            logger.info(f"Data keys before serializer: {list(data.keys())}")
            logger.info(f"Commodities field removed: {'commodities' not in data}")
            
            # Log file fields after filtering
            # Get dynamic file fields from document requirements
            from documents.models import DocumentRequirement
            file_fields = [req.code.lower() for req in DocumentRequirement.objects.filter(is_active=True)]
            for field in file_fields:
                if field in data:
                    logger.info(f"File field {field}: {type(data[field])} - {data[field]}")
                else:
                    logger.info(f"File field {field}: REMOVED")
        
        # Log the exact data being sent to serializer
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Data type: {type(data)}")
        logger.info(f"Data being sent to serializer: {data}")
        logger.info(f"Commodity IDs type: {type(data.get('commodity_ids'))}")
        logger.info(f"Commodity IDs value: {data.get('commodity_ids')}")
        
        try:
            # Validate foreign key references before serializer
            from core.models import Region, Commodity
            
            # Check region exists
            if 'region_id' in data:
                try:
                    region = Region.objects.get(id=data['region_id'])
                    logger.info(f"Region validation passed: {region.name}")
                except Region.DoesNotExist:
                    logger.error(f"Region ID {data['region_id']} does not exist")
                    return JsonResponse({'error': 'Invalid region selected'}, status=400)
            
            # Check commodities exist
            if 'commodity_ids' in data and data['commodity_ids']:
                try:
                    commodities = Commodity.objects.filter(id__in=data['commodity_ids'])
                    if len(commodities) != len(data['commodity_ids']):
                        logger.error(f"Some commodity IDs do not exist: {data['commodity_ids']}")
                        return JsonResponse({'error': 'Invalid commodities selected'}, status=400)
                    logger.info(f"Commodities validation passed: {[c.name for c in commodities]}")
                except Exception as e:
                    logger.error(f"Commodity validation error: {e}")
                    return JsonResponse({'error': 'Invalid commodities selected'}, status=400)
            
            serializer = ApplicationSubmitSerializer(data=data)
            logger.info(f"Serializer created successfully")
            
            if serializer.is_valid():
                logger.info(f"Serializer validation passed")
                application = serializer.save()
                
                # Log application creation
                from core.models import AuditLog
                AuditLog.objects.create(
                    user=None,  # No user for public submission
                    action='APPLICATION_CREATED',
                    model_name='SupplierApplication',
                    object_id=str(application.pk),
                    details={
                        'application_tracking_code': application.tracking_code,
                        'business_name': application.business_name,
                        'status': application.status,
                        'submitted_via': 'public_form'
                    },
                    ip_address=AuditLog.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Send admin notification for new application
                try:
                    from core.admin_notification_service import send_admin_new_application_notification
                    admin_result = send_admin_new_application_notification(application)
                    logger.info(f"Admin notification sent for application {application.tracking_code}: {admin_result.get('success', False)}")
                except Exception as e:
                    logger.warning(f"Failed to send admin notification for application {application.tracking_code}: {str(e)}")
                
                # Generate PDF in background
                try:
                    from .background_tasks import enqueue_application_processing
                    enqueue_application_processing(application.id)
                    logger.info(f"PDF generation enqueued for application {application.id}")
                except Exception as e:
                    logger.warning(f"Failed to enqueue PDF generation for application {application.id}: {str(e)}")
                
                # Send confirmation email and SMS immediately
                try:
                    from core.utils import (
                        send_application_confirmation_sms,
                        check_missing_documents, 
                        send_outstanding_documents_email
                    )
                    from core.template_notification_service import send_template_notification
                    
                    # Send confirmation email using template
                    email_result = send_template_notification(
                        template_name="Application Submission Confirmation",
                        recipient_email=application.email,
                        application=application,
                        channel='EMAIL'
                    )
                    logger.info(f"Application confirmation email sent using template: {email_result.get('success', False)}")
                    
                    # Send SMS immediately
                    send_application_confirmation_sms(application)
                    
                    # Check for missing documents and send outstanding documents email if needed
                    missing_docs = check_missing_documents(application)
                    if missing_docs:
                        # Don't automatically change status to UNDER_REVIEW
                        # Status should remain PENDING_REVIEW until admin opens the application
                        logger.info(f"Application {application.tracking_code} has missing documents but status remains PENDING_REVIEW")
                        
                        # Send document request using template
                        # Convert DocumentRequirement objects to dict format expected by template
                        missing_docs_dict = [{'name': doc.label} for doc in missing_docs]
                        doc_result = send_template_notification(
                            template_name="Document Request Notification",
                            recipient_email=application.email,
                            application=application,
                            context_data={'missing_documents': missing_docs_dict},
                            channel='EMAIL'
                        )
                        logger.info(f"Document request email sent using template: {doc_result.get('success', False)}")
                except Exception as e:
                    # Log email errors but don't fail the submission
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Email sending failed for application {application.tracking_code}: {str(e)}")
                    missing_docs = []
                
                return Response({
                    'message': 'Application submitted successfully',
                    'tracking_code': application.tracking_code,
                    'application_id': application.id,
                    'missing_documents': len(missing_docs) > 0
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer validation failed")
                logger.error(f"Application submission errors: {serializer.errors}")
                logger.error(f"Submitted data keys: {list(data.keys())}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Exception during serializer processing: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': 'Internal server error during validation'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApplicationStatusView(APIView):
    """
    Public view for checking application status.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, tracking_code):
        """Get application status by tracking code."""
        try:
            application = SupplierApplication.objects.get(
                tracking_code=tracking_code,
                is_deleted=False
            )
            serializer = ApplicationStatusSerializer(application)
            return Response(serializer.data)
        except SupplierApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class OutstandingDocumentsView(APIView):
    """
    Public view for outstanding documents.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, tracking_code):
        """Get outstanding documents for application."""
        try:
            application = SupplierApplication.objects.get(
                tracking_code=tracking_code,
                is_deleted=False
            )
            
            if application.status not in [application.ApplicationStatus.PENDING_REVIEW, application.ApplicationStatus.UNDER_REVIEW]:
                return Response(
                    {'error': 'No outstanding documents for this application'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = OutstandingDocumentsSerializer(application)
            return Response(serializer.data)
        except SupplierApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DocumentUploadView(APIView):
    """
    Public view for uploading documents.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, tracking_code):
        """Upload document for application."""
        try:
            application = SupplierApplication.objects.get(
                tracking_code=tracking_code,
                is_deleted=False
            )
            
            if application.status not in [application.ApplicationStatus.PENDING_REVIEW, application.ApplicationStatus.UNDER_REVIEW]:
                return Response(
                    {'error': 'Cannot upload documents for this application status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({'message': 'Document uploaded successfully'})
        except SupplierApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RequestMoreDocumentsView(APIView):
    """
    Admin view for requesting more documents.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Request more documents from applicant."""
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        if application.status not in [application.ApplicationStatus.SUBMITTED, application.ApplicationStatus.UNDER_REVIEW]:
            return Response(
                {'error': 'Cannot request documents for this application status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requirement_ids = request.data.get('requirement_ids', [])
        message = request.data.get('message', '')
        
        if not requirement_ids:
            return Response(
                {'error': 'At least one requirement must be specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        application.status = application.ApplicationStatus.UNDER_REVIEW
        application.reviewed_at = timezone.now()
        application.save()
        
        return Response({'message': 'Document request sent successfully'})


class ApproveApplicationView(APIView):
    """
    Admin view for approving applications.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Approve application."""
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        if application.status != application.ApplicationStatus.UNDER_REVIEW:
            return Response(
                {'error': 'Application must be under review to approve'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all required documents are verified
        required_docs = application.document_uploads.filter(requirement__is_required=True)
        unverified_docs = required_docs.filter(verified=False)
        
        if unverified_docs.exists():
            return Response(
                {'error': f'{unverified_docs.count()} required documents not verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create supplier user account
        supplier_user = User.objects.create_user(
            email=application.email,
            username=application.email,
            first_name=application.signer_name.split()[0] if application.signer_name else '',
            last_name=' '.join(application.signer_name.split()[1:]) if application.signer_name and len(application.signer_name.split()) > 1 else '',
            role=User.Role.SUPPLIER,
            is_active=True
        )
        
        # Set a temporary password
        temp_password = User.objects.make_random_password()
        supplier_user.set_password(temp_password)
        supplier_user.save()
        
        # Update application
        application.status = application.ApplicationStatus.APPROVED
        application.decided_at = timezone.now()
        application.supplier_user = supplier_user
        application.save()
        
        # Send approval email
        from core.utils import send_approval_email
        send_approval_email(application, supplier_user, temp_password)
        
        return Response({
            'message': 'Application approved successfully',
            'supplier_user_id': supplier_user.id
        })


class RejectApplicationView(APIView):
    """
    Admin view for rejecting applications.
    """
    permission_classes = [IsAuthenticated]


class ApplicationPDFDownloadView(View):
    """
    View to download application PDF.
    """
    
    def get(self, request, pk):
        """Download PDF for an application."""
        try:
            application = SupplierApplication.objects.get(pk=pk)
            
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
            
        except SupplierApplication.DoesNotExist:
            return HttpResponse(
                'Application not found',
                status=404
            )
        except Exception as e:
            logger.error(f"Error downloading PDF for application {pk}: {str(e)}")
            return HttpResponse(
                'Error downloading PDF',
                status=500
            )


class ApplicationPDFGenerateView(View):
    """
    View to generate application PDF.
    """
    
    def get(self, request, pk):
        """Generate PDF for an application."""
        try:
            application = SupplierApplication.objects.get(pk=pk)
            
            # Generate PDF using the PDF service
            from .pdf_service import ApplicationPDFService
            pdf_service = ApplicationPDFService()
            pdf_path = pdf_service.generate_application_pdf(application)
            
            if pdf_path:
                # Redirect to the download view
                from django.urls import reverse
                return HttpResponseRedirect(
                    reverse('applications:application-pdf', kwargs={'pk': pk})
                )
            else:
                return HttpResponse(
                    'Failed to generate PDF',
                    status=500
                )
            
        except SupplierApplication.DoesNotExist:
            return HttpResponse(
                'Application not found',
                status=404
            )
        except Exception as e:
            logger.error(f"Error generating PDF for application {pk}: {str(e)}")
            return HttpResponse(
                'Error generating PDF',
                status=500
            )


def application_success_view(request):
    """
    Success page after application submission.
    Only accessible with valid tracking code from recent submission.
    """
    tracking_code = request.GET.get('tracking_code')
    
    if not tracking_code:
        # Redirect to application form if no tracking code
        return redirect('applications:application-form')
    
    try:
        application = get_object_or_404(SupplierApplication, tracking_code=tracking_code)
        
        # Check if application was submitted recently (within last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        # If submitted_at is None, use created_at as fallback
        submission_time = application.submitted_at or application.created_at
        
        if submission_time < timezone.now() - timedelta(hours=24):
            # Redirect to application form if too old
            return redirect('applications:application-form')
        
        # Get commodities
        commodities = []
        if application.commodities_to_supply.exists():
            commodities = [c.name for c in application.commodities_to_supply.all()]
        
        context = {
            'tracking_code': tracking_code,
            'reference_number': application.tracking_code,  # Use tracking_code as reference_number
            'business_email': application.email,
            'business_name': application.business_name,
            'business_type': application.business_type,
            'registration_number': application.registration_number,
            'tin_number': application.tin_number,
            'submitted_at': application.submitted_at,
            'signed_at': application.signed_at,
            'status': 'Pending Review',  # Always show Pending Review on success page
            'commodities': commodities,
            'other_commodities': application.other_commodities,
            'region': application.region.name if application.region else 'Not specified',
            'telephone': application.telephone,
            'physical_address': application.physical_address,
            'city': application.city,
            'warehouse_location': application.warehouse_location,
        }
        
        return render(request, 'applications/application_success_professional.html', context)
        
    except SupplierApplication.DoesNotExist:
        # Redirect to application form if application not found
        return redirect('applications:application-form')