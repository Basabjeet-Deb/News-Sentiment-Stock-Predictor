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
- Fetch stock data for 10 major stocks
- Scrape targeted news articles
- Analyze sentiment and generate predictions

### 3. Start Application

```bash
start_app.bat
```

Or manually:

**Terminal 1 - Backend:**
```bash
cd backend
python api.py
```

**Terminal 2 - Frontend:**
Open `frontend/index.html` in your browser

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stocks` | GET | List all stocks |
| `/api/predictions` | GET | Get all predictions |
| `/api/prediction/{ticker}` | GET | Get specific prediction |
| `/api/news` | GET | Get news articles |
| `/api/stats` | GET | System statistics |
| `/api/refresh` | POST | Refresh data |

API Documentation: http://localhost:8000/docs

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
