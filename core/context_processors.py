"""
Context processors for making data available globally in templates.
"""

from django.db.models import Q


def sidebar_counts(request):
    """
    Provide real-time counts for sidebar badges.
    
    Usage in templates:
        {{ pending_applications_count }}
        {{ pending_documents_count }}
        {{ unread_notifications_count }}
    """
    counts = {
        'pending_applications_count': 0,
        'pending_documents_count': 0,
        'unread_notifications_count': 0,
    }
    
    # Only calculate counts for authenticated users
    if not request.user.is_authenticated:
        return counts
    
    try:
        # Import models here to avoid circular imports
        from applications.models import Application
        
        # Count pending applications (PENDING_REVIEW status)
        counts['pending_applications_count'] = Application.objects.filter(
            Q(status='PENDING_REVIEW') | Q(status='SUBMITTED')
        ).count()
        
        # Count pending documents (documents that need verification)
        # This could be documents with status != 'APPROVED'
        from applications.models import Document
        counts['pending_documents_count'] = Document.objects.filter(
            status='PENDING'
        ).count()
        
    except Exception as e:
        # If Application model doesn't exist yet or database error, return zeros
        pass
    
    try:
        # Count unread notifications
        from notifications.models import Notification
        counts['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
    except Exception as e:
        # If Notification model doesn't exist yet or database error, return zero
        pass
    
    return counts

