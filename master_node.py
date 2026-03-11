"""
Master Node - Distributed Stock Prediction System
Coordinates workers, distributes stocks, aggregates predictions
Provides REST API for frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import time
import threading
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Store connected workers
workers = {}
worker_lock = threading.Lock()

# Store results
all_predictions = []
results_lock = threading.Lock()

# Processing status
processing_status = {
    'active': False,
    'total_stocks': 0,
    'completed_stocks': 0,
    'start_time': None
}

# Stock distribution (50 stocks split into 3 groups)
STOCK_GROUPS = {
    'worker1': ['AAPL', 'AMD', 'AMZN', 'ABT', 'ABBV', 'AXP', 'BA', 'BAC', 'BLK', 'BMY', 'C', 'CAT', 'COP', 'COST', 'CVX', 'DHR', 'DIS'],
    'worker2': ['EOG', 'GE', 'GOOGL', 'GS', 'HD', 'HON', 'INTC', 'JNJ', 'JPM', 'LLY', 'LOW', 'MCD', 'MRK', 'MS', 'MSFT', 'META', 'MMM'],
    'worker3': ['NFLX', 'NKE', 'NVDA', 'ORCL', 'PFE', 'SBUX', 'SCHW', 'SLB', 'TGT', 'TMO', 'TSLA', 'UNH', 'V', 'WFC', 'WMT', 'XOM']
}


# ============================================================
# WORKER MANAGEMENT
# ============================================================

@app.route('/register', methods=['POST'])
def register_worker():
    """Worker registration endpoint"""
    data = request.json
    worker_id = data.get('worker_id')
    worker_url = data.get('worker_url')  # Get URL from worker
    worker_ip = request.remote_addr
    
    # If worker didn't provide URL, construct it from IP
    if not worker_url:
        worker_url = f"http://{worker_ip}:5000"
    
    with worker_lock:
        workers[worker_id] = {
            'id': worker_id,
            'ip': worker_ip,
            'url': worker_url,  # Use provided URL
            'online': True,
            'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tasks_completed': 0,
            'assigned_stocks': []
        }
    
    print(f"[OK] Worker {worker_id} registered from {worker_ip}")
    print(f"[OK] Worker URL: {worker_url}")
    
    return jsonify({
        'status': 'registered',
        'worker_id': worker_id,
        'message': 'Successfully registered with master'
    })


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    """Worker heartbeat to maintain connection"""
    data = request.json
    worker_id = data.get('worker_id')
    
    with worker_lock:
        if worker_id in workers:
            workers[worker_id]['online'] = True
            workers[worker_id]['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({'status': 'ok'})


@app.route('/submit_result', methods=['POST'])
def submit_result():
    """Workers submit their results here"""
    data = request.json
    worker_id = data.get('worker_id')
    results = data.get('results', [])
    
    with worker_lock:
        if worker_id in workers:
            workers[worker_id]['tasks_completed'] += len(results)
    
    with results_lock:
        all_predictions.extend(results)
        processing_status['completed_stocks'] += len(results)
    
    print(f"[OK] Received {len(results)} predictions from Worker {worker_id}")
    
    return jsonify({'status': 'received'})


# ============================================================
# API ENDPOINTS FOR FRONTEND
# ============================================================

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Get all stock predictions"""
    with results_lock:
        return jsonify({
            'predictions': all_predictions,
            'total': len(all_predictions),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })


@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock(ticker):
    """Get prediction for specific stock"""
    with results_lock:
        stock_pred = next((p for p in all_predictions if p['ticker'] == ticker), None)
        
        if stock_pred:
            return jsonify(stock_pred)
        else:
            return jsonify({'error': 'Stock not found'}), 404


