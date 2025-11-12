from django.db import models

from django.core.validators import MinValueValidator
from django.utils import timezone
from django.apps import apps 
from django.core.exceptions import ValidationError

class EnrollmentChoices(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CANCELLED = 'cancelled', 'Cancelled'
    COMPLETED = 'completed', 'Completed'
    EXPIRED = 'expired', 'Expired'

class ClassEnrollment(models.Model):
    student = models.ForeignKey(
        "accounts.CustomUser",
        limit_choices_to={"role": 'student'},
        on_delete=models.CASCADE, 
        related_name="class_enrollments"
    )

    class_enrolled = models.ForeignKey('course.Class', on_delete=models.CASCADE, related_name='enrollments')

    status = models.CharField(max_length=20, choices=EnrollmentChoices.choices,  default=EnrollmentChoices.PENDING)

    enrolled_at = models.DateTimeField(blank=True, null=True, help_text="Set when status becomes active for the first time")

    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0)],
        verbose_name="Amount Paid",
        help_text="Amount paid by student for this enrollment. Cannot exceed the class price."
    )
    payment_ref = models.CharField(max_length=255, blank=True, verbose_name="Payment Reference")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'class_enrolled')
        ordering = ('-created_at',)
        verbose_name = 'Class Enrollment'
        verbose_name_plural = 'Class Enrollments'

    def __str__(self):
        return f'ClassEnrollment: {self.student.email} -> {self.class_enrolled.title} ({self.status})'

    def clean(self):
        if self.status == EnrollmentChoices.COMPLETED:
            class_obj = self.class_enrolled
            enrolled_count = class_obj.enrolled_count()
            if not self.pk or ClassEnrollment.objects.get(pk=self.pk).status != EnrollmentChoices.COMPLETED:
                # Only check capacity if this is a new enrollment or status is changing to COMPLETED
                if enrolled_count >= class_obj.capacity:
                    raise ValidationError(f'Cannot complete enrollment: Class "{class_obj.title}" is at full capacity.')
        
        # Validate that price doesn't exceed class price
        if self.class_enrolled:
            class_price = self.class_enrolled.price
            enrollment_price = self.price if self.price else 0
            
            # If class is free (null or 0), allow 0 or empty enrollment price
            if not class_price or class_price == 0:
                # Allow 0 or empty for free classes, but not more than 0
                if enrollment_price > 0:
                    raise ValidationError({
                        'price': f'This class is free. Amount paid cannot exceed $0.00.'
                    })
            else:
                # If class has a price, enrollment price cannot exceed class price
                if enrollment_price > class_price:
                    raise ValidationError({
                        'price': f'Amount paid cannot exceed the class price of ${class_price}. You entered ${enrollment_price}.'
                    })



    def save(self, *args, **kwargs):
        # determine previous status (if any)
        previous_status = None
        if self.pk:
            try:
                prev = ClassEnrollment.objects.get(pk=self.pk)
                previous_status = prev.status
            except ClassEnrollment.DoesNotExist:
                previous_status = None

        # if status becomes completed, set enrolled_at if not set
        if self.status == EnrollmentChoices.COMPLETED and not self.enrolled_at:
            self.enrolled_at = timezone.now()

        super().save(*args, **kwargs)  

        
        StudentProfile = apps.get_model('profiles', 'StudentProfile')

        try:
            student_profile = StudentProfile.objects.get(user=self.student)
        except StudentProfile.DoesNotExist:
            student_profile = None

        if not student_profile:
            return

        # Only update the profile if status actually changed (avoids unnecessary writes).
        if previous_status != self.status:
            if self.status == EnrollmentChoices.COMPLETED:
                if not student_profile.is_paid:
                    student_profile.is_paid = True
                    student_profile.save(update_fields=['is_paid', 'updated_at'])
            else:
                if student_profile.is_paid:
                    student_profile.is_paid = False
                    student_profile.save(update_fields=['is_paid', 'updated_at'])


# Legacy alias for backward compatibility during migration
CourseEnrollment = ClassEnrollment
