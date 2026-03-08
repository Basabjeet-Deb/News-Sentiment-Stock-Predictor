"""
Master Node - Coordinates distributed processing
Teammates connect their worker nodes to this master
"""

from flask import Flask, request, jsonify, render_template_string
import requests
import time
import threading
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)

# Store connected workers
workers = {}
worker_lock = threading.Lock()

# Store processing results
results = []
results_lock = threading.Lock()

# Processing status
processing_status = {
    'active': False,
    'total_tasks': 0,
    'completed_tasks': 0,
    'start_time': None
}


@app.route('/')
def dashboard():
    """Master dashboard"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Master Node Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
            .card { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .worker { padding: 10px; margin: 10px 0; background: #ecf0f1; border-radius: 3px; }
            .online { border-left: 5px solid #27ae60; }
            .offline { border-left: 5px solid #e74c3c; }
            .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
            .btn:hover { background: #2980b9; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #34495e; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Master Node Dashboard</h1>
                <p>Distributed News Sentiment Analysis Cluster</p>
            </div>
            
            <div class="card">
                <h2>📊 Cluster Status</h2>
                <p><strong>Master Node:</strong> Online</p>
                <p><strong>Connected Workers:</strong> {{ worker_count }}</p>
                <p><strong>Processing Status:</strong> {{ 'Active' if status.active else 'Idle' }}</p>
                {% if status.active %}
                <p><strong>Progress:</strong> {{ status.completed_tasks }}/{{ status.total_tasks }} tasks</p>
                {% endif %}
            </div>
            
            <div class="card">
                <h2>👥 Connected Workers</h2>
                {% if workers %}
                    {% for worker_id, worker in workers.items() %}
                    <div class="worker {{ 'online' if worker.online else 'offline' }}">
                        <strong>Worker {{ worker_id }}</strong><br>
                        IP: {{ worker.ip }}<br>
                        Status: {{ 'Online ✓' if worker.online else 'Offline ✗' }}<br>
                        Last Seen: {{ worker.last_seen }}<br>
                        Tasks Completed: {{ worker.tasks_completed }}
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No workers connected yet.</p>
                    <p><strong>Workers should connect to:</strong> http://YOUR_IP:5000/register</p>
                {% endif %}
            </div>
            
            <div class="card">
                <h2>🚀 Actions</h2>
                <button class="btn" onclick="startProcessing()">Start Processing</button>
                <button class="btn" onclick="location.reload()">Refresh</button>
            </div>
            
            <div class="card">
                <h2>📈 Recent Results</h2>
                {% if results %}
                <table>
                    <tr>
                        <th>Worker</th>
                        <th>Tasks</th>
                        <th>Avg Sentiment</th>
                        <th>Time</th>
                    </tr>
                    {% for result in results[-10:] %}
                    <tr>
                        <td>{{ result.worker_id }}</td>
                        <td>{{ result.count }}</td>
                        <td>{{ "%.4f"|format(result.avg_sentiment) }}</td>
                        <td>{{ result.timestamp }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No results yet.</p>
                {% endif %}
            </div>
        </div>
        
        <script>
            function startProcessing() {
                fetch('/start_processing', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    });
            }
        </script>
    </body>
    </html>
    """
    
    with worker_lock:
        worker_list = {k: {
            'ip': v['ip'],
            'online': v['online'],
            'last_seen': v['last_seen'],
            'tasks_completed': v['tasks_completed']
        } for k, v in workers.items()}
    
    with results_lock:
        result_list = results.copy()
    
    return render_template_string(
        html,
        workers=worker_list,
        worker_count=len([w for w in worker_list.values() if w['online']]),
        status=processing_status,
        results=result_list
    )


@app.route('/register', methods=['POST'])
def register_worker():
    """Worker registration endpoint"""
    data = request.json
    worker_id = data.get('worker_id')
    worker_ip = request.remote_addr
    
    with worker_lock:
        workers[worker_id] = {
            'id': worker_id,
            'ip': worker_ip,
            'url': f"http://{worker_ip}:5000",
            'online': True,
            'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tasks_completed': 0
        }
    
    print(f"✓ Worker {worker_id} registered from {worker_ip}")
    
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
    
    with worker_lock:
        if worker_id in workers:
            workers[worker_id]['tasks_completed'] += 1
    
    with results_lock:
        results.append({
            'worker_id': worker_id,
            'count': data.get('count', 0),
            'avg_sentiment': data.get('avg_sentiment', 0),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        processing_status['completed_tasks'] += 1
    
    print(f"✓ Received results from Worker {worker_id}")
    
    return jsonify({'status': 'received'})


@app.route('/start_processing', methods=['POST'])
def start_processing():
    """Start distributed processing"""
    with worker_lock:
        online_workers = [w for w in workers.values() if w['online']]
    
    if not online_workers:
        return jsonify({'status': 'error', 'message': 'No workers available'})
    
    # Load data
    data_path = 'data/gdelt_english_news.csv'
    if not os.path.exists(data_path):
        # Use sample data
        news_data = [
            "Stock market reaches all-time high",
            "Tech company announces layoffs",
            "Federal Reserve raises interest rates",
            "Oil prices surge amid tensions",
            "Bank reports record profits",
            "Cryptocurrency market crashes",
            "Manufacturing sector slows down",
            "Consumer confidence drops",
            "Tech stocks rally on earnings",
            "Supply chain issues persist"
        ] * 10
    else:
        df = pd.read_csv(data_path)
        news_data = df.iloc[:, 0].dropna().tolist()[:100]
    
    # Distribute tasks
    chunk_size = len(news_data) // len(online_workers)
    
    processing_status['active'] = True
    processing_status['total_tasks'] = len(online_workers)
    processing_status['completed_tasks'] = 0
    processing_status['start_time'] = time.time()
    
    def distribute_tasks():
        for i, worker in enumerate(online_workers):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < len(online_workers) - 1 else len(news_data)
            chunk = news_data[start_idx:end_idx]
            
            try:
                response = requests.post(
                    f"{worker['url']}/process",
                    json={'news': chunk},
                    timeout=30
                )
                print(f"✓ Sent {len(chunk)} items to Worker {worker['id']}")
            except Exception as e:
                print(f"✗ Failed to send to Worker {worker['id']}: {e}")
        
        processing_status['active'] = False
    
    threading.Thread(target=distribute_tasks, daemon=True).start()
    
    return jsonify({
        'status': 'started',
        'message': f'Processing started with {len(online_workers)} workers'
    })


@app.route('/status')
def status():
    """API endpoint for cluster status"""
    with worker_lock:
        worker_count = len([w for w in workers.values() if w['online']])
    
    return jsonify({
        'master': 'online',
        'workers': worker_count,
        'processing': processing_status['active']
    })


if __name__ == '__main__':
    print("="*60)
    print("MASTER NODE STARTING")
    print("="*60)
    print(f"Dashboard: http://localhost:5000")
    print(f"Workers should register at: http://YOUR_IP:5000/register")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
