"""
Dependency injection for FastAPI
"""

from functools import lru_cache
from app.core.config import Settings, get_settings
from app.services.news_service import NewsService
from app.services.sentiment_service import SentimentService
from app.services.price_service import PriceService
from app.services.prediction_service import PredictionService
from app.services.pipeline_service import PipelineService


@lru_cache()
def get_news_service() -> NewsService:
    """Get cached news service instance"""
    return NewsService()


@lru_cache()
def get_sentiment_service() -> SentimentService:
    """Get cached sentiment service instance"""
    return SentimentService()


@lru_cache()
def get_price_service() -> PriceService:
    """Get cached price service instance"""
    return PriceService()


@lru_cache()
def get_prediction_service() -> PredictionService:
    """Get cached prediction service instance"""
    return PredictionService()


def get_pipeline_service() -> PipelineService:
    """Get pipeline service (not cached - stateful)"""
    return PipelineService()
