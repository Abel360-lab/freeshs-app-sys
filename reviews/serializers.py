"""
Serializers for reviews app.
"""

from rest_framework import serializers
from .models import ReviewComment, ReviewChecklist, ReviewDecision


class ReviewCommentSerializer(serializers.ModelSerializer):
    """Serializer for ReviewComment model."""
    
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = ReviewComment
        fields = [
            'id', 'application', 'reviewer', 'reviewer_name', 'comment',
            'is_internal', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']


class ReviewChecklistSerializer(serializers.ModelSerializer):
    """Serializer for ReviewChecklist model."""
    
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewChecklist
        fields = [
            'id', 'application', 'reviewer', 'reviewer_name',
            'business_registration', 'vat_certificate', 'ppa_certificate',
            'tax_clearance', 'proof_of_office', 'id_directors',
            'gcx_registration', 'team_member_id', 'fda_certificate',
            'bank_account', 'contact_info', 'business_details',
            'team_members', 'next_of_kin', 'declaration',
            'is_complete', 'completion_percentage', 'overall_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reviewer', 'is_complete', 'completion_percentage',
            'created_at', 'updated_at'
        ]
    
    def get_completion_percentage(self, obj):
        """Get completion percentage."""
        return obj.get_completion_percentage()


class ReviewDecisionSerializer(serializers.ModelSerializer):
    """Serializer for ReviewDecision model."""
    
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = ReviewDecision
        fields = [
            'id', 'application', 'reviewer', 'reviewer_name', 'decision',
            'reason', 'is_final', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']
    
    def validate(self, data):
        """Validate decision data."""
        decision = data.get('decision')
        reason = data.get('reason')
        
        if decision in [ReviewDecision.Decision.APPROVE, ReviewDecision.Decision.REJECT]:
            if not reason:
                raise serializers.ValidationError("Reason is required for approve/reject decisions.")
        
        return data
