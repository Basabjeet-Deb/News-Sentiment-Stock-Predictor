"""
Distributed Computing Worker Node
Pull-based task execution
"""

import requests
import time
import socket
import os
from datetime import datetime

# Configuration
MASTER_URL = os.getenv('MASTER_URL', 'http://localhost:8000')
WORKER_ID = os.getenv('WORKER_ID', socket.gethostname())
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '2'))  # seconds


def execute_task(task):
    """Execute the task operation"""
    operation = task.get('operation')
    value = task.get('value')
    
    try:
        if operation == 'square':
            result = value ** 2
        elif operation == 'cube':
            result = value ** 3
        elif operation == 'double':
            result = value * 2
        elif operation == 'factorial':
            result = 1
            for i in range(1, value + 1):
                result *= i
        elif operation == 'fibonacci':
            if value <= 1:
                result = value
            else:
                a, b = 0, 1
                for _ in range(value - 1):
                    a, b = b, a + b
                result = b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return result, None
    
    except Exception as e:
        return None, str(e)


def register_worker():
    """Register with master"""
    try:
        response = requests.post(
            f"{MASTER_URL}/register_worker",
            json={"worker_id": WORKER_ID},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[OK] Registered with master as {WORKER_ID}")
            return True
        else:
            print(f"[ERROR] Registration failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] Cannot connect to master: {e}")
        return False


def request_task():
    """Request a task from master"""
    try:
        response = requests.get(
            f"{MASTER_URL}/get_task",
            params={"worker_id": WORKER_ID},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "task_assigned":
                return data.get("task")
        
        return None
    
    except Exception as e:
        print(f"[ERROR] Failed to request task: {e}")
        return None


def submit_result(task_id, result, error):
    """Submit task result to master"""
    try:
        response = requests.post(
            f"{MASTER_URL}/submit_result",
            json={
                "task_id": task_id,
                "result": result,
                "error": error,
                "worker_id": WORKER_ID
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"[ERROR] Failed to submit result: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] Failed to submit result: {e}")
        return False


def main():
    print("="*60)
    print("DISTRIBUTED COMPUTING WORKER")
    print("="*60)
    print(f"Worker ID: {WORKER_ID}")
    print(f"Master URL: {MASTER_URL}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print("="*60)
    
    # Register with master
    while not register_worker():
        print("Retrying registration in 5 seconds...")
        time.sleep(5)
    
    print("\n[READY] Worker is ready to process tasks")
    print("Polling for tasks...\n")
    
    tasks_processed = 0
    
    # Main worker loop
    while True:
        try:
            # Request task from master
            task = request_task()
            
            if task:
                task_id = task.get('task_id')
                operation = task.get('operation')
                value = task.get('value')
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Task received: {operation}({value})")
                
                # Execute task
                result, error = execute_task(task)
                
                if error:
                    print(f"  [ERROR] {error}")
                else:
                    print(f"  [OK] Result: {result}")
                
                # Submit result
                if submit_result(task_id, result, error):
                    tasks_processed += 1
                    print(f"  [SUBMITTED] Total processed: {tasks_processed}\n")
            
            # Wait before next poll
            time.sleep(POLL_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Worker stopped by user")
            print(f"Total tasks processed: {tasks_processed}")
            break
        
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
