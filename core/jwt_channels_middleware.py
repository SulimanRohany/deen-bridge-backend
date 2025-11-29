import logging
import jwt
from django.conf import settings
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from accounts.models import CustomUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    """
    ASGI 3-style middleware for JWT authentication in Django Channels 4.x+
    Now properly handles both regular JWT tokens and SimpleJWT tokens
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            # Copy scope to avoid mutation issues
            scope = dict(scope)
            # Get token from query string or headers
            token = None
            query_string = scope.get('query_string', b'').decode()
            
            if query_string:
                params = parse_qs(query_string)
                token_list = params.get('token')
                if token_list:
                    token = token_list[0]
            
            if not token:
                headers = dict(scope.get('headers', []))
                auth_header = headers.get(b'sec-websocket-protocol')
                if auth_header:
                    token = auth_header.decode()
            
            # Store token in scope for consumers to use
            scope['jwt_token'] = token
            user = await self.get_user(token)
            scope['user'] = user
            
            return await self.app(scope, receive, send)
            
        except Exception as e:
            logger.error(f"Error in JWT middleware: {e}", exc_info=True)
            # Don't fail the connection, just pass through with no user
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()
            return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        if not token:
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
        
        try:
            # First try SimpleJWT token validation (for regular API tokens)
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            if user_id:
                user = CustomUser.objects.get(id=user_id)
                return user
        except (InvalidToken, TokenError):
            pass
        except CustomUser.DoesNotExist:
            pass
        
        try:
            # Fallback to raw JWT validation (for signaling tokens)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('user_id')
            if user_id:
                user = CustomUser.objects.get(id=user_id)
                return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass
        except CustomUser.DoesNotExist:
            pass
        except Exception:
            pass
            
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

def JWTAuthMiddlewareStack(app):
    return JWTAuthMiddleware(app)
