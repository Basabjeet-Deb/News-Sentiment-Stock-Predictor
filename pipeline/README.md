# Stock Prediction Pipeline

This folder contains the complete data pipeline for stock prediction.

## Pipeline Components

### 1. News Scraping
- **`news_spider.py`** - Scrapy spider that scrapes 5000+ articles in 30 seconds
  - Sources: Finviz, MarketWatch, Seeking Alpha, Reuters, Bloomberg, Investing.com
  - Handles 100+ stock tickers
  - Outputs to `data/scraped_news.json`

### 2. News Fetching & Processing
- **`news_fetcher.py`** - Main news fetcher orchestrator
  - Runs Scrapy spider
  - Removes fuzzy duplicates (85% similarity threshold)
  - Filters irrelevant content
  - Analyzes causal impacts

### 3. Sentiment Analysis
- **`sentiment_analyzer.py`** - Advanced sentiment analysis
  - VADER sentiment scoring
  - Relevance filtering (removes non-financial news)
  - Impact level classification (high/medium/macro/low)
  - Fuzzy duplicate detection
  - Outputs sentiment scores for each article

### 4. Impact Analysis
- **`impact_analyzer.py`** - Causal reasoning engine
  - Predicts which stocks will be affected by news
  - Understands sector relationships
  - Calculates intelligent confidence scores (40-95%)
  - Examples:
    - "Oil ban" → Oil exporters DOWN, Alternative suppliers UP
    - "FDA approval" → Pharma company UP, Competitors DOWN
    - "Interest rate rise" → Banks UP, Real estate DOWN

### 5. Price Fetching
- **`price_fetcher.py`** - Real-time stock price data
  - Fetches current prices from Yahoo Finance
  - Historical data with multiple periods (1M, 3M, 6M, 1Y, 2Y, 5Y)
  - OHLCV data for charting
  - Handles 550+ stocks

### 6. ML Prediction
- **`ml_predictor.py`** - Ensemble ML model
  - Trains 6 models: Logistic Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM, SVM
  - Creates ensemble from top 3 performers
  - Feature engineering (19 features)
  - Generates buy/sell/hold recommendations
  - Outputs predictions with confidence scores

### 7. Pipeline Orchestrator
- **`run_pipeline.py`** - Main pipeline runner
  - Runs all components in sequence
  - Handles errors gracefully
  - Saves results to CSV files

## Pipeline Flow

```
1. News Scraping (news_spider.py)
   ↓
   5000+ raw articles
   ↓
2. News Processing (news_fetcher.py)
   ↓
   Deduplicated & filtered articles
   ↓
3. Sentiment Analysis (sentiment_analyzer.py)
   ↓
   Articles with sentiment scores
   ↓
4. Impact Analysis (impact_analyzer.py)
   ↓
   Predicted stock impacts
   ↓
5. Price Fetching (price_fetcher.py)
   ↓
   Current stock prices
   ↓
6. ML Prediction (ml_predictor.py)
   ↓
   Final recommendations
```

## Usage

### Run Complete Pipeline
```bash
python pipeline/run_pipeline.py
```

### Run Individual Components

**Scrape News:**
```python
from pipeline import run_spider
run_spider(tickers=['AAPL', 'MSFT', 'GOOGL'])
```

**Analyze Sentiment:**
```python
from pipeline import SentimentAnalyzer
analyzer = SentimentAnalyzer()
analyzed = analyzer.analyze_batch(articles)
```

**Predict Impacts:**
```python
from pipeline import ImpactAnalyzer
impact = ImpactAnalyzer()
predictions = impact.analyze_news_impact(article)
```

**Fetch Prices:**
```python
from pipeline import StockPriceFetcher
fetcher = StockPriceFetcher()
prices = fetcher.fetch_current_prices(['AAPL', 'MSFT'])
```

**Run ML Model:**
```python
from pipeline import MLStockPredictor
predictor = MLStockPredictor()
predictor.run_full_pipeline()
```

## Output Files

All outputs are saved to the `data/` folder:

- `data/scraped_news.json` - Raw scraped articles
- `data/news_analyzed.csv` - Analyzed articles with sentiment
- `data/stock_prices.csv` - Current stock prices
- `data/predictions.csv` - Stock predictions
- `data/ml_predictions.csv` - ML model predictions
- `data/ml_confusion_matrix.png` - Model performance visualization
- `data/feature_importance.png` - Feature importance chart
- `data/model_comparison.png` - Model comparison chart

## Performance

- **News Scraping**: 5000+ articles in ~30 seconds
- **Sentiment Analysis**: ~1000 articles/second
- **ML Training**: ~10 seconds for 6 models
- **Total Pipeline**: ~2-3 minutes for complete analysis

## Key Features

1. ✅ **Scrapy-powered** - Fast, scalable web scraping
2. ✅ **Fuzzy deduplication** - Removes similar articles
3. ✅ **Relevance filtering** - Only financial news
4. ✅ **Causal reasoning** - Understands sector impacts
5. ✅ **Ensemble ML** - 6 models stacked for accuracy
6. ✅ **Intelligent confidence** - Varies 40-95% based on factors
7. ✅ **550+ stocks** - Full S&P 500 coverage

## Dependencies

```
scrapy>=2.11.0
vaderSentiment>=3.3.2
yfinance>=0.2.32
pandas>=2.1.0
scikit-learn>=1.3.0
xgboost
lightgbm
```

## Configuration

Edit `config.py` in the root directory to configure:
- Stock tickers to track
- News topics
- Sentiment thresholds
- Prediction weights
- API endpoints
