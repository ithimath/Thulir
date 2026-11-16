# THULIR Platform Launcher (PowerShell)
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "              THULIR PLATFORM LAUNCHER" -ForegroundColor Cyan
Write-Host "  Student Early-Warning and Decision Support System" -ForegroundColor DarkCyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; & 'backend\.venv\Scripts\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host " Both services launched!" -ForegroundColor Green
Write-Host " - Frontend Portal: http://localhost:5173" -ForegroundColor White
Write-Host " - Backend API:     http://127.0.0.1:8000" -ForegroundColor White
Write-Host ""
Write-Host " Default Demo Accounts:" -ForegroundColor Gray
Write-Host " - Admin:      admin      / Password123!" -ForegroundColor Gray
Write-Host " - Teacher:    teacher    / Password123!" -ForegroundColor Gray
Write-Host " - Counsellor: counsellor / Password123!" -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
