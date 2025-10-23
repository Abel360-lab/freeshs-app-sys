# Generated manually for SiteSettings model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0006_add_unit_of_measure_to_commodity'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='Ghana Commodity Exchange', help_text='Official company name', max_length=200)),
                ('tagline', models.CharField(default='Connecting People, Connecting Markets & Providing Opportunities', help_text='Company tagline or slogan', max_length=300)),
                ('primary_phone', models.CharField(default='+233 24 123 4567', help_text='Primary contact phone number', max_length=20)),
                ('secondary_phone', models.CharField(blank=True, default='+233 30 123 4567', help_text='Secondary contact phone number', max_length=20)),
                ('support_email', models.EmailField(default='itsupport@gcx.com.gh', help_text='IT Support email address', max_length=254)),
                ('info_email', models.EmailField(default='info@gcx.com.gh', help_text='General information email address', max_length=254)),
                ('address_line1', models.CharField(default='2nd Floor, Africa Trade House', help_text='Address line 1', max_length=200)),
                ('address_line2', models.CharField(blank=True, default='Ridge, Accra', help_text='Address line 2', max_length=200)),
                ('city', models.CharField(default='Accra', help_text='City', max_length=100)),
                ('country', models.CharField(default='Ghana', help_text='Country', max_length=100)),
                ('weekday_hours', models.CharField(default='Monday - Friday: 8:00 AM - 5:00 PM', help_text='Weekday business hours', max_length=100)),
                ('weekend_hours', models.CharField(blank=True, default='Saturday: 9:00 AM - 1:00 PM', help_text='Weekend business hours', max_length=100)),
                ('facebook_url', models.URLField(blank=True, default='', help_text='Facebook page URL')),
                ('twitter_url', models.URLField(blank=True, default='', help_text='X (Twitter) profile URL')),
                ('linkedin_url', models.URLField(blank=True, default='', help_text='LinkedIn company page URL')),
                ('instagram_url', models.URLField(blank=True, default='', help_text='Instagram profile URL')),
                ('youtube_url', models.URLField(blank=True, default='', help_text='YouTube channel URL')),
                ('show_social_media', models.BooleanField(default=True, help_text='Display social media links on the website')),
                ('portal_version', models.CharField(default='v1.0', help_text='Portal version number', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, help_text='User who last updated the settings', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_settings_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Site Settings',
                'verbose_name_plural': 'Site Settings',
                'db_table': 'core_site_settings',
            },
        ),
    ]

