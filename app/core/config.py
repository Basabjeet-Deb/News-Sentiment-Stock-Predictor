"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "News Sentiment Stock Predictor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Keys (optional - system works without them)
    # News is collected via web scraping - no API keys needed
    ALPHA_VANTAGE_KEY: Optional[str] = None  # Backup for stock prices
    FMP_API_KEY: Optional[str] = None  # Financial Modeling Prep (optional)
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "*"]
    
    # Data paths - use absolute paths relative to project root
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    NEWS_CSV: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "news_analyzed.csv")
    PREDICTIONS_CSV: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "predictions.csv")
    PRICES_CSV: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "stock_prices.csv")
    
    # Pipeline settings (fetch limit; dedupe+cap may reduce further via PIPELINE_ARTICLE_CAP)
    MAX_ARTICLES: int = 500
    # Hard cap after dedupe before sentiment (RAM budget ~1 GB friendly)
    PIPELINE_ARTICLE_CAP: int = 500
    CACHE_EXPIRY_MINUTES: int = 30
    # Sentiment: vader (default, light) | finbert (needs torch+transformers)
    SENTIMENT_BACKEND: str = "vader"
    FINBERT_BATCH_SIZE: int = 4
    FINBERT_MAX_LENGTH: int = 128
    # Exponential half-life (hours) for ticker-level avg sentiment
    SENTIMENT_HALF_LIFE_HOURS: float = 24.0
    HISTORICAL_DAYS: int = 7
    
    # Rate limits
    ALPHA_VANTAGE_RATE_LIMIT: int = 2  # Backup for stock prices
    YAHOO_RATE_LIMIT: int = 30  # For yfinance stock data
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Stock tickers list - S&P 500 + additional popular stocks
STOCK_TICKERS = [
    # Tech Giants & Software
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'INTC', 
    'AMD', 'CRM', 'ORCL', 'ADBE', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'INTU', 'NOW',
    'SNOW', 'DDOG', 'NET', 'MDB', 'TEAM', 'ZS', 'CRWD', 'PANW', 'FTNT', 'WDAY',
    'ADSK', 'CDNS', 'SNPS', 'UBER', 'LYFT', 'ABNB', 'DASH', 'SPOT', 'RBLX',
    
    # Finance & Banks
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT', 
    'SCHW', 'BLK', 'SPGI', 'AXP', 'DFS', 'SYF', 'MCO', 'CME', 'ICE', 'NDAQ', 'CBOE',
    'AFL', 'ALL', 'AIG', 'MET', 'PRU', 'TRV', 'PGR', 'CB', 'AJG', 'MMC', 'AON',
    
    # Payment/Fintech
    'V', 'MA', 'PYPL', 'SQ', 'COIN', 'AFRM', 'SOFI',
    
    # Defense/Aerospace
    'LMT', 'RTX', 'BA', 'NOC', 'GD', 'LHX', 'HII', 'TXT', 'HWM',
    
    # Energy & Oil
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL', 'BKR', 
    'DVN', 'FANG', 'MRO', 'APA', 'OKE', 'WMB', 'KMI', 'EPD', 'ET',
    
    # Gold/Mining
    'NEM', 'GOLD', 'FCX', 'AEM', 'WPM', 'FNV', 'RGLD', 'AU', 'KGC', 'HL',
    
    # Retail & Consumer
    'WMT', 'TGT', 'COST', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'BKNG', 'CMG', 'YUM', 
    'DG', 'ROST', 'TJX', 'ULTA', 'BBY', 'GPS', 'ANF', 'LULU', 'DECK',
    
    # E-commerce
    'SHOP', 'EBAY', 'ETSY', 'W', 'CHWY', 'CVNA',
    
    # Healthcare & Pharma
    'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'LLY', 'BMY', 'AMGN', 
    'GILD', 'CVS', 'CI', 'ANTM', 'HUM', 'CNC', 'MOH', 'ELV', 'BIIB', 'REGN', 'VRTX',
    'ISRG', 'SYK', 'BSX', 'MDT', 'EW', 'ZBH', 'BAX', 'BDX', 'HOLX', 'ALGN',
    
    # Industrials
    'CAT', 'DE', 'GE', 'HON', 'UPS', 'UNP', 'MMM', 'EMR', 'ITW', 'ETN', 'FDX', 'NSC',
    'CSX', 'WM', 'RSG', 'IR', 'CARR', 'OTIS', 'PCAR', 'ROK', 'DOV', 'XYL',
    
    # Consumer Goods
    'PG', 'KO', 'PEP', 'PM', 'MO', 'CL', 'EL', 'KMB', 'GIS', 'HSY', 'MDLZ',
    'STZ', 'TAP', 'CPB', 'CAG', 'SJM', 'HRL', 'MKC', 'CHD',
    
    # Telecom
    'T', 'VZ', 'TMUS', 'CMCSA', 'CHTR',
    
    # Automotive
    'F', 'GM', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI',
    
    # Semiconductors
    'TSM', 'ASML', 'MU', 'AMAT', 'LRCX', 'KLAC', 'MCHP', 'ADI', 'NXPI', 'MRVL',
    'ON', 'MPWR', 'SWKS', 'QRVO', 'TER', 'ENTG',
    
    # Media & Entertainment
    'DIS', 'WBD', 'FOXA', 'FOX', 'NWSA', 'NWS', 'LYV', 'MSG', 'MSGS',
    
    # Real Estate
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL', 'DLR', 'AVB', 'EQR',
    'VTR', 'ARE', 'INVH', 'MAA', 'UDR', 'ESS', 'CPT', 'FRT', 'BXP',
    
    # Utilities
    'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ED', 'ES', 'PEG', 'WEC',
    'AWK', 'DTE', 'PPL', 'AEE', 'CMS', 'EVRG', 'FE', 'CNP',
    
    # Crypto-related
    'MSTR', 'MARA', 'RIOT', 'CLSK', 'BITF', 'HUT',
    
    # Materials
    'LIN', 'APD', 'ECL', 'SHW', 'DD', 'DOW', 'NEM', 'FCX', 'NUE', 'STLD', 'VMC',
    'MLM', 'PKG', 'IP', 'AMCR', 'ALB', 'CE', 'FMC', 'EMN', 'CF',
    
    # Additional S&P 500 stocks
    'ABBV', 'ACN', 'ADBE', 'ADP', 'AEE', 'AEP', 'AES', 'AFL', 'AIG', 'AIZ',
    'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK', 'ALL', 'ALLE', 'AMAT', 'AMCR', 'AME',
    'AMGN', 'AMP', 'AMT', 'AMZN', 'ANET', 'AON', 'AOS', 'APA', 'APD',
    'APH', 'APTV', 'ARE', 'ATO', 'AVB', 'AVGO', 'AVY', 'AWK', 'AXON', 'AXP',
    'AZO', 'BA', 'BAC', 'BALL', 'BAX', 'BBWI', 'BBY', 'BDX', 'BEN', 'BF.B',
    'BG', 'BIIB', 'BIO', 'BK', 'BKNG', 'BKR', 'BLDR', 'BLK', 'BMY', 'BR',
    'BRK.B', 'BRO', 'BSX', 'BWA', 'BX', 'BXP', 'C', 'CAG', 'CAH', 'CARR',
    'CAT', 'CB', 'CBOE', 'CBRE', 'CCI', 'CCL', 'CDAY', 'CDNS', 'CDW', 'CE',
    'CEG', 'CF', 'CFG', 'CHD', 'CHRW', 'CHTR', 'CI', 'CINF', 'CL', 'CLX',
    'CMCSA', 'CME', 'CMG', 'CMI', 'CMS', 'CNC', 'CNP', 'COF', 'COO',
    'COP', 'COR', 'COST', 'CPAY', 'CPB', 'CPRT', 'CPT', 'CRL', 'CRM', 'CSCO',
    'CSGP', 'CSX', 'CTAS', 'CTLT', 'CTRA', 'CTSH', 'CTVA', 'CVS', 'CVX', 'CZR',
    'D', 'DAL', 'DD', 'DE', 'DECK', 'DFS', 'DG', 'DGX', 'DHI',
    'DHR', 'DIS', 'DLR', 'DLTR', 'DOC', 'DOV', 'DOW', 'DPZ', 'DRI', 'DTE',
    'DUK', 'DVA', 'DVN', 'DXCM', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EG',
    'EIX', 'EL', 'ELV', 'EMN', 'EMR', 'ENPH', 'EOG', 'EPAM', 'EQIX', 'EQR',
    'EQT', 'ES', 'ESS', 'ETN', 'ETR', 'ETSY', 'EVRG', 'EW', 'EXC', 'EXPD',
    'EXPE', 'EXR', 'F', 'FANG', 'FAST', 'FCX', 'FDS', 'FDX', 'FE', 'FFIV',
    'FICO', 'FIS', 'FITB', 'FLT', 'FMC', 'FOX', 'FOXA', 'FRT', 'FSLR',
    'FTNT', 'FTV', 'GD', 'GE', 'GEHC', 'GEN', 'GEV', 'GILD', 'GIS', 'GL',
    'GLW', 'GM', 'GNRC', 'GOOG', 'GOOGL', 'GPC', 'GPN', 'GRMN', 'GS', 'GWW',
    'HAL', 'HAS', 'HBAN', 'HCA', 'HD', 'HIG', 'HII', 'HLT', 'HOLX',
    'HON', 'HPE', 'HPQ', 'HRL', 'HSIC', 'HST', 'HSY', 'HUBB', 'HUM', 'HWM',
    'IBM', 'ICE', 'IDXX', 'IEX', 'IFF', 'INCY', 'INTC', 'INTU', 'INVH', 'IP',
    'IQV', 'IR', 'IRM', 'ISRG', 'IT', 'ITW', 'IVZ', 'J', 'JBHT',
    'JBL', 'JCI', 'JKHY', 'JNJ', 'JNPR', 'JPM', 'KDP', 'KEY', 'KEYS',
    'KHC', 'KIM', 'KKR', 'KLAC', 'KMB', 'KMI', 'KMX', 'KO', 'KR', 'KVUE',
    'L', 'LDOS', 'LEN', 'LH', 'LHX', 'LIN', 'LKQ', 'LLY', 'LMT', 'LNT',
    'LOW', 'LRCX', 'LULU', 'LUV', 'LVS', 'LW', 'LYB', 'LYV', 'MA', 'MAA',
    'MAR', 'MAS', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'META',
    'MGM', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MMM', 'MNST', 'MO', 'MOH',
    'MOS', 'MPC', 'MPWR', 'MRK', 'MRNA', 'MRO', 'MS', 'MSCI', 'MSFT', 'MSI',
    'MTB', 'MTCH', 'MTD', 'MU', 'NCLH', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NFLX',
    'NI', 'NKE', 'NOC', 'NOW', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA',
    'NVR', 'NWS', 'NWSA', 'NXPI', 'O', 'ODFL', 'OKE', 'OMC', 'ON', 'ORCL',
    'ORLY', 'OTIS', 'OXY', 'PANW', 'PAYC', 'PAYX', 'PCAR', 'PCG', 'PEG',
    'PEP', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKG', 'PLD', 'PM',
    'PNC', 'PNR', 'PNW', 'PODD', 'POOL', 'PPG', 'PPL', 'PRU', 'PSA', 'PSX',
    'PTC', 'PWR', 'PYPL', 'QCOM', 'QRVO', 'RCL', 'REG', 'REGN', 'RF', 'RJF',
    'RL', 'RMD', 'ROK', 'ROL', 'ROP', 'ROST', 'RSG', 'RTX', 'RVTY', 'SBAC',
    'SBUX', 'SCHW', 'SHW', 'SJM', 'SLB', 'SMCI', 'SNA', 'SNPS', 'SO', 'SPG',
    'SPGI', 'SRE', 'STE', 'STLD', 'STT', 'STX', 'STZ', 'SWK', 'SWKS', 'SYF',
    'SYK', 'SYY', 'T', 'TAP', 'TDG', 'TDY', 'TECH', 'TEL', 'TER', 'TFC',
    'TFX', 'TGT', 'TJX', 'TMO', 'TMUS', 'TPR', 'TRGP', 'TRMB', 'TROW', 'TRV',
    'TSCO', 'TSLA', 'TSN', 'TT', 'TTWO', 'TXN', 'TXT', 'TYL', 'UAL', 'UBER',
    'UDR', 'UHS', 'ULTA', 'UNH', 'UNP', 'UPS', 'URI', 'USB', 'V', 'VICI',
    'VLO', 'VLTO', 'VMC', 'VRSK', 'VRSN', 'VRTX', 'VST', 'VTR', 'VTRS', 'VZ',
    'WAB', 'WAT', 'WBD', 'WDC', 'WEC', 'WELL', 'WFC', 'WM', 'WMB',
    'WMT', 'WRB', 'WRK', 'WST', 'WTW', 'WY', 'WYNN', 'XEL', 'XOM', 'XYL',
    'YUM', 'ZBH', 'ZBRA', 'ZTS',
]

