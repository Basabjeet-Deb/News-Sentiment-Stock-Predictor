# 🤖 Stock AI Chatbot

An intelligent chatbot that answers questions about stock predictions, market sentiment, and news analysis.

## Features

- 📊 Stock information queries (price, recommendation, confidence)
- 📰 News analysis for specific stocks
- 🎯 Top buy/sell recommendations
- 💭 Market sentiment overview
- 📈 Statistics and data insights

## Quick Start

### Option 1: Command Line Interface

```bash
cd chatbot
python chatbot.py
```

Then ask questions like:
- "Tell me about AAPL"
- "What are the top buy recommendations?"
- "Show news for TSLA"
- "What's the market sentiment?"

### Option 2: Web Interface

1. Start the chatbot API:
```bash
cd chatbot
python web_chatbot.py
```

2. Open `chat_ui.html` in your browser or serve it:
```bash
python -m http.server 8002 --directory .
```

3. Navigate to `http://localhost:8002/chat_ui.html`

## Architecture

```
chatbot/
├── chatbot.py          # Core chatbot logic
├── web_chatbot.py      # FastAPI web service
├── chat_ui.html        # Web interface
└── README.md           # This file
```

## API Endpoints

### POST /chat
Send a question and get an answer.

**Request:**
```json
{
  "question": "What are the top buy recommendations?"
}
```

**Response:**
```json
{
  "answer": "🚀 Top 5 AI Recommendations:\n\n1. AAPL - STRONG BUY...",
  "timestamp": "2026-04-02T10:30:00"
}
```

### GET /health
Check chatbot status.

**Response:**
```json
{
  "status": "healthy",
  "predictions_loaded": 166,
  "news_loaded": 995
}
```

## Example Questions

### Stock Information
- "Tell me about AAPL"
- "What's the price of TSLA?"
- "Show me info on MSFT"

### News Queries
- "Show news for AAPL"
- "What's the latest on GOOGL?"

### Recommendations
- "What are the top buy recommendations?"
- "Show me top picks"
- "Best stocks to buy?"

### Market Analysis
- "What's the market sentiment?"
- "How's the market looking?"
- "Is the market bullish or bearish?"

### Statistics
- "How many stocks are you tracking?"
- "How many news articles?"

## Integration with Main App

The chatbot can be integrated into the main dashboard by:

1. Adding a chat widget in the frontend
2. Connecting to the web_chatbot API on port 8001
3. Using the same glassmorphism design

## Requirements

- Python 3.8+
- pandas
- fastapi (for web version)
- uvicorn (for web version)

Install dependencies:
```bash
pip install pandas fastapi uvicorn
```

## Data Sources

The chatbot reads from:
- `../data/predictions.csv` - Stock predictions
- `../data/news_analyzed.csv` - Analyzed news articles

Make sure to run the main pipeline first to generate these files.

## Notes

- Chatbot automatically reloads data on startup
- Supports natural language queries
- Case-insensitive ticker matching
- Formatted responses with emojis for better readability
- Web UI uses glassmorphism design matching the main dashboard
