#!/bin/bash
# Start the Deen Bridge Backend in production mode
# Uses Gunicorn with Uvicorn workers for ASGI/WebSocket support

set -e  # Exit on error

echo "=========================================="
echo "Starting Deen Bridge Backend (Production)"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set Django settings module to production
export DJANGO_SETTINGS_MODULE=backend.settings.production

# Verify SECRET_KEY is set
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is not set!"
    exit 1
fi

# Verify DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL is not set. Using SQLite (not recommended for production)."
fi

echo ""
echo "🚀 Starting Gunicorn server..."
echo ""

# Start Gunicorn with the configuration file
exec gunicorn -c gunicorn_config.py backend.asgi:application

