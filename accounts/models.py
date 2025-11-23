from django.db import models

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