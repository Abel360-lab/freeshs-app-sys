"""
Views for documents app.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import DocumentRequirement, DocumentUpload, OutstandingDocumentRequest
from .serializers import (
    DocumentRequirementSerializer, DocumentUploadSerializer,
    DocumentUploadCreateSerializer, OutstandingDocumentRequestSerializer,
    DocumentVerificationSerializer
)


class DocumentUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document uploads (admin only).
    """
    queryset = DocumentUpload.objects.all()
    serializer_class = DocumentUploadSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['verified', 'requirement', 'application']
    search_fields = ['original_filename', 'application__business_name']
    ordering_fields = ['uploaded_at', 'verified_at']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Filter uploads based on user permissions."""
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(application__is_deleted=False)
        return qs


class VerifyDocumentView(APIView):
    """
    Admin view for verifying documents.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Verify or unverify a document."""
        upload = get_object_or_404(DocumentUpload, pk=pk)
        
        serializer = DocumentVerificationSerializer(
            upload, 
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Document verification updated successfully',
                'verified': upload.verified
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)