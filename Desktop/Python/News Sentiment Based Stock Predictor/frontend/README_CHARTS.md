# Stock Charts Feature

## Quick Start

1. Start the server:
```bash
python -m uvicorn app.main:app --reload
```

2. Open http://localhost:8000

3. Click any stock ticker to see interactive charts!

## What You Get

### 📈 Line Chart
- Clean price trend visualization
- Perfect for quick overview
- Shows closing prices over time

### 📊 Candlestick Chart
- Professional trading view
- Shows Open, High, Low, Close (OHLC)
- Green = price up, Red = price down
- See intraday volatility

### ⏱️ Time Periods
- 1D - Intraday view
- 5D - Week view
- 1M - Month view (default)
- 3M - Quarter view
- 6M - Half year
- 1Y - Full year

### 📰 Related News
- See news articles for the stock
- Sentiment scores included
- Recent articles only

## Click Anywhere!

Stock tickers are clickable in:
- Dashboard (top picks, gainers, losers)
- Predictions table
- Stocks table

## Chart Controls

- **Hover**: See exact values
- **Scroll**: Zoom in/out
- **Drag**: Pan left/right
- **Buttons**: Switch chart type or period

## Technology

- **Lightweight Charts** by TradingView
- Fast and responsive
- Professional-grade charting
- Dark theme matching your app

Enjoy! 🎉
