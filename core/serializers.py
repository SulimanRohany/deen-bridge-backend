from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for contact form messages"""
    
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
    
    def create(self, validated_data):
        # Add request information if available
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return super().create(validated_data)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ContactMessageListSerializer(serializers.ModelSerializer):
    """Serializer for listing contact messages (admin view)"""
    
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'status', 'created_at', 'ip_address']
        read_only_fields = ['id', 'created_at', 'ip_address']


class ContactMessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating contact message status (admin view)"""
    
    class Meta:
        model = ContactMessage
        fields = ['status']