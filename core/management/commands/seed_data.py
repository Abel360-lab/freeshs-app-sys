"""
Management command to seed the database with initial data.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Region, Commodity, Warehouse
from documents.models import DocumentRequirement

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with initial data...')
        
        # Create superuser if it doesn't exist
        self.create_superuser()
        
        # Seed regions
        self.seed_regions()
        
        # Seed commodities
        self.seed_commodities()
        
        # Seed warehouses
        self.seed_warehouses()
        
        # Seed document requirements
        self.seed_document_requirements()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with initial data')
        )

    def create_superuser(self):
        """Create superuser if it doesn't exist."""
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email='admin@gcx.com.gh',
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role=User.Role.ADMIN
            )
            self.stdout.write('Created superuser: admin@gcx.com.gh / admin123')

    def seed_regions(self):
        """Seed Ghana regions."""
        regions_data = [
            {'code': 'AR', 'name': 'Ashanti Region'},
            {'code': 'AS', 'name': 'Ashanti Region'},
            {'code': 'BA', 'name': 'Brong-Ahafo Region'},
            {'code': 'CR', 'name': 'Central Region'},
            {'code': 'ER', 'name': 'Eastern Region'},
            {'code': 'GR', 'name': 'Greater Accra Region'},
            {'code': 'NR', 'name': 'Northern Region'},
            {'code': 'UE', 'name': 'Upper East Region'},
            {'code': 'UW', 'name': 'Upper West Region'},
            {'code': 'VR', 'name': 'Volta Region'},
            {'code': 'WR', 'name': 'Western Region'},
        ]
        
        for region_data in regions_data:
            region, created = Region.objects.get_or_create(
                code=region_data['code'],
                defaults=region_data
            )
            if created:
                self.stdout.write(f'Created region: {region.name}')

    def seed_commodities(self):
        """Seed commodities."""
        commodities_data = [
            {
                'name': 'Rice',
                'description': 'White and brown rice varieties',
                'is_processed_food': False
            },
            {
                'name': 'Maize',
                'description': 'Yellow and white maize',
                'is_processed_food': False
            },
            {
                'name': 'Tom Brown',
                'description': 'Processed cereal food',
                'is_processed_food': True
            },
            {
                'name': 'Palm Oil',
                'description': 'Cooking oil from palm fruits',
                'is_processed_food': True
            },
            {
                'name': 'Cassava',
                'description': 'Fresh cassava tubers',
                'is_processed_food': False
            },
            {
                'name': 'Yam',
                'description': 'Fresh yam tubers',
                'is_processed_food': False
            },
            {
                'name': 'Plantain',
                'description': 'Fresh plantain',
                'is_processed_food': False
            },
            {
                'name': 'Groundnut',
                'description': 'Groundnuts and groundnut products',
                'is_processed_food': False
            },
            {
                'name': 'Soybean',
                'description': 'Soybeans and soybean products',
                'is_processed_food': False
            },
            {
                'name': 'Sorghum',
                'description': 'Sorghum grains',
                'is_processed_food': False
            },
        ]
        
        for commodity_data in commodities_data:
            commodity, created = Commodity.objects.get_or_create(
                name=commodity_data['name'],
                defaults=commodity_data
            )
            if created:
                self.stdout.write(f'Created commodity: {commodity.name}')

    def seed_warehouses(self):
        """Seed warehouses."""
        warehouses_data = [
            {
                'name': 'Accra Central Warehouse',
                'city': 'Accra',
                'region_code': 'GR',
                'address': 'Central Business District, Accra',
                'contact_person': 'John Doe',
                'contact_phone': '+233241234567'
            },
            {
                'name': 'Kumasi Main Warehouse',
                'city': 'Kumasi',
                'region_code': 'AR',
                'address': 'Industrial Area, Kumasi',
                'contact_person': 'Jane Smith',
                'contact_phone': '+233241234568'
            },
            {
                'name': 'Tamale Storage Facility',
                'city': 'Tamale',
                'region_code': 'NR',
                'address': 'Commercial Area, Tamale',
                'contact_person': 'Mohammed Ali',
                'contact_phone': '+233241234569'
            },
            {
                'name': 'Cape Coast Depot',
                'city': 'Cape Coast',
                'region_code': 'CR',
                'address': 'Harbor Road, Cape Coast',
                'contact_person': 'Kwame Asante',
                'contact_phone': '+233241234570'
            },
            {
                'name': 'Takoradi Port Warehouse',
                'city': 'Takoradi',
                'region_code': 'WR',
                'address': 'Port Area, Takoradi',
                'contact_person': 'Ama Boateng',
                'contact_phone': '+233241234571'
            },
        ]
        
        for warehouse_data in warehouses_data:
            region = Region.objects.get(code=warehouse_data.pop('region_code'))
            warehouse_data['region'] = region
            
            warehouse, created = Warehouse.objects.get_or_create(
                name=warehouse_data['name'],
                defaults=warehouse_data
            )
            if created:
                self.stdout.write(f'Created warehouse: {warehouse.name}')

    def seed_document_requirements(self):
        """Seed document requirements."""
        requirements_data = [
            {
                'code': 'BUSINESS_REGISTRATION_DOCS',
                'label': 'Business Registration Documents',
                'description': 'Certificate of Incorporation, Form 3, Form C',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'VAT_CERTIFICATE',
                'label': 'VAT Certificate',
                'description': 'Valid VAT registration certificate',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'PPA_CERTIFICATE',
                'label': 'PPA Certificate',
                'description': 'Valid PPA registration certificate',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'TAX_CLEARANCE_CERT',
                'label': 'Tax Clearance Certificate',
                'description': 'Valid tax clearance certificate with TIN number',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'PROOF_OF_OFFICE',
                'label': 'Proof of Office',
                'description': 'Utility bill, rent agreement, or other proof of office location',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'ID_MD_CEO_PARTNERS',
                'label': 'ID of MD/CEO/Partners',
                'description': 'Valid ID of directors, partners, or managing director',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'GCX_REGISTRATION_PROOF',
                'label': 'GCX Registration Proof',
                'description': 'Proof of GCX registration or membership',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'TEAM_MEMBER_ID',
                'label': 'Team Member ID',
                'description': 'Valid ID of experienced team member',
                'is_required': True,
                'condition_note': 'Required for all applications',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
            {
                'code': 'FDA_CERT_PROCESSED_FOOD',
                'label': 'FDA Certificate for Processed Food',
                'description': 'FDA certificate for processed food products',
                'is_required': False,
                'condition_note': 'Required only if supplying processed foods',
                'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
                'max_file_size_mb': 10
            },
        ]
        
        for req_data in requirements_data:
            requirement, created = DocumentRequirement.objects.get_or_create(
                code=req_data['code'],
                defaults=req_data
            )
            if created:
                self.stdout.write(f'Created document requirement: {requirement.label}')
