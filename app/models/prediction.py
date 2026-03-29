"""
Stock prediction models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RecommendationType(str, Enum):
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"


class Prediction(BaseModel):
    """Stock prediction with recommendation"""
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Company name")
    current_price: float = Field(..., ge=0, description="Current stock price")
    price_change_percent: float = Field(..., description="Price change percentage")
    sector: str = Field(..., description="Company sector")
    
    # Sentiment data
    news_count: int = Field(..., ge=0, description="Number of news articles analyzed")
    avg_sentiment: float = Field(..., ge=-1, le=1, description="Average sentiment score")
    positive_news: int = Field(..., ge=0, description="Count of positive news")
    negative_news: int = Field(..., ge=0, description="Count of negative news")
    sentiment_recommendation: str = Field(..., description="Sentiment-based recommendation")
    
    # Prediction
    prediction_score: float = Field(..., ge=-1, le=1, description="Overall prediction score")
    recommendation: RecommendationType = Field(..., description="Final recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Prediction timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "current_price": 248.80,
                "price_change_percent": -1.25,
                "sector": "Technology",
                "news_count": 8,
                "avg_sentiment": 0.45,
                "positive_news": 6,
                "negative_news": 1,
                "sentiment_recommendation": "BUY",
                "prediction_score": 0.456,
                "recommendation": "BUY",
                "confidence": 0.72,
                "timestamp": "2026-03-29T08:00:00Z"
            }
        }


class PredictionResponse(BaseModel):
    """Response containing stock predictions"""
    total_count: int = Field(..., description="Total predictions generated")
    predictions: List[Prediction] = Field(..., description="List of predictions")
    top_buys: List[Prediction] = Field(default_factory=list, description="Top buy recommendations")
    top_sells: List[Prediction] = Field(default_factory=list, description="Top sell recommendations")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 166,
                "predictions": [],
                "top_buys": [],
                "top_sells": [],
                "timestamp": "2026-03-29T08:00:00Z"
            }
        }


class PredictionFilterParams(BaseModel):
    """Parameters for filtering predictions"""
    ticker: Optional[str] = Field(None, description="Filter by ticker symbol")
    sector: Optional[str] = Field(None, description="Filter by sector")
    recommendation: Optional[RecommendationType] = Field(None, description="Filter by recommendation")
    min_score: Optional[float] = Field(None, ge=-1, le=1, description="Minimum prediction score")
    max_score: Optional[float] = Field(None, ge=-1, le=1, description="Maximum prediction score")
    min_confidence: Optional[float] = Field(None, ge=0, le=1, description="Minimum confidence")
    min_news_count: Optional[int] = Field(None, ge=0, description="Minimum news articles")
    limit: int = Field(50, ge=1, le=500, description="Maximum predictions to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: str = Field("prediction_score", description="Sort field")
    sort_desc: bool = Field(True, description="Sort descending")


class PredictionSummary(BaseModel):
    """Summary statistics for predictions"""
    total_stocks: int = Field(..., description="Total stocks analyzed")
    strong_buy_count: int = Field(..., ge=0, description="Strong buy recommendations")
    buy_count: int = Field(..., ge=0, description="Buy recommendations")
    hold_count: int = Field(..., ge=0, description="Hold recommendations")
    sell_count: int = Field(..., ge=0, description="Sell recommendations")
    strong_sell_count: int = Field(..., ge=0, description="Strong sell recommendations")
    avg_sentiment: float = Field(..., description="Average sentiment across all stocks")
    avg_confidence: float = Field(..., ge=0, le=1, description="Average confidence")
    top_sectors: List[dict] = Field(default_factory=list, description="Top performing sectors")
    bottom_sectors: List[dict] = Field(default_factory=list, description="Bottom performing sectors")
