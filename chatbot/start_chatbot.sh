#!/bin/bash

echo "========================================"
echo "Starting Stock AI Chatbot Web Service"
echo "========================================"
echo ""
echo "Chatbot API will run on: http://localhost:8001"
echo "Web UI will be available at: http://localhost:8002/chat_ui.html"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start chatbot API
python web_chatbot.py &
CHATBOT_PID=$!

# Wait for API to start
sleep 2

# Start web server
python -m http.server 8002 &
SERVER_PID=$!

echo ""
echo "✅ Chatbot is running!"
echo ""
echo "Open your browser and go to:"
echo "http://localhost:8002/chat_ui.html"
echo ""

# Wait for user interrupt
trap "kill $CHATBOT_PID $SERVER_PID; exit" INT
wait
