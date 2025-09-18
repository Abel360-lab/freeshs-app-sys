"""
Management command to generate notification analytics.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.models import NotificationAnalytics


class Command(BaseCommand):
    help = 'Generate notification analytics for specified date range'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to generate analytics for (default: 7)'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to generate analytics for (YYYY-MM-DD)'
        )
    
    def handle(self, *args, **options):
        if options['date']:
            # Generate for specific date
            try:
                date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
                self.generate_analytics_for_date(date)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully generated analytics for {date}')
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
        else:
            # Generate for date range
            days = options['days']
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            current_date = start_date
            while current_date <= end_date:
                self.generate_analytics_for_date(current_date)
                current_date += timedelta(days=1)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated analytics for {days} days')
            )
    
    def generate_analytics_for_date(self, date):
        """Generate analytics for a specific date."""
        try:
            NotificationAnalytics.generate_daily_analytics(date)
            self.stdout.write(f'Generated analytics for {date}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating analytics for {date}: {str(e)}')
            )
