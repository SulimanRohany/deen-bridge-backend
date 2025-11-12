import django_filters
from .models import ClassEnrollment

class ClassEnrollmentFilter(django_filters.FilterSet):
    class Meta:
        model = ClassEnrollment
        fields = {
            'student': ['exact'],
            'class_enrolled': ['exact'],
            'status': ['iexact'],
            'price': ['exact', 'gte', 'lte'],
            'enrolled_at': ['exact', 'year__gt', 'year__lt'],
            'created_at': ['exact', 'year__gt', 'year__lt'],
            'updated_at': ['exact', 'year__gt', 'year__lt'],
        }


# Legacy alias for backward compatibility
CourseEnrollmentFilter = ClassEnrollmentFilter