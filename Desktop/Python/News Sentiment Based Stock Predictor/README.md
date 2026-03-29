# 📈 News Sentiment Based Stock Predictor

> Comprehensive stock prediction system using news sentiment analysis and machine learning for 550+ stocks with distributed computing support

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### Core Functionality
- **Multi-Source News Fetching**: 1000+ articles/day from 7 sources (NewsAPI, Finnhub, Alpha Vantage, Marketaux, Yahoo Finance, Google News, Finviz)
- **Intelligent Sentiment Analysis**: VADER-based sentiment with relevance filtering and impact assessment
- **Real-Time Stock Prices**: Live prices for 550+ stocks with historical data
- **ML-Powered Predictions**: Buy/Hold/Sell recommendations with confidence scores
- **Interactive Charts**: TradingView Lightweight Charts with line and candlestick views
- **REST API**: FastAPI backend with interactive documentation
- **Distributed Computing**: Master-slave cluster architecture for 3x faster processing

### Web Interface
- **Search Functionality**: Natural language search (e.g., "Tesla" → TSLA)
- **Interactive Dashboard**: Top recommendations, gainers, losers
- **Stock Detail Modals**: Click any ticker for charts, news, and predictions
- **Multiple Time Periods**: 1M, 3M, 6M, 1Y, 2Y, 5Y, MAX
- **Animated UI**: Modern design with gradient backgrounds and smooth animations

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip (Python package manager)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Basabjeet-Deb/News-Sentiment-Stock-Predictor.git
cd News-Sentiment-Stock-Predictor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up API keys** (optional but recommended)
```bash
cp .env.example .env
# Edit .env and add your API keys (see API Keys section below)
```

4. **Run the application**

**Option A: Web Interface (Recommended)**
```bash
python -m uvicorn app.main:app --reload
```
Then open http://localhost:8000

**Option B: Pipeline Only**
```bash
python scripts/run_pipeline.py
```

---

## 🔑 API Keys Setup

### Free API Keys (All FREE Tiers!)

#### 1. NewsAPI ⭐ (Easiest - 5 minutes)
- **Sign up**: https://newsapi.org/register
- **Free tier**: 100 requests/day
- **Provides**: General financial and business news

#### 2. Finnhub ⭐ (Best for stocks)
- **Sign up**: https://finnhub.io/register
- **Free tier**: 60 calls/minute
- **Provides**: Company news, market news

#### 3. Alpha Vantage (Has sentiment scores!)
- **Sign up**: https://www.alphavantage.co/support/#api-key
- **Free tier**: 25 requests/day
- **Provides**: News with built-in sentiment analysis

#### 4. Marketaux (Optional - more coverage)
- **Sign up**: https://www.marketaux.com/account/signup
- **Free tier**: 100 requests/day
- **Provides**: Multi-topic financial coverage

### Adding Keys to .env

Edit the `.env` file:
```env
NEWSAPI_KEY=your_newsapi_key_here
FINNHUB_KEY=your_finnhub_key_here
ALPHA_VANTAGE_KEY=your_alphavantage_key_here
MARKETAUX_KEY=your_marketaux_key_here
```

### No API Keys? No Problem!

Run without API keys using free sources:
```bash
python scripts/free_news_fetcher.py
```

This uses Yahoo Finance RSS + Google News (no keys required, ~100 articles/day)

---

## 📊 How It Works

### Pipeline Flow
```
1. News Fetching (Multi-Source)
   ├─ General Market News → Affects all 550+ stocks
   ├─ Macro Economic News → Affects sectors (gold, oil, inflation)
   ├─ Sector News → Affects groups (tech, finance, defense)
   └─ Stock-Specific News → Top 150 stocks get dedicated coverage

2. Sentiment Analysis
   ├─ Analyze each article with VADER
   ├─ Filter for relevance (removes fluff)
   ├─ Assess impact level (high/medium/macro/low)
   └─ Keep only impactful articles

3. Stock Price Fetching
   └─ Get real-time prices for all 550+ stocks

4. Prediction Generation
   ├─ Sentiment Score (60% weight)
   ├─ Price Momentum (30% weight)
   ├─ News Volume (10% weight)
   └─ Final Recommendation: STRONG BUY / BUY / HOLD / SELL / STRONG SELL
```

### Coverage Strategy

**How we cover 550+ stocks with limited API calls:**

- **General Market News** (50-100 articles): "Stock market", "S&P 500", "Wall Street" → Affects ALL stocks
- **Macro Economic News** (100-150 articles): Inflation, interest rates, GDP, commodities → Affects most stocks
- **Sector News** (50-100 articles): Technology, finance, energy, healthcare → Affects groups of 50-100 stocks
- **Direct Stock Mentions** (200-300 articles): Top 150 stocks by market cap → Direct company news

**Result**: Every stock is covered either directly or via sector/macro news

---

## 🎯 Interactive Charts Feature

### What You Can Do

Click on any stock ticker to open an interactive modal with:

- **Real-time price information** with change %
- **Interactive charts**: Switch between line and candlestick views
- **Multiple time periods**: 1M, 3M, 6M, 1Y, 2Y, 5Y, MAX
- **Volume bars**: See trading volume alongside price
- **Stock-specific news**: Recent articles with sentiment scores
- **Prediction details**: Buy/Sell/Hold recommendation with confidence

### Chart Types

**Line Chart** 📈
- Clean price trend visualization
- Great for quick overview
- Smooth curves showing closing prices

**Candlestick Chart** 📊
- OHLC (Open, High, Low, Close) data
- Green candles = price up, Red candles = price down
- Shows intraday volatility
- Professional trading view

### Where to Click

You can click on stocks in:
1. Dashboard page (Top Buy/Sell, Gainers/Losers)
2. Predictions page (any row in table)
3. Stocks page (any row in table)
4. Search results

---

## 🖥️ Distributed Computing (Cluster Mode)

### Two Operating Modes

#### Mode 1: Standalone (Original)
Run everything on one machine:
```bash
python scripts/run_pipeline.py
```
**Time**: ~4 minutes for 550 stocks

#### Mode 2: Distributed Cluster (NEW!)
Run across multiple machines for faster processing:

**Quick Demo (Single Machine):**
```bash
cd cluster
run_cluster_demo.bat    # Windows
# OR
./run_cluster_demo.sh   # Linux/Mac
```

This opens 4 terminals:
- 1 Master node
- 3 Slave nodes

Watch them work together!

**Real Distributed (Multiple Machines):**

**On Master Machine:**
```bash
cd cluster
python master.py --slaves 3 --timeout 30
```

**On Each Slave Machine:**
```bash
cd cluster
python slave.py --master <MASTER_IP> --port 5000
```

### How Cluster Works

1. Master splits 550 stocks into N chunks (e.g., 3 slaves = ~183 stocks each)
2. Each slave processes its assigned stocks independently
3. Slaves send results back to master
4. Master aggregates everything
5. Same output files as standalone mode!

### Performance Comparison

| Mode | Machines | Time | Speedup |
|------|----------|------|---------|
| Standalone | 1 | ~4 min | 1x |
| Cluster (3 slaves) | 3 | ~1.5 min | 3x |
| Cluster (10 slaves) | 10 | ~30 sec | 8x |

### Cluster Architecture

```
┌─────────────┐
│   MASTER    │  (Coordinates work, aggregates results)
│   Node      │
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
   ┌───▼───┐  ┌──▼────┐  ┌──▼────┐  ┌──▼────┐
   │SLAVE 1│  │SLAVE 2│  │SLAVE 3│  │SLAVE N│
   └───────┘  └───────┘  └───────┘  └───────┘
   (Process   (Process   (Process   (Process
    stocks    stocks     stocks     stocks
    1-183)    184-366)   367-550)   ...)
```

### Perfect for College Demo

✅ Shows distributed computing concepts
✅ Master-slave architecture
✅ Network programming with sockets
✅ Parallel processing
✅ Data aggregation
✅ Fault tolerance (falls back to standalone if slaves fail)

---

## 🌐 REST API Endpoints