@app.route('/api/workers', methods=['GET'])
def get_workers():
    """Get worker status"""
    with worker_lock:
        worker_list = list(workers.values())
    
    return jsonify({
        'workers': worker_list,
        'total': len(worker_list),
        'online': len([w for w in worker_list if w['online']])
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    with results_lock:
        predictions = all_predictions.copy()
    
    if not predictions:
        return jsonify({
            'total_stocks': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'avg_sentiment': 0,
            'processing': processing_status['active']
        })
    
    buy = len([p for p in predictions if p['recommendation'] == 'BUY'])
    sell = len([p for p in predictions if p['recommendation'] == 'SELL'])
    hold = len([p for p in predictions if p['recommendation'] == 'HOLD'])
    avg_sentiment = sum(p['sentiment'] for p in predictions) / len(predictions)
    
    return jsonify({
        'total_stocks': len(predictions),
        'buy_signals': buy,
        'sell_signals': sell,
        'hold_signals': hold,
        'avg_sentiment': round(avg_sentiment, 3),
        'processing': processing_status['active'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/start', methods=['POST'])
def start_processing():
    """Start distributed processing"""
    
    with worker_lock:
        online_workers = {k: v for k, v in workers.items() if v['online']}
    
    if len(online_workers) == 0:
        return jsonify({'status': 'error', 'message': 'No workers available'}), 400
    
    print("\n" + "="*60)
    print("STARTING DISTRIBUTED STOCK ANALYSIS")
    print("="*60)
    
    # Load data
    try:
        stock_df = pd.read_csv('data/stock_prices.csv')
        news_df = pd.read_csv('data/processed_news.csv')
        print(f"[OK] Loaded {len(stock_df)} stock records")
        print(f"[OK] Loaded {len(news_df)} news articles")
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to load data: {e}'}), 500
    
    # Clear previous results
    with results_lock:
        all_predictions.clear()
        processing_status['active'] = True
        processing_status['total_stocks'] = 50
        processing_status['completed_stocks'] = 0
        processing_status['start_time'] = time.time()
    
    # Distribute tasks
    def distribute_tasks():
        worker_ids = list(online_workers.keys())
        
        for i, worker_id in enumerate(worker_ids):
            # Assign stock group
            group_key = f'worker{i+1}' if i < 3 else 'worker3'
            assigned_stocks = STOCK_GROUPS.get(group_key, [])
            
            # Filter data for assigned stocks
            worker_stock_data = stock_df[stock_df['Ticker'].isin(assigned_stocks)]
            worker_news_data = news_df[news_df['mentioned_stocks'].notna()]
            
            # Update worker assignment
            with worker_lock:
                workers[worker_id]['assigned_stocks'] = assigned_stocks
            
            print(f"\n[Worker {worker_id}]")
            print(f"  Assigned stocks: {len(assigned_stocks)}")
            print(f"  Stock records: {len(worker_stock_data)}")
            
            # Send task to worker
            try:
                worker_url = online_workers[worker_id]['url']
                response = requests.post(
                    f"{worker_url}/process_stocks",
                    json={
                        'stocks': assigned_stocks,
                        'stock_data': worker_stock_data.to_dict('records'),
                        'news_data': worker_news_data.to_dict('records')
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    print(f"  [OK] Task sent successfully")
                else:
                    print(f"  [ERROR] Task failed: {response.status_code}")
            
            except Exception as e:
                print(f"  [ERROR] Failed to send task: {e}")
        
        processing_status['active'] = False
        
        # Save results to CSV
        if all_predictions:
            os.makedirs('results', exist_ok=True)
            results_df = pd.DataFrame(all_predictions)
            results_df.to_csv('results/predictions.csv', index=False)
            print(f"\n[OK] Saved {len(all_predictions)} predictions to results/predictions.csv")
    
    # Start distribution in background
    threading.Thread(target=distribute_tasks, daemon=True).start()
    
    return jsonify({
        'status': 'started',
        'message': f'Processing started with {len(online_workers)} workers',
        'workers': len(online_workers),
        'total_stocks': 50
    })


@app.route('/')
def dashboard():
    """Simple status page"""
    with worker_lock:
        worker_count = len([w for w in workers.values() if w['online']])
    
    with results_lock:
        prediction_count = len(all_predictions)
    
    return f"""
    <html>
    <head><title>Stock Prediction Master Node</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>Stock Prediction Master Node</h1>
        <h2>Status</h2>
        <p>Workers Online: {worker_count}</p>
        <p>Predictions: {prediction_count}</p>
        <p>Processing: {'Yes' if processing_status['active'] else 'No'}</p>
        
        <h2>API Endpoints</h2>
        <ul>
            <li><a href="/api/predictions">/api/predictions</a> - All predictions</li>
            <li><a href="/api/workers">/api/workers</a> - Worker status</li>
            <li><a href="/api/stats">/api/stats</a> - Statistics</li>
            <li>POST /api/start - Start processing</li>
        </ul>
        
        <h2>Actions</h2>
        <button onclick="fetch('/api/start', {{method: 'POST'}}).then(r => r.json()).then(d => alert(JSON.stringify(d)))">
            Start Processing
        </button>
    </body>
    </html>
    """


if __name__ == '__main__':
    print("="*60)
    print("MASTER NODE - STOCK PREDICTION SYSTEM")
    print("="*60)
    print("API Endpoints:")
    print("  GET  /api/predictions - All stock predictions")
    print("  GET  /api/stock/<ticker> - Single stock")
    print("  GET  /api/workers - Worker status")
    print("  GET  /api/stats - Statistics")
    print("  POST /api/start - Start processing")
    print("\nDashboard: http://localhost:5000")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
