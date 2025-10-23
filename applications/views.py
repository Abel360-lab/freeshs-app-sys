"""
Views for applications app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_POST
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from django.shortcuts import redirect
from .models import SupplierApplication, StoreReceiptVoucher, Waybill, Invoice, ContractDocument, ContractDocumentAssignment, ContractSigning
from documents.models import DocumentRequirement, OutstandingDocumentRequest, DocumentUpload
from core.models import AuditLog

logger = logging.getLogger(__name__)
from .serializers import (
    SupplierApplicationSerializer, ApplicationStatusSerializer,
    OutstandingDocumentsSerializer, ApplicationSubmitSerializer
)
from .forms import SRVCreationForm, WaybillCreationForm, InvoiceCreationForm

User = get_user_model()


def supplier_account_activated_required(view_func):
    """
    Decorator to ensure supplier account is activated (application approved).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not request.user.is_supplier:
            messages.error(request, 'Access denied. This area is for suppliers only.')
            return redirect('applications:backoffice-dashboard')
        
        # Check if user has an approved application
        try:
            application = SupplierApplication.objects.get(user=request.user)
            if application.status != SupplierApplication.ApplicationStatus.APPROVED:
                messages.error(
                    request, 
                    'Your account is not activated yet. Please wait for your application to be approved by the administrator.'
                )
                return redirect('accounts:dashboard')
        except SupplierApplication.DoesNotExist:
            messages.error(
                request, 
                'No application found for your account. Please contact the administrator.'
            )
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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
    
    regions = Region.objects.filter(is_active=True).order_by('name')
    commodities = Commodity.objects.filter(is_active=True).order_by('name')
    document_requirements = DocumentRequirement.objects.filter(is_active=True).order_by('code')
    
    context = {
        'regions': regions,
        'commodities': commodities,
        'document_requirements': document_requirements,
    }
    
    return render(request, 'application_form.html', context)


@method_decorator(csrf_exempt, name='dispatch')
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
                
                # Create user account for the applicant (optimized)
                from accounts.models import User
                import secrets
                import string
                
                # Generate a temporary password
                def generate_temp_password(length=12):
                    characters = string.ascii_letters + string.digits + "!@#$%^&*"
                    return ''.join(secrets.choice(characters) for _ in range(length))
                
                temp_password = generate_temp_password()
                
                # Check if user already exists (single query)
                try:
                    user = User.objects.get(email=application.email)
                    user_created = False
                    logger.info(f"User account already exists for email {application.email}")
                    
                    # For existing users, update their information if needed
                    user.first_name = application.signer_name.split(' ')[0] if application.signer_name else user.first_name
                    user.last_name = ' '.join(application.signer_name.split(' ')[1:]) if application.signer_name and ' ' in application.signer_name else user.last_name
                    user.phone_number = application.telephone
                    user.save(update_fields=['first_name', 'last_name', 'phone_number'])
                    
                except User.DoesNotExist:
                    # Create new user with optimized fields
                    user = User.objects.create(
                        email=application.email,
                        username=application.email,
                        first_name=application.signer_name.split(' ')[0] if application.signer_name else '',
                        last_name=' '.join(application.signer_name.split(' ')[1:]) if application.signer_name and ' ' in application.signer_name else '',
                        phone_number=application.telephone,
                        role=User.Role.SUPPLIER,
                        is_active=False,  # Account inactive until admin activates
                        is_staff=False,
                        is_superuser=False,
                        must_change_password=True,  # User must change password on first login
                    )
                    user.set_password(temp_password)
                    user.save()
                    user_created = True
                    logger.info(f"Created new user account for application {application.tracking_code}")
                
                # Link application to user (single update)
                application.user = user
                application.save(update_fields=['user'])
                
                # Log application creation
                from core.models import AuditLog
                AuditLog.objects.create(
                    user=user if user_created else None,
                    action='APPLICATION_CREATED',
                    model_name='SupplierApplication',
                    object_id=str(application.pk),
                    details={
                        'application_tracking_code': application.tracking_code,
                        'business_name': application.business_name,
                        'status': application.status,
                        'submitted_via': 'public_form',
                        'user_created': user_created,
                        'user_id': user.id if user else None
                    },
                    ip_address=AuditLog.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Send notifications in background (non-blocking)
                try:
                    import threading
                    
                    def send_notifications_background():
                        try:
                            # Send admin notification
                            from core.admin_notification_service import send_admin_new_application_notification
                            admin_result = send_admin_new_application_notification(application)
                            logger.info(f"Admin notification sent for application {application.tracking_code}: {admin_result.get('success', False)}")
                            
                            # Send confirmation email and SMS
                            from core.utils import send_application_confirmation_sms
                            from core.template_notification_service import send_template_notification
                            
                            # Send confirmation email using template
                            email_result = send_template_notification(
                                template_name="Application Submission Confirmation",
                                recipient_email=application.email,
                                application=application,
                                context_data={
                                    'temporary_password': temp_password,
                                    'user_created': user_created,
                                    'user_email': user.email,
                                    'login_url': f"{settings.FRONTEND_PUBLIC_URL}/accounts/login/"
                                },
                                channel='EMAIL'
                            )
                            logger.info(f"Application confirmation email sent using template: {email_result.get('success', False)}")
                            
                            # Send SMS
                            send_application_confirmation_sms(application)
                            logger.info(f"Confirmation SMS sent to {application.telephone} for application {application.tracking_code}")
                            
                            # Check for missing documents and send document request if needed
                            from core.utils import check_missing_documents
                            missing_docs = check_missing_documents(application)
                            if missing_docs:
                                logger.info(f"Application {application.tracking_code} has missing documents but status remains PENDING_REVIEW")
                                
                                # Convert DocumentRequirement objects to dict format expected by template
                                missing_docs_dict = [{'name': doc.label} for doc in missing_docs]
                                
                                # Send document request using template
                                doc_result = send_template_notification(
                                    template_name="Document Request Notification",
                                    recipient_email=application.email,
                                    application=application,
                                    context_data={'missing_documents': missing_docs_dict},
                                    channel='EMAIL'
                                )
                                logger.info(f"Document request email sent using template: {doc_result.get('success', False)}")
                            
                            # Generate PDF in background
                            from .background_tasks import enqueue_application_processing
                            enqueue_application_processing(application.id)
                            logger.info(f"PDF generation enqueued for application {application.id}")
                            
                        except Exception as e:
                            logger.error(f"Background notification processing failed for application {application.tracking_code}: {str(e)}")
                    
                    # Start background thread
                    thread = threading.Thread(target=send_notifications_background, daemon=True)
                    thread.start()
                    logger.info(f"Background notification thread started for application {application.tracking_code}")
                    
                except Exception as e:
                    logger.warning(f"Failed to start background notifications for application {application.tracking_code}: {str(e)}")
                
                # Prepare response data
                response_data = {
                    'message': 'Application submitted successfully',
                    'tracking_code': application.tracking_code,
                    'application_id': application.id,
                    'missing_documents': False,  # Will be determined in background
                    'user_created': user_created,
                }
                
                # Provide appropriate login guidance
                if user_created:
                    # New user - provide temporary password
                    response_data['login_credentials'] = {
                        'email': application.email,
                        'temporary_password': temp_password,
                        'login_url': '/accounts/login/',
                        'message': 'A new account has been created for you. Use the temporary password below to log in for the first time.'
                    }
                else:
                    # Existing user - provide login guidance
                    response_data['login_credentials'] = {
                        'email': application.email,
                        'temporary_password': None,
                        'login_url': '/accounts/login/',
                        'message': 'Your account already exists. Please use your existing login credentials to access your dashboard.'
                    }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer validation failed")
                logger.error(f"Application submission errors: {serializer.errors}")
                logger.error(f"Submitted data keys: {list(data.keys())}")
                
                # Format errors for better user experience
                formatted_errors = {}
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        # Join multiple errors for the same field
                        formatted_errors[field] = ' '.join([str(error) for error in errors])
                    else:
                        formatted_errors[field] = str(errors)
                
                return Response(formatted_errors, status=status.HTTP_400_BAD_REQUEST)
                
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
        
        # Check if user was created for this application
        user_created = application.user is not None
        login_credentials = None
        
        if user_created and application.user:
            # User account was already created during application submission by the signal
            # The temporary password was sent via email notification
            login_credentials = {
                'email': application.user.email,
                'temporary_password': '******',  # Password was sent via email
                'login_url': '/accounts/login/',
                'password_sent_via_email': True  # Flag to show that password was sent via email
            }
        
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
            'user_created': user_created,
            'login_credentials': login_credentials,
        }
        
        return render(request, 'application_success.html', context)
        
    except SupplierApplication.DoesNotExist:
        # Redirect to application form if application not found
        return redirect('applications:application-form')


