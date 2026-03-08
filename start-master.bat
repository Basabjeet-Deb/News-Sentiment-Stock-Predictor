@echo off
echo ======================================
echo Starting MASTER Node
echo ======================================
echo.

echo Building Docker image...
docker-compose -f docker-compose-master.yml build

echo.
echo Starting master node...
docker-compose -f docker-compose-master.yml up -d

echo.
echo ======================================
echo Master Node Started!
echo ======================================
echo.
echo Dashboard: http://localhost:5000
echo.
echo Share this with your teammates:
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    goto :found
)
:found
echo Worker Registration URL: http://%IP:~1%:5000/register
echo.
echo Your teammates should:
echo 1. Update MASTER_URL in worker_node.py to: http://%IP:~1%:5000
echo 2. Run: start-worker.bat
echo.
echo ======================================
echo.
echo View logs: docker-compose -f docker-compose-master.yml logs -f
echo Stop: docker-compose -f docker-compose-master.yml down
echo.
pause
