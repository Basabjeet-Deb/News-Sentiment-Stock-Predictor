"""
Predictions API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.services.prediction_service import PredictionService
from app.core.dependencies import get_prediction_service
from app.models.prediction import RecommendationType

router = APIRouter()


@router.get("/")
async def get_predictions(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    recommendation: Optional[str] = Query(None, description="Filter by recommendation (STRONG BUY, BUY, HOLD, SELL, STRONG SELL)"),
    min_score: Optional[float] = Query(None, ge=-1, le=1, description="Minimum prediction score"),
    max_score: Optional[float] = Query(None, ge=-1, le=1, description="Maximum prediction score"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence"),
    min_news_count: Optional[int] = Query(None, ge=0, description="Minimum news articles"),
    sort_by: str = Query("prediction_score", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Get stock predictions with optional filtering.
    
    Returns predictions sorted by score by default, showing top recommendations first.
    """
    # Load predictions from cache or CSV
    predictions = prediction_service.get_cached_predictions()
    if not predictions:
        predictions = prediction_service.load_from_csv()
    
    if not predictions:
        return {
            "total_count": 0,
            "predictions": [],
            "message": "No predictions available. Run the pipeline first.",
            "timestamp": datetime.now().isoformat()
        }
    
    # Filter
    filtered = prediction_service.filter_predictions(
        predictions,
        ticker=ticker,
        sector=sector,
        recommendation=recommendation,
        min_score=min_score,
        max_score=max_score,
        min_confidence=min_confidence,
        min_news_count=min_news_count,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        offset=offset
    )
    
    return {
        "total_count": len(filtered),
        "predictions": filtered,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/summary")
async def get_predictions_summary(
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Get summary statistics for all predictions.
    
    Includes counts by recommendation type, average sentiment, top/bottom sectors,
    and validation metrics for transparency.
    """
    predictions = prediction_service.get_cached_predictions()
    if not predictions:
        predictions = prediction_service.load_from_csv()
    
    if not predictions:
        return {
            "message": "No predictions available. Run the pipeline first.",
            "timestamp": datetime.now().isoformat()
        }
    
    summary = prediction_service.get_prediction_summary(predictions)
    
    # Add validation metrics for transparency
    total_predictions = len(predictions)
    predictions_with_news = len([p for p in predictions if p.get('news_count', 0) > 0])
    avg_news_per_stock = sum(p.get('news_count', 0) for p in predictions) / total_predictions if total_predictions > 0 else 0
    high_confidence = len([p for p in predictions if p.get('confidence', 0) >= 0.7])
    
    summary["validation_metrics"] = {
        "total_predictions": total_predictions,
        "predictions_with_news": predictions_with_news,
        "coverage_rate": f"{(predictions_with_news / total_predictions * 100):.1f}%" if total_predictions > 0 else "0%",
        "avg_news_per_stock": f"{avg_news_per_stock:.1f}",
        "high_confidence_predictions": high_confidence,
        "high_confidence_rate": f"{(high_confidence / total_predictions * 100):.1f}%" if total_predictions > 0 else "0%",
        "data_freshness": "Real-time",
        "methodology": "Sentiment Analysis + Price Momentum",
        "disclaimer": "Educational tool only - Not financial advice"
    }
    
    summary["timestamp"] = datetime.now().isoformat()
    
    return summary


@router.get("/top")
async def get_top_predictions(
    count: int = Query(10, ge=1, le=50, description="Number of top picks"),
    min_news_count: int = Query(1, ge=0, description="Minimum news articles"),
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Get top buy recommendations.
    
    Returns stocks with highest prediction scores and positive sentiment.
    """
    predictions = prediction_service.get_cached_predictions()
    if not predictions:
        predictions = prediction_service.load_from_csv()
    
    if not predictions:
        return {
            "top_picks": [],
            "message": "No predictions available.",
        }
    
    # Filter for min news and sort by score
    top = prediction_service.filter_predictions(
        predictions,
        min_news_count=min_news_count,
        sort_by="prediction_score",
        sort_desc=True,
        limit=count
    )
    
    return {
        "count": len(top),
        "top_picks": top,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/bottom")
async def get_bottom_predictions(
    count: int = Query(10, ge=1, le=50, description="Number of sell candidates"),
    min_news_count: int = Query(1, ge=0, description="Minimum news articles"),
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Get sell recommendations (lowest scores).
    
    Returns stocks with lowest prediction scores and negative sentiment.
    """
    predictions = prediction_service.get_cached_predictions()
    if not predictions:
        predictions = prediction_service.load_from_csv()
    
    if not predictions:
        return {
            "sell_candidates": [],
            "message": "No predictions available.",
        }
    
    # Filter for min news and sort ascending (worst first)
    bottom = prediction_service.filter_predictions(
        predictions,
        min_news_count=min_news_count,
        sort_by="prediction_score",
        sort_desc=False,
        limit=count
    )
    
    return {
        "count": len(bottom),
        "sell_candidates": bottom,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{ticker}")
async def get_prediction_by_ticker(
    ticker: str,
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Get prediction for a specific stock.
    
    Returns detailed prediction including sentiment analysis and recommendation.
    """
    predictions = prediction_service.get_cached_predictions()
    if not predictions:
        predictions = prediction_service.load_from_csv()
    
    # Find the ticker
    ticker_upper = ticker.upper()
    for pred in predictions:
        if pred.get('ticker', '').upper() == ticker_upper:
            return {
                "prediction": pred,
                "timestamp": datetime.now().isoformat()
            }
    
    raise HTTPException(status_code=404, detail=f"Prediction not found for ticker: {ticker}")
