"""
Custom authentication views for the accounts app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomLoginView(LoginView):
    """
    Custom login view that handles password change redirects for suppliers.
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to appropriate page after successful login."""
        user = self.request.user
        
        # Redirect based on user role (password change will be handled via popup)
        if user.is_supplier:
            return reverse_lazy('accounts:dashboard')
        elif user.is_reviewer or user.is_admin:
            return reverse_lazy('applications:backoffice-dashboard')
        else:
            return reverse_lazy('accounts:dashboard')
    
    def form_valid(self, form):
        """Handle successful login."""
        # Call parent form_valid to perform login
        response = super().form_valid(form)
        
        # Add success message
        messages.success(self.request, f'Welcome back, {self.request.user.get_display_name()}!')
        
        return response
    
    def form_invalid(self, form):
        """Handle failed login."""
        messages.error(self.request, 'Invalid email or password. Please try again.')
        return super().form_invalid(form)


class SupplierLoginView(View):
    """
    Dedicated login view for suppliers only.
    Prevents suppliers from accessing admin/backoffice areas.
    """
    
    def get(self, request):
        """Display supplier login form."""
        if request.user.is_authenticated:
            if request.user.is_supplier:
                return redirect('accounts:dashboard')
            else:
                return redirect('applications:backoffice-dashboard')
        
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        """Handle supplier login."""
        email = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'accounts/login.html')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'accounts/login.html')
        
        # Check if user is a supplier
        if not user.is_supplier:
            messages.error(request, 'Access denied. This area is for suppliers only.')
            return render(request, 'accounts/login.html')
        
        # Login the user
        login(request, user)
        messages.success(request, f'Welcome back, {user.get_display_name()}!')
        
        # Redirect to supplier dashboard (password change will be handled via popup)
        return redirect('accounts:dashboard')


class AdminLoginView(LoginView):
    """
    Admin-only login view for admin/backoffice access.
    """
    template_name = 'accounts/admin_login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to backoffice dashboard after successful admin login."""
        return reverse_lazy('applications:backoffice-dashboard')
    
    def form_valid(self, form):
        """Handle successful admin login."""
        user = form.get_user()
        
        # Check if user has admin/backoffice access
        if not (user.is_superuser or user.is_staff or user.is_reviewer or user.is_admin):
            messages.error(self.request, 'Access denied. Admin privileges required.')
            return self.form_invalid(form)
        
        # Call parent form_valid to perform login
        response = super().form_valid(form)
        
        # Add success message
        messages.success(self.request, f'Welcome back, {user.get_display_name()}!')
        
        return response
    
    def form_invalid(self, form):
        """Handle failed admin login."""
        messages.error(self.request, 'Invalid credentials. Please try again.')
        return super().form_invalid(form)
