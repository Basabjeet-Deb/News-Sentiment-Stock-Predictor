"""
Cluster Master - Command Distribution System
Sends commands to worker nodes and collects results
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
import threading
import time
from datetime import datetime
import uuid

app = FastAPI(title="Cluster Master")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
workers: Dict[str, Dict] = {}
commands: Dict[str, Dict] = {}
results: Dict[str, Dict] = {}

lock = threading.Lock()


class WorkerRegistration(BaseModel):
    worker_id: str
    worker_ip: str


class Command(BaseModel):
    command: str
    target: Optional[str] = "all"  # "all" or specific worker_id


class CommandResult(BaseModel):
    command_id: str
    worker_id: str
    output: str
    error: Optional[str] = None
    exit_code: int


@app.get("/")
def home():
    return {
        "service": "Cluster Master",
        "status": "running",
        "workers": len(workers),
        "commands_sent": len(commands),
        "results_received": len(results)
    }


@app.post("/register")
def register_worker(worker: WorkerRegistration):
    """Worker registers with master"""
    with lock:
        workers[worker.worker_id] = {
            "worker_id": worker.worker_id,
            "ip": worker.worker_ip,
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "status": "online",
            "commands_executed": 0
        }
    
    print(f"[OK] Worker {worker.worker_id} registered from {worker.worker_ip}")
    
    return {
        "status": "registered",
        "worker_id": worker.worker_id
    }


@app.post("/heartbeat")
def heartbeat(worker_id: str):
    """Worker sends heartbeat"""
    with lock:
        if worker_id in workers:
            workers[worker_id]["last_seen"] = datetime.now().isoformat()
            workers[worker_id]["status"] = "online"
    
    return {"status": "ok"}


@app.get("/workers")
def get_workers():
    """Get all registered workers"""
    return {
        "total": len(workers),
        "workers": list(workers.values())
    }


@app.post("/execute")
def execute_command(cmd: Command):
    """Execute command on workers"""
    
    command_id = str(uuid.uuid4())
    
    # Determine target workers
    if cmd.target == "all":
        target_workers = list(workers.keys())
    else:
        if cmd.target not in workers:
            raise HTTPException(status_code=404, detail=f"Worker {cmd.target} not found")
        target_workers = [cmd.target]
    
    if not target_workers:
        raise HTTPException(status_code=400, detail="No workers available")
    
    # Store command
    with lock:
        commands[command_id] = {
            "command_id": command_id,
            "command": cmd.command,
            "target": cmd.target,
            "target_workers": target_workers,
            "submitted_at": datetime.now().isoformat(),
            "status": "pending",
            "results": {}
        }
    
    # Send command to workers in background
    def send_to_workers():
        for worker_id in target_workers:
            try:
                worker_ip = workers[worker_id]["ip"]
                
                response = requests.post(
                    f"http://{worker_ip}:5000/execute",
                    json={
                        "command_id": command_id,
                        "command": cmd.command
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"[OK] Command sent to {worker_id}")
                else:
                    print(f"[ERROR] Failed to send to {worker_id}: {response.status_code}")
            
            except Exception as e:
                print(f"[ERROR] Failed to send to {worker_id}: {e}")
        
        with lock:
            commands[command_id]["status"] = "sent"
    
    threading.Thread(target=send_to_workers, daemon=True).start()
    
    return {
        "status": "accepted",
        "command_id": command_id,
        "target_workers": target_workers,
        "message": f"Command will be executed on {len(target_workers)} worker(s)"
    }


@app.post("/result")
def submit_result(result: CommandResult):
    """Worker submits command result"""
    
    command_id = result.command_id
    
    with lock:
        if command_id not in commands:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Store result
        commands[command_id]["results"][result.worker_id] = {
            "worker_id": result.worker_id,
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code,
            "received_at": datetime.now().isoformat()
        }
        
        # Update worker stats
        if result.worker_id in workers:
            workers[result.worker_id]["commands_executed"] += 1
        
        # Check if all results received
        expected = len(commands[command_id]["target_workers"])
        received = len(commands[command_id]["results"])
        
        if received >= expected:
            commands[command_id]["status"] = "completed"
            commands[command_id]["completed_at"] = datetime.now().isoformat()
    
    return {"status": "accepted"}


@app.get("/command/{command_id}")
def get_command_status(command_id: str):
    """Get command status and results"""
    
    if command_id not in commands:
        raise HTTPException(status_code=404, detail="Command not found")
    
    return commands[command_id]


@app.get("/commands")
def get_all_commands():
    """Get all commands"""
    return {
        "total": len(commands),
        "commands": list(commands.values())
    }


@app.get("/results")
def get_all_results():
    """Get all completed commands with results"""
    completed = [cmd for cmd in commands.values() if cmd["status"] == "completed"]
    
    return {
        "total": len(completed),
        "results": completed
    }


if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("CLUSTER MASTER - COMMAND DISTRIBUTION")
    print("="*60)
    print("Starting master on port 8000...")
    print("\nEndpoints:")
    print("  POST /register - Worker registration")
    print("  POST /execute - Execute command on workers")
    print("  GET  /command/{id} - Get command status")
    print("  GET  /workers - List workers")
    print("  GET  /results - Get all results")
    print("="*60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
