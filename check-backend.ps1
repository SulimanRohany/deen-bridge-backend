# Script to check if backend server is running
Write-Host "Checking backend server status..." -ForegroundColor Cyan
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health/" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend server is RUNNING!" -ForegroundColor Green
        Write-Host "   Status: $($response.StatusCode)" -ForegroundColor White
        Write-Host "   Response: $($response.Content)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Backend server is NOT running or not accessible" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start the backend server, run:" -ForegroundColor Cyan
    Write-Host "   cd backend" -ForegroundColor White
    Write-Host "   python manage.py runserver 8000" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the provided script:" -ForegroundColor Cyan
    Write-Host "   .\START_BACKEND.ps1" -ForegroundColor White
}


