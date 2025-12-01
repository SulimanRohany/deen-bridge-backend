from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    LibraryCategory, LibraryResource, ResourceRating,
    ResourceBookmark, ResourceView
)


class HasPDFFilter(admin.SimpleListFilter):
    """Filter to show resources with or without PDF files"""
    title = 'PDF Status'
    parameter_name = 'has_pdf'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has PDF'),
            ('no', 'Missing PDF'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(pdf_file='')
        if self.value() == 'no':
            return queryset.filter(pdf_file='')
        return queryset


class HasCoverFilter(admin.SimpleListFilter):
    """Filter to show resources with or without cover images"""
    title = 'Cover Image Status'
    parameter_name = 'has_cover'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has Cover'),
            ('no', 'Missing Cover'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(cover_image='')
        if self.value() == 'no':
            return queryset.filter(cover_image='')
        return queryset


@admin.register(LibraryCategory)
class LibraryCategoryAdmin(admin.ModelAdmin):
    """Admin interface for library categories"""
    list_display = ['name', 'name_arabic', 'parent', 'display_order', 'resource_count', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'name_arabic', 'description']
    ordering = ['display_order', 'name']
    list_editable = ['display_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_arabic', 'description', 'icon')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'display_order')
        }),
    )
    
    def resource_count(self, obj):
        """Show count of resources in category"""
        count = obj.resources.filter(is_published=True).count()
        return format_html('<strong>{}</strong>', count)
    resource_count.short_description = 'Resources'


class ResourceRatingInline(admin.TabularInline):
    """Inline ratings for resources"""
    model = ResourceRating
    extra = 0
    readonly_fields = ['student', 'rating', 'created_at']
    can_delete = True


class LibraryResourceAdminForm(forms.ModelForm):
    """Custom form to ensure file uploads work properly"""
    # Override tags field with better help text and widget
    tags = forms.CharField(
        required=False,
        help_text='Enter tags separated by commas (e.g., "Islamic Studies, Tafsir, Quran"). Each tag will be saved separately.',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Tafsir, Hadith, Fiqh',
            'style': 'width: 100%;'
        })
    )
    
    class Meta:
        model = LibraryResource
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make PDF file optional (not required)
        if 'pdf_file' in self.fields:
            self.fields['pdf_file'].required = False
        # Add helpful text
        if 'pdf_file' in self.fields:
            self.fields['pdf_file'].help_text = 'Upload PDF file (max 100MB). Users can only download books that have PDF files.'
        if 'cover_image' in self.fields:
            self.fields['cover_image'].help_text = 'Upload cover image (max 10MB). Recommended size: 300x450px.'
    
    def clean_tags(self):
        """Clean and validate tags input"""
        tags_str = self.cleaned_data.get('tags', '')
        if not tags_str:
            return tags_str
        
        # Split by comma, strip whitespace, and filter empty strings
        tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        # Return as comma-separated string (taggit will handle the parsing)
        return ', '.join(tags_list)


