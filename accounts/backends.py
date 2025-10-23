"""
Custom authentication backends for the accounts app.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class SupplierAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend that allows inactive supplier users to login.
    Inactive suppliers can access limited features (monitoring applications, uploading docs).
    This backend only handles supplier users, not admin/staff users.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return
        
        try:
            user = User._default_manager.get_by_natural_key(username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
            return None
        else:
            # Only handle supplier users, let other backends handle admin/staff
            if user.is_supplier and user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None
    
    def user_can_authenticate(self, user):
        """
        Allow supplier users to authenticate even if they are inactive.
        This backend only handles suppliers, not admin/staff users.
        """
        return user.is_supplier
