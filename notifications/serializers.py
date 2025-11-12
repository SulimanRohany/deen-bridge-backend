from rest_framework import serializers
from django.utils import timezone

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'channel', 'type', 'title', 'body', 
            'metadata', 'action_url', 'status', 'sent_at', 
            'read_at', 'is_read', 'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = ['sent_at', 'read_at', 'created_at', 'updated_at', 'is_read', 'time_ago']
    
    def get_is_read(self, obj):
        return obj.is_read
    
    def get_time_ago(self, obj):
        """Return human-readable time ago"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        return "Just now"


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    is_read = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'body', 'action_url', 'is_read', 'time_ago', 'created_at']
    
    def get_is_read(self, obj):
        return obj.is_read
    
    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        return "Just now"

