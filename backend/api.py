"""
Scalable FastAPI Backend for Stock Predictor
RESTful API with caching and async support
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TARGET_STOCKS, STOCK_NAMES

app = FastAPI(
    title="Stock Predictor API",
    description="AI-powered stock prediction using news sentiment analysis",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache
cache = {
    'predictions': None,
    'last_updated': None,
    'stocks': None,
    'news': None,
    'sentiment': None
}


# Models
class StockInfo(BaseModel):
    ticker: str
    company: str
    current_price: float
    change_24h: Optional[float] = None


class Prediction(BaseModel):
    ticker: str
    company: str
    current_price: float
    predicted_price: float
    predicted_change_pct: float
    sentiment: str
    sentiment_score: float
    news_count: int
    confidence: float
    recommendation: str
    trend: str


class NewsArticle(BaseModel):
    title: str
    source: str
    ticker: str
    company: str
    sentiment_score: Optional[float] = None
    scraped_date: str


class SystemStats(BaseModel):
    total_stocks: int
    total_predictions: int
    total_news: int
    last_updated: Optional[str]
    buy_signals: int
    sell_signals: int
    hold_signals: int


# Helper functions
def load_data():
    """Load all data files"""
    try:
        if os.path.exists('data/predictions.csv'):
            cache['predictions'] = pd.read_csv('data/predictions.csv')
        
        if os.path.exists('data/prototype_stocks.csv'):
            cache['stocks'] = pd.read_csv('data/prototype_stocks.csv')
        
        if os.path.exists('data/prototype_news.csv'):
            cache['news'] = pd.read_csv('data/prototype_news.csv')
        
        if os.path.exists('data/sentiment_analysis.csv'):
            cache['sentiment'] = pd.read_csv('data/sentiment_analysis.csv')
        
        cache['last_updated'] = datetime.now().isoformat()
        
        return True
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return False


def get_stock_change(ticker):
    """Calculate 24h price change"""
    if cache['stocks'] is None:
        return None
    
    ticker_data = cache['stocks'][cache['stocks']['Ticker'] == ticker]
    
    if len(ticker_data) < 2:
        return None
    
    latest = ticker_data.iloc[-1]['Close']
    previous = ticker_data.iloc[-2]['Close']
    
    change = ((latest - previous) / previous) * 100
    return round(change, 2)


# Startup
@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    print("Loading data...")
    load_data()
    print("API ready!")


# Endpoints
@app.get("/")
def root():
    """API info"""
    return {
        "name": "Stock Predictor API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "stocks": "/api/stocks",
            "predictions": "/api/predictions",
            "prediction": "/api/prediction/{ticker}",
            "news": "/api/news",
            "stats": "/api/stats",
            "refresh": "/api/refresh"
        }
    }


@app.get("/api/stocks", response_model=List[StockInfo])
def get_stocks():
    """Get all available stocks"""
    stocks = []
    
    for ticker in TARGET_STOCKS:
        change = get_stock_change(ticker)
        
        # Get current price
        if cache['stocks'] is not None:
            ticker_data = cache['stocks'][cache['stocks']['Ticker'] == ticker]
            if len(ticker_data) > 0:
                current_price = float(ticker_data.iloc[-1]['Close'])
            else:
                current_price = 0.0
        else:
            current_price = 0.0
        
        stocks.append(StockInfo(
            ticker=ticker,
            company=STOCK_NAMES[ticker],
            current_price=current_price,
            change_24h=change
        ))
    
    return stocks


@app.get("/api/predictions", response_model=List[Prediction])
def get_predictions():
    """Get all stock predictions"""
    if cache['predictions'] is None:
        raise HTTPException(status_code=404, detail="No predictions available. Run analysis first.")
    
    predictions = []
    
    for _, row in cache['predictions'].iterrows():
        predictions.append(Prediction(
            ticker=row['ticker'],
            company=row['company'],
            current_price=float(row['current_price']),
            predicted_price=float(row.get('predicted_price', row['current_price'])),
            predicted_change_pct=float(row['predicted_change_pct']),
            sentiment=row['sentiment'],
            sentiment_score=float(row['sentiment_score']),
            news_count=int(row['news_count']),
            confidence=float(row['confidence']),
            recommendation=row['recommendation'],
            trend=row.get('trend', 'Unknown')
        ))
    
    return predictions


@app.get("/api/prediction/{ticker}", response_model=Prediction)
def get_prediction(ticker: str):
    """Get prediction for specific stock"""
    ticker = ticker.upper()
    
    if cache['predictions'] is None:
        raise HTTPException(status_code=404, detail="No predictions available")
    
    pred = cache['predictions'][cache['predictions']['ticker'] == ticker]
    
    if len(pred) == 0:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    row = pred.iloc[0]
    
    return Prediction(
        ticker=row['ticker'],
        company=row['company'],
        current_price=float(row['current_price']),
        predicted_price=float(row.get('predicted_price', row['current_price'])),
        predicted_change_pct=float(row['predicted_change_pct']),
        sentiment=row['sentiment'],
        sentiment_score=float(row['sentiment_score']),
        news_count=int(row['news_count']),
        confidence=float(row['confidence']),
        recommendation=row['recommendation'],
        trend=row.get('trend', 'Unknown')
    )


@app.get("/api/news", response_model=List[NewsArticle])
def get_news(ticker: Optional[str] = None, limit: int = 50):
    """Get news articles"""
    if cache['news'] is None:
        raise HTTPException(status_code=404, detail="No news available")
    
    news_df = cache['news']
    
    if ticker:
        ticker = ticker.upper()
        news_df = news_df[news_df['ticker'] == ticker]
    
    news_df = news_df.head(limit)
    
    articles = []
    
    for _, row in news_df.iterrows():
        # Get sentiment if available
        sentiment_score = None
        if cache['sentiment'] is not None:
            sent = cache['sentiment'][cache['sentiment']['title'] == row['title']]
            if len(sent) > 0:
                sentiment_score = float(sent.iloc[0]['compound'])
        
        articles.append(NewsArticle(
            title=row['title'],
            source=row['source'],
            ticker=row['ticker'],
            company=row['company'],
            sentiment_score=sentiment_score,
            scraped_date=row['scraped_date']
        ))
    
    return articles


@app.get("/api/stats", response_model=SystemStats)
def get_stats():
    """Get system statistics"""
    
    total_stocks = len(TARGET_STOCKS)
    total_predictions = len(cache['predictions']) if cache['predictions'] is not None else 0
    total_news = len(cache['news']) if cache['news'] is not None else 0
    
    buy_signals = 0
    sell_signals = 0
    hold_signals = 0
    
    if cache['predictions'] is not None:
        buy_signals = len(cache['predictions'][cache['predictions']['recommendation'] == 'BUY'])
        sell_signals = len(cache['predictions'][cache['predictions']['recommendation'] == 'SELL'])
        hold_signals = len(cache['predictions'][cache['predictions']['recommendation'] == 'HOLD'])
    
    return SystemStats(
        total_stocks=total_stocks,
        total_predictions=total_predictions,
        total_news=total_news,
        last_updated=cache['last_updated'],
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        hold_signals=hold_signals
    )


@app.post("/api/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """Refresh data in background"""
    
    def refresh():
        load_data()
    
    background_tasks.add_task(refresh)
    
    return {
        "status": "refreshing",
        "message": "Data refresh started in background"
    }


@app.get("/api/chart/{ticker}")
def get_chart_data(ticker: str, days: int = 30):
    """Get historical price data for charts"""
    ticker = ticker.upper()
    
    if cache['stocks'] is None:
        raise HTTPException(status_code=404, detail="No stock data available")
    
    ticker_data = cache['stocks'][cache['stocks']['Ticker'] == ticker]
    
    if len(ticker_data) == 0:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    # Get last N days
    ticker_data = ticker_data.tail(days)
    
    chart_data = {
        "ticker": ticker,
        "dates": ticker_data['Date'].tolist(),
        "prices": ticker_data['Close'].tolist(),
        "volumes": ticker_data['Volume'].tolist()
    }
    
    return chart_data


if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("STOCK PREDICTOR API")
    print("="*60)
    print("Starting API server on http://0.0.0.0:8000")
    print("Docs: http://localhost:8000/docs")
    print("="*60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
