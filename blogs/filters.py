import django_filters
from .models import Post


class PostFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method='filter_by_tag')
    search = django_filters.CharFilter(method='filter_by_search')
    status = django_filters.ChoiceFilter(choices=Post._meta.get_field('status').choices)
    
    class Meta:
        model = Post
        fields = ['status', 'tag', 'search']
    
    def filter_by_tag(self, queryset, name, value):
        if value:
            return queryset.filter(tags__name__icontains=value)
        return queryset
    
    def filter_by_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                django_filters.Q(title__icontains=value) |
                django_filters.Q(body__icontains=value)
            )
        return queryset
