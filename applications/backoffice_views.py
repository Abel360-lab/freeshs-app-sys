"""
Backoffice views for managing applications and suppliers.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)

from .models import SupplierApplication
from documents.models import DocumentUpload, OutstandingDocumentRequest
from core.models import Region


@staff_member_required
def backoffice_dashboard(request):
    """Main backoffice dashboard with key metrics."""
    
    # Calculate key metrics
    total_applications = SupplierApplication.objects.count()
    
    # Applications this week
    week_ago = timezone.now() - timedelta(days=7)
    new_this_week = SupplierApplication.objects.filter(created_at__gte=week_ago).count()
    
    # Status breakdown
    status_counts = SupplierApplication.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Calculate status percentages
    status_percentages = {}
    total_percentage = 0
    for status in status_counts:
        percentage = (status['count'] / total_applications * 100) if total_applications > 0 else 0
        # Use more precise rounding to avoid floating point errors
        status_percentages[status['status']] = round(percentage * 10) / 10
        total_percentage += status_percentages[status['status']]
    
    # Normalize percentages to ensure they add up to exactly 100.0
    if total_percentage != 100.0 and total_percentage > 0:
        # Find the largest percentage and adjust it to make the total exactly 100.0
        max_status = max(status_percentages.items(), key=lambda x: x[1])
        if max_status[1] > 0:
            adjustment = 100.0 - total_percentage
            status_percentages[max_status[0]] = round((max_status[1] + adjustment) * 10) / 10
    
    # Recent applications
    recent_applications = SupplierApplication.objects.select_related('region').order_by('-created_at')[:5]
    
    # Monthly trend data
    monthly_data = []
    monthly_labels = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        count = SupplierApplication.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        monthly_data.append(count)
        monthly_labels.append(month_start.strftime('%b'))
    
    monthly_data.reverse()
    monthly_labels.reverse()
    
    # Regional distribution
    region_stats = SupplierApplication.objects.values('region__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Additional metrics for dashboard
    pending_count = SupplierApplication.objects.filter(status='PENDING_REVIEW').count()
    approved_count = SupplierApplication.objects.filter(status='APPROVED').count()
    review_count = SupplierApplication.objects.filter(status='UNDER_REVIEW').count()
    rejected_count = SupplierApplication.objects.filter(status='REJECTED').count()
    docs_pending = SupplierApplication.objects.filter(status='UNDER_REVIEW').count()
    
    context = {
        'total_applications': total_applications,
        'new_this_week': new_this_week,
        'status_counts': status_counts,
        'recent_applications': recent_applications,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'region_stats': region_stats,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'review_count': review_count,
        'rejected_count': rejected_count,
        'docs_pending': docs_pending,
        'active_suppliers': approved_count,
        'pending_review_percentage': status_percentages.get('PENDING_REVIEW', 0),
        'approved_percentage': status_percentages.get('APPROVED', 0),
        'review_percentage': status_percentages.get('UNDER_REVIEW', 0),
        'rejected_percentage': status_percentages.get('REJECTED', 0),
        'today': timezone.now(),
    }
    
    return render(request, 'backoffice/dashboard.html', context)


@staff_member_required
def application_management(request):
    """Application management interface with filtering and search."""
    
    applications = SupplierApplication.objects.select_related('region').order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    region_filter = request.GET.get('region')
    search_query = request.GET.get('search')
    
    # Handle "None" string case and other falsy values
    if search_query in ['None', 'none', '']:
        search_query = None
    
    # Map URL status values to database status values
    status_mapping = {
        'pending': 'PENDING_REVIEW',
        'under_review': 'UNDER_REVIEW',
        'approved': 'APPROVED',
        'rejected': 'REJECTED',
    }
    
    if status_filter and status_filter in status_mapping:
        applications = applications.filter(status=status_mapping[status_filter])
    
    if region_filter:
        applications = applications.filter(region_id=region_filter)
    
    if search_query:
        applications = applications.filter(
            Q(business_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(tracking_code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get regions for filter dropdown
    regions = Region.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'regions': regions,
        'current_status': status_filter or '',
        'current_region': region_filter or '',
        'current_search': search_query or '',
    }
    
    return render(request, 'backoffice/application_management.html', context)


@staff_member_required
def application_detail(request, pk):
    """Detailed view of a single application."""
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    # Update status to UNDER_REVIEW when admin opens the application for review
    if application.status == 'PENDING_REVIEW':
        application.status = 'UNDER_REVIEW'
        application.reviewed_at = timezone.now()
        application.save(update_fields=['status', 'reviewed_at'])
    
    # Get related data
    team_members = application.team_members.all()
    next_of_kin = application.next_of_kin.all()
    bank_accounts = application.bank_accounts.all()
    
    # Get all active documents for comparison (including optional ones like FDA certificate)
    from documents.models import DocumentRequirement
    required_documents = DocumentRequirement.objects.filter(is_active=True)
    
    # Get all document uploads for this application
    from documents.models import DocumentUpload
    document_uploads = DocumentUpload.objects.filter(application=application)
    
    document_status = []
    for req_doc in required_documents:
        # Check if there's an upload for this requirement
        uploaded_doc = document_uploads.filter(requirement=req_doc).first()
        is_uploaded = uploaded_doc is not None
        is_verified = uploaded_doc.verified if uploaded_doc else False
        
        document_status.append({
            'requirement': req_doc,
            'uploaded_doc': uploaded_doc,
            'is_uploaded': is_uploaded,
            'is_verified': is_verified,
            'is_gcx_proof': req_doc.code == 'GCX_REGISTRATION_PROOF',
            'is_required': req_doc.is_required,
            'is_optional': not req_doc.is_required
        })
    
    # Check if GCX Registration Proof is uploaded (payment confirmation)
    gcx_proof_upload = document_uploads.filter(
        requirement__code='GCX_REGISTRATION_PROOF'
    ).first()
    gcx_proof_uploaded = gcx_proof_upload is not None
    gcx_proof_verified = gcx_proof_upload.verified if gcx_proof_upload else False
    
    # Calculate missing documents dynamically based on actual uploads
    missing_documents = []
    for doc_status in document_status:
        if doc_status['is_required'] and not doc_status['is_uploaded']:
            missing_documents.append({
                'name': doc_status['requirement'].label,
                'code': doc_status['requirement'].code
            })
    
    context = {
        'application': application,
        'team_members': team_members,
        'next_of_kin': next_of_kin,
        'bank_accounts': bank_accounts,
        'document_status': document_status,
        'gcx_proof_uploaded': gcx_proof_uploaded,
        'gcx_proof_verified': gcx_proof_verified,
        'missing_documents': missing_documents,
        'can_approve': application.status in ['PENDING_REVIEW', 'UNDER_REVIEW'] and gcx_proof_uploaded and gcx_proof_verified,
        'can_reject': application.status in ['PENDING_REVIEW', 'UNDER_REVIEW'],
        'can_request_docs': application.status in ['PENDING_REVIEW', 'UNDER_REVIEW'],
    }
    
    return render(request, 'backoffice/application_detail.html', context)


@staff_member_required
def application_pdf_download(request, pk):
    """View PDF for an application from backoffice in browser."""
    from django.http import HttpResponse
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    if not application.pdf_file:
        return HttpResponse(
            'PDF not yet generated for this application',
            status=404
        )
    
    # Return the PDF file for inline viewing
    response = HttpResponse(
        application.pdf_file.read(),
        content_type='application/pdf'
    )
    # Use 'inline' instead of 'attachment' to view in browser
    response['Content-Disposition'] = f'inline; filename="application_{application.tracking_code}.pdf"'
    return response


@staff_member_required
def application_pdf_generate(request, pk):
    """Generate PDF for an application from backoffice."""
    from django.http import HttpResponseRedirect
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
            return HttpResponseRedirect(f'/backoffice/applications/{pk}/pdf/')
        else:
            messages.error(request, 'Failed to generate PDF')
            return HttpResponseRedirect(f'/backoffice/applications/{pk}/')
            
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return HttpResponseRedirect(f'/backoffice/applications/{pk}/')


@staff_member_required
def supplier_management(request):
    """Supplier management interface for approved applicants."""
    
    suppliers = SupplierApplication.objects.filter(status='APPROVED').select_related('region').order_by('-updated_at')
    
    # Filtering
    region_filter = request.GET.get('region')
    search_query = request.GET.get('search')
    
    if region_filter:
        suppliers = suppliers.filter(region_id=region_filter)
    
    if search_query:
        suppliers = suppliers.filter(
            Q(business_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(tracking_code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get regions for filter dropdown
    regions = Region.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'regions': regions,
        'current_region': region_filter,
        'current_search': search_query,
    }
    
    return render(request, 'backoffice/supplier_management.html', context)


@staff_member_required
def document_verification(request):
    """Document verification and review system."""
    
    documents = DocumentUpload.objects.select_related('application', 'requirement').order_by('-uploaded_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    application_filter = request.GET.get('application')
    
    if status_filter:
        documents = documents.filter(status=status_filter)
    
    if application_filter:
        documents = documents.filter(application_id=application_filter)
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_status': status_filter,
        'current_application': application_filter,
    }
    
    return render(request, 'backoffice/document_verification.html', context)


@staff_member_required
def analytics(request):
    """Analytics and reporting dashboard."""
    
    # Get time period from request
    period = request.GET.get('period', '30')
    try:
        period_days = int(period)
    except (ValueError, TypeError):
        period_days = 30
    
    # Monthly application trends
    monthly_data = []
    monthly_labels = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        count = SupplierApplication.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        monthly_data.append(count)
        monthly_labels.append(month_start.strftime('%b'))
    
    monthly_data.reverse()
    monthly_labels.reverse()
    
    # Status distribution
    status_data = []
    status_labels = []
    status_counts = SupplierApplication.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    for item in status_counts:
        status_labels.append(item['status'].replace('_', ' ').title())
        status_data.append(item['count'])
    
    # Regional distribution
    region_data = []
    region_labels = []
    region_stats = SupplierApplication.objects.values('region__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for item in region_stats:
        region_labels.append(item['region__name'])
        region_data.append(item['count'])
    
    # Commodity distribution
    commodity_data = []
    commodity_labels = []
    commodity_stats = SupplierApplication.objects.values('commodities_to_supply__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for item in commodity_stats:
        if item['commodities_to_supply__name']:
            commodity_labels.append(item['commodities_to_supply__name'])
            commodity_data.append(item['count'])
    
    # Key metrics
    total_applications = SupplierApplication.objects.count()
    approved_applications = SupplierApplication.objects.filter(status='APPROVED').count()
    pending_applications = SupplierApplication.objects.filter(status='PENDING_REVIEW').count()
    active_suppliers = approved_applications
    
    # Calculate percentages
    approval_rate = round((approved_applications / total_applications * 100) if total_applications > 0 else 0, 1)
    pending_percentage = round((pending_applications / total_applications * 100) if total_applications > 0 else 0, 1)
    approved_percentage = round((approved_applications / total_applications * 100) if total_applications > 0 else 0, 1)
    
    # This month's data
    month_start = timezone.now().replace(day=1)
    new_this_month = SupplierApplication.objects.filter(created_at__gte=month_start).count()
    new_suppliers = SupplierApplication.objects.filter(status='APPROVED', decided_at__gte=month_start).count()
    
    # Processing time metrics (simplified)
    avg_processing_days = 5  # This would be calculated from actual data
    fastest_processing = 1
    slowest_processing = 15
    on_time_rate = 85
    
    # Performance targets
    monthly_target = 100
    target_achievement = min(100, round((new_this_month / monthly_target * 100), 1))
    approval_target = 80
    approval_achievement = min(100, round((approval_rate / approval_target * 100), 1))
    time_target = 5
    time_achievement = min(100, round((time_target / avg_processing_days * 100), 1))
    
    # Top performing regions (simplified)
    top_regions = []
    for region in region_stats[:5]:
        top_regions.append({
            'name': region['region__name'],
            'app_count': region['count'],
            'approval_rate': 75,  # This would be calculated
            'trend': 1  # This would be calculated
        })
    
    context = {
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'status_labels': status_labels,
        'status_data': status_data,
        'region_labels': region_labels,
        'region_data': region_data,
        'commodity_labels': commodity_labels,
        'commodity_data': commodity_data,
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'active_suppliers': active_suppliers,
        'approval_rate': approval_rate,
        'pending_percentage': pending_percentage,
        'approved_percentage': approved_percentage,
        'new_this_month': new_this_month,
        'new_suppliers': new_suppliers,
        'avg_processing_days': avg_processing_days,
        'fastest_processing': fastest_processing,
        'slowest_processing': slowest_processing,
        'on_time_rate': on_time_rate,
        'monthly_target': monthly_target,
        'target_achievement': target_achievement,
        'approval_target': approval_target,
        'approval_achievement': approval_achievement,
        'time_target': time_target,
        'time_achievement': time_achievement,
        'top_regions': top_regions,
        'pending_count': pending_applications,
        'approved_count': approved_applications,
        'review_count': SupplierApplication.objects.filter(status='UNDER_REVIEW').count(),
        'rejected_count': SupplierApplication.objects.filter(status='REJECTED').count(),
        'rejected_percentage': round((SupplierApplication.objects.filter(status='REJECTED').count() / total_applications * 100) if total_applications > 0 else 0, 1),
        'review_percentage': round((SupplierApplication.objects.filter(status='UNDER_REVIEW').count() / total_applications * 100) if total_applications > 0 else 0, 1),
    }
    
    return render(request, 'backoffice/analytics.html', context)


@staff_member_required
@require_POST
def approve_application(request, pk):
    """Approve an application and create user account."""
    from core.models import AuditLog
    from accounts.models import User
    from django.contrib.auth.hashers import make_password
    import secrets
    import string
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    # Store old status for audit log
    old_status = application.status
    
    if application.status not in ['PENDING_REVIEW', 'UNDER_REVIEW']:
        messages.error(request, 'Only submitted, pending review, under review, or needs more documents applications can be approved.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    # Check if user already exists
    existing_user = User.objects.filter(email=application.email).first()
    if existing_user:
        messages.warning(request, f'User account already exists for {application.email}. Application approved without creating new account.')
        application.status = 'APPROVED'
        application.approved_at = timezone.now()
        application.approved_by = request.user
        application.reviewer_comment = request.POST.get('comment', '')
        application.save()
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    # Generate secure password
    def generate_password():
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(12))
    
    temp_password = generate_password()
    
    try:
        # Create user account
        user = User.objects.create_user(
            username=application.email,  # Use email as username
            email=application.email,
            password=temp_password,
            first_name=application.signer_name.split()[0] if application.signer_name else '',
            last_name=' '.join(application.signer_name.split()[1:]) if application.signer_name and len(application.signer_name.split()) > 1 else '',
            phone_number=application.telephone,
            role=User.Role.SUPPLIER,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        
        logger.info(f"Created user account for approved application {application.tracking_code}: {user.email}")
        
        # Update application status
        application.status = 'APPROVED'
        application.approved_at = timezone.now()
        application.approved_by = request.user
        application.reviewer_comment = request.POST.get('comment', '')
        application.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='APPROVE_APPLICATION',
            model_name='SupplierApplication',
            object_id=str(application.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'old_status': old_status,
                'new_status': application.status,
                'approved_at': application.approved_at.isoformat(),
                'reviewer_comment': application.reviewer_comment,
                'user_created': True,
                'user_id': str(user.pk)
            },
            ip_address=AuditLog.get_client_ip(request) if hasattr(AuditLog, 'get_client_ip') else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send approval notification with credentials
        try:
            from core.utils import send_approval_email, send_approval_sms
            send_approval_email(application, user, temp_password)
            send_approval_sms(application)
            messages.success(request, f'Application {application.tracking_code} has been approved and user account created. Notifications sent to {application.email} and {application.telephone}.')
        except Exception as e:
            logger.error(f"Failed to send approval notifications: {str(e)}")
            messages.warning(request, f'Application approved and user account created, but failed to send notifications: {str(e)}')
                
    except Exception as e:
        logger.error(f"Failed to create user account for application {application.tracking_code}: {str(e)}")
        messages.error(request, f'Failed to approve application: {str(e)}')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    return redirect('applications:backoffice-application-detail', pk=pk)


@staff_member_required
@require_POST
def reject_application(request, pk):
    """Reject an application."""
    from core.models import AuditLog
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    # Store old status for audit log
    old_status = application.status
    
    if application.status not in ['PENDING_REVIEW', 'UNDER_REVIEW']:
        messages.error(request, 'Only submitted, under review, or needs more documents applications can be rejected.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    reason = request.POST.get('reason', '')
    if not reason:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    application.status = 'REJECTED'
    application.rejected_at = timezone.now()
    application.rejected_by = request.user
    application.reviewer_comment = reason
    application.save()
    
    # Log the action
    AuditLog.objects.create(
        user=request.user,
        action='REJECT_APPLICATION',
        model_name='SupplierApplication',
        object_id=str(application.pk),
        details={
            'application_tracking_code': application.tracking_code,
            'business_name': application.business_name,
            'old_status': old_status,
            'new_status': application.status,
            'rejected_at': application.rejected_at.isoformat(),
            'reason': reason,
            'reviewer_comment': application.reviewer_comment
        },
        ip_address=AuditLog.get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Send rejection notification
    try:
        from core.utils import send_rejection_email, send_rejection_sms
        send_rejection_email(application, reason)
        send_rejection_sms(application, reason)
        messages.success(request, f'Application {application.tracking_code} has been rejected. Notifications sent to {application.email} and {application.telephone}.')
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {str(e)}")
        messages.warning(request, f'Application rejected but failed to send email notification: {str(e)}')
    
    return redirect('applications:backoffice-application-detail', pk=pk)


@staff_member_required
@require_POST
def request_documents(request, pk):
    """Request additional documents from applicant."""
    from core.models import AuditLog
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    # Store old status for audit log
    old_status = application.status
    
    # Get missing documents
    missing_documents = application.get_missing_documents_list()
    
    # Get the actual DocumentRequirement objects for missing documents
    from documents.models import DocumentRequirement
    missing_requirements = DocumentRequirement.objects.filter(
        label__in=missing_documents,
        is_active=True
    )
    
    # Also include FDA certificate if the application supplies processed foods
    if application.supplies_processed_foods():
        fda_requirement = DocumentRequirement.objects.filter(
            code='FDA_CERT_PROCESSED_FOOD',
            is_active=True
        ).first()
        if fda_requirement and fda_requirement not in missing_requirements:
            # Check if FDA certificate is already uploaded
            fda_uploaded = application.document_uploads.filter(
                requirement=fda_requirement
            ).exists()
            if not fda_uploaded:
                missing_requirements = missing_requirements.union(
                    DocumentRequirement.objects.filter(id=fda_requirement.id)
                )
    
    # Create outstanding document request
    outstanding_request = OutstandingDocumentRequest.objects.create(
        application=application,
        message=request.POST.get('comment', 'Please provide additional documents.'),
        requested_by=request.user
    )
    outstanding_request.requirements.set(missing_requirements)
    
    # Update application status to UNDER_REVIEW
    application.status = 'UNDER_REVIEW'
    application.reviewer_comment = request.POST.get('comment', 'Please provide additional documents.')
    application.save()
    
    # Log the action
    AuditLog.objects.create(
        user=request.user,
        action='REQUEST_DOCUMENTS',
        model_name='SupplierApplication',
        object_id=str(application.pk),
        details={
            'application_tracking_code': application.tracking_code,
            'business_name': application.business_name,
            'old_status': old_status,
            'new_status': application.status,
            'missing_documents': missing_documents,
            'outstanding_request_id': outstanding_request.pk,
            'reviewer_comment': application.reviewer_comment
        },
        ip_address=AuditLog.get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Send notification to applicant
    try:
        from notifications.services import NotificationService
        NotificationService.send_document_request_notification(application, outstanding_request, request)
        messages.success(request, f'Document request sent for application {application.tracking_code}. Status changed to Under Review. Email notification sent to applicant.')
    except Exception as e:
        logger.error(f"Failed to send document request notification: {str(e)}")
        messages.warning(request, f'Document request created but failed to send email notification: {str(e)}')
    
    return redirect('applications:backoffice-application-detail', pk=pk)


@staff_member_required
@require_POST
def bulk_approve_applications(request):
    """Bulk approve applications."""
    application_ids = request.POST.getlist('application_ids')
    
    if not application_ids:
        messages.error(request, 'No applications selected.')
        return redirect('applications:backoffice-applications')
    
    applications = SupplierApplication.objects.filter(
        id__in=application_ids, 
        status='pending'
    )
    
    count = 0
    for application in applications:
        application.status = 'approved'
        application.decided_at = timezone.now()
        application.save()
        count += 1
    
    messages.success(request, f'{count} applications have been approved.')
    return redirect('applications:backoffice-applications')


@staff_member_required
@require_POST
def bulk_reject_applications(request):
    """Bulk reject applications."""
    application_ids = request.POST.getlist('application_ids')
    reason = request.POST.get('reason', '')
    
    if not application_ids:
        messages.error(request, 'No applications selected.')
        return redirect('applications:backoffice-applications')
    
    if not reason:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('applications:backoffice-applications')
    
    applications = SupplierApplication.objects.filter(
        id__in=application_ids, 
        status='pending'
    )
    
    count = 0
    for application in applications:
        application.status = 'rejected'
        application.decided_at = timezone.now()
        application.reviewer_comment = reason
        application.save()
        count += 1
    
    messages.success(request, f'{count} applications have been rejected.')
    return redirect('applications:backoffice-applications')


@staff_member_required
@require_POST
def verify_document(request, pk):
    """Verify a document."""
    from core.models import AuditLog
    
    document = get_object_or_404(DocumentUpload, pk=pk)
    
    # Store old state for audit log
    old_verified = document.verified
    
    document.verified = True
    document.verified_at = timezone.now()
    document.verified_by = request.user
    document.save()
    
    # If this is the GCX Registration Proof, update the application's payment status
    if document.requirement.code == 'GCX_REGISTRATION_PROOF':
        application = document.application
        application.gcx_registration_proof_uploaded = True
        application.save()
        
        # Log payment confirmation
        AuditLog.objects.create(
            user=request.user,
            action='PAYMENT_CONFIRMED',
            model_name='DocumentUpload',
            object_id=str(document.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'document_type': document.requirement.label,
                'document_code': document.requirement.code,
                'old_verified': old_verified,
                'new_verified': True,
                'gcx_proof_uploaded': True,
                'payment_confirmed': True
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'Document "{document.requirement.label}" has been verified and payment confirmed.')
    else:
        # Log document verification
        AuditLog.objects.create(
            user=request.user,
            action='VERIFY_DOCUMENT',
            model_name='DocumentUpload',
            object_id=str(document.pk),
            details={
                'application_tracking_code': document.application.tracking_code,
                'business_name': document.application.business_name,
                'document_type': document.requirement.label,
                'document_code': document.requirement.code,
                'old_verified': old_verified,
                'new_verified': True
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'Document "{document.requirement.label}" has been verified.')
    
    # Redirect back to the application detail page
    return redirect('applications:backoffice-application-detail', pk=document.application.pk)


@staff_member_required
@require_POST
def reject_document(request, pk):
    """Reject a document."""
    document = get_object_or_404(DocumentUpload, pk=pk)
    
    reason = request.POST.get('reason', '')
    if not reason:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('applications:backoffice-documents')
    
    document.status = 'rejected'
    document.rejected_at = timezone.now()
    document.rejected_by = request.user
    document.rejection_reason = reason
    document.save()
    
    messages.success(request, 'Document has been rejected.')
    return redirect('applications:backoffice-documents')
