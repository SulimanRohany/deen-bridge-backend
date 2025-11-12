# Migration Guide: Old Settings to New Settings Structure

This guide will help you migrate from the old single `settings.py` file to the new organized settings structure.

## What Changed?

### Old Structure
```
backend/
  settings.py  # Single file with hardcoded values
```

### New Structure
```
backend/
  settings/
    __init__.py
    base.py         # Common settings
    development.py  # Development-specific settings
    production.py   # Production-specific settings
```

## Migration Steps

### Step 1: Remove Old Settings File

The old `backend/settings.py` has been replaced. If you have any custom settings in the old file, you need to:

1. **Review your old settings** (if you made custom changes)
2. **Copy custom settings** to the appropriate new file:
   - Common settings → `settings/base.py`
   - Development-only → `settings/development.py`
   - Production-only → `settings/production.py`

### Step 2: Create Environment File

1. Copy the example file:
   ```bash
   cp env.example .env
   ```

2. Update the `.env` file with your values:
   ```bash
   # For development
   SECRET_KEY=your-dev-secret-key
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3  # or your PostgreSQL URL
   REDIS_URL=redis://127.0.0.1:6379/0
   ```

### Step 3: Update Environment Variables

#### For Development

The default settings module is now `backend.settings.development`. No action needed for local development.

#### For Production

Set the environment variable:
```bash
export DJANGO_SETTINGS_MODULE=backend.settings.production
```

Or in your `.env` file:
```bash
DJANGO_SETTINGS_MODULE=backend.settings.production
```

### Step 4: Update Your Scripts

#### Old Way
```bash
python manage.py runserver
```

#### New Way (Development)
```bash
# On Windows
.\start-development.ps1

# On Linux/Mac
python manage.py runserver  # Uses development settings by default
```

#### New Way (Production)
```bash
# Deploy
./deploy-production.sh

# Start
./start-production.sh

# Or manually
export DJANGO_SETTINGS_MODULE=backend.settings.production
gunicorn -c gunicorn_config.py backend.asgi:application
```

### Step 5: Update Deployment Configuration

#### Systemd Service
Update your systemd service file to include:
```ini
Environment="DJANGO_SETTINGS_MODULE=backend.settings.production"
```

#### Docker
Update your Dockerfile:
```dockerfile
ENV DJANGO_SETTINGS_MODULE=backend.settings.production
```

#### Heroku
```bash
heroku config:set DJANGO_SETTINGS_MODULE=backend.settings.production
```

## Key Changes

### 1. No More Hardcoded Credentials

**Old:**
```python
SECRET_KEY = 'django-insecure-...'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Deen Bridge',
        'USER': 'postgres',
        'PASSWORD': 'Sadat@123',  # Hardcoded!
    }
}
```

**New:**
```python
SECRET_KEY = env('SECRET_KEY')
DATABASES = {
    'default': env.db()  # Reads from DATABASE_URL
}
```

### 2. Environment-Based Configuration

**Old:**
```python
DEBUG = True  # Always True
ALLOWED_HOSTS = ['*']  # Insecure
```

**New:**
```python
DEBUG = env('DEBUG')  # From .env file
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # Configurable
```

### 3. Proper Security Settings

**Old:**
```python
# No security headers
CORS_ALLOW_ALL_ORIGINS = True  # Insecure in production
```

**New (Production):**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
```

### 4. Improved Middleware

**New middleware added:**
- `ErrorHandlerMiddleware` - Consistent error responses
- `RequestLoggingMiddleware` - API request logging
- `SecurityHeadersMiddleware` - Additional security headers (production only)

### 5. Custom Exception Handler

All API errors now return consistent JSON responses:
```json
{
  "error": "Error message",
  "status_code": 400
}
```

## Testing the Migration

### 1. Test Development Setup
```bash
# Set development environment
export DJANGO_SETTINGS_MODULE=backend.settings.development

# Run checks
python manage.py check

# Test server
python manage.py runserver
```

### 2. Test Production Setup
```bash
# Set production environment
export DJANGO_SETTINGS_MODULE=backend.settings.production

# Run deployment checks
python manage.py check --deploy

# Collect static files
python manage.py collectstatic --noinput
```

### 3. Verify Environment Variables
```bash
python manage.py shell
```

```python
from django.conf import settings
print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DATABASE: {settings.DATABASES['default']['ENGINE']}")
```

## Common Issues

### Issue 1: Import Error for Settings
**Error:** `ModuleNotFoundError: No module named 'backend.settings'`

**Solution:** Update to use the full path:
```bash
export DJANGO_SETTINGS_MODULE=backend.settings.development
# or
export DJANGO_SETTINGS_MODULE=backend.settings.production
```

### Issue 2: Missing Environment Variables
**Error:** `django.core.exceptions.ImproperlyConfigured: Set the SECRET_KEY environment variable`

**Solution:** Create `.env` file with required variables:
```bash
cp env.example .env
# Edit .env with your values
```

### Issue 3: Database Connection Error
**Error:** `could not connect to server`

**Solution:** Update `DATABASE_URL` in `.env`:
```bash
# For PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# For SQLite (development only)
DATABASE_URL=sqlite:///db.sqlite3
```

### Issue 4: CORS Errors in Production
**Error:** `CORS header 'Access-Control-Allow-Origin' missing`

**Solution:** Set `CORS_ALLOWED_ORIGINS` in `.env`:
```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Rollback Plan

If you need to rollback to the old settings:

1. **Keep a backup** of the old `settings.py`
2. **Document any issues** you encounter
3. **Restore** by copying the old `settings.py` back

However, **we strongly recommend** using the new structure for better security and maintainability.

## Benefits of New Structure

✅ **Security**: No hardcoded credentials  
✅ **Flexibility**: Easy to switch between environments  
✅ **Maintainability**: Organized and clear settings  
✅ **Best Practices**: Follows Django deployment guidelines  
✅ **Scalability**: Ready for production deployment  
✅ **Logging**: Comprehensive error and request logging  
✅ **Monitoring**: Built-in health check endpoint  

## Need Help?

If you encounter issues during migration:

1. Check the error messages carefully
2. Review the `DEPLOYMENT.md` guide
3. Verify all environment variables are set
4. Check the logs in `logs/django.log`
5. Open an issue on GitHub with error details

## Next Steps

After successful migration:

1. ✅ Test all functionality in development
2. ✅ Set up production environment variables
3. ✅ Configure database and Redis
4. ✅ Set up SSL certificates
5. ✅ Configure Nginx reverse proxy
6. ✅ Set up monitoring and backups
7. ✅ Deploy to production

See `DEPLOYMENT.md` for detailed production deployment instructions.

