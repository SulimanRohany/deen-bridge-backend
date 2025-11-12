from django.urls import re_path
from core.consumers import WebRTCSignalingConsumer
from chats.routing import websocket_urlpatterns as chat_websocket_patterns
from notifications.routing import websocket_urlpatterns as notification_websocket_patterns

websocket_urlpatterns = [
    # SFU signaling for sessions
    re_path(r'ws/sessions/(?P<session_id>[^/]+)/signaling/$', WebRTCSignalingConsumer.as_asgi()),
] + chat_websocket_patterns + notification_websocket_patterns
