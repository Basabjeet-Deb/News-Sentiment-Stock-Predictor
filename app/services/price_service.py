"""
Stock price fetching service - wraps existing price fetching logic
"""

import sys
import os
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Add parent directory to import existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.price_fetcher import StockPriceFetcher as BasePriceFetcher
from app.core.config import get_settings, STOCK_TICKERS


class PriceService:
    """Service for fetching stock prices"""
    
    def __init__(self):
        self.fetcher = BasePriceFetcher()
        self._cache: Dict[str, Dict] = {}
        self._cache_timestamp: Optional[datetime] = None
        self.settings = get_settings()
    
    def fetch_prices(self, tickers: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Fetch current prices for stocks
        
        Args:
            tickers: List of ticker symbols (defaults to all tracked stocks)
            
        Returns:
            Dictionary of ticker -> price data
        """
        tickers = tickers or STOCK_TICKERS
        prices = self.fetcher.fetch_current_prices(tickers)
        self._cache = prices
        self._cache_timestamp = datetime.now()
        return prices
    
    def get_price(self, ticker: str) -> Optional[Dict]:
        """
        Get price for a single stock
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Price data dictionary or None
        """
        if ticker in self._cache:
            return self._cache[ticker]
        
        # Fetch single stock
        prices = self.fetcher.fetch_current_prices([ticker])
        if ticker in prices and 'error' not in prices[ticker]:
            self._cache[ticker] = prices[ticker]
            return prices[ticker]
        
        return None
    
    def get_cached_prices(self) -> Dict[str, Dict]:
        """Get cached prices if available"""
        return self._cache
    
    def get_historical_data(self, ticker: str, period: str = "1mo", interval: str = "1d"):
        """
        Get historical price data for a stock
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Data interval (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
            
        Returns:
            DataFrame with OHLCV data
        """
        return self.fetcher.fetch_historical_prices(ticker, period=period, interval=interval)
    
    def load_from_csv(self, filepath: str = None) -> Dict[str, Dict]:
        """
        Load prices from CSV file
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Dictionary of ticker -> price data
        """
        filepath = filepath or self.settings.PRICES_CSV
        
        if not os.path.exists(filepath):
            return {}
        
        try:
            df = pd.read_csv(filepath)
            # Replace NaN and inf for JSON compatibility
            df = df.replace([float('inf'), float('-inf')], None)
            df = df.fillna(0)
            prices = {}
            for _, row in df.iterrows():
                ticker = row.get('ticker', '')
                if ticker:
                    prices[ticker] = row.to_dict()
            self._cache = prices
            return prices
        except Exception as e:
            print(f"Error loading prices CSV: {e}")
            return {}
    
    def get_market_summary(self, prices: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        Get market summary statistics
        
        Args:
            prices: Price data (uses cache if not provided)
            
        Returns:
            Market summary dictionary
        """
        prices = prices or self._cache
        
        if not prices:
            return {
                "total_stocks": 0,
                "gainers": 0,
                "losers": 0,
                "unchanged": 0,
                "top_gainers": [],
                "top_losers": [],
                "most_active": [],
            }
        
        # Filter valid prices
        valid = {k: v for k, v in prices.items() 
                 if 'error' not in v and v.get('price', 0) > 0}
        
        # Count gainers/losers
        gainers = sum(1 for v in valid.values() if v.get('change_percent', 0) > 0)
        losers = sum(1 for v in valid.values() if v.get('change_percent', 0) < 0)
        unchanged = len(valid) - gainers - losers
        
        # Sort for top lists
        sorted_by_change = sorted(valid.values(), 
                                  key=lambda x: x.get('change_percent', 0), 
                                  reverse=True)
        sorted_by_volume = sorted(valid.values(), 
                                  key=lambda x: x.get('volume', 0), 
                                  reverse=True)
        
        return {
            "total_stocks": len(valid),
            "gainers": gainers,
            "losers": losers,
            "unchanged": unchanged,
            "top_gainers": sorted_by_change[:10],
            "top_losers": sorted_by_change[-10:],
            "most_active": sorted_by_volume[:10],
            "timestamp": datetime.now().isoformat(),
        }
    
    def filter_prices(
        self,
        prices: Dict[str, Dict],
        sector: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_change_percent: Optional[float] = None,
        max_change_percent: Optional[float] = None,
        sort_by: str = "change_percent",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Filter and sort price data
        
        Args:
            prices: Price data dictionary
            sector: Filter by sector
            min_price: Minimum price
            max_price: Maximum price
            min_change_percent: Minimum change %
            max_change_percent: Maximum change %
            sort_by: Field to sort by
            sort_desc: Sort descending
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Filtered and sorted list of prices
        """
        # Filter valid prices
        filtered = [v for v in prices.values() 
                    if 'error' not in v and v.get('price', 0) > 0]
        
        if sector:
            filtered = [p for p in filtered 
                       if sector.lower() in p.get('sector', '').lower()]
        
        if min_price is not None:
            filtered = [p for p in filtered if p.get('price', 0) >= min_price]
        
        if max_price is not None:
            filtered = [p for p in filtered if p.get('price', 0) <= max_price]
        
        if min_change_percent is not None:
            filtered = [p for p in filtered 
                       if p.get('change_percent', 0) >= min_change_percent]
        
        if max_change_percent is not None:
            filtered = [p for p in filtered 
                       if p.get('change_percent', 0) <= max_change_percent]
        
        # Sort
        filtered.sort(key=lambda x: x.get(sort_by, 0), reverse=sort_desc)
        
        # Paginate
        return filtered[offset:offset + limit]
