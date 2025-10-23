"""
Management command to import data from Excel files.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import tablib
from core.models import Region, Commodity
from applications.models import School


class Command(BaseCommand):
    help = 'Import data from Excel files (XLSX/XLS)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Excel file to import (.xlsx or .xls)',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['schools', 'regions', 'commodities'],
            required=True,
            help='Type of data to import',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force import even if data already exists',
        )
        parser.add_argument(
            '--sheet',
            type=int,
            default=0,
            help='Sheet number to import (0-based, default: 0)',
        )

    def handle(self, *args, **options):
        excel_file = options['file']
        data_type = options['type']
        
        if not os.path.exists(excel_file):
            raise CommandError(f'Excel file not found: {excel_file}')

        # Validate file extension
        file_ext = os.path.splitext(excel_file)[1].lower()
        if file_ext not in ['.xlsx', '.xls']:
            raise CommandError(f'Unsupported file format: {file_ext}. Use .xlsx or .xls')

        self.stdout.write(f'Importing {data_type} from {excel_file}...')

        try:
            # Read Excel file
            with open(excel_file, 'rb') as f:
                if file_ext == '.xlsx':
                    data = tablib.Dataset().load(f.read(), format='xlsx')
                else:  # .xls
                    data = tablib.Dataset().load(f.read(), format='xls')
            
            # Handle multiple sheets
            if hasattr(data, 'sheets') and len(data.sheets) > options['sheet']:
                data = data.sheets[options['sheet']]
            
            self.stdout.write(f'Found {len(data)} rows in Excel file')
            
            # Import based on type
            if data_type == 'schools':
                self.import_schools(data, options['force'])
            elif data_type == 'regions':
                self.import_regions(data, options['force'])
            elif data_type == 'commodities':
                self.import_commodities(data, options['force'])
                
        except Exception as e:
            raise CommandError(f'Error reading Excel file: {str(e)}')

    def import_schools(self, data, force=False):
        """Import schools from Excel data."""
        imported_count = 0
        error_count = 0
        
        for row_num, row in enumerate(data.dict, start=1):
            try:
                # Clean the data
                school_code = str(row.get('code', '')).strip()
                school_name = str(row.get('name', '')).strip()
                region_name = str(row.get('Region', '')).strip()
                district = str(row.get('district', '')).strip()
                address = str(row.get('address', '')).strip()
                
                # Handle boolean
                is_active = str(row.get('is_active', 'True')).strip().upper() in ['TRUE', '1', 'YES', 'T']
                
                # Handle contact fields (convert empty strings to None)
                contact_person = str(row.get('contact_person', '')).strip() or None
                contact_phone = str(row.get('contact_phone', '')).strip() or None
                contact_email = str(row.get('contact_email', '')).strip() or None
                
                # Validate required fields
                if not school_code or not school_name or not region_name:
                    self.stdout.write(
                        self.style.WARNING(f'Row {row_num}: Missing required fields, skipping')
                    )
                    continue
                
                # Get the region
                try:
                    region = Region.objects.get(name=region_name)
                except Region.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Row {row_num}: Region not found: {region_name}')
                    )
                    error_count += 1
                    continue
                
                # Check if school already exists
                if not force and School.objects.filter(code=school_code).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Row {row_num}: School already exists: {school_name} ({school_code})')
                    )
                    continue
                
                # Create or update school
                school, created = School.objects.get_or_create(
                    code=school_code,
                    defaults={
                        'name': school_name,
                        'region': region,
                        'district': district,
                        'address': address,
                        'contact_person': contact_person,
                        'contact_phone': contact_phone,
                        'contact_email': contact_email,
                        'is_active': is_active
                    }
                )
                
                if created:
                    imported_count += 1
                    self.stdout.write(f'  ✓ Created: {school_name} in {region.name}')
                else:
                    self.stdout.write(f'  - Already exists: {school_name}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Row {row_num}: Error processing {row.get("name", "Unknown")}: {str(e)}')
                )
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Import completed: {imported_count} schools imported, {error_count} errors')
        )

    def import_regions(self, data, force=False):
        """Import regions from Excel data."""
        imported_count = 0
        error_count = 0
        
        for row_num, row in enumerate(data.dict, start=1):
            try:
                region_name = str(row.get('name', '')).strip()
                region_code = str(row.get('code', '')).strip()
                is_active = str(row.get('is_active', 'True')).strip().upper() in ['TRUE', '1', 'YES', 'T']
                
                if not region_name or not region_code:
                    self.stdout.write(
                        self.style.WARNING(f'Row {row_num}: Missing required fields, skipping')
                    )
                    continue
                
                region, created = Region.objects.get_or_create(
                    code=region_code,
                    defaults={
                        'name': region_name,
                        'is_active': is_active
                    }
                )
                
                if created:
                    imported_count += 1
                    self.stdout.write(f'  ✓ Created: {region_name} ({region_code})')
                else:
                    self.stdout.write(f'  - Already exists: {region_name}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Row {row_num}: Error processing {row.get("name", "Unknown")}: {str(e)}')
                )
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Import completed: {imported_count} regions imported, {error_count} errors')
        )

    def import_commodities(self, data, force=False):
        """Import commodities from Excel data."""
        imported_count = 0
        error_count = 0
        
        for row_num, row in enumerate(data.dict, start=1):
            try:
                name = str(row.get('name', '')).strip()
                description = str(row.get('description', '')).strip()
                is_active = str(row.get('is_active', 'True')).strip().upper() in ['TRUE', '1', 'YES', 'T']
                is_processed_food = str(row.get('is_processed_food', 'False')).strip().upper() in ['TRUE', '1', 'YES', 'T']
                
                if not name:
                    self.stdout.write(
                        self.style.WARNING(f'Row {row_num}: Missing commodity name, skipping')
                    )
                    continue
                
                commodity, created = Commodity.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'is_active': is_active,
                        'is_processed_food': is_processed_food
                    }
                )
                
                if created:
                    imported_count += 1
                    self.stdout.write(f'  ✓ Created: {name}')
                else:
                    self.stdout.write(f'  - Already exists: {name}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Row {row_num}: Error processing {row.get("name", "Unknown")}: {str(e)}')
                )
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Import completed: {imported_count} commodities imported, {error_count} errors')
        )