# Supplier-specific views (authenticated users only)
@login_required
def supplier_applications_list(request):
    """List all applications for the logged-in supplier."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('accounts:login')
    
    applications = SupplierApplication.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'applications': applications,
        'user': request.user,
        'title': 'My Applications'
    }
    
    return render(request, 'accounts/supplier_applications_list_new.html', context)


@login_required
def supplier_application_detail(request, pk):
    """Detail view for a specific application (supplier access only)."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('accounts:login')
    
    application = get_object_or_404(SupplierApplication, pk=pk, user=request.user)
    
    # Get commodities
    commodities = []
    if application.commodities_to_supply.exists():
        commodities = [c.name for c in application.commodities_to_supply.all()]
    
    # Get outstanding document requests
    outstanding_requests = OutstandingDocumentRequest.objects.filter(
        application=application, 
        is_resolved=False
    )
    
    # Get uploaded documents
    uploaded_documents = DocumentUpload.objects.filter(application=application)
    
    # Get missing documents (required documents not yet uploaded)
    from documents.models import DocumentRequirement
    all_required_docs = DocumentRequirement.objects.filter(is_active=True)
    uploaded_doc_requirements = set(uploaded_documents.values_list('requirement_id', flat=True))
    missing_documents = all_required_docs.exclude(id__in=uploaded_doc_requirements)
    
    # Create comprehensive timeline
    timeline_events = []
    
    # 1. Application creation
    timeline_events.append({
        'type': 'application_created',
        'timestamp': application.created_at,
        'title': 'Application Submitted',
        'description': f'Application {application.tracking_code} was submitted successfully for {application.business_name}',
        'user': application.user,
        'icon': 'fas fa-file-alt',
        'color': 'primary',
        'details': {
            'business_name': application.business_name,
            'email': application.email,
            'region': application.region.name if application.region else 'Not specified',
            'commodities_count': application.commodities_to_supply.count()
        }
    })
    
    # 2. Account creation (if user exists)
    if application.user:
        timeline_events.append({
            'type': 'account_created',
            'timestamp': application.created_at,
            'title': 'Supplier Account Created',
            'description': f'User account created for {application.user.email} to track application progress',
            'user': application.user,
            'icon': 'fas fa-user-plus',
            'color': 'info',
            'details': {
                'email': application.user.email,
                'account_status': 'Active' if application.user.is_active else 'Pending Activation'
            }
        })
    
    # 3. Document uploads with detailed information
    for doc in uploaded_documents:
        file_size_mb = round(doc.file_size / (1024 * 1024), 2) if doc.file_size else 0
        timeline_events.append({
            'type': 'document_uploaded',
            'timestamp': doc.uploaded_at,
            'title': f'Document Uploaded: {doc.requirement.label}',
            'description': f'File "{doc.original_filename}" ({file_size_mb} MB) was uploaded',
            'user': None,  # Document uploads don't have uploaded_by field
            'icon': 'fas fa-upload',
            'color': 'success',
            'details': {
                'filename': doc.original_filename,
                'file_size': f"{file_size_mb} MB",
                'file_type': doc.mime_type,
                'requirement': doc.requirement.label
            }
        })
        
        # 4. Document verifications
        if doc.verified and doc.verified_at:
            timeline_events.append({
                'type': 'document_verified',
                'timestamp': doc.verified_at,
                'title': f'Document Verified: {doc.requirement.label}',
                'description': f'File "{doc.original_filename}" was verified and approved by admin',
                'user': doc.verified_by,
                'icon': 'fas fa-check-circle',
                'color': 'success',
                'details': {
                    'filename': doc.original_filename,
                    'verified_by': doc.verified_by.email if doc.verified_by else 'System',
                    'verifier_note': doc.verifier_note if doc.verifier_note else 'No notes provided'
                }
            })
    
    # 5. Status changes with detailed information
    if application.updated_at and application.updated_at != application.created_at:
        status_display = application.get_status_display()
        status_icons = {
            'PENDING_REVIEW': 'fas fa-clock',
            'UNDER_REVIEW': 'fas fa-search',
            'APPROVED': 'fas fa-check-circle',
            'REJECTED': 'fas fa-times-circle',
        }
        status_colors = {
            'PENDING_REVIEW': 'warning',
            'UNDER_REVIEW': 'info',
            'APPROVED': 'success',
            'REJECTED': 'danger',
        }
        
        timeline_events.append({
            'type': 'status_change',
            'timestamp': application.updated_at,
            'title': f'Status Changed to {status_display}',
            'description': f'Application status was updated to {status_display}',
            'user': None,  # System action
            'icon': status_icons.get(application.status, 'fas fa-flag'),
            'color': status_colors.get(application.status, 'secondary'),
            'details': {
                'previous_status': 'Submitted',
                'new_status': status_display,
                'reviewer_comment': application.reviewer_comment if application.reviewer_comment else 'No comment provided'
            }
        })
    
    # 6. Review actions
    if application.reviewed_at:
        timeline_events.append({
            'type': 'application_reviewed',
            'timestamp': application.reviewed_at,
            'title': 'Application Under Review',
            'description': f'Application was reviewed by admin staff',
            'user': None,  # Could be enhanced to track reviewer
            'icon': 'fas fa-search',
            'color': 'info',
            'details': {
                'reviewed_at': application.reviewed_at.strftime('%Y-%m-%d %H:%M'),
                'reviewer_comment': application.reviewer_comment if application.reviewer_comment else 'No comment provided'
            }
        })
    
    # 7. Decision actions
    if application.decided_at:
        decision_type = 'Approved' if application.status == 'APPROVED' else 'Rejected'
        timeline_events.append({
            'type': 'application_decided',
            'timestamp': application.decided_at,
            'title': f'Application {decision_type}',
            'description': f'Final decision: {decision_type}',
            'user': None,  # Could be enhanced to track decision maker
            'icon': 'fas fa-gavel',
            'color': 'success' if application.status == 'APPROVED' else 'danger',
            'details': {
                'decision': decision_type,
                'decided_at': application.decided_at.strftime('%Y-%m-%d %H:%M'),
                'reviewer_comment': application.reviewer_comment if application.reviewer_comment else 'No comment provided'
            }
        })
    
    # 8. Audit logs for other actions
    from core.models import AuditLog
    audit_logs = AuditLog.objects.filter(
        object_id=str(application.pk),
        model_name='SupplierApplication'
    ).exclude(action='APPLICATION_CREATED').order_by('created_at')
    
    for log in audit_logs:
        action_icons = {
            'APPLICATION_APPROVED': 'fas fa-check-circle',
            'APPLICATION_REJECTED': 'fas fa-times-circle',
            'APPLICATION_UNDER_REVIEW': 'fas fa-search',
            'DOCUMENT_REQUESTED': 'fas fa-file-upload',
            'ACCOUNT_ACTIVATED': 'fas fa-user-check',
            'ACCOUNT_DEACTIVATED': 'fas fa-user-times',
            'DOCUMENT_UPLOADED': 'fas fa-upload',
            'DOCUMENT_VERIFIED': 'fas fa-check-circle',
        }
        
        action_colors = {
            'APPLICATION_APPROVED': 'success',
            'APPLICATION_REJECTED': 'danger',
            'APPLICATION_UNDER_REVIEW': 'info',
            'DOCUMENT_REQUESTED': 'warning',
            'ACCOUNT_ACTIVATED': 'success',
            'ACCOUNT_DEACTIVATED': 'danger',
            'DOCUMENT_UPLOADED': 'success',
            'DOCUMENT_VERIFIED': 'success',
        }
        
        # Format action title
        action_title = log.action.replace('_', ' ').title()
        if log.action == 'DOCUMENT_UPLOADED':
            action_title = 'Document Uploaded'
        elif log.action == 'DOCUMENT_VERIFIED':
            action_title = 'Document Verified'
        
        timeline_events.append({
            'type': 'audit_log',
            'timestamp': log.created_at,
            'title': action_title,
            'description': log.description or f"System action: {log.action}",
            'user': log.user,
            'icon': action_icons.get(log.action, 'fas fa-info-circle'),
            'color': action_colors.get(log.action, 'secondary'),
            'details': log.details or {}
        })
    
    # 9. Add missing documents notice if any
    if missing_documents.exists():
        timeline_events.append({
            'type': 'missing_documents',
            'timestamp': timezone.now(),
            'title': 'Missing Documents Required',
            'description': f'{missing_documents.count()} required documents are still missing',
            'user': None,
            'icon': 'fas fa-exclamation-triangle',
            'color': 'warning',
            'details': {
                'missing_count': missing_documents.count(),
                'documents': [doc.label for doc in missing_documents]
            }
        })
    
    # Sort timeline by timestamp (most recent first)
    timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate commodity counts
    total_commodities = application.commodities_to_supply.count()
    processed_commodities_count = application.commodities_to_supply.filter(is_processed_food=True).count()
    raw_commodities_count = application.commodities_to_supply.filter(is_processed_food=False).count()
    
    context = {
        'application': application,
        'commodities': commodities,
        'outstanding_requests': outstanding_requests,
        'uploaded_documents': uploaded_documents,
        'missing_documents': missing_documents,
        'timeline_events': timeline_events,
        'user': request.user,
        'title': f'Application {application.tracking_code}',
        'total_commodities': total_commodities,
        'processed_commodities_count': processed_commodities_count,
        'raw_commodities_count': raw_commodities_count,
    }
    
    return render(request, 'accounts/supplier_application_detail_new.html', context)


