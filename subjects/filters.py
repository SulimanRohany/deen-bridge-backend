import django_filters
from .models import Subject

class CourseFilter(django_filters.FilterSet):
    """Deprecated: Use SubjectFilter instead. Kept for backwards compatibility."""
    class Meta:
        model = Subject
        fields = {
            'name': ['exact', 'icontains'],
            'description': ['icontains'],
            'created_at': ['exact', 'year__gt', 'year__lt'],
            'updated_at': ['exact', 'year__gt', 'year__lt'],
        }

class SubjectFilter(django_filters.FilterSet):
    """Filter for Subject model"""
    class Meta:
        model = Subject
        fields = {
            'name': ['exact', 'icontains'],
            'description': ['icontains'],
            'created_at': ['exact', 'year__gt', 'year__lt'],
            'updated_at': ['exact', 'year__gt', 'year__lt'],
        }