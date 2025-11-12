import django_filters


from .models import CustomUser, RoleChoices


class CustomUserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr='icontains')
    full_name = django_filters.CharFilter(lookup_expr='icontains')
    role = django_filters.ChoiceFilter(choices=RoleChoices.choices)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'role']






class UserWithProfileFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(field_name='role', choices=RoleChoices.choices)
    
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    full_name = django_filters.CharFilter(field_name='full_name', lookup_expr='icontains')

    is_active = django_filters.BooleanFilter(field_name='is_active')

    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = CustomUser
        # fields here are optional; we keep explicit filters above
        fields = ['role', 'email', 'full_name', 'is_active', 'created_at_after', 'created_at_before']