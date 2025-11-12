from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager


class LibraryCategory(models.Model):
    """Categories for library resources (e.g., Tafsir, Hadith, Fiqh, Seerah, etc.)"""
    name = models.CharField(max_length=255, unique=True)
    name_arabic = models.CharField(max_length=255, blank=True, help_text="Arabic name of the category")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Tabler icon name (e.g., 'IconBook')")
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='subcategories'
    )
    display_order = models.IntegerField(default=0, help_text="Order in which to display categories")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('display_order', 'name')
        verbose_name = 'Library Category'
        verbose_name_plural = 'Library Categories'

    def __str__(self):
        return self.name
    
    @property
    def resource_count(self):
        """Count of resources in this category"""
        return self.resources.filter(is_published=True).count()


class ResourceType(models.TextChoices):
    """Types of resources available in the library"""
    BOOK = 'book', 'Book'


class Language(models.TextChoices):
    """Languages available for resources"""
    ARABIC = 'arabic', 'Arabic'
    ENGLISH = 'english', 'English'
    URDU = 'urdu', 'Urdu'
    FARSI = 'farsi', 'Farsi'
    PASHTO = 'pashto', 'Pashto'
    TURKISH = 'turkish', 'Turkish'


class LibraryResource(models.Model):
    """Main model for library resources"""
    
    # Basic Information
    title = models.CharField(max_length=500)
    title_arabic = models.CharField(max_length=500, blank=True, help_text="Arabic title")
    author = models.CharField(max_length=255)
    author_arabic = models.CharField(max_length=255, blank=True, help_text="Arabic author name")
    
    # Categories
    category = models.ForeignKey(
        'LibraryCategory',
        on_delete=models.SET_NULL,
        null=True,
        related_name='resources',
        help_text="Primary category"
    )
    subcategories = models.ManyToManyField(
        'LibraryCategory',
        blank=True,
        related_name='subcategory_resources',
        help_text="Additional subcategories"
    )
    
    # Subjects
    subjects = models.ManyToManyField(
        'subjects.Subject', 
        blank=True, 
        related_name='library_resources',
        help_text="Related subjects from the platform"
    )
    
    # Content Details
    resource_type = models.CharField(
        max_length=20, 
        choices=ResourceType.choices, 
        default=ResourceType.BOOK
    )
    language = models.CharField(
        max_length=20, 
        choices=Language.choices, 
        default=Language.ARABIC
    )
    description = models.TextField(blank=True)
    
    # Files
    cover_image = models.ImageField(
        upload_to='library/covers/%Y/%m/', 
        blank=True, 
        null=True,
        help_text="Cover image for the book"
    )
    pdf_file = models.FileField(
        upload_to='library/pdfs/%Y/%m/', 
        blank=True, 
        null=True,
        help_text="PDF file for the book"
    )
    
    # Metadata
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(2100)]
    )
    isbn = models.CharField(max_length=20, blank=True, help_text="ISBN number")
    pages = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)]
    )
    
    # Ratings & Statistics
    total_ratings = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    # Status & Publishing
    is_featured = models.BooleanField(default=False, help_text="Show in featured section")
    is_published = models.BooleanField(default=True, help_text="Make visible to users")
    featured_order = models.IntegerField(default=0, help_text="Order in featured section")
    
    # Relationships
    added_by = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='added_resources',
        help_text="User who added this resource"
    )
    
    # Tags
    tags = TaggableManager(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Library Resource'
        verbose_name_plural = 'Library Resources'
        indexes = [
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['is_featured', 'featured_order']),
            models.Index(fields=['-average_rating']),
            models.Index(fields=['-view_count']),
        ]

    def __str__(self):
        return self.title
    
    def clean(self):
        """Validate the book data"""
        # Validate cover image
        if self.cover_image:
            if self.cover_image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError({'cover_image': 'Cover image must be less than 5MB.'})
        
        # Validate PDF file
        if self.pdf_file:
            if self.pdf_file.size > 50 * 1024 * 1024:  # 50MB
                raise ValidationError({'pdf_file': 'PDF file must be less than 50MB.'})
        
        # Note: PDF file validation removed to allow saving books during creation
        # Admins can add the PDF file after initial creation if needed
        # The download feature checks for pdf_file existence before allowing downloads
    
    def increment_view_count(self):
        """Increment the view count"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])
        self.refresh_from_db()
    
    def increment_download_count(self):
        """Increment the download count"""
        self.download_count = models.F('download_count') + 1
        self.save(update_fields=['download_count'])
        self.refresh_from_db()
    
    def update_rating(self):
        """Recalculate average rating and total ratings"""
        ratings = self.ratings.all()
        self.total_ratings = ratings.count()
        if self.total_ratings > 0:
            self.average_rating = sum(r.rating for r in ratings) / self.total_ratings
        else:
            self.average_rating = 0.00
        self.save(update_fields=['total_ratings', 'average_rating'])


class ResourceRating(models.Model):
    """Student ratings and reviews for resources"""
    resource = models.ForeignKey(
        LibraryResource, 
        on_delete=models.CASCADE, 
        related_name='ratings'
    )
    student = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'student'}, 
        related_name='resource_ratings'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    review = models.TextField(blank=True, help_text="Optional review text")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('resource', 'student')
        ordering = ('-created_at',)
        verbose_name = 'Resource Rating'
        verbose_name_plural = 'Resource Ratings'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.resource.title} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        """Update resource rating when saving"""
        super().save(*args, **kwargs)
        self.resource.update_rating()
    
    def delete(self, *args, **kwargs):
        """Update resource rating when deleting"""
        resource = self.resource
        super().delete(*args, **kwargs)
        resource.update_rating()


class ResourceBookmark(models.Model):
    """User bookmarks for easy access to resources"""
    resource = models.ForeignKey(
        LibraryResource, 
        on_delete=models.CASCADE, 
        related_name='bookmarks'
    )
    user = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.CASCADE, 
        related_name='bookmarked_resources'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('resource', 'user')
        ordering = ('-created_at',)
        verbose_name = 'Resource Bookmark'
        verbose_name_plural = 'Resource Bookmarks'
    
    def __str__(self):
        return f"{self.user.full_name} bookmarked {self.resource.title}"


class ResourceView(models.Model):
    """Track resource views for analytics"""
    resource = models.ForeignKey(
        LibraryResource, 
        on_delete=models.CASCADE, 
        related_name='views'
    )
    user = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-viewed_at',)
        verbose_name = 'Resource View'
        verbose_name_plural = 'Resource Views'
        indexes = [
            models.Index(fields=['resource', '-viewed_at']),
        ]
    
    def __str__(self):
        user_info = self.user.full_name if self.user else self.ip_address
        return f"{user_info} viewed {self.resource.title}"

