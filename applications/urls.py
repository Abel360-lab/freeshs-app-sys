"""
URL configuration for applications app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, backoffice_views, document_submission_views

app_name = 'applications'

# API Router
router = DefaultRouter()
router.register(r'admin/applications', views.SupplierApplicationViewSet, basename='admin-applications')

urlpatterns = [
    # Public form views
    path('apply/', views.application_form_view, name='application-form'),
    path('apply/success/', views.application_success_view, name='application-success'),
    
    # Document submission views
    path('submit/<str:token>/', document_submission_views.document_submission_view, name='document-submission'),
    path('submit/<str:token>/success/', document_submission_views.document_submission_success, name='document-submission-success'),
    path('upload/<str:token>/', document_submission_views.DocumentUploadView.as_view(), name='document-upload'),
    
    # Public API endpoints
    path('applications/submit/', views.ApplicationSubmitView.as_view(), name='application-submit'),
    path('applications/<str:tracking_code>/status/', views.ApplicationStatusView.as_view(), name='application-status'),
    path('applications/<str:tracking_code>/outstanding/', views.OutstandingDocumentsView.as_view(), name='outstanding-documents'),
    path('applications/<str:tracking_code>/outstanding/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    
    # Admin API endpoints
    path('', include(router.urls)),
    
    # Admin actions
    path('admin/applications/<int:pk>/request-more-docs/', views.RequestMoreDocumentsView.as_view(), name='request-more-docs'),
    path('admin/applications/<int:pk>/approve/', views.ApproveApplicationView.as_view(), name='approve-application'),
    path('admin/applications/<int:pk>/reject/', views.RejectApplicationView.as_view(), name='reject-application'),
    path('admin/applications/<int:pk>/pdf/', views.ApplicationPDFDownloadView.as_view(), name='application-pdf'),
    path('admin/applications/<int:pk>/generate-pdf/', views.ApplicationPDFGenerateView.as_view(), name='generate-pdf'),
    
    # Backoffice views
    path('backoffice/', backoffice_views.backoffice_dashboard, name='backoffice-dashboard'),
    path('backoffice/applications/', backoffice_views.application_management, name='backoffice-applications'),
    path('backoffice/applications/<int:pk>/', backoffice_views.application_detail, name='backoffice-application-detail'),
    path('backoffice/suppliers/', backoffice_views.supplier_management, name='backoffice-suppliers'),
    path('backoffice/documents/', backoffice_views.document_verification, name='backoffice-documents'),
    path('backoffice/analytics/', backoffice_views.analytics, name='backoffice-analytics'),
    
    # Application actions
    path('backoffice/applications/<int:pk>/approve/', backoffice_views.approve_application, name='backoffice-approve-application'),
    path('backoffice/applications/<int:pk>/reject/', backoffice_views.reject_application, name='backoffice-reject-application'),
    path('backoffice/applications/<int:pk>/request-documents/', backoffice_views.request_documents, name='backoffice-request-documents'),
    path('backoffice/applications/<int:pk>/pdf/', backoffice_views.application_pdf_download, name='backoffice-application-pdf'),
    path('backoffice/applications/<int:pk>/generate-pdf/', backoffice_views.application_pdf_generate, name='backoffice-generate-pdf'),
    path('backoffice/applications/bulk-approve/', backoffice_views.bulk_approve_applications, name='backoffice-bulk-approve'),
    path('backoffice/applications/bulk-reject/', backoffice_views.bulk_reject_applications, name='backoffice-bulk-reject'),
    
    # Document actions
    path('backoffice/documents/<int:pk>/verify/', backoffice_views.verify_document, name='backoffice-verify-document'),
    path('backoffice/documents/<int:pk>/reject/', backoffice_views.reject_document, name='backoffice-reject-document'),
    
]
