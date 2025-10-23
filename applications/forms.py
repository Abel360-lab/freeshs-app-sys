"""
Forms for applications app.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import SupplierApplication, TeamMember, NextOfKin, BankAccount, DeliveryTracking, StoreReceiptVoucher, Waybill, Invoice, School, ContractDocumentRequirement
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
        choices=[('', 'Select ID Type')] + list(TeamMember.IDCardType.choices),
        required=False,
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


class ContractDocumentUploadForm(forms.Form):
    """Dynamic form for contract document uploads based on requirements."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active contract document requirements
        requirements = ContractDocumentRequirement.objects.filter(is_active=True)
        
        for requirement in requirements:
            field_name = f'document_{requirement.code}'
            self.fields[field_name] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=requirement.is_required,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024,
                    'data-requirement-id': requirement.id
                })
            )
            
            # Add condition note if exists
            if requirement.condition_note:
                self.fields[field_name].help_text += f" ({requirement.condition_note})"
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = '.' + file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type {file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except ContractDocumentRequirement.DoesNotExist:
                    pass
        
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
        choices=[('', 'Select ID Type')] + list(NextOfKin.IDCardType.choices),
        required=False,
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


class ContractDocumentUploadForm(forms.Form):
    """Dynamic form for contract document uploads based on requirements."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active contract document requirements
        requirements = ContractDocumentRequirement.objects.filter(is_active=True)
        
        for requirement in requirements:
            field_name = f'document_{requirement.code}'
            self.fields[field_name] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=requirement.is_required,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024,
                    'data-requirement-id': requirement.id
                })
            )
            
            # Add condition note if exists
            if requirement.condition_note:
                self.fields[field_name].help_text += f" ({requirement.condition_note})"
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = '.' + file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type {file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except ContractDocumentRequirement.DoesNotExist:
                    pass
        
        return cleaned_data


class DeliveryCommodityForm(forms.Form):
    """Form for individual commodity in a delivery."""
    
    def __init__(self, commodities=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Commodity field
        commodity_queryset = commodities if commodities else Commodity.objects.filter(is_active=True)
        self.fields['commodity'] = forms.ModelChoiceField(
            queryset=commodity_queryset,
            empty_label="Select Commodity",
            widget=forms.Select(attrs={
                'class': 'form-select commodity-select',
                'required': True
            }),
            help_text="Select the commodity being delivered"
        )
        
        # Quantity field
        self.fields['quantity'] = forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            widget=forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'step': '0.01',
                'required': True,
                'min': '0.01'
            }),
            help_text="Quantity of commodity delivered"
        )
        
        # Unit of measure field (auto-filled from commodity settings)
        self.fields['unit_of_measure'] = forms.CharField(
            max_length=50,
            widget=forms.TextInput(attrs={
                'class': 'form-control unit-input',
                'required': True,
                'readonly': True,
                'style': 'background-color: #f8f9fa;'
            }),
            help_text="Unit of measure (auto-filled from commodity settings, e.g., '100kg bag', '1 crate', '50kg sack')"
        )
        
        # Unit price field (optional)
        self.fields['unit_price'] = forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            required=False,
            widget=forms.NumberInput(attrs={
                'class': 'form-control price-input',
                'step': '0.01',
                'min': '0'
            }),
            help_text="Unit price (optional)"
        )


class DeliveryForm(forms.Form):
    """Form for creating delivery tracking entries."""
    
    def __init__(self, user=None, commodities=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Import School model here to avoid circular imports
        from .models import School
        
        # Region field
        self.fields['region'] = forms.ModelChoiceField(
            queryset=Region.objects.filter(is_active=True),
            empty_label="Select Region",
            widget=forms.Select(attrs={
                'class': 'form-select',
                'id': 'delivery_region',
                'required': True
            }),
            help_text="Select the region for delivery"
        )
        
        # School field (will be populated via AJAX)
        self.fields['school'] = forms.ModelChoiceField(
            queryset=School.objects.none(),
            empty_label="Select School",
            widget=forms.Select(attrs={
                'class': 'form-select',
                'id': 'delivery_school',
                'required': True,
                'disabled': True
            }),
            help_text="Select the school for delivery"
        )
        
        # Keep the old single commodity field for backward compatibility
        commodity_queryset = commodities if commodities else Commodity.objects.filter(is_active=True)
        self.fields['commodity'] = forms.ModelChoiceField(
            queryset=commodity_queryset,
            empty_label="Select Commodity",
            widget=forms.Select(attrs={
                'class': 'form-select',
                'id': 'delivery_commodity',
                'required': False  # Make it optional since we now support multiple commodities
            }),
            help_text="Legacy single commodity field (deprecated - use commodities section below)"
        )
        
        # Other fields
        self.fields['serial_number'] = forms.CharField(
            max_length=100,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            help_text="Serial number for this delivery"
        )
        
        self.fields['delivery_date'] = forms.DateField(
            widget=forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            help_text="Date of delivery"
        )
        
        self.fields['srv_number'] = forms.CharField(
            max_length=100,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            help_text="Store Receipt Voucher number"
        )
        
        self.fields['waybill_number'] = forms.CharField(
            max_length=100,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            help_text="Waybill number"
        )
        
        self.fields['invoice_number'] = forms.CharField(
            max_length=100,
            required=False,
            widget=forms.TextInput(attrs={
                'class': 'form-control'
            }),
            help_text="Invoice number (optional)"
        )
        
        self.fields['quantity_delivered'] = forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'required': True
            }),
            help_text="Actual quantity delivered"
        )
        
        self.fields['unit_of_measure'] = forms.CharField(
            max_length=50,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            help_text="Unit of measure (e.g., kg, bags, pieces)"
        )
        
        # Optional notes field
        self.fields['notes'] = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional notes about this delivery...'
            }),
            help_text="Additional delivery notes (optional)"
        )
        
        # Document fields
        self.fields['srv_document'] = forms.FileField(
            required=False,
            widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            help_text="SRV document (optional)"
        )
        
        self.fields['waybill_document'] = forms.FileField(
            required=False,
            widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            help_text="Waybill document (optional)"
        )
        
        self.fields['invoice_document'] = forms.FileField(
            required=False,
            widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            help_text="Invoice document (optional)"
        )
    
    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        
        # Validate that either school or region is selected
        region = cleaned_data.get('region')
        school = cleaned_data.get('school')
        
        if not region:
            raise ValidationError("Please select a region.")
        
        if not school:
            raise ValidationError("Please select a school.")
        
        # Validate that school belongs to selected region
        if school and school.region != region:
            raise ValidationError("Selected school does not belong to the selected region.")
        
        return cleaned_data


class ContractDocumentUploadForm(forms.Form):
    """Dynamic form for contract document uploads based on requirements."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active contract document requirements
        requirements = ContractDocumentRequirement.objects.filter(is_active=True)
        
        for requirement in requirements:
            field_name = f'document_{requirement.code}'
            self.fields[field_name] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=requirement.is_required,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024,
                    'data-requirement-id': requirement.id
                })
            )
            
            # Add condition note if exists
            if requirement.condition_note:
                self.fields[field_name].help_text += f" ({requirement.condition_note})"
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = '.' + file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type {file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except ContractDocumentRequirement.DoesNotExist:
                    pass
        
        return cleaned_data


class SRVCreationForm(forms.ModelForm):
    """Form for creating Store Receipt Vouchers."""
    
    class Meta:
        model = StoreReceiptVoucher
        fields = [
            'srv_number', 'delivery_region', 'delivery_school', 'commodity',
            'quantity', 'unit_of_measure', 'unit_price', 'delivery_date',
            'received_by', 'received_by_designation', 'notes', 'document'
        ]
        widgets = {
            'srv_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter SRV number'
            }),
            'delivery_region': forms.Select(attrs={
                'class': 'form-select',
                'id': 'srv_region'
            }),
            'delivery_school': forms.Select(attrs={
                'class': 'form-select',
                'id': 'srv_school',
                'disabled': True
            }),
            'commodity': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter quantity'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100kg bag, 1 crate, 50kg sack'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter unit price'
            }),
            'delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'received_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of person who received goods'
            }),
            'received_by_designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Designation/Position'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Set initial values
        if user and hasattr(user, 'supplier_application'):
            app = user.supplier_application
            if app.region:
                self.fields['delivery_region'].initial = app.region
        
        # Set school queryset to empty initially
        self.fields['delivery_school'].queryset = School.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('delivery_region')
        school = cleaned_data.get('delivery_school')
        
        if region and school and school.region != region:
            raise ValidationError("Selected school does not belong to the selected region.")
        
        return cleaned_data


