"""
Serializers for documents app.
"""

from rest_framework import serializers
from .models import DocumentRequirement, DocumentUpload, OutstandingDocumentRequest


class DocumentRequirementSerializer(serializers.ModelSerializer):
    """Serializer for DocumentRequirement model."""
    
    class Meta:
        model = DocumentRequirement
        fields = [
            'id', 'code', 'label', 'description', 'is_required',
            'condition_note', 'allowed_extensions', 'max_file_size_mb'
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for DocumentUpload model."""
    
    requirement = DocumentRequirementSerializer(read_only=True)
    requirement_id = serializers.IntegerField(write_only=True)
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    is_image = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentUpload
        fields = [
            'id', 'requirement', 'requirement_id', 'file', 'original_filename',
            'file_size', 'file_size_mb', 'mime_type', 'file_url', 'is_image',
            'verified', 'verified_by', 'verified_at', 'verifier_note', 'uploaded_at'
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_size', 'mime_type', 'verified',
            'verified_by', 'verified_at', 'verifier_note', 'uploaded_at'
        ]
    
    def get_file_url(self, obj):
        """Get file URL."""
        if obj.file:
            return obj.file.url
        return None
    
    def get_file_size_mb(self, obj):
        """Get file size in MB."""
        return obj.file_size_mb
    
    def get_is_image(self, obj):
        """Check if file is an image."""
        return obj.is_image


class DocumentUploadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating document uploads."""
    
    class Meta:
        model = DocumentUpload
        fields = ['requirement_id', 'file']
    
    def validate(self, data):
        """Validate upload data."""
        requirement = data.get('requirement_id')
        file = data.get('file')
        
        if requirement and file:
            try:
                req = DocumentRequirement.objects.get(id=requirement)
                
                # Check file size
                if file.size > req.max_file_size_mb * 1024 * 1024:
                    raise serializers.ValidationError(
                        f"File size exceeds maximum allowed size of {req.max_file_size_mb}MB"
                    )
                
                # Check file extension
                file_ext = file.name.split('.')[-1].lower()
                if file_ext not in req.get_allowed_extensions():
                    raise serializers.ValidationError(
                        f"File type .{file_ext} is not allowed. Allowed types: {', '.join(req.get_allowed_extensions())}"
                    )
                
            except DocumentRequirement.DoesNotExist:
                raise serializers.ValidationError("Invalid requirement ID")
        
        return data


class OutstandingDocumentRequestSerializer(serializers.ModelSerializer):
    """Serializer for OutstandingDocumentRequest model."""
    
    requirements = DocumentRequirementSerializer(many=True, read_only=True)
    requirement_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = OutstandingDocumentRequest
        fields = [
            'id', 'application', 'requirements', 'requirement_ids', 'message',
            'requested_by', 'is_resolved', 'resolved_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'application', 'requested_by', 'is_resolved', 'resolved_at', 'created_at'
        ]
    
    def create(self, validated_data):
        """Create outstanding document request."""
        requirement_ids = validated_data.pop('requirement_ids', [])
        request = OutstandingDocumentRequest.objects.create(**validated_data)
        
        if requirement_ids:
            requirements = DocumentRequirement.objects.filter(id__in=requirement_ids)
            request.requirements.set(requirements)
        
        return request


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """Serializer for document verification."""
    
    class Meta:
        model = DocumentUpload
        fields = ['verified', 'verifier_note']
    
    def update(self, instance, validated_data):
        """Update verification status."""
        instance.verified = validated_data.get('verified', instance.verified)
        instance.verifier_note = validated_data.get('verifier_note', instance.verifier_note)
        
        if instance.verified and not instance.verified_by:
            instance.verified_by = self.context['request'].user
            instance.verified_at = timezone.now()
        
        instance.save()
        return instance
