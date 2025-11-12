from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import communications_views

# Router for the unified UserCommunication ViewSet
router = DefaultRouter()
router.register(r'communications', communications_views.UserCommunicationViewSet, basename='user-communication')

urlpatterns = [
    # Unified communications endpoints
    path('', include(router.urls)),
    
    # Backward compatible public endpoints (these now use the unified model)
    path('contact/', communications_views.ContactMessageCreateView.as_view(), name='contact-create'),
    path('custom-course-request/', communications_views.CustomCourseRequestCreateView.as_view(), name='custom-course-request-create'),
    
    # Legacy contact form endpoints (DEPRECATED - kept for backward compatibility)
    path('contact/list/', views.ContactMessageListView.as_view(), name='contact-list-legacy'),
    path('contact/<uuid:pk>/', views.ContactMessageDetailView.as_view(), name='contact-detail-legacy'),
    path('contact/stats/', views.ContactMessageStatsView.as_view(), name='contact-stats-legacy'),
]
