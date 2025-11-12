import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connect to the WebSocket"""
        # Get user from scope (set by JWT middleware)
        self.user = self.scope.get('user')
        
        if self.user and self.user.is_authenticated:
            # Create a group for this user's notifications
            self.room_group_name = f'notifications_{self.user.id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to notifications'
            }))
        else:
            # Reject connection if user is not authenticated
            await self.close()

    async def disconnect(self, close_code):
        """Disconnect from the WebSocket"""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                # Send pong back
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def notification_message(self, event):
        """Receive notification from room group and send to WebSocket"""
        notification = event['notification']
        
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))

    async def notification_update(self, event):
        """Handle notification updates (mark as read, etc.)"""
        await self.send(text_data=json.dumps({
            'type': 'notification_updated',
            'notification_id': event.get('notification_id'),
            'updates': event.get('updates')
        }))

