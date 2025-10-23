from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.urls import resolve
from django.conf import settings
import logging

from .models import AuditLog, SystemSettings

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log system activities.
    """
    
    def process_request(self, request):
        """Process the request and log basic information."""
        # Skip logging for certain paths
        skip_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/admin/jsi18n/',
            '/admin/autocomplete/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return
        
        # Skip if audit logging is disabled
        try:
            settings_obj = SystemSettings.get_settings()
            if not settings_obj.audit_log_enabled:
                return
        except:
            pass
        
        # Store request info for later use
        request._audit_log_data = {
            'path': request.path,
            'method': request.method,
            'user': getattr(request, 'user', None),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_key': request.session.session_key if hasattr(request, 'session') else '',
        }
    
    def process_response(self, request, response):
        """Process the response and create audit log entry."""
        # Skip if no audit data was stored
        if not hasattr(request, '_audit_log_data'):
            return response
        
        try:
            # Skip logging for certain paths
            skip_paths = [
                '/static/',
                '/media/',
                '/favicon.ico',
                '/admin/jsi18n/',
                '/admin/autocomplete/',
            ]
            
            if any(request.path.startswith(path) for path in skip_paths):
                return response
            
            # Skip if audit logging is disabled
            try:
                settings_obj = SystemSettings.get_settings()
                if not settings_obj.audit_log_enabled:
                    return response
            except:
                pass
            
            # Determine action based on request method and path
            action = self._determine_action(request, response)
            
            # Skip if no action to log
            if not action:
                return response
            
            # Get user
            user = request._audit_log_data['user']
            if not user or not user.is_authenticated:
                user = None
            
            # Create audit log entry
            object_type = self._get_object_type(request) or 'System'
            object_id = self._get_object_id(request) or ''
            object_name = self._get_object_name(request) or ''
            
            AuditLog.log_action(
                action=action,
                description=self._get_description(request, response, action),
                user=user,
                object_type=object_type,
                object_id=object_id,
                object_name=object_name,
                request=request,
                severity=self._get_severity(request, response),
                metadata=self._get_metadata(request, response),
                tags=self._get_tags(request, response)
            )
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
        
        return response
    
    def _get_client_ip(self, request):
        """Get the client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _determine_action(self, request, response):
        """Determine the action based on request method and path."""
        method = request.method
        path = request.path
        
        # Login/Logout actions
        if 'login' in path.lower():
            return 'LOGIN' if method == 'POST' else None
        if 'logout' in path.lower():
            return 'LOGOUT'
        
        # CRUD actions based on method
        if method == 'POST':
            if 'create' in path.lower() or 'add' in path.lower():
                return 'CREATE'
            elif 'update' in path.lower() or 'edit' in path.lower():
                return 'UPDATE'
            elif 'delete' in path.lower() or 'remove' in path.lower():
                return 'DELETE'
            elif 'approve' in path.lower():
                return 'APPROVE'
            elif 'reject' in path.lower():
                return 'REJECT'
            elif 'send' in path.lower():
                if 'email' in path.lower():
                    return 'SEND_EMAIL'
                elif 'sms' in path.lower():
                    return 'SEND_SMS'
            elif 'export' in path.lower():
                return 'EXPORT'
            elif 'import' in path.lower():
                return 'IMPORT'
            elif 'upload' in path.lower():
                return 'UPLOAD'
            elif 'download' in path.lower():
                return 'DOWNLOAD'
            else:
                return 'UPDATE'  # Default for POST requests
        
        elif method == 'GET':
            if 'download' in path.lower():
                return 'DOWNLOAD'
            elif 'export' in path.lower():
                return 'EXPORT'
            else:
                return 'VIEW'  # Default for GET requests
        
        elif method == 'DELETE':
            return 'DELETE'
        
        elif method == 'PUT' or method == 'PATCH':
            return 'UPDATE'
        
        return None
    
    def _get_description(self, request, response, action):
        """Generate a description for the audit log entry."""
        method = request.method
        path = request.path
        
        # Get view name if possible
        try:
            resolved = resolve(path)
            view_name = resolved.view_name
        except:
            view_name = path
        
        # Generate description based on action
        descriptions = {
            'LOGIN': f"User logged in via {view_name}",
            'LOGOUT': f"User logged out via {view_name}",
            'CREATE': f"Created new record via {view_name}",
            'UPDATE': f"Updated record via {view_name}",
            'DELETE': f"Deleted record via {view_name}",
            'VIEW': f"Viewed {view_name}",
            'DOWNLOAD': f"Downloaded file via {view_name}",
            'UPLOAD': f"Uploaded file via {view_name}",
            'APPROVE': f"Approved record via {view_name}",
            'REJECT': f"Rejected record via {view_name}",
            'SEND_EMAIL': f"Sent email via {view_name}",
            'SEND_SMS': f"Sent SMS via {view_name}",
            'EXPORT': f"Exported data via {view_name}",
            'IMPORT': f"Imported data via {view_name}",
        }
        
        return descriptions.get(action, f"{action} action via {view_name}")
    
    def _get_object_type(self, request):
        """Determine the object type from the request path."""
        path = request.path
        
        # Extract object type from URL patterns
        if '/applications/' in path:
            return 'Application'
        elif '/suppliers/' in path:
            return 'Supplier'
        elif '/contracts/' in path:
            return 'Contract'
        elif '/deliveries/' in path:
            return 'Delivery'
        elif '/documents/' in path:
            return 'Document'
        elif '/users/' in path:
            return 'User'
        elif '/settings/' in path:
            return 'Settings'
        elif '/audit-logs/' in path:
            return 'AuditLog'
        
        return None
    
    def _get_object_id(self, request):
        """Extract object ID from request path."""
        path = request.path
        
        # Try to extract ID from URL
        parts = path.strip('/').split('/')
        for part in parts:
            if part.isdigit():
                return part
        
        return None
    
    def _get_object_name(self, request):
        """Generate object name for the audit log."""
        object_type = self._get_object_type(request)
        object_id = self._get_object_id(request)
        
        if object_type and object_id:
            return f"{object_type} #{object_id}"
        
        return None
    
    def _get_severity(self, request, response):
        """Determine severity based on response status and action."""
        status_code = response.status_code
        
        # Critical errors
        if status_code >= 500:
            return 'CRITICAL'
        
        # High severity for client errors
        if status_code >= 400:
            return 'HIGH'
        
        # Medium severity for redirects
        if status_code >= 300:
            return 'MEDIUM'
        
        # Low severity for successful requests
        return 'LOW'
    
    def _get_metadata(self, request, response):
        """Get additional metadata for the audit log."""
        metadata = {
            'status_code': response.status_code,
            'content_type': response.get('Content-Type', ''),
            'content_length': response.get('Content-Length', ''),
        }
        
        # Add request-specific metadata
        if hasattr(request, 'POST') and request.method == 'POST':
            # Add non-sensitive POST data
            sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
            post_data = {}
            for key, value in request.POST.items():
                if not any(field in key.lower() for field in sensitive_fields):
                    post_data[key] = str(value)[:100]  # Limit length
            if post_data:
                metadata['post_data'] = post_data
        
        return metadata
    
    def _get_tags(self, request, response):
        """Generate tags for the audit log entry."""
        tags = []
        
        # Add method tag
        tags.append(request.method.lower())
        
        # Add status tag
        if response.status_code < 400:
            tags.append('success')
        else:
            tags.append('error')
        
        # Add path-based tags
        path = request.path
        if '/admin/' in path:
            tags.append('admin')
        elif '/api/' in path:
            tags.append('api')
        elif '/backoffice/' in path:
            tags.append('backoffice')
        
        return tags
