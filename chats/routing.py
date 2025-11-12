from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    # Chat WebSocket for live sessions
    re_path(r'ws/sessions/(?P<session_id>[^/]+)/chat/$', ChatConsumer.as_asgi()),
]

