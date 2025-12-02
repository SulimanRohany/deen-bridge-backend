from django.db import models
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, EmailValidator


class RoleChoices(models.TextChoices):
    STUDENT = 'student', 'Student'
    TEACHER = 'teacher', 'Teacher'
    PARENT = 'parent', 'Parent'
    STAFF = 'staff', 'Staff'
    SUPER_ADMIN = 'super_admin', "Super Admin"



class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, password=None, full_name=None, role=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email.")
        if not full_name:
            raise ValueError("Users must have a full name")
        if not role:
            raise ValueError("Users must have a role")

        # Normalize email
        email = self.normalize_email(email)
        
        # Remove email from extra_fields if present to avoid duplication
        extra_fields.pop('email', None)

        user = self.model(
            email=email,
            full_name=full_name,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, full_name=None,  **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', RoleChoices.SUPER_ADMIN)
        extra_fields.setdefault('email_verified', True)  # Superusers are automatically verified
        return self.create_user(
            email=email, 
            password=password, 
            full_name=full_name,
            **extra_fields
        )


class CustomUser(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(unique=True, validators=[EmailValidator()])
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=100, choices=RoleChoices.choices)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'  # Still needed for some commands
    REQUIRED_FIELDS = ['full_name', 'role']

    objects = CustomUserManager()


    def __str__(self):
        return f"{self.email} - {self.role}"




class StudentUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role="student")

class StudentUser(CustomUser):
    objects = StudentUserManager()

    class Meta:
        proxy = True


class TeacherUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role="teacher")

class TeacherUser(CustomUser):
    objects = TeacherUserManager()

    class Meta:
        proxy = True


class ParentUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role="parent")

class ParentUser(CustomUser):
    objects = ParentUserManager()

    class Meta:
        proxy = True


class StaffUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role="staff")

class StaffUser(CustomUser):
    objects = StaffUserManager()

    class Meta:
        proxy = True


class SuperAdminUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role="super_admin")

class SuperAdminUser(CustomUser):
    objects = SuperAdminUserManager()

    class Meta:
        proxy = True
        verbose_name = "super admin user"


class PasswordResetToken(models.Model):
    """Model to store password reset tokens with expiration and single-use validation"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
        ]

    def __str__(self):
        return f"Password reset token for {self.user.email} - {'Used' if self.used else 'Active'}"

    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save(update_fields=['used'])

    @classmethod
    def create_for_user(cls, user, expiration_hours=1):
        """Create a new password reset token for a user"""
        import secrets
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=expiration_hours)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )


class EmailVerificationToken(models.Model):
    """Model to store email verification tokens with expiration and single-use validation"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'email_verification_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
        ]

    def __str__(self):
        return f"Email verification token for {self.user.email} - {'Used' if self.used else 'Active'}"

    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save(update_fields=['used'])

    @classmethod
    def create_for_user(cls, user, expiration_hours=24):
        """Create a new email verification token for a user"""
        import secrets
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=expiration_hours)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )


class EmailVerificationAttempt(models.Model):
    """Model to track email verification attempts for security purposes"""
    email = models.EmailField(db_index=True)
    attempt_count = models.IntegerField(default=0)
    first_attempt_at = models.DateTimeField(auto_now_add=True)
    last_attempt_at = models.DateTimeField(auto_now=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'email_verification_attempts'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['locked_until']),
        ]
    
    def __str__(self):
        return f"Verification attempts for {self.email} - Count: {self.attempt_count}"
    
    def is_locked(self):
        """Check if this email is currently locked due to too many attempts"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def increment_attempts(self, ip_address=None):
        """Increment attempt count and lock if necessary"""
        self.attempt_count += 1
        if ip_address:
            self.ip_address = ip_address
        
        # Lock for 1 hour after 5 failed attempts
        if self.attempt_count >= 5:
            self.locked_until = timezone.now() + timedelta(hours=1)
        
        self.save()
    
    def reset_attempts(self):
        """Reset attempt count after successful verification"""
        self.attempt_count = 0
        self.locked_until = None
        self.save()
    
    @classmethod
    def cleanup_old_attempts(cls):
        """Clean up attempts older than 24 hours"""
        cutoff_time = timezone.now() - timedelta(hours=24)
        cls.objects.filter(
            first_attempt_at__lt=cutoff_time,
            locked_until__isnull=True
        ).delete()
        
        # Also clean up expired locks
        cls.objects.filter(
            locked_until__lt=timezone.now()
        ).update(locked_until=None, attempt_count=0)
    
    @classmethod
    def get_or_create_for_email(cls, email, ip_address=None):
        """Get or create an attempt record for an email"""
        # First cleanup old attempts
        cls.cleanup_old_attempts()
        
        attempt, created = cls.objects.get_or_create(
            email=email.lower(),
            defaults={'ip_address': ip_address}
        )
        return attempt