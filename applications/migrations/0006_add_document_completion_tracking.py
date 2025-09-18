# Generated manually for document completion tracking

from django.db import migrations, models
import uuid


def generate_unique_tokens(apps, schema_editor):
    """Generate unique tokens for existing records."""
    SupplierApplication = apps.get_model('applications', 'SupplierApplication')
    for application in SupplierApplication.objects.all():
        application.completion_token = uuid.uuid4()
        application.save(update_fields=['completion_token'])


def reverse_generate_tokens(apps, schema_editor):
    """Reverse operation - no need to do anything."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0005_add_additional_fields'),
    ]

    operations = [
        # First add the field without unique constraint
        migrations.AddField(
            model_name='supplierapplication',
            name='completion_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='Secure token for document completion', null=True),
        ),
        # Generate unique tokens for existing records
        migrations.RunPython(generate_unique_tokens, reverse_generate_tokens),
        # Now make it unique and not null
        migrations.AlterField(
            model_name='supplierapplication',
            name='completion_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='Secure token for document completion', unique=True),
        ),
        migrations.AddField(
            model_name='supplierapplication',
            name='missing_documents',
            field=models.JSONField(blank=True, default=list, help_text='List of missing document types'),
        ),
        migrations.AddField(
            model_name='supplierapplication',
            name='gcx_registration_proof_uploaded',
            field=models.BooleanField(default=False, help_text='Whether GCX Registration Proof has been uploaded'),
        ),
        migrations.AddField(
            model_name='supplierapplication',
            name='document_completion_deadline',
            field=models.DateTimeField(blank=True, help_text='Deadline for completing missing documents', null=True),
        ),
    ]