@login_required
def supplier_document_upload(request, pk):
    """Upload documents for a specific application (supplier access only)."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('accounts:login')
    
    application = get_object_or_404(SupplierApplication, pk=pk, user=request.user)
    
    if request.method == 'POST':
        print(f"DEBUG: POST request received for application {pk}")
        print(f"DEBUG: request.POST = {request.POST}")
        print(f"DEBUG: request.FILES = {request.FILES}")
        
        # Get the document requirement from the form
        from documents.models import DocumentRequirement
        document_requirement_id = request.POST.get('document_requirement_id')
        print(f"DEBUG: document_requirement_id = {document_requirement_id}")
        
        if not document_requirement_id:
            messages.error(request, 'No document requirement specified.')
            return redirect('applications:supplier-document-upload', pk=pk)
            
        document_requirement = get_object_or_404(DocumentRequirement, id=document_requirement_id)
        
        # Get the uploaded file
        uploaded_file = request.FILES.get('file')  # Changed from 'document' to 'file'
        print(f"DEBUG: uploaded_file = {uploaded_file}")
        
        if not uploaded_file:
            messages.error(request, 'No file selected.')
            return redirect('applications:supplier-document-upload', pk=pk)
        
        if uploaded_file:
            # Create or update document upload
            document_upload, created = DocumentUpload.objects.get_or_create(
                application=application,
                requirement=document_requirement,
                defaults={
                    'file': uploaded_file,
                    'original_filename': uploaded_file.name,
                    'file_size': uploaded_file.size,
                    'mime_type': uploaded_file.content_type,
                }
            )
            
            if not created:
                # Update existing document
                document_upload.file = uploaded_file
                document_upload.original_filename = uploaded_file.name
                document_upload.file_size = uploaded_file.size
                document_upload.mime_type = uploaded_file.content_type
                document_upload.uploaded_by = request.user
                document_upload.save()
            
            messages.success(request, f'Document "{document_requirement.label}" uploaded successfully.')
            print(f"DEBUG: Document uploaded successfully - {document_upload.id}")
            
            # Log the upload
            from core.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='DOCUMENT_UPLOADED',
                model_name='DocumentUpload',
                object_id=str(document_upload.id),
                details={
                    'application_tracking_code': application.tracking_code,
                    'document_requirement': document_requirement.label,
                    'original_filename': uploaded_file.name,
                    'file_size': uploaded_file.size,
                },
                ip_address=AuditLog.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return redirect('applications:supplier-application-detail', pk=pk)
        else:
            messages.error(request, 'Please select a file to upload.')
            print("DEBUG: No file selected")
    
    # Get outstanding document requests for this application
    outstanding_requests = OutstandingDocumentRequest.objects.filter(
        application=application, 
        is_resolved=False
    )
    
    # Get uploaded documents
    uploaded_documents = DocumentUpload.objects.filter(application=application)
    
    # Get missing documents (required documents not yet uploaded)
    from documents.models import DocumentRequirement
    all_required_docs = DocumentRequirement.objects.filter(is_active=True)
    uploaded_doc_requirements = set(uploaded_documents.values_list('requirement_id', flat=True))
    missing_documents = all_required_docs.exclude(id__in=uploaded_doc_requirements)
    
    context = {
        'application': application,
        'outstanding_requests': outstanding_requests,
        'uploaded_documents': uploaded_documents,
        'missing_documents': missing_documents,
        'user': request.user,
        'title': f'Upload Documents - {application.tracking_code}'
    }
    
    return render(request, 'accounts/supplier_document_upload_new.html', context)


@login_required
def supplier_general_document_upload(request):
    """General document upload page for suppliers - shows all applications."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('accounts:login')
    
    # Get all applications for this user
    applications = SupplierApplication.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'applications': applications,
        'user': request.user,
        'title': 'Upload Documents'
    }
    
    return render(request, 'accounts/supplier_general_document_upload.html', context)


