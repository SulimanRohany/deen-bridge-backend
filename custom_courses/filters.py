import django_filters
from .models import CustomCourseRequest


class CustomCourseRequestFilter(django_filters.FilterSet):
    """Filter for custom course requests"""
    
    # Search across name, email, and phone
    search = django_filters.CharFilter(method='filter_by_search', label='Search')
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=CustomCourseRequest.STATUS_CHOICES)
    
    # Course type filter
    course_type = django_filters.ChoiceFilter(
        field_name='courseType',
        choices=CustomCourseRequest.COURSE_TYPE_CHOICES
    )
    
    # Date filters
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created Before'
    )
    
    class Meta:
        model = CustomCourseRequest
        fields = ['status', 'course_type', 'search']
    
    def filter_by_search(self, queryset, name, value):
        """Search across name, email, and phone"""
        if value:
            return queryset.filter(
                django_filters.Q(name__icontains=value) |
                django_filters.Q(email__icontains=value) |
                django_filters.Q(phone__icontains=value)
            )
        return queryset

