from django.db import models
import uuid

# Create your models here.

class TimeStampedModel(models.Model):
    """Abstract base class with self-updating 'created_at' and 'updated_at' fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base class with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class CompanySetting(models.Model):
    contact = models.ManyToManyField(
        "CompanyContact",
        related_name='company_settings'
    )
    default_timezone = models.CharField(max_length=64, default='UTC')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class CompanyContact(models.Model):
    department = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Department: {self.department} - email: {self.email} - phone_number: {self.phone_number}"


class ContactMessage(TimeStampedModel, UUIDModel):
    """Model to store contact form messages - DEPRECATED: Use UserCommunication instead"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.status})"


class UserCommunication(TimeStampedModel):
    """Unified model for all user-to-admin communications"""
    
    COMMUNICATION_TYPE_CHOICES = [
        ('custom_request', 'Custom Course Request'),
        ('contact_message', 'Contact Message'),
        ('report', 'Report'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('new', 'New'),
        ('read', 'Read'),
        ('reviewed', 'Reviewed'),
        ('contacted', 'Contacted'),
        ('replied', 'Replied'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('resolved', 'Resolved'),
    ]
    
    # Custom Course Request choices
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
    
    # Report choices
    REPORT_TYPE_CHOICES = [
        ('bug', 'Bug/Issue'),
        ('content', 'Inappropriate Content'),
        ('feedback', 'Feedback'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other'),
    ]
    
    # Core fields (common to all types)
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    user = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='communications'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin fields
    admin_notes = models.TextField(blank=True, null=True)
    response_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking fields
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Type-specific fields for Contact Messages
    subject = models.CharField(max_length=255, blank=True, null=True)
    
    # Type-specific fields for Custom Course Requests
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, blank=True, null=True)
    number_of_students = models.CharField(max_length=10, blank=True, null=True)
    preferred_schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, blank=True, null=True)
    subjects = models.CharField(max_length=255, blank=True, null=True)
    
    # Type-specific fields for Reports
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    screen_shot = models.ImageField(upload_to='reports/screen_shots/', blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Communication'
        verbose_name_plural = 'User Communications'
        indexes = [
            models.Index(fields=['communication_type', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        type_display = self.get_communication_type_display()
        return f"{self.name} - {type_display} ({self.status})"
    
    @property
    def is_pending(self):
        """Check if communication is pending"""
        return self.status in ['pending', 'new']
    
    @property
    def response_time(self):
        """Calculate response time in minutes"""
        if self.response_sent_at:
            delta = self.response_sent_at - self.created_at
            return delta.total_seconds() / 60
        return None
    
    def get_type_display_fields(self):
        """Return a dictionary of relevant fields based on communication type"""
        if self.communication_type == 'custom_request':
            return {
                'course_type': self.get_course_type_display() if self.course_type else None,
                'number_of_students': self.number_of_students,
                'preferred_schedule': self.get_preferred_schedule_display() if self.preferred_schedule else None,
                'subjects': self.subjects,
            }
        elif self.communication_type == 'contact_message':
            return {
                'subject': self.subject,
            }
        elif self.communication_type == 'report':
            return {
                'report_type': self.get_report_type_display() if self.report_type else None,
                'title': self.title,
                'screen_shot': self.screen_shot.url if self.screen_shot else None,
                'is_resolved': self.is_resolved,
            }
        return {}
    
    def save(self, *args, **kwargs):
        """Set default status based on communication type if not set"""
        if not self.status:
            if self.communication_type == 'contact_message':
                self.status = 'new'
            else:
                self.status = 'pending'
        super().save(*args, **kwargs)