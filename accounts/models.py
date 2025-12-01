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