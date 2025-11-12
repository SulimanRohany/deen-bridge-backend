from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LibraryCategoryViewSet, LibraryResourceViewSet,
    ResourceRatingViewSet, ResourceBookmarkViewSet
)

app_name = 'library'

router = DefaultRouter()
router.register(r'category', LibraryCategoryViewSet, basename='category')
router.register(r'resource', LibraryResourceViewSet, basename='resource')
router.register(r'rating', ResourceRatingViewSet, basename='rating')
router.register(r'bookmark', ResourceBookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
]

