"""
Distributed Stock Analysis
Splits 10 stocks across cluster workers for parallel processing
"""

import requests
import json
import time
from config import TARGET_STOCKS, STOCK_NAMES

# Configuration
MASTER_URL = "http://192.168.1.100:8000"  # UPDATE THIS


def split_stocks(num_workers):
    """Split stocks evenly across workers"""
    stocks_per_worker = len(TARGET_STOCKS) // num_workers
    remainder = len(TARGET_STOCKS) % num_workers
    
    assignments = []
    start = 0
    
    for i in range(num_workers):
        # Add one extra stock to first 'remainder' workers
        count = stocks_per_worker + (1 if i < remainder else 0)
        end = start + count
        
        assignments.append({
            'worker_num': i + 1,
            'stocks': TARGET_STOCKS[start:end]
        })
        
        start = end
    
    return assignments


def send_analysis_command(stocks):
    """Send stock analysis command to cluster"""
    
    # Create Python command to analyze stocks
    stocks_str = ','.join(stocks)
    
    command = f"""python -c "
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Stocks to analyze
stocks = '{stocks_str}'.split(',')

# Load data
stock_df = pd.read_csv('data/prototype_stocks.csv')
news_df = pd.read_csv('data/prototype_news.csv')
analyzer = SentimentIntensityAnalyzer()

results = []

for ticker in stocks:
    # Get stock data
    ticker_data = stock_df[stock_df['Ticker'] == ticker].copy()
    if len(ticker_data) == 0:
        continue
    
    # Calculate indicators
    ticker_data['MA_7'] = ticker_data['Close'].rolling(window=7).mean()
    ticker_data['MA_30'] = ticker_data['Close'].rolling(window=30).mean()
    latest = ticker_data.iloc[-1]
    
    # Get sentiment
    ticker_news = news_df[news_df['ticker'] == ticker]
    if len(ticker_news) > 0:
        sentiments = [analyzer.polarity_scores(str(row['title']))['compound'] for _, row in ticker_news.iterrows()]
        avg_sentiment = np.mean(sentiments)
        news_count = len(sentiments)
    else:
        avg_sentiment = 0.0
        news_count = 0
    
    # Prediction
    trend_score = 1 if latest['MA_7'] > latest['MA_30'] else -1
    predicted_change = (trend_score * 0.5) + (avg_sentiment * 2)
    
    if predicted_change > 0.3:
        recommendation = 'BUY'
    elif predicted_change < -0.3:
        recommendation = 'SELL'
    else:
        recommendation = 'HOLD'
    
    confidence = min(abs(predicted_change) * 0.5 + (news_count / 20), 1.0)
    
    results.append(f'{ticker}|{latest[\"Close\"]:.2f}|{predicted_change:.2f}|{avg_sentiment:.3f}|{news_count}|{confidence:.2f}|{recommendation}')

print('RESULTS:')
for r in results:
    print(r)
"
"""
    
    try:
        response = requests.post(
            f"{MASTER_URL}/execute",
            json={
                "command": command,
                "target": "all"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("command_id")
        else:
            print(f"Error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_command_results(command_id, timeout=120):
    """Wait for and retrieve command results"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{MASTER_URL}/command/{command_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "completed":
                    return data.get("results", {})
            
            time.sleep(3)
        
        except Exception as e:
            print(f"Error checking status: {e}")
            time.sleep(3)
    
    return None


def parse_results(results):
    """Parse results from workers"""
    all_predictions = []
    
    for worker_id, result in results.items():
        output = result.get('output', '')
        
        # Parse output
        lines = output.split('\n')
        in_results = False
        
        for line in lines:
            if 'RESULTS:' in line:
                in_results = True
                continue
            
            if in_results and '|' in line:
                parts = line.strip().split('|')
                if len(parts) == 7:
                    all_predictions.append({
                        'ticker': parts[0],
                        'company': STOCK_NAMES.get(parts[0], parts[0]),
                        'current_price': float(parts[1]),
                        'predicted_change': float(parts[2]),
                        'sentiment': float(parts[3]),
                        'news_count': int(parts[4]),
                        'confidence': float(parts[5]),
                        'recommendation': parts[6],
                        'worker': worker_id
                    })
    
    return all_predictions


def main():
    print("="*60)
    print("DISTRIBUTED STOCK ANALYSIS")
    print("="*60)
    print(f"Master URL: {MASTER_URL}")
    print(f"Stocks to analyze: {len(TARGET_STOCKS)}")
    print("="*60)
    
    # Get workers
    try:
        response = requests.get(f"{MASTER_URL}/workers", timeout=10)
        workers = response.json()
        num_workers = workers.get('total', 0)
        
        if num_workers == 0:
            print("\n[ERROR] No workers available")
            print("Make sure workers are running and registered with master")
            return
        
        print(f"\n[OK] Found {num_workers} workers")
        
        # Show worker info
        for w in workers.get('workers', []):
            print(f"  - {w['worker_id']} ({w['ip']}) - {w['status']}")
    
    except Exception as e:
        print(f"\n[ERROR] Cannot connect to master: {e}")
        return
    
    # Split stocks across workers
    assignments = split_stocks(num_workers)
    
    print(f"\n[OK] Stock distribution:")
    for assignment in assignments:
        stocks = assignment['stocks']
        print(f"  Worker {assignment['worker_num']}: {', '.join(stocks)} ({len(stocks)} stocks)")
    
    # Send analysis command
    print(f"\n[SENDING] Analysis command to cluster...")
    
    # For simplicity, send all stocks to all workers (they'll process in parallel)
    command_id = send_analysis_command(TARGET_STOCKS)
    
    if not command_id:
        print("[ERROR] Failed to send command")
        return
    
    print(f"[OK] Command ID: {command_id}")
    print("[WAITING] Processing on cluster...")
    
    # Wait for results
    results = get_command_results(command_id)
    
    if not results:
        print("\n[ERROR] Timeout waiting for results")
        return
    
    print(f"\n[OK] Received results from {len(results)} workers")
    
    # Parse and display results
    predictions = parse_results(results)
    
    if not predictions:
        print("\n[ERROR] No predictions generated")
        return
    
    print("\n" + "="*60)
    print("PREDICTIONS")
    print("="*60)
    
    # Sort by ticker
    predictions.sort(key=lambda x: x['ticker'])
    
    for pred in predictions:
        print(f"\n[{pred['ticker']}] {pred['company']}")
        print(f"  Current Price: ${pred['current_price']:.2f}")
        print(f"  Predicted Change: {pred['predicted_change']:+.2f}%")
        print(f"  Sentiment: {pred['sentiment']:+.3f} ({pred['news_count']} articles)")
        print(f"  Confidence: {pred['confidence']:.2f}")
        print(f"  Recommendation: {pred['recommendation']}")
        print(f"  Processed by: {pred['worker']}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    buy_count = len([p for p in predictions if p['recommendation'] == 'BUY'])
    sell_count = len([p for p in predictions if p['recommendation'] == 'SELL'])
    hold_count = len([p for p in predictions if p['recommendation'] == 'HOLD'])
    
    print(f"Total Stocks Analyzed: {len(predictions)}")
    print(f"BUY: {buy_count}")
    print(f"SELL: {sell_count}")
    print(f"HOLD: {hold_count}")
    print(f"Workers Used: {len(results)}")
    
    # Save results
    import pandas as pd
    df = pd.DataFrame(predictions)
    output_file = 'data/distributed_predictions.csv'
    df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
