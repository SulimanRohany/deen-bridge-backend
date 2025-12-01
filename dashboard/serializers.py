from rest_framework import serializers
from django.utils import timezone
from django.db.models import Count, Q, Avg
from datetime import timedelta

from accounts.models import CustomUser
from accounts.serializers import UserWithProfileSerializer
from course.models import Class, LiveSession, Attendance, Certificate
from course.serializers import ClassSerializer, LiveSessionSerializer
from enrollments.models import ClassEnrollment, EnrollmentChoices
from enrollments.serializers import ClassEnrollmentSerializer
from profiles.models import StudentProfile


class ChildSummarySerializer(serializers.Serializer):
    """Summary information about a child"""
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    profile_image = serializers.SerializerMethodField()
    relationship = serializers.CharField()
    
    def get_profile_image(self, obj):
        """Get profile image URL"""
        if hasattr(obj, 'studentprofile_profile') and obj.studentprofile_profile.profile_image:
            return obj.studentprofile_profile.profile_image.url
        return None


class ChildEnrollmentSerializer(serializers.Serializer):
    """Enrollment information for a child"""
    enrollment_id = serializers.IntegerField(source='id')
    class_id = serializers.IntegerField(source='class_enrolled.id')
    class_title = serializers.CharField(source='class_enrolled.title')
    class_description = serializers.CharField(source='class_enrolled.description', allow_null=True)
    status = serializers.CharField()
    enrolled_at = serializers.DateTimeField(allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    created_at = serializers.DateTimeField()
    
    # Additional class info
    class_teachers = serializers.SerializerMethodField()
    class_start_time = serializers.TimeField(source='class_enrolled.start_time')
    class_end_time = serializers.TimeField(source='class_enrolled.end_time')
    class_days = serializers.SerializerMethodField()
    
    def get_class_teachers(self, obj):
        """Get list of teacher names"""
        teachers = obj.class_enrolled.teacher.all()
        return [{'id': t.id, 'full_name': t.full_name, 'email': t.email} for t in teachers]
    
    def get_class_days(self, obj):
        """Get formatted days of week"""
        return obj.class_enrolled.get_days_display()


class ChildAttendanceSerializer(serializers.Serializer):
    """Attendance information for a child"""
    attendance_id = serializers.IntegerField(source='id')
    session_id = serializers.IntegerField(source='session.id')
    session_title = serializers.CharField(source='session.title')
    session_date = serializers.DateField(source='session.scheduled_date', allow_null=True)
    class_id = serializers.IntegerField(source='session.class_session.id')
    class_title = serializers.CharField(source='session.class_session.title')
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    
    # Attendance statistics
    attendance_rate = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()
    attended_sessions = serializers.SerializerMethodField()
    
    def get_attendance_rate(self, obj):
        """Calculate attendance rate for the class"""
        enrollment = obj.class_enrollment
        total = Attendance.objects.filter(
            class_enrollment__class_enrolled=enrollment.class_enrolled,
            class_enrollment__student=enrollment.student
        ).count()
        present = Attendance.objects.filter(
            class_enrollment__class_enrolled=enrollment.class_enrolled,
            class_enrollment__student=enrollment.student,
            status='present'
        ).count()
        return round((present / total * 100), 2) if total > 0 else 0.0
    
    def get_total_sessions(self, obj):
        """Get total sessions for the class"""
        enrollment = obj.class_enrollment
        return LiveSession.objects.filter(
            class_session=enrollment.class_enrolled
        ).count()
    
    def get_attended_sessions(self, obj):
        """Get attended sessions count"""
        enrollment = obj.class_enrollment
        return Attendance.objects.filter(
            class_enrollment__class_enrolled=enrollment.class_enrolled,
            class_enrollment__student=enrollment.student,
            status='present'
        ).count()


class ChildSessionSerializer(serializers.Serializer):
    """Session information for a child"""
    session_id = serializers.IntegerField(source='id')
    title = serializers.CharField()
    scheduled_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    class_id = serializers.IntegerField(source='class_session.id')
    class_title = serializers.CharField(source='class_session.title')
    class_start_time = serializers.TimeField(source='class_session.start_time')
    class_end_time = serializers.TimeField(source='class_session.end_time')
    recording_available = serializers.BooleanField()
    recording_url = serializers.URLField(allow_null=True, allow_blank=True)
    created_at = serializers.DateTimeField()
    
    # Attendance status for this session
    attendance_status = serializers.SerializerMethodField()
    
    def get_attendance_status(self, obj):
        """Get attendance status for this session"""
        # This would need the student context - we'll handle this in the view
        return None


class ChildCertificateSerializer(serializers.Serializer):
    """Certificate information for a child"""
    certificate_id = serializers.IntegerField(source='id')
    class_id = serializers.IntegerField(source='class_completed.id')
    class_title = serializers.CharField(source='class_completed.title')
    certificate_code = serializers.CharField()
    pdf_url = serializers.URLField(allow_null=True, allow_blank=True)
    issued_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()


class ChildProgressSerializer(serializers.Serializer):
    """Progress summary for a child"""
    total_enrollments = serializers.IntegerField()
    active_enrollments = serializers.IntegerField()
    completed_enrollments = serializers.IntegerField()
    total_certificates = serializers.IntegerField()
    overall_attendance_rate = serializers.FloatField()
    total_sessions_attended = serializers.IntegerField()
    total_sessions = serializers.IntegerField()


class ChildDetailSerializer(serializers.Serializer):
    """Comprehensive child detail information"""
    child = ChildSummarySerializer()
    enrollments = ChildEnrollmentSerializer(many=True)
    attendance = ChildAttendanceSerializer(many=True)
    upcoming_sessions = ChildSessionSerializer(many=True)
    past_sessions = ChildSessionSerializer(many=True)
    certificates = ChildCertificateSerializer(many=True)
    progress = ChildProgressSerializer()


class ParentDashboardSerializer(serializers.Serializer):
    """Main parent dashboard data"""
    children = ChildSummarySerializer(many=True)
    total_children = serializers.IntegerField()
    
    # Overview statistics
    total_enrollments = serializers.IntegerField()
    total_certificates = serializers.IntegerField()
    average_attendance_rate = serializers.FloatField()
    upcoming_sessions_count = serializers.IntegerField()
    
    # Per-child summaries
    children_summaries = serializers.SerializerMethodField()
    
    def get_children_summaries(self, obj):
        """Get summary for each child"""
        summaries = []
        for child_data in obj.get('children_data', []):
            summaries.append({
                'child': ChildSummarySerializer(child_data['child']).data,
                'enrollments_count': child_data.get('enrollments_count', 0),
                'attendance_rate': child_data.get('attendance_rate', 0.0),
                'upcoming_sessions_count': child_data.get('upcoming_sessions_count', 0),
                'certificates_count': child_data.get('certificates_count', 0),
            })
        return summaries


