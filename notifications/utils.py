"""
Utility functions for creating and sending notifications
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

from .models import Notification, NotificationChannels, NotificationType, NotificationStatus
from .serializers import NotificationListSerializer


def send_notification(
    user,
    title,
    body,
    notification_type=NotificationType.INFO,
    channel=NotificationChannels.IN_APP,
    action_url=None,
    metadata=None
):
    """
    Create and send a notification to a user in real-time via WebSocket.
    
    Args:
        user: The user to send the notification to
        title: Notification title
        body: Notification body/message
        notification_type: Type of notification (default: INFO)
        channel: Notification channel (default: IN_APP)
        action_url: Optional URL for notification action
        metadata: Optional dictionary of additional metadata
    
    Returns:
        The created Notification instance
    """
    # Create the notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        body=body,
        type=notification_type,
        channel=channel,
        action_url=action_url,
        metadata=metadata or {},
        status=NotificationStatus.SENT,
        sent_at=timezone.now()
    )
    
    # Send real-time update via WebSocket
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                "type": "notification_message",
                "notification": NotificationListSerializer(notification).data
            }
        )
    except Exception as e:
        print(f"Error sending notification via WebSocket to user {user.id}: {e}")
    
    return notification


def send_notification_to_multiple_users(
    users,
    title,
    body,
    notification_type=NotificationType.INFO,
    channel=NotificationChannels.IN_APP,
    action_url=None,
    metadata=None
):
    """
    Create and send notifications to multiple users in real-time via WebSocket.
    
    Args:
        users: Queryset or list of users to send the notification to
        title: Notification title
        body: Notification body/message
        notification_type: Type of notification (default: INFO)
        channel: Notification channel (default: IN_APP)
        action_url: Optional URL for notification action
        metadata: Optional dictionary of additional metadata
    
    Returns:
        List of created Notification instances
    """
    notifications = []
    channel_layer = get_channel_layer()
    
    for user in users:
        # Create the notification
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            type=notification_type,
            channel=channel,
            action_url=action_url,
            metadata=metadata or {},
            status=NotificationStatus.SENT,
            sent_at=timezone.now()
        )
        notifications.append(notification)
        
        # Send real-time update via WebSocket
        try:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user.id}",
                {
                    "type": "notification_message",
                    "notification": NotificationListSerializer(notification).data
                }
            )
        except Exception as e:
            print(f"Error sending notification via WebSocket to user {user.id}: {e}")
    
    return notifications

