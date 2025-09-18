"""
Views for reviews app.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ReviewComment, ReviewChecklist, ReviewDecision
from .serializers import (
    ReviewCommentSerializer, ReviewChecklistSerializer, ReviewDecisionSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews (admin only).
    """
    queryset = ReviewComment.objects.all()
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['application', 'reviewer', 'is_internal']
    search_fields = ['comment', 'application__business_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter reviews based on user permissions."""
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(application__is_deleted=False)
        return qs