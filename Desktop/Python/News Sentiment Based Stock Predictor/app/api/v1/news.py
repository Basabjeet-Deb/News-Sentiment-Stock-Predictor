"""
News API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.services.news_service import NewsService
from app.services.sentiment_service import SentimentService
from app.core.dependencies import get_news_service, get_sentiment_service

router = APIRouter()


@router.get("/")
async def get_news(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    source: Optional[str] = Query(None, description="Filter by news source"),
    min_sentiment: Optional[float] = Query(None, ge=-1, le=1, description="Minimum sentiment score"),
    max_sentiment: Optional[float] = Query(None, ge=-1, le=1, description="Maximum sentiment score"),
    impact_level: Optional[str] = Query(None, description="Filter by impact level (high, medium, macro, low)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum articles"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    Get analyzed news articles with optional filtering.
    
    Returns news articles with sentiment scores and relevance information.
    """
    # Load news from cache or CSV
    news = news_service.get_cached_news()
    if not news:
        news = news_service.load_from_csv()
    
    if not news:
        return {
            "total_count": 0,
            "articles": [],
            "message": "No news available. Run the pipeline first.",
            "timestamp": datetime.now().isoformat()
        }
    
    # Filter
    filtered = news_service.filter_news(
        news,
        ticker=ticker,
        source=source,
        min_sentiment=min_sentiment,
        max_sentiment=max_sentiment,
        impact_level=impact_level,
        limit=limit,
        offset=offset
    )
    
    return {
        "total_count": len(filtered),
        "articles": filtered,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/summary")
async def get_news_summary(
    news_service: NewsService = Depends(get_news_service)
):
    """
    Get summary statistics for news articles.
    
    Includes counts by source, ticker mentions, and sentiment distribution.
    """
    news = news_service.get_cached_news()
    if not news:
        news = news_service.load_from_csv()
    
    if not news:
        return {
            "message": "No news available. Run the pipeline first.",
            "timestamp": datetime.now().isoformat()
        }
    
    summary = news_service.get_news_summary(news)
    summary["timestamp"] = datetime.now().isoformat()
    
    return summary


@router.get("/sentiment-distribution")
async def get_sentiment_distribution(
    sentiment_service: SentimentService = Depends(get_sentiment_service),
    news_service: NewsService = Depends(get_news_service)
):
    """
    Get distribution of sentiment across all news articles.
    """
    news = news_service.get_cached_news()
    if not news:
        news = news_service.load_from_csv()
    
    if not news:
        return {
            "message": "No news available.",
            "timestamp": datetime.now().isoformat()
        }
    
    distribution = sentiment_service.get_sentiment_distribution(news)
    distribution["timestamp"] = datetime.now().isoformat()
    
    return distribution


@router.get("/by-ticker/{ticker}")
async def get_news_by_ticker(
    ticker: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum articles"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    Get news articles for a specific stock ticker.
    """
    news = news_service.get_cached_news()
    if not news:
        news = news_service.load_from_csv()
    
    filtered = news_service.filter_news(
        news,
        ticker=ticker.upper(),
        limit=limit
    )
    
    if not filtered:
        return {
            "ticker": ticker.upper(),
            "count": 0,
            "articles": [],
            "message": f"No news found for {ticker.upper()}",
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "ticker": ticker.upper(),
        "count": len(filtered),
        "articles": filtered,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/by-source/{source}")
async def get_news_by_source(
    source: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum articles"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    Get news articles from a specific source.
    """
    news = news_service.get_cached_news()
    if not news:
        news = news_service.load_from_csv()
    
    filtered = news_service.filter_news(
        news,
        source=source,
        limit=limit
    )
    
    return {
        "source": source,
        "count": len(filtered),
        "articles": filtered,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/analyze")
async def analyze_text(
    text: str = Query(..., min_length=10, description="Text to analyze"),
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """
    Analyze sentiment of arbitrary text.
    
    Useful for testing sentiment analysis on custom text.
    """
    result = sentiment_service.analyze_text(text)
    
    return {
        "text": text[:200] + "..." if len(text) > 200 else text,
        "sentiment": result,
        "timestamp": datetime.now().isoformat()
    }
