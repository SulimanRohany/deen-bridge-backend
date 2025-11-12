from rest_framework import viewsets, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from .models import (
    LibraryCategory, LibraryResource, ResourceRating,
    ResourceBookmark, ResourceView
)
from .serializers import (
    LibraryCategorySerializer, LibraryResourceListSerializer,
    LibraryResourceDetailSerializer, ResourceRatingSerializer,
    ResourceBookmarkSerializer, ResourceViewSerializer
)
from .filters import LibraryResourceFilter, LibraryCategoryFilter, ResourceRatingFilter
from accounts.models import RoleChoices
from core.pagination import CustomPagination


class IsSuperAdmin(IsAuthenticated):
    """Permission class for super admin only"""
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view) and
            request.user.role == RoleChoices.SUPER_ADMIN
        )


class IsStudent(IsAuthenticated):
    """Permission class for students"""
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view) and
            request.user.role == RoleChoices.STUDENT
        )


class LibraryCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for library categories
    - Read-only for all users
    - CRUD for super admins
    """
    queryset = LibraryCategory.objects.all()
    serializer_class = LibraryCategorySerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = LibraryCategoryFilter
    search_fields = ['name', 'name_arabic', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']
    
    def get_permissions(self):
        """
        Allow read for anyone, write for super admins only
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsSuperAdmin()]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def root_categories(self, request):
        """Get only root categories (no parent)"""
        categories = self.queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def subcategories(self, request, pk=None):
        """Get subcategories of a specific category"""
        category = self.get_object()
        subcategories = category.subcategories.all()
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def resources(self, request, pk=None):
        """Get all resources in this category"""
        category = self.get_object()
        resources = LibraryResource.objects.filter(
            Q(category=category) | Q(subcategories=category),
            is_published=True
        ).distinct()
        
        # Apply pagination
        page = self.paginate_queryset(resources)
        if page is not None:
            serializer = LibraryResourceListSerializer(
                page, 
                many=True, 
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = LibraryResourceListSerializer(
            resources, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)


class LibraryResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for library resources
    - Read for all (published only for non-admins)
    - CUD for super admins
    """
    queryset = LibraryResource.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = LibraryResourceFilter
    search_fields = ['title', 'title_arabic', 'author', 'author_arabic', 'description']
    ordering_fields = ['created_at', 'updated_at', 'average_rating', 'view_count', 'download_count', 'title']
    ordering = ['-created_at']
    pagination_class = CustomPagination  # Enable pagination for library resources
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve/create/update, list serializer for list"""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return LibraryResourceDetailSerializer
        return LibraryResourceListSerializer
    
    def get_permissions(self):
        """
        Allow read for anyone, write for super admins only
        Download requires authentication
        """
        if self.action in ['list', 'retrieve', 'featured', 'recommended', 'popular', 'recent', 'top_rated', 'related']:
            return [AllowAny()]
        if self.action == 'download':
            return [IsAuthenticated()]
        return [IsSuperAdmin()]
    
    def get_queryset(self):
        """Filter by published status for non-admins"""
        queryset = super().get_queryset()
        
        # Super admins see everything
        if self.request.user.is_authenticated and self.request.user.role == RoleChoices.SUPER_ADMIN:
            return queryset
        
        # Others see only published
        return queryset.filter(is_published=True)
    
    def perform_create(self, serializer):
        """Set added_by on creation and handle file uploads"""
        serializer.save(added_by=self.request.user)
    
    def perform_update(self, serializer):
        """Handle file uploads during update"""
        serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        """Track view when retrieving a resource"""
        instance = self.get_object()
        
        # Track view
        ip_address = self.get_client_ip(request)
        ResourceView.objects.create(
            resource=instance,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address
        )
        
        # Increment view count
        instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        """
        Track download and return download URL.
        
        Authentication Required:
        - Only authenticated users can download books
        - Unauthenticated users will receive a 401 Unauthorized error
        """
        try:
            resource = self.get_object()
            
            # Double-check authentication (DRF should handle this, but being explicit)
            if not request.user.is_authenticated:
                return Response(
                    {
                        'error': 'Authentication required',
                        'detail': 'Please log in to download this resource.',
                        'requires_auth': True
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if PDF file exists
            if not resource.pdf_file:
                return Response(
                    {
                        'error': 'No PDF file available for this resource',
                        'detail': 'This book does not have a PDF file uploaded yet.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if file exists on disk
            if not resource.pdf_file.storage.exists(resource.pdf_file.name):
                return Response(
                    {
                        'error': 'PDF file not found',
                        'detail': 'The PDF file is no longer available on the server.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Increment download count
            resource.increment_download_count()
            
            # Return PDF file URL
            pdf_url = request.build_absolute_uri(resource.pdf_file.url)
            
            return Response({
                'success': True,
                'message': 'Download tracked successfully',
                'pdf_url': pdf_url,
                'filename': resource.pdf_file.name.split('/')[-1],
                'size': resource.pdf_file.size,
                'resource_title': resource.title
            })
            
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to process download',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        """Get featured resources"""
        resources = self.get_queryset().filter(
            is_featured=True
        ).order_by('featured_order', '-created_at')[:12]
        
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def popular(self, request):
        """Get most popular resources by view count"""
        resources = self.get_queryset().order_by('-view_count', '-download_count')[:20]
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def recent(self, request):
        """Get recently added resources"""
        resources = self.get_queryset().order_by('-created_at')[:20]
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def top_rated(self, request):
        """Get top rated resources"""
        resources = self.get_queryset().filter(
            total_ratings__gte=3  # At least 3 ratings
        ).order_by('-average_rating', '-total_ratings')[:20]
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        """Get recommended resources based on user's subjects and activity"""
        user = request.user
        
        # Get user's enrolled subjects
        from enrollments.models import CourseEnrollment, EnrollmentChoices
        enrollments = CourseEnrollment.objects.filter(
            student=user,
            status=EnrollmentChoices.COMPLETED
        )
        
        subject_ids = []
        for enrollment in enrollments:
            course_subjects = enrollment.timetable.course.subject.all()
            subject_ids.extend([s.id for s in course_subjects])
        
        # Get resources related to these subjects
        if subject_ids:
            resources = self.get_queryset().filter(
                subjects__id__in=subject_ids
            ).distinct().order_by('-average_rating', '-created_at')[:20]
        else:
            # Fallback to popular resources
            resources = self.get_queryset().order_by('-view_count')[:20]
        
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def related(self, request, pk=None):
        """Get related resources (same subjects)"""
        resource = self.get_object()
        
        # Get resources with same subjects
        related = self.get_queryset().filter(
            Q(subjects__in=resource.subjects.all())
        ).exclude(id=resource.id).distinct().order_by('-average_rating')[:6]
        
        serializer = self.get_serializer(related, many=True)
        return Response(serializer.data)


class ResourceRatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for resource ratings
    - Students can CRUD their own ratings
    - All can view ratings
    """
    queryset = ResourceRating.objects.all()
    serializer_class = ResourceRatingSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = ResourceRatingFilter
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Allow read for anyone, write for students only
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsStudent()]
    
    def get_queryset(self):
        """Filter to show user's own ratings for update/delete"""
        queryset = super().get_queryset()
        
        if self.action in ['update', 'partial_update', 'destroy']:
            if self.request.user.is_authenticated:
                # Show only user's own ratings for editing
                if self.request.user.role == RoleChoices.SUPER_ADMIN:
                    return queryset  # Admin sees all
                return queryset.filter(student=self.request.user)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Handle duplicate review attempts"""
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # This is a backup in case validation is bypassed
            return Response(
                {
                    'detail': 'You have already reviewed this resource. Please edit your existing review instead.',
                    'error': 'duplicate_review'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_create(self, serializer):
        """Ensure student is set to current user"""
        serializer.save(student=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_ratings(self, request):
        """Get current user's ratings"""
        ratings = self.queryset.filter(student=request.user)
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)


class ResourceBookmarkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for resource bookmarks
    - Users can add/remove their own bookmarks
    """
    queryset = ResourceBookmark.objects.all()
    serializer_class = ResourceBookmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Show only current user's bookmarks"""
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Ensure user is set to current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle(self, request):
        """Toggle bookmark for a resource"""
        resource_id = request.data.get('resource')
        if not resource_id:
            return Response(
                {'error': 'Resource ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resource = get_object_or_404(LibraryResource, id=resource_id)
        bookmark, created = ResourceBookmark.objects.get_or_create(
            resource=resource,
            user=request.user
        )
        
        if not created:
            # Already bookmarked, so remove it
            bookmark.delete()
            return Response({
                'message': 'Bookmark removed',
                'bookmarked': False
            })
        
        return Response({
            'message': 'Bookmark added',
            'bookmarked': True,
            'bookmark': self.get_serializer(bookmark).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_bookmarks(self, request):
        """Get current user's bookmarks"""
        bookmarks = self.get_queryset()
        page = self.paginate_queryset(bookmarks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookmarks, many=True)
        return Response(serializer.data)
