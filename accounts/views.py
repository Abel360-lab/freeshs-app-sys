from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.

@login_required
def supplier_dashboard(request):
    """Supplier dashboard for approved applicants."""
    if not request.user.is_supplier:
        messages.error(request, 'Access denied. This area is for suppliers only.')
        return redirect('applications:backoffice-dashboard')
    
    context = {
        'user': request.user,
        'title': 'Supplier Dashboard'
    }
    
    return render(request, 'accounts/supplier_dashboard.html', context)
