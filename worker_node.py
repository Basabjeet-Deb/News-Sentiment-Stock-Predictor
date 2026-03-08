"""
Worker Node - Connects to master and processes tasks
Your teammates run this on their machines
"""

from flask import Flask, request, jsonify
import requests
import time
import threading
import os
import socket
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)

# Configuration
MASTER_URL = os.getenv('MASTER_URL', 'http://192.168.1.2:5000')  # Master IP
WORKER_ID = os.getenv('WORKER_ID', socket.gethostname())

# Sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Worker state
worker_state = {
    'registered': False,
    'tasks_processed': 0
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
                print(f"✓ Successfully registered with master at {MASTER_URL}")
                return True
            else:
                print(f"✗ Registration failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Cannot connect to master (attempt {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("✗ Failed to register with master after all retries")
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
        'tasks_processed': worker_state['tasks_processed']
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'worker_id': WORKER_ID})


@app.route('/process', methods=['POST'])
def process_task():
    """Process news sentiment analysis task from master"""
    data = request.json
    news_list = data.get('news', [])
    
    if not news_list:
        return jsonify({'error': 'No news data provided'}), 400
    
    print(f"[Worker {WORKER_ID}] Processing {len(news_list)} news items...")
    
    # Perform sentiment analysis
    sentiments = []
    for text in news_list:
        scores = analyzer.polarity_scores(text)
        sentiments.append(scores['compound'])
    
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    
    worker_state['tasks_processed'] += len(news_list)
    
    # Send results back to master
    try:
        requests.post(
            f"{MASTER_URL}/submit_result",
            json={
                'worker_id': WORKER_ID,
                'count': len(sentiments),
                'avg_sentiment': avg_sentiment,
                'sentiments': sentiments
            },
            timeout=10
        )
        print(f"✓ Submitted results to master (avg sentiment: {avg_sentiment:.4f})")
    except Exception as e:
        print(f"✗ Failed to submit results: {e}")
    
    return jsonify({
        'status': 'completed',
        'worker_id': WORKER_ID,
        'processed': len(sentiments),
        'avg_sentiment': avg_sentiment
    })


if __name__ == '__main__':
    print("="*60)
    print("WORKER NODE STARTING")
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