Start the server:
```bash
python -m uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

### Predictions
- `GET /api/v1/predictions/` - List all predictions (with filters)
- `GET /api/v1/predictions/top` - Top buy recommendations
- `GET /api/v1/predictions/bottom` - Sell candidates
- `GET /api/v1/predictions/summary` - Summary statistics
- `GET /api/v1/predictions/{ticker}` - Prediction for specific stock

### News
- `GET /api/v1/news/` - List analyzed news articles
- `GET /api/v1/news/summary` - News summary by source/ticker
- `GET /api/v1/news/by-ticker/{ticker}` - News for specific stock
- `POST /api/v1/news/analyze` - Analyze custom text sentiment

### Stocks
- `GET /api/v1/stocks/` - Current stock prices
- `GET /api/v1/stocks/summary` - Market summary
- `GET /api/v1/stocks/gainers` - Top gaining stocks
- `GET /api/v1/stocks/losers` - Top losing stocks
- `GET /api/v1/stocks/{ticker}` - Price for specific stock
- `GET /api/v1/stocks/{ticker}/history` - Historical OHLCV data

### Pipeline
- `GET /api/v1/pipeline/status` - Pipeline status
- `POST /api/v1/pipeline/run` - Run full pipeline (background)
- `POST /api/v1/pipeline/quick-update` - Quick refresh

---

## 📂 Project Structure

```
News-Sentiment-Stock-Predictor/
├── app/                           # FastAPI application
│   ├── main.py                    # FastAPI entry point
│   ├── api/v1/                    # API endpoints
│   │   ├── predictions.py         # Predictions endpoints
│   │   ├── news.py                # News endpoints
│   │   ├── stocks.py              # Stocks endpoints (with history)
│   │   └── pipeline.py            # Pipeline control
│   ├── core/                      # Configuration
│   │   ├── config.py              # App configuration
│   │   └── dependencies.py        # Dependency injection
│   ├── services/                  # Business logic
│   │   ├── news_service.py
│   │   ├── prediction_service.py
│   │   ├── price_service.py
│   │   └── sentiment_service.py
│   └── models/                    # Pydantic models
│       ├── news.py
│       ├── prediction.py
│       └── stock.py
├── scripts/                       # Standalone scripts
│   ├── run_pipeline.py            # Main pipeline (RUN THIS!)
│   ├── enhanced_news_fetcher.py   # Multi-source news fetcher
│   ├── sentiment_analyzer.py      # Sentiment + relevance filtering
│   ├── stock_price_fetcher.py     # Real-time stock prices
│   ├── news_aggregator.py         # API-based news fetching
│   ├── free_news_fetcher.py       # Free news (no API keys)
│   ├── ml_predictor.py            # ML prediction model
│   └── backtest.py                # Backtesting engine
├── cluster/                       # Distributed computing
│   ├── master.py                  # Master node coordinator
│   ├── slave.py                   # Worker node
│   ├── run_cluster_demo.bat       # Windows demo launcher
│   └── run_cluster_demo.sh        # Linux/Mac demo launcher
├── frontend/                      # Web interface
│   ├── index.html                 # Main HTML
│   ├── app.js                     # Application logic
│   ├── api.js                     # API client
│   ├── styles.css                 # Styling
│   ├── stock-lookup.js            # Company name → ticker mapping
│   └── ticker-names.js            # Ticker → company name mapping
├── data/                          # Output files
│   ├── news_analyzed.csv          # Analyzed news with sentiment
│   ├── predictions.csv            # Stock predictions
│   ├── stock_prices.csv           # Current stock prices
│   └── ml_predictions.csv         # ML model predictions
├── tests/                         # Test suite
├── config.py                      # Global configuration
├── requirements.txt               # Python dependencies
├── .env                           # Your API keys (don't commit!)
├── .env.example                   # API keys template
└── README.md                      # This file
```

---

## 🎯 Stocks Covered

**Total**: 550+ stocks across all sectors

### Major Sectors
- **Tech Giants**: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
- **Finance & Banks**: JPM, BAC, GS, MS, V, MA, WFC
- **Defense & Aerospace**: LMT, RTX, BA, NOC, GD
- **Energy & Oil**: XOM, CVX, COP, SLB, HAL, OXY
- **Gold & Mining**: GOLD, NEM, FCX, AEM
- **Retail & Consumer**: WMT, TGT, COST, HD, NKE, MCD
- **Healthcare & Pharma**: JNJ, PFE, UNH, ABBV, ABT
- **Semiconductors**: NVDA, AMD, INTC, TSM, AVGO, QCOM
- **Cloud/Software**: CRM, ORCL, ADBE, NOW, SNOW
- **Automotive**: TSLA, F, GM, RIVN
- **Crypto-related**: COIN, MARA, RIOT, MSTR

Full list in `config.py`

---

## 🔍 Search Functionality

### Natural Language Search

Users can search using:
- **Company names**: "Tesla" → TSLA, "Apple" → AAPL
- **Ticker symbols**: "MSFT", "GOOGL"
- **Partial matches**: "Micro" → MSFT, "Alphabet" → GOOGL

### Supported Search Terms

The app includes 200+ company name mappings:
- "Tesla" or "Tesla Motors" → TSLA
- "Apple" → AAPL
- "Microsoft" → MSFT
- "Alphabet" or "Google" → GOOGL
- "Halliburton" → HAL
- "Welltower" → WELL
- And many more...

---

## 📈 Example Output

### Top Recommendations
```
Rank   Ticker   Company              Recommendation   Score     Price      News
---------------------------------------------------------------------------------
1      HAL      Halliburton          STRONG BUY       0.586    $40.42     1 article
2      KO       Coca-Cola            STRONG BUY       0.517    $75.71     1 article
3      LRCX     Lam Research         BUY              0.498    $211.41    1 article
4      WELL     Welltower            BUY              0.454    $195.77    1 article
5      COP      ConocoPhillips       BUY              0.426    $133.80    1 article
```

### Sentiment Display

News articles show intuitive sentiment:
- 🟢 Very Positive (0.5 to 1.0)
- 🟢 Positive (0.1 to 0.5)
- ⚪ Neutral (-0.1 to 0.1)
- 🔴 Negative (-0.5 to -0.1)
- 🔴 Very Negative (-1.0 to -0.5)

---

## 🛠️ Advanced Usage

### Running Individual Components

**Fetch news only:**
```bash
python scripts/enhanced_news_fetcher.py
```

**Analyze sentiment:**
```bash
python scripts/sentiment_analyzer.py
```

**Get stock prices:**
```bash
python scripts/stock_price_fetcher.py
```

**Generate predictions:**
```bash
python scripts/ml_predictor.py
```

### Backtesting

Test prediction accuracy on historical data:
```bash
python scripts/backtest.py
```

### Performance Analysis

Analyze prediction performance:
```bash
python scripts/analyze_performance.py
```

---

## 🎨 UI Features

### Modern Design
- Animated gradient background with moving orbs
- Glass morphism effects with backdrop blur
- Smooth transitions and hover effects
- Responsive design for mobile and desktop

### Interactive Elements
- Click any stock ticker to open detail modal
- Switch between line and candlestick charts
- Change time periods with one click
- Search with natural language
- Loading skeletons for better UX

### Color Coding
- 🟢 Green: Positive sentiment, price gains, buy recommendations
- 🔴 Red: Negative sentiment, price losses, sell recommendations
- ⚪ Gray: Neutral sentiment, hold recommendations

---

## 🔧 Troubleshooting

### Charts not loading?
- Ensure server is running: `python -m uvicorn app.main:app --reload`
- Check browser console for errors
- Verify stock ticker exists in database
- Run pipeline first to generate data

### No news showing?
- Run the pipeline: `python scripts/run_pipeline.py`
- Check API keys in `.env` file
- Try free news fetcher: `python scripts/free_news_fetcher.py`

### Cluster slaves can't connect?
- Check master IP address is correct
- Verify port 5000 is not blocked by firewall
- Ensure master is running before starting slaves
- Increase timeout: `python master.py --timeout 60`

### API keys not working?
- Verify no spaces around `=` in `.env` file
- Check keys are correct (copy-paste again)
- Ensure `.env` file is saved
- Restart the application

---

## 📊 Data Sources

### News Sources (7 total)
1. **NewsAPI**: General financial news (100 req/day)
2. **Finnhub**: Company news (60 calls/min)
3. **Alpha Vantage**: News with sentiment (25 req/day)
4. **Marketaux**: Multi-topic coverage (100 req/day)
5. **Yahoo Finance RSS**: Market news (unlimited)
6. **Google News RSS**: Financial news (unlimited)
7. **Finviz**: Stock-specific news (unlimited scraping)

### Price Data
- **Yahoo Finance (yfinance)**: Real-time and historical stock prices

### Sentiment Analysis
- **VADER**: Valence Aware Dictionary and sEntiment Reasoner

---

## 🚀 Future Enhancements

Potential additions:
- [ ] Technical indicators (MA, RSI, MACD, Bollinger Bands)
- [ ] Real-time updates with WebSocket
- [ ] User accounts and watchlists
- [ ] Email/SMS alerts for recommendations
- [ ] Portfolio tracking
- [ ] More advanced ML models (LSTM, Transformer)
- [ ] Options and derivatives analysis
- [ ] Earnings calendar integration
- [ ] Social media sentiment (Twitter, Reddit)

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 👨‍💻 Author

**Basabjeet Deb**
- GitHub: [@Basabjeet-Deb](https://github.com/Basabjeet-Deb)

---

## 🙏 Acknowledgments

- **NewsAPI, Finnhub, Alpha Vantage, Marketaux** for free API access
- **Yahoo Finance** for reliable stock data
- **TradingView** for the Lightweight Charts library
- **FastAPI** for the excellent web framework
- **VADER Sentiment** for sentiment analysis

---

## 📞 Support

Having issues or questions?
1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Open an issue on GitHub

---

**Built with**: Python, FastAPI, TradingView Lightweight Charts, VADER Sentiment, yfinance, and ❤️

**Last Updated**: March 29, 2026
