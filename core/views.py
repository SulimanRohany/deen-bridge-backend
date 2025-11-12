from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.authentication import BaseAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from core.pagination import CustomPagination

from .models import ContactMessage
from .serializers import (
    ContactMessageSerializer, 
    ContactMessageListSerializer, 
    ContactMessageUpdateSerializer
)


class ContactMessageCreateView(generics.CreateAPIView):
    """API view to create contact messages (public endpoint)"""
    
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]
    # Force JSON responses only and disable session authentication/CSRF for this public endpoint
    authentication_classes = []
    renderer_classes = [JSONRenderer]
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                'message': 'Your message has been sent successfully! We will get back to you within 24 hours.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            # Always return JSON so the frontend never receives an HTML error page
            return Response({
                'message': 'Failed to submit your message.',
                'error': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)


class ContactMessageListView(generics.ListAPIView):
    """API view to list contact messages (admin only)"""
    
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageListSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    pagination_class = CustomPagination
    
    def get_queryset(self):
        # Only show messages to authenticated users (admin)
        return ContactMessage.objects.all()


class ContactMessageDetailView(generics.RetrieveUpdateAPIView):
    """API view to retrieve and update contact messages (admin only)"""
    
    renderer_classes = [JSONRenderer]
    queryset = ContactMessage.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ContactMessageUpdateSerializer
        return ContactMessageListSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Message status updated successfully',
            'data': ContactMessageListSerializer(instance).data
        })


class ContactMessageStatsView(generics.GenericAPIView):
    """API view to get contact message statistics (admin only)"""
    
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        total_messages = ContactMessage.objects.count()
        new_messages = ContactMessage.objects.filter(status='new').count()
        read_messages = ContactMessage.objects.filter(status='read').count()
        replied_messages = ContactMessage.objects.filter(status='replied').count()
        closed_messages = ContactMessage.objects.filter(status='closed').count()
        
        return Response({
            'total_messages': total_messages,
            'new_messages': new_messages,
            'read_messages': read_messages,
            'replied_messages': replied_messages,
            'closed_messages': closed_messages,
            'status_distribution': {
                'new': new_messages,
                'read': read_messages,
                'replied': replied_messages,
                'closed': closed_messages
            }
        })