"""
Distributed Computing Client
Submit tasks and retrieve results
"""

import requests
import time
import sys

MASTER_URL = "http://localhost:8000"


def submit_task(operation, value):
    """Submit a task to the master"""
    try:
        response = requests.post(
            f"{MASTER_URL}/submit_task",
            json={"operation": operation, "value": value},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("task_id")
        else:
            print(f"Error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error submitting task: {e}")
        return None


def get_result(task_id):
    """Get task result"""
    try:
        response = requests.get(
            f"{MASTER_URL}/results/{task_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        print(f"Error getting result: {e}")
        return None


def get_all_results():
    """Get all completed results"""
    try:
        response = requests.get(f"{MASTER_URL}/results", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        print(f"Error getting results: {e}")
        return None


def get_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{MASTER_URL}/stats", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None


def main():
    print("="*60)
    print("DISTRIBUTED COMPUTING CLIENT")
    print("="*60)
    print(f"Master URL: {MASTER_URL}\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # Batch mode: submit multiple tasks
        print("Submitting batch tasks...\n")
        
        tasks = [
            ("square", 5),
            ("cube", 3),
            ("double", 10),
            ("factorial", 5),
            ("fibonacci", 10),
            ("square", 12),
            ("cube", 4),
            ("factorial", 6),
        ]
        
        task_ids = []
        
        for operation, value in tasks:
            task_id = submit_task(operation, value)
            if task_id:
                print(f"[OK] Submitted: {operation}({value}) -> Task ID: {task_id}")
                task_ids.append(task_id)
            time.sleep(0.1)
        
        print(f"\n[OK] Submitted {len(task_ids)} tasks")
        print("\nWaiting for results...\n")
        
        # Wait for all tasks to complete
        completed = 0
        while completed < len(task_ids):
            time.sleep(2)
            results = get_all_results()
            if results:
                completed = results.get("total", 0)
                print(f"Progress: {completed}/{len(task_ids)} completed", end="\r")
        
        print("\n\n[COMPLETED] All tasks finished!\n")
        
        # Display results
        results = get_all_results()
        if results:
            print("Results:")
            print("-" * 60)
            for r in results.get("results", []):
                op = r.get("operation")
                val = r.get("value")
                res = r.get("result")
                err = r.get("error")
                
                if err:
                    print(f"  {op}({val}) = ERROR: {err}")
                else:
                    print(f"  {op}({val}) = {res}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        # Show statistics
        stats = get_stats()
        if stats:
            print("System Statistics:")
            print("-" * 60)
            print(f"Tasks Queued:     {stats['tasks']['queued']}")
            print(f"Tasks Processing: {stats['tasks']['processing']}")
            print(f"Tasks Completed:  {stats['tasks']['completed']}")
            print(f"Total Tasks:      {stats['tasks']['total']}")
            print(f"\nWorkers Active:   {stats['workers']['total']}")
    
    else:
        # Interactive mode
        print("Commands:")
        print("  submit <operation> <value> - Submit a task")
        print("  result <task_id>           - Get task result")
        print("  results                    - Get all results")
        print("  stats                      - Show statistics")
        print("  quit                       - Exit")
        print("\nOperations: square, cube, double, factorial, fibonacci")
        print("-" * 60)
        
        while True:
            try:
                cmd = input("\n> ").strip().split()
                
                if not cmd:
                    continue
                
                if cmd[0] == "quit":
                    break
                
                elif cmd[0] == "submit" and len(cmd) == 3:
                    operation = cmd[1]
                    value = int(cmd[2])
                    task_id = submit_task(operation, value)
                    if task_id:
                        print(f"Task submitted: {task_id}")
                
                elif cmd[0] == "result" and len(cmd) == 2:
                    task_id = cmd[1]
                    result = get_result(task_id)
                    if result:
                        print(result)
                
                elif cmd[0] == "results":
                    results = get_all_results()
                    if results:
                        print(f"Total: {results['total']}")
                        for r in results.get("results", [])[:10]:
                            print(f"  {r['operation']}({r['value']}) = {r.get('result', 'N/A')}")
                
                elif cmd[0] == "stats":
                    stats = get_stats()
                    if stats:
                        print(f"Queued: {stats['tasks']['queued']}, "
                              f"Processing: {stats['tasks']['processing']}, "
                              f"Completed: {stats['tasks']['completed']}")
                
                else:
                    print("Invalid command")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
