@echo off
echo ============================================================
echo STOCK PREDICTOR - STARTING APPLICATION
echo ============================================================
echo.
echo Starting backend API server...
echo.

cd backend
start "Backend API" cmd /k "python api.py"
cd ..

timeout /t 3 /nobreak >nul

echo.
echo Backend started on http://localhost:8000
echo.
echo Opening frontend in browser...
echo.

start "" "frontend/index.html"

echo.
echo ============================================================
echo APPLICATION RUNNING
echo ============================================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: Open frontend/index.html in browser
echo.
echo Press any key to stop the backend...
pause >nul

taskkill /FI "WINDOWTITLE eq Backend API*" /T /F
