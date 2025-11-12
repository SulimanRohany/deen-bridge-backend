from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Exists, OuterRef
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from course.models import LiveSession


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat messages.
    Provides CRUD operations and chat history retrieval.
    """
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session', 'sender', 'message_type']
    
    def get_queryset(self):
        """Filter messages based on user access."""
        queryset = super().get_queryset()
        
        # Only show non-deleted messages by default
        if not self.request.query_params.get('show_deleted'):
            queryset = queryset.filter(is_deleted=False)
        
        return queryset.select_related('sender', 'session')
    
    def perform_create(self, serializer):
        """Set the sender to the current user when creating a message."""
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='session/(?P<session_id>[^/.]+)')
    def session_messages(self, request, session_id=None):
        """
        Get all chat messages for a specific session.
        Query params:
        - limit: Number of messages to return (default: 50)
        - offset: Offset for pagination (default: 0)
        """
        try:
            # Verify session exists
            session = LiveSession.objects.get(id=session_id)
            
            # Get messages for the session
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            messages = ChatMessage.objects.filter(
                session=session,
                is_deleted=False
            ).order_by('created_at')[offset:offset + limit]
            
            serializer = self.get_serializer(messages, many=True)
            
            return Response({
                'count': messages.count(),
                'results': serializer.data,
            })
            
        except LiveSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid limit or offset parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def delete_message(self, request, pk=None):
        """Soft delete a message (only sender or admin can delete)."""
        message = self.get_object()
        
        # Check if user is the sender or has admin privileges
        if message.sender != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to delete this message'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_deleted = True
        message.save()
        
        return Response({'message': 'Message deleted successfully'})
    
    @action(detail=False, methods=['post'], url_path='session/(?P<session_id>[^/.]+)/mark-read')
    def mark_session_messages_read(self, request, session_id=None):
        """
        Mark all messages in a session as read for the current user.
        Optionally, mark messages up to a specific message_id.
        
        Request body (optional):
        - message_id: Mark messages up to and including this message
        """
        try:
            # Verify session exists
            session = LiveSession.objects.get(id=session_id)
            
            # Get message_id from request if provided
            message_id = request.data.get('message_id')
            
            # Get all unread messages in the session for this user
            messages_query = ChatMessage.objects.filter(
                session=session,
                is_deleted=False
            ).exclude(
                read_by=request.user  # Only get messages user hasn't read
            )
            
            # If message_id is provided, only mark messages up to that message
            if message_id:
                messages_query = messages_query.filter(id__lte=message_id)
            
            marked_count = 0
            
            # Add user to read_by for each unread message
            for message in messages_query:
                message.read_by.add(request.user)
                marked_count += 1
            
            return Response({
                'message': f'Marked {marked_count} messages as read',
                'marked_count': marked_count,
            })
            
        except LiveSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='session/(?P<session_id>[^/.]+)/unread-count')
    def unread_count(self, request, session_id=None):
        """
        Get the count of unread messages in a session for the current user.
        """
        try:
            # Verify session exists
            session = LiveSession.objects.get(id=session_id)
            
            # Count unread messages (messages where user is NOT in read_by)
            unread_count = ChatMessage.objects.filter(
                session=session,
                is_deleted=False
            ).exclude(
                read_by=request.user  # Exclude messages user has read
            ).count()
            
            return Response({
                'session_id': session_id,
                'unread_count': unread_count,
            })
            
        except LiveSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
