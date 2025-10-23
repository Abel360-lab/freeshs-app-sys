"""
Simple health check views for Railway deployment
"""
from django.http import JsonResponse

def health_check(request):
    """
    Simple health check endpoint for Railway
    """
    return JsonResponse({'status': 'ok', 'message': 'Django app is running'})
