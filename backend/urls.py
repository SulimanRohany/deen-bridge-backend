
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from course.views import SFURoomAccessView, SFUWebhookView


def health_check(request):
    """Health check endpoint for monitoring and load balancers"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'deenbridge-backend',
        'version': '1.0.0',
    })


def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Deen Bridge API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health/',
            'admin': '/admin/',
            'api': '/api/',
        }
    })


urlpatterns = [
    # Health check (no authentication required)
    path('health/', health_check, name='health_check'),
    path('', api_root, name='api_root'),
    
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/profile/', include('profiles.urls')),
    path('api/blog/', include('blogs.urls')),
    path('api/course/', include('course.urls')),
    path('api/enrollment/', include('enrollments.urls')),
    path('api/notification/', include('notifications.urls')),
    path('api/subject/', include('subjects.urls')),
    path('api/report/', include('reports.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/chat/', include('chats.urls')),
    path('api/library/', include('library.urls')),
    path('api/quran/', include('quran.urls')),
    path('api/', include('custom_courses.urls')),
    
    # SFU backend endpoints (must be before core.urls to avoid conflicts)
    path('api/sfu/room-access/', SFURoomAccessView.as_view(), name='sfu-room-access'),
    path('api/sfu/webhook/', SFUWebhookView.as_view(), name='sfu_webhook'),
    
    # Core app - includes unified communications endpoints
    path('api/', include('core.urls')),

]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)