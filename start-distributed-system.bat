@echo off
echo ============================================================
echo DISTRIBUTED COMPUTING SYSTEM - QUICK START
echo ============================================================
echo.
echo This will start:
echo   - 1 Master node (port 8000)
echo   - 3 Worker nodes
echo.
echo Press Ctrl+C to stop all services
echo.
pause

docker-compose -f docker-compose-distributed.yml up --build
