# Start Django Backend Server
Write-Host "Starting Django Backend Server..." -ForegroundColor Green
Write-Host "Database: SQLite" -ForegroundColor Yellow
Write-Host "Server will run on: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python manage.py runserver 8000

