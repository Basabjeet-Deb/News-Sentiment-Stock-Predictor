"""
Cluster Client - Send commands to cluster
"""

import requests
import time
import sys

MASTER_URL = "http://192.168.1.100:8000"  # UPDATE THIS


def send_command(command, target="all"):
    """Send command to cluster"""
    try:
        response = requests.post(
            f"{MASTER_URL}/execute",
            json={
                "command": command,
                "target": target
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


def get_command_status(command_id):
    """Get command status and results"""
    try:
        response = requests.get(
            f"{MASTER_URL}/command/{command_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_workers():
    """Get list of workers"""
    try:
        response = requests.get(f"{MASTER_URL}/workers", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def wait_for_results(command_id, timeout=60):
    """Wait for command to complete"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = get_command_status(command_id)
        
        if status and status.get("status") == "completed":
            return status
        
        time.sleep(2)
    
    return None


def main():
    print("="*60)
    print("CLUSTER CLIENT - COMMAND INTERFACE")
    print("="*60)
    print(f"Master URL: {MASTER_URL}\n")
    
    if len(sys.argv) > 1:
        # Command line mode
        command = " ".join(sys.argv[1:])
        
        print(f"Executing: {command}\n")
        
        command_id = send_command(command)
        
        if command_id:
            print(f"Command ID: {command_id}")
            print("Waiting for results...\n")
            
            result = wait_for_results(command_id)
            
            if result:
                print("="*60)
                print("RESULTS")
                print("="*60)
                
                for worker_id, worker_result in result.get("results", {}).items():
                    print(f"\n[{worker_id}]")
                    print(f"Exit Code: {worker_result.get('exit_code')}")
                    
                    output = worker_result.get('output', '').strip()
                    if output:
                        print(f"Output:\n{output}")
                    
                    error = worker_result.get('error')
                    if error:
                        print(f"Error:\n{error}")
                    
                    print("-"*60)
            else:
                print("Timeout waiting for results")
    
    else:
        # Interactive mode
        print("Commands:")
        print("  exec <command>  - Execute command on all workers")
        print("  workers         - List workers")
        print("  status <id>     - Get command status")
        print("  quit            - Exit")
        print("-"*60)
        
        while True:
            try:
                cmd = input("\n> ").strip()
                
                if not cmd:
                    continue
                
                if cmd == "quit":
                    break
                
                elif cmd == "workers":
                    workers = get_workers()
                    if workers:
                        print(f"\nTotal Workers: {workers['total']}")
                        for w in workers.get('workers', []):
                            print(f"  - {w['worker_id']} ({w['ip']}) - {w['status']}")
                
                elif cmd.startswith("exec "):
                    command = cmd[5:].strip()
                    
                    command_id = send_command(command)
                    
                    if command_id:
                        print(f"Command ID: {command_id}")
                        print("Waiting for results...")
                        
                        result = wait_for_results(command_id)
                        
                        if result:
                            print("\nResults:")
                            for worker_id, worker_result in result.get("results", {}).items():
                                print(f"\n[{worker_id}]")
                                output = worker_result.get('output', '').strip()
                                if output:
                                    print(output)
                        else:
                            print("Timeout")
                
                elif cmd.startswith("status "):
                    command_id = cmd[7:].strip()
                    status = get_command_status(command_id)
                    
                    if status:
                        print(f"\nStatus: {status.get('status')}")
                        print(f"Command: {status.get('command')}")
                        print(f"Results: {len(status.get('results', {}))}/{len(status.get('target_workers', []))}")
                
                else:
                    print("Invalid command")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
