"""
URL configuration for documents app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'documents'

# API Router
router = DefaultRouter()
router.register(r'admin/documents', views.DocumentUploadViewSet, basename='admin-documents')

urlpatterns = [
    # Admin API endpoints
    path('', include(router.urls)),
    
    # Admin actions
    path('admin/documents/<int:pk>/verify/', views.VerifyDocumentView.as_view(), name='verify-document'),
]
