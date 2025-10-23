"""
Custom User model for GCX Supplier Application Portal.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model extending AbstractUser with role-based access control.
    
    Roles:
    - ADMIN: Full access to admin panel and all features
    - REVIEWER: Can review applications and manage documents
    - SUPPLIER: Approved applicants with limited access to their profile
    """
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        REVIEWER = 'REVIEWER', 'Reviewer'
        SUPPLIER = 'SUPPLIER', 'Supplier'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SUPPLIER,
        help_text="User role determining access permissions"
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text="Phone number in international format"
    )
    
    is_phone_verified = models.BooleanField(
        default=False,
        help_text="Whether the phone number has been verified"
    )
    
    must_change_password = models.BooleanField(
        default=False,
        help_text="Whether the user must change their password on next login"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_admin(self):
        """Check if user is an administrator."""
        return self.role == self.Role.ADMIN
    
    @property
    def is_reviewer(self):
        """Check if user is a reviewer."""
        return self.role in [self.Role.ADMIN, self.Role.REVIEWER]
    
    @property
    def is_supplier(self):
        """Check if user is a supplier."""
        return self.role == self.Role.SUPPLIER
    
    def get_display_name(self):
        """Get display name for the user."""
        if self.get_full_name():
            return self.get_full_name()
        return self.username