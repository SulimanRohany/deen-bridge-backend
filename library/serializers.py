from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import (
    LibraryCategory, LibraryResource, ResourceRating, 
    ResourceBookmark, ResourceView
)
from subjects.serializers import SubjectSerializer
from accounts.models import CustomUser


class LibraryCategorySerializer(serializers.ModelSerializer):
    """Serializer for library categories"""
    subcategories = serializers.SerializerMethodField()
    resource_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = LibraryCategory
        fields = [
            'id', 'name', 'name_arabic', 'description', 'icon',
            'parent', 'display_order', 'subcategories', 'resource_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_subcategories(self, obj):
        """Get subcategories recursively"""
        if obj.subcategories.exists():
            return LibraryCategorySerializer(obj.subcategories.all(), many=True).data
        return []


class SimpleCategorySerializer(serializers.ModelSerializer):
    """Simple category serializer without nested data"""
    class Meta:
        model = LibraryCategory
        fields = ['id', 'name', 'name_arabic', 'icon']


class ResourceRatingSerializer(serializers.ModelSerializer):
    """Serializer for resource ratings"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceRating
        fields = [
            'id', 'resource', 'student', 'student_name', 'student_email',
            'rating', 'review', 'can_edit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        """Check if current user can edit this rating"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.student == request.user or request.user.role == 'super_admin'
        return False
    
    def validate(self, data):
        """Validate that user hasn't already reviewed this resource"""
        request = self.context.get('request')
        resource = data.get('resource')
        
        # Only check on creation (not on update)
        if not self.instance and request and resource:
            # Check if user already has a review for this resource
            existing_review = ResourceRating.objects.filter(
                resource=resource,
                student=request.user
            ).first()
            
            if existing_review:
                raise serializers.ValidationError({
                    'detail': 'You have already reviewed this resource. Please edit your existing review instead.',
                    'existing_review_id': existing_review.id
                })
        
        return data
    
    def create(self, validated_data):
        """Auto-assign student from request"""
        request = self.context.get('request')
        validated_data['student'] = request.user
        return super().create(validated_data)


class LibraryResourceListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for library resource list view"""
    category_details = SimpleCategorySerializer(source='category', read_only=True)
    tags = TagListSerializerField(required=False)
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    pdf_file_url = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    
    # Explicitly declare file fields (read-only for list view)
    cover_image = serializers.ImageField(read_only=True)
    pdf_file = serializers.FileField(read_only=True)
    
    class Meta:
        model = LibraryResource
        fields = [
            'id', 'title', 'title_arabic', 'author', 'author_arabic',
            'category', 'category_details',
            'language', 'description', 'cover_image', 'cover_image_url',
            'pdf_file', 'pdf_file_url',
            'average_rating', 'total_ratings', 'view_count', 'download_count',
            'is_featured', 'is_published', 'tags', 'is_bookmarked', 'user_rating',
            'publisher', 'publication_year', 'isbn', 'pages',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'average_rating', 'total_ratings', 'view_count', 'download_count',
            'created_at', 'updated_at'
        ]
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this resource"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ResourceBookmark.objects.filter(
                resource=obj, 
                user=request.user
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating for this resource"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = ResourceRating.objects.get(
                    resource=obj, 
                    student=request.user
                )
                return rating.rating
            except ResourceRating.DoesNotExist:
                return None
        return None
    
    def get_cover_image_url(self, obj):
        """Get full URL for cover image"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
        return None
    
    def get_pdf_file_url(self, obj):
        """Get full URL for PDF file"""
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
        return None


class LibraryResourceDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Detailed serializer for library resource"""
    category_details = SimpleCategorySerializer(source='category', read_only=True)
    subcategory_details = SimpleCategorySerializer(source='subcategories', many=True, read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    subject_ids = serializers.PrimaryKeyRelatedField(
        queryset=LibraryResource.subjects.field.model.objects.all(),
        source='subjects',
        many=True,
        write_only=True,
        required=False
    )
    subcategory_ids = serializers.PrimaryKeyRelatedField(
        queryset=LibraryCategory.objects.all(),
        source='subcategories',
        many=True,
        write_only=True,
        required=False
    )
    tags = TagListSerializerField(required=False)
    ratings = ResourceRatingSerializer(many=True, read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    user_review = serializers.SerializerMethodField()
    added_by_name = serializers.CharField(source='added_by.full_name', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    pdf_file_url = serializers.SerializerMethodField()
    rating_breakdown = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    
    # Explicitly declare file fields for upload handling
    cover_image = serializers.ImageField(required=False, allow_null=True, use_url=True)
    pdf_file = serializers.FileField(required=False, allow_null=True, use_url=True)
    
    class Meta:
        model = LibraryResource
        fields = [
            'id', 'title', 'title_arabic', 'author', 'author_arabic',
            'category', 'category_details', 'subcategories', 'subcategory_ids', 'subcategory_details',
            'subjects', 'subject_ids', 'language',
            'description', 'cover_image', 'cover_image_url',
            'pdf_file', 'pdf_file_url',
            'publisher', 'publication_year', 'isbn', 'pages',
            'average_rating', 'total_ratings', 'view_count', 'download_count',
            'is_featured', 'is_published', 'featured_order',
            'added_by', 'added_by_name', 'tags',
            'is_bookmarked', 'user_rating', 'user_review', 'ratings',
            'rating_breakdown', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'average_rating', 'total_ratings', 'view_count', 'download_count',
            'added_by', 'created_at', 'updated_at'
        ]
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this resource"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ResourceBookmark.objects.filter(
                resource=obj, 
                user=request.user
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = ResourceRating.objects.get(
                    resource=obj, 
                    student=request.user
                )
                return rating.rating
            except ResourceRating.DoesNotExist:
                return None
        return None
    
    def get_user_review(self, obj):
        """Get current user's review"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = ResourceRating.objects.get(
                    resource=obj, 
                    student=request.user
                )
                return {
                    'id': rating.id,
                    'rating': rating.rating,
                    'review': rating.review,
                    'created_at': rating.created_at,
                    'updated_at': rating.updated_at
                }
            except ResourceRating.DoesNotExist:
                return None
        return None
    
    def get_cover_image_url(self, obj):
        """Get full URL for cover image"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
        return None
    
    def get_pdf_file_url(self, obj):
        """Get full URL for PDF file"""
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
        return None
    
    def get_rating_breakdown(self, obj):
        """Get breakdown of ratings by star count"""
        ratings = obj.ratings.all()
        total = ratings.count()
        if total == 0:
            return {
                '5': {'count': 0, 'percentage': 0},
                '4': {'count': 0, 'percentage': 0},
                '3': {'count': 0, 'percentage': 0},
                '2': {'count': 0, 'percentage': 0},
                '1': {'count': 0, 'percentage': 0},
            }
        
        breakdown = {}
        for star in range(5, 0, -1):
            count = ratings.filter(rating=star).count()
            percentage = (count / total * 100) if total > 0 else 0
            breakdown[str(star)] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        return breakdown
    
    def validate_cover_image(self, value):
        """Validate cover image file"""
        if value:
            # Check file size (max 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError('Cover image must be less than 10MB.')
            # Check file type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError('File must be an image.')
        return value
    
    def validate_pdf_file(self, value):
        """Validate PDF file"""
        if value:
            # Check file size (max 100MB)
            if value.size > 100 * 1024 * 1024:
                raise serializers.ValidationError('PDF file must be less than 100MB.')
            # Check file type
            if value.content_type != 'application/pdf':
                raise serializers.ValidationError('File must be a PDF.')
        return value
    
    def create(self, validated_data):
        """Auto-assign added_by from request"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['added_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle file updates properly"""
        request = self.context.get('request')
        
        # Extract ManyToMany fields first
        subjects = validated_data.pop('subjects', None)
        subcategories = validated_data.pop('subcategories', None)
        
        # Handle file fields separately to ensure they're processed correctly
        # Only update files if they are explicitly provided
        
        # Handle cover image
        if 'cover_image' in validated_data:
            cover_image = validated_data.pop('cover_image')
            if cover_image is not None:
                # Delete old cover image if exists
                if instance.cover_image:
                    instance.cover_image.delete(save=False)
                instance.cover_image = cover_image
        
        # Check if cover image should be removed
        if request and request.data.get('remove_cover_image') == 'true':
            if instance.cover_image:
                instance.cover_image.delete(save=False)
                instance.cover_image = None
        
        # Handle PDF file
        if 'pdf_file' in validated_data:
            pdf_file = validated_data.pop('pdf_file')
            if pdf_file is not None:
                # Delete old PDF file if exists
                if instance.pdf_file:
                    instance.pdf_file.delete(save=False)
                instance.pdf_file = pdf_file
        
        # Check if PDF file should be removed
        if request and request.data.get('remove_pdf_file') == 'true':
            if instance.pdf_file:
                instance.pdf_file.delete(save=False)
                instance.pdf_file = None
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the instance
        instance.save()
        
        # Handle ManyToMany relationships using .set()
        if subjects is not None:
            instance.subjects.set(subjects)
        if subcategories is not None:
            instance.subcategories.set(subcategories)
        
        return instance


class ResourceBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for resource bookmarks"""
    resource_title = serializers.CharField(source='resource.title', read_only=True)
    resource_details = LibraryResourceListSerializer(source='resource', read_only=True)
    
    class Meta:
        model = ResourceBookmark
        fields = [
            'id', 'resource', 'resource_title', 'resource_details',
            'user', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        """Auto-assign user from request"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ResourceViewSerializer(serializers.ModelSerializer):
    """Serializer for resource views"""
    
    class Meta:
        model = ResourceView
        fields = ['id', 'resource', 'user', 'ip_address', 'viewed_at']
        read_only_fields = ['user', 'viewed_at']
