from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomCourseRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('contacted', 'Contacted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    COURSE_TYPE_CHOICES = [
        ('family', 'Family Course'),
        ('private', 'Private Class (1-on-1)'),
        ('group', 'Small Group (2-5 people)'),
        ('corporate', 'Corporate Training'),
    ]

    SCHEDULE_CHOICES = [
        ('morning', 'Morning (8am-12pm)'),
        ('afternoon', 'Afternoon (12pm-5pm)'),
        ('evening', 'Evening (5pm-9pm)'),
        ('weekend', 'Weekend Only'),
        ('flexible', 'Flexible'),
    ]

    # Personal Information
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Course Details
    courseType = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    numberOfStudents = models.CharField(max_length=10, blank=True, null=True)
    preferredSchedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, blank=True, null=True)
    subjects = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_course_requests')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, null=True)
    response_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Custom Course Request'
        verbose_name_plural = 'Custom Course Requests'

    def __str__(self):
        return f"{self.name} - {self.get_courseType_display()} ({self.status})"

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def response_time(self):
        """Calculate response time in minutes"""
        if self.response_sent_at:
            delta = self.response_sent_at - self.created_at
            return delta.total_seconds() / 60
        return None

