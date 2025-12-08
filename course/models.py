from django.db import models

from django.core.validators import MinValueValidator
from django.utils import timezone

from django.core.exceptions import ValidationError

from enrollments.models import EnrollmentChoices
from accounts.models import RoleChoices


current_time = timezone.localtime().time()

class MeetChoices(models.TextChoices):
    ZOOM = "zoom", 'Zoom'
    GOOGLE_MEET = 'google_meet', 'Google_Meet'
    SFU = "sfu", 'SFU Video Conference'
    

class SessionStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    LIVE = 'live', 'Live'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class CourseType(models.TextChoices):
    SIMPLE = 'simple', 'Simple'
    SPECIAL = 'special', 'Special'


class AttendanceStatus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'



class Class(models.Model):
    DAY_OF_WEEK = (
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='course/covers/%Y/%m/%d/', blank=True, null=True)

    teacher = models.ManyToManyField(
        'accounts.CustomUser', 
        related_name="classes",
        limit_choices_to={'role': 'teacher'}
    )
    subject = models.ManyToManyField('subjects.Subject', blank=True, related_name="classes")

    capacity = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(1)])

    is_special_class = models.BooleanField(default=False)

    # Timing fields (previously in CourseTimeTable)
    days_of_week = models.JSONField(default=list, help_text="List of integers representing days of the week (0=Monday, 6=Sunday)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=64, default='UTC')
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    @property
    def is_on_weekend(self):
        """Check if this class is scheduled on weekend (Saturday or Sunday)"""
        return any(day in [5, 6] for day in self.days_of_week) if isinstance(self.days_of_week, list) else False
    
    def get_days_display(self):
        """Return comma-separated string of day names"""
        day_names = dict(self.DAY_OF_WEEK)
        return ', '.join(day_names.get(day, 'Unknown') for day in self.days_of_week) if isinstance(self.days_of_week, list) else ''
    
    def enrolled_count(self):
        """
        Number of students enrolled (COMPLETED) for this class.
        """
        from enrollments.models import ClassEnrollment
        return ClassEnrollment.objects.filter(
            status=EnrollmentChoices.COMPLETED, 
            class_enrolled=self
        ).count()

    def seat_left(self):
        return max(0, self.capacity - self.enrolled_count())

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})
        if not isinstance(self.days_of_week, list) or not all(isinstance(day, int) and 0 <= day <= 6 for day in self.days_of_week):
            raise ValidationError({'days_of_week': 'Days of week must be a list of integers between 0 and 6.'})
        if len(set(self.days_of_week)) != len(self.days_of_week):
            raise ValidationError({'days_of_week': 'Days of week must be unique.'})

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'


# Legacy alias for backward compatibility during migration
Course = Class



class LiveSession(models.Model):
    title = models.CharField(max_length=255, blank=True)
    class_session = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='live_sessions')
    
    # Scheduled date for this session (auto-assigned to next available date)
    scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text='Specific date when this session will occur. Leave blank to auto-calculate based on class schedule (days_of_week).'
    )

    auto_record = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    recording_available = models.BooleanField(default=True)

    # Recording state fields
    is_recording = models.BooleanField(default=False, help_text='Whether recording is currently active')
    recording_started_at = models.DateTimeField(null=True, blank=True, help_text='When recording started')
    recording_file = models.FileField(upload_to='recordings/%Y/%m/%d/', blank=True, null=True, help_text='The recording file')

    status = models.CharField(max_length=25, choices=SessionStatus.choices, default='scheduled')
    
    reminder_sent = models.BooleanField(default=False, help_text='Whether 15-minute reminder has been sent')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-scheduled_date', '-created_at',)

    def __str__(self):
        return f'{self.title} ({self.class_session.start_time.isoformat()})'
    
    def get_next_scheduled_date(self):
        """Get the next available scheduled date for this class based on days_of_week"""
        from datetime import timedelta
        
        # Get the class's scheduled days
        class_days = self.class_session.days_of_week
        if not class_days or not isinstance(class_days, list) or len(class_days) == 0:
            # No schedule defined, use today's date as fallback
            return timezone.localtime().date()
        
        # Get the latest session for this class
        latest_session = LiveSession.objects.filter(
            class_session=self.class_session
        ).exclude(
            pk=self.pk  # Exclude current instance if updating
        ).order_by('-scheduled_date').first()
        
        # Determine starting point
        if latest_session and latest_session.scheduled_date:
            # Start from the day after the latest session
            start_date = latest_session.scheduled_date + timedelta(days=1)
        else:
            # No previous sessions, start from today
            start_date = timezone.localtime().date()
        
        # Find the next date that matches one of the class's scheduled days
        # Check up to 14 days ahead to find the next scheduled day
        for i in range(14):
            check_date = start_date + timedelta(days=i)
            # Python's weekday(): Monday=0, Sunday=6
            # Our model uses: Monday=0, Sunday=6 (same)
            if check_date.weekday() in class_days:
                return check_date
        
        # Fallback: if no matching day found in 2 weeks, return start_date
        return start_date
    
    def generate_title(self):
        """Generate title in format: 'Class Title - Date'"""
        if self.scheduled_date:
            date_str = self.scheduled_date.strftime('%b %d, %Y')
        else:
            # Fallback to created_at if scheduled_date is not set
            date_str = timezone.localtime(self.created_at).strftime('%b %d, %Y')
        return f"{self.class_session.title} - {date_str}"
    
    def save(self, *args, **kwargs):
        """Auto-generate scheduled_date and title if not provided"""
        is_new = not self.pk
        
        # Auto-assign scheduled_date for new sessions
        if is_new and not self.scheduled_date:
            self.scheduled_date = self.get_next_scheduled_date()
        
        # Generate title only if empty or not provided
        # This allows users to provide custom titles
        if not self.title or self.title.strip() == '':
            if is_new:
                # For new instances, we need scheduled_date first
                self.title = "Temporary"
                super().save(*args, **kwargs)
                # Now generate the proper title with scheduled_date
                self.title = self.generate_title()
                # Save again with proper title
                super().save(update_fields=['title'])
                return
            else:
                # For existing instances being updated without a title
                self.title = self.generate_title()
        
        super().save(*args, **kwargs)
    
    def get_session_join_url(self, user):
        """Get the URL to join this session."""
        return f"/video-conference/session/{self.id}/"
    
    def can_user_join(self, user):
        """Check if user can join this session."""
        # Allow superusers and super admins to join any session (for monitoring)
        if user.is_superuser or user.role == RoleChoices.SUPER_ADMIN:
            return True
        
        # Check if user is a teacher of the class
        if self.class_session.teacher.filter(id=user.id).exists():
            return True
        
        # Check if user is enrolled in the class
        from enrollments.models import ClassEnrollment, EnrollmentChoices
        return ClassEnrollment.objects.filter(
            student=user,
            class_enrolled=self.class_session,
            status=EnrollmentChoices.COMPLETED
        ).exists()
    



