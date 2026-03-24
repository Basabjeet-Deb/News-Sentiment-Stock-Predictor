"""
Fetch data for prototype stocks
Focused on 10 major stocks with targeted news
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TARGET_STOCKS, STOCK_NAMES, HISTORICAL_DAYS

def fetch_stock_data():
    """Fetch stock price data for target stocks"""
    
    print("="*60)
    print("FETCHING STOCK DATA FOR PROTOTYPE")
    print("="*60)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=HISTORICAL_DAYS)
    
    all_data = []
    
    for ticker in TARGET_STOCKS:
        try:
            print(f"\n[{ticker}] {STOCK_NAMES[ticker]}")
            print(f"  Fetching data from {start_date.date()} to {end_date.date()}...")
            
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if len(df) > 0:
                df['Ticker'] = ticker
                df['Date'] = df.index
                df = df.reset_index(drop=True)
                
                all_data.append(df)
                
                print(f"  [OK] Fetched {len(df)} records")
                print(f"  Latest price: ${df['Close'].iloc[-1]:.2f}")
            else:
                print(f"  [WARN] No data available")
        
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    if all_data:
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save to CSV
        os.makedirs('data', exist_ok=True)
        output_file = 'data/prototype_stocks.csv'
        combined_df.to_csv(output_file, index=False)
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total records: {len(combined_df)}")
        print(f"Stocks: {len(TARGET_STOCKS)}")
        print(f"Saved to: {output_file}")
        
        # Show summary per stock
        print("\nRecords per stock:")
        for ticker in TARGET_STOCKS:
            count = len(combined_df[combined_df['Ticker'] == ticker])
            print(f"  {ticker}: {count} records")
        
        return output_file
    
    else:
        print("\n[ERROR] No data fetched")
        return None


if __name__ == "__main__":
    fetch_stock_data()
