"""
Custom middleware for the application.
"""

import logging
import time
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(MiddlewareMixin):
    """
    Middleware to catch and handle unhandled exceptions in the application.
    This ensures that all errors return JSON responses and are properly logged.
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions that occur during request handling.
        """
        # Log the exception with full context
        logger.error(
            f"Unhandled exception: {exception}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
                'get_params': dict(request.GET),
                'post_params': dict(request.POST) if request.method == 'POST' else {},
            }
        )
        
        # In production, return a generic error message
        if not settings.DEBUG:
            return JsonResponse(
                {
                    'error': 'An internal server error occurred',
                    'message': 'Please try again later or contact support if the problem persists',
                },
                status=500
            )
        
        # In debug mode, let Django's default exception handling show the debug page
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests for monitoring and debugging.
    """
    
    def process_request(self, request):
        """Log the incoming request"""
        request._start_time = time.time()
        
        # Only log API requests
        if request.path.startswith('/api/'):
            logger.info(
                f"Request: {request.method} {request.path}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                    'ip': self.get_client_ip(request),
                }
            )
        
        return None
    
    def process_response(self, request, response):
        """Log the outgoing response"""
        # Only log API requests
        if hasattr(request, '_start_time') and request.path.startswith('/api/'):
            duration = time.time() - request._start_time
            
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                'ip': self.get_client_ip(request),
            }
            
            # Log at appropriate level based on status code
            if response.status_code >= 500:
                logger.error(f"Response: {request.method} {request.path} - {response.status_code}", extra=log_data)
            elif response.status_code >= 400:
                logger.warning(f"Response: {request.method} {request.path} - {response.status_code}", extra=log_data)
            else:
                logger.info(f"Response: {request.method} {request.path} - {response.status_code}", extra=log_data)
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add additional security headers to responses.
    """
    
    def process_response(self, request, response):
        """Add security headers to the response"""
        # Add Content Security Policy
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: ws:; "
            )
        
        # Add Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Permissions Policy (formerly Feature Policy)
        # Allow camera and microphone for same origin (needed for live video sessions)
        # Block geolocation for security
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(self), "
            "camera=(self)"
        )
        
        return response


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to handle health check requests quickly without authentication.
    """
    
    def process_request(self, request):
        """Handle health check requests"""
        if request.path == '/health/' or request.path == '/health':
            return JsonResponse({
                'status': 'healthy',
                'service': 'backend',
            })
        return None


class DisableCSRFForAPI(MiddlewareMixin):
    """
    Middleware to disable CSRF protection for API endpoints.
    API endpoints use JWT authentication and don't need CSRF protection.
    """
    
    def process_request(self, request):
        """Disable CSRF for API endpoints"""
        # Exempt all API endpoints from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