@login_required
def supplier_direct_document_upload(request, pk):
    """Handle direct document upload via AJAX from application detail page."""
    if not request.user.is_supplier:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        application = get_object_or_404(SupplierApplication, pk=pk, user=request.user)
        
        # Get the document requirement ID and file
        document_requirement_id = request.POST.get('document_requirement_id')
        uploaded_file = request.FILES.get('file')
        
        if not document_requirement_id:
            return JsonResponse({'success': False, 'error': 'No document requirement specified'})
        
        if not uploaded_file:
            return JsonResponse({'success': False, 'error': 'No file selected'})
        
        document_requirement = get_object_or_404(DocumentRequirement, id=document_requirement_id)
        
        # Create or update the document upload
        document_upload, created = DocumentUpload.objects.get_or_create(
            application=application,
            requirement=document_requirement,
            defaults={
                'file': uploaded_file,
                'original_filename': uploaded_file.name,
                'file_size': uploaded_file.size,
            }
        )
        
        if not created:
            # Update existing document
            document_upload.file = uploaded_file
            document_upload.original_filename = uploaded_file.name
            document_upload.file_size = uploaded_file.size
            document_upload.verified = False
            document_upload.verified_at = None
            document_upload.verified_by = None
            document_upload.save()
        
        # Log the upload
        AuditLog.objects.create(
            user=request.user,
            action='DOCUMENT_UPLOADED',
            model_name='DocumentUpload',
            object_id=str(document_upload.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'document_requirement': document_requirement.label,
                'filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'upload_method': 'direct_upload'
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Document "{document_requirement.label}" uploaded successfully',
            'document': {
                'id': document_upload.id,
                'requirement_label': document_requirement.label,
                'filename': document_upload.original_filename,
                'uploaded_at': document_upload.uploaded_at.isoformat(),
                'file_url': document_upload.file.url
            }
        })
        
    except Exception as e:
        logger.error(f"Error in direct document upload: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Upload failed. Please try again.'}, status=500)


@login_required
@supplier_account_activated_required
def supplier_contracts(request):
    """View for suppliers to see their contracts."""
    from .models import SupplierContract, ContractAcceptance
    
    # Get contracts for this supplier's application
    contracts = SupplierContract.objects.filter(
        application__user=request.user
    ).select_related('application').prefetch_related('contract_commodities__commodity', 'contract_commodities__school', 'contract_commodities__region')
    
    # Get acceptance status for each contract
    contract_data = []
    for contract in contracts:
        acceptance = ContractAcceptance.objects.filter(
            contract=contract,
            supplier_user=request.user
        ).first()
        
        contract_data.append({
            'contract': contract,
            'acceptance': acceptance,
            'commodities': contract.contract_commodities.all(),
            'total_commodities': contract.contract_commodities.count(),
            'total_value': sum(cc.total_amount for cc in contract.contract_commodities.all() if cc.total_amount)
        })
    
    context = {
        'contracts': contract_data,
        'total_contracts': len(contract_data),
        'pending_contracts': len([c for c in contract_data if not c['acceptance'] or c['acceptance'].status == 'PENDING']),
        'accepted_contracts': len([c for c in contract_data if c['acceptance'] and c['acceptance'].status == 'ACCEPTED']),
    }
    
    return render(request, 'accounts/supplier_contracts.html', context)


@login_required
@supplier_account_activated_required
def supplier_contract_detail(request, pk):
    """Detailed view of a contract for suppliers."""
    from .models import SupplierContract, ContractAcceptance, ContractCommodity, ContractDocumentAssignment, ContractDocument
    
    contract = get_object_or_404(SupplierContract, pk=pk, application__user=request.user)
    
    # Get contract documents by category
    contract_assignments = ContractDocumentAssignment.objects.filter(
        contract=contract
    ).select_related('document', 'document__requirement')
    
    # Group documents by category
    static_documents = []
    dynamic_documents = []
    contract_specific_documents = []
    
    for assignment in contract_assignments:
        if assignment.document.category == 'STATIC':
            static_documents.append(assignment)
        elif assignment.document.category == 'DYNAMIC':
            dynamic_documents.append(assignment)
        elif assignment.document.category == 'CONTRACT_SPECIFIC':
            contract_specific_documents.append(assignment)
    
    # Get acceptance status
    acceptance = ContractAcceptance.objects.filter(
        contract=contract,
        supplier_user=request.user
    ).first()
    
    # Get delivery tracking for this contract
    from .models import DeliveryTracking
    deliveries = DeliveryTracking.objects.filter(
        contract_commodity__contract=contract,
        supplier_user=request.user
    ).select_related('contract_commodity__commodity', 'contract_commodity__school', 'contract_commodity__region')
    
    # Debug logging
    logger.info(f"Contract {contract.contract_number} documents: static={len(static_documents)}, dynamic={len(dynamic_documents)}, contract_specific={len(contract_specific_documents)}")
    
    context = {
        'contract': contract,
        'acceptance': acceptance,
        'deliveries': deliveries,
        'total_deliveries': deliveries.count(),
        'verified_deliveries': deliveries.filter(status='VERIFIED').count(),
        'static_documents': static_documents,
        'dynamic_documents': dynamic_documents,
        'contract_specific_documents': contract_specific_documents,
        'contract_documents': contract_assignments,
    }
    
    return render(request, 'accounts/supplier_contract_detail.html', context)


@login_required
@supplier_account_activated_required
@require_POST
def upload_signed_document(request, pk):
    """Upload signed document for a contract."""
    from .models import SupplierContract, ContractDocument, ContractDocumentAssignment
    from django.utils import timezone
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    import os
    
    try:
        contract = get_object_or_404(SupplierContract, pk=pk, application__user=request.user)
        
        document_id = request.POST.get('document_id')
        signed_file = request.FILES.get('signed_document')
        notes = request.POST.get('notes', '')
        
        if not document_id or not signed_file:
            return JsonResponse({
                'success': False,
                'message': 'Document ID and signed file are required'
            })
        
        # Get the original document
        original_doc = get_object_or_404(ContractDocument, pk=document_id)
        
        # Create a new contract-specific document with the signed version
        # Make title unique by adding contract number and timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        signed_document = ContractDocument.objects.create(
            title=f"Signed - {original_doc.title} - {contract.contract_number}",
            description=f"Signed version of {original_doc.title} for contract {contract.contract_number}",
            category='CONTRACT_SPECIFIC',
            version=f'1.0-{timestamp}',
            status='ACTIVE',
            effective_from=timezone.now().date(),
            is_current_version=True,
            document_file=signed_file,
            created_by=request.user,
            requirement=original_doc.requirement
        )
        
        # Assign to contract
        ContractDocumentAssignment.objects.create(
            contract=contract,
            document=signed_document,
            is_required=True,
            assigned_by=request.user
        )
        
        # Log the activity
        AuditLog.objects.create(
            user=request.user,
            action='DOCUMENT_UPLOADED',
            model_name='ContractDocument',
            object_id=str(signed_document.pk),
            details={'message': f'Signed document uploaded for {original_doc.title} in contract {contract.contract_number}'}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Signed document for "{original_doc.title}" has been uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading signed document for contract {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error uploading signed document: {str(e)}'
        })


