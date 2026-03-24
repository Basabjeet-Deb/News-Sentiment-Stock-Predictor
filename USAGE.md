# Stock Predictor - Usage Guide

Complete guide to using the Stock Predictor application.

## Table of Contents
1. [Installation](#installation)
2. [Data Collection](#data-collection)
3. [Starting the Application](#starting-the-application)
4. [Using the Dashboard](#using-the-dashboard)
5. [API Usage](#api-usage)
6. [Distributed Computing](#distributed-computing)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites
- Python 3.11 or higher
- Internet connection
- Modern web browser (Chrome, Firefox, Edge)

### Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (Backend API)
- Pandas & NumPy (Data processing)
- VADER Sentiment (Sentiment analysis)
- yfinance (Stock data)
- BeautifulSoup4 (Web scraping)
- Flask & Requests (Cluster communication)

---

## Data Collection

### Step 1: Run Data Pipeline

```bash
python scripts/run_prototype.py
```

**What it does:**
1. Fetches 1 year of historical stock data for 10 major stocks
2. Scrapes latest news articles from multiple sources
3. Analyzes sentiment using VADER
4. Generates predictions with BUY/SELL/HOLD recommendations

**Output files** (saved in `data/` folder):
- `prototype_stocks.csv` - Stock price data (2,510 records)
- `prototype_news.csv` - News articles with metadata
- `sentiment_analysis.csv` - Sentiment scores for each article
- `predictions.csv` - Final predictions with recommendations

**Time:** ~2-3 minutes

---

## Starting the Application

### Method 1: Automatic Start (Windows)

```bash
start_app.bat
```

This will:
- Start backend API on port 8000
- Open frontend dashboard in browser
- Keep backend running in background

### Method 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python api.py
```

**Terminal 2 - Frontend:**
```bash
start frontend/index.html
```

Or double-click `frontend/index.html`

### Verify Backend is Running

Open: http://localhost:8000

You should see:
```json
{
  "name": "Stock Predictor API",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Using the Dashboard

### Access Dashboard

Open `frontend/index.html` in your browser

### Dashboard Sections

#### 1. Dashboard (Home)
- **Stats Cards**: Total stocks, buy/sell signals, news count
- **Charts**: 
  - Recommendations distribution (pie chart)
  - Sentiment analysis (bar chart)
- **Top Predictions**: Best predictions sorted by confidence

#### 2. Predictions
- Complete list of all stock predictions
- Shows:
  - Current price vs predicted price
  - Predicted change percentage
  - Sentiment score and label
  - News article count
  - Confidence score (0-1)
  - Recommendation (BUY/SELL/HOLD)

#### 3. News Feed
- Latest news articles
- Filtered by stock ticker
- Shows sentiment badges (Positive/Negative/Neutral)
- Source and timestamp

#### 4. Stocks
- Grid view of all 10 stocks
- Current price
- 24-hour change percentage
- Click to view details

### Refresh Data

Click "Refresh Data" button in sidebar to reload latest data from backend.

---

## API Usage

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### 1. Get All Stocks
```bash
curl http://localhost:8000/api/stocks
```

**Response:**
```json
[
  {
    "ticker": "AAPL",
    "company": "Apple Inc.",
    "current_price": 251.49,
    "change_24h": -0.52
  },
  ...
]
```

#### 2. Get All Predictions
```bash
curl http://localhost:8000/api/predictions
```

**Response:**
```json
[
  {
    "ticker": "AAPL",
    "company": "Apple Inc.",
    "current_price": 251.49,
    "predicted_price": 252.50,
    "predicted_change_pct": 0.40,
    "sentiment": "Positive",
    "sentiment_score": 0.450,
    "news_count": 15,
    "confidence": 0.85,
    "recommendation": "BUY",
    "trend": "Uptrend"
  },
  ...
]
```

#### 3. Get Specific Stock Prediction
```bash
curl http://localhost:8000/api/prediction/AAPL
```

#### 4. Get News Articles
```bash
# All news
curl http://localhost:8000/api/news

# Filter by ticker
curl http://localhost:8000/api/news?ticker=TSLA

# Limit results
curl http://localhost:8000/api/news?ticker=TSLA&limit=5
```

#### 5. Get System Statistics
```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "total_stocks": 10,
  "total_predictions": 10,
  "total_news": 6,
  "last_updated": "2026-03-24T20:30:00",
  "buy_signals": 1,
  "sell_signals": 9,
  "hold_signals": 0
}
```

#### 6. Get Chart Data
```bash
curl http://localhost:8000/api/chart/AAPL?days=30
```

#### 7. Refresh Data
```bash
curl -X POST http://localhost:8000/api/refresh
```

### Interactive API Docs

Open: http://localhost:8000/docs

Features:
- Try out all endpoints
- See request/response schemas
- Test with different parameters

---

## Distributed Computing

For running on college cluster, see [docs/DISTRIBUTED-DEMO.md](docs/DISTRIBUTED-DEMO.md)

### Quick Cluster Setup

**1. Start Master (One machine):**
```bash
python cluster/cluster_master.py
```

**2. Start Workers (Other machines):**

Edit `cluster/cluster_worker.py` line 15:
```python
MASTER_URL = 'http://MASTER_IP:8000'  # Replace with master IP
```

Then:
```bash
python cluster/cluster_worker.py
```

**3. Run Distributed Analysis:**

Edit `cluster/distributed_analyze.py` line 8:
```python
MASTER_URL = "http://MASTER_IP:8000"  # Replace with master IP
```

Then:
```bash
python cluster/distributed_analyze.py
```

---

## Troubleshooting

### Backend Not Starting

**Error: Port 8000 already in use**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <process_id> /F
```

**Error: Module not found**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Not Loading Data

**Check backend is running:**
```bash
curl http://localhost:8000
```

**Check browser console:**
- Press F12 in browser
- Look for errors in Console tab
- Common issue: CORS errors (backend should handle this)

**Clear browser cache:**
- Press Ctrl+Shift+Delete
- Clear cached images and files

### No News Articles

News scraping may fail due to:
- Website structure changes
- Rate limiting
- Network issues

**Solution:**
- Run scraper again: `python scripts/fetch_targeted_news.py`
- Check different news sources
- Use existing GDELT data: `data/gdelt_english_news.csv`

### Predictions Not Accurate

This is a prototype using simple sentiment analysis. For better predictions:
- Collect more news articles
- Use longer historical data
- Implement machine learning models
- Add more technical indicators

### Cluster Workers Not Connecting

**Check master is accessible:**
```bash
curl http://MASTER_IP:8000
```

**Check firewall:**
- Allow ports 8000 (master) and 5000 (workers)
- On Windows: `netsh advfirewall firewall add rule name="Stock Predictor" dir=in action=allow protocol=TCP localport=8000`

**Verify worker configuration:**
- Ensure `MASTER_URL` is correct in `cluster_worker.py`
- Check worker can ping master: `ping MASTER_IP`

---

## Advanced Usage

### Custom Stock List

Edit `config.py`:
```python
TARGET_STOCKS = [
    'AAPL',
    'MSFT',
    'YOUR_STOCK',
    # Add more...
]

STOCK_NAMES = {
    'YOUR_STOCK': 'Your Company Name',
    # Add more...
}
```

### Change Historical Data Range

Edit `config.py`:
```python
HISTORICAL_DAYS = 730  # 2 years instead of 1
```

### Add News Sources

Edit `scripts/fetch_targeted_news.py` and add new scraper methods.

### Customize Sentiment Thresholds

Edit `config.py`:
```python
SENTIMENT_POSITIVE = 0.5  # More strict
SENTIMENT_NEGATIVE = -0.5
```

---

## Support

For issues or questions:
1. Check this guide
2. See [README.md](README.md)
3. Check [docs/](docs/) folder
4. Review code comments

---

## Next Steps

1. ✅ Collect data
2. ✅ Start application
3. ✅ View dashboard
4. 📊 Analyze predictions
5. 🎯 Make investment decisions (at your own risk!)
6. 🔄 Refresh data daily for latest predictions

**Remember:** This is a prototype for educational purposes. Always do your own research before making investment decisions!
