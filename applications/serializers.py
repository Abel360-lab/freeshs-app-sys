"""
Serializers for applications app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import Region, Commodity
from .models import SupplierApplication, TeamMember, NextOfKin, BankAccount

User = get_user_model()


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model."""
    
    class Meta:
        model = Region
        fields = ['id', 'code', 'name']


class CommoditySerializer(serializers.ModelSerializer):
    """Serializer for Commodity model."""
    
    class Meta:
        model = Commodity
        fields = ['id', 'name', 'description', 'is_processed_food']


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember model."""
    
    region = RegionSerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'full_name', 'position', 'years_experience', 'address', 'city', 'country', 'region', 'region_id',
            'telephone', 'email', 'id_card_type', 'id_card_number'
        ]
    
    def validate(self, data):
        """Validate team member data."""
        if not data.get('telephone') and not data.get('email'):
            raise serializers.ValidationError("Either telephone or email must be provided.")
        
        if data.get('id_card_type') and not data.get('id_card_number'):
            raise serializers.ValidationError("ID card number is required when ID card type is specified.")
        
        return data


class NextOfKinSerializer(serializers.ModelSerializer):
    """Serializer for NextOfKin model."""
    
    class Meta:
        model = NextOfKin
        fields = [
            'id', 'full_name', 'relationship', 'address', 'mobile',
            'id_card_type', 'id_card_number'
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for BankAccount model."""
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'bank_name', 'branch', 'account_name', 'account_number', 'account_index'
        ]
    
    def validate(self, data):
        """Validate bank account data."""
        application = self.context.get('application')
        if application:
            # Check if account name matches business name
            business_name_clean = ''.join(c.lower() for c in application.business_name if c.isalnum())
            account_name_clean = ''.join(c.lower() for c in data['account_name'] if c.isalnum())
            
            if business_name_clean != account_name_clean:
                raise serializers.ValidationError(
                    f"Account name must match business name '{application.business_name}'"
                )
        
        return data