class ContractDocumentUploadForm(forms.Form):
    """Dynamic form for contract document uploads based on requirements."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active contract document requirements
        requirements = ContractDocumentRequirement.objects.filter(is_active=True)
        
        for requirement in requirements:
            field_name = f'document_{requirement.code}'
            self.fields[field_name] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=requirement.is_required,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024,
                    'data-requirement-id': requirement.id
                })
            )
            
            # Add condition note if exists
            if requirement.condition_note:
                self.fields[field_name].help_text += f" ({requirement.condition_note})"
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = '.' + file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type {file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except ContractDocumentRequirement.DoesNotExist:
                    pass
        
        return cleaned_data


class WaybillCreationForm(forms.ModelForm):
    """Form for creating Waybill documents."""
    
    class Meta:
        model = Waybill
        fields = [
            'waybill_number', 'transporter_name', 'vehicle_number', 'driver_name',
            'driver_license', 'origin', 'destination_region', 'destination_school',
            'commodity', 'quantity', 'unit_of_measure', 'loading_date',
            'expected_delivery_date', 'notes', 'document'
        ]
        widgets = {
            'waybill_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter waybill number'
            }),
            'transporter_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of transporter company'
            }),
            'vehicle_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vehicle registration number'
            }),
            'driver_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Driver full name'
            }),
            'driver_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Driver license number (optional)'
            }),
            'origin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Origin location'
            }),
            'destination_region': forms.Select(attrs={
                'class': 'form-select',
                'id': 'waybill_region'
            }),
            'destination_school': forms.Select(attrs={
                'class': 'form-select',
                'id': 'waybill_school',
                'disabled': True
            }),
            'commodity': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter quantity'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100kg bag, 1 crate, 50kg sack'
            }),
            'loading_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'expected_delivery_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Set school queryset to empty initially
        self.fields['destination_school'].queryset = School.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('destination_region')
        school = cleaned_data.get('destination_school')
        
        if region and school and school.region != region:
            raise ValidationError("Selected school does not belong to the selected region.")
        
        return cleaned_data


class ContractDocumentUploadForm(forms.Form):
    """Dynamic form for contract document uploads based on requirements."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active contract document requirements
        requirements = ContractDocumentRequirement.objects.filter(is_active=True)
        
        for requirement in requirements:
            field_name = f'document_{requirement.code}'
            self.fields[field_name] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=requirement.is_required,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024,
                    'data-requirement-id': requirement.id
                })
            )
            
            # Add condition note if exists
            if requirement.condition_note:
                self.fields[field_name].help_text += f" ({requirement.condition_note})"
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = '.' + file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type {file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except ContractDocumentRequirement.DoesNotExist:
                    pass
        
        return cleaned_data


class InvoiceCreationForm(forms.ModelForm):
    """Form for creating Invoice documents."""
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'client_region', 'client_school', 'commodity',
            'quantity', 'unit_of_measure', 'unit_price', 'invoice_date',
            'due_date', 'tax_rate', 'notes', 'document'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter invoice number'
            }),
            'client_region': forms.Select(attrs={
                'class': 'form-select',
                'id': 'invoice_region'
            }),
            'client_school': forms.Select(attrs={
                'class': 'form-select',
                'id': 'invoice_school',
                'disabled': True
            }),
            'commodity': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter quantity'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100kg bag, 1 crate, 50kg sack'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter unit price'
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Tax rate percentage (e.g., 15.5)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Set school queryset to empty initially
        self.fields['client_school'].queryset = School.objects.none()
        
        # Set default tax rate
        self.fields['tax_rate'].initial = 15.0
    
    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('client_region')
        school = cleaned_data.get('client_school')
        
        if region and school and school.region != region:
            raise ValidationError("Selected school does not belong to the selected region.")
        
        return cleaned_data


