"""
Password management views for the accounts app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect


@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def change_password(request):
    """
    View for changing user password.
    Required for users with must_change_password=True.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Clear the must_change_password flag
            user.must_change_password = False
            user.save()
            
            # Update the session auth hash to prevent logout
            update_session_auth_hash(request, user)
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Your password was successfully updated!'
                })
            
            messages.success(request, 'Your password was successfully updated!')
            
            # Redirect based on user role
            if user.is_supplier:
                return redirect('accounts:dashboard')
            elif user.is_reviewer or user.is_admin:
                return redirect('applications:backoffice-dashboard')
            else:
                return redirect('/')
        else:
            # Handle AJAX validation errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, field_errors in form.errors.items():
                    errors[field] = field_errors
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'title': 'Change Password',
        'is_required': request.user.must_change_password,
    }
    
    return render(request, 'accounts/change_password.html', context)


@method_decorator(login_required, name='dispatch')
class RequiredPasswordChangeView(View):
    """
    View that enforces password change for users with must_change_password=True.
    """
    
    def get(self, request):
        if not request.user.must_change_password:
            # User doesn't need to change password, redirect to dashboard
            if request.user.is_supplier:
                return redirect('accounts:dashboard')
            elif request.user.is_reviewer or request.user.is_admin:
                return redirect('applications:backoffice-dashboard')
            else:
                return redirect('/')
        
        form = PasswordChangeForm(request.user)
        context = {
            'form': form,
            'title': 'Change Password Required',
            'is_required': True,
        }
        return render(request, 'accounts/change_password.html', context)
    
    def post(self, request):
        if not request.user.must_change_password:
            # User doesn't need to change password, redirect to dashboard
            if request.user.is_supplier:
                return redirect('accounts:dashboard')
            elif request.user.is_reviewer or request.user.is_admin:
                return redirect('applications:backoffice-dashboard')
            else:
                return redirect('/')
        
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Clear the must_change_password flag
            user.must_change_password = False
            user.save()
            
            # Update the session auth hash to prevent logout
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password was successfully updated!')
            
            # Redirect based on user role
            if user.is_supplier:
                return redirect('accounts:dashboard')
            elif user.is_reviewer or user.is_admin:
                return redirect('applications:backoffice-dashboard')
            else:
                return redirect('/')
        
        context = {
            'form': form,
            'title': 'Change Password Required',
            'is_required': True,
        }
        return render(request, 'accounts/change_password.html', context)
