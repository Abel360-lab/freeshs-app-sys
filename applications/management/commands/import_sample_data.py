"""
Management command to import sample data for the GCX Supplier Portal.
This command imports regions, commodities, and schools in the correct order.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
import os
import csv
from core.models import Region, Commodity
from applications.models import School


class Command(BaseCommand):
    help = 'Import sample data (regions, commodities, schools) for the GCX Supplier Portal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regions',
            action='store_true',
            help='Import regions only',
        )
        parser.add_argument(
            '--commodities',
            action='store_true',
            help='Import commodities only',
        )
        parser.add_argument(
            '--schools',
            action='store_true',
            help='Import schools only',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Import all sample data (default)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force import even if data already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting sample data import...')
        )

        # Determine what to import
        import_all = options['all'] or not any([
            options['regions'], 
            options['commodities'], 
            options['schools']
        ])

        if import_all or options['regions']:
            self.import_regions(options['force'])
        
        if import_all or options['commodities']:
            self.import_commodities(options['force'])
        
        if import_all or options['schools']:
            self.import_schools(options['force'])

        self.stdout.write(
            self.style.SUCCESS('Sample data import completed successfully!')
        )

    def import_regions(self, force=False):
        """Import regions from CSV file."""
        self.stdout.write('Importing regions...')
        
        if not force and Region.objects.exists():
            self.stdout.write(
                self.style.WARNING('Regions already exist. Use --force to reimport.')
            )
            return

        csv_file = os.path.join(settings.BASE_DIR, 'sample_data', 'regions_import_template.csv')
        
        if not os.path.exists(csv_file):
            raise CommandError(f'Regions CSV file not found: {csv_file}')

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                imported_count = 0
                
                for row in reader:
                    region, created = Region.objects.get_or_create(
                        code=row['code'],
                        defaults={
                            'name': row['name'],
                            'is_active': row['is_active'].lower() == 'true'
                        }
                    )
                    
                    if created:
                        imported_count += 1
                        self.stdout.write(f'  Created region: {region.name}')
                    else:
                        self.stdout.write(f'  Region already exists: {region.name}')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_count} regions')
            )
            
        except Exception as e:
            raise CommandError(f'Error importing regions: {str(e)}')

    def import_commodities(self, force=False):
        """Import commodities from CSV file."""
        self.stdout.write('Importing commodities...')
        
        if not force and Commodity.objects.exists():
            self.stdout.write(
                self.style.WARNING('Commodities already exist. Use --force to reimport.')
            )
            return

        csv_file = os.path.join(settings.BASE_DIR, 'sample_data', 'commodities_import_template.csv')
        
        if not os.path.exists(csv_file):
            raise CommandError(f'Commodities CSV file not found: {csv_file}')

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                imported_count = 0
                
                for row in reader:
                    commodity, created = Commodity.objects.get_or_create(
                        name=row['name'],
                        defaults={
                            'description': row['description'],
                            'is_active': row['is_active'].lower() == 'true',
                            'is_processed_food': row['is_processed_food'].lower() == 'true'
                        }
                    )
                    
                    if created:
                        imported_count += 1
                        self.stdout.write(f'  Created commodity: {commodity.name}')
                    else:
                        self.stdout.write(f'  Commodity already exists: {commodity.name}')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_count} commodities')
            )
            
        except Exception as e:
            raise CommandError(f'Error importing commodities: {str(e)}')

    def import_schools(self, force=False):
        """Import schools from CSV file."""
        self.stdout.write('Importing schools...')
        
        if not force and School.objects.exists():
            self.stdout.write(
                self.style.WARNING('Schools already exist. Use --force to reimport.')
            )
            return

        csv_file = os.path.join(settings.BASE_DIR, 'sample_data', 'schools_import_template.csv')
        
        if not os.path.exists(csv_file):
            raise CommandError(f'Schools CSV file not found: {csv_file}')

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                imported_count = 0
                
                for row in reader:
                    # Get the region
                    try:
                        region = Region.objects.get(name=row['Region'])
                    except Region.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'Region not found: {row["Region"]}. Skipping school: {row["name"]}')
                        )
                        continue

                    school, created = School.objects.get_or_create(
                        code=row['code'],
                        defaults={
                            'name': row['name'],
                            'region': region,
                            'district': row['district'],
                            'address': row['address'],
                            'contact_person': row.get('contact_person', ''),
                            'contact_phone': row.get('contact_phone', ''),
                            'contact_email': row.get('contact_email', ''),
                            'is_active': row['is_active'].lower() == 'true'
                        }
                    )
                    
                    if created:
                        imported_count += 1
                        self.stdout.write(f'  Created school: {school.name} in {region.name}')
                    else:
                        self.stdout.write(f'  School already exists: {school.name}')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_count} schools')
            )
            
        except Exception as e:
            raise CommandError(f'Error importing schools: {str(e)}')

