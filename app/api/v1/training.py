"""
Training API endpoints for ML model training
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import os
from datetime import datetime

router = APIRouter()

class CollectDataRequest(BaseModel):
    months: int = 3
    tickers: Optional[List[str]] = None

class TrainingStatus(BaseModel):
    status: str
    message: str
    timestamp: str

# Track training status
training_status = {
    "is_training": False,
    "last_training": None,
    "last_collection": None
}

@router.post("/collect-data")
async def collect_historical_data(request: CollectDataRequest, background_tasks: BackgroundTasks):
    """
    Collect historical data for ML training
    
    This endpoint triggers the historical data collection process
    """
    try:
        if training_status["is_training"]:
            return {
                "status": "busy",
                "message": "Training or data collection already in progress",
                "timestamp": datetime.now().isoformat()
            }
        
        # Mark as busy
        training_status["is_training"] = True
        
        # Run data collection in background
        def collect_data():
            try:
                # Use the quick ML prep script which uses existing cached data
                result = subprocess.run(
                    ["python", "pipeline/quick_ml_prep.py"],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                training_status["last_collection"] = datetime.now().isoformat()
                training_status["is_training"] = False
                
                if result.returncode == 0:
                    print(f"[OK] Data collection completed")
                    print(result.stdout)
                else:
                    print(f"[ERROR] Data collection failed: {result.stderr}")
                    
            except Exception as e:
                print(f"[ERROR] Data collection error: {e}")
                training_status["is_training"] = False
        
        background_tasks.add_task(collect_data)
        
        return {
            "status": "started",
            "message": f"Historical data collection started for {request.months} months",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        training_status["is_training"] = False
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-model")
async def train_model(background_tasks: BackgroundTasks):
    """
    Train the ML prediction model
    
    This endpoint triggers the model training process using collected historical data
    """
    try:
        if training_status["is_training"]:
            return {
                "status": "busy",
                "message": "Training or data collection already in progress",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if training data exists
        training_data_path = "data/ml_training_data.csv"
        if not os.path.exists(training_data_path):
            return {
                "status": "error",
                "message": "No training data found. Please collect historical data first.",
                "timestamp": datetime.now().isoformat()
            }
        
        # Mark as busy
        training_status["is_training"] = True
        
        # Run training in background
        def train():
            try:
                # Run the ML training script
                result = subprocess.run(
                    ["python", "pipeline/forecaster.py"],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minute timeout
                )
                
                training_status["last_training"] = datetime.now().isoformat()
                training_status["is_training"] = False
                
                if result.returncode == 0:
                    print(f"[OK] Model training completed")
                else:
                    print(f"[ERROR] Model training failed: {result.stderr}")
                    
            except Exception as e:
                print(f"[ERROR] Training error: {e}")
                training_status["is_training"] = False
        
        background_tasks.add_task(train)
        
        return {
            "status": "started",
            "message": "Model training started. This may take several minutes.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        training_status["is_training"] = False
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_training_status():
    """Get current training status"""
    return {
        "is_training": training_status["is_training"],
        "last_training": training_status["last_training"],
        "last_collection": training_status["last_collection"],
        "timestamp": datetime.now().isoformat()
    }
