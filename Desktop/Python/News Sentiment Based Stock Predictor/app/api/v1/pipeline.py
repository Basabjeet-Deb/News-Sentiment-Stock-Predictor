"""
Pipeline API endpoints
"""

from fastapi import APIRouter, Depends, BackgroundTasks, Query
from typing import Optional
from datetime import datetime

from app.services.pipeline_service import PipelineService
from app.core.dependencies import get_pipeline_service

router = APIRouter()

# Store for background task status
_pipeline_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
}


@router.get("/status")
async def get_pipeline_status():
    """
    Get current pipeline status.
    
    Shows whether pipeline is running and last run results.
    """
    pipeline_service = get_pipeline_service()
    
    return {
        "is_running": _pipeline_status["running"],
        "last_run": _pipeline_status["last_run"],
        "last_result": _pipeline_status["last_result"],
        "data_status": pipeline_service.get_last_run_status(),
        "timestamp": datetime.now().isoformat()
    }


def _run_pipeline_task(max_articles: int):
    """Background task to run pipeline"""
    global _pipeline_status
    
    _pipeline_status["running"] = True
    _pipeline_status["last_run"] = datetime.now().isoformat()
    
    try:
        pipeline_service = PipelineService()
        result = pipeline_service.run_full_pipeline(max_articles)
        _pipeline_status["last_result"] = result
    except Exception as e:
        _pipeline_status["last_result"] = {
            "status": "error",
            "error": str(e),
        }
    finally:
        _pipeline_status["running"] = False


@router.post("/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    max_articles: int = Query(1000, ge=100, le=2000, description="Max news articles to fetch"),
):
    """
    Run the complete prediction pipeline.
    
    This runs in the background and fetches news, analyzes sentiment,
    gets prices, and generates predictions.
    
    **Note**: This may take several minutes to complete.
    """
    if _pipeline_status["running"]:
        return {
            "status": "already_running",
            "message": "Pipeline is already running. Check /status for progress.",
            "timestamp": datetime.now().isoformat()
        }
    
    # Start pipeline in background
    background_tasks.add_task(_run_pipeline_task, max_articles)
    
    return {
        "status": "started",
        "message": f"Pipeline started with max_articles={max_articles}. Check /status for progress.",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/run-sync")
async def run_pipeline_sync(
    max_articles: int = Query(500, ge=100, le=1000, description="Max news articles"),
):
    """
    Run pipeline synchronously (blocking).
    
    **Warning**: This blocks the request until complete (may take minutes).
    Use /run for non-blocking execution.
    """
    if _pipeline_status["running"]:
        return {
            "status": "already_running",
            "message": "Pipeline is already running.",
        }
    
    _pipeline_status["running"] = True
    _pipeline_status["last_run"] = datetime.now().isoformat()
    
    try:
        pipeline_service = PipelineService()
        result = pipeline_service.run_full_pipeline(max_articles)
        _pipeline_status["last_result"] = result
        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
        }
        _pipeline_status["last_result"] = error_result
        return error_result
    finally:
        _pipeline_status["running"] = False


@router.post("/quick-update")
async def run_quick_update(
    background_tasks: BackgroundTasks,
):
    """
    Run a quick update (fewer articles, uses cached prices).
    
    Faster than full pipeline run.
    """
    if _pipeline_status["running"]:
        return {
            "status": "already_running",
            "message": "Pipeline is already running.",
        }
    
    def quick_update_task():
        global _pipeline_status
        _pipeline_status["running"] = True
        try:
            pipeline_service = PipelineService()
            result = pipeline_service.run_quick_update()
            _pipeline_status["last_result"] = result
        except Exception as e:
            _pipeline_status["last_result"] = {"status": "error", "error": str(e)}
        finally:
            _pipeline_status["running"] = False
    
    background_tasks.add_task(quick_update_task)
    
    return {
        "status": "started",
        "message": "Quick update started. Check /status for progress.",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/data")
async def get_loaded_data():
    """
    Get summary of currently loaded data.
    
    Shows counts of news, predictions, and prices.
    """
    pipeline_service = get_pipeline_service()
    data = pipeline_service.load_existing_data()
    
    return {
        "news_count": data["news_count"],
        "predictions_count": data["predictions_count"],
        "prices_count": data["prices_count"],
        "has_data": data["news_count"] > 0 and data["predictions_count"] > 0,
        "timestamp": datetime.now().isoformat()
    }
