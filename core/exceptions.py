"""
Custom exception handling for the API.
Provides consistent error responses across all endpoints.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides consistent error responses.
    
    This function is called for any exception raised during API request processing.
    It logs errors and returns user-friendly error messages.
    """
    # Call REST framework's default exception handler first to get the standard error response
    response = exception_handler(exc, context)
    
    # Get the view and request from context
    view = context.get('view', None)
    request = context.get('request', None)
    
    # Log the error with context
    if response is None:
        # This is an unhandled exception (500 error)
        logger.error(
            f"Unhandled exception in {view.__class__.__name__ if view else 'unknown view'}: {exc}",
            exc_info=True,
            extra={
                'request_path': request.path if request else 'unknown',
                'request_method': request.method if request else 'unknown',
                'user': str(request.user) if request and hasattr(request, 'user') else 'anonymous',
            }
        )
        
        # Return a generic error response
        return Response(
            {
                'error': 'An internal server error occurred. Please try again later.',
                'detail': 'Internal Server Error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Handle specific Django exceptions that DRF doesn't handle by default
    if isinstance(exc, Http404):
        response.data = {
            'error': 'The requested resource was not found.',
            'detail': str(exc) if str(exc) else 'Not found',
        }
        response.status_code = status.HTTP_404_NOT_FOUND
    
    elif isinstance(exc, PermissionDenied):
        response.data = {
            'error': 'You do not have permission to perform this action.',
            'detail': str(exc) if str(exc) else 'Permission denied',
        }
        response.status_code = status.HTTP_403_FORBIDDEN
    
    elif isinstance(exc, DjangoValidationError):
        response.data = {
            'error': 'Validation error occurred.',
            'detail': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
        }
        response.status_code = status.HTTP_400_BAD_REQUEST
    
    # Customize the response data structure for consistency
    if response is not None:
        # Ensure we have a consistent error structure
        if 'detail' in response.data:
            # DRF returns {'detail': 'error message'} for many errors
            error_detail = response.data.get('detail')
            response.data = {
                'error': error_detail,
                'status_code': response.status_code,
            }
        elif isinstance(response.data, dict) and not response.data.get('error'):
            # Add an 'error' key if it doesn't exist
            response.data['error'] = response.data.get('detail', 'An error occurred')
            response.data['status_code'] = response.status_code
        
        # Log non-500 errors at appropriate levels
        if response.status_code >= 500:
            logger.error(
                f"Server error ({response.status_code}) in {view.__class__.__name__ if view else 'unknown view'}: {exc}",
                exc_info=True,
                extra={
                    'request_path': request.path if request else 'unknown',
                    'request_method': request.method if request else 'unknown',
                    'user': str(request.user) if request and hasattr(request, 'user') else 'anonymous',
                }
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Client error ({response.status_code}): {exc}",
                extra={
                    'request_path': request.path if request else 'unknown',
                    'request_method': request.method if request else 'unknown',
                    'user': str(request.user) if request and hasattr(request, 'user') else 'anonymous',
                }
            )
    
    return response


class APIException(Exception):
    """Base exception for API errors"""
    default_message = 'An error occurred'
    default_status = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, message=None, status_code=None):
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status
        super().__init__(self.message)


class ValidationException(APIException):
    """Exception for validation errors"""
    default_message = 'Validation error'
    default_status = status.HTTP_400_BAD_REQUEST


class NotFoundException(APIException):
    """Exception for not found errors"""
    default_message = 'Resource not found'
    default_status = status.HTTP_404_NOT_FOUND


class PermissionException(APIException):
    """Exception for permission errors"""
    default_message = 'Permission denied'
    default_status = status.HTTP_403_FORBIDDEN


class AuthenticationException(APIException):
    """Exception for authentication errors"""
    default_message = 'Authentication required'
    default_status = status.HTTP_401_UNAUTHORIZED