class Recording(models.Model):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='recordings')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    slides = models.FileField(upload_to='recordings/slides/%Y/%m/%d/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Recording: {self.title} ({self.session})'

    class Meta:
        ordering = ('-created_at',)


class ResourceType(models.TextChoices):
    """Types of resources that can be uploaded to a live session"""
    DOCUMENT = 'document', 'Document'
    IMAGE = 'image', 'Image'
    VIDEO = 'video', 'Video'
    OTHER = 'other', 'Other'


class LiveSessionResource(models.Model):
    """Model for storing resources (files, images, documents) attached to live sessions"""
    session = models.ForeignKey(
        LiveSession, 
        on_delete=models.CASCADE, 
        related_name='resources',
        help_text='The live session this resource belongs to'
    )
    title = models.CharField(
        max_length=255,
        help_text='Title or name of the resource'
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description of the resource'
    )
    file = models.FileField(
        upload_to='live_sessions/resources/%Y/%m/%d/',
        help_text='The file/resource to upload'
    )
    file_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.OTHER,
        help_text='Type of resource'
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    uploaded_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='uploaded_resources',
        help_text='User who uploaded this resource'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['session', '-created_at']),
        ]

    def __str__(self):
        return f'{self.title} - {self.session.title}'
    
    def save(self, *args, **kwargs):
        """Auto-detect file type and size before saving"""
        if self.file:
            # Set file size
            try:
                self.file_size = self.file.size
            except:
                pass
            
            # Auto-detect file type based on extension
            if not self.file_type or self.file_type == ResourceType.OTHER:
                file_name = self.file.name.lower()
                if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']):
                    self.file_type = ResourceType.IMAGE
                elif any(ext in file_name for ext in ['.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx']):
                    self.file_type = ResourceType.DOCUMENT
                elif any(ext in file_name for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']):
                    self.file_type = ResourceType.VIDEO
                else:
                    self.file_type = ResourceType.OTHER
        
        super().save(*args, **kwargs)
    
    def get_file_extension(self):
        """Get the file extension"""
        import os
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        if not self.file_size:
            return 'Unknown'
        
        # Convert bytes to human-readable format
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"



class Attendance(models.Model):
    class_enrollment = models.ForeignKey('enrollments.ClassEnrollment', on_delete=models.CASCADE, related_name='attendance_records')
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='attendance_records')

    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default='absent')
    device_info = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        unique_together = [['class_enrollment', 'session']]
        constraints = [
            models.UniqueConstraint(
                fields=['class_enrollment', 'session'],
                name='unique_attendance_per_session'
            )
        ]

    def __str__(self):
        return f'Student: {self.class_enrollment.student.email} - Session: {self.session.title}'


class Certificate(models.Model):
    student = models.ForeignKey("accounts.CustomUser", limit_choices_to={"role": "student"}, on_delete=models.CASCADE, related_name="certificates")
    class_completed = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="certificates")
    issued_at = models.DateTimeField(default=timezone.now)
    pdf_url = models.URLField(blank=True)

    certificate_code = models.CharField(max_length=128, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.certificate_code:
            import uuid
            self.certificate_code = uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Student: {self.student.email} - Class: {self.class_completed.title}'




