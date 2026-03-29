"""
Stock price models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class StockPrice(BaseModel):
    """Current stock price data"""
    ticker: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., ge=0, description="Current price")
    previous_close: float = Field(..., ge=0, description="Previous closing price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Price change percentage")
    volume: int = Field(..., ge=0, description="Trading volume")
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="P/E ratio")
    week_52_high: Optional[float] = Field(None, ge=0, description="52-week high")
    week_52_low: Optional[float] = Field(None, ge=0, description="52-week low")
    company_name: str = Field(..., description="Company name")
    sector: str = Field("Unknown", description="Company sector")
    industry: str = Field("Unknown", description="Company industry")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "price": 248.80,
                "previous_close": 251.95,
                "change": -3.15,
                "change_percent": -1.25,
                "volume": 45678900,
                "market_cap": 3850000000000,
                "pe_ratio": 32.5,
                "week_52_high": 260.10,
                "week_52_low": 164.08,
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            }
        }


class StockPriceResponse(BaseModel):
    """Response containing stock prices"""
    total_count: int = Field(..., description="Total stocks fetched")
    prices: List[StockPrice] = Field(..., description="List of stock prices")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 173,
                "prices": [],
                "timestamp": "2026-03-29T08:00:00Z"
            }
        }


class MarketSummary(BaseModel):
    """Market summary statistics"""
    total_stocks: int = Field(..., description="Total stocks tracked")
    gainers_count: int = Field(..., ge=0, description="Number of gainers")
    losers_count: int = Field(..., ge=0, description="Number of losers")
    unchanged_count: int = Field(..., ge=0, description="Number unchanged")
    top_gainers: List[StockPrice] = Field(default_factory=list, description="Top gaining stocks")
    top_losers: List[StockPrice] = Field(default_factory=list, description="Top losing stocks")
    most_active: List[StockPrice] = Field(default_factory=list, description="Most active by volume")
    sector_performance: Dict[str, float] = Field(default_factory=dict, description="Average change by sector")
    timestamp: datetime = Field(default_factory=datetime.now, description="Summary timestamp")


class StockFilterParams(BaseModel):
    """Parameters for filtering stock prices"""
    tickers: Optional[List[str]] = Field(None, description="List of tickers to fetch")
    sector: Optional[str] = Field(None, description="Filter by sector")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_change_percent: Optional[float] = Field(None, description="Minimum change %")
    max_change_percent: Optional[float] = Field(None, description="Maximum change %")
    limit: int = Field(50, ge=1, le=500, description="Maximum stocks to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: str = Field("change_percent", description="Sort field")
    sort_desc: bool = Field(True, description="Sort descending")
