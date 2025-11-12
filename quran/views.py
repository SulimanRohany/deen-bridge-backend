from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Surah, Verse, Bookmark, ReadingHistory
from .serializers import (
    SurahListSerializer, SurahDetailSerializer, VerseSerializer,
    BookmarkSerializer, ReadingHistorySerializer
)
from .permissions import IsAuthenticatedOrLimitedAccess


class VersePagination(PageNumberPagination):
    """Custom pagination for verses"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class SurahViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Surahs
    List: Returns all surahs with basic info
    Retrieve: Returns a single surah with all verses
    
    Authentication Restrictions:
    - Unauthenticated users: Can access first 5 ayahs only
    - Authenticated users: Full access to all ayahs
    """
    queryset = Surah.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'number'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SurahDetailSerializer
        return SurahListSerializer
    
    @action(detail=True, methods=['get'], url_path='verses')
    def get_verses(self, request, number=None):
        """
        Get verses for a surah with pagination.
        
        Authentication Restrictions:
        - Unauthenticated users: Limited to first 5 ayahs
        - Authenticated users: Full access
        """
        try:
            surah = self.get_object()
            verses = Verse.objects.filter(surah=surah).order_by('verse_number')
            
            # Check if user is authenticated
            is_authenticated = request.user and request.user.is_authenticated
            
            # Limit unauthenticated users to first 6 ayahs (5 normal + 1 blurred preview)
            if not is_authenticated:
                verses = verses[:6]
                # Add metadata to indicate restricted access
                restricted = True
            else:
                restricted = False
            
            # Apply pagination
            paginator = VersePagination()
            page = paginator.paginate_queryset(verses, request)
            
            if page is not None:
                serializer = VerseSerializer(page, many=True)
                response_data = paginator.get_paginated_response(serializer.data).data
                # Add authentication status to response
                response_data['is_authenticated'] = is_authenticated
                response_data['access_restricted'] = restricted
                if restricted:
                    response_data['message'] = 'Login to access all ayahs. Currently showing first 5 ayahs only.'
                return Response(response_data)
            
            # Fallback if no pagination
            serializer = VerseSerializer(verses, many=True)
            return Response({
                'results': serializer.data,
                'is_authenticated': is_authenticated,
                'access_restricted': restricted,
                'message': 'Login to access all ayahs. Currently showing first 5 ayahs only.' if restricted else None
            })
        except Surah.DoesNotExist:
            return Response(
                {'error': 'Surah not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search surahs by name or number"""
        query = request.query_params.get('q', '')
        if query:
            surahs = Surah.objects.filter(
                Q(name_arabic__icontains=query) |
                Q(name_transliteration__icontains=query) |
                Q(name_translation__icontains=query) |
                Q(number__icontains=query)
            )
        else:
            surahs = Surah.objects.all()
        
        serializer = self.get_serializer(surahs, many=True)
        return Response(serializer.data)


class VerseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing individual verses
    
    Authentication Restrictions:
    - Unauthenticated users: Can access first 5 ayahs of any surah only
    - Authenticated users: Full access to all ayahs
    """
    queryset = Verse.objects.all()
    serializer_class = VerseSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Verse.objects.all()
        surah_number = self.request.query_params.get('surah', None)
        if surah_number:
            queryset = queryset.filter(surah__number=surah_number)
            
            # Limit unauthenticated users to first 6 ayahs (5 normal + 1 blurred preview)
            is_authenticated = self.request.user and self.request.user.is_authenticated
            if not is_authenticated:
                queryset = queryset.filter(verse_number__lte=6)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to add authentication metadata"""
        queryset = self.filter_queryset(self.get_queryset())
        is_authenticated = request.user and request.user.is_authenticated
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['is_authenticated'] = is_authenticated
            if not is_authenticated:
                response.data['message'] = 'Login to access all ayahs. Currently showing first 5 ayahs only.'
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'is_authenticated': is_authenticated,
            'message': 'Login to access all ayahs. Currently showing first 5 ayahs only.' if not is_authenticated else None
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search verses by Arabic text or translation"""
        query = request.query_params.get('q', '')
        if query:
            verses = Verse.objects.filter(
                Q(text_arabic__icontains=query) |
                Q(text_translation__icontains=query) |
                Q(text_transliteration__icontains=query)
            )[:50]  # Limit results
        else:
            verses = Verse.objects.all()[:50]
        
        serializer = self.get_serializer(verses, many=True)
        return Response(serializer.data)


class BookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user bookmarks"""
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle bookmark for a verse"""
        verse_id = request.data.get('verse_id')
        if not verse_id:
            return Response(
                {'error': 'verse_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            verse = Verse.objects.get(id=verse_id)
        except Verse.DoesNotExist:
            return Response(
                {'error': 'Verse not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            verse=verse
        )
        
        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})
        
        return Response({
            'bookmarked': True,
            'bookmark': BookmarkSerializer(bookmark).data
        })


class ReadingHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reading history"""
    serializer_class = ReadingHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ReadingHistory.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def update_progress(self, request):
        """Update reading progress for a surah"""
        surah_id = request.data.get('surah_id')
        last_verse = request.data.get('last_verse', 1)
        
        if not surah_id:
            return Response(
                {'error': 'surah_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            surah = Surah.objects.get(id=surah_id)
        except Surah.DoesNotExist:
            return Response(
                {'error': 'Surah not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        history, created = ReadingHistory.objects.update_or_create(
            user=request.user,
            surah=surah,
            defaults={'last_verse': last_verse}
        )
        
        return Response(ReadingHistorySerializer(history).data)

