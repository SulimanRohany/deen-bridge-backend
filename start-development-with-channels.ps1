# Start Django Backend with Daphne (WebSocket Support) in Development Mode
# Updated to use new settings structure

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Starting Deen Bridge Backend with Daphne (Development)" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Set environment variables for development
$env:DJANGO_SETTINGS_MODULE = "backend.settings.development"
$env:DEBUG = "True"

Write-Host "📝 Configuration:" -ForegroundColor Cyan
Write-Host "   - Settings Module: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor White
Write-Host "   - Debug Mode: Enabled" -ForegroundColor White
Write-Host "   - ASGI Server: Daphne" -ForegroundColor White
Write-Host "   - WebSocket Support: ✅ Enabled" -ForegroundColor Green
Write-Host "   - Server: http://0.0.0.0:8000" -ForegroundColor White
Write-Host ""

# Check if we're in the backend directory
if (-not (Test-Path ".\manage.py")) {
    Write-Host "❌ Error: This script must be run from the backend directory" -ForegroundColor Red
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Check if Daphne is installed
Write-Host "🔍 Checking Daphne installation..." -ForegroundColor Cyan
try {
    $daphneCheck = python -c "import daphne; print('installed')" 2>&1
    if ($daphneCheck -eq "installed") {
        Write-Host "   ✅ Daphne is installed" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Daphne not found" -ForegroundColor Red
        Write-Host "   Installing Daphne..." -ForegroundColor Yellow
        pip install daphne
    }
} catch {
    Write-Host "   ❌ Error checking Daphne" -ForegroundColor Red
    Write-Host "   Installing Daphne..." -ForegroundColor Yellow
    pip install daphne
}

Write-Host ""
Write-Host "🚀 Starting Daphne server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Daphne
daphne -b 0.0.0.0 -p 8000 backend.asgi:application

