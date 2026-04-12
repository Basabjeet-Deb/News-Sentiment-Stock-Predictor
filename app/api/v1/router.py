"""
API v1 Router - combines all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1 import predictions, news, stocks, pipeline, chat, training

router = APIRouter(prefix="/v1")

# Include all endpoint routers
router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
router.include_router(news.router, prefix="/news", tags=["News"])
router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
router.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(training.router, prefix="/training", tags=["Training"])
