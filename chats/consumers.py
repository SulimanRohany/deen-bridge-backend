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
        try:
            print(f"🔍 Chat connection attempt started")
            
            # Get session ID from URL route
            self.session_id = self.scope['url_route']['kwargs']['session_id']
            self.room_group_name = f'chat.session.{self.session_id}'
            
            # Get user from scope (authenticated via JWT middleware)
            self.user = self.scope.get('user')
            
            print(f"   Session ID: {self.session_id}")
            print(f"   Room group: {self.room_group_name}")
            print(f"   User: {self.user}")
            print(f"   Is authenticated: {self.user.is_authenticated if self.user else 'No user'}")
            
            # Check authentication
            if not self.user or not self.user.is_authenticated:
                print(f"❌ Unauthorized chat connection attempt for session: {self.session_id}")
                await self.close(code=4001)
                return
            
            print(f"✅ Chat WebSocket connection for session: {self.session_id}, user: {self.user.email}")
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to chat',
                'session_id': self.session_id,
            }))
            
            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'user_name': self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email,
                }
            )
            
            print(f"✅ Chat WebSocket connection established successfully")
            
        except Exception as e:
            print(f"❌ Error in chat connect: {e}")
            import traceback
            traceback.print_exc()
            try:
                await self.close(code=4002)
            except:
                pass

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        print(f"💬 Chat WebSocket disconnected for session: {self.session_id}, code: {close_code}")
        
        # Notify others that user left
        if hasattr(self, 'user') and self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'user_name': self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email,
                }
            )
        
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            print(f"📩 Received chat message: {message_type} from {self.user.email}")
            
            if message_type == 'chat_message':
                # Handle chat message
                message_text = data.get('message', '').strip()
                
                if not message_text:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message cannot be empty',
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
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message_broadcast',
                        'message': await self.message_to_dict(chat_message),
                        'sender_id': self.user.id,  # Include sender ID for filtering
                    }
                )
            
            elif message_type == 'typing':
                # Handle typing indicator
                is_typing = data.get('is_typing', False)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': self.user.id,
                        'user_name': self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email,
                        'is_typing': is_typing,
                    }
                )
            
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
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in chat: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format',
            }))
        except Exception as e:
            print(f"❌ Error processing chat message: {e}")
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
        
        print(f"📤 Broadcasting to {self.user.email}: sender_id={sender_id}, is_sender={is_sender}")
        
        if not is_sender:
            # This user is receiving the message, calculate their unread count
            unread_count = await self.get_unread_count(self.session_id)
            message_data['unread_count'] = unread_count
            print(f"   📊 Unread count for {self.user.email}: {unread_count}")
        else:
            print(f"   ✉️ User is sender, no unread count needed")
        
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
        
        print(f"🔍 get_unread_count for {self.user.email}: total={all_messages}, unread={unread_count}")
        
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
        
        print(f"✅ Marked {marked_count} messages as read for {self.user.email}")
        
        return marked_count

