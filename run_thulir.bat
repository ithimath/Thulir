@echo off
echo ========================================================
echo               THULIR PLATFORM LAUNCHER
echo   Student Early-Warning and Decision Support System
echo ========================================================
echo.

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "THULIR Backend (Port 8000)" cmd /k "cd /d "%~dp0" && backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Vite Frontend on http://localhost:5173...
start "THULIR Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo  Both services launched in separate windows!
echo  - Frontend Portal: http://localhost:5173
echo  - Backend API:     http://127.0.0.1:8000
echo.
echo  Default Demo Accounts:
echo  - Admin:      admin      / Password123!
echo  - Teacher:    teacher    / Password123!
echo  - Counsellor: counsellor / Password123!
echo ========================================================
echo.
pause
