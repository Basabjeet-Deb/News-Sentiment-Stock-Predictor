"""
News Sentiment Stock Predictor - FastAPI Application

Main entry point for the REST API server.
"""

import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to path for importing existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1.router import router as v1_router
from app.core.config import get_settings, STOCK_TICKERS
from app.middleware import RateLimitMiddleware, get_cors_config


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    settings = get_settings()
    print(f"[STARTUP] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[STARTUP] Tracking {len(STOCK_TICKERS)} stocks")
    print(f"[STARTUP] Data directory: {settings.DATA_DIR}")
    
    # Check if data files exist
    if os.path.exists(settings.PREDICTIONS_CSV):
        print(f"[STARTUP] Predictions data available")
    else:
        print(f"[STARTUP] No prediction data - run pipeline to generate")
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Application shutting down")


# Create FastAPI application
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Stock Prediction API powered by News Sentiment Analysis
    
    This API provides stock predictions based on news sentiment analysis for 180+ stocks.
    
    ### Features:
    - **Predictions**: Get buy/hold/sell recommendations with confidence scores
    - **News**: Access analyzed news articles with sentiment scores
    - **Stocks**: Get current stock prices and market summary
    - **Pipeline**: Run the prediction pipeline to refresh data
    
    ### Quick Start:
    1. Check `/api/v1/pipeline/status` to see data availability
    2. If no data, run `/api/v1/pipeline/run` to generate predictions
    3. Get predictions from `/api/v1/predictions/top`
    
    ### Data Sources:
    - Web scraping: Google News, Finviz, MarketWatch, Yahoo Finance
    - VADER sentiment analysis
    - Real-time stock prices via yfinance
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS middleware with environment-based configuration
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
    )


# Root API endpoint moved to /api/root as / now serves the frontend
@app.get("/api/root", tags=["Health"])
async def root():
    """
    API root - health check and basic info
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "stocks_tracked": len(STOCK_TICKERS),
        "docs_url": "/docs",
        "api_base": "/api/v1",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api", tags=["Health"])
async def api_info():
    """
    API information and available endpoints
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "predictions": {
                "list": "/api/v1/predictions/",
                "summary": "/api/v1/predictions/summary",
                "top": "/api/v1/predictions/top",
                "bottom": "/api/v1/predictions/bottom",
                "by_ticker": "/api/v1/predictions/{ticker}",
            },
            "news": {
                "list": "/api/v1/news/",
                "summary": "/api/v1/news/summary",
                "by_ticker": "/api/v1/news/by-ticker/{ticker}",
                "by_source": "/api/v1/news/by-source/{source}",
                "analyze": "/api/v1/news/analyze",
            },
            "stocks": {
                "list": "/api/v1/stocks/",
                "summary": "/api/v1/stocks/summary",
                "gainers": "/api/v1/stocks/gainers",
                "losers": "/api/v1/stocks/losers",
                "tracked": "/api/v1/stocks/tracked",
                "by_ticker": "/api/v1/stocks/{ticker}",
            },
            "pipeline": {
                "status": "/api/v1/pipeline/status",
                "run": "/api/v1/pipeline/run",
                "run_sync": "/api/v1/pipeline/run-sync",
                "quick_update": "/api/v1/pipeline/quick-update",
                "data": "/api/v1/pipeline/data",
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


# Include API routers
app.include_router(v1_router, prefix="/api")

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# CLI entry point
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print(f" {settings.APP_NAME}")
    print("=" * 60)
    print(f"\nStarting server at http://localhost:8000")
    print(f"API docs at http://localhost:8000/docs")
    print(f"Tracking {len(STOCK_TICKERS)} stocks\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
