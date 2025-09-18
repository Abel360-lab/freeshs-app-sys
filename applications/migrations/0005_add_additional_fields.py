# Generated manually to add additional missing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0004_add_business_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierapplication',
            name='postal_code',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Postal/ZIP code',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='supplierapplication',
            name='data_consent',
            field=models.BooleanField(
                default=False,
                help_text='Whether the applicant consents to data processing',
            ),
        ),
        migrations.AddField(
            model_name='teammember',
            name='position',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Position/role of the team member',
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name='teammember',
            name='years_experience',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Years of experience in food supply/distribution',
                null=True,
            ),
        ),
    ]


