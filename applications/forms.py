"""
Forms for applications app.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import SupplierApplication, TeamMember, NextOfKin, BankAccount
from core.models import Region, Commodity
from documents.models import DocumentRequirement


class SupplierApplicationForm(forms.ModelForm):
    """Form for supplier application submission."""
    
    # Override fields to make them required
    business_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    physical_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'required': True})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    telephone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+233XXXXXXXXX',
            'required': True
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True})
    )
    warehouse_location = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'required': True})
    )
    signer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    signer_designation = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    declaration_agreed = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'required': True})
    )
    
    # Choice fields
    region = forms.ModelChoiceField(
        queryset=Region.objects.filter(is_active=True),
        empty_label="Select Region",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    commodities_to_supply = forms.ModelMultipleChoiceField(
        queryset=Commodity.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    
    class Meta:
        model = SupplierApplication
        fields = [
            'business_name', 'physical_address', 'city', 'country', 'region',
            'telephone', 'email', 'commodities_to_supply', 'warehouse_location',
            'declaration_agreed', 'signer_name', 'signer_designation'
        ]
    
    def clean_telephone(self):
        """Validate Ghana phone number format."""
        telephone = self.cleaned_data.get('telephone')
        if not telephone.startswith('+233') or len(telephone) != 13:
            raise ValidationError("Phone number must be in Ghana format: +233XXXXXXXXX")
        return telephone
    
    def clean_email(self):
        """Check for duplicate emails in non-finalized applications."""
        email = self.cleaned_data.get('email')
        existing_apps = SupplierApplication.objects.filter(
            email=email,
            status__in=[
                SupplierApplication.ApplicationStatus.DRAFT,
                SupplierApplication.ApplicationStatus.SUBMITTED,
                SupplierApplication.ApplicationStatus.UNDER_REVIEW
            ]
        )
        if existing_apps.exists():
            raise ValidationError("An application with this email is already in progress.")
        return email


class TeamMemberForm(forms.ModelForm):
    """Form for team member information."""
    
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'required': True})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    telephone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+233XXXXXXXXX'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.filter(is_active=True),
        empty_label="Select Region",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    id_card_type = forms.ChoiceField(
        choices=TeamMember.IDCardType.choices,
        required=False,
        empty_label="Select ID Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_card_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = TeamMember
        fields = [
            'full_name', 'address', 'city', 'country', 'region',
            'telephone', 'email', 'id_card_type', 'id_card_number'
        ]
    
    def clean(self):
        """Validate team member data."""
        cleaned_data = super().clean()
        telephone = cleaned_data.get('telephone')
        email = cleaned_data.get('email')
        
        if not telephone and not email:
            raise ValidationError("Either telephone or email must be provided.")
        
        if telephone and not telephone.startswith('+233'):
            raise ValidationError("Phone number must be in Ghana format: +233XXXXXXXXX")
        
        id_card_type = cleaned_data.get('id_card_type')
        id_card_number = cleaned_data.get('id_card_number')
        
        if id_card_type and not id_card_number:
            raise ValidationError("ID card number is required when ID card type is specified.")
        
        return cleaned_data


class NextOfKinForm(forms.ModelForm):
    """Form for next of kin information."""
    
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    relationship = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'required': True})
    )
    mobile = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+233XXXXXXXXX',
            'required': True
        })
    )
    id_card_type = forms.ChoiceField(
        choices=NextOfKin.IDCardType.choices,
        required=False,
        empty_label="Select ID Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_card_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = NextOfKin
        fields = [
            'full_name', 'relationship', 'address', 'mobile',
            'id_card_type', 'id_card_number'
        ]
    
    def clean_mobile(self):
        """Validate Ghana phone number format."""
        mobile = self.cleaned_data.get('mobile')
        if not mobile.startswith('+233') or len(mobile) != 13:
            raise ValidationError("Phone number must be in Ghana format: +233XXXXXXXXX")
        return mobile


class BankAccountForm(forms.ModelForm):
    """Form for bank account information."""
    
    bank_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    branch = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    account_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    account_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    account_index = forms.ChoiceField(
        choices=[(1, 'Option 1'), (2, 'Option 2')],
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'branch', 'account_name', 'account_number', 'account_index']


class DocumentUploadForm(forms.Form):
    """Form for document uploads."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all required document requirements
        requirements = DocumentRequirement.objects.filter(is_required=True, is_active=True)
        
        for requirement in requirements:
            self.fields[f'document_{requirement.code}'] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=True,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024
                })
            )
        
        # Add FDA certificate if needed (will be handled in view)
        fda_requirement = DocumentRequirement.objects.filter(
            code='FDA_CERT_PROCESSED_FOOD'
        ).first()
        if fda_requirement:
            self.fields[f'document_{fda_requirement.code}'] = forms.FileField(
                label=f"{fda_requirement.label} (if applicable)",
                help_text=f"{fda_requirement.description} - {fda_requirement.condition_note}",
                required=False,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(fda_requirement.get_allowed_extensions()),
                    'data-max-size': fda_requirement.max_file_size_mb * 1024 * 1024
                })
            )
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = DocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type .{file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except DocumentRequirement.DoesNotExist:
                    pass
        
        return cleaned_data
