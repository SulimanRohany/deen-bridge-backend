import django_filters
from django.db.models import Q
from .models import LibraryResource, LibraryCategory, ResourceRating, ResourceType, Language


class LibraryResourceFilter(django_filters.FilterSet):
    """Comprehensive filters for library resources"""
    
    # Search across multiple fields
    search = django_filters.CharFilter(method='filter_by_search', label='Search')
    
    # Category filters
    category = django_filters.NumberFilter(field_name='category__id', label='Category')
    category_name = django_filters.CharFilter(
        field_name='category__name', 
        lookup_expr='icontains',
        label='Category Name'
    )
    
    # Type and language filters
    resource_type = django_filters.ChoiceFilter(choices=ResourceType.choices, label='Resource Type')
    language = django_filters.MultipleChoiceFilter(choices=Language.choices, label='Language')
    
    # Subject filter
    subject = django_filters.NumberFilter(field_name='subjects__id', label='Subject')
    
    # Tag filter
    tag = django_filters.CharFilter(method='filter_by_tag', label='Tag')
    
    # Rating filters
    min_rating = django_filters.NumberFilter(
        field_name='average_rating', 
        lookup_expr='gte',
        label='Minimum Rating'
    )
    has_ratings = django_filters.BooleanFilter(
        method='filter_has_ratings',
        label='Has Ratings'
    )
    
    # Featured filter
    is_featured = django_filters.BooleanFilter(label='Featured')
    is_published = django_filters.BooleanFilter(label='Published')
    
    # Author filter
    author = django_filters.CharFilter(lookup_expr='icontains', label='Author')
    author_arabic = django_filters.CharFilter(lookup_expr='icontains', label='Author (Arabic)')
    
    # Title filter
    title = django_filters.CharFilter(lookup_expr='icontains', label='Title')
    
    # Year range
    year_from = django_filters.NumberFilter(
        field_name='publication_year', 
        lookup_expr='gte',
        label='Published From'
    )
    year_to = django_filters.NumberFilter(
        field_name='publication_year', 
        lookup_expr='lte',
        label='Published To'
    )
    
    # Publisher filter
    publisher = django_filters.CharFilter(lookup_expr='icontains', label='Publisher')
    
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
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
            ('average_rating', 'rating'),
            ('view_count', 'views'),
            ('download_count', 'downloads'),
            ('title', 'title'),
            ('author', 'author'),
            ('publication_year', 'year'),
        ),
        label='Order By'
    )
    
    class Meta:
        model = LibraryResource
        fields = [
            'search', 'category', 'resource_type', 'language',
            'subject', 'tag', 'min_rating', 'is_featured',
            'is_published', 'author', 'year_from', 'year_to'
        ]
    
    def filter_by_search(self, queryset, name, value):
        """Search across title, author, description"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(title_arabic__icontains=value) |
                Q(author__icontains=value) |
                Q(author_arabic__icontains=value) |
                Q(description__icontains=value) |
                Q(publisher__icontains=value)
            )
        return queryset
    
    def filter_by_tag(self, queryset, name, value):
        """Filter by tag name"""
        if value:
            return queryset.filter(tags__name__icontains=value).distinct()
        return queryset
    
    def filter_has_ratings(self, queryset, name, value):
        """Filter resources that have ratings"""
        if value:
            return queryset.filter(total_ratings__gt=0)
        return queryset


class LibraryCategoryFilter(django_filters.FilterSet):
    """Filters for library categories"""
    
    search = django_filters.CharFilter(method='filter_by_search', label='Search')
    parent = django_filters.NumberFilter(field_name='parent__id', label='Parent Category')
    has_parent = django_filters.BooleanFilter(method='filter_has_parent', label='Has Parent')
    
    ordering = django_filters.OrderingFilter(
        fields=(
            ('display_order', 'display_order'),
            ('name', 'name'),
            ('created_at', 'created_at'),
        ),
        label='Order By'
    )
    
    class Meta:
        model = LibraryCategory
        fields = ['search', 'parent', 'has_parent']
    
    def filter_by_search(self, queryset, name, value):
        """Search across name and description"""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_arabic__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset
    
    def filter_has_parent(self, queryset, name, value):
        """Filter by whether category has a parent"""
        if value:
            return queryset.filter(parent__isnull=False)
        else:
            return queryset.filter(parent__isnull=True)


class ResourceRatingFilter(django_filters.FilterSet):
    """Filters for resource ratings"""
    
    resource = django_filters.NumberFilter(field_name='resource__id', label='Resource')
    student = django_filters.NumberFilter(field_name='student__id', label='Student')
    rating = django_filters.NumberFilter(label='Rating')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte', label='Min Rating')
    has_review = django_filters.BooleanFilter(method='filter_has_review', label='Has Review')
    
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('rating', 'rating'),
        ),
        label='Order By'
    )
    
    class Meta:
        model = ResourceRating
        fields = ['resource', 'student', 'rating', 'min_rating', 'has_review']
    
    def filter_has_review(self, queryset, name, value):
        """Filter ratings that have review text"""
        if value:
            return queryset.exclude(review='')
        else:
            return queryset.filter(review='')