class SupplierApplicationSerializer(serializers.ModelSerializer):
    """Serializer for SupplierApplication model."""
    
    region = RegionSerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    commodities_to_supply = CommoditySerializer(many=True, read_only=True)
    team_members = TeamMemberSerializer(many=True, required=False)
    next_of_kin = NextOfKinSerializer(many=True, required=False)
    bank_accounts = BankAccountSerializer(many=True, required=False)
    
    class Meta:
        model = SupplierApplication
        fields = [
            'id', 'business_name', 'business_type', 'registration_number', 'tin_number',
            'physical_address', 'city', 'postal_code', 'country', 'region', 'region_id', 
            'telephone', 'email', 'commodities_to_supply', 'other_commodities',
            'warehouse_location', 'declaration_agreed', 'data_consent',
            'signer_name', 'signer_designation', 'tracking_code', 'status',
            'submitted_at', 'signed_at', 'reviewed_at', 'decided_at', 'reviewer_comment',
            'team_members', 'next_of_kin', 'bank_accounts', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tracking_code', 'status', 'reviewed_at',
            'decided_at', 'reviewer_comment', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate application data."""
        if data.get('status') == SupplierApplication.ApplicationStatus.PENDING_REVIEW:
            if not data.get('declaration_agreed'):
                raise serializers.ValidationError("Declaration must be agreed to before submission.")
        
        return data
    
    def create(self, validated_data):
        """Create application with nested objects."""
        # Extract nested data
        team_members_data = validated_data.pop('team_members', [])
        next_of_kin_data = validated_data.pop('next_of_kin', [])
        bank_accounts_data = validated_data.pop('bank_accounts', [])
        
        # Create application
        application = SupplierApplication.objects.create(**validated_data)
        
        # Create team members
        for member_data in team_members_data:
            member_data['application'] = application
            TeamMember.objects.create(**member_data)
        
        # Create next of kin
        for kin_data in next_of_kin_data:
            kin_data['application'] = application
            NextOfKin.objects.create(**kin_data)
        
        # Create bank accounts
        for account_data in bank_accounts_data:
            account_data['application'] = application
            BankAccount.objects.create(**account_data)
        
        return application


class ApplicationStatusSerializer(serializers.ModelSerializer):
    """Serializer for application status check."""
    
    region = RegionSerializer(read_only=True)
    commodities_to_supply = CommoditySerializer(many=True, read_only=True)
    
    class Meta:
        model = SupplierApplication
        fields = [
            'id', 'business_name', 'tracking_code', 'status', 'region',
            'commodities_to_supply', 'submitted_at', 'reviewed_at', 'decided_at',
            'reviewer_comment'
        ]


class OutstandingDocumentsSerializer(serializers.ModelSerializer):
    """Serializer for outstanding documents."""
    
    class Meta:
        model = SupplierApplication
        fields = ['id', 'business_name', 'tracking_code', 'status']


class ApplicationSubmitSerializer(serializers.ModelSerializer):
    """Serializer for application submission."""
    
    region_id = serializers.IntegerField(write_only=True)
    team_members = TeamMemberSerializer(many=True, required=False)
    next_of_kin = NextOfKinSerializer(many=True, required=False)
    bank_accounts = BankAccountSerializer(many=True, required=False)
    commodity_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    # Document fields
    business_registration_docs = serializers.FileField(required=False)
    vat_certificate = serializers.FileField(required=False)
    ppa_certificate = serializers.FileField(required=False)
    tax_clearance_cert = serializers.FileField(required=False)
    proof_of_office = serializers.FileField(required=False)
    id_md_ceo_partners = serializers.FileField(required=False)
    gcx_registration_proof = serializers.FileField(required=False)
    team_member_id = serializers.FileField(required=False)
    fda_cert_processed_food = serializers.FileField(required=False)
    
    class Meta:
        model = SupplierApplication
        fields = [
            'business_name', 'business_type', 'registration_number', 'tin_number',
            'physical_address', 'city', 'postal_code', 'country', 'region_id',
            'telephone', 'email', 'commodity_ids', 'other_commodities', 'warehouse_location',
            'declaration_agreed', 'data_consent', 'signer_name', 'signer_designation',
            'team_members', 'next_of_kin', 'bank_accounts',
            'business_registration_docs', 'vat_certificate', 'ppa_certificate',
            'tax_clearance_cert', 'proof_of_office', 'id_md_ceo_partners',
            'gcx_registration_proof', 'team_member_id', 'fda_cert_processed_food',
            'signed_at', 'submitted_at'
        ]
    
    def validate(self, data):
        """Validate submission data."""
        if not data.get('declaration_agreed'):
            raise serializers.ValidationError("Declaration must be agreed to before submission.")
        
        # Validate commodities - must have either predefined commodities or other commodities
        commodity_ids = data.get('commodity_ids', [])
        other_commodities = data.get('other_commodities', '').strip()
        
        # Ensure commodity_ids is a list
        if commodity_ids is None:
            commodity_ids = []
        
        if not commodity_ids and not other_commodities:
            raise serializers.ValidationError("You must select at least one commodity from the predefined list OR check 'Other' and specify other commodities.")
        
        # Check if FDA certificate is required based on commodities
        fda_required = False
        if commodity_ids:
            from core.models import Commodity
            selected_commodities = Commodity.objects.filter(id__in=commodity_ids)
            processed_food_commodities = selected_commodities.filter(is_processed_food=True)
            fda_required = processed_food_commodities.exists()
        
        # Also check other_commodities for processed foods
        if not fda_required and other_commodities:
            processed_food_names = ['tom brown', 'palm oil']
            fda_required = any(food in other_commodities.lower() for food in processed_food_names)
        
        # Validate FDA certificate if required
        if fda_required:
            fda_file = data.get('fda_cert_processed_food')
            if not fda_file or (hasattr(fda_file, 'size') and fda_file.size == 0):
                raise serializers.ValidationError("FDA certificate is required when supplying processed foods (Tom Brown, Palm Oil, etc.)")
        else:
            # If FDA certificate is not required, we can still accept it if provided
            # No validation needed for optional field
            pass
        
        return data
    
    def create(self, validated_data):
        """Create and submit application with documents."""
        from documents.models import DocumentRequirement, DocumentUpload
        
        # Extract document data
        document_data = {}
        document_fields = [
            'business_registration_docs', 'vat_certificate', 'ppa_certificate',
            'tax_clearance_cert', 'proof_of_office', 'id_md_ceo_partners',
            'gcx_registration_proof', 'team_member_id', 'fda_cert_processed_food'
        ]
        
        for field in document_fields:
            if field in validated_data:
                document_data[field] = validated_data.pop(field)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"DEBUG: Serializer processing document field {field}: {type(document_data[field])}")
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"DEBUG: Serializer field {field} not in validated_data")
        
        # Set status to submitted and timestamps
        from django.utils import timezone
        validated_data['status'] = SupplierApplication.ApplicationStatus.PENDING_REVIEW
        validated_data['signed_at'] = timezone.now()
        validated_data['submitted_at'] = timezone.now()
        
        # Extract commodity_ids before creating application
        commodity_ids = validated_data.pop('commodity_ids', [])
        
        # Create application using the main serializer
        serializer = SupplierApplicationSerializer(data=validated_data)
        if serializer.is_valid():
            application = serializer.save()
            
            # Add commodities directly
            if commodity_ids:
                from core.models import Commodity
                commodities = Commodity.objects.filter(id__in=commodity_ids)
                application.commodities_to_supply.set(commodities)
            
            # Create document uploads
            document_mapping = {
                'business_registration_docs': 'BUSINESS_REGISTRATION_DOCS',
                'vat_certificate': 'VAT_CERTIFICATE',
                'ppa_certificate': 'PPA_CERTIFICATE',
                'tax_clearance_cert': 'TAX_CLEARANCE_CERT',
                'proof_of_office': 'PROOF_OF_OFFICE',
                'id_md_ceo_partners': 'ID_MD_CEO_PARTNERS',
                'gcx_registration_proof': 'GCX_REGISTRATION_PROOF',
                'team_member_id': 'TEAM_MEMBER_ID',
                'fda_cert_processed_food': 'FDA_CERT_PROCESSED_FOOD'
            }
            
            for field_name, file in document_data.items():
                if file:
                    try:
                        requirement = DocumentRequirement.objects.get(
                            code=document_mapping[field_name]
                        )
                        # Get content type safely
                        content_type = getattr(file, 'content_type', 'application/octet-stream')
                        if hasattr(file, 'content_type'):
                            content_type = file.content_type
                        elif hasattr(file, 'file') and hasattr(file.file, 'content_type'):
                            content_type = file.file.content_type
                        
                        DocumentUpload.objects.create(
                            application=application,
                            requirement=requirement,
                            file=file,
                            original_filename=file.name,
                            file_size=file.size,
                            mime_type=content_type
                        )
                    except DocumentRequirement.DoesNotExist:
                        pass  # Skip if requirement doesn't exist
            
            return application
        else:
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"SupplierApplicationSerializer validation failed: {serializer.errors}")
            logger.error(f"Validated data keys: {list(validated_data.keys())}")
            logger.error(f"Validated data region_id: {validated_data.get('region_id')}")
            logger.error(f"Validated data team_members: {validated_data.get('team_members')}")
            raise serializers.ValidationError(serializer.errors)
