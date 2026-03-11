@echo off
echo ============================================================
echo STARTING MASTER NODE IN DOCKER
echo ============================================================
echo.
echo Building and starting Docker container...
docker-compose -f docker-compose-master.yml up --build
