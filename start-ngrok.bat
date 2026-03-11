@echo off
echo ============================================================
echo STARTING NGROK TUNNEL
echo ============================================================
echo.
echo Exposing Docker master (localhost:5000) to the internet...
echo.
echo IMPORTANT: Keep this terminal open!
echo.
ngrok http 5000
