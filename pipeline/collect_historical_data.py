"""
Master Script for Historical Data Collection
Orchestrates the entire process: scrape → analyze → build training data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
from datetime import datetime, timedelta
import config


def collect_historical_data(months=6, tickers_count=500):
    """
    Collect historical data for training
    
    Args:
        months: Number of months of historical data (default: 6)
        tickers_count: Number of tickers to track (default: 500)
    """
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print("\n" + "="*70)
    print("HISTORICAL DATA COLLECTION PIPELINE")
    print("="*70)
    print(f"Date Range: {start_str} to {end_str} ({months} months)")
    print(f"Tickers: {tickers_count}")
    print("="*70)
    
    # File paths
    news_file = f'data/historical_news_{start_str}_to_{end_str}.json'
    training_file = f'data/training_data_{start_str}_to_{end_str}.csv'
    
    # Step 1: Scrape historical news
    print("\n" + "="*70)
    print("STEP 1: SCRAPING HISTORICAL NEWS")
    print("="*70)
    print(f"This will scrape {months} months of news from multiple sources")
    print(f"Estimated time: {months * 10} minutes")
    print("="*70)
    
    response = input("\nProceed with scraping? (y/n): ")
    if response.lower() != 'y':
        print("[!] Scraping cancelled")
        return
    
    print("\n[*] Starting historical news spider...")
    
    cmd = [
        'python', 'pipeline/historical_news_spider.py',
        '--mode', 'historical',
        '--start-date', start_str,
        '--end-date', end_str,
        '--tickers', str(tickers_count),
        '--output', news_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[OK] Historical news saved to: {news_file}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Scraping failed: {e}")
        return
    
    # Step 2: Build training dataset
    print("\n" + "="*70)
    print("STEP 2: BUILDING TRAINING DATASET")
    print("="*70)
    print("This will:")
    print("  1. Analyze sentiment for all articles")
    print("  2. Analyze impact and affected stocks")
    print("  3. Fetch historical prices from Yahoo Finance")
    print("  4. Match news with price movements")
    print("  5. Create training dataset")
    print("="*70)
    
    response = input("\nProceed with building dataset? (y/n): ")
    if response.lower() != 'y':
        print("[!] Dataset building cancelled")
        return
    
    print("\n[*] Building training dataset...")
    
    cmd = [
        'python', 'pipeline/build_training_data.py',
        '--start-date', start_str,
        '--end-date', end_str,
        '--news-file', news_file,
        '--output', training_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[OK] Training data saved to: {training_file}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Dataset building failed: {e}")
        return
    
    # Step 3: Summary
    print("\n" + "="*70)
    print("HISTORICAL DATA COLLECTION COMPLETE!")
    print("="*70)
    print(f"\nFiles created:")
    print(f"  1. Historical News: {news_file}")
    print(f"  2. Training Data:   {training_file}")
    print(f"\nNext steps:")
    print(f"  1. Review the training data")
    print(f"  2. Train ML model: python pipeline/ml_predictor.py --train {training_file}")
    print(f"  3. Backtest strategy: python scripts/backtest.py")
    print("="*70)


def collect_realtime_data(tickers_count=100):
    """
    Collect real-time data (current news)
    
    Args:
        tickers_count: Number of tickers to track (default: 100)
    """
    
    print("\n" + "="*70)
    print("REAL-TIME DATA COLLECTION")
    print("="*70)
    print(f"Tickers: {tickers_count}")
    print("="*70)
    
    news_file = 'data/scraped_news.json'
    
    print("\n[*] Starting real-time news spider...")
    
    cmd = [
        'python', 'pipeline/historical_news_spider.py',
        '--mode', 'realtime',
        '--tickers', str(tickers_count),
        '--output', news_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[OK] Real-time news saved to: {news_file}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Scraping failed: {e}")
        return
    
    print("\n[*] Run the full pipeline to get predictions:")
    print("    python pipeline/run_pipeline.py")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect historical or real-time data')
    parser.add_argument('--mode', choices=['historical', 'realtime'], required=True,
                       help='Data collection mode')
    parser.add_argument('--months', type=int, default=6,
                       help='Months of historical data (for historical mode)')
    parser.add_argument('--tickers', type=int, default=500,
                       help='Number of tickers to track')
    
    args = parser.parse_args()
    
    if args.mode == 'historical':
        collect_historical_data(months=args.months, tickers_count=args.tickers)
    else:
        collect_realtime_data(tickers_count=args.tickers)
