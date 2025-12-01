# Generated manually for email verification system

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def set_existing_users_as_verified(apps, schema_editor):
    """Set all existing users as email_verified=True"""
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.all().update(email_verified=True)


def reverse_set_existing_users_as_verified(apps, schema_editor):
    """Reverse migration - set all users back to email_verified=False"""
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.all().update(email_verified=False)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_passwordresettoken'),
    ]

    operations = [
        # Add email_verified field to CustomUser
        migrations.AddField(
            model_name='customuser',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        # Create EmailVerificationToken model
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_verification_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'email_verification_tokens',
            },
        ),
        # Add indexes to EmailVerificationToken
        migrations.AddIndex(
            model_name='emailverificationtoken',
            index=models.Index(fields=['token'], name='email_veri_token_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverificationtoken',
            index=models.Index(fields=['user', 'used'], name='email_veri_user_id_def456_idx'),
        ),
        # Data migration: Set existing users as verified
        migrations.RunPython(
            set_existing_users_as_verified,
            reverse_set_existing_users_as_verified,
        ),
    ]