@login_required
@supplier_account_activated_required
@require_POST
def accept_contract(request, pk):
    """Accept a contract."""
    from .models import SupplierContract, ContractAcceptance
    from django.utils import timezone
    
    try:
        contract = get_object_or_404(SupplierContract, pk=pk, application__user=request.user)
        
        # Check if already accepted
        existing_acceptance = ContractAcceptance.objects.filter(
            contract=contract,
            supplier_user=request.user
        ).first()
        
        if existing_acceptance and existing_acceptance.status == 'ACCEPTED':
            return JsonResponse({
                'success': False,
                'message': 'Contract has already been accepted'
            })
        
        # Get form data
        terms_accepted = request.POST.get('terms_accepted') == 'on'
        notes = request.POST.get('notes', '')
        
        if not terms_accepted:
            return JsonResponse({
                'success': False,
                'message': 'You must accept the terms and conditions'
            })
        
        # Check if all dynamic documents have been signed (uploaded)
        from .models import ContractDocumentAssignment
        dynamic_assignments = ContractDocumentAssignment.objects.filter(
            contract=contract,
            document__category='DYNAMIC',
            is_required=True
        )
        
        contract_specific_assignments = ContractDocumentAssignment.objects.filter(
            contract=contract,
            document__category='CONTRACT_SPECIFIC',
            document__title__startswith='Signed -'
        )
        
        # Check if all dynamic documents have corresponding signed versions
        for dynamic_assignment in dynamic_assignments:
            has_signed_version = contract_specific_assignments.filter(
                document__requirement=dynamic_assignment.document.requirement
            ).exists()
            
            if not has_signed_version:
                return JsonResponse({
                    'success': False,
                    'message': f'You must sign and upload "{dynamic_assignment.document.title}" before accepting the contract'
                })
        
        # Create or update acceptance
        if existing_acceptance:
            existing_acceptance.status = 'ACCEPTED'
            existing_acceptance.acceptance_date = timezone.now()
            existing_acceptance.terms_accepted = True
            existing_acceptance.notes = notes
            existing_acceptance.save()
        else:
            ContractAcceptance.objects.create(
                contract=contract,
                supplier_user=request.user,
                status='ACCEPTED',
                acceptance_date=timezone.now(),
                terms_accepted=True,
                notes=notes
            )
        
        # Update ContractSigning status to SIGNED
        from .models import ContractSigning
        contract_signing, created = ContractSigning.objects.get_or_create(
            contract=contract,
            supplier=request.user,
            defaults={'status': 'SIGNED', 'signed_at': timezone.now()}
        )
        if not created:
            contract_signing.status = 'SIGNED'
            contract_signing.signed_at = timezone.now()
            contract_signing.save()
        
        # Create audit log
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_ACCEPTED',
            model_name='ContractAcceptance',
            object_id=str(contract.pk),
            details={
                'contract_number': contract.contract_number,
                'business_name': contract.application.business_name,
                'accepted_by': request.user.get_full_name() or request.user.username,
                'notes': notes
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contract accepted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error accepting contract {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to accept contract: {str(e)}'
        })


