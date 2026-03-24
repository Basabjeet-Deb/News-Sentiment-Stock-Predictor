"""
Cluster Worker - Command Execution Node
Receives and executes commands from master
"""

from flask import Flask, request, jsonify
import subprocess
import requests
import threading
import time
import socket
import os

app = Flask(__name__)

# Configuration
MASTER_URL = os.getenv('MASTER_URL', 'http://192.168.1.100:8000')  # UPDATE THIS
WORKER_ID = os.getenv('WORKER_ID', socket.gethostname())
WORKER_IP = socket.gethostbyname(socket.gethostname())

# State
worker_state = {
    'registered': False,
    'commands_executed': 0
}


def register_with_master():
    """Register with master"""
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{MASTER_URL}/register",
                json={
                    "worker_id": WORKER_ID,
                    "worker_ip": WORKER_IP
                },
                timeout=10
            )
            
            if response.status_code == 200:
                worker_state['registered'] = True
                print(f"[OK] Registered with master at {MASTER_URL}")
                return True
            else:
                print(f"[ERROR] Registration failed: {response.status_code}")
        
        except Exception as e:
            print(f"[ERROR] Cannot connect to master (attempt {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in 5 seconds...")
            time.sleep(5)
    
    print("[ERROR] Failed to register with master")
    return False


def send_heartbeat():
    """Send periodic heartbeat to master"""
    while True:
        if worker_state['registered']:
            try:
                requests.post(
                    f"{MASTER_URL}/heartbeat",
                    params={"worker_id": WORKER_ID},
                    timeout=5
                )
            except:
                pass
        
        time.sleep(10)


@app.route('/')
def home():
    return jsonify({
        "node_type": "worker",
        "worker_id": WORKER_ID,
        "worker_ip": WORKER_IP,
        "master_url": MASTER_URL,
        "registered": worker_state['registered'],
        "commands_executed": worker_state['commands_executed']
    })


@app.route('/health')
def health():
    return jsonify({"status": "healthy"})


@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute command received from master"""
    
    data = request.json
    command_id = data.get('command_id')
    command = data.get('command')
    
    print(f"\n[COMMAND] Received: {command}")
    
    try:
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = result.stdout
        error = result.stderr if result.returncode != 0 else None
        exit_code = result.returncode
        
        print(f"[OK] Executed with exit code {exit_code}")
        
        worker_state['commands_executed'] += 1
        
        # Send result back to master
        try:
            requests.post(
                f"{MASTER_URL}/result",
                json={
                    "command_id": command_id,
                    "worker_id": WORKER_ID,
                    "output": output,
                    "error": error,
                    "exit_code": exit_code
                },
                timeout=10
            )
            print(f"[OK] Result sent to master")
        
        except Exception as e:
            print(f"[ERROR] Failed to send result: {e}")
        
        return jsonify({
            "status": "executed",
            "exit_code": exit_code
        })
    
    except subprocess.TimeoutExpired:
        error_msg = "Command execution timeout (5 minutes)"
        print(f"[ERROR] {error_msg}")
        
        return jsonify({
            "status": "error",
            "error": error_msg
        }), 500
    
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {error_msg}")
        
        return jsonify({
            "status": "error",
            "error": error_msg
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("CLUSTER WORKER - COMMAND EXECUTION")
    print("="*60)
    print(f"Worker ID: {WORKER_ID}")
    print(f"Worker IP: {WORKER_IP}")
    print(f"Master URL: {MASTER_URL}")
    print("="*60)
    
    # Register with master
    if register_with_master():
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        print(f"\nWorker listening on port 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("Failed to start worker - could not register with master")
