from django.db import models
from django.conf import settings
from core.models import TimeStampedModel


class ChatMessage(TimeStampedModel):
    """Model for storing chat messages in live sessions."""
    session = models.ForeignKey(
        'course.LiveSession',
        on_delete=models.CASCADE,
        related_name='chat_messages',
        help_text='The live session this message belongs to'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text='The user who sent the message'
    )
    message = models.TextField(
        blank=True,
        help_text='The chat message content'
    )
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('system', 'System'),
        ],
        default='text',
        help_text='Type of message'
    )
    
    # Array of users who have read this message (sender is automatically added)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_chat_messages',
        blank=True,
        help_text='Users who have read this message'
    )
    
    is_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.email} - {self.message[:50]} ({self.created_at})"
    
    def save(self, *args, **kwargs):
        """Override save to automatically add sender to read_by."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Add sender to read_by after save (for new messages)
        if is_new:
            self.read_by.add(self.sender)
    
    def to_dict(self):
        """Convert message to dictionary for WebSocket transmission."""
        # Get profile picture based on user role
        profile_picture = None
        try:
            if hasattr(self.sender, 'role'):
                role = self.sender.role
                if role == 'teacher' and hasattr(self.sender, 'teacherprofile_profile'):
                    profile = self.sender.teacherprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
                elif role == 'student' and hasattr(self.sender, 'studentprofile_profile'):
                    profile = self.sender.studentprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
                elif role == 'staff' and hasattr(self.sender, 'staffprofile_profile'):
                    profile = self.sender.staffprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
                elif role == 'super_admin' and hasattr(self.sender, 'superadminprofile_profile'):
                    profile = self.sender.superadminprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
        except Exception:
            # If profile doesn't exist or has no image, profile_picture remains None
            pass
        
        # Construct full URL for profile picture
        if profile_picture and not profile_picture.startswith('http'):
            # Add backend domain to relative URLs
            profile_picture = f'http://localhost:8000{profile_picture}'
        
        return {
            'id': self.id,
            'session_id': str(self.session.id),
            'sender_id': self.sender.id,
            'sender_name': self.sender.full_name if hasattr(self.sender, 'full_name') and self.sender.full_name else self.sender.email,
            'sender_email': self.sender.email,
            'sender_role': self.sender.role if hasattr(self.sender, 'role') else 'student',
            'sender_profile_picture': profile_picture,
            'message': self.message,
            'message_type': self.message_type,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
        }
