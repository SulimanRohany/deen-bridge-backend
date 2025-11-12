from rest_framework import serializers
from .models import CustomCourseRequest


class CustomCourseRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    courseType_display = serializers.CharField(source='get_courseType_display', read_only=True)
    schedule_display = serializers.CharField(source='get_preferredSchedule_display', read_only=True)
    response_time = serializers.FloatField(read_only=True)

    class Meta:
        model = CustomCourseRequest
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'courseType',
            'courseType_display',
            'numberOfStudents',
            'preferredSchedule',
            'schedule_display',
            'subjects',
            'message',
            'status',
            'status_display',
            'admin_notes',
            'response_sent_at',
            'response_time',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'response_time']


class CustomCourseRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomCourseRequest
        fields = [
            'name',
            'email',
            'phone',
            'courseType',
            'numberOfStudents',
            'preferredSchedule',
            'subjects',
            'message',
        ]

    def create(self, validated_data):
        # You can add the current user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)