@admin.register(LibraryResource)
class LibraryResourceAdmin(admin.ModelAdmin):
    """Admin interface for library resources"""
    form = LibraryResourceAdminForm  # Use custom form for file uploads
    
    list_display = [
        'title', 'author', 'category', 'language',
        'has_pdf', 'has_cover', 'rating_display', 
        'view_count', 'download_count',
        'is_featured', 'is_published', 'created_at'
    ]
    list_filter = [
        HasPDFFilter, HasCoverFilter,
        'language', 'category', 'is_featured',
        'is_published', 'created_at'
    ]
    search_fields = ['title', 'title_arabic', 'author', 'author_arabic', 'description']
    ordering = ['-created_at']
    list_editable = ['is_featured', 'is_published']
    
    filter_horizontal = ['subcategories', 'subjects']
    inlines = [ResourceRatingInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'title_arabic', 'author', 'author_arabic',
                'description', 'language'
            ),
            'description': 'Enter the basic book information'
        }),
        ('Files (Upload Book Content)', {
            'fields': ('pdf_file', 'cover_image'),
            'description': 'Upload the PDF file and cover image. PDF file is required for users to download the book.'
        }),
        ('Categorization', {
            'fields': ('category', 'subcategories', 'subjects', 'tags'),
            'description': 'Categorize the book for easy discovery'
        }),
        ('Metadata', {
            'fields': (
                'publisher', 'publication_year', 'isbn', 'pages'
            )
        }),
        ('Publishing', {
            'fields': (
                'is_published', 'is_featured', 'featured_order', 'added_by'
            )
        }),
        ('Statistics', {
            'fields': (
                'average_rating', 'total_ratings', 'view_count', 'download_count'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['average_rating', 'total_ratings', 'view_count', 'download_count', 'added_by']
    
    def save_model(self, request, obj, form, change):
        """Set added_by on creation and show warning if PDF is missing"""
        if not change:  # Only on creation
            obj.added_by = request.user
        
        # Save the model
        super().save_model(request, obj, form, change)
        
        # Show warning if PDF is missing
        if not obj.pdf_file:
            from django.contrib import messages
            messages.warning(
                request, 
                f'Warning: "{obj.title}" was saved without a PDF file. '
                'Users will not be able to download this book until you upload a PDF file.'
            )
    
    def has_pdf(self, obj):
        """Show if resource has PDF file"""
        if obj.pdf_file:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_pdf.short_description = 'PDF'
    has_pdf.admin_order_field = 'pdf_file'
    
    def has_cover(self, obj):
        """Show if resource has cover image"""
        if obj.cover_image:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">—</span>')
    has_cover.short_description = 'Cover'
    has_cover.admin_order_field = 'cover_image'
    
    def rating_display(self, obj):
        """Display rating with stars"""
        if obj.total_ratings > 0:
            stars = '★' * int(obj.average_rating)
            return format_html(
                '<span style="color: gold;">{}</span> ({:.1f}/5 - {} reviews)',
                stars, obj.average_rating, obj.total_ratings
            )
        return format_html('<span style="color: gray;">No ratings</span>')
    rating_display.short_description = 'Rating'
    
    actions = ['mark_as_featured', 'unmark_as_featured', 'publish', 'unpublish', 'check_missing_pdfs']
    
    def check_missing_pdfs(self, request, queryset):
        """Check for resources missing PDF files"""
        missing_pdfs = queryset.filter(pdf_file='')
        count = missing_pdfs.count()
        
        if count > 0:
            from django.contrib import messages
            book_list = ', '.join([f'"{book.title}"' for book in missing_pdfs[:5]])
            if count > 5:
                book_list += f' and {count - 5} more'
            messages.warning(
                request,
                f'{count} book(s) are missing PDF files: {book_list}. '
                'These books cannot be downloaded by users.'
            )
        else:
            from django.contrib import messages
            messages.success(request, 'All selected books have PDF files! ✓')
    check_missing_pdfs.short_description = 'Check for missing PDFs'
    
    def mark_as_featured(self, request, queryset):
        """Mark selected resources as featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} resource(s) marked as featured.')
    mark_as_featured.short_description = 'Mark as featured'
    
    def unmark_as_featured(self, request, queryset):
        """Unmark selected resources as featured"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} resource(s) unmarked as featured.')
    unmark_as_featured.short_description = 'Unmark as featured'
    
    def publish(self, request, queryset):
        """Publish selected resources"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} resource(s) published.')
    publish.short_description = 'Publish'
    
    def unpublish(self, request, queryset):
        """Unpublish selected resources"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} resource(s) unpublished.')
    unpublish.short_description = 'Unpublish'


@admin.register(ResourceRating)
class ResourceRatingAdmin(admin.ModelAdmin):
    """Admin interface for resource ratings"""
    list_display = ['resource', 'student', 'rating_stars', 'has_review', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['resource__title', 'student__full_name', 'student__email', 'review']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def rating_stars(self, obj):
        """Display rating as stars"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_stars.short_description = 'Rating'
    
    def has_review(self, obj):
        """Show if rating has review text"""
        return bool(obj.review)
    has_review.boolean = True
    has_review.short_description = 'Has Review'


@admin.register(ResourceBookmark)
class ResourceBookmarkAdmin(admin.ModelAdmin):
    """Admin interface for resource bookmarks"""
    list_display = ['user', 'resource', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__full_name', 'user__email', 'resource__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ResourceView)
class ResourceViewAdmin(admin.ModelAdmin):
    """Admin interface for resource views"""
    list_display = ['resource', 'user_display', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['resource__title', 'user__full_name', 'user__email', 'ip_address']
    ordering = ['-viewed_at']
    readonly_fields = ['viewed_at']
    
    def user_display(self, obj):
        """Display user or IP"""
        if obj.user:
            return obj.user.full_name
        return f'Anonymous ({obj.ip_address})'
    user_display.short_description = 'User'
