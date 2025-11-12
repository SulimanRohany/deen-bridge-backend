from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    sender_profile_picture = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'session',
            'sender',
            'sender_name',
            'sender_email',
            'sender_role',
            'sender_profile_picture',
            'message',
            'message_type',
            'is_deleted',
            'is_read',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'sender', 'is_read']
    
    def get_sender_name(self, obj):
        """Get the sender's full name or email."""
        return obj.sender.full_name if hasattr(obj.sender, 'full_name') and obj.sender.full_name else obj.sender.email
    
    def get_sender_email(self, obj):
        """Get the sender's email."""
        return obj.sender.email
    
    def get_sender_role(self, obj):
        """Get the sender's role."""
        return obj.sender.role if hasattr(obj.sender, 'role') else 'student'
    
    def get_sender_profile_picture(self, obj):
        """Get the sender's profile picture URL."""
        profile_picture = None
        try:
            if hasattr(obj.sender, 'role'):
                role = obj.sender.role
                if role == 'teacher' and hasattr(obj.sender, 'teacherprofile_profile'):
                    profile = obj.sender.teacherprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
                elif role == 'student' and hasattr(obj.sender, 'studentprofile_profile'):
                    profile = obj.sender.studentprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
                elif role == 'staff' and hasattr(obj.sender, 'staffprofile_profile'):
                    profile = obj.sender.staffprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
                elif role == 'super_admin' and hasattr(obj.sender, 'superadminprofile_profile'):
                    profile = obj.sender.superadminprofile_profile
                    if profile.profile_image:
                        profile_picture = profile.profile_image.url
        except Exception:
            pass
        
        if profile_picture and not profile_picture.startswith('http'):
            profile_picture = f'http://localhost:8000{profile_picture}'
        
        return profile_picture
    
    def get_is_read(self, obj):
        """Check if the current user has read this message."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Check if user is in the read_by list
        return obj.read_by.filter(id=request.user.id).exists()
