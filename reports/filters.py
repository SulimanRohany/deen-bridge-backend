import django_filters
from .models import Report

class ReportFilter(django_filters.FilterSet):
    user = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    report_type = django_filters.ChoiceFilter(choices=Report.REPORT_TYPES)
    is_resolved = django_filters.BooleanFilter()

    class Meta:
        model = Report
        fields = ['user', 'report_type', 'is_resolved', 'created_at']