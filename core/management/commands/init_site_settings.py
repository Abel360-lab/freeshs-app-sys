"""
Management command to initialize site settings with default values.
"""

from django.core.management.base import BaseCommand
from core.models import SiteSettings


class Command(BaseCommand):
    help = 'Initialize site settings with default values'

    def handle(self, *args, **options):
        settings, created = SiteSettings.objects.get_or_create(pk=1)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Successfully created site settings with default values')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ Site settings already exist')
            )
        
        # Display current settings
        self.stdout.write('\n📋 Current Site Settings:')
        self.stdout.write(f'   Company: {settings.company_name}')
        self.stdout.write(f'   Tagline: {settings.tagline}')
        self.stdout.write(f'   Primary Phone: {settings.primary_phone}')
        self.stdout.write(f'   Support Email: {settings.support_email}')
        self.stdout.write(f'   Address: {settings.get_full_address()}')
        self.stdout.write(f'   Portal Version: {settings.portal_version}')
        
        # Social Media Status
        self.stdout.write('\n🌐 Social Media Links:')
        self.stdout.write(f'   Show Social Media: {"Yes" if settings.show_social_media else "No"}')
        if settings.facebook_url:
            self.stdout.write(f'   Facebook: {settings.facebook_url}')
        if settings.twitter_url:
            self.stdout.write(f'   X (Twitter): {settings.twitter_url}')
        if settings.linkedin_url:
            self.stdout.write(f'   LinkedIn: {settings.linkedin_url}')
        if settings.instagram_url:
            self.stdout.write(f'   Instagram: {settings.instagram_url}')
        if settings.youtube_url:
            self.stdout.write(f'   YouTube: {settings.youtube_url}')
        
        self.stdout.write('\n✨ You can now update these settings from the Django admin panel at:')
        self.stdout.write('   /admin/core/sitesettings/1/change/')