@login_required
@require_POST
def reject_contract(request, pk):
    """Reject a contract."""
    from .models import SupplierContract, ContractAcceptance
    from django.utils import timezone
    
    try:
        contract = get_object_or_404(SupplierContract, pk=pk, application__user=request.user)
        
        # Get form data
        rejection_reason = request.POST.get('rejection_reason', '')
        notes = request.POST.get('notes', '')
        
        if not rejection_reason.strip():
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            })
        
        # Create or update acceptance
        existing_acceptance = ContractAcceptance.objects.filter(
            contract=contract,
            supplier_user=request.user
        ).first()
        
        if existing_acceptance:
            existing_acceptance.status = 'REJECTED'
            existing_acceptance.rejection_reason = rejection_reason
            existing_acceptance.notes = notes
            existing_acceptance.save()
        else:
            ContractAcceptance.objects.create(
                contract=contract,
                supplier_user=request.user,
                status='REJECTED',
                rejection_reason=rejection_reason,
                notes=notes
            )
        
        # Create audit log
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_REJECTED',
            model_name='ContractAcceptance',
            object_id=str(contract.pk),
            details={
                'contract_number': contract.contract_number,
                'business_name': contract.application.business_name,
                'rejected_by': request.user.get_full_name() or request.user.username,
                'rejection_reason': rejection_reason,
                'notes': notes
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contract rejected successfully'
        })
        
    except Exception as e:
        logger.error(f"Error rejecting contract {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to reject contract: {str(e)}'
        })


@login_required
@supplier_account_activated_required
def supplier_deliveries(request):
    """View for suppliers to manage their deliveries."""
    from .models import DeliveryTracking, SupplierContract, ContractSigning
    from core.models import Region, Commodity
    import logging
    logger = logging.getLogger(__name__)
    
    # Get deliveries for this supplier
    deliveries = DeliveryTracking.objects.filter(
        supplier_user=request.user
    ).select_related(
        'delivery_region',
        'delivery_school',
        'delivery_commodity',
        'contract',
        'contract__application',
        'contract_commodity__contract',
        'contract_commodity__commodity',
        'contract_commodity__school',
        'contract_commodity__region'
    ).prefetch_related(
        'commodities__commodity'
    ).order_by('-created_at')
    
    # Get regions and commodities for the form
    regions = Region.objects.filter(is_active=True).order_by('name')
    
    # Get signed contracts for this supplier
    # First, let's get all contracts for this user and then filter by signing status
    all_user_contracts = SupplierContract.objects.filter(
        application__user=request.user
    ).select_related('application').prefetch_related('signings')
    
    # Filter contracts that have SIGNED status
    signed_contracts = []
    for contract in all_user_contracts:
        signings = contract.signings.filter(supplier=request.user, status='SIGNED')
        if signings.exists():
            signed_contracts.append(contract)
    
    
    
    
    # Get only commodities from supplier's applications (fallback)
    from .models import SupplierApplication
    supplier_applications = SupplierApplication.objects.filter(
        user=request.user,
        status__in=['APPROVED', 'UNDER_REVIEW']
    )
    
    # Get commodities from supplier's applications only
    applied_commodities = set()
    for app in supplier_applications:
        for commodity in app.commodities_to_supply.all():
            applied_commodities.add(commodity)
    
    # Only show commodities that the supplier applied for
    commodities = list(applied_commodities)
    commodities.sort(key=lambda x: x.name)  # Sort by name
    
    # Calculate statistics
    total_deliveries = deliveries.count()
    pending_deliveries = deliveries.filter(status='PENDING').count()
    delivered = deliveries.filter(status='DELIVERED').count()
    verified = deliveries.filter(status='VERIFIED').count()
    
    context = {
        'deliveries': deliveries,
        'regions': regions,
        'commodities': commodities,
        'signed_contracts': signed_contracts,
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'delivered': delivered,
        'verified': verified,
    }
    
    return render(request, 'accounts/supplier_deliveries.html', context)


