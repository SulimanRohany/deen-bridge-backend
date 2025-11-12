#!/bin/bash
# Production deployment script for Deen Bridge Backend
# This script prepares the application for production deployment

set -e  # Exit on error

echo "=========================================="
echo "Deen Bridge Backend - Production Deployment"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create a .env file from env.example and configure it for production."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Verify required environment variables
if [ "$DEBUG" = "True" ]; then
    echo "⚠️  WARNING: DEBUG is set to True. This should be False in production!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set Django settings module to production
export DJANGO_SETTINGS_MODULE=backend.settings.production

echo ""
echo "📦 Step 1: Installing dependencies..."
pip install -r requirements.txt --upgrade

echo ""
echo "🔄 Step 2: Running database migrations..."
python manage.py migrate --noinput

echo ""
echo "📊 Step 3: Collecting static files..."
python manage.py collectstatic --noinput --clear

echo ""
echo "✅ Step 4: Running system checks..."
python manage.py check --deploy

echo ""
echo "👤 Step 5: Creating superuser (skip if already exists)..."
python manage.py createsuperuser --noinput || echo "Superuser already exists or skipped"

echo ""
echo "🧹 Step 6: Cleaning up..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete

echo ""
echo "=========================================="
echo "✅ Deployment preparation complete!"
echo "=========================================="
echo ""
echo "To start the server, run:"
echo "  ./start-production.sh"
echo ""
echo "Or manually with Gunicorn:"
echo "  gunicorn -c gunicorn_config.py backend.asgi:application"
echo ""

