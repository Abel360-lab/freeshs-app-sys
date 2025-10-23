from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from functools import wraps

# Create your views here.

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
        from applications.models import SupplierApplication
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

@login_required
@supplier_account_activated_required
def sop_starter_pack(request):
    """SOP Starter Pack page for suppliers."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('applications:backoffice-dashboard')
    
    return render(request, 'accounts/sop_starter_pack.html')

@login_required
def supplier_dashboard(request):
    """Supplier dashboard for suppliers (both active and inactive)."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('applications:backoffice-dashboard')
    
    # Note: Password change requirement will be handled via popup in template
    
    # Get user's applications
    from applications.models import SupplierApplication
    from documents.models import DocumentRequirement, OutstandingDocumentRequest
    
    applications = SupplierApplication.objects.filter(user=request.user).order_by('-created_at')
    applications_count = applications.count()
    
    # Calculate document completion
    completed_docs_count = 0
    pending_docs_count = 0
    pending_documents = []
    
    for application in applications:
        # Get outstanding document requests for this application (unresolved ones)
        outstanding_requests = OutstandingDocumentRequest.objects.filter(application=application, is_resolved=False)
        
        for outstanding_request in outstanding_requests:
            # Get the requirements for this request
            for requirement in outstanding_request.requirements.all():
                pending_documents.append({
                    'label': requirement.label,
                    'description': requirement.description,
                    'application_id': application.id
                })
                pending_docs_count += 1
        
        # Count completed documents
        from documents.models import DocumentUpload
        completed_docs = DocumentUpload.objects.filter(application=application).count()
        completed_docs_count += completed_docs
    
    # Calculate profile completion percentage
    total_required_docs = DocumentRequirement.objects.filter(is_active=True).count()
    if total_required_docs > 0:
        profile_completion = min(100, int((completed_docs_count / (completed_docs_count + pending_docs_count)) * 100)) if (completed_docs_count + pending_docs_count) > 0 else 0
    else:
        profile_completion = 100
    
    # Get delivery and contract information
    from applications.models import DeliveryTracking, SupplierContract, ContractSigning
    
    # Delivery statistics
    deliveries = DeliveryTracking.objects.filter(supplier_user=request.user)
    total_deliveries = deliveries.count()
    pending_deliveries = deliveries.filter(status='PENDING').count()
    verified_deliveries = deliveries.filter(status='VERIFIED').count()
    rejected_deliveries = deliveries.filter(status='REJECTED').count()
    
    # Recent deliveries (last 5)
    recent_deliveries = deliveries.select_related(
        'delivery_region', 'delivery_school', 'contract'
    ).order_by('-created_at')[:5]
    
    # Contract statistics
    contracts = SupplierContract.objects.filter(application__user=request.user)
    total_contracts = contracts.count()
    active_contracts = contracts.filter(status='ACTIVE').count()
    
    # Signed contracts
    signed_contracts = []
    for contract in contracts:
        if ContractSigning.objects.filter(contract=contract, supplier=request.user, status='SIGNED').exists():
            signed_contracts.append(contract)
    
    signed_contracts_count = len(signed_contracts)
    
    # Recent contracts (last 5)
    recent_contracts = contracts.select_related('application').order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'title': 'Supplier Dashboard',
        'applications': applications,
        'applications_count': applications_count,
        'pending_docs_count': pending_docs_count,
        'completed_docs_count': completed_docs_count,
        'profile_completion': profile_completion,
        'pending_documents': pending_documents,
        
        # Delivery information
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'verified_deliveries': verified_deliveries,
        'rejected_deliveries': rejected_deliveries,
        'recent_deliveries': recent_deliveries,
        
        # Contract information
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'signed_contracts_count': signed_contracts_count,
        'recent_contracts': recent_contracts,
    }
    
    return render(request, 'accounts/supplier_dashboard_new.html', context)


@require_POST
def custom_logout(request):
    """
    Custom logout view that logs out the user and redirects to login page.
    """
    # Get user info before logout
    user_email = request.user.email if request.user.is_authenticated else "Unknown"
    
    # Log out the user
    logout(request)
    
    # Add success message
    messages.success(request, f"You have been successfully logged out. Thank you for using GCX Supplier Portal!")
    
    # Redirect to login page
    return redirect('accounts:login')


class CustomLogoutView(View):
    """
    Class-based view for logout that handles both GET and POST requests.
    """
    
    def get(self, request):
        """Handle GET request by redirecting to POST."""
        return redirect('accounts:login')
    
    def post(self, request):
        """Handle POST request for logout."""
        return custom_logout(request)
