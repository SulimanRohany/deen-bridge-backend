# Start Django Backend with Daphne (WebSocket Support)
# This script starts Django with Daphne ASGI server to support WebSocket connections

Write-Host "🚀 Starting Django Backend with Daphne..." -ForegroundColor Green
Write-Host ""
Write-Host "📝 Configuration:" -ForegroundColor Cyan
Write-Host "   - Host: 0.0.0.0 (accessible from network)" -ForegroundColor White
Write-Host "   - Port: 8000" -ForegroundColor White
Write-Host "   - ASGI Application: backend.asgi:application" -ForegroundColor White
Write-Host "   - WebSocket Support: ✅ Enabled" -ForegroundColor Green
Write-Host ""

# Check if we're in the backend directory
if (-not (Test-Path ".\manage.py")) {
    Write-Host "❌ Error: This script must be run from the backend directory" -ForegroundColor Red
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "   Expected: D:\Deen Bridge\Project\backend" -ForegroundColor Yellow
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
Write-Host "🌐 Starting server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Start Daphne
daphne -b 0.0.0.0 -p 8000 backend.asgi:application