# Remove duplicates and sort
STOCK_TICKERS = sorted(list(set(STOCK_TICKERS)))


# News topics that impact stocks broadly
NEWS_TOPICS = [
    # Commodities
    'gold', 'silver', 'oil', 'natural gas', 'commodities',
    
    # Defense & Geopolitics
    'military', 'defense', 'army', 'war', 'geopolitics',
    
    # Economic Indicators
    'inflation', 'interest rates', 'federal reserve', 'GDP', 'unemployment',
    
    # Crypto
    'bitcoin', 'cryptocurrency', 'ethereum',
    
    # Technology
    'artificial intelligence', 'AI', 'semiconductors', 'cloud computing',
    
    # Market General
    'stock market', 'wall street', 'nasdaq', 'dow jones', 'S&P 500',
]


# Sentiment thresholds
SENTIMENT_THRESHOLDS = {
    'very_positive': 0.5,
    'positive': 0.05,
    'neutral': -0.05,
    'negative': -0.5,
    'very_negative': -0.5,
}


# Prediction weights
PREDICTION_WEIGHTS = {
    'sentiment': 0.6,
    'price_momentum': 0.3,
    'volume': 0.1,
}


# Recommendation thresholds
RECOMMENDATION_THRESHOLDS = {
    'strong_buy': 0.5,
    'buy': 0.2,
    'hold_upper': 0.2,
    'hold_lower': -0.2,
    'sell': -0.5,
}
