from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for chat messages."""
    list_display = ['id', 'session', 'sender', 'message_preview', 'message_type', 'read_count', 'created_at']
    list_filter = ['message_type', 'is_deleted', 'created_at']
    search_fields = ['message', 'sender__email', 'session__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    filter_horizontal = ['read_by']  # Makes read_by field easier to manage
    
    def message_preview(self, obj):
        """Show preview of message."""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    
    message_preview.short_description = 'Message Preview'
    
    def read_count(self, obj):
        """Show how many users have read this message."""
        return obj.read_by.count()
    
    read_count.short_description = 'Read By Count'
