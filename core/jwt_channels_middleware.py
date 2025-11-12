import jwt
from django.conf import settings
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from accounts.models import CustomUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JWTAuthMiddleware:
    """
    ASGI 3-style middleware for JWT authentication in Django Channels 4.x+
    Now properly handles both regular JWT tokens and SimpleJWT tokens
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            print(f"🔍 JWT Middleware called for scope type: {scope.get('type')}")
            
            # Copy scope to avoid mutation issues
            scope = dict(scope)
            # Get token from query string or headers
            token = None
            query_string = scope.get('query_string', b'').decode()
            
            print(f"   Query string: {query_string}")
            
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
            
            print(f"   Extracted token: {token[:20] if token else 'None'}...")
            
            # Store token in scope for consumers to use
            scope['jwt_token'] = token
            user = await self.get_user(token)
            scope['user'] = user
            
            print(f"   User: {user}")
            
            return await self.app(scope, receive, send)
            
        except Exception as e:
            print(f"❌ Error in JWT middleware: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the connection, just pass through with no user
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()
            return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        if not token:
            print("   No token provided")
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
        
        try:
            # First try SimpleJWT token validation (for regular API tokens)
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            if user_id:
                user = CustomUser.objects.get(id=user_id)
                print(f"   ✅ User authenticated via SimpleJWT: {user.email}")
                return user
        except InvalidToken as e:
            print(f"   ⚠️ SimpleJWT token invalid: {e}")
        except TokenError as e:
            print(f"   ⚠️ SimpleJWT token error: {e}")
        except CustomUser.DoesNotExist:
            print(f"   ⚠️ User not found for user_id: {user_id}")
        
        try:
            # Fallback to raw JWT validation (for signaling tokens)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('user_id')
            if user_id:
                user = CustomUser.objects.get(id=user_id)
                print(f"   ✅ User authenticated via raw JWT: {user.email}")
                return user
        except jwt.ExpiredSignatureError:
            print(f"   ⚠️ JWT token expired")
        except jwt.InvalidTokenError as e:
            print(f"   ⚠️ JWT token invalid: {e}")
        except CustomUser.DoesNotExist:
            print(f"   ⚠️ User not found for user_id: {user_id}")
        except Exception as e:
            print(f"   ⚠️ JWT validation error: {e}")
            
        from django.contrib.auth.models import AnonymousUser
        print("   ❌ Authentication failed, returning AnonymousUser")
        return AnonymousUser()

def JWTAuthMiddlewareStack(app):
    return JWTAuthMiddleware(app)
