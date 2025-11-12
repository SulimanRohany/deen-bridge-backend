from django.db.models import JSONField, Q
import django_filters
from .models import Class, LiveSession, Recording, Attendance, Certificate, LiveSessionResource



class ClassFilter(django_filters.FilterSet):
    # Custom filters for better search and filtering
    teacher = django_filters.NumberFilter(field_name='teacher__id')
    subject = django_filters.NumberFilter(field_name='subject__id')
    is_special_class = django_filters.BooleanFilter(field_name='is_special_class')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = Class
        fields = {
            'id': ['exact'],
            'title': ['icontains'],
            'description': ['icontains'],
            'days_of_week': ['exact', 'icontains'],
            'start_time': ['exact', 'hour__gt', 'hour__lt'],
            'end_time': ['exact', 'hour__gt', 'hour__lt'],
            'timezone': ['exact'],
            'created_at': ['exact', 'year__gt', 'year__lt'],
            'updated_at': ['exact', 'year__gt', 'year__lt'],
        }
        filter_overrides = {
            JSONField: {
                'filter_class': django_filters.CharFilter,
            },
        }


# Legacy alias for backward compatibility
CourseFilter = ClassFilter


# LiveSession filtering
# class LiveSessionFilter(django_filters.FilterSet):
#     class Meta:
#         model = LiveSession
#         fields = {
#             'id': ['exact'],
#             'title': ['icontains'],
#             'timetable': ['exact'],
#             'meeting_provider': ['exact'],
#             'meeting_id': ['icontains'],
#             'status': ['iexact'],
#             'created_at': ['iexact', 'year__gt', 'year__lt'],
#             'updated_at': ['iexact', 'year__gt', 'year__lt'],
#         }


class LiveSessionFilter(django_filters.FilterSet):
    # Map ?class=<id> to class_session__id (also support ?course for backward compatibility)
    class_id = django_filters.NumberFilter(field_name="class_session__id")
    course = django_filters.NumberFilter(field_name="class_session__id")  # Legacy support
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    ordering = django_filters.OrderingFilter(fields=(('created_at', 'created_at'),))

    class Meta:
        model = LiveSession
        fields = ['class_id', 'course', 'title', 'status']




# # Recording filtering
# class RecordingFilter(django_filters.FilterSet):
#     class Meta:
#         model = Recording
#         fields = {
#             'id': ['exact'],
#             'session': ['exact'],
#             'title': ['icontains'],
#             'video_url': ['icontains'],
#             'created_at': ['exact', 'year__gt', 'year__lt'],
#             'updated_at': ['exact', 'year__gt', 'year__lt'],
#         }



# # Attendance filtering
# class AttendanceFilter(django_filters.FilterSet):
#     class Meta:
#         model = Attendance
#         fields = {
#             'id': ['exact'],
#             'course_enrollment': ['exact'],
#             'session': ['exact'],
#             'status': ['iexact'],
#             'joined_at': ['exact', 'year__gt', 'year__lt'],
#             'left_at': ['exact', 'year__gt', 'year__lt'],
#             'created_at': ['exact', 'year__gt', 'year__lt'],
#             'updated_at': ['exact', 'year__gt', 'year__lt'],
#         }


class AttendanceFilter(django_filters.FilterSet):
    class_id = django_filters.NumberFilter(field_name="class_enrollment__class_enrolled__id")
    course = django_filters.NumberFilter(field_name="class_enrollment__class_enrolled__id")  # Legacy support
    student = django_filters.NumberFilter(field_name="class_enrollment__student__id")
    session = django_filters.NumberFilter(field_name="session__id")
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    ordering = django_filters.OrderingFilter(fields=(('created_at','created_at'),))
    
    # Add search filter for student name and email
    search = django_filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        """Filter by student name, email, session title, or class title"""
        if not value:
            return queryset
        return queryset.filter(
            Q(class_enrollment__student__full_name__icontains=value) |
            Q(class_enrollment__student__email__icontains=value) |
            Q(session__title__icontains=value) |
            Q(class_enrollment__class_enrolled__title__icontains=value)
        )

    class Meta:
        model = Attendance
        fields = ['class_id', 'course', 'student', 'session', 'status', 'search']

class RecordingFilter(django_filters.FilterSet):
    # Filter recordings by class id via session -> class_session
    class_id = django_filters.NumberFilter(field_name="session__class_session__id")
    course = django_filters.NumberFilter(field_name="session__class_session__id")  # Legacy support
    # Simple search by title
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    ordering = django_filters.OrderingFilter(fields=(('created_at','created_at'),))

    class Meta:
        model = Recording
        fields = ['class_id', 'course', 'title']




# Certificate filtering
class CertificateFilter(django_filters.FilterSet):
    class Meta:
        model = Certificate
        fields = {
            'id': ['exact'],
            'student': ['exact'],
            'class_completed': ['exact'],
            'certificate_code': ['icontains', 'exact'],
            'issued_at': ['exact', 'year__gt', 'year__lt'],
            'created_at': ['exact', 'year__gt', 'year__lt'],
            'updated_at': ['exact', 'year__gt', 'year__lt'],
        }


# LiveSessionResource filtering
class LiveSessionResourceFilter(django_filters.FilterSet):
    session = django_filters.NumberFilter(field_name="session__id")
    class_id = django_filters.NumberFilter(field_name="session__class_session__id")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    file_type = django_filters.CharFilter(field_name="file_type", lookup_expr="exact")
    uploaded_by = django_filters.NumberFilter(field_name="uploaded_by__id")
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    ordering = django_filters.OrderingFilter(fields=(('created_at', 'created_at'), ('title', 'title')))
    
    search = django_filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        """Search by title, description, session title"""
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(session__title__icontains=value)
        )
    
    class Meta:
        model = LiveSessionResource
        fields = ['session', 'class_id', 'title', 'file_type', 'uploaded_by', 'search']

