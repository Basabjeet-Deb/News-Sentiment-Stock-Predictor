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
import contextlib
import io
import logging

from app.core.config import get_settings

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from pipeline.sector_mapper import SectorCache
from pipeline.ticker_utils import yahoo_ticker_symbol

class StockPriceFetcher:
    """Fetch stock prices from Yahoo Finance"""
    
    def __init__(self):
        self.price_cache = {}
        # Reduce yfinance noise (it logs/warns a lot for missing symbols)
        logging.getLogger("yfinance").setLevel(logging.ERROR)
        logging.getLogger("yfinance.base").setLevel(logging.ERROR)
    
    # Known problematic / non-Yahoo symbols in this project universe (skip quietly)
    _SKIP_TICKERS = {
        "ANSS", "CMA", "DAY", "FI", "HES", "IPG", "K", "PARA", "WBA",
    }
    
    @staticmethod
    def _normalize_ticker_for_yahoo(ticker: str) -> str:
        """Normalize tickers into Yahoo Finance format (delegates to `yahoo_ticker_symbol`)."""
        return yahoo_ticker_symbol(ticker)
        
    def fetch_current_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch current prices for multiple stocks with robust error handling
        
        Returns:
            Dict of ticker -> {price, change, change_percent, volume, market_cap, etc.}
        """
        # Normalize tickers to reduce 404s from Yahoo/yfinance
        original_tickers = [t for t in tickers]
        tickers = [self._normalize_ticker_for_yahoo(t) for t in tickers]
        tickers = [t for t in tickers if t and t not in self._SKIP_TICKERS]
        
        print(f"[*] Fetching current prices for {len(tickers)} stocks...")
        
        results = {}
        failed = []
        batch_size = 100  # prefer fewer calls
        
        # Fast path: batch download last 2 days close for all tickers.
        # This avoids `quoteSummary` 404 spam and is much more reliable than `.info`.
        try:
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                # yfinance sometimes prints to stdout for missing symbols; suppress it.
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    data = yf.download(
                        tickers=" ".join(batch),
                        period="5d",
                        interval="1d",
                        group_by="ticker",
                        auto_adjust=False,
                        threads=True,
                        progress=False,
                    )
                
                # Single ticker vs multi-ticker shape
                for ticker in batch:
                    try:
                        if isinstance(data.columns, pd.MultiIndex):
                            tdf = data[ticker].dropna()
                        else:
                            # single ticker: columns like Open/Close...
                            tdf = data.dropna()
                        
                        if tdf is None or len(tdf) < 1:
                            failed.append(ticker)
                            continue
                        
                        close = float(tdf["Close"].iloc[-1])
                        prev_close = float(tdf["Close"].iloc[-2]) if len(tdf) > 1 else close
                        change = close - prev_close
                        change_percent = (change / prev_close) * 100 if prev_close else 0
                        
                        results[ticker] = {
                            "ticker": ticker,
                            "price": close,
                            "previous_close": prev_close,
                            "change": change,
                            "change_percent": change_percent,
                            # Optional fields not available in batch OHLC:
                            "volume": float(tdf["Volume"].iloc[-1]) if "Volume" in tdf.columns else 0,
                            "market_cap": 0,
                            "pe_ratio": 0,
                            "52w_high": 0,
                            "52w_low": 0,
                            "company_name": ticker,
                            "sector": "Unknown",
                            "industry": "Unknown",
                        }
                    except Exception:
                        failed.append(ticker)
                        continue
        except Exception:
            # Fallback to original per-ticker approach
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="2d")
                    if len(hist) > 0:
                        close = float(hist["Close"].iloc[-1])
                        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else close
                    else:
                        failed.append(ticker)
                        continue
                    change = close - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0
                    results[ticker] = {
                        "ticker": ticker,
                        "price": close,
                        "previous_close": prev_close,
                        "change": change,
                        "change_percent": change_percent,
                        "volume": 0,
                        "market_cap": 0,
                        "pe_ratio": 0,
                        "52w_high": 0,
                        "52w_low": 0,
                        "company_name": ticker,
                        "sector": "Unknown",
                        "industry": "Unknown",
                    }
                except Exception:
                    failed.append(ticker)
                    continue
        
        if failed:
            print(f"[!] Skipped {len(failed)} invalid/delisted tickers")
        print(f"[OK] Fetched prices for {len(results)} stocks")

        # Enrich sectors/industries from persistent cache (fast path).
        # NOTE: Do NOT fetch new sectors here by default (yfinance .info is slow and can stall the pipeline).
        try:
            settings = get_settings()
            cache = SectorCache(data_dir=settings.DATA_DIR)
            sec_map = cache.to_map()
            for t, v in results.items():
                m = sec_map.get(t, {})
                if not m and "." not in t:
                    m = sec_map.get(t.replace("-", "."), {})
                if m.get("sector") and m.get("sector") != "Unknown":
                    v["sector"] = m.get("sector")
                if m.get("industry") and m.get("industry") != "Unknown":
                    v["industry"] = m.get("industry")
                cn = (m.get("company_name") or "").strip()
                if cn:
                    v["company_name"] = cn
        except Exception:
            pass

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
