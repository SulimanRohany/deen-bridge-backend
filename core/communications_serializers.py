"""Serializers for the unified UserCommunication model"""
from rest_framework import serializers
from .models import UserCommunication
from accounts.serializers import UserWithProfileSerializer


class UserCommunicationSerializer(serializers.ModelSerializer):
    """Base serializer for UserCommunication with all fields"""
    user_details = UserWithProfileSerializer(source='user', read_only=True)
    communication_type_display = serializers.CharField(source='get_communication_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    response_time = serializers.FloatField(read_only=True)
    
    # Display fields for custom course requests
    course_type_display = serializers.CharField(source='get_course_type_display', read_only=True)
    preferred_schedule_display = serializers.CharField(source='get_preferred_schedule_display', read_only=True)
    
    # Display field for reports
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = UserCommunication
        fields = [
            'id',
            'communication_type',
            'communication_type_display',
            'user',
            'user_details',
            'name',
            'email',
            'phone',
            'message',
            'status',
            'status_display',
            'admin_notes',
            'response_sent_at',
            'response_time',
            'ip_address',
            'user_agent',
            # Contact message fields
            'subject',
            # Custom course request fields
            'course_type',
            'course_type_display',
            'number_of_students',
            'preferred_schedule',
            'preferred_schedule_display',
            'subjects',
            # Report fields
            'report_type',
            'report_type_display',
            'title',
            'screen_shot',
            'is_resolved',
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'response_time', 'user_details']


class CustomCourseRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating custom course requests"""
    
    class Meta:
        model = UserCommunication
        fields = [
            'name',
            'email',
            'phone',
            'course_type',
            'number_of_students',
            'preferred_schedule',
            'subjects',
            'message',
        ]
    
    def validate(self, attrs):
        """Ensure required fields for custom course requests are present"""
        if not attrs.get('course_type'):
            raise serializers.ValidationError({'course_type': 'This field is required for custom course requests.'})
        return attrs
    
    def create(self, validated_data):
        """Create a custom course request"""
        validated_data['communication_type'] = 'custom_request'
        validated_data['status'] = 'pending'
        
        # Add user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        return super().create(validated_data)


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating contact messages"""
    
    class Meta:
        model = UserCommunication
        fields = [
            'name',
            'email',
            'phone',
            'subject',
            'message',
        ]
    
    def validate(self, attrs):
        """Ensure required fields for contact messages are present"""
        if not attrs.get('subject'):
            raise serializers.ValidationError({'subject': 'This field is required for contact messages.'})
        return attrs
    
    def create(self, validated_data):
        """Create a contact message"""
        validated_data['communication_type'] = 'contact_message'
        validated_data['status'] = 'new'
        
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


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for creating reports"""
    user_details = UserWithProfileSerializer(source='user', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = UserCommunication
        fields = [
            'id',
            'user',
            'user_details',
            'report_type',
            'report_type_display',
            'title',
            'message',
            'screen_shot',
            'is_resolved',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'user_details', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Ensure required fields for reports are present"""
        if not attrs.get('report_type'):
            raise serializers.ValidationError({'report_type': 'This field is required for reports.'})
        if not attrs.get('title'):
            raise serializers.ValidationError({'title': 'This field is required for reports.'})
        if not attrs.get('message'):
            raise serializers.ValidationError({'message': 'This field is required for reports.'})
        return attrs
    
    def create(self, validated_data):
        """Create a report"""
        validated_data['communication_type'] = 'report'
        validated_data['status'] = 'pending'
        
        # Add user from request (required for reports)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            user = request.user
            
            # CustomUser model uses 'full_name' instead of first_name/last_name
            validated_data['name'] = getattr(user, 'full_name', None) or getattr(user, 'email', 'Unknown User')
            validated_data['email'] = getattr(user, 'email', 'noemail@example.com')
        else:
            raise serializers.ValidationError('User must be authenticated to submit a report')
        
        return super().create(validated_data)


class UserCommunicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to user communications"""
    
    class Meta:
        model = UserCommunication
        fields = [
            'status',
            'admin_notes',
            'response_sent_at',
            'is_resolved',
        ]
    
    def validate_status(self, value):
        """Ensure status is valid for the communication type"""
        communication_type = self.instance.communication_type
        
        # Define valid statuses for each type
        valid_statuses = {
            'custom_request': ['pending', 'reviewed', 'contacted', 'approved', 'rejected', 'completed'],
            'contact_message': ['new', 'read', 'replied', 'closed'],
            'report': ['pending', 'reviewed', 'resolved', 'closed'],
        }
        
        if value not in valid_statuses.get(communication_type, []):
            raise serializers.ValidationError(
                f"'{value}' is not a valid status for {communication_type}. "
                f"Valid statuses are: {', '.join(valid_statuses[communication_type])}"
            )
        
        return value


class UserCommunicationListSerializer(serializers.ModelSerializer):
    """Serializer for listing user communications with all necessary fields"""
    user_details = UserWithProfileSerializer(source='user', read_only=True)
    communication_type_display = serializers.CharField(source='get_communication_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    response_time = serializers.FloatField(read_only=True)
    
    # Display fields for custom course requests
    course_type_display = serializers.CharField(source='get_course_type_display', read_only=True)
    preferred_schedule_display = serializers.CharField(source='get_preferred_schedule_display', read_only=True)
    
    # Display field for reports
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = UserCommunication
        fields = [
            'id',
            'communication_type',
            'communication_type_display',
            'user',
            'user_details',
            'name',
            'email',
            'phone',
            'message',
            'status',
            'status_display',
            'admin_notes',
            'response_sent_at',
            'response_time',
            'ip_address',
            'user_agent',
            # Contact message fields
            'subject',
            # Custom course request fields
            'course_type',
            'course_type_display',
            'number_of_students',
            'preferred_schedule',
            'preferred_schedule_display',
            'subjects',
            # Report fields
            'report_type',
            'report_type_display',
            'title',
            'screen_shot',
            'is_resolved',
            # Timestamps
            'created_at',
            'updated_at',
        ]

