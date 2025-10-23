"""
Health check views for Railway deployment
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Simple health check endpoint for Railway
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache (if using Redis)
        try:
            cache.set('health_check', 'ok', 10)
            cache_status = cache.get('health_check') == 'ok'
        except Exception:
            cache_status = True  # Cache is optional
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected' if cache_status else 'optional',
            'timestamp': str(timezone.now())
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)

def simple_health(request):
    """
    Very simple health check for Railway
    """
    return JsonResponse({'status': 'ok'})
