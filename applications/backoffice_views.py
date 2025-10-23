"""
Backoffice views for managing applications and suppliers.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import csv
import io
import zipfile
import os
from django.http import StreamingHttpResponse

from .models import (
    SupplierApplication, DeliveryTracking, DeliveryCommodity,
    StoreReceiptVoucher, Waybill, Invoice, SupplierContract, ContractDocument, 
    ContractDocumentRequirement, ContractDocumentAssignment, ContractSigning
)
from accounts.models import User
from core.models import Region
from documents.models import DocumentUpload, OutstandingDocumentRequest
from notifications.models import NotificationTemplate
from notifications.services import NotificationService
from core.models import AuditLog

logger = logging.getLogger(__name__)


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
    
    # Delivery statistics
    from .models import DeliveryTracking
    total_deliveries = DeliveryTracking.objects.count()
    pending_deliveries = DeliveryTracking.objects.filter(status='PENDING').count()
    verified_deliveries = DeliveryTracking.objects.filter(status='VERIFIED').count()
    rejected_deliveries = DeliveryTracking.objects.filter(status='REJECTED').count()
    
    # Recent deliveries (last 5)
    recent_deliveries = DeliveryTracking.objects.select_related(
        'supplier_user', 'delivery_region', 'delivery_school', 'contract'
    ).order_by('-created_at')[:5]
    
    # Contract statistics
    from .models import SupplierContract, ContractSigning
    total_contracts = SupplierContract.objects.count()
    active_contracts = SupplierContract.objects.filter(status='ACTIVE').count()
    signed_contracts = ContractSigning.objects.filter(status='SIGNED').count()
    pending_contracts = SupplierContract.objects.filter(status='PENDING').count()
    
    # Recent contracts (last 5)
    recent_contracts = SupplierContract.objects.select_related(
        'application', 'application__user'
    ).order_by('-created_at')[:5]
    
    # Supplier statistics
    total_suppliers = User.objects.filter(role=User.Role.SUPPLIER).count()
    active_suppliers = User.objects.filter(role=User.Role.SUPPLIER, is_active=True).count()
    inactive_suppliers = User.objects.filter(role=User.Role.SUPPLIER, is_active=False).count()
    
    # Weekly statistics
    delivery_this_week = DeliveryTracking.objects.filter(
        created_at__gte=week_ago
    ).count()
    contract_this_week = SupplierContract.objects.filter(
        created_at__gte=week_ago
    ).count()
    
    # Recent activity feed - combine all recent activities
    recent_activities = []
    
    # Add recent applications with better status mapping
    for app in recent_applications:
        if app.status == 'APPROVED':
            color = 'success'
            icon = 'fas fa-check-circle'
        elif app.status == 'REJECTED':
            color = 'danger'
            icon = 'fas fa-times-circle'
        elif app.status == 'UNDER_REVIEW':
            color = 'warning'
            icon = 'fas fa-clock'
        else:
            color = 'info'
            icon = 'fas fa-file-alt'
            
        recent_activities.append({
            'type': 'application',
            'action': f'Application {app.get_status_display().lower()}',
            'description': f'{app.business_name} - {app.region.name if app.region else "Unknown Region"}',
            'timestamp': app.created_at,
            'icon': icon,
            'color': color,
            'status': app.status
        })
    
    # Add recent deliveries with better status mapping
    for delivery in recent_deliveries:
        if delivery.status == 'VERIFIED':
            color = 'success'
            icon = 'fas fa-check-circle'
        elif delivery.status == 'REJECTED':
            color = 'danger'
            icon = 'fas fa-times-circle'
        elif delivery.status == 'PENDING':
            color = 'warning'
            icon = 'fas fa-clock'
        else:
            color = 'info'
            icon = 'fas fa-truck'
            
        recent_activities.append({
            'type': 'delivery',
            'action': f'Delivery {delivery.get_status_display().lower()}',
            'description': f'{delivery.serial_number} - {delivery.delivery_school.name}',
            'timestamp': delivery.created_at,
            'icon': icon,
            'color': color,
            'status': delivery.status
        })
    
    # Add recent contracts with better status mapping
    for contract in recent_contracts:
        if contract.status == 'ACTIVE':
            color = 'success'
            icon = 'fas fa-check-circle'
        elif contract.status == 'EXPIRED':
            color = 'danger'
            icon = 'fas fa-times-circle'
        elif contract.status == 'PENDING':
            color = 'warning'
            icon = 'fas fa-clock'
        else:
            color = 'primary'
            icon = 'fas fa-file-contract'
            
        recent_activities.append({
            'type': 'contract',
            'action': f'Contract {contract.get_status_display().lower()}',
            'description': f'{contract.contract_number} - {contract.application.business_name}',
            'timestamp': contract.created_at,
            'icon': icon,
            'color': color,
            'status': contract.status
        })
    
    # Add contract signings if available
    try:
        recent_signings = ContractSigning.objects.select_related(
            'contract', 'contract__application'
        ).order_by('-created_at')[:3]
        
        for signing in recent_signings:
            if signing.status == 'SIGNED':
                color = 'success'
                icon = 'fas fa-signature'
            else:
                color = 'warning'
                icon = 'fas fa-clock'
                
            recent_activities.append({
                'type': 'signing',
                'action': f'Contract {signing.get_status_display().lower()}',
                'description': f'{signing.contract.contract_number} - {signing.contract.application.business_name}',
                'timestamp': signing.created_at,
                'icon': icon,
                'color': color,
                'status': signing.status
            })
    except:
        pass  # ContractSigning might not exist in all cases
    
    # Sort by timestamp (most recent first) and take top 10
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]
    
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
        
        # Delivery information
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'verified_deliveries': verified_deliveries,
        'rejected_deliveries': rejected_deliveries,
        'recent_deliveries': recent_deliveries,
        'delivery_this_week': delivery_this_week,
        
        # Contract information
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'signed_contracts': signed_contracts,
        'pending_contracts': pending_contracts,
        'recent_contracts': recent_contracts,
        'contract_this_week': contract_this_week,
        
        # Supplier information
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'inactive_suppliers': inactive_suppliers,
        
        # Recent activities
        'recent_activities': recent_activities,
        
        'today': timezone.now(),
    }
    
    return render(request, 'backoffice/dashboard.html', context)


@staff_member_required
def reports_dashboard(request):
    """Comprehensive reports dashboard for backoffice admin."""
    import json
    from django.db.models import Count, Sum, Avg, Q
    from datetime import datetime, timedelta
    from .models import DeliveryTracking, SupplierContract, ContractSigning
    from core.models import Region
    
    # Date range filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Default to last 30 days if no dates provided
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    try:
        date_from_dt = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        date_from_dt = (timezone.now() - timedelta(days=30)).date()
        date_to_dt = timezone.now().date()
    
    # Application Statistics
    applications_in_range = SupplierApplication.objects.filter(
        created_at__date__range=[date_from_dt, date_to_dt]
    )
    
    app_stats = {
        'total': applications_in_range.count(),
        'approved': applications_in_range.filter(status='APPROVED').count(),
        'pending': applications_in_range.filter(status='PENDING_REVIEW').count(),
        'under_review': applications_in_range.filter(status='UNDER_REVIEW').count(),
        'rejected': applications_in_range.filter(status='REJECTED').count(),
    }
    
    # Delivery Statistics
    deliveries_in_range = DeliveryTracking.objects.filter(
        created_at__date__range=[date_from_dt, date_to_dt]
    )
    
    delivery_stats = {
        'total': deliveries_in_range.count(),
        'pending': deliveries_in_range.filter(status='PENDING').count(),
        'verified': deliveries_in_range.filter(status='VERIFIED').count(),
        'rejected': deliveries_in_range.filter(status='REJECTED').count(),
    }
    
    # Calculate total delivery value
    total_delivery_value = deliveries_in_range.aggregate(
        total_value=Sum('commodities__total_amount')
    )['total_value'] or 0
    
    # Contract Statistics
    contracts_in_range = SupplierContract.objects.filter(
        created_at__date__range=[date_from_dt, date_to_dt]
    )
    
    contract_stats = {
        'total': contracts_in_range.count(),
        'active': contracts_in_range.filter(status='ACTIVE').count(),
        'pending': contracts_in_range.filter(status='PENDING').count(),
        'signed': ContractSigning.objects.filter(
            created_at__date__range=[date_from_dt, date_to_dt],
            status='SIGNED'
        ).count(),
    }
    
    # Regional Distribution
    regional_stats = SupplierApplication.objects.filter(
        created_at__date__range=[date_from_dt, date_to_dt]
    ).values('region__name').annotate(
        application_count=Count('id'),
        delivery_count=Count('contracts__deliveries', distinct=True),
        contract_count=Count('contracts', distinct=True)
    ).order_by('-application_count')
    
    # Monthly Trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        month_apps = SupplierApplication.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        month_deliveries = DeliveryTracking.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        month_contracts = SupplierContract.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        monthly_trends.append({
            'month': month_start.strftime('%b %Y'),
            'applications': month_apps,
            'deliveries': month_deliveries,
            'contracts': month_contracts,
        })
    
    monthly_trends.reverse()
    
    # Top Performing Suppliers
    top_suppliers = User.objects.filter(
        role=User.Role.SUPPLIER,
        supplierapplication__status='APPROVED'
    ).annotate(
        total_deliveries_count=Count('deliveries'),
        verified_deliveries_count=Count('deliveries', filter=Q(deliveries__status='VERIFIED')),
        total_contracts_count=Count('supplierapplication__contracts'),
        total_delivery_value=Sum('deliveries__commodities__total_amount')
    ).order_by('-verified_deliveries_count')[:10]
    
    # Delivery Performance Metrics
    delivery_performance = {
        'avg_verification_time': 0,  # Could be calculated based on created_at vs verified_at
        'verification_rate': 0,
        'rejection_rate': 0,
    }
    
    if delivery_stats['total'] > 0:
        delivery_performance['verification_rate'] = (delivery_stats['verified'] / delivery_stats['total']) * 100
        delivery_performance['rejection_rate'] = (delivery_stats['rejected'] / delivery_stats['total']) * 100
    
    # Contract Performance Metrics
    contract_performance = {
        'signing_rate': 0,
        'avg_contract_value': 0,
    }
    
    if contract_stats['total'] > 0:
        contract_performance['signing_rate'] = (contract_stats['signed'] / contract_stats['total']) * 100
        
        avg_contract_value = SupplierContract.objects.filter(
            created_at__date__range=[date_from_dt, date_to_dt]
        ).aggregate(avg_value=Avg('contract_value'))['avg_value']
        contract_performance['avg_contract_value'] = avg_contract_value or 0
    
    # Recent Activity Summary
    recent_activities = []
    
    # Recent applications
    for app in applications_in_range.order_by('-created_at')[:5]:
        recent_activities.append({
            'type': 'application',
            'title': f'New application from {app.business_name}',
            'date': app.created_at,
            'status': app.status,
            'icon': 'fas fa-file-alt',
            'color': 'primary'
        })
    
    # Recent deliveries
    for delivery in deliveries_in_range.order_by('-created_at')[:5]:
        recent_activities.append({
            'type': 'delivery',
            'title': f'Delivery #{delivery.serial_number} from {delivery.supplier_user.get_full_name()}',
            'date': delivery.created_at,
            'status': delivery.status,
            'icon': 'fas fa-truck',
            'color': 'success'
        })
    
    # Recent contracts
    for contract in contracts_in_range.order_by('-created_at')[:5]:
        recent_activities.append({
            'type': 'contract',
            'title': f'Contract #{contract.contract_number} awarded',
            'date': contract.created_at,
            'status': contract.status,
            'icon': 'fas fa-file-contract',
            'color': 'info'
        })
    
    # Sort by date and take top 10
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'date_from_dt': date_from_dt,
        'date_to_dt': date_to_dt,
        
        # Statistics
        'app_stats': app_stats,
        'delivery_stats': delivery_stats,
        'contract_stats': contract_stats,
        'total_delivery_value': total_delivery_value,
        
        # Performance metrics
        'delivery_performance': delivery_performance,
        'contract_performance': contract_performance,
        
        # Regional and trend data
        'regional_stats': regional_stats,
        'monthly_trends': monthly_trends,
        
        # Top performers
        'top_suppliers': top_suppliers,
        
        # Recent activities
        'recent_activities': recent_activities,
        
        # For charts (JSON data)
        'monthly_trends_json': json.dumps(monthly_trends),
        'regional_stats_json': json.dumps(list(regional_stats)),
        'app_stats_json': json.dumps(app_stats),
        'delivery_stats_json': json.dumps(delivery_stats),
        'contract_stats_json': json.dumps(contract_stats),
    }
    
    return render(request, 'backoffice/reports.html', context)


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
    
    # Create comprehensive timeline for backoffice
    timeline_events = []
    
    # 1. Application creation
    timeline_events.append({
        'type': 'application_created',
        'timestamp': application.created_at,
        'title': 'Application Submitted',
        'description': f'Application {application.tracking_code} was submitted by {application.business_name}',
        'user': application.user,
        'icon': 'fas fa-file-alt',
        'color': 'primary',
        'details': {
            'business_name': application.business_name,
            'email': application.email,
            'region': application.region.name if application.region else 'Not specified',
            'commodities_count': application.commodities_to_supply.count(),
            'submission_method': 'Public Form'
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
                'account_status': 'Active' if application.user.is_active else 'Pending Activation',
                'user_role': 'Supplier'
            }
        })
    
    # 3. Document uploads with detailed information
    for doc in document_uploads:
        file_size_mb = round(doc.file_size / (1024 * 1024), 2) if doc.file_size else 0
        timeline_events.append({
            'type': 'document_uploaded',
            'timestamp': doc.uploaded_at,
            'title': f'Document Uploaded: {doc.requirement.label}',
            'description': f'File "{doc.original_filename}" ({file_size_mb} MB) was uploaded by supplier',
            'user': None,  # Document uploads don't have uploaded_by field
            'icon': 'fas fa-upload',
            'color': 'success',
            'details': {
                'filename': doc.original_filename,
                'file_size': f"{file_size_mb} MB",
                'file_type': doc.mime_type,
                'requirement': doc.requirement.label,
                'uploaded_by': 'Supplier'
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
                    'verifier_note': doc.verifier_note if doc.verifier_note else 'No notes provided',
                    'verification_date': doc.verified_at.strftime('%Y-%m-%d %H:%M')
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
                'reviewer_comment': application.reviewer_comment if application.reviewer_comment else 'No comment provided',
                'status_change_date': application.updated_at.strftime('%Y-%m-%d %H:%M')
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
                'reviewer_comment': application.reviewer_comment if application.reviewer_comment else 'No comment provided',
                'review_status': 'In Progress'
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
                'reviewer_comment': application.reviewer_comment if application.reviewer_comment else 'No comment provided',
                'decision_maker': 'Admin Staff'
            }
        })
    
    # 8. Audit logs for other actions
    from core.models import AuditLog
    audit_logs = AuditLog.objects.filter(
        object_id=str(application.pk),
        object_type='Application'
    ).exclude(action='CREATE').order_by('timestamp')
    
    for log in audit_logs:
        action_icons = {
            'APPROVE': 'fas fa-check-circle',
            'REJECT': 'fas fa-times-circle',
            'UPDATE': 'fas fa-edit',
            'DELETE': 'fas fa-trash',
            'VIEW': 'fas fa-eye',
            'DOWNLOAD': 'fas fa-download',
            'UPLOAD': 'fas fa-upload',
            'EXPORT': 'fas fa-file-export',
            'IMPORT': 'fas fa-file-import',
            'SETTINGS_CHANGE': 'fas fa-cog',
            'PASSWORD_CHANGE': 'fas fa-key',
            'PERMISSION_CHANGE': 'fas fa-shield-alt',
            'SYSTEM_ERROR': 'fas fa-exclamation-triangle',
            'SECURITY_EVENT': 'fas fa-lock',
        }
        
        action_colors = {
            'APPROVE': 'success',
            'REJECT': 'danger',
            'UPDATE': 'primary',
            'DELETE': 'danger',
            'VIEW': 'secondary',
            'DOWNLOAD': 'success',
            'UPLOAD': 'success',
            'EXPORT': 'success',
            'IMPORT': 'success',
            'SETTINGS_CHANGE': 'warning',
            'PASSWORD_CHANGE': 'warning',
            'PERMISSION_CHANGE': 'warning',
            'SYSTEM_ERROR': 'danger',
            'SECURITY_EVENT': 'danger',
        }
        
        # Format action title
        action_title = log.get_action_display()
        
        timeline_events.append({
            'type': 'audit_log',
            'timestamp': log.timestamp,
            'title': action_title,
            'description': log.description or f"System action: {log.action}",
            'user': log.user,
            'icon': action_icons.get(log.action, 'fas fa-info-circle'),
            'color': action_colors.get(log.action, 'secondary'),
            'details': log.metadata or {}
        })
    
    # 9. Add missing documents notice if any
    if missing_documents:
        timeline_events.append({
            'type': 'missing_documents',
            'timestamp': timezone.now(),
            'title': 'Missing Documents Required',
            'description': f'{len(missing_documents)} required documents are still missing',
            'user': None,
            'icon': 'fas fa-exclamation-triangle',
            'color': 'warning',
            'details': {
                'missing_count': len(missing_documents),
                'documents': [doc['name'] for doc in missing_documents]
            }
        })
    
    # Sort timeline by timestamp (most recent first)
    timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate commodity counts
    total_commodities = application.commodities_to_supply.count()
    processed_commodities_count = application.commodities_to_supply.filter(is_processed_food=True).count()
    raw_commodities_count = application.commodities_to_supply.filter(is_processed_food=False).count()
    
    # Check if all required documents are uploaded and verified
    all_documents_uploaded = len(missing_documents) == 0
    all_documents_verified = True
    if document_status:
        for status in document_status:
            if status['is_uploaded'] and not status['is_verified']:
                all_documents_verified = False
                break
    else:
        all_documents_verified = False
    
    # Check if all documents are uploaded (not verified yet)
    has_unverified_documents = False
    if document_status:
        for status in document_status:
            if status['is_uploaded'] and not status['is_verified']:
                has_unverified_documents = True
                break
    
    # Determine action permissions
    can_approve = (application.status in ['PENDING_REVIEW', 'UNDER_REVIEW'] and 
                   all_documents_uploaded and all_documents_verified)
    can_reject = application.status in ['PENDING_REVIEW', 'UNDER_REVIEW']
    can_request_docs = (application.status in ['PENDING_REVIEW', 'UNDER_REVIEW'] and 
                       not all_documents_uploaded)
    should_show_request_docs = (application.status in ['PENDING_REVIEW', 'UNDER_REVIEW'] and 
                               not all_documents_uploaded)
    
    context = {
        'application': application,
        'team_members': team_members,
        'next_of_kin': next_of_kin,
        'bank_accounts': bank_accounts,
        'document_status': document_status,
        'gcx_proof_uploaded': gcx_proof_uploaded,
        'gcx_proof_verified': gcx_proof_verified,
        'missing_documents': missing_documents,
        'timeline_events': timeline_events,
        'can_approve': can_approve,
        'can_reject': can_reject,
        'can_request_docs': can_request_docs,
        'should_show_request_docs': should_show_request_docs,
        'all_documents_uploaded': all_documents_uploaded,
        'all_documents_verified': all_documents_verified,
        'has_unverified_documents': has_unverified_documents,
        'total_commodities': total_commodities,
        'processed_commodities_count': processed_commodities_count,
        'raw_commodities_count': raw_commodities_count,
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
    """Delivery receipts verification and review system."""
    
    # Get delivery receipts with related data
    deliveries = DeliveryTracking.objects.select_related(
        'supplier_user', 'delivery_region', 'delivery_school'
    ).prefetch_related('commodities__commodity').order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    supplier_filter = request.GET.get('supplier')
    region_filter = request.GET.get('region')
    
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)
    
    if supplier_filter:
        deliveries = deliveries.filter(supplier_user_id=supplier_filter)
    
    if region_filter:
        deliveries = deliveries.filter(delivery_region_id=region_filter)
    
    # Get filter options
    suppliers = User.objects.filter(role=User.Role.SUPPLIER).order_by('first_name', 'last_name')
    regions = Region.objects.filter(is_active=True).order_by('name')
    
    # Pagination
    paginator = Paginator(deliveries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_deliveries = DeliveryTracking.objects.count()
    pending_deliveries = DeliveryTracking.objects.filter(status='PENDING').count()
    completed_deliveries = DeliveryTracking.objects.filter(status='COMPLETED').count()
    verified_deliveries = DeliveryTracking.objects.filter(status='VERIFIED').count()
    
    context = {
        'page_obj': page_obj,
        'current_status': status_filter,
        'current_supplier': supplier_filter,
        'current_region': region_filter,
        'suppliers': suppliers,
        'regions': regions,
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'completed_deliveries': completed_deliveries,
        'verified_deliveries': verified_deliveries,
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
    
    # Send rejection notification using the working template system
    try:
        from core.template_notification_service import send_template_notification
        
        # Prepare context data for the rejection notification template
        context_data = {
            'application': application,
            'business_name': application.business_name,
            'tracking_code': application.tracking_code,
            'reason': reason,
            'rejected_at': application.rejected_at,
            'email': application.email,
            'telephone': application.telephone,
        }
        
        # Send rejection notification
        result = send_template_notification(
            template_name="Application Rejection Notification",
            recipient_email=application.email,
            recipient_phone=application.telephone,
            application=application,
            context_data=context_data,
            channel='EMAIL'
        )
        
        if result['success']:
            messages.success(request, f'Application {application.tracking_code} has been rejected. Notification sent to {application.email}.')
        else:
            messages.warning(request, f'Application rejected but failed to send notification: {result.get("message", "Unknown error")}')
            
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {str(e)}")
        messages.warning(request, f'Application rejected but failed to send notification: {str(e)}')
    
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
    notification_success_count = 0
    
    for application in applications:
        application.status = 'rejected'
        application.decided_at = timezone.now()
        application.reviewer_comment = reason
        application.save()
        count += 1
        
        # Send rejection notification using the working template system
        try:
            from core.template_notification_service import send_template_notification
            
            # Prepare context data for the rejection notification template
            context_data = {
                'application': application,
                'business_name': application.business_name,
                'tracking_code': application.tracking_code,
                'reason': reason,
                'rejected_at': application.decided_at,
                'email': application.email,
                'telephone': application.telephone,
            }
            
            # Send rejection notification
            result = send_template_notification(
                template_name="Application Rejection Notification",
                recipient_email=application.email,
                recipient_phone=application.telephone,
                application=application,
                context_data=context_data,
                channel='EMAIL'
            )
            
            if result['success']:
                notification_success_count += 1
                
        except Exception as e:
            logger.error(f"Failed to send rejection notification for application {application.tracking_code}: {str(e)}")
    
    if notification_success_count == count:
        messages.success(request, f'{count} applications have been rejected. All notifications sent successfully.')
    elif notification_success_count > 0:
        messages.warning(request, f'{count} applications have been rejected. {notification_success_count} notifications sent successfully.')
    else:
        messages.warning(request, f'{count} applications have been rejected. Failed to send notifications.')
    
    return redirect('applications:backoffice-applications')


@staff_member_required
@require_POST
def verify_document(request, pk):
    """Verify or reject a document."""
    from core.models import AuditLog
    
    document = get_object_or_404(DocumentUpload, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        verification_notes = request.POST.get('verification_notes', '')
        
        # Store old state for audit log
        old_verified = document.verified
        
        if action == 'approve':
            document.verified = True
            document.verified_at = timezone.now()
            document.verified_by = request.user
            document.verifier_note = verification_notes
            document.save()
        elif action == 'reject':
            document.verified = False
            document.verified_at = timezone.now()
            document.verified_by = request.user
            document.verifier_note = verification_notes
            document.save()
        else:
            messages.error(request, 'Invalid action.')
            return redirect('applications:backoffice-application-detail', pk=document.application.pk)
    
        # Handle GCX Registration Proof payment status
        if document.requirement.code == 'GCX_REGISTRATION_PROOF' and action == 'approve':
            application = document.application
            application.gcx_registration_proof_uploaded = True
            application.save()
        
        # Log the action
        if action == 'approve':
            action_name = 'PAYMENT_CONFIRMED' if document.requirement.code == 'GCX_REGISTRATION_PROOF' else 'DOCUMENT_VERIFIED'
            message_text = f'Document "{document.requirement.label}" has been verified'
            if document.requirement.code == 'GCX_REGISTRATION_PROOF':
                message_text += ' and payment confirmed'
            messages.success(request, message_text + '.')
        else:  # reject
            action_name = 'DOCUMENT_REJECTED'
            messages.warning(request, f'Document "{document.requirement.label}" has been rejected.')
        
        AuditLog.objects.create(
            user=request.user,
            action=action_name,
            model_name='DocumentUpload',
            object_id=str(document.pk),
            details={
                'application_tracking_code': document.application.tracking_code,
                'business_name': document.application.business_name,
                'document_type': document.requirement.label,
                'document_code': document.requirement.code,
                'filename': document.original_filename,
                'old_verified': old_verified,
                'new_verified': document.verified,
                'verification_notes': verification_notes,
                'action': action
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
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


@staff_member_required
@require_POST
def activate_supplier_account(request, pk):
    """Activate a supplier account."""
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    if not application.user:
        messages.error(request, 'No user account found for this application.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    if application.user.is_active:
        messages.warning(request, 'Account is already active.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    if application.status != SupplierApplication.ApplicationStatus.APPROVED:
        messages.error(request, 'Application must be approved before activating account.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    # Activate the user account
    application.user.is_active = True
    application.user.save()
    
    # Log the activation
    AuditLog.objects.create(
        user=request.user,
        action='ACCOUNT_ACTIVATED',
        model_name='User',
        object_id=str(application.user.id),
        details={
            'application_tracking_code': application.tracking_code,
            'business_name': application.business_name,
            'user_email': application.user.email,
            'activated_by': request.user.email
        },
        ip_address=AuditLog.get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(request, f'Account for {application.business_name} has been activated successfully.')
    return redirect('applications:backoffice-application-detail', pk=pk)


@staff_member_required
@require_POST
def deactivate_supplier_account(request, pk):
    """Deactivate a supplier account."""
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    if not application.user:
        messages.error(request, 'No user account found for this application.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    if not application.user.is_active:
        messages.warning(request, 'Account is already inactive.')
        return redirect('applications:backoffice-application-detail', pk=pk)
    
    # Deactivate the user account
    application.user.is_active = False
    application.user.save()
    
    # Log the deactivation
    AuditLog.objects.create(
        user=request.user,
        action='ACCOUNT_DEACTIVATED',
        model_name='User',
        object_id=str(application.user.id),
        details={
            'application_tracking_code': application.tracking_code,
            'business_name': application.business_name,
            'user_email': application.user.email,
            'deactivated_by': request.user.email
        },
        ip_address=AuditLog.get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(request, f'Account for {application.business_name} has been deactivated.')
    return redirect('applications:backoffice-application-detail', pk=pk)


@staff_member_required
@require_POST
def approve_application(request, pk):
    """Approve application with optional account activation"""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        data = json.loads(request.body)
        activate_account = data.get('activate_account', False)
        notes = data.get('notes', '')
        
        # Update application status
        application.status = 'APPROVED'
        application.approved_at = timezone.now()
        application.approved_by = request.user
        application.notes = notes
        application.save()
        
        # Activate account if requested
        if activate_account and application.user:
            application.user.is_active = True
            application.user.save()
            
            # Create audit log for account activation
            AuditLog.objects.create(
                user=request.user,
                action='ACCOUNT_ACTIVATED',
                model_name='User',
                object_id=str(application.user.pk),
                details={
                    'application_tracking_code': application.tracking_code,
                    'business_name': application.business_name,
                    'activated_by': request.user.get_full_name() or request.user.username
                },
                ip_address=AuditLog.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        # Create audit log for approval
        AuditLog.log_action(
            action='APPROVE',
            description=f"Application {application.tracking_code} approved by {request.user.get_full_name() or request.user.username}",
            user=request.user,
            object_type='Application',
            object_id=str(application.pk),
            object_name=f"Application {application.tracking_code}",
            request=request,
            metadata={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'approved_by': request.user.get_full_name() or request.user.username,
                'account_activated': activate_account,
                'approval_notes': notes
            }
        )
        
        # Send notification to supplier using notification API with template
        email_sent = False
        email_error = None
        
        try:
            # Import notification service and models
            from core.notification_service import send_notification_email
            from notifications.models import NotificationTemplate
            
            # Get or create the APPLICATION_APPROVED notification template
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=NotificationTemplate.NotificationType.APPLICATION_APPROVED,
                defaults={
                    'name': 'Application Approved Notification',
                    'subject': 'Application {{ tracking_code }} Approved - Ghana Commodity Exchange',
                    'body_html': '''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Application Approved - GCX Supplier Portal</title>
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                            .header { background-color: #198754; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                            .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }
                            .tracking-code { background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; font-size: 18px; font-weight: bold; margin: 20px 0; }
                            .success-box { background-color: #d1e7dd; border: 1px solid #badbcc; padding: 20px; border-radius: 5px; margin: 20px 0; }
                            .credentials-box { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin: 20px 0; }
                            .info-box { background-color: white; padding: 20px; border-radius: 5px; border-left: 4px solid #198754; margin: 20px 0; }
                            .button { display: inline-block; background-color: #198754; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                            .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 14px; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>🎉 Congratulations!</h1>
                            <p>Your Application Has Been Approved</p>
                        </div>
                        <div class="content">
                            <h2>Dear {{ business_name }},</h2>
                            <p>We are pleased to inform you that your application to become a GCX supplier has been <strong>APPROVED</strong>!</p>
                            <div class="tracking-code">Tracking Code: {{ tracking_code }}</div>
                            <div class="success-box">
                                <h3>✅ Application Status: APPROVED</h3>
                                <p>Your business has been successfully registered as a GCX supplier.</p>
                            </div>
                            {% if activate_account %}
                            <div class="credentials-box">
                                <h3>🔐 Your Account Has Been Activated</h3>
                                <p>Your supplier account has been activated and you can now log in to the supplier portal.</p>
                            </div>
                            {% else %}
                            <div class="info-box">
                                <h3>🔐 Account Activation</h3>
                                <p>Your supplier account will be activated shortly.</p>
                            </div>
                            {% endif %}
                            <div style="text-align: center;">
                                <a href="{{ login_url }}" class="button">Access Supplier Portal</a>
                            </div>
                            <div class="info-box">
                                <h3>Application Details:</h3>
                                <ul>
                                    <li><strong>Business Name:</strong> {{ business_name }}</li>
                                    <li><strong>Tracking Code:</strong> {{ tracking_code }}</li>
                                    <li><strong>Approved By:</strong> {{ approved_by }}</li>
                                    <li><strong>Approval Date:</strong> {{ approval_date }}</li>
                                </ul>
                            </div>
                            {% if approval_notes %}
                            <div class="info-box">
                                <h3>📝 Approval Notes:</h3>
                                <p>{{ approval_notes }}</p>
                            </div>
                            {% endif %}
                            <p>Welcome to the GCX family! We look forward to a successful partnership.</p>
                            <p>Best regards,<br><strong>GCX Supplier Portal Team</strong></p>
                        </div>
                        <div class="footer">
                            <p>This is an automated message. Please do not reply to this email.</p>
                            <p>&copy; 2024 Ghana Commodity Exchange. All rights reserved.</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'body_text': '''
                    Dear {{ business_name }},

                    We are pleased to inform you that your application to become a GCX supplier has been APPROVED!

                    Tracking Code: {{ tracking_code }}

                    Application Details:
                    - Business Name: {{ business_name }}
                    - Tracking Code: {{ tracking_code }}
                    - Approved By: {{ approved_by }}
                    - Approval Date: {{ approval_date }}
                    
                    {% if approval_notes %}
                    Approval Notes: {{ approval_notes }}
                    {% endif %}

                    {% if activate_account %}
                    Your account has been activated and you can now log in to the supplier portal.
                    {% else %}
                    Your supplier account will be activated shortly.
                    {% endif %}

                    Access your supplier portal at: {{ login_url }}

                    Welcome to the GCX family!

                    Best regards,
                    GCX Supplier Portal Team
                    ''',
                    'is_active': True
                }
            )
            
            # Create email context for template rendering
            context = {
                'application': application,
                'tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'approved_by': request.user.get_full_name() or request.user.username,
                'approval_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
                'activate_account': activate_account,
                'approval_notes': notes,
                'login_url': request.build_absolute_uri('/') + 'accounts/login/',
                'portal_url': request.build_absolute_uri('/')
            }
            
            # Render the template with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context))
            rendered_body_html = body_html_template.render(Context(context))
            rendered_body_text = body_text_template.render(Context(context))
            
            # Send notification using the notification API with the template
            result = send_notification_email(
                to=application.email,
                subject=rendered_subject,
                body=rendered_body_html,
                is_html=True,
                from_name="GCX eServices",
                application=application,
                template_name=template.name
            )
            
            if result['success']:
                email_sent = True
                print(f"Approval notification sent successfully to {application.email} using template: {template.name}")
            else:
                email_error = result.get('message', 'Unknown error')
                print(f"Failed to send approval notification: {email_error}")
            
        except Exception as e:
            # Log email error but don't fail the approval
            email_error = str(e)
            print(f"Failed to send approval notification email: {email_error}")
        
        # Create success message with email status
        success_message = 'Application approved successfully'
        if activate_account:
            success_message += ' and account activated'
        
        if email_sent:
            success_message += '. Notification sent to supplier.'
        else:
            success_message += f'. Notification failed ({email_error}). Please notify supplier manually.'
        
        return JsonResponse({
            'success': True,
            'message': success_message,
            'email_sent': email_sent,
            'email_error': email_error
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to approve application: {str(e)}'
        })


@staff_member_required
@require_POST
def update_application_status(request, pk):
    """Update application status"""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if new_status not in ['PENDING_REVIEW', 'UNDER_REVIEW', 'APPROVED', 'REJECTED']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid status provided'
            })
        
        old_status = application.status
        application.status = new_status
        
        if new_status == 'APPROVED':
            application.approved_at = timezone.now()
            application.approved_by = request.user
        elif new_status == 'REJECTED':
            application.rejected_at = timezone.now()
            application.rejected_by = request.user
        
        if notes:
            application.notes = notes
            
        application.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='STATUS_CHANGED',
            model_name='SupplierApplication',
            object_id=str(application.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'old_status': old_status,
                'new_status': new_status,
                'changed_by': request.user.get_full_name() or request.user.username,
                'notes': notes
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notifications based on status change
        if new_status == 'REJECTED':
            try:
                from core.template_notification_service import send_template_notification
                
                # Prepare context data for the rejection notification template
                context_data = {
                    'application': application,
                    'business_name': application.business_name,
                    'tracking_code': application.tracking_code,
                    'reason': notes or 'No specific reason provided',
                    'rejected_at': application.rejected_at,
                    'email': application.email,
                    'telephone': application.telephone,
                }
                
                # Send rejection notification
                result = send_template_notification(
                    template_name="Application Rejection Notification",
                    recipient_email=application.email,
                    recipient_phone=application.telephone,
                    application=application,
                    context_data=context_data,
                    channel='EMAIL'
                )
                
                if not result['success']:
                    logger.error(f"Failed to send rejection notification for application {application.tracking_code}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Failed to send rejection notification for application {application.tracking_code}: {str(e)}")
        
        elif new_status == 'APPROVED':
            try:
                from core.template_notification_service import send_template_notification
                
                # Prepare context data for the approval notification template
                context_data = {
                    'application': application,
                    'business_name': application.business_name,
                    'tracking_code': application.tracking_code,
                    'approved_at': application.approved_at,
                    'email': application.email,
                    'telephone': application.telephone,
                }
                
                # Send approval notification
                result = send_template_notification(
                    template_name="Application Approval with Credentials",
                    recipient_email=application.email,
                    recipient_phone=application.telephone,
                    application=application,
                    context_data=context_data,
                    channel='EMAIL'
                )
                
                if not result['success']:
                    logger.error(f"Failed to send approval notification for application {application.tracking_code}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Failed to send approval notification for application {application.tracking_code}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {new_status}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update status: {str(e)}'
        })


@staff_member_required
@require_POST
def request_documents(request, pk):
    """Request documents from supplier"""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        data = json.loads(request.body)
        message = data.get('message', '')
        send_copy = data.get('send_copy', False)
        
        if not message.strip():
            return JsonResponse({
                'success': False,
                'message': 'Document request message is required'
            })
        
        # Get missing documents for this application
        from documents.models import DocumentRequirement, DocumentUpload
        required_documents = DocumentRequirement.objects.filter(is_active=True)
        document_uploads = DocumentUpload.objects.filter(application=application)
        
        missing_docs_list = []
        for req_doc in required_documents:
            uploaded_doc = document_uploads.filter(requirement=req_doc).first()
            if req_doc.is_required and not uploaded_doc:
                missing_docs_list.append({
                    'name': req_doc.label,
                    'code': req_doc.code,
                    'description': req_doc.description or ''
                })
        
        # Create outstanding document request
        OutstandingDocumentRequest.objects.create(
            application=application,
            requested_by=request.user,
            message=message,
            is_resolved=False
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='DOCUMENTS_REQUESTED',
            model_name='SupplierApplication',
            object_id=str(application.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'requested_by': request.user.get_full_name() or request.user.username,
                'request_message': message
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notification to supplier using notification template
        email_sent = False
        email_error = None
        
        try:
            # Import notification service and models
            from core.notification_service import send_notification_email
            from notifications.models import NotificationTemplate
            
            # Get or update the DOCUMENTS_REQUESTED notification template
            template, created = NotificationTemplate.objects.update_or_create(
                notification_type=NotificationTemplate.NotificationType.DOCUMENTS_REQUESTED,
                defaults={
                    'name': 'Documents Requested Notification',
                    'subject': 'Additional Documents Required - Application {{ tracking_code }}',
                    'body_html': '''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Additional Documents Required - GCX Supplier Portal</title>
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                            .header { background: linear-gradient(135deg, #ffc107, #ff8c00); color: #000; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }
                            .header h1 { margin: 0; font-size: 24px; }
                            .content { background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }
                            .tracking-code { background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; text-align: center; font-size: 16px; font-weight: bold; margin: 20px 0; color: #111827; }
                            .message-box { background-color: #fffbeb; border-left: 4px solid #ffc107; padding: 20px; border-radius: 5px; margin: 20px 0; white-space: pre-wrap; }
                            .docs-box { background-color: #fee2e2; border: 1px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0; }
                            .docs-box h3 { margin-top: 0; color: #991b1b; }
                            .docs-list { list-style: none; padding: 0; margin: 15px 0; }
                            .docs-list li { padding: 10px; background: #ffffff; margin-bottom: 8px; border-radius: 5px; border-left: 3px solid #ef4444; }
                            .docs-list li strong { color: #111827; }
                            .button { display: inline-block; background: linear-gradient(135deg, #ffc107, #ff8c00); color: #000; padding: 14px 32px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3); }
                            .button:hover { box-shadow: 0 6px 16px rgba(255, 193, 7, 0.4); }
                            .info-box { background-color: #f9fafb; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; margin: 20px 0; }
                            .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 13px; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>📄 Additional Documents Required</h1>
                            <p style="margin: 5px 0 0 0; opacity: 0.9;">GCX Supplier Application Portal</p>
                        </div>
                        <div class="content">
                            <div class="tracking-code">Application: {{ tracking_code }}</div>
                            
                            {% if missing_count > 0 %}
                            <div class="docs-box">
                                <h3>⚠️ Missing Documents ({{ missing_count }})</h3>
                                <p>The following documents are required to proceed with your application:</p>
                                <ul class="docs-list">
                                    {% for doc in missing_documents %}
                                    <li>
                                        <strong>{{ doc.name }}</strong>
                                        {% if doc.description %}<br><small style="color: #6b7280;">{{ doc.description }}</small>{% endif %}
                                    </li>
                                    {% endfor %}
                                </ul>
                            </div>
                            {% endif %}
                            
                            <div class="message-box">{{ request_message }}</div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{ upload_url }}" class="button">📤 Upload Documents Now</a>
                            </div>
                            
                            <div class="info-box">
                                <h4 style="margin-top: 0;">📋 Document Requirements:</h4>
                                <ul style="margin: 10px 0; padding-left: 20px;">
                                    <li>All documents must be in <strong>PDF, JPG, or PNG</strong> format</li>
                                    <li>Maximum file size: <strong>10MB</strong> per document</li>
                                    <li>Documents must be <strong>clear and legible</strong></li>
                                    <li>All documents must be <strong>current and valid</strong></li>
                                </ul>
                            </div>
                            
                            <div class="info-box">
                                <p style="margin: 0;"><strong>📞 Need Help?</strong></p>
                                <p style="margin: 10px 0 0 0;">Contact our support team at <strong>membership@gcx.com.gh</strong> or call <strong>+233 302 937 677</strong></p>
                            </div>
                            
                            <p style="margin-top: 30px;">Best regards,<br><strong>GCX Supplier Portal Team</strong></p>
                        </div>
                        <div class="footer">
                            <p style="margin: 5px 0;">This is an automated message from GCX Supplier Portal</p>
                            <p style="margin: 5px 0;">&copy; {{ request_date|slice:"-4:" }} Ghana Commodity Exchange. All rights reserved.</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'body_text': '''
ADDITIONAL DOCUMENTS REQUIRED
GCX Supplier Application Portal

Application: {{ tracking_code }}

{% if missing_count > 0 %}
⚠️ Missing Documents ({{ missing_count }}):
{% for doc in missing_documents %}
- {{ doc.name }}{% if doc.description %} ({{ doc.description }}){% endif %}
{% endfor %}
{% endif %}

MESSAGE FROM GCX ADMIN:
{{ request_message }}

📋 DOCUMENT REQUIREMENTS:
- All documents must be in PDF, JPG, or PNG format
- Maximum file size: 10MB per document
- Documents must be clear and legible
- All documents must be current and valid

UPLOAD YOUR DOCUMENTS:
{{ upload_url }}

📞 NEED HELP?
Contact our support team:
Email: membership@gcx.com.gh
Phone: +233 302 937 677

Best regards,
GCX Supplier Portal Team

---
This is an automated message from GCX Supplier Portal
© {{ request_date|slice:"-4:" }} Ghana Commodity Exchange. All rights reserved.
                    ''',
                    'is_active': True
                }
            )
            
            # Create email context for template rendering
            context = {
                'application': application,
                'tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'requested_by': request.user.get_full_name() or request.user.username,
                'request_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
                'request_message': message,
                'missing_documents': missing_docs_list,
                'missing_count': len(missing_docs_list),
                'upload_url': request.build_absolute_uri('/') + f'accounts/applications/{application.pk}/upload/',
                'portal_url': request.build_absolute_uri('/')
            }
            
            # Render the template with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context))
            rendered_body_html = body_html_template.render(Context(context))
            rendered_body_text = body_text_template.render(Context(context))
            
            # Send notification using the notification API with the template
            result = send_notification_email(
                to=application.email,
                subject=rendered_subject,
                body=rendered_body_html,
                is_html=True,
                from_name="GCX eServices",
                application=application,
                template_name=template.name
            )
            
            if result['success']:
                email_sent = True
                print(f"Document request notification sent successfully to {application.email} using template: {template.name}")
                
                # Send copy to admin if requested
                if send_copy and request.user.email:
                    try:
                        copy_result = send_notification_email(
                            to=request.user.email,
                            subject=f"Copy: {rendered_subject}",
                            body=rendered_body_html,
                            is_html=True,
                            from_name="GCX eServices",
                            application=application,
                            template_name=f"{template.name} (Copy)"
                        )
                        if copy_result['success']:
                            print(f"Email copy sent to admin: {request.user.email}")
                    except Exception as copy_error:
                        print(f"Failed to send email copy to admin: {copy_error}")
            else:
                email_error = result.get('message', 'Unknown error')
                print(f"Failed to send document request notification: {email_error}")
            
        except Exception as e:
            # Log email error but don't fail the request
            email_error = str(e)
            print(f"Failed to send document request notification email: {email_error}")
        
        # Create response message with email status
        response_message = 'Document request sent to supplier'
        if email_sent:
            response_message += ' and notification sent'
        elif email_error:
            response_message += f' but notification failed ({email_error}). Please notify supplier manually.'
        
        return JsonResponse({
            'success': True,
            'message': response_message,
            'email_sent': email_sent,
            'email_error': email_error
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to send document request: {str(e)}'
        })


@staff_member_required
@require_POST
def activate_supplier_account(request, pk):
    """Activate supplier account"""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        if not application.user:
            return JsonResponse({
                'success': False,
                'message': 'No user account found for this application'
            })
        
        if application.user.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Account is already active'
            })
        
        application.user.is_active = True
        application.user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='ACCOUNT_ACTIVATED',
            model_name='User',
            object_id=str(application.user.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'activated_by': request.user.get_full_name() or request.user.username
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier account activated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to activate account: {str(e)}'
        })


@staff_member_required
@require_POST
def send_notification(request, pk):
    """Send notification to supplier"""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message.strip():
            return JsonResponse({
                'success': False,
                'message': 'Notification message is required'
            })
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='NOTIFICATION_SENT',
            model_name='SupplierApplication',
            object_id=str(application.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'sent_by': request.user.get_full_name() or request.user.username,
                'notification_message': message
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notification to supplier using notification template
        email_sent = False
        email_error = None
        
        try:
            # Import notification service and models
            from core.notification_service import send_notification_email
            from notifications.models import NotificationTemplate
            
            # Get or create the ADMIN_NOTIFICATION notification template
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=NotificationTemplate.NotificationType.ADMIN_NOTIFICATION,
                defaults={
                    'name': 'Admin Notification',
                    'subject': 'Notification - Application {{ tracking_code }}',
                    'body_html': '''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Notification - GCX Supplier Portal</title>
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                            .header { background-color: #6c757d; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                            .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }
                            .tracking-code { background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; font-size: 18px; font-weight: bold; margin: 20px 0; }
                            .info-box { background-color: white; padding: 20px; border-radius: 5px; border-left: 4px solid #6c757d; margin: 20px 0; }
                            .button { display: inline-block; background-color: #6c757d; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                            .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 14px; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>📢 Notification</h1>
                            <p>Important Update</p>
                        </div>
                        <div class="content">
                            <h2>Dear {{ business_name }},</h2>
                            <p>We have an important update regarding your application.</p>
                            <div class="tracking-code">Tracking Code: {{ tracking_code }}</div>
                            <div class="info-box">
                                <h3>📝 Message from GCX Team:</h3>
                                <p>{{ notification_message }}</p>
                            </div>
                            <div style="text-align: center;">
                                <a href="{{ portal_url }}" class="button">Access Portal</a>
                            </div>
                            <div class="info-box">
                                <h3>Application Details:</h3>
                                <ul>
                                    <li><strong>Business Name:</strong> {{ business_name }}</li>
                                    <li><strong>Tracking Code:</strong> {{ tracking_code }}</li>
                                    <li><strong>Sent By:</strong> {{ sent_by }}</li>
                                    <li><strong>Date:</strong> {{ notification_date }}</li>
                                </ul>
                            </div>
                            <p>If you have any questions, please contact our support team.</p>
                            <p>Best regards,<br><strong>GCX Supplier Portal Team</strong></p>
                        </div>
                        <div class="footer">
                            <p>This is an automated message. Please do not reply to this email.</p>
                            <p>&copy; 2024 Ghana Commodity Exchange. All rights reserved.</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'body_text': '''
                    Dear {{ business_name }},

                    We have an important update regarding your application.

                    Tracking Code: {{ tracking_code }}

                    Message from GCX Team: {{ notification_message }}

                    Application Details:
                    - Business Name: {{ business_name }}
                    - Tracking Code: {{ tracking_code }}
                    - Sent By: {{ sent_by }}
                    - Date: {{ notification_date }}

                    Access your portal at: {{ portal_url }}

                    If you have any questions, please contact our support team.

                    Best regards,
                    GCX Supplier Portal Team
                    ''',
                    'is_active': True
                }
            )
            
            # Create email context for template rendering
            context = {
                'application': application,
                'tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'sent_by': request.user.get_full_name() or request.user.username,
                'notification_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
                'notification_message': message,
                'portal_url': request.build_absolute_uri('/'),
                'upload_url': request.build_absolute_uri('/') + f'accounts/applications/{application.pk}/upload/'
            }
            
            # Render the template with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context))
            rendered_body_html = body_html_template.render(Context(context))
            rendered_body_text = body_text_template.render(Context(context))
            
            # Send notification using the notification API with the template
            result = send_notification_email(
                to=application.email,
                subject=rendered_subject,
                body=rendered_body_html,
                is_html=True,
                from_name="GCX eServices",
                application=application,
                template_name=template.name
            )
            
            if result['success']:
                email_sent = True
                print(f"Notification sent successfully to {application.email} using template: {template.name}")
            else:
                email_error = result.get('message', 'Unknown error')
                print(f"Failed to send notification: {email_error}")
            
        except Exception as e:
            # Log email error but don't fail the notification
            email_error = str(e)
            print(f"Failed to send notification email: {email_error}")
        
        # Create response message with email status
        response_message = 'Notification sent to supplier'
        if email_sent:
            response_message += ' and email delivered'
        elif email_error:
            response_message += f' but email failed ({email_error}). Please notify supplier manually.'
        
        return JsonResponse({
            'success': True,
            'message': response_message,
            'email_sent': email_sent,
            'email_error': email_error
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to send notification: {str(e)}'
        })


@staff_member_required
@require_POST
def add_application_notes(request, pk):
    """Add notes to application"""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        data = json.loads(request.body)
        notes = data.get('notes', '')
        
        if not notes.strip():
            return JsonResponse({
                'success': False,
                'message': 'Notes content is required'
            })
        
        # Append to existing notes or create new
        if application.notes:
            application.notes += f"\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {request.user.get_full_name() or request.user.username}: {notes}"
        else:
            application.notes = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {request.user.get_full_name() or request.user.username}: {notes}"
        
        application.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='NOTES_ADDED',
            model_name='SupplierApplication',
            object_id=str(application.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'added_by': request.user.get_full_name() or request.user.username,
                'notes_content': notes
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Notes added to application'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to add notes: {str(e)}'
        })


@staff_member_required
def supplier_detail(request, pk):
    """Detailed view of a supplier with contracts, SRVs, and invoices."""
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    # Get related data
    team_members = application.team_members.all()
    next_of_kin = application.next_of_kin.all()
    bank_accounts = application.bank_accounts.all()
    
    # Get contracts
    from .models import SupplierContract, StoreReceiptVoucher, Invoice
    contracts = SupplierContract.objects.filter(application=application).order_by('-created_at')
    
    # Get SRVs for this supplier
    srvs = StoreReceiptVoucher.objects.filter(supplier=application.user).order_by('-created_at')
    
    # Get invoices for this supplier
    invoices = Invoice.objects.filter(supplier=application.user).order_by('-created_at')
    
    # Get contract document requirements and documents
    contract_requirements = ContractDocumentRequirement.objects.filter(is_active=True).order_by('label')
    contract_documents = ContractDocument.objects.filter(status='ACTIVE').order_by('-created_at')
    
    # Get contract signings for this supplier
    contract_signings = ContractSigning.objects.filter(supplier=application.user).order_by('-created_at')
    
    # Calculate summary statistics
    total_contracts = contracts.count()
    active_contracts = contracts.filter(status='ACTIVE').count()
    total_contract_value = sum(contract.contract_value or 0 for contract in contracts if contract.contract_value)
    
    total_srvs = srvs.count()
    pending_srvs = srvs.filter(status='PENDING').count()
    approved_srvs = srvs.filter(status='APPROVED').count()
    
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(status='PAID').count()
    overdue_invoices = invoices.filter(status='OVERDUE').count()
    total_invoice_amount = sum(invoice.total_amount for invoice in invoices)
    total_paid_amount = sum(invoice.paid_amount for invoice in invoices)
    
    # Recent activity (last 10 items)
    recent_activity = []
    
    # Add contract activities
    for contract in contracts[:5]:
        recent_activity.append({
            'type': 'contract',
            'object': contract,
            'date': contract.created_at,
            'action': f"Contract {contract.contract_number} created"
        })
    
    # Add SRV activities
    for srv in srvs[:3]:
        recent_activity.append({
            'type': 'srv',
            'object': srv,
            'date': srv.created_at,
            'action': f"SRV {srv.srv_number} created"
        })
    
    # Add invoice activities
    for invoice in invoices[:2]:
        recent_activity.append({
            'type': 'invoice',
            'object': invoice,
            'date': invoice.created_at,
            'action': f"Invoice {invoice.invoice_number} created"
        })
    
    # Sort by date
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:10]
    
    context = {
        'application': application,
        'team_members': team_members,
        'next_of_kin': next_of_kin,
        'bank_accounts': bank_accounts,
        'contracts': contracts,
        'srvs': srvs,
        'invoices': invoices,
        'contract_requirements': contract_requirements,
        'contract_documents': contract_documents,
        'contract_signings': contract_signings,
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'total_contract_value': total_contract_value,
        'total_srvs': total_srvs,
        'pending_srvs': pending_srvs,
        'approved_srvs': approved_srvs,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_invoice_amount': total_invoice_amount,
        'total_paid_amount': total_paid_amount,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'backoffice/supplier_detail_new.html', context)


@staff_member_required
def award_contract_page(request, pk):
    """Display the contract awarding page."""
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    # Get static and dynamic documents
    static_documents = ContractDocument.objects.filter(
        category='STATIC',
        status='ACTIVE',
        is_current_version=True
    ).select_related('requirement')
    
    dynamic_documents = ContractDocument.objects.filter(
        category='DYNAMIC',
        status='ACTIVE',
        is_current_version=True
    ).select_related('requirement')
    
    context = {
        'application': application,
        'static_documents': static_documents,
        'dynamic_documents': dynamic_documents,
    }
    
    return render(request, 'backoffice/award_contract.html', context)


@staff_member_required
@require_POST
def verify_document(request, pk):
    """Verify an uploaded document for an application."""
    import json
    from django.http import JsonResponse
    from documents.models import DocumentUpload, DocumentRequirement
    
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        # Parse request body
        data = json.loads(request.body)
        document_type = data.get('document_type')
        notes = data.get('notes', '')
        
        if not document_type:
            return JsonResponse({'success': False, 'message': 'Document type is required'})
        
        # Find the document requirement
        requirement = DocumentRequirement.objects.filter(code=document_type).first()
        if not requirement:
            return JsonResponse({'success': False, 'message': 'Document requirement not found'})
        
        # Find the uploaded document
        document_upload = DocumentUpload.objects.filter(
            application=application,
            requirement=requirement
        ).first()
        
        if not document_upload:
            return JsonResponse({'success': False, 'message': 'No uploaded document found'})
        
        # Verify the document
        document_upload.verified = True
        document_upload.verified_at = timezone.now()
        document_upload.verified_by = request.user
        if notes:
            document_upload.verifier_note = notes
        document_upload.save()
        
        # Log the verification
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='DOCUMENT_VERIFIED',
            model_name='DocumentUpload',
            object_id=str(document_upload.id),
            description=f"Verified {requirement.label} for {application.business_name}",
            details={
                'document_type': document_type,
                'document_label': requirement.label,
                'notes': notes
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Document verified successfully'
        })
        
    except Exception as e:
        logger.error(f"Error verifying document: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@staff_member_required
@require_POST
def award_contract(request, pk):
    """Award a contract to a supplier with document assignment."""
    
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        # Create contract
        contract = SupplierContract.objects.create(
            application=application,
            contract_number=request.POST.get('contract_number'),
            title=f"Contract {request.POST.get('contract_number')}",
            description=request.POST.get('description', ''),
            contract_type=request.POST.get('contract_type'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            contract_value=0.00,
            currency='GHS',
            status='ACTIVE'
        )
        
        # Assign static documents to the contract
        static_documents = ContractDocument.objects.filter(
            category='STATIC',
            status='ACTIVE',
            is_current_version=True
        )
        
        for document in static_documents:
            ContractDocumentAssignment.objects.create(
                contract=contract,
                document=document,
                is_required=True,
                assigned_by=request.user
            )
        
        # Handle dynamic documents (assign as templates for suppliers to sign)
        dynamic_docs = ContractDocument.objects.filter(
            category='DYNAMIC',
            status='ACTIVE',
            is_current_version=True
        )
        
        for dynamic_doc in dynamic_docs:
            # Check if a file was uploaded for this dynamic document
            file_key = f'dynamic_doc_{dynamic_doc.id}'
            if file_key in request.FILES:
                doc_file = request.FILES[file_key]
                
                # Update the dynamic document with the uploaded file (this becomes the template)
                dynamic_doc.document_file = doc_file
                dynamic_doc.save()
            
            # Assign the dynamic document to the contract (as a template for signing)
            ContractDocumentAssignment.objects.create(
                contract=contract,
                document=dynamic_doc,
                is_required=True,
                assigned_by=request.user
            )
        
        # Create contract signing record
        ContractSigning.objects.create(
            contract=contract,
            supplier=application.user,
            status='PENDING'
        )
        
        # Log the activity
        total_docs = static_documents.count() + dynamic_docs.count()
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_AWARDED',
            model_name='SupplierContract',
            object_id=str(contract.pk),
            details={'message': f'Contract {contract.contract_number} awarded to {application.business_name} with {total_docs} documents'}
        )
        
        # Send contract awarded notification
        try:
            from core.contract_delivery_notifications import send_contract_awarded_notification
            send_contract_awarded_notification(contract, application.user)
        except Exception as e:
            logger.error(f"Failed to send contract awarded notification: {str(e)}")
        
        messages.success(request, f'Contract {contract.contract_number} has been successfully awarded to {application.business_name}')
        return redirect('applications:backoffice-supplier-detail', pk=pk)
        
    except Exception as e:
        logger.error(f"Error awarding contract to supplier {pk}: {str(e)}")
        messages.error(request, f'Error awarding contract: {str(e)}')
        return redirect('applications:backoffice-supplier-detail', pk=pk)


@staff_member_required
@require_POST
def activate_supplier_account(request, user_id):
    """Activate a supplier account."""
    try:
        user = get_object_or_404(User, pk=user_id)
        user.is_active = True
        user.save()
        
        # Log the activity
        AuditLog.objects.create(
            user=request.user,
            action='ACCOUNT_ACTIVATED',
            resource_type='User',
            resource_id=user.pk,
            details=f'Supplier account activated for {user.get_full_name()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Account for {user.get_full_name()} has been activated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error activating account {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error activating account: {str(e)}'
        })


@staff_member_required
@require_POST
def deactivate_supplier_account(request, user_id):
    """Deactivate a supplier account."""
    try:
        user = get_object_or_404(User, pk=user_id)
        user.is_active = False
        user.save()
        
        # Log the activity
        AuditLog.objects.create(
            user=request.user,
            action='ACCOUNT_DEACTIVATED',
            resource_type='User',
            resource_id=user.pk,
            details=f'Supplier account deactivated for {user.get_full_name()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Account for {user.get_full_name()} has been deactivated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deactivating account {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deactivating account: {str(e)}'
        })


@staff_member_required
@require_POST
def upload_contract_document(request):
    """Upload contract documents using dynamic form."""
    try:
        from .forms import ContractDocumentUploadForm
        
        form = ContractDocumentUploadForm(request.POST, request.FILES)
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Form validation failed',
                'errors': form.errors
            })
        
        uploaded_documents = []
        
        # Process each uploaded file
        for field_name, file in form.cleaned_data.items():
            if field_name.startswith('document_') and file:
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Create contract document
                    document = ContractDocument.objects.create(
                        requirement=requirement,
                        title=requirement.label,
                        description=requirement.description,
                        version='1.0',
                        status='ACTIVE',
                        effective_from=timezone.now().date(),
                        is_current_version=True,
                        document_file=file,
                        created_by=request.user
                    )
                    
                    uploaded_documents.append(document)
                    
                except ContractDocumentRequirement.DoesNotExist:
                    continue
        
        # Log the activity
        if uploaded_documents:
            AuditLog.objects.create(
                user=request.user,
                action='DOCUMENT_UPLOADED',
                resource_type='ContractDocument',
                resource_id=uploaded_documents[0].pk,
                details=f'{len(uploaded_documents)} contract documents uploaded'
            )
        
        return JsonResponse({
            'success': True,
            'message': f'{len(uploaded_documents)} contract document(s) uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading contract document: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error uploading document: {str(e)}'
        })


@staff_member_required
@require_POST
def upload_contract(request, pk):
    """Upload a contract for a supplier."""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        # Get form data
        contract_number = request.POST.get('contract_number')
        contract_type = request.POST.get('contract_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        contract_value = request.POST.get('contract_value')
        currency = request.POST.get('currency', 'GHS')
        contract_file = request.FILES.get('contract_file')
        
        # Validate required fields
        if not all([contract_number, contract_type, title, start_date, end_date, contract_file]):
            return JsonResponse({
                'success': False,
                'message': 'All required fields must be provided'
            })
        
        # Create contract
        from .models import SupplierContract
        contract = SupplierContract.objects.create(
            application=application,
            contract_number=contract_number,
            contract_type=contract_type,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            contract_value=contract_value if contract_value else None,
            currency=currency,
            contract_file=contract_file,
            created_by=request.user
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='CONTRACT_UPLOADED',
            model_name='SupplierContract',
            object_id=str(contract.pk),
            details={
                'application_tracking_code': application.tracking_code,
                'business_name': application.business_name,
                'contract_number': contract_number,
                'contract_type': contract_type,
                'title': title,
                'uploaded_by': request.user.get_full_name() or request.user.username
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contract uploaded successfully',
            'contract_id': contract.pk
        })
        
    except Exception as e:
        logger.error(f"Error uploading contract for application {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to upload contract: {str(e)}'
        })


@staff_member_required
@require_POST
def create_srv(request, pk):
    """Create a Store Receipt Voucher for a contract."""
    try:
        from .models import SupplierContract, StoreReceiptVoucher
        contract = get_object_or_404(SupplierContract, pk=pk)
        
        # Get form data
        srv_number = request.POST.get('srv_number')
        srv_date = request.POST.get('srv_date')
        description = request.POST.get('description')
        delivery_location = request.POST.get('delivery_location')
        delivery_date = request.POST.get('delivery_date')
        items_description = request.POST.get('items_description')
        total_quantity = request.POST.get('total_quantity')
        unit_of_measure = request.POST.get('unit_of_measure')
        unit_price = request.POST.get('unit_price')
        currency = request.POST.get('currency', 'GHS')
        srv_document = request.FILES.get('srv_document')
        
        # Validate required fields
        if not all([srv_number, srv_date, description, delivery_location, delivery_date, 
                   items_description, total_quantity, unit_of_measure, unit_price]):
            return JsonResponse({
                'success': False,
                'message': 'All required fields must be provided'
            })
        
        # Create SRV
        srv = StoreReceiptVoucher.objects.create(
            contract=contract,
            srv_number=srv_number,
            srv_date=srv_date,
            description=description,
            delivery_location=delivery_location,
            delivery_date=delivery_date,
            items_description=items_description,
            total_quantity=total_quantity,
            unit_of_measure=unit_of_measure,
            unit_price=unit_price,
            currency=currency,
            srv_document=srv_document,
            created_by=request.user
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='SRV_CREATED',
            model_name='StoreReceiptVoucher',
            object_id=str(srv.pk),
            details={
                'application_tracking_code': contract.application.tracking_code,
                'business_name': contract.application.business_name,
                'contract_number': contract.contract_number,
                'srv_number': srv_number,
                'created_by': request.user.get_full_name() or request.user.username
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'SRV created successfully',
            'srv_id': srv.pk
        })
        
    except Exception as e:
        logger.error(f"Error creating SRV for contract {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to create SRV: {str(e)}'
        })


@staff_member_required
@require_POST
def create_invoice(request, pk):
    """Create an invoice for an SRV."""
    try:
        from .models import StoreReceiptVoucher, Invoice
        srv = get_object_or_404(StoreReceiptVoucher, pk=pk)
        
        # Get form data
        invoice_number = request.POST.get('invoice_number')
        invoice_date = request.POST.get('invoice_date')
        due_date = request.POST.get('due_date')
        subtotal = request.POST.get('subtotal')
        tax_rate = request.POST.get('tax_rate', 0)
        payment_terms = request.POST.get('payment_terms', 'NET_30')
        currency = request.POST.get('currency', 'GHS')
        notes = request.POST.get('notes', '')
        invoice_document = request.FILES.get('invoice_document')
        
        # Validate required fields
        if not all([invoice_number, invoice_date, due_date, subtotal]):
            return JsonResponse({
                'success': False,
                'message': 'All required fields must be provided'
            })
        
        # Create invoice
        invoice = Invoice.objects.create(
            srv=srv,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            subtotal=subtotal,
            tax_rate=tax_rate,
            payment_terms=payment_terms,
            currency=currency,
            notes=notes,
            invoice_document=invoice_document,
            created_by=request.user
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='INVOICE_CREATED',
            model_name='Invoice',
            object_id=str(invoice.pk),
            details={
                'application_tracking_code': srv.contract.application.tracking_code,
                'business_name': srv.contract.application.business_name,
                'contract_number': srv.contract.contract_number,
                'srv_number': srv.srv_number,
                'invoice_number': invoice_number,
                'created_by': request.user.get_full_name() or request.user.username
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Invoice created successfully',
            'invoice_id': invoice.pk
        })
        
    except Exception as e:
        logger.error(f"Error creating invoice for SRV {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to create invoice: {str(e)}'
        })


@staff_member_required
def delivery_detail(request, pk):
    """Detailed view of a delivery receipt with all information and supporting documents."""
    
    try:
        # Get the delivery with all related data
        delivery = get_object_or_404(
            DeliveryTracking.objects.select_related(
                'supplier_user',
                'delivery_region', 
                'delivery_school'
            ).prefetch_related(
                'commodities__commodity'
            ),
            pk=pk
        )
        
        # Get all commodities delivered
        commodities = delivery.commodities.all()
        
        # Get supporting documents (SRV, Waybill, Invoice)
        supporting_documents = []
        
        # Debug: Log document status
        logger.info(f"Delivery {delivery.pk} documents: SRV={bool(delivery.srv_document)}, Waybill={bool(delivery.waybill_document)}, Invoice={bool(delivery.invoice_document)}")
        
        # Check for SRV document
        if delivery.srv_document:
            supporting_documents.append({
                'type': 'SRV',
                'name': f'SRV #{delivery.srv_number}',
                'file': delivery.srv_document,
                'date': delivery.delivery_date,
                'description': 'Store Receipt Voucher'
            })
        
        # Check for Waybill document
        if delivery.waybill_document:
            supporting_documents.append({
                'type': 'Waybill',
                'name': f'Waybill #{delivery.waybill_number}',
                'file': delivery.waybill_document,
                'date': delivery.delivery_date,
                'description': 'Waybill Document'
            })
        
        # Check for Invoice document
        if delivery.invoice_document:
            supporting_documents.append({
                'type': 'Invoice',
                'name': f'Invoice #{delivery.invoice_number}',
                'file': delivery.invoice_document,
                'date': delivery.delivery_date,
                'description': 'Invoice Document'
            })
        
        logger.info(f"Found {len(supporting_documents)} supporting documents for delivery {delivery.pk}")
        
        # Get delivery statistics
        total_commodities = commodities.count()
        total_quantity = sum(commodity.quantity for commodity in commodities)
        
        # Get related contract information if available
        contract = None
        if delivery.contract_commodity and delivery.contract_commodity.contract:
            contract = delivery.contract_commodity.contract
        
        # Get supplier's other deliveries for context
        supplier_deliveries = DeliveryTracking.objects.filter(
            supplier_user=delivery.supplier_user
        ).exclude(pk=pk).order_by('-created_at')[:5]
        
        context = {
            'delivery': delivery,
            'commodities': commodities,
            'supporting_documents': supporting_documents,
            'contract': contract,
            'supplier_deliveries': supplier_deliveries,
            'total_commodities': total_commodities,
            'total_quantity': total_quantity,
            'page_title': f'Delivery #{delivery.serial_number}',
        }
        
        return render(request, 'backoffice/delivery_detail_verification.html', context)
        
    except Exception as e:
        logger.error(f"Error loading delivery detail {pk}: {str(e)}")
        messages.error(request, f'Error loading delivery details: {str(e)}')    
        return redirect('backoffice-documents')


def contract_deliveries(request, contract_pk):
    """View all delivery receipts for a specific contract."""
    contract = get_object_or_404(
        SupplierContract.objects.select_related('application', 'application__user'),
        pk=contract_pk
    )
    
    # Get all deliveries for this contract
    deliveries = DeliveryTracking.objects.filter(
        contract=contract
    ).select_related(
        'delivery_region',
        'delivery_school',
        'supplier_user'
    ).prefetch_related(
        'commodities__commodity'
    ).order_by('-created_at')
    
    # Get delivery statistics
    total_deliveries = deliveries.count()
    pending_deliveries = deliveries.filter(status='PENDING').count()
    delivered = deliveries.filter(status='DELIVERED').count()
    verified = deliveries.filter(status='VERIFIED').count()
    
    context = {
        'contract': contract,
        'deliveries': deliveries,
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'delivered': delivered,
        'verified': verified,
    }
    
    return render(request, 'backoffice/contract_deliveries.html', context)


@staff_member_required
@require_POST
def verify_delivery(request, pk):
    """Verify a delivery receipt."""
    try:
        delivery = get_object_or_404(DeliveryTracking, pk=pk)
        
        # Update delivery status
        delivery.status = 'VERIFIED'
        delivery.verified_at = timezone.now()
        delivery.verified_by = request.user
        delivery.save()
        
        # Create audit log
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='DELIVERY_VERIFIED',
            model_name='DeliveryTracking',
            object_id=str(delivery.pk),
            details={
                'delivery_number': delivery.serial_number,
                'supplier': delivery.supplier_user.get_full_name() or delivery.supplier_user.username,
                'school': delivery.delivery_school.name,
                'region': delivery.delivery_region.name,
                'verified_by': request.user.get_full_name() or request.user.username,
                'verification_date': timezone.now().isoformat()
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send delivery verified notification
        try:
            from core.contract_delivery_notifications import send_delivery_verified_notification
            send_delivery_verified_notification(delivery)
        except Exception as e:
            logger.error(f"Failed to send delivery verified notification: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Delivery {delivery.serial_number} has been verified successfully'
        })
        
    except Exception as e:
        logger.error(f"Error verifying delivery {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to verify delivery: {str(e)}'
        })


@staff_member_required
@require_POST
def reject_delivery(request, pk):
    """Reject a delivery receipt."""
    try:
        delivery = get_object_or_404(DeliveryTracking, pk=pk)
        
        # Get rejection reason
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            })
        
        # Update delivery status
        delivery.status = 'REJECTED'
        delivery.rejected_at = timezone.now()
        delivery.rejected_by = request.user
        delivery.rejection_reason = rejection_reason
        delivery.save()
        
        # Create audit log
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='DELIVERY_REJECTED',
            model_name='DeliveryTracking',
            object_id=str(delivery.pk),
            details={
                'delivery_number': delivery.serial_number,
                'supplier': delivery.supplier_user.get_full_name() or delivery.supplier_user.username,
                'school': delivery.delivery_school.name,
                'region': delivery.delivery_region.name,
                'rejected_by': request.user.get_full_name() or request.user.username,
                'rejection_reason': rejection_reason,
                'rejection_date': timezone.now().isoformat()
            },
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send delivery rejected notification
        try:
            from core.contract_delivery_notifications import send_delivery_rejected_notification
            send_delivery_rejected_notification(delivery)
        except Exception as e:
            logger.error(f"Failed to send delivery rejected notification: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Delivery {delivery.serial_number} has been rejected'
        })
        
    except Exception as e:
        logger.error(f"Error rejecting delivery {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to reject delivery: {str(e)}'
        })


@staff_member_required
def export_reports(request):
    """
    Export comprehensive reports data with customizable field selection.
    """
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Default to last 30 days if no dates provided
    if not date_from or not date_to:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
    
    # Convert string dates to date objects
    start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Get export format
    export_format = request.GET.get('format', 'csv')
    
    # Get selected data types
    selected_types = request.GET.getlist('data_types')
    if not selected_types:
        selected_types = ['applications', 'deliveries', 'contracts', 'suppliers']
    
    # Get selected fields for each data type
    application_fields = request.GET.getlist('application_fields')
    delivery_fields = request.GET.getlist('delivery_fields')
    contract_fields = request.GET.getlist('contract_fields')
    supplier_fields = request.GET.getlist('supplier_fields')
    
    # Default fields if none selected
    if not application_fields:
        application_fields = ['id', 'business_name', 'contact_person', 'email', 'phone', 'status', 'created_at']
    if not delivery_fields:
        delivery_fields = ['serial_number', 'supplier_user__username', 'delivery_school__name', 'delivery_region__name', 'status', 'delivery_date', 'commodities_delivered', 'total_commodity_value']
    if not contract_fields:
        contract_fields = ['contract_number', 'application__business_name', 'status', 'created_at']
    if not supplier_fields:
        supplier_fields = ['username', 'email', 'first_name', 'last_name', 'date_joined']
    
    # Prepare context for template
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'export_format': export_format,
        'selected_types': selected_types,
        'application_fields': application_fields,
        'delivery_fields': delivery_fields,
        'contract_fields': contract_fields,
        'supplier_fields': supplier_fields,
    }
    
    # If this is a POST request, generate the export
    if request.method == 'POST':
        return generate_export_file(
            request, start_date, end_date, export_format,
            selected_types, application_fields, delivery_fields,
            contract_fields, supplier_fields
        )
    
    return render(request, 'backoffice/export_reports.html', context)


def generate_export_file(request, start_date, end_date, export_format, 
                        selected_types, application_fields, delivery_fields,
                        contract_fields, supplier_fields):
    """
    Generate and return the export file.
    """
    try:
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reports_export_{start_date}_to_{end_date}.csv"'
            
            writer = csv.writer(response)
            
            # Write headers
            headers = []
            if 'applications' in selected_types:
                headers.extend([f"Application_{field}" for field in application_fields])
            if 'deliveries' in selected_types:
                # Add standard delivery fields
                for field in delivery_fields:
                    if field != 'commodities_delivered':
                        headers.append(f"Delivery_{field}")
                    else:
                        # For commodities_delivered, we'll add dynamic headers later
                        pass
            if 'contracts' in selected_types:
                headers.extend([f"Contract_{field}" for field in contract_fields])
            if 'suppliers' in selected_types:
                headers.extend([f"Supplier_{field}" for field in supplier_fields])
            
            # Add commodity headers if deliveries are selected
            if 'deliveries' in selected_types and 'commodities_delivered' in delivery_fields:
                # Add commodity-specific headers for expanded format
                headers.extend([
                    'Commodity',
                    'Quantity', 
                    'Unit_of_Measure',
                    'Unit_Price',
                    'Total_Weight',
                    'Total_Value'
                ])
            
            writer.writerow(headers)
            
            # Get all data based on selected types with proper relationships
            all_data = []
            
            # Create a comprehensive dataset that shows relationships
            if len(selected_types) > 1:
                # When multiple types are selected, create comprehensive rows
                # Start with deliveries as they link to suppliers, contracts, and schools
                if 'deliveries' in selected_types:
                    deliveries = DeliveryTracking.objects.filter(
                        created_at__date__range=[start_date, end_date]
                    ).select_related(
                        'supplier_user', 'delivery_school', 'delivery_region', 
                        'contract', 'contract__application', 'verified_by'
                    ).prefetch_related('commodities__commodity')
                    
                    for delivery in deliveries:
                        # Get all commodities for this delivery
                        commodities = delivery.commodities.all()
                        
                        if commodities.exists():
                            # Create a separate row for each commodity
                            for commodity in commodities:
                                row_data = {}
                                
                                # Delivery data (excluding commodities_delivered)
                                for field in delivery_fields:
                                    if field == 'commodities_delivered':
                                        # Skip this field as we're creating separate rows
                                        continue
                                    elif field == 'total_commodity_value':
                                        # Calculate total value of all commodities
                                        total_value = sum(c.total_amount for c in delivery.commodities.all() if c.total_amount)
                                        row_data[f"Delivery_{field}"] = f"{total_value:.2f}" if total_value else '0.00'
                                    elif '__' in field:
                                        # Handle related fields
                                        parts = field.split('__')
                                        obj = delivery
                                        for part in parts:
                                            try:
                                                obj = getattr(obj, part)
                                            except:
                                                obj = ''
                                                break
                                        row_data[f"Delivery_{field}"] = str(obj) if obj else ''
                                    elif field == 'delivery_date':
                                        row_data[f"Delivery_{field}"] = delivery.delivery_date.strftime('%Y-%m-%d') if delivery.delivery_date else ''
                                    elif field == 'verified_at':
                                        row_data[f"Delivery_{field}"] = delivery.verified_at.strftime('%Y-%m-%d %H:%M:%S') if delivery.verified_at else ''
                                    else:
                                        row_data[f"Delivery_{field}"] = str(getattr(delivery, field, ''))
                                
                                # Add commodity-specific data
                                row_data['Commodity'] = commodity.commodity.name
                                row_data['Quantity'] = commodity.quantity
                                row_data['Unit_of_Measure'] = commodity.unit_of_measure
                                row_data['Unit_Price'] = f"GHS {commodity.unit_price:.2f}" if commodity.unit_price else "GHS 0.00"
                                
                                # Calculate total weight
                                unit_match = commodity.unit_of_measure.split()[0] if commodity.unit_of_measure.split()[0].replace('.', '').isdigit() else "1"
                                total_weight = float(commodity.quantity) * float(unit_match)
                                row_data['Total_Weight'] = total_weight
                                
                                row_data['Total_Value'] = f"GHS {commodity.total_amount:.2f}" if commodity.total_amount else "GHS 0.00"
                                
                                # Contract data (if delivery has a contract)
                                if 'contracts' in selected_types and delivery.contract:
                                    for field in contract_fields:
                                        if '__' in field:
                                            parts = field.split('__')
                                            obj = delivery.contract
                                            for part in parts:
                                                try:
                                                    obj = getattr(obj, part)
                                                except:
                                                    obj = ''
                                                    break
                                            row_data[f"Contract_{field}"] = str(obj) if obj else ''
                                        elif field == 'created_at':
                                            row_data[f"Contract_{field}"] = delivery.contract.created_at.strftime('%Y-%m-%d %H:%M:%S')
                                        else:
                                            row_data[f"Contract_{field}"] = str(getattr(delivery.contract, field, ''))
                                
                                # Application data (if delivery has contract with application)
                                if 'applications' in selected_types and delivery.contract and delivery.contract.application:
                                    for field in application_fields:
                                        if field == 'created_at':
                                            row_data[f"Application_{field}"] = delivery.contract.application.created_at.strftime('%Y-%m-%d %H:%M:%S')
                                        else:
                                            row_data[f"Application_{field}"] = str(getattr(delivery.contract.application, field, ''))
                                
                                # Supplier data (from delivery supplier)
                                if 'suppliers' in selected_types and delivery.supplier_user:
                                    for field in supplier_fields:
                                        if field == 'date_joined':
                                            row_data[f"Supplier_{field}"] = delivery.supplier_user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
                                        elif field == 'last_login':
                                            row_data[f"Supplier_{field}"] = delivery.supplier_user.last_login.strftime('%Y-%m-%d %H:%M:%S') if delivery.supplier_user.last_login else ''
                                        else:
                                            row_data[f"Supplier_{field}"] = str(getattr(delivery.supplier_user, field, ''))
                                
                                all_data.append(row_data)
                        else:
                            # No commodities - create a single row with empty commodity data
                            row_data = {}
                            
                            # Delivery data (excluding commodities_delivered)
                            for field in delivery_fields:
                                if field == 'commodities_delivered':
                                    continue
                                elif field == 'total_commodity_value':
                                    row_data[f"Delivery_{field}"] = '0.00'
                                elif '__' in field:
                                    parts = field.split('__')
                                    obj = delivery
                                    for part in parts:
                                        try:
                                            obj = getattr(obj, part)
                                        except:
                                            obj = ''
                                            break
                                    row_data[f"Delivery_{field}"] = str(obj) if obj else ''
                                elif field == 'delivery_date':
                                    row_data[f"Delivery_{field}"] = delivery.delivery_date.strftime('%Y-%m-%d') if delivery.delivery_date else ''
                                elif field == 'verified_at':
                                    row_data[f"Delivery_{field}"] = delivery.verified_at.strftime('%Y-%m-%d %H:%M:%S') if delivery.verified_at else ''
                                else:
                                    row_data[f"Delivery_{field}"] = str(getattr(delivery, field, ''))
                            
                            # Add empty commodity data
                            row_data['Commodity'] = 'No commodities'
                            row_data['Quantity'] = 0
                            row_data['Unit_of_Measure'] = ''
                            row_data['Unit_Price'] = 'GHS 0.00'
                            row_data['Total_Weight'] = 0
                            row_data['Total_Value'] = 'GHS 0.00'
                            
                            # Add other data types if selected
                            if 'contracts' in selected_types and delivery.contract:
                                for field in contract_fields:
                                    if '__' in field:
                                        parts = field.split('__')
                                        obj = delivery.contract
                                        for part in parts:
                                            try:
                                                obj = getattr(obj, part)
                                            except:
                                                obj = ''
                                                break
                                        row_data[f"Contract_{field}"] = str(obj) if obj else ''
                                    elif field == 'created_at':
                                        row_data[f"Contract_{field}"] = delivery.contract.created_at.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        row_data[f"Contract_{field}"] = str(getattr(delivery.contract, field, ''))
                            
                            if 'applications' in selected_types and delivery.contract and delivery.contract.application:
                                for field in application_fields:
                                    if field == 'created_at':
                                        row_data[f"Application_{field}"] = delivery.contract.application.created_at.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        row_data[f"Application_{field}"] = str(getattr(delivery.contract.application, field, ''))
                            
                            if 'suppliers' in selected_types and delivery.supplier_user:
                                for field in supplier_fields:
                                    if field == 'date_joined':
                                        row_data[f"Supplier_{field}"] = delivery.supplier_user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
                                    elif field == 'last_login':
                                        row_data[f"Supplier_{field}"] = delivery.supplier_user.last_login.strftime('%Y-%m-%d %H:%M:%S') if delivery.supplier_user.last_login else ''
                                    else:
                                        row_data[f"Supplier_{field}"] = str(getattr(delivery.supplier_user, field, ''))
                            
                            all_data.append(row_data)
                
                # Add standalone contracts (without deliveries)
                if 'contracts' in selected_types:
                    standalone_contracts = SupplierContract.objects.filter(
                        created_at__date__range=[start_date, end_date],
                        deliveries__isnull=True
                    ).select_related('application')
                    
                    for contract in standalone_contracts:
                        row_data = {}
                        
                        # Contract data
                        for field in contract_fields:
                            if '__' in field:
                                parts = field.split('__')
                                obj = contract
                                for part in parts:
                                    try:
                                        obj = getattr(obj, part)
                                    except:
                                        obj = ''
                                        break
                                row_data[f"Contract_{field}"] = str(obj) if obj else ''
                            elif field == 'created_at':
                                row_data[f"Contract_{field}"] = contract.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                row_data[f"Contract_{field}"] = str(getattr(contract, field, ''))
                        
                        # Application data
                        if 'applications' in selected_types and contract.application:
                            for field in application_fields:
                                if field == 'created_at':
                                    row_data[f"Application_{field}"] = contract.application.created_at.strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    row_data[f"Application_{field}"] = str(getattr(contract.application, field, ''))
                        
                        all_data.append(row_data)
                
                # Add standalone applications (without contracts)
                if 'applications' in selected_types:
                    standalone_applications = SupplierApplication.objects.filter(
                        created_at__date__range=[start_date, end_date],
                        contracts__isnull=True
                    ).select_related('user')
                    
                    for app in standalone_applications:
                        row_data = {}
                        
                        # Application data
                        for field in application_fields:
                            if field == 'created_at':
                                row_data[f"Application_{field}"] = app.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                row_data[f"Application_{field}"] = str(getattr(app, field, ''))
                        
                        # Supplier data
                        if 'suppliers' in selected_types and app.user:
                            for field in supplier_fields:
                                if field == 'date_joined':
                                    row_data[f"Supplier_{field}"] = app.user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
                                elif field == 'last_login':
                                    row_data[f"Supplier_{field}"] = app.user.last_login.strftime('%Y-%m-%d %H:%M:%S') if app.user.last_login else ''
                                else:
                                    row_data[f"Supplier_{field}"] = str(getattr(app.user, field, ''))
                        
                        all_data.append(row_data)
                        
            else:
                # Single data type selected - export each type separately
                if 'applications' in selected_types:
                    applications = SupplierApplication.objects.filter(
                        created_at__date__range=[start_date, end_date]
                    ).select_related('user')
                    
                    for app in applications:
                        row_data = {}
                        for field in application_fields:
                            if field == 'created_at':
                                row_data[f"Application_{field}"] = app.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                row_data[f"Application_{field}"] = str(getattr(app, field, ''))
                        all_data.append(row_data)
                
                if 'deliveries' in selected_types:
                    deliveries = DeliveryTracking.objects.filter(
                        created_at__date__range=[start_date, end_date]
                    ).select_related('supplier_user', 'delivery_school', 'delivery_region', 'contract').prefetch_related('commodities__commodity')
                    
                    for delivery in deliveries:
                        row_data = {}
                        for field in delivery_fields:
                            if field == 'commodities_delivered':
                                # Get all commodities for this delivery
                                commodities = delivery.commodities.all()
                                commodity_list = []
                                for commodity in commodities:
                                    commodity_info = f"{commodity.commodity.name} ({commodity.quantity} {commodity.unit_of_measure})"
                                    if commodity.unit_price:
                                        commodity_info += f" @ {commodity.unit_price}"
                                    commodity_list.append(commodity_info)
                                row_data[f"Delivery_{field}"] = "; ".join(commodity_list) if commodity_list else 'No commodities'
                            elif field == 'total_commodity_value':
                                # Calculate total value of all commodities
                                total_value = sum(commodity.total_amount for commodity in delivery.commodities.all() if commodity.total_amount)
                                row_data[f"Delivery_{field}"] = f"{total_value:.2f}" if total_value else '0.00'
                            elif '__' in field:
                                parts = field.split('__')
                                obj = delivery
                                for part in parts:
                                    try:
                                        obj = getattr(obj, part)
                                    except:
                                        obj = ''
                                        break
                                row_data[f"Delivery_{field}"] = str(obj) if obj else ''
                            elif field == 'delivery_date':
                                row_data[f"Delivery_{field}"] = delivery.delivery_date.strftime('%Y-%m-%d') if delivery.delivery_date else ''
                            elif field == 'verified_at':
                                row_data[f"Delivery_{field}"] = delivery.verified_at.strftime('%Y-%m-%d %H:%M:%S') if delivery.verified_at else ''
                            else:
                                row_data[f"Delivery_{field}"] = str(getattr(delivery, field, ''))
                        all_data.append(row_data)
                
                if 'contracts' in selected_types:
                    contracts = SupplierContract.objects.filter(
                        created_at__date__range=[start_date, end_date]
                    ).select_related('application')
                    
                    for contract in contracts:
                        row_data = {}
                        for field in contract_fields:
                            if '__' in field:
                                parts = field.split('__')
                                obj = contract
                                for part in parts:
                                    try:
                                        obj = getattr(obj, part)
                                    except:
                                        obj = ''
                                        break
                                row_data[f"Contract_{field}"] = str(obj) if obj else ''
                            elif field == 'created_at':
                                row_data[f"Contract_{field}"] = contract.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                row_data[f"Contract_{field}"] = str(getattr(contract, field, ''))
                        all_data.append(row_data)
                
                if 'suppliers' in selected_types:
                    suppliers = User.objects.filter(
                        role=User.Role.SUPPLIER,
                        date_joined__date__range=[start_date, end_date]
                    )
                    
                    for supplier in suppliers:
                        row_data = {}
                        for field in supplier_fields:
                            if field == 'date_joined':
                                row_data[f"Supplier_{field}"] = supplier.date_joined.strftime('%Y-%m-%d %H:%M:%S')
                            elif field == 'last_login':
                                row_data[f"Supplier_{field}"] = supplier.last_login.strftime('%Y-%m-%d %H:%M:%S') if supplier.last_login else ''
                            else:
                                row_data[f"Supplier_{field}"] = str(getattr(supplier, field, ''))
                        all_data.append(row_data)
            
            # Write data rows
            for row_data in all_data:
                row = []
                for header in headers:
                    row.append(row_data.get(header, ''))
                writer.writerow(row)
            
            return response
            
        else:
            return HttpResponse("Export format not supported", status=400)
            
    except Exception as e:
        logger.error(f"Error generating export: {str(e)}")
        return HttpResponse(f"Error generating export: {str(e)}", status=400)


@staff_member_required
def download_application_pack(request, pk):
    """
    Download a zip file containing all uploaded documents and the application PDF.
    """
    import zipfile
    import tempfile
    import os
    from django.conf import settings
    from .pdf_service import EnhancedApplicationPDFService
    
    application = get_object_or_404(SupplierApplication, pk=pk)
    
    try:
        # Create a temporary file for the zip
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Add the application PDF
            pdf_service = EnhancedApplicationPDFService()
            pdf_path = pdf_service.generate_application_pdf(application)
            
            if pdf_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, pdf_path)):
                full_pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
                zipf.write(
                    full_pdf_path,
                    f"{application.tracking_code}_Application_Form.pdf"
                )
                logger.info(f"Added application PDF to zip for {application.tracking_code}")
            
            # 2. Add all uploaded documents from the documents folder
            docs_base_path = os.path.join(settings.MEDIA_ROOT, 'documents', application.tracking_code)
            
            if os.path.exists(docs_base_path):
                # Document folder mapping
                document_folders = {
                    'BUSINESS_REGISTRATION_DOCS': 'Business_Registration_Certificate',
                    'VAT_CERTIFICATE': 'VAT_Certificate',
                    'PPA_CERTIFICATE': 'PPA_Certificate',
                    'TAX_CLEARANCE_CERT': 'Tax_Clearance_Certificate',
                    'PROOF_OF_OFFICE': 'Proof_of_Office',
                    'ID_MD_CEO_PARTNERS': 'ID_Cards_of_Directors',
                    'GCX_REGISTRATION_PROOF': 'GCX_Registration_Documents',
                    'TEAM_MEMBER_ID': 'Team_Member_ID_Documents',
                    'FDA_CERT_PROCESSED_FOOD': 'FDA_Certificate',
                }
                
                files_added = 0
                for folder_name, clean_name in document_folders.items():
                    folder_path = os.path.join(docs_base_path, folder_name)
                    
                    if os.path.exists(folder_path) and os.path.isdir(folder_path):
                        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
                        
                        for filename in files:
                            file_path = os.path.join(folder_path, filename)
                            # Add file to zip with organized folder structure
                            arcname = os.path.join('Documents', clean_name, filename)
                            zipf.write(file_path, arcname)
                            files_added += 1
                
                logger.info(f"Added {files_added} document files to zip for {application.tracking_code}")
            else:
                logger.warning(f"No documents folder found for {application.tracking_code}")
        
        # Read the zip file content
        temp_zip.close()
        with open(temp_zip.name, 'rb') as f:
            zip_content = f.read()
        
        # Clean up the temporary file
        os.unlink(temp_zip.name)
        
        # Create the response
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{application.tracking_code}_Complete_Pack.zip"'
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='DOWNLOAD_PACK',
            model_name='SupplierApplication',
            object_id=str(application.id),
            details=f'Downloaded complete application pack for {application.tracking_code}'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating application pack for {application.tracking_code}: {str(e)}")
        messages.error(request, f"Error creating download pack: {str(e)}")
        return redirect('applications:backoffice-application-detail', pk=pk)


@staff_member_required
def download_signed_documents_zip(request, pk):
    """Download all signed documents for a supplier as a ZIP file."""
    try:
        application = get_object_or_404(SupplierApplication, pk=pk)
        
        # Get all signed documents for this supplier
        contract_signings = ContractSigning.objects.filter(
            supplier=application.user,
            status='SIGNED',
            signature_file__isnull=False
        ).select_related('contract')
        
        if not contract_signings.exists():
            messages.warning(request, 'No signed documents found for this supplier.')
            return redirect('applications:backoffice-supplier-detail', pk=pk)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for signing in contract_signings:
                if signing.signature_file:
                    # Get the file path
                    file_path = signing.signature_file.path
                    if os.path.exists(file_path):
                        # Create a clean filename
                        contract_number = signing.contract.contract_number
                        file_extension = os.path.splitext(signing.signature_file.name)[1]
                        clean_filename = f"{contract_number}_signed{file_extension}"
                        
                        # Add file to ZIP
                        zip_file.write(file_path, clean_filename)
        
        # Prepare response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{application.business_name}_signed_documents.zip"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating signed documents ZIP for supplier {pk}: {str(e)}")
        messages.error(request, f"Error creating ZIP file: {str(e)}")
        return redirect('applications:backoffice-supplier-detail', pk=pk)
