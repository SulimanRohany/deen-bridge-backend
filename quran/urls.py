from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SurahViewSet, VerseViewSet, BookmarkViewSet, ReadingHistoryViewSet

router = DefaultRouter()
router.register(r'surahs', SurahViewSet, basename='surah')
router.register(r'verses', VerseViewSet, basename='verse')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'history', ReadingHistoryViewSet, basename='reading-history')

urlpatterns = [
    path('', include(router.urls)),
]

