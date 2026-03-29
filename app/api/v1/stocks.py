"""
Stocks API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.services.price_service import PriceService
from app.core.dependencies import get_price_service
from app.core.config import STOCK_TICKERS

router = APIRouter()


@router.get("/")
async def get_stock_prices(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_change_percent: Optional[float] = Query(None, description="Minimum change %"),
    max_change_percent: Optional[float] = Query(None, description="Maximum change %"),
    sort_by: str = Query("change_percent", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    price_service: PriceService = Depends(get_price_service)
):
    """
    Get current stock prices with optional filtering.
    
    Returns price data including change, volume, and company info.
    """
    # Load prices from cache or CSV
    prices = price_service.get_cached_prices()
    if not prices:
        prices = price_service.load_from_csv()
    
    if not prices:
        return {
            "total_count": 0,
            "prices": [],
            "message": "No price data available. Run the pipeline first.",
            "timestamp": datetime.now().isoformat()
        }
    
    # Filter
    filtered = price_service.filter_prices(
        prices,
        sector=sector,
        min_price=min_price,
        max_price=max_price,
        min_change_percent=min_change_percent,
        max_change_percent=max_change_percent,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        offset=offset
    )
    
    return {
        "total_count": len(filtered),
        "prices": filtered,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/summary")
async def get_market_summary(
    price_service: PriceService = Depends(get_price_service)
):
    """
    Get market summary statistics.
    
    Includes gainers/losers counts, top movers, and most active stocks.
    """
    prices = price_service.get_cached_prices()
    if not prices:
        prices = price_service.load_from_csv()
    
    if not prices:
        return {
            "message": "No price data available. Run the pipeline first.",
            "timestamp": datetime.now().isoformat()
        }
    
    summary = price_service.get_market_summary(prices)
    
    return summary


@router.get("/gainers")
async def get_top_gainers(
    count: int = Query(10, ge=1, le=50, description="Number of stocks"),
    price_service: PriceService = Depends(get_price_service)
):
    """
    Get top gaining stocks by percentage change.
    """
    prices = price_service.get_cached_prices()
    if not prices:
        prices = price_service.load_from_csv()
    
    gainers = price_service.filter_prices(
        prices,
        min_change_percent=0,
        sort_by="change_percent",
        sort_desc=True,
        limit=count
    )
    
    return {
        "count": len(gainers),
        "gainers": gainers,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/losers")
async def get_top_losers(
    count: int = Query(10, ge=1, le=50, description="Number of stocks"),
    price_service: PriceService = Depends(get_price_service)
):
    """
    Get top losing stocks by percentage change.
    """
    prices = price_service.get_cached_prices()
    if not prices:
        prices = price_service.load_from_csv()
    
    losers = price_service.filter_prices(
        prices,
        max_change_percent=0,
        sort_by="change_percent",
        sort_desc=False,
        limit=count
    )
    
    return {
        "count": len(losers),
        "losers": losers,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/tracked")
async def get_tracked_stocks():
    """
    Get list of all tracked stock tickers.
    """
    return {
        "count": len(STOCK_TICKERS),
        "tickers": STOCK_TICKERS,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{ticker}")
async def get_stock_price(
    ticker: str,
    price_service: PriceService = Depends(get_price_service)
):
    """
    Get price data for a specific stock.
    """
    prices = price_service.get_cached_prices()
    if not prices:
        prices = price_service.load_from_csv()
    
    ticker_upper = ticker.upper()
    
    if ticker_upper in prices and 'error' not in prices[ticker_upper]:
        return {
            "price": prices[ticker_upper],
            "timestamp": datetime.now().isoformat()
        }
    
    # Try to fetch fresh price
    price_data = price_service.get_price(ticker_upper)
    
    if price_data:
        return {
            "price": price_data,
            "timestamp": datetime.now().isoformat()
        }
    
    raise HTTPException(status_code=404, detail=f"Price not found for ticker: {ticker}")


@router.get("/{ticker}/history")
async def get_stock_history(
    ticker: str,
    period: str = Query("1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1d", description="Data interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo"),
    price_service: PriceService = Depends(get_price_service)
):
    """
    Get historical price data for a stock (OHLCV).
    
    Returns candlestick data for charting.
    """
    ticker_upper = ticker.upper()
    
    try:
        history = price_service.get_historical_data(ticker_upper, period=period, interval=interval)
        
        if history.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")
        
        # Convert to list of dicts for JSON
        data = []
        for index, row in history.iterrows():
            data.append({
                "date": index.isoformat(),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        return {
            "ticker": ticker_upper,
            "period": period,
            "interval": interval,
            "data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.post("/refresh")
async def refresh_prices(
    tickers: Optional[List[str]] = Query(None, description="Specific tickers to refresh"),
    price_service: PriceService = Depends(get_price_service)
):
    """
    Refresh stock prices (fetches from Yahoo Finance).
    
    Warning: This makes external API calls and may take time.
    """
    tickers_to_fetch = [t.upper() for t in tickers] if tickers else STOCK_TICKERS
    
    prices = price_service.fetch_prices(tickers_to_fetch)
    valid_count = sum(1 for v in prices.values() if 'error' not in v)
    
    return {
        "status": "complete",
        "requested": len(tickers_to_fetch),
        "fetched": valid_count,
        "timestamp": datetime.now().isoformat()
    }
