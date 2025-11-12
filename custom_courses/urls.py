from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomCourseRequestViewSet

router = DefaultRouter()
# DEPRECATED: Use core.communications endpoints instead
# Keeping this for backward compatibility during transition period
router.register(r'custom-course-requests', CustomCourseRequestViewSet, basename='custom-course-request-legacy')

urlpatterns = [
    path('', include(router.urls)),
]

