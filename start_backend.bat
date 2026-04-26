@echo off
echo ============================================================
echo  Starting News Sentiment Stock Predictor Backend
echo ============================================================
echo.

REM Load environment variables from .env file
if exist .env (
    echo [INFO] Loading environment variables from .env file
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
    echo [INFO] Environment variables loaded
) else (
    echo [WARNING] .env file not found - using defaults
    echo [WARNING] Create .env file from .env.example for custom configuration
)

echo.
echo [INFO] Starting FastAPI server on http://localhost:8000
echo.

REM Start the backend
python app/main.py

pause
