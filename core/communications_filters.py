"""Filters for the unified UserCommunication model"""
import django_filters
from .models import UserCommunication


class UserCommunicationFilter(django_filters.FilterSet):
    """Unified filter for all user communications"""
    
    # Communication type filter
    communication_type = django_filters.ChoiceFilter(
        choices=UserCommunication.COMMUNICATION_TYPE_CHOICES
    )
    
    # Status filter
    status = django_filters.ChoiceFilter(
        choices=UserCommunication.STATUS_CHOICES
    )
    
    # Search across name, email, and phone
    search = django_filters.CharFilter(
        method='filter_by_search',
        label='Search'
    )
    
    # Custom course request specific filters
    course_type = django_filters.ChoiceFilter(
        choices=UserCommunication.COURSE_TYPE_CHOICES
    )
    
    # Report specific filters
    report_type = django_filters.ChoiceFilter(
        choices=UserCommunication.REPORT_TYPE_CHOICES
    )
    is_resolved = django_filters.BooleanFilter()
    
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
    
    # User filter
    user = django_filters.CharFilter(
        field_name='user__username',
        lookup_expr='icontains'
    )
    user_id = django_filters.NumberFilter(
        field_name='user__id'
    )
    
    class Meta:
        model = UserCommunication
        fields = [
            'communication_type',
            'status',
            'search',
            'course_type',
            'report_type',
            'is_resolved',
            'user',
            'user_id',
        ]
    
    def filter_by_search(self, queryset, name, value):
        """Search across name, email, phone, subject, and title"""
        if value:
            return queryset.filter(
                django_filters.Q(name__icontains=value) |
                django_filters.Q(email__icontains=value) |
                django_filters.Q(phone__icontains=value) |
                django_filters.Q(subject__icontains=value) |
                django_filters.Q(title__icontains=value) |
                django_filters.Q(message__icontains=value)
            )
        return queryset

