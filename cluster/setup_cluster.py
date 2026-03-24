"""
Setup cluster for distributed analysis
Copies data files to all worker nodes
"""

import requests
import time

MASTER_URL = "http://192.168.1.100:8000"  # UPDATE THIS


def send_setup_command(command):
    """Send setup command to all workers"""
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
            return response.json().get("command_id")
        return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def wait_for_completion(command_id):
    """Wait for command to complete"""
    for _ in range(30):
        try:
            response = requests.get(f"{MASTER_URL}/command/{command_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "completed":
                    return True
            time.sleep(2)
        except:
            time.sleep(2)
    return False


def main():
    print("="*60)
    print("CLUSTER SETUP FOR DISTRIBUTED ANALYSIS")
    print("="*60)
    
    # Check workers
    try:
        response = requests.get(f"{MASTER_URL}/workers", timeout=10)
        workers = response.json()
        num_workers = workers.get('total', 0)
        
        if num_workers == 0:
            print("\n[ERROR] No workers available")
            return
        
        print(f"\n[OK] Found {num_workers} workers")
    except Exception as e:
        print(f"\n[ERROR] Cannot connect to master: {e}")
        return
    
    # Setup commands
    commands = [
        ("Create data directory", "mkdir -p data"),
        ("Install pandas", "pip install pandas numpy vaderSentiment -q"),
        ("Check Python", "python --version")
    ]
    
    for description, command in commands:
        print(f"\n[SETUP] {description}...")
        command_id = send_setup_command(command)
        
        if command_id:
            if wait_for_completion(command_id):
                print(f"  [OK] Completed")
            else:
                print(f"  [WARN] Timeout")
        else:
            print(f"  [ERROR] Failed to send command")
    
    print("\n" + "="*60)
    print("SETUP COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Copy data files to workers manually or via shared storage")
    print("2. Run: python distributed_analyze.py")


if __name__ == "__main__":
    main()