class ContractDocumentUploadForm(forms.Form):
    """Dynamic form for contract document uploads based on requirements."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active contract document requirements
        requirements = ContractDocumentRequirement.objects.filter(is_active=True)
        
        for requirement in requirements:
            field_name = f'document_{requirement.code}'
            self.fields[field_name] = forms.FileField(
                label=requirement.label,
                help_text=requirement.description,
                required=requirement.is_required,
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': ','.join(requirement.get_allowed_extensions()),
                    'data-max-size': requirement.max_file_size_mb * 1024 * 1024,
                    'data-requirement-id': requirement.id
                })
            )
            
            # Add condition note if exists
            if requirement.condition_note:
                self.fields[field_name].help_text += f" ({requirement.condition_note})"
    
    def clean(self):
        """Validate file uploads."""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if field_name.startswith('document_') and file:
                # Get requirement code from field name
                requirement_code = field_name.replace('document_', '')
                try:
                    requirement = ContractDocumentRequirement.objects.get(code=requirement_code)
                    
                    # Check file size
                    if file.size > requirement.max_file_size_mb * 1024 * 1024:
                        raise ValidationError(
                            f"{requirement.label}: File size exceeds {requirement.max_file_size_mb}MB"
                        )
                    
                    # Check file extension
                    file_ext = '.' + file.name.split('.')[-1].lower()
                    if file_ext not in requirement.get_allowed_extensions():
                        raise ValidationError(
                            f"{requirement.label}: File type {file_ext} not allowed. "
                            f"Allowed: {', '.join(requirement.get_allowed_extensions())}"
                        )
                
                except ContractDocumentRequirement.DoesNotExist:
                    pass
        
        return cleaned_data
