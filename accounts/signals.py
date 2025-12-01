from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, RoleChoices
from profiles.models import TeacherProfile, StudentProfile, StudentParentProfile, StaffProfile, SuperAdminProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == RoleChoices.TEACHER:
            TeacherProfile.objects.create(user=instance)
        elif instance.role == RoleChoices.STUDENT:
            StudentProfile.objects.create(user=instance)
        # Note: StudentParentProfile is not auto-created for parents
        # as it requires a student relationship which is created separately
        elif instance.role == RoleChoices.STAFF:
            StaffProfile.objects.create(user=instance)
        elif instance.role == RoleChoices.SUPER_ADMIN:
            SuperAdminProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def notify_super_admins_on_new_user(sender, instance, created, **kwargs):
    """
    Send real-time notification to all super admins when a new user is created/registered
    """
    if created:
        # Import here to avoid circular imports
        from notifications.utils import send_notification_to_multiple_users
        from notifications.models import NotificationType
        from django.conf import settings
        
        # Get all super admin users
        super_admins = CustomUser.objects.filter(role=RoleChoices.SUPER_ADMIN)
        
        if super_admins.exists():
            # Create notification title and body
            title = "New User Registration"
            body = f"A new {instance.get_role_display()} has registered: {instance.full_name} ({instance.email})"
            
            # Determine the appropriate action URL
            # You can change this to a frontend URL if you have a user management page
            # For now, pointing to Django admin on backend
            backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
            action_url = f"{backend_url}/admin/accounts/customuser/{instance.id}/change/"
            
            # Send notification to all super admins
            send_notification_to_multiple_users(
                users=super_admins,
                title=title,
                body=body,
                notification_type=NotificationType.USER_REGISTRATION,
                action_url=action_url,
                metadata={
                    'user_id': instance.id,
                    'user_email': instance.email,
                    'user_full_name': instance.full_name,
                    'user_role': instance.role,
                    'admin_url': action_url,  # Full Django admin URL
                    'frontend_path': f'/admin/users/{instance.id}',  # Suggested frontend path
                }
            )


@receiver(post_save, sender=CustomUser)
def send_verification_email_on_registration(sender, instance, created, **kwargs):
    """
    Send email verification email when a new user is created
    Only sends if user is not already verified and not a superuser
    """
    if created and not instance.email_verified:
        # Skip verification for superusers - they are automatically verified
        if instance.is_superuser:
            instance.email_verified = True
            instance.save(update_fields=['email_verified'])
            return
        
        try:
            # Import here to avoid circular imports
            from .models import EmailVerificationToken
            from .utils import send_email_verification
            
            # Create verification token (24 hour expiration)
            verification_token = EmailVerificationToken.create_for_user(instance, expiration_hours=24)
            
            # Send verification email
            send_email_verification(instance, verification_token.token)
        except Exception as e:
            # Log error but don't prevent user creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {instance.email}: {str(e)}")
            # Don't raise - user creation should still succeed even if email fails