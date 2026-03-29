"""
Configuration file for News Sentiment Stock Predictor
Store your API keys and settings here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# API KEYS (Get from respective websites)
# =============================================================================

# NewsAPI: https://newsapi.org/ (100 requests/day free)
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', 'YOUR_NEWSAPI_KEY_HERE')

# Alpha Vantage: https://www.alphavantage.co/ (25 requests/day free)
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'YOUR_ALPHA_VANTAGE_KEY_HERE')

# Finnhub: https://finnhub.io/ (60 calls/minute free)
FINNHUB_KEY = os.getenv('FINNHUB_KEY', 'YOUR_FINNHUB_KEY_HERE')

# Marketaux: https://www.marketaux.com/ (100 requests/day free)
MARKETAUX_KEY = os.getenv('MARKETAUX_KEY', 'YOUR_MARKETAUX_KEY_HERE')

# Bing News - DISCONTINUED (Microsoft ended free tier)
# BING_NEWS_KEY = os.getenv('BING_NEWS_KEY', 'YOUR_BING_NEWS_KEY_HERE')

# =============================================================================
# STOCKS TO TRACK
# =============================================================================

# =============================================================================
# STOCKS TO TRACK - Expanded to 500+ stocks
# =============================================================================

# Download S&P 500 list or use major stocks across sectors
STOCK_TICKERS = [
    # Tech Giants (FAANG+)
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'INTC', 'AMD', 'CRM', 'ORCL', 'ADBE', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'INTU', 'NOW',
    
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT', 'SCHW', 'BLK', 'SPGI', 'AXP', 'DFS', 'SYF',
    
    # Payment/Fintech
    'V', 'MA', 'PYPL', 'SQ', 'COIN',
    
    # Defense/Aerospace (impacted by army/military news)
    'LMT', 'RTX', 'BA', 'NOC', 'GD', 'LHX', 'HII', 'TXT',
    
    # Energy & Oil (impacted by oil/commodity news)
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL', 'BKR', 'DVN', 'FANG', 'HES', 'MRO',
    
    # Gold/Mining (impacted by gold/commodity news)
    'NEM', 'GOLD', 'FCX', 'AEM', 'WPM', 'FNV',
    
    # Retail & Consumer
    'WMT', 'TGT', 'COST', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'BKNG', 'CMG', 'YUM', 'DG', 'ROST', 'TJX',
    
    # Healthcare & Pharma
    'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'LLY', 'BMY', 'AMGN', 'GILD', 'CVS', 'CI', 'ANTM',
    
    # Industrials
    'CAT', 'DE', 'GE', 'HON', 'UPS', 'UNP', 'MMM', 'EMR', 'ITW', 'ETN',
    
    # Consumer Goods
    'PG', 'KO', 'PEP', 'PM', 'MO', 'CL', 'EL', 'KMB', 'GIS', 'K',
    
    # Telecom
    'T', 'VZ', 'TMUS',
    
    # Automotive
    'F', 'GM', 'RIVN', 'LCID',
    
    # Semiconductors
    'TSM', 'ASML', 'MU', 'AMAT', 'LRCX', 'KLAC', 'MCHP', 'ADI', 'NXPI',
    
    # Cloud/Software
    'MSFT', 'AMZN', 'GOOGL', 'SNOW', 'DDOG', 'NET', 'MDB', 'TEAM', 'ZS', 'CRWD',
    
    # E-commerce
    'AMZN', 'SHOP', 'EBAY', 'ETSY', 'W',
    
    # Media & Entertainment
    'DIS', 'CMCSA', 'NFLX', 'PARA', 'WBD',
    
    # Real Estate
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL', 'DLR', 'AVB',
    
    # Utilities
    'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL',
    
    # Crypto-related
    'COIN', 'MSTR', 'MARA', 'RIOT',
]

# Remove duplicates and sort
STOCK_TICKERS = sorted(list(set(STOCK_TICKERS)))

# =============================================================================
# TOPICS TO TRACK (for news that impacts stocks broadly)
# =============================================================================

NEWS_TOPICS = [
    # Commodities
    'gold', 'silver', 'oil', 'natural gas', 'commodities',
    
    # Defense & Geopolitics
    'military', 'defense', 'army', 'war', 'geopolitics',
    
    # Economic Indicators
    'inflation', 'interest rates', 'federal reserve', 'GDP', 'unemployment',
    
    # Crypto (impacts tech stocks)
    'bitcoin', 'cryptocurrency', 'ethereum',
    
    # Technology
    'artificial intelligence', 'AI', 'semiconductors', 'cloud computing',
    
    # Market General
    'stock market', 'wall street', 'nasdaq', 'dow jones', 'S&P 500',
]

# =============================================================================
# SENTIMENT THRESHOLDS
# =============================================================================

SENTIMENT_THRESHOLDS = {
    'very_positive': 0.5,    # Score >= 0.5
    'positive': 0.05,         # Score >= 0.05
    'neutral': -0.05,         # Score between -0.05 and 0.05
    'negative': -0.5,         # Score <= -0.05
    'very_negative': -0.5,    # Score <= -0.5
}

# =============================================================================
# PREDICTION SETTINGS
# =============================================================================

PREDICTION_WEIGHTS = {
    'stock_specific_news': 0.5,    # Weight for news about the stock itself
    'sector_news': 0.2,             # Weight for sector/industry news
    'general_market': 0.15,         # Weight for general market sentiment
    'commodities': 0.1,             # Weight for commodity news (gold, oil)
    'geopolitics': 0.05,            # Weight for military/defense/geopolitics
}

# Recommendation thresholds
RECOMMENDATION_THRESHOLDS = {
    'strong_buy': 0.4,
    'buy': 0.15,
    'hold': -0.15,
    'sell': -0.4,
    'strong_sell': -0.4,
}

# =============================================================================
# DATA SETTINGS
# =============================================================================

# How many days of historical news to fetch
HISTORICAL_DAYS = 7

# Maximum articles per source per request
MAX_ARTICLES_PER_SOURCE = 100  # Increased from 50

# Number of API calls per batch (to get more news)
API_BATCH_SIZE = 20  # Fetch more stocks per API call

# Cache expiry (minutes)
CACHE_EXPIRY_MINUTES = 30

# Data files
DATA_DIR = 'data'
NEWS_CSV = f'{DATA_DIR}/news.csv'
SENTIMENT_CSV = f'{DATA_DIR}/sentiment.csv'
PREDICTIONS_CSV = f'{DATA_DIR}/predictions.csv'
STOCKS_CSV = f'{DATA_DIR}/stocks.csv'

# =============================================================================
# API RATE LIMITS (requests per minute)
# =============================================================================

RATE_LIMITS = {
    'newsapi': 5,           # Conservative to stay under daily limit
    'alphavantage': 2,      # Very limited on free tier
    'finnhub': 50,          # 60/min but being conservative
    'marketaux': 5,         # Conservative for daily limit
    'yahoo': 30,            # Scraping, can be more aggressive
}

# =============================================================================
# API ENDPOINTS
# =============================================================================

API_ENDPOINTS = {
    'newsapi': 'https://newsapi.org/v2/everything',
    'alphavantage': 'https://www.alphavantage.co/query',
    'finnhub': 'https://finnhub.io/api/v1/company-news',
    'marketaux': 'https://api.marketaux.com/v1/news/all',
}
