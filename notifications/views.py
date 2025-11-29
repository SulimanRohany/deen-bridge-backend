from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
import logging

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification
from .serializers import NotificationSerializer, NotificationListSerializer

logger = logging.getLogger(__name__)


class NotificationPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 100


class NotificationListCreateView(ListCreateAPIView):
    serializer_class = NotificationListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        """Filter notifications for the authenticated user only"""
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by read/unread status if specified
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(read_at__isnull=False)
            elif is_read.lower() == 'false':
                queryset = queryset.filter(read_at__isnull=True)
        
        # Filter by type if specified
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        return queryset.select_related('user')
    
    def perform_create(self, serializer):
        """Automatically set the user when creating a notification"""
        notification = serializer.save()
        
        # Send real-time update via WebSocket
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{notification.user.id}",
                {
                    "type": "notification_message",
                    "notification": NotificationListSerializer(notification).data
                }
            )
        except Exception as e:
            logger.error(f"Error sending notification via WebSocket: {e}", exc_info=True)


class NotificationRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only allow users to access their own notifications"""
        return Notification.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, pk):
    """Mark a single notification as read"""
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.mark_as_read()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_unread(request, pk):
    """Mark a single notification as unread"""
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.mark_as_unread()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """Mark all notifications as read for the current user"""
    notifications = Notification.objects.filter(
        user=request.user,
        read_at__isnull=True
    )
    count = notifications.update(read_at=timezone.now())
    
    return Response(
        {"message": f"{count} notifications marked as read"},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Get the count of unread notifications for the current user"""
    count = Notification.objects.filter(
        user=request.user,
        read_at__isnull=True
    ).count()
    
    return Response(
        {"unread_count": count},
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_notifications(request):
    """Delete all notifications for the current user"""
    count, _ = Notification.objects.filter(user=request.user).delete()
    
    return Response(
        {"message": f"{count} notifications deleted"},
        status=status.HTTP_200_OK
    )
