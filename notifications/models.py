from django.db import models
from django.utils import timezone


class NotificationChannels(models.TextChoices):
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push'
    SMS = 'sms', 'SMS'
    IN_APP = 'in_app', 'In App'


class NotificationStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'


class NotificationType(models.TextChoices):
    INFO = 'info', 'Information'
    SUCCESS = 'success', 'Success'
    WARNING = 'warning', 'Warning'
    ERROR = 'error', 'Error'
    COURSE = 'course', 'Course Update'
    ENROLLMENT = 'enrollment', 'Enrollment'
    SESSION = 'session', 'Session'
    LIBRARY = 'library', 'Library'
    SYSTEM = 'system', 'System'
    USER_REGISTRATION = 'user_registration', 'User Registration'


class Notification(models.Model):
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    channel = models.CharField(
        max_length=16, 
        choices=NotificationChannels.choices,
        default=NotificationChannels.IN_APP
    )
    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    
    # Additional metadata for notifications (e.g., course_id, link, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Action link for the notification
    action_url = models.CharField(max_length=500, blank=True, null=True)

    status = models.CharField(
        max_length=16, 
        choices=NotificationStatus.choices, 
        default=NotificationStatus.QUEUED
    )

    sent_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', )
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'read_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_as_read(self):
        if not self.is_read:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def mark_as_unread(self):
        self.read_at = None
        self.save(update_fields=['read_at'])


