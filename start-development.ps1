# Start Django Backend in Development Mode
# Updated to use new settings structure

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Starting Deen Bridge Backend (Development)" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Set environment variables for development
$env:DJANGO_SETTINGS_MODULE = "backend.settings.development"
$env:DEBUG = "True"

Write-Host "📝 Configuration:" -ForegroundColor Cyan
Write-Host "   - Settings Module: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor White
Write-Host "   - Debug Mode: Enabled" -ForegroundColor White
Write-Host "   - Server: http://127.0.0.1:8000" -ForegroundColor White
Write-Host ""

# Check if we're in the backend directory
if (-not (Test-Path ".\manage.py")) {
    Write-Host "❌ Error: This script must be run from the backend directory" -ForegroundColor Red
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Starting development server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Django development server
python manage.py runserver 8000

