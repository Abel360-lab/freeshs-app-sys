"""
Management command to import Ahafo region schools from CSV file.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import csv
from core.models import Region
from applications.models import School


class Command(BaseCommand):
    help = 'Import Ahafo region schools from ahafo.csv file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='ahafo.csv',
            help='CSV file to import (default: ahafo.csv)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force import even if schools already exist',
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        self.stdout.write(f'Importing schools from {csv_file}...')

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                imported_count = 0
                error_count = 0
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        # Clean the data
                        school_code = row['code'].strip()
                        school_name = row['name'].strip()
                        region_name = row['Region'].strip()
                        district = row['district'].strip()
                        address = row['address'].strip()
                        
                        # Handle boolean
                        is_active = row['is_active'].strip().upper() in ['TRUE', '1', 'YES', 'T']
                        
                        # Handle contact fields (convert empty strings to None)
                        contact_person = row.get('contact_person', '').strip() or None
                        contact_phone = row.get('contact_phone', '').strip() or None
                        contact_email = row.get('contact_email', '').strip() or None
                        
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
                        if not options['force'] and School.objects.filter(code=school_code).exists():
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
            
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')

