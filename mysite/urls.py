"""
URL configuration for GCX Supplier Application Portal.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.urls', namespace='applications')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('documents/', include('documents.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('core/', include('core.urls', namespace='core')),
    # Redirect only the exact root path to backoffice
    path('', RedirectView.as_view(url='/backoffice/', permanent=False)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
