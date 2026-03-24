"""
Configuration for Stock Predictor Prototype
Focus on 5-10 major stocks for demonstration
"""

# Target stocks for prototype
TARGET_STOCKS = [
    'AAPL',  # Apple
    'MSFT',  # Microsoft
    'GOOGL', # Google
    'TSLA',  # Tesla
    'AMZN',  # Amazon
    'NVDA',  # NVIDIA
    'META',  # Meta (Facebook)
    'JPM',   # JPMorgan
    'V',     # Visa
    'WMT'    # Walmart
]

# Stock names for display
STOCK_NAMES = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc. (Google)',
    'TSLA': 'Tesla Inc.',
    'AMZN': 'Amazon.com Inc.',
    'NVDA': 'NVIDIA Corporation',
    'META': 'Meta Platforms Inc.',
    'JPM': 'JPMorgan Chase & Co.',
    'V': 'Visa Inc.',
    'WMT': 'Walmart Inc.'
}

# News sources to scrape
NEWS_SOURCES = {
    'yahoo_finance': 'https://finance.yahoo.com/topic/stock-market-news/',
    'cnbc': 'https://www.cnbc.com/markets/',
    'marketwatch': 'https://www.marketwatch.com/latest-news',
    'reuters': 'https://www.reuters.com/business/'
}

# Date range for historical data
HISTORICAL_DAYS = 365  # 1 year of data

# Sentiment thresholds
SENTIMENT_POSITIVE = 0.3
SENTIMENT_NEGATIVE = -0.3

# Prediction confidence thresholds
CONFIDENCE_HIGH = 0.7
CONFIDENCE_MEDIUM = 0.5
CONFIDENCE_LOW = 0.3
