"""
Fetch historical stock price data using yfinance
Free and no API key required
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os


class StockDataFetcher:
    def __init__(self):
        self.output_dir = "data"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_stock_data(self, ticker, period="1mo", interval="1d"):
        """
        Fetch stock price data
        
        Parameters:
        - ticker: Stock symbol (e.g., 'AAPL', 'MSFT')
        - period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        - interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        """
        
        print(f"Fetching {ticker} data for period: {period}")
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                print(f"✗ No data found for {ticker}")
                return None
            
            # Add ticker column
            df['Ticker'] = ticker
            
            # Reset index to make Date a column
            df.reset_index(inplace=True)
            
            print(f"✓ Fetched {len(df)} records for {ticker}")
            return df
            
        except Exception as e:
            print(f"✗ Error fetching {ticker}: {e}")
            return None
    
    def fetch_multiple_stocks(self, tickers, period="1mo", interval="1d"):
        """Fetch data for multiple stocks"""
        
        all_data = []
        
        for ticker in tickers:
            df = self.fetch_stock_data(ticker, period, interval)
            if df is not None:
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df
        else:
            return None
    
    def save_to_csv(self, df, filename=None):
        """Save stock data to CSV"""
        
        if df is None or df.empty:
            print("No data to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stock_prices_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False)
        
        print(f"\n✓ Saved {len(df)} records to {filepath}")
        return filepath
    
    def get_stock_info(self, ticker):
        """Get company information"""
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'ticker': ticker,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'current_price': info.get('currentPrice', 'N/A')
            }
        except Exception as e:
            print(f"✗ Error getting info for {ticker}: {e}")
            return None


def main():
    fetcher = StockDataFetcher()
    
    print("="*60)
    print("STOCK PRICE DATA FETCHER - LARGE DATASET")
    print("="*60)
    
    # Define stocks to track (expanded list - 50 stocks)
    tickers = [
        # Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'ORCL',
        # Finance
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V',
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'DHR', 'BMY', 'LLY',
        # Consumer
        'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'COST', 'LOW', 'DIS', 'NFLX',
        # Energy
        'XOM', 'CVX', 'COP', 'SLB', 'EOG',
        # Industrial
        'BA', 'CAT', 'GE', 'MMM', 'HON'
    ]
    
    print(f"\nFetching data for {len(tickers)} stocks...")
    print(f"Period: 2 years of historical data")
    print(f"This will create a LARGE dataset for distributed processing")
    
    # Fetch 2 years of daily data
    df = fetcher.fetch_multiple_stocks(
        tickers=tickers,
        period="2y",  # 2 years
        interval="1d"
    )
    
    if df is not None:
        # Save to CSV
        filepath = fetcher.save_to_csv(df, filename="stock_prices.csv")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total records: {len(df)}")
        print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"Stocks: {df['Ticker'].nunique()}")
        print(f"Average records per stock: {len(df) / df['Ticker'].nunique():.0f}")
        print(f"\nDataset size: ~{len(df) * 9 / 1000:.1f}K data points")
        print(f"Perfect for distributed processing across 3 worker nodes!")
        
        # Show sample data
        print("\nSample data:")
        print(df.head())
    else:
        print("\n[ERROR] No stock data fetched")


if __name__ == "__main__":
    main()
