"""
News article models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class SentimentLabel(str, Enum):
    VERY_POSITIVE = "Very Positive"
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"
    VERY_NEGATIVE = "Very Negative"


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    MACRO = "macro"
    LOW = "low"


class SentimentScore(BaseModel):
    """Sentiment analysis scores"""
    compound: float = Field(..., ge=-1, le=1, description="Compound sentiment score (-1 to 1)")
    positive: float = Field(..., ge=0, le=1, description="Positive sentiment ratio")
    negative: float = Field(..., ge=0, le=1, description="Negative sentiment ratio")
    neutral: float = Field(..., ge=0, le=1, description="Neutral sentiment ratio")
    label: SentimentLabel = Field(..., description="Sentiment label")


class RelevanceInfo(BaseModel):
    """Relevance and impact information"""
    score: float = Field(..., ge=0, le=1, description="Relevance score (0 to 1)")
    is_relevant: bool = Field(..., description="Whether article is relevant")
    impact_level: ImpactLevel = Field(..., description="Impact level")
    is_impactful: bool = Field(..., description="Whether article is impactful")


class NewsArticle(BaseModel):
    """Single news article with sentiment"""
    title: str = Field(..., description="Article headline")
    source: str = Field(..., description="News source")
    ticker: Optional[str] = Field(None, description="Associated stock ticker")
    url: Optional[str] = Field(None, description="Article URL")
    description: Optional[str] = Field(None, description="Article summary")
    published_at: Optional[str] = Field(None, description="Publication timestamp")
    sentiment: Optional[SentimentScore] = Field(None, description="Sentiment analysis")
    relevance: Optional[RelevanceInfo] = Field(None, description="Relevance info")
    topics: List[str] = Field(default_factory=list, description="Related topics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Apple Reports Record Earnings",
                "source": "Yahoo Finance",
                "ticker": "AAPL",
                "url": "https://finance.yahoo.com/news/apple-earnings",
                "description": "Apple Inc exceeded earnings expectations with strong iPhone sales",
                "published_at": "2026-03-29T10:00:00Z",
                "sentiment": {
                    "compound": 0.65,
                    "positive": 0.35,
                    "negative": 0.05,
                    "neutral": 0.60,
                    "label": "Positive"
                },
                "relevance": {
                    "score": 0.85,
                    "is_relevant": True,
                    "impact_level": "high",
                    "is_impactful": True
                }
            }
        }


class NewsResponse(BaseModel):
    """Response containing list of news articles"""
    total_count: int = Field(..., description="Total number of articles")
    articles: List[NewsArticle] = Field(..., description="List of news articles")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    sources: Dict[str, int] = Field(default_factory=dict, description="Article count by source")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 347,
                "articles": [],
                "timestamp": "2026-03-29T08:00:00Z",
                "sources": {
                    "Google News": 95,
                    "Finviz": 240,
                    "MarketWatch": 40
                }
            }
        }


class NewsFilterParams(BaseModel):
    """Parameters for filtering news articles"""
    ticker: Optional[str] = Field(None, description="Filter by ticker symbol")
    source: Optional[str] = Field(None, description="Filter by news source")
    min_sentiment: Optional[float] = Field(None, ge=-1, le=1, description="Minimum sentiment score")
    max_sentiment: Optional[float] = Field(None, ge=-1, le=1, description="Maximum sentiment score")
    impact_level: Optional[ImpactLevel] = Field(None, description="Filter by impact level")
    limit: int = Field(50, ge=1, le=500, description="Maximum articles to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
