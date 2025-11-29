import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat in live sessions.
    Each session has its own chat room: chat.session.<session_id>
    """

    async def connect(self):
        """Handle WebSocket connection."""
        # Initialize attributes early to prevent AttributeError
        self.session_id = None
        self.room_group_name = None
        self.user = None
        self.is_fully_connected = False  # Track if connection is fully established (room group joined)
        
        try:
            # Get session ID from URL route
            self.session_id = self.scope['url_route']['kwargs']['session_id']
            self.room_group_name = f'chat.session.{self.session_id}'
            
            # Get user from scope (authenticated via JWT middleware)
            self.user = self.scope.get('user')
            
            # Check authentication
            if not self.user or not self.user.is_authenticated:
                await self.close(code=4001)
                return
            
            # Accept connection first (before joining group)
            await self.accept()
            
            # Join room group (after accepting connection)
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                self.is_fully_connected = True  # Mark as fully connected
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a Redis connection error
                if '6379' in error_msg or 'redis' in error_msg.lower() or '10061' in error_msg or 'ConnectionRefusedError' in error_msg:
                    # Send error message to client before closing
                    try:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': 'Chat service unavailable. Redis server is not running.',
                        }))
                    except:
                        pass
                else:
                    # Send generic error
                    try:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': 'Failed to join chat room.',
                        }))
                    except:
                        pass
                
                await self.close(code=4002)
                return
            
            # Send connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to chat',
                'session_id': self.session_id,
            }))
            
            # Notify others that user joined (only if we successfully joined the room)
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_joined',
                        'user_id': self.user.id,
                        'user_name': self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email,
                    }
                )
            except Exception as e:
                # Don't fail the connection if this fails
                pass
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                await self.close(code=4002)
            except:
                pass

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Notify others that user left (only if we successfully connected)
        if hasattr(self, 'user') and self.user and self.user.is_authenticated and hasattr(self, 'room_group_name'):
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user_id': self.user.id,
                        'user_name': self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email,
                    }
                )
            except Exception:
                pass
        
        # Leave room group (only if we successfully joined)
        if hasattr(self, 'room_group_name') and hasattr(self, 'channel_name'):
            try:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            except Exception:
                pass

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            # Check if connection is fully established
            if not hasattr(self, 'is_fully_connected') or not self.is_fully_connected:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Connection not fully established. Please reconnect. (Redis may not be running)',
                }))
                return
            
            # Check if user is set (connection might have failed)
            if not hasattr(self, 'user') or not self.user:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Connection not properly established. Please reconnect.',
                }))
                return
            
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                # Handle chat message
                message_text = data.get('message', '').strip()
                
                if not message_text:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message cannot be empty',
                    }))
                    return
                
                # Check if room group is set
                if not hasattr(self, 'room_group_name') or not self.room_group_name:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Connection not fully established. Please reconnect.',
                    }))
                    return
                
                # Save message to database
                chat_message = await self.save_message(
                    session_id=self.session_id,
                    sender=self.user,
                    message=message_text,
                    message_type='text'
                )
                
                # Broadcast message to all users in the room
                try:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message_broadcast',
                            'message': await self.message_to_dict(chat_message),
                            'sender_id': self.user.id,  # Include sender ID for filtering
                        }
                    )
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if it's a Redis error
                    if '6379' in error_msg or 'redis' in error_msg.lower() or '10061' in error_msg or 'ConnectionRefusedError' in error_msg:
                        error_message = 'Failed to send message. Redis server is not running. Please start Redis and reconnect.'
                    else:
                        error_message = 'Failed to send message. Please try again.'
                    
                    # Send error back to sender
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': error_message,
                    }))
                    return
            
            elif message_type == 'typing':
                # Handle typing indicator
                is_typing = data.get('is_typing', False)
                
                try:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'user_typing',
                            'user_id': self.user.id,
                            'user_name': self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email,
                            'is_typing': is_typing,
                        }
                    )
                except Exception:
                    # Don't fail - typing indicator is not critical
                    pass
            
            elif message_type == 'get_history':
                # Send chat history to the requesting user
                limit = data.get('limit', 50)
                messages = await self.get_chat_history(self.session_id, limit)
                unread_count = await self.get_unread_count(self.session_id)
                
                await self.send(text_data=json.dumps({
                    'type': 'chat_history',
                    'messages': messages,
                    'unread_count': unread_count,
                }))
            
            elif message_type == 'mark_read':
                # Mark messages as read
                message_id = data.get('message_id')
                marked_count = await self.mark_messages_read(self.session_id, message_id)
                
                # Get updated unread count after marking as read
                updated_unread_count = await self.get_unread_count(self.session_id)
                
                await self.send(text_data=json.dumps({
                    'type': 'messages_marked_read',
                    'marked_count': marked_count,
                    'unread_count': updated_unread_count,
                }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format',
            }))
        except Exception:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to process message',
            }))

    async def chat_message_broadcast(self, event):
        """Send chat message to WebSocket with unread count for current user."""
        message_data = {
            'type': 'chat_message',
            'message': event['message'],
        }
        
        # Add unread count for the receiving user (not the sender)
        sender_id = event.get('sender_id')
        is_sender = sender_id == self.user.id
        
        if not is_sender:
            # This user is receiving the message, calculate their unread count
            unread_count = await self.get_unread_count(self.session_id)
            message_data['unread_count'] = unread_count
        
        await self.send(text_data=json.dumps(message_data))

    async def user_joined(self, event):
        """Send user joined notification to WebSocket."""
        # Don't send to the user who joined
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
            }))

    async def user_left(self, event):
        """Send user left notification to WebSocket."""
        # Don't send to the user who left
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
            }))

    async def user_typing(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))

    @database_sync_to_async
    def save_message(self, session_id, sender, message, message_type='text'):
        """Save chat message to database."""
        from .models import ChatMessage
        from course.models import LiveSession
        
        session = LiveSession.objects.get(id=session_id)
        
        chat_message = ChatMessage.objects.create(
            session=session,
            sender=sender,
            message=message,
            message_type=message_type,
        )
        
        return chat_message

    @database_sync_to_async
    def message_to_dict(self, message):
        """Convert message to dictionary."""
        return message.to_dict()

    @database_sync_to_async
    def get_chat_history(self, session_id, limit=50):
        """Get chat history for a session."""
        from .models import ChatMessage
        
        messages = ChatMessage.objects.filter(
            session_id=session_id,
            is_deleted=False
        ).order_by('-created_at')[:limit]
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        return [msg.to_dict() for msg in messages]
    
    @database_sync_to_async
    def get_unread_count(self, session_id):
        """Get unread message count for current user in this session."""
        from .models import ChatMessage
        
        # Get all messages in session
        all_messages = ChatMessage.objects.filter(
            session_id=session_id,
            is_deleted=False
        ).count()
        
        # Get unread count - messages where user is NOT in read_by
        unread_count = ChatMessage.objects.filter(
            session_id=session_id,
            is_deleted=False
        ).exclude(
            read_by=self.user  # Exclude messages where user is in read_by
        ).count()
        
        return unread_count
    
    @database_sync_to_async
    def mark_messages_read(self, session_id, message_id=None):
        """Mark messages as read for the current user."""
        from .models import ChatMessage
        from course.models import LiveSession
        
        session = LiveSession.objects.get(id=session_id)
        
        # Get all unread messages in the session for this user
        messages_query = ChatMessage.objects.filter(
            session=session,
            is_deleted=False
        ).exclude(
            read_by=self.user  # Only get messages user hasn't read
        )
        
        # If message_id is provided, only mark messages up to that message
        if message_id:
            messages_query = messages_query.filter(id__lte=message_id)
        
        marked_count = 0
        
        # Add user to read_by for each unread message
        for message in messages_query:
            message.read_by.add(self.user)
            marked_count += 1
        
        return marked_count

