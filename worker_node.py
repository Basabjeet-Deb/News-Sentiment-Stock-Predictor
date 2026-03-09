"""
Worker Node - Distributed Stock Analysis
Processes assigned stocks: sentiment analysis + price prediction
"""

from flask import Flask, request, jsonify
import requests
import time
import threading
import os
import socket
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)

# Configuration
MASTER_URL = os.getenv('MASTER_URL', 'https://sequestrable-tammy-unrefused.ngrok-free.dev')
WORKER_ID = os.getenv('WORKER_ID', socket.gethostname())

# Sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Worker state
worker_state = {
    'registered': False,
    'tasks_processed': 0,
    'assigned_stocks': [],
    'current_task': None
}


def register_with_master():
    """Register this worker with the master node"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{MASTER_URL}/register",
                json={'worker_id': WORKER_ID},
                timeout=10
            )
            
            if response.status_code == 200:
                worker_state['registered'] = True
                print(f"[OK] Successfully registered with master at {MASTER_URL}")
                return True
            else:
                print(f"[ERROR] Registration failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Cannot connect to master (attempt {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("[ERROR] Failed to register with master after all retries")
    return False


def send_heartbeat():
    """Send periodic heartbeat to master"""
    while True:
        if worker_state['registered']:
            try:
                requests.post(
                    f"{MASTER_URL}/heartbeat",
                    json={'worker_id': WORKER_ID},
                    timeout=5
                )
            except:
                pass
        time.sleep(10)


@app.route('/')
def home():
    """Worker status page"""
    return jsonify({
        'node_type': 'worker',
        'worker_id': WORKER_ID,
        'registered': worker_state['registered'],
        'master_url': MASTER_URL,
        'tasks_processed': worker_state['tasks_processed'],
        'assigned_stocks': worker_state['assigned_stocks'],
        'current_task': worker_state['current_task']
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'worker_id': WORKER_ID})


@app.route('/process_stocks', methods=['POST'])
def process_stocks():
    """Process stock analysis task from master"""
    data = request.json
    
    stock_data = data.get('stock_data', [])
    news_data = data.get('news_data', [])
    assigned_stocks = data.get('stocks', [])
    
    worker_state['assigned_stocks'] = assigned_stocks
    worker_state['current_task'] = 'processing'
    
    print(f"\n[Worker {WORKER_ID}] Processing {len(assigned_stocks)} stocks...")
    print(f"Stock records: {len(stock_data)}")
    print(f"News articles: {len(news_data)}")
    
    try:
        # Convert to DataFrames
        stock_df = pd.DataFrame(stock_data)
        news_df = pd.DataFrame(news_data)
        
        results = []
        
        for ticker in assigned_stocks:
            # Get stock data for this ticker
            ticker_data = stock_df[stock_df['Ticker'] == ticker].copy()
            
            if len(ticker_data) == 0:
                continue
            
            # Calculate technical indicators
            ticker_data['MA_7'] = ticker_data['Close'].rolling(window=7).mean()
            ticker_data['MA_30'] = ticker_data['Close'].rolling(window=30).mean()
            ticker_data['volatility'] = ticker_data['Close'].rolling(window=7).std()
            
            # Get latest data
            latest = ticker_data.iloc[-1]
            
            # Get news sentiment for this stock
            ticker_news = news_df[news_df['mentioned_stocks'].str.contains(ticker, na=False)]
            
            if len(ticker_news) > 0:
                sentiments = []
                for text in ticker_news['title']:
                    scores = analyzer.polarity_scores(str(text))
                    sentiments.append(scores['compound'])
                avg_sentiment = np.mean(sentiments)
                news_count = len(sentiments)
            else:
                avg_sentiment = 0.0
                news_count = 0
            
            # Simple prediction logic
            price_trend = 1 if latest['MA_7'] > latest['MA_30'] else -1
            sentiment_factor = avg_sentiment * 2
            
            predicted_change = (price_trend * 0.5) + sentiment_factor
            
            # Determine recommendation
            if predicted_change > 0.3:
                recommendation = 'BUY'
            elif predicted_change < -0.3:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'
            
            # Calculate confidence
            confidence = min(abs(predicted_change) * 0.5 + (news_count / 10), 1.0)
            
            results.append({
                'ticker': ticker,
                'current_price': float(latest['Close']),
                'predicted_change': round(predicted_change, 2),
                'sentiment': round(avg_sentiment, 3),
                'news_count': news_count,
                'confidence': round(confidence, 2),
                'recommendation': recommendation,
                'ma_7': round(float(latest['MA_7']), 2) if not pd.isna(latest['MA_7']) else None,
                'ma_30': round(float(latest['MA_30']), 2) if not pd.isna(latest['MA_30']) else None
            })
        
        worker_state['tasks_processed'] += len(results)
        worker_state['current_task'] = None
        
        print(f"[OK] Processed {len(results)} stocks")
        
        # Send results back to master
        try:
            requests.post(
                f"{MASTER_URL}/submit_result",
                json={
                    'worker_id': WORKER_ID,
                    'results': results
                },
                timeout=30
            )
            print(f"[OK] Submitted results to master")
        except Exception as e:
            print(f"[ERROR] Failed to submit results: {e}")
        
        return jsonify({
            'status': 'completed',
            'worker_id': WORKER_ID,
            'processed': len(results),
            'results': results
        })
    
    except Exception as e:
        worker_state['current_task'] = None
        print(f"[ERROR] Processing failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    print("="*60)
    print("WORKER NODE - STOCK ANALYSIS")
    print("="*60)
    print(f"Worker ID: {WORKER_ID}")
    print(f"Master URL: {MASTER_URL}")
    print("="*60)
    
    # Register with master
    if register_with_master():
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        print(f"Worker listening on port 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("Failed to start worker - could not register with master")
