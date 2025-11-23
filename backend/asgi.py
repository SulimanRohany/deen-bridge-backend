"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""


import os

# Ensure DJANGO_SETTINGS_MODULE is set
# Default to development settings for local development
# For production, set DJANGO_SETTINGS_MODULE environment variable explicitly
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings.development'

from django.core.asgi import get_asgi_application

# Set up Django first
django_asgi_app = get_asgi_application()

# Now import channels and your middleware
from channels.routing import ProtocolTypeRouter, URLRouter
from core.jwt_channels_middleware import JWTAuthMiddlewareStack
import core.routing

application = ProtocolTypeRouter({
	"http": django_asgi_app,
	"websocket": JWTAuthMiddlewareStack(
		URLRouter(
			core.routing.websocket_urlpatterns
		)
	),
})
