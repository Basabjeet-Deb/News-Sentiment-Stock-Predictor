@echo off
echo ========================================
echo Starting Stock AI Chatbot Web Service
echo ========================================
echo.
echo Chatbot API will run on: http://localhost:8001
echo Web UI will be available at: http://localhost:8002/chat_ui.html
echo.
echo Press Ctrl+C to stop
echo.

start /B python web_chatbot.py
timeout /t 2 /nobreak >nul
start /B python -m http.server 8002

echo.
echo ✅ Chatbot is running!
echo.
echo Open your browser and go to:
echo http://localhost:8002/chat_ui.html
echo.

pause