@login_required
@supplier_account_activated_required
def supplier_delivery_detail(request, pk):
    """View for suppliers to see detailed information about a specific delivery."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('applications:supplier-dashboard')
    
    from .models import DeliveryTracking
    
    # Get the delivery and ensure it belongs to this supplier
    delivery = get_object_or_404(
        DeliveryTracking.objects.select_related(
            'delivery_region',
            'delivery_school', 
            'contract',
            'contract__application',
            'verified_by',
            'rejected_by'
        ).prefetch_related(
            'commodities__commodity'
        ),
        pk=pk,
        supplier_user=request.user
    )
    
    # Get delivery commodities
    commodities = delivery.commodities.all()
    
    # Calculate total quantity and amount
    total_quantity = sum(float(commodity.quantity) for commodity in commodities)
    total_amount = sum(float(commodity.total_amount or 0) for commodity in commodities)
    
    context = {
        'delivery': delivery,
        'commodities': commodities,
        'total_quantity': total_quantity,
        'total_amount': total_amount,
    }
    
    return render(request, 'accounts/supplier_delivery_detail.html', context)


@login_required
@supplier_account_activated_required
@require_POST
def create_delivery(request):
    """Create a new delivery tracking entry with multiple commodities."""
    from .models import ContractCommodity, DeliveryTracking, DeliveryCommodity, School, SupplierContract
    from core.models import Region, Commodity
    
    try:
        # Get form data
        serial_number = request.POST.get('serial_number')
        delivery_date = request.POST.get('delivery_date')
        srv_number = request.POST.get('srv_number')
        waybill_number = request.POST.get('waybill_number')
        invoice_number = request.POST.get('invoice_number', '')
        notes = request.POST.get('notes', '')
        
        # Contract selection (required)
        contract_id = request.POST.get('contract')
        
        # Direct delivery fields (required)
        region_id = request.POST.get('region')
        school_id = request.POST.get('school')
        
        # File uploads
        srv_document = request.FILES.get('srv_document')
        waybill_document = request.FILES.get('waybill_document')
        invoice_document = request.FILES.get('invoice_document')
        
        # Validate required fields including contract
        if not all([serial_number, delivery_date, srv_number, waybill_number, region_id, school_id, contract_id]):
            return JsonResponse({
                'success': False,
                'message': 'All required fields including contract must be provided'
            })
        
        # Get related objects
        try:
            region = Region.objects.get(pk=region_id)
            school = School.objects.get(pk=school_id, region=region)
        except (Region.DoesNotExist, School.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Invalid region or school selected'
            })
        
        # Handle contract selection (required)
        try:
            contract = SupplierContract.objects.get(
                pk=contract_id,
                application__user=request.user,
                status='ACTIVE'
            )
            # Verify contract is signed
            from .models import ContractSigning
            if not ContractSigning.objects.filter(
                contract=contract,
                supplier=request.user,
                status='SIGNED'
            ).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Contract must be signed before creating deliveries'
                })
        except SupplierContract.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid contract selected'
            })
        
        # Process commodities data
        commodities_data = []
        for key, value in request.POST.items():
            if key.startswith('commodities[') and key.endswith('][commodity]'):
                # Extract index from key like 'commodities[0][commodity]'
                index = key.split('[')[1].split(']')[0]
                commodity_id = value
                quantity = request.POST.get(f'commodities[{index}][quantity]')
                unit_of_measure = request.POST.get(f'commodities[{index}][unit_of_measure]')
                unit_price = request.POST.get(f'commodities[{index}][unit_price]')
                
                if commodity_id and quantity and unit_of_measure:
                    try:
                        commodity = Commodity.objects.get(pk=commodity_id)
                        commodities_data.append({
                            'commodity': commodity,
                            'quantity': quantity,
                            'unit_of_measure': unit_of_measure,
                            'unit_price': unit_price if unit_price else None
                        })
                    except Commodity.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'message': f'Invalid commodity selected'
                        })
        
        if not commodities_data:
            return JsonResponse({
                'success': False,
                'message': 'At least one commodity must be provided'
            })
        
        # Create delivery tracking (with contract if applicable)
        delivery = DeliveryTracking.objects.create(
            supplier_user=request.user,
            contract=contract,
            delivery_region=region,
            delivery_school=school,
            serial_number=serial_number,
            delivery_date=delivery_date,
            srv_number=srv_number,
            waybill_number=waybill_number,
            invoice_number=invoice_number,
            notes=notes,
            srv_document=srv_document,
            waybill_document=waybill_document,
            invoice_document=invoice_document
        )
        
        # Create delivery commodities
        commodity_names = []
        for commodity_data in commodities_data:
            # Convert string values to proper types
            try:
                quantity = float(commodity_data['quantity'])
                unit_price = float(commodity_data['unit_price']) if commodity_data['unit_price'] else 0.0
                total_amount = quantity * unit_price
                
                DeliveryCommodity.objects.create(
                    delivery=delivery,
                    commodity=commodity_data['commodity'],
                    quantity=quantity,
                    unit_of_measure=commodity_data['unit_of_measure'],
                    unit_price=unit_price,
                    total_amount=total_amount
                )
                commodity_names.append(commodity_data['commodity'].name)
            except (ValueError, TypeError) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid quantity or price value: {str(e)}'
                })
        
        # Create audit log for contract delivery (contract is always required now)
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_DELIVERY_CREATED',
            model_name='SupplierContract',
            object_id=str(contract.pk),
            details={
                'contract_number': contract.contract_number,
                'delivery_id': delivery.pk,
                'commodities': commodity_names,
                'school_name': school.name,
                'region_name': region.name,
                'serial_number': serial_number,
                'srv_number': srv_number,
                'waybill_number': waybill_number,
                'invoice_number': invoice_number,
                'created_by': request.user.get_full_name() or request.user.username
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create audit log for delivery
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='DELIVERY_CREATED',
            model_name='DeliveryTracking',
            object_id=str(delivery.pk),
            details={
                'commodities': commodity_names,
                'school_name': school.name,
                'region_name': region.name,
                'serial_number': serial_number,
                'srv_number': srv_number,
                'waybill_number': waybill_number,
                'invoice_number': invoice_number,
                'contract_number': contract.contract_number,
                'created_by': request.user.get_full_name() or request.user.username
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Delivery created successfully with {len(commodities_data)} commodities',
            'delivery_id': delivery.pk
        })
        
    except Exception as e:
        logger.error(f"Error creating delivery: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to create delivery: {str(e)}'
        })


@csrf_exempt
def get_schools_by_region(request):
    """Get schools filtered by region for AJAX requests."""
    from .models import School
    
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse({'schools': []})
    
    try:
        schools = School.objects.filter(
            region_id=region_id,
            is_active=True
        ).values('id', 'name', 'code')
        
        return JsonResponse({
            'schools': list(schools)
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        })


# Document Creation Views
@login_required
def create_srv(request):
    """Create a new Store Receipt Voucher."""
    if request.method == 'POST':
        form = SRVCreationForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            srv = form.save(commit=False)
            srv.supplier = request.user
            srv.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='CREATE_SRV',
                details=f'Created SRV {srv.srv_number} for {srv.delivery_school.name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'SRV {srv.srv_number} created successfully!')
            return redirect('applications:supplier-srvs')
    else:
        form = SRVCreationForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Store Receipt Voucher',
        'page_title': 'Create SRV'
    }
    return render(request, 'accounts/create_srv.html', context)


@login_required
def create_waybill(request):
    """Create a new Waybill."""
    if request.method == 'POST':
        form = WaybillCreationForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            waybill = form.save(commit=False)
            waybill.supplier = request.user
            waybill.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='CREATE_WAYBILL',
                details=f'Created Waybill {waybill.waybill_number} to {waybill.destination_school.name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Waybill {waybill.waybill_number} created successfully!')
            return redirect('applications:supplier-waybills')
    else:
        form = WaybillCreationForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Waybill',
        'page_title': 'Create Waybill'
    }
    return render(request, 'accounts/create_waybill.html', context)


@login_required
def create_invoice(request):
    """Create a new Invoice."""
    if request.method == 'POST':
        form = InvoiceCreationForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.supplier = request.user
            invoice.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='CREATE_INVOICE',
                details=f'Created Invoice {invoice.invoice_number} for {invoice.client_school.name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('applications:supplier-invoices')
    else:
        form = InvoiceCreationForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Invoice',
        'page_title': 'Create Invoice'
    }
    return render(request, 'accounts/create_invoice.html', context)


@login_required
def supplier_srvs(request):
    """List all SRVs created by the supplier."""
    srvs = StoreReceiptVoucher.objects.filter(supplier=request.user).select_related(
        'delivery_region', 'delivery_school', 'commodity'
    ).order_by('-created_at')
    
    context = {
        'srvs': srvs,
        'title': 'My Store Receipt Vouchers',
        'page_title': 'SRVs'
    }
    return render(request, 'accounts/supplier_srvs.html', context)


@login_required
def supplier_waybills(request):
    """List all Waybills created by the supplier."""
    waybills = Waybill.objects.filter(supplier=request.user).select_related(
        'destination_region', 'destination_school', 'commodity'
    ).order_by('-created_at')
    
    context = {
        'waybills': waybills,
        'title': 'My Waybills',
        'page_title': 'Waybills'
    }
    return render(request, 'accounts/supplier_waybills.html', context)


@login_required
def supplier_invoices(request):
    """List all Invoices created by the supplier."""
    invoices = Invoice.objects.filter(supplier=request.user).select_related(
        'client_region', 'client_school', 'commodity'
    ).order_by('-created_at')
    
    context = {
        'invoices': invoices,
        'title': 'My Invoices',
        'page_title': 'Invoices'
    }
    return render(request, 'accounts/supplier_invoices.html', context)


@login_required
@supplier_account_activated_required
def supplier_contract_documents(request):
    """View for suppliers to see and sign contract documents."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('applications:supplier-dashboard')
    
    # Get contract signings for this supplier
    contract_signings = ContractSigning.objects.filter(
        supplier=request.user
    ).select_related('contract', 'contract__application').order_by('-created_at')
    
    # Get statistics
    total_contracts = contract_signings.count()
    pending_contracts = contract_signings.filter(status='PENDING').count()
    signed_contracts = contract_signings.filter(status='SIGNED').count()
    reviewed_contracts = contract_signings.filter(status='REVIEWED').count()
    
    context = {
        'contract_signings': contract_signings,
        'total_contracts': total_contracts,
        'pending_contracts': pending_contracts,
        'signed_contracts': signed_contracts,
        'reviewed_contracts': reviewed_contracts,
    }
    
    return render(request, 'suppliers/contract_documents.html', context)


