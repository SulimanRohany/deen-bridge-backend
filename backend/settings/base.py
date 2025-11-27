"""
Django settings for backend project.
Base settings shared across all environments.
"""

from datetime import timedelta
from pathlib import Path
import environ
import os

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'django-insecure-CHANGE-THIS-IN-PRODUCTION'),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, ''),
    REDIS_URL=(str, ''),  # Empty by default - uses InMemoryChannelLayer. Set to 'redis://127.0.0.1:6379/0' to use Redis
    BACKEND_URL=(str, 'http://localhost:8000'),
    CORS_ALLOWED_ORIGINS=(list, []),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Backend URL for notifications and links
BACKEND_URL = env('BACKEND_URL')

# Application definition
INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # local apps
    'accounts',
    'blogs',
    'core',
    'course',
    'enrollments',
    'notifications',
    'profiles', 
    'subjects',
    'reports',
    'dashboard',
    'chats',
    'library',
    'quran',
    'custom_courses',

    # 3rd party apps
    'taggit',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPagination',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'core.middleware.DisableCSRFForAPI',  # Disable CSRF for API endpoints (before CSRF middleware)
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ASGI/WSGI
WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASE_URL = env('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': env.db()
    }
else:
    # Fallback to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File Upload Size Limits
# Increase upload size limits to handle large blog posts with rich text content and images
# 10MB for form data (non-file fields like rich text content)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
# 50MB for file uploads (featured images, etc.)
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
# Maximum number of fields in a form
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
# Maximum number of files in a multipart upload
DATA_UPLOAD_MAX_NUMBER_FILES = 100

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

# Channels Configuration
# Default to InMemory for development, Redis for production
# Set REDIS_URL='' or don't set it to use InMemoryChannelLayer (development only)
# Set REDIS_URL='redis://127.0.0.1:6379/0' to use Redis (production)
REDIS_URL_VALUE = env('REDIS_URL', default='')
USE_REDIS = REDIS_URL_VALUE and REDIS_URL_VALUE.strip() and 'redis://' in REDIS_URL_VALUE

if USE_REDIS:
    # Parse Redis URL to extract host and port
    try:
        from urllib.parse import urlparse
        parsed = urlparse(REDIS_URL_VALUE)
        redis_host = parsed.hostname or '127.0.0.1'
        redis_port = parsed.port or 6379
        redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
        
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    "hosts": [(redis_host, redis_port)],
                    "channel_capacity": {
                        "http.request": 200,
                        "http.response!*": 10,
                        "websocket.send": 20,
                    },
                },
            },
        }
        print(f"✅ Using Redis Channel Layer: {redis_host}:{redis_port} (db: {redis_db})")
    except Exception as e:
        print(f"⚠️ Error parsing REDIS_URL, falling back to InMemoryChannelLayer: {e}")
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer',
            },
        }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    print("✅ Using InMemoryChannelLayer (Redis not configured or disabled)")

# CORS Settings (will be overridden in production)
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# Default CORS origins for development
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3005",
    "http://localhost:3001",
])

# CSRF Settings - Exempt API endpoints from CSRF (they use JWT authentication)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=CORS_ALLOWED_ORIGINS)
# Exempt API endpoints from CSRF protection since they use JWT
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_USE_SESSIONS = False

# WebSocket CORS settings
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'sec-websocket-protocol',
    'sec-websocket-version',
    'sec-websocket-key',
    'sec-websocket-extensions',
]

