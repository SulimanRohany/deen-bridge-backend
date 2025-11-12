from rest_framework.permissions import BasePermission


class AyahAccessPermission(BasePermission):
    """
    Custom permission to limit unauthenticated users to first 5 ayahs.
    Authenticated users get full access.
    """
    
    def has_permission(self, request, view):
        # Always allow the request at view level
        return True
    
    def has_object_permission(self, request, view, obj):
        # Always allow at object level (filtering happens in view)
        return True


class IsAuthenticatedOrLimitedAccess(BasePermission):
    """
    Allows authenticated users full access.
    Allows unauthenticated users limited access (first 5 ayahs only).
    """
    
    def has_permission(self, request, view):
        # Allow all requests - restrictions applied at data level
        return True

