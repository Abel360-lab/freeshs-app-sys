"""
URL configuration for GCX Supplier Application Portal.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
from . import health_views

# URL patterns
urlpatterns = [
    # Health check
    path('health/', health_views.health_check, name='health-check'),
    
    # Admin URLs
    path('admin/', admin.site.urls),
    path('admin/login/', RedirectView.as_view(url='/accounts/admin/login/', permanent=False)),
    
    # i18n URL patterns
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Main application URLs
    path('', include('applications.urls', namespace='applications')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('documents/', include('documents.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('core/', include('core.urls', namespace='core')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Serve media files in production (temporary solution)
    # In production, you should serve media files through your web server (nginx/apache)
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