@login_required
@supplier_account_activated_required
def contract_document_detail(request, signing_id):
    """Detailed view of contract documents for signing."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('applications:supplier-dashboard')
    
    signing = get_object_or_404(
        ContractSigning.objects.select_related('contract', 'contract__application'),
        pk=signing_id,
        supplier=request.user
    )
    
    # Get assigned documents for this contract
    assigned_documents = ContractDocumentAssignment.objects.filter(
        contract=signing.contract
    ).select_related('document').order_by('document__category', 'document__title')
    
    # Group documents by category
    static_docs = assigned_documents.filter(document__category='STATIC')
    dynamic_docs = assigned_documents.filter(document__category='DYNAMIC')
    contract_specific_docs = assigned_documents.filter(document__category='CONTRACT_SPECIFIC')
    
    context = {
        'signing': signing,
        'contract': signing.contract,
        'assigned_documents': assigned_documents,
        'static_docs': static_docs,
        'dynamic_docs': dynamic_docs,
        'contract_specific_docs': contract_specific_docs,
    }
    
    return render(request, 'suppliers/contract_document_detail.html', context)


@login_required
@supplier_account_activated_required
@require_POST
def review_contract_documents(request, signing_id):
    """Mark contract documents as reviewed."""
    if not request.user.is_supplier:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    try:
        signing = get_object_or_404(ContractSigning, pk=signing_id, supplier=request.user)
        
        if signing.status != 'PENDING':
            return JsonResponse({
                'success': False, 
                'message': 'Contract documents have already been processed'
            })
        
        signing.status = 'REVIEWED'
        signing.reviewed_at = timezone.now()
        signing.save()
        
        # Log the activity
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_REVIEWED',
            resource_type='ContractSigning',
            resource_id=signing.pk,
            details=f'Contract {signing.contract.contract_number} documents reviewed by supplier'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contract documents have been marked as reviewed'
        })
        
    except Exception as e:
        logger.error(f"Error reviewing contract documents {signing_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error reviewing contract: {str(e)}'
        })


@login_required
@supplier_account_activated_required
@require_POST
def sign_contract_documents(request, signing_id):
    """Sign contract documents."""
    if not request.user.is_supplier:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    try:
        signing = get_object_or_404(ContractSigning, pk=signing_id, supplier=request.user)
        
        if signing.status not in ['PENDING', 'REVIEWED']:
            return JsonResponse({
                'success': False, 
                'message': 'Contract documents cannot be signed in current status'
            })
        
        # Update signing status
        signing.status = 'SIGNED'
        signing.signed_at = timezone.now()
        if request.FILES.get('signature_file'):
            signing.signature_file = request.FILES.get('signature_file')
        if request.POST.get('notes'):
            signing.notes = request.POST.get('notes')
        signing.save()
        
        # Log the activity
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_SIGNED',
            resource_type='ContractSigning',
            resource_id=signing.pk,
            details=f'Contract {signing.contract.contract_number} signed by supplier'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contract has been successfully signed'
        })
        
    except Exception as e:
        logger.error(f"Error signing contract {signing_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error signing contract: {str(e)}'
        })


@login_required
@supplier_account_activated_required
@require_POST
def reject_contract_documents(request, signing_id):
    """Reject contract documents."""
    if not request.user.is_supplier:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    try:
        signing = get_object_or_404(ContractSigning, pk=signing_id, supplier=request.user)
        
        if signing.status not in ['PENDING', 'REVIEWED']:
            return JsonResponse({
                'success': False, 
                'message': 'Contract documents cannot be rejected in current status'
            })
        
        rejection_reason = request.POST.get('rejection_reason', '')
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            })
        
        # Update signing status
        signing.status = 'REJECTED'
        signing.rejection_reason = rejection_reason
        signing.save()
        
        # Log the activity
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_REJECTED',
            resource_type='ContractSigning',
            resource_id=signing.pk,
            details=f'Contract {signing.contract.contract_number} rejected by supplier: {rejection_reason}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contract has been rejected'
        })
        
    except Exception as e:
        logger.error(f"Error rejecting contract {signing_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error rejecting contract: {str(e)}'
        })