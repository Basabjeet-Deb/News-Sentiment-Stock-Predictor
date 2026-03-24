# Stock Predictor - AI-Powered Stock Analysis

News sentiment-based stock prediction system with distributed computing support.

## Features

✅ **AI-Powered Predictions** - Sentiment analysis on news articles  
✅ **10 Major Stocks** - AAPL, MSFT, GOOGL, TSLA, AMZN, NVDA, META, JPM, V, WMT  
✅ **Modern Dashboard** - Beautiful web interface with charts  
✅ **Distributed Computing** - Cluster support for parallel processing  
✅ **RESTful API** - Scalable FastAPI backend  

## Project Structure

```
├── backend/           # FastAPI backend
│   └── api.py        # REST API server
├── frontend/          # Web dashboard
│   ├── index.html    # Main page
│   ├── style.css     # Styles
│   └── app.js        # JavaScript
├── scripts/           # Data processing
│   ├── fetch_prototype_data.py
│   ├── fetch_targeted_news.py
│   ├── analyze_prototype.py
│   └── run_prototype.py
├── cluster/           # Distributed computing
│   ├── cluster_master.py
│   ├── cluster_worker.py
│   └── distributed_analyze.py
├── data/              # Data files
├── docs/              # Documentation
└── config.py          # Configuration

```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Collect Data

```bash
python scripts/run_prototype.py
```

This will:
- Fetch stock data for 10 major stocks (1 year history)
- Scrape targeted news articles from multiple sources
- Analyze sentiment and generate predictions
- Save results to `data/` folder

### 3. Start Application

**Option A - Automatic (Windows):**
```bash
start_app.bat
```

**Option B - Manual:**

Terminal 1 - Start Backend:
```bash
cd backend
python api.py
```

Terminal 2 - Open Frontend:
```bash
# Open frontend/index.html in your browser
start frontend/index.html
```

Or simply double-click `frontend/index.html`

### 4. Access the Application

- **Frontend Dashboard**: `frontend/index.html` (opens in browser)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Endpoints**: http://localhost:8000/api/

### 5. View Results

The dashboard shows:
- 📊 Real-time statistics (stocks, signals, news count)
- 📈 Interactive charts (recommendations, sentiment analysis)
- 💹 Stock predictions with BUY/SELL/HOLD recommendations
- 📰 Latest news feed with sentiment scores
- 🎯 Confidence scores for each prediction

## API Endpoints

Base URL: `http://localhost:8000/api`

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/stocks` | GET | List all stocks with current prices | `curl http://localhost:8000/api/stocks` |
| `/api/predictions` | GET | Get all predictions | `curl http://localhost:8000/api/predictions` |
| `/api/prediction/{ticker}` | GET | Get specific stock prediction | `curl http://localhost:8000/api/prediction/AAPL` |
| `/api/news` | GET | Get news articles (optional: ?ticker=AAPL&limit=20) | `curl http://localhost:8000/api/news?ticker=AAPL` |
| `/api/stats` | GET | System statistics | `curl http://localhost:8000/api/stats` |
| `/api/chart/{ticker}` | GET | Historical price data for charts | `curl http://localhost:8000/api/chart/AAPL?days=30` |
| `/api/refresh` | POST | Refresh data in background | `curl -X POST http://localhost:8000/api/refresh` |

**Interactive API Documentation**: http://localhost:8000/docs

### Example API Calls

**Get all predictions:**
```bash
curl http://localhost:8000/api/predictions
```

**Get specific stock:**
```bash
curl http://localhost:8000/api/prediction/AAPL
```

**Get news for Tesla:**
```bash
curl http://localhost:8000/api/news?ticker=TSLA&limit=10
```

**Get system stats:**
```bash
curl http://localhost:8000/api/stats
```

## Distributed Computing

For cluster deployment, see [docs/DISTRIBUTED-DEMO.md](docs/DISTRIBUTED-DEMO.md)

### Quick Cluster Setup

**Master Node:**
```bash
python cluster/cluster_master.py
```

**Worker Nodes:**
```bash
python cluster/cluster_worker.py
```

**Run Analysis:**
```bash
python cluster/distributed_analyze.py
```

## Configuration

Edit `config.py` to customize:
- Target stocks
- News sources
- Sentiment thresholds
- Historical data range

## Screenshots

### Dashboard
- Real-time stock predictions
- Sentiment analysis charts
- News feed with sentiment scores

### Predictions
- BUY/SELL/HOLD recommendations
- Confidence scores
- Price predictions

## Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- Pandas - Data processing
- VADER - Sentiment analysis
- yfinance - Stock data

**Frontend:**
- Bootstrap 5 - UI framework
- Chart.js - Data visualization
- Font Awesome - Icons

**Distributed:**
- Custom master-worker architecture
- HTTP-based communication
- Parallel processing

## Development

### Run Backend Only
```bash
cd backend
python api.py
```

### Run Data Collection Only
```bash
python scripts/run_prototype.py
```

### Run Distributed Analysis
```bash
python cluster/distributed_analyze.py
```

## Data Files

Generated in `data/` folder:
- `prototype_stocks.csv` - Stock price data
- `prototype_news.csv` - News articles
- `sentiment_analysis.csv` - Sentiment scores
- `predictions.csv` - Stock predictions

## Requirements

- Python 3.11+
- Internet connection (for data fetching)
- Modern web browser

## License

MIT

## Authors

Basabjeet Deb

## Acknowledgments

- VADER Sentiment Analysis
- Yahoo Finance API
- News sources: CNBC, Yahoo Finance, Google News
