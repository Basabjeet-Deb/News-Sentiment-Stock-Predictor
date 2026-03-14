"""
Distributed Computing Master Node
Pull-based task distribution system
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
from datetime import datetime
import threading

app = FastAPI(title="Distributed Master")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
task_queue: List[Dict] = []
pending_tasks: Dict[str, Dict] = {}
completed_tasks: Dict[str, Dict] = {}
workers: Dict[str, Dict] = {}

lock = threading.Lock()


class Task(BaseModel):
    operation: str
    value: int


class TaskResult(BaseModel):
    task_id: str
    result: Optional[int] = None
    error: Optional[str] = None
    worker_id: str


class WorkerRegistration(BaseModel):
    worker_id: str


@app.get("/")
def home():
    return {
        "service": "Distributed Computing Master",
        "status": "running",
        "tasks_queued": len(task_queue),
        "tasks_pending": len(pending_tasks),
        "tasks_completed": len(completed_tasks),
        "workers": len(workers)
    }


@app.post("/submit_task")
def submit_task(task: Task):
    """Client submits a task"""
    task_id = str(uuid.uuid4())
    
    task_data = {
        "task_id": task_id,
        "operation": task.operation,
        "value": task.value,
        "submitted_at": datetime.now().isoformat(),
        "status": "queued"
    }
    
    with lock:
        task_queue.append(task_data)
    
    return {
        "status": "accepted",
        "task_id": task_id,
        "message": "Task queued for processing"
    }


@app.post("/register_worker")
def register_worker(worker: WorkerRegistration):
    """Worker registers with master"""
    with lock:
        workers[worker.worker_id] = {
            "worker_id": worker.worker_id,
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "tasks_completed": 0
        }
    
    return {
        "status": "registered",
        "worker_id": worker.worker_id
    }


@app.get("/get_task")
def get_task(worker_id: str):
    """Worker requests a task (pull-based)"""
    
    # Update worker last seen
    with lock:
        if worker_id in workers:
            workers[worker_id]["last_seen"] = datetime.now().isoformat()
    
    with lock:
        if not task_queue:
            return {"status": "no_task", "message": "No tasks available"}
        
        # Get next task
        task = task_queue.pop(0)
        task["status"] = "processing"
        task["worker_id"] = worker_id
        task["started_at"] = datetime.now().isoformat()
        
        # Move to pending
        pending_tasks[task["task_id"]] = task
    
    return {
        "status": "task_assigned",
        "task": task
    }


@app.post("/submit_result")
def submit_result(result: TaskResult):
    """Worker submits task result"""
    
    with lock:
        # Remove from pending
        if result.task_id in pending_tasks:
            task = pending_tasks.pop(result.task_id)
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update task
        task["status"] = "completed" if not result.error else "failed"
        task["result"] = result.result
        task["error"] = result.error
        task["completed_at"] = datetime.now().isoformat()
        task["worker_id"] = result.worker_id
        
        # Move to completed
        completed_tasks[result.task_id] = task
        
        # Update worker stats
        if result.worker_id in workers:
            workers[result.worker_id]["tasks_completed"] += 1
    
    return {
        "status": "accepted",
        "message": "Result recorded"
    }


@app.get("/results")
def get_results():
    """Get all completed results"""
    return {
        "total": len(completed_tasks),
        "results": list(completed_tasks.values())
    }


@app.get("/results/{task_id}")
def get_result(task_id: str):
    """Get specific task result"""
    if task_id in completed_tasks:
        return completed_tasks[task_id]
    elif task_id in pending_tasks:
        return {"status": "processing", "task": pending_tasks[task_id]}
    elif any(t["task_id"] == task_id for t in task_queue):
        return {"status": "queued", "message": "Task is queued"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@app.get("/workers")
def get_workers():
    """Get worker status"""
    return {
        "total": len(workers),
        "workers": list(workers.values())
    }


@app.get("/stats")
def get_stats():
    """Get system statistics"""
    return {
        "tasks": {
            "queued": len(task_queue),
            "processing": len(pending_tasks),
            "completed": len(completed_tasks),
            "total": len(task_queue) + len(pending_tasks) + len(completed_tasks)
        },
        "workers": {
            "total": len(workers),
            "active": len([w for w in workers.values()])
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("DISTRIBUTED COMPUTING MASTER")
    print("="*60)
    print("Starting master node on port 8000...")
    print("\nEndpoints:")
    print("  POST /submit_task - Submit a task")
    print("  GET  /get_task?worker_id=X - Worker requests task")
    print("  POST /submit_result - Worker submits result")
    print("  GET  /results - Get all results")
    print("  GET  /workers - Worker status")
    print("="*60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
