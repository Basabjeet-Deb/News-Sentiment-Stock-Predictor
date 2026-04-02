"""
Stock Price Fetcher
Fetches real-time and historical stock prices using yfinance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class StockPriceFetcher:
    """Fetch stock prices from Yahoo Finance"""
    
    def __init__(self):
        self.price_cache = {}
        
    def fetch_current_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch current prices for multiple stocks with robust error handling
        
        Returns:
            Dict of ticker -> {price, change, change_percent, volume, market_cap, etc.}
        """
        print(f"[*] Fetching current prices for {len(tickers)} stocks...")
        
        results = {}
        failed = []
        batch_size = 50  # Yahoo Finance handles batches well
        
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i+batch_size]
            
            for ticker in batch:
                try:
                    stock = yf.Ticker(ticker)
                    
                    # Try to get info first
                    try:
                        info = stock.info
                        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('ask', 0)
                        prev_close = info.get('previousClose', 0)
                    except:
                        # If info fails, try history
                        hist = stock.history(period='2d')
                        if len(hist) > 0:
                            current_price = float(hist['Close'].iloc[-1])
                            prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                            info = {}
                        else:
                            failed.append(ticker)
                            continue
                    
                    # Calculate change
                    if prev_close > 0:
                        change = current_price - prev_close
                        change_percent = (change / prev_close) * 100
                    else:
                        change = 0
                        change_percent = 0
                    
                    results[ticker] = {
                        'ticker': ticker,
                        'price': current_price,
                        'previous_close': prev_close,
                        'change': change,
                        'change_percent': change_percent,
                        'volume': info.get('volume', 0),
                        'market_cap': info.get('marketCap', 0),
                        'pe_ratio': info.get('trailingPE', 0),
                        '52w_high': info.get('fiftyTwoWeekHigh', 0),
                        '52w_low': info.get('fiftyTwoWeekLow', 0),
                        'company_name': info.get('longName', ticker),
                        'sector': info.get('sector', 'Unknown'),
                        'industry': info.get('industry', 'Unknown'),
                    }
                except Exception as e:
                    # Silently skip failed tickers (delisted/invalid)
                    failed.append(ticker)
                    continue
        
        if failed:
            print(f"[!] Skipped {len(failed)} invalid/delisted tickers")
        print(f"[OK] Fetched prices for {len(results)} stocks")
        self.price_cache = results
        return results
    
    def fetch_historical_prices(self, ticker: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical price data for a single stock
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Data interval (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            return hist
        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_price_change_summary(self, tickers: List[str]) -> Dict:
        """
        Get summary of price movements
        
        Returns:
            Summary stats: gainers, losers, most_active, etc.
        """
        if not self.price_cache:
            self.fetch_current_prices(tickers)
        
        # Filter valid prices
        valid_stocks = {k: v for k, v in self.price_cache.items() 
                       if 'error' not in v and v.get('price', 0) > 0}
        
        # Sort by change percent
        sorted_by_change = sorted(valid_stocks.items(), 
                                 key=lambda x: x[1].get('change_percent', 0), 
                                 reverse=True)
        
        # Sort by volume
        sorted_by_volume = sorted(valid_stocks.items(), 
                                 key=lambda x: x[1].get('volume', 0), 
                                 reverse=True)
        
        return {
            'total_stocks': len(valid_stocks),
            'top_gainers': [{'ticker': k, **v} for k, v in sorted_by_change[:10]],
            'top_losers': [{'ticker': k, **v} for k, v in sorted_by_change[-10:]],
            'most_active': [{'ticker': k, **v} for k, v in sorted_by_volume[:10]],
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    print("=" * 70)
    print("[TEST] STOCK PRICE FETCHER TEST")
    print("=" * 70 + "\n")
    
    fetcher = StockPriceFetcher()
    
    # Test with a few stocks
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'JPM', 'GS', 'LMT']
    
    prices = fetcher.fetch_current_prices(test_stocks)
    
    print("\n" + "=" * 70)
    print("[PRICES] CURRENT PRICES:")
    print("=" * 70 + "\n")
    
    for ticker, data in prices.items():
        if 'error' not in data:
            price = data['price']
            change = data['change_percent']
            arrow = "[+]" if change >= 0 else "[-]"
            print(f"{arrow} {ticker:6s}: ${price:8.2f}  ({change:+.2f}%)  |  {data['company_name'][:40]}")
    
    # Get summary
    summary = fetcher.get_price_change_summary(test_stocks)
    
    print("\n" + "=" * 70)
    print("[TOP] GAINERS:")
    print("=" * 70)
    for stock in summary['top_gainers'][:5]:
        print(f"  {stock['ticker']:6s}: {stock['change_percent']:+.2f}%")
    
    print("\n" + "=" * 70)
    print("[BOTTOM] LOSERS:")
    print("=" * 70)
    for stock in summary['top_losers'][:5]:
        print(f"  {stock['ticker']:6s}: {stock['change_percent']:+.2f}%")
