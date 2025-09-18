# Generated manually to add missing business fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0003_supplierapplication_business_registration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierapplication',
            name='business_type',
            field=models.CharField(
                choices=[
                    ('sole', 'Sole Proprietorship'),
                    ('partnership', 'Partnership'),
                    ('limited', 'Limited Liability Company'),
                    ('corporation', 'Corporation'),
                    ('other', 'Other'),
                ],
                default='sole',
                help_text='Type of business entity',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='supplierapplication',
            name='registration_number',
            field=models.CharField(
                default='',
                help_text='Business registration number',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='supplierapplication',
            name='tin_number',
            field=models.CharField(
                default='',
                help_text='Tax Identification Number (TIN)',
                max_length=20,
            ),
        ),
    ]


