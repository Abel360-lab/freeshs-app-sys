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
    
    # Supplier-specific views (authenticated)
    path('supplier/applications/', views.supplier_applications_list, name='supplier-applications-list'),
    path('supplier/applications/<int:pk>/', views.supplier_application_detail, name='supplier-application-detail'),
    path('supplier/documents/upload/', views.supplier_general_document_upload, name='supplier-general-document-upload'),
    path('supplier/applications/<int:pk>/upload/', views.supplier_document_upload, name='supplier-document-upload'),
    path('supplier/applications/<int:pk>/direct-upload/', views.supplier_direct_document_upload, name='supplier-direct-upload'),
    
    # Supplier contract and delivery management
    path('supplier/contracts/', views.supplier_contracts, name='supplier-contracts'),
    path('supplier/contracts/<int:pk>/', views.supplier_contract_detail, name='supplier-contract-detail'),
    path('supplier/contracts/<int:pk>/accept/', views.accept_contract, name='supplier-accept-contract'),
    path('supplier/contracts/<int:pk>/reject/', views.reject_contract, name='supplier-reject-contract'),
    path('supplier/contracts/<int:pk>/upload-signed/', views.upload_signed_document, name='supplier-upload-signed-document'),
    path('supplier/deliveries/', views.supplier_deliveries, name='supplier-deliveries'),
    path('supplier/deliveries/<int:pk>/', views.supplier_delivery_detail, name='supplier-delivery-detail'),
    path('supplier/deliveries/create/', views.create_delivery, name='supplier-create-delivery'),
    path('supplier/schools/by-region/', views.get_schools_by_region, name='schools-by-region'),
    
    # Document creation views
    path('supplier/srvs/', views.supplier_srvs, name='supplier-srvs'),
    path('supplier/srvs/create/', views.create_srv, name='supplier-create-srv'),
    path('supplier/waybills/', views.supplier_waybills, name='supplier-waybills'),
    path('supplier/waybills/create/', views.create_waybill, name='supplier-create-waybill'),
    path('supplier/invoices/', views.supplier_invoices, name='supplier-invoices'),
    path('supplier/contract-documents/', views.supplier_contract_documents, name='supplier-contract-documents'),
    path('supplier/contract-documents/<int:signing_id>/', views.contract_document_detail, name='contract-document-detail'),
    path('supplier/contract-documents/<int:signing_id>/review/', views.review_contract_documents, name='review-contract-documents'),
    path('supplier/contract-documents/<int:signing_id>/sign/', views.sign_contract_documents, name='sign-contract-documents'),
    path('supplier/contract-documents/<int:signing_id>/reject/', views.reject_contract_documents, name='reject-contract-documents'),
    path('supplier/invoices/create/', views.create_invoice, name='supplier-create-invoice'),
    
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
    path('backoffice/reports/', backoffice_views.reports_dashboard, name='backoffice-reports'),
    path('backoffice/reports/export/', backoffice_views.export_reports, name='backoffice-export-reports'),
    path('backoffice/applications/', backoffice_views.application_management, name='backoffice-applications'),
    path('backoffice/applications/<int:pk>/', backoffice_views.application_detail, name='backoffice-application-detail'),
    path('backoffice/suppliers/', backoffice_views.supplier_management, name='backoffice-suppliers'),
    path('backoffice/documents/', backoffice_views.document_verification, name='backoffice-documents'),
    path('backoffice/analytics/', backoffice_views.analytics, name='backoffice-analytics'),
    
    # Application actions
    path('backoffice/applications/<int:pk>/approve/', backoffice_views.approve_application, name='backoffice-approve-application'),
    path('backoffice/applications/<int:pk>/reject/', backoffice_views.reject_application, name='backoffice-reject-application'),
    path('backoffice/applications/<int:pk>/update-status/', backoffice_views.update_application_status, name='backoffice-update-status'),
    path('backoffice/applications/<int:pk>/request-documents/', backoffice_views.request_documents, name='backoffice-request-documents'),
    path('backoffice/applications/<int:pk>/send-notification/', backoffice_views.send_notification, name='backoffice-send-notification'),
    path('backoffice/applications/<int:pk>/add-notes/', backoffice_views.add_application_notes, name='backoffice-add-notes'),
    path('backoffice/applications/<int:pk>/verify-document/', backoffice_views.verify_document, name='backoffice-verify-document'),
    path('backoffice/applications/<int:pk>/pdf/', backoffice_views.application_pdf_download, name='backoffice-application-pdf'),
    path('backoffice/applications/<int:pk>/generate-pdf/', backoffice_views.application_pdf_generate, name='backoffice-generate-pdf'),
    path('backoffice/applications/<int:pk>/download-pack/', backoffice_views.download_application_pack, name='backoffice-download-pack'),
    path('backoffice/applications/<int:pk>/activate-account/', backoffice_views.activate_supplier_account, name='backoffice-activate-account'),
    path('backoffice/applications/<int:pk>/deactivate-account/', backoffice_views.deactivate_supplier_account, name='backoffice-deactivate-account'),
    path('backoffice/applications/bulk-approve/', backoffice_views.bulk_approve_applications, name='backoffice-bulk-approve'),
    path('backoffice/applications/bulk-reject/', backoffice_views.bulk_reject_applications, name='backoffice-bulk-reject'),
    
    # Document actions
    path('backoffice/documents/<int:pk>/verify/', backoffice_views.verify_document, name='backoffice-verify-document'),
    path('backoffice/documents/<int:pk>/reject/', backoffice_views.reject_document, name='backoffice-reject-document'),
    
    # Delivery management
    path('backoffice/deliveries/<int:pk>/', backoffice_views.delivery_detail, name='backoffice-delivery-detail'),
    path('backoffice/suppliers/<int:pk>/award-contract/', backoffice_views.award_contract_page, name='backoffice-award-contract-page'),
    path('backoffice/suppliers/<int:pk>/award-contract/submit/', backoffice_views.award_contract, name='backoffice-award-contract'),
    path('backoffice/users/<int:user_id>/activate/', backoffice_views.activate_supplier_account, name='backoffice-activate-account'),
    path('backoffice/users/<int:user_id>/deactivate/', backoffice_views.deactivate_supplier_account, name='backoffice-deactivate-account'),
    path('backoffice/upload-document/', backoffice_views.upload_contract_document, name='backoffice-upload-document'),
    
    # Contract deliveries
    path('backoffice/contracts/<int:contract_pk>/deliveries/', backoffice_views.contract_deliveries, name='backoffice-contract-deliveries'),
    
    # Delivery verification
    path('backoffice/deliveries/<int:pk>/verify/', backoffice_views.verify_delivery, name='backoffice-verify-delivery'),
    path('backoffice/deliveries/<int:pk>/reject/', backoffice_views.reject_delivery, name='backoffice-reject-delivery'),
    
    # Supplier management
    path('backoffice/suppliers/<int:pk>/', backoffice_views.supplier_detail, name='backoffice-supplier-detail'),
    path('backoffice/suppliers/<int:pk>/upload-contract/', backoffice_views.upload_contract, name='backoffice-upload-contract'),
    path('backoffice/suppliers/<int:pk>/download-signed-documents/', backoffice_views.download_signed_documents_zip, name='download-signed-documents-zip'),
    path('backoffice/contracts/<int:pk>/create-srv/', backoffice_views.create_srv, name='backoffice-create-srv'),
    path('backoffice/srvs/<int:pk>/create-invoice/', backoffice_views.create_invoice, name='backoffice-create-invoice'),
    
]
