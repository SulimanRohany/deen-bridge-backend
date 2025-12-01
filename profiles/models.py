from django.db import models
from django.conf import settings

from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import RoleChoices

class GenderChoices(models.TextChoices):
    MALE = "male", 'Male',
    FEMALE = "female", 'Female'
    OTHER = "other", 'Other'


class BaseProfile(models.Model):
    profile_image = models.ImageField(upload_to='profiles/profile_images/%Y/%m/%d/', blank=True, null=True)
    address = models.TextField(blank=True)

    gender = models.CharField(max_length=10, choices=GenderChoices.choices, blank=True)

    phone_number = models.CharField(max_length=32, blank=True, null=True)
    date_of_birth = models.DateTimeField(blank=True, null=True)



    preferred_timezone = models.CharField(max_length=100, default='UTC')
    preferred_language = models.CharField(max_length=100, default="en")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True

    def clean(self):
        if self.date_of_birth and self.date_of_birth >= timezone.now():
            raise ValidationError({'date_of_birth': 'Date of birth must not be in the future.'})



class TeacherProfile(BaseProfile):
    user = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="%(class)s_profile",
        limit_choices_to={'role': RoleChoices.TEACHER}
    )
    department = models.CharField(max_length=128, blank=True)
    specialization = models.CharField(max_length=256, blank=True)
    qualification = models.CharField(max_length=256, blank=True)

    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profile: {self.user.email} - Teacher"



class StudentProfile(BaseProfile):
    user = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="%(class)s_profile",
        limit_choices_to={'role': RoleChoices.STUDENT}
    )

    is_paid = models.BooleanField(default=False)

    # add the logic that if the studnet is minor we should create a parent account automatically for it 
    is_minor = models.BooleanField(default=False)

    @property
    def calculated_is_minor(self):
        if not self.date_of_birth:
            return self.is_minor
        age = (timezone.now().date() - self.date_of_birth).days / 365.2
        return age < 16

    def __str__(self):
        return f"Profile: {self.user.email} - Student"


class SuperAdminProfile(BaseProfile):
    user = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="%(class)s_profile",
        limit_choices_to={'role': RoleChoices.SUPER_ADMIN}
    )

class StaffProfile(BaseProfile):
    user = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="%(class)s_profile",
        limit_choices_to={'role': RoleChoices.STAFF}
    )
    position = models.CharField(max_length=128, blank=True)


class StudentParentProfile(models.Model):
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="student_parent_relationships",
        limit_choices_to={'role': RoleChoices.PARENT}
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='student_parent_profiles')
    relationship = models.CharField(max_length=100, blank=True)
    preferred_language = models.CharField(max_length=100, default='en')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("student", "user")
        verbose_name = 'Student Parent Relationship'
        verbose_name_plural = 'Student Parent Relationships'
    
    def __str__(self):
        return f'{self.user.full_name} - {self.student.user.full_name} ({self.relationship})'