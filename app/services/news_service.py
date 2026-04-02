"""
News fetching service - wraps existing news fetching logic
"""

import sys
import os
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Add parent directory to import existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.news_spider import FinancialNewsSpider
from scrapy.crawler import CrawlerProcess
import json
import os
# FreeNewsFetcher removed - using Scrapy spider instead
# from scripts.free_news_fetcher import FreeNewsFetcher
from app.core.config import get_settings
import pandas as pd


class NewsService:
    """Service for fetching news from CSV data"""
    
    def __init__(self):
        self._cache: List[Dict] = []
        self._cache_timestamp: Optional[datetime] = None
        self.settings = get_settings()
        self.news_file = 'data/news_analyzed.csv'
    
    def fetch_comprehensive_news(self, max_articles: int = 1000) -> List[Dict]:
        """
        Fetch news from CSV file
        
        Args:
            max_articles: Maximum articles to fetch
            
        Returns:
            List of news article dictionaries
        """
        try:
            df = pd.read_csv(self.news_file)
            news = df.head(max_articles).to_dict('records')
            self._cache = news
            self._cache_timestamp = datetime.now()
            return news
        except Exception as e:
            print(f"Error loading news: {e}")
            return []
    
    def fetch_free_news(self, stocks: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch news from CSV file
        
        Args:
            stocks: List of stock tickers
            
        Returns:
            List of news article dictionaries
        """
        return self.fetch_comprehensive_news()
    
    def get_cached_news(self) -> List[Dict]:
        """Get cached news if available"""
        return self._cache
    
    def load_from_csv(self, filepath: str = None) -> List[Dict]:
        """
        Load analyzed news from CSV file
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of news article dictionaries
        """
        filepath = filepath or self.settings.NEWS_CSV
        
        if not os.path.exists(filepath):
            return []
        
        try:
            df = pd.read_csv(filepath)
            # Replace NaN and inf values for JSON compatibility
            df = df.replace([float('inf'), float('-inf')], None)
            df = df.fillna('')
            news = df.to_dict('records')
            self._cache = news
            return news
        except Exception as e:
            print(f"Error loading news CSV: {e}")
            return []
    
    def filter_news(
        self,
        news: List[Dict],
        ticker: Optional[str] = None,
        source: Optional[str] = None,
        min_sentiment: Optional[float] = None,
        max_sentiment: Optional[float] = None,
        impact_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Filter news articles based on criteria
        
        Args:
            news: List of news articles
            ticker: Filter by stock ticker
            source: Filter by news source
            min_sentiment: Minimum sentiment score
            max_sentiment: Maximum sentiment score
            impact_level: Filter by impact level
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Filtered list of articles
        """
        filtered = news
        
        if ticker:
            filtered = [n for n in filtered if n.get('ticker', '').upper() == ticker.upper()]
        
        if source:
            filtered = [n for n in filtered if source.lower() in n.get('source', '').lower()]
        
        if min_sentiment is not None:
            filtered = [n for n in filtered 
                       if n.get('sentiment_compound', n.get('sentiment', {}).get('compound', 0)) >= min_sentiment]
        
        if max_sentiment is not None:
            filtered = [n for n in filtered 
                       if n.get('sentiment_compound', n.get('sentiment', {}).get('compound', 0)) <= max_sentiment]
        
        if impact_level:
            filtered = [n for n in filtered 
                       if n.get('impact_level', n.get('relevance', {}).get('impact_level', '')) == impact_level]
        
        # Apply pagination
        return filtered[offset:offset + limit]
    
    def get_news_summary(self, news: List[Dict]) -> Dict:
        """
        Get summary statistics for news articles
        
        Args:
            news: List of news articles
            
        Returns:
            Dictionary with summary statistics
        """
        if not news:
            return {
                "total_count": 0,
                "sources": {},
                "tickers": {},
                "avg_sentiment": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            }
        
        # Count by source
        sources = {}
        for n in news:
            source = n.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        # Count by ticker
        tickers = {}
        for n in news:
            ticker = n.get('ticker', '')
            if ticker:
                tickers[ticker] = tickers.get(ticker, 0) + 1
        
        # Sentiment stats
        sentiments = []
        for n in news:
            sent = n.get('sentiment_compound', n.get('sentiment', {}).get('compound', 0))
            if isinstance(sent, (int, float)) and not (sent != sent):  # Check for NaN
                sentiments.append(sent)
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        positive = sum(1 for s in sentiments if s > 0.05)
        negative = sum(1 for s in sentiments if s < -0.05)
        neutral = len(sentiments) - positive - negative
        
        return {
            "total_count": len(news),
            "sources": sources,
            "tickers": dict(sorted(tickers.items(), key=lambda x: x[1], reverse=True)[:20]),
            "avg_sentiment": round(float(avg_sentiment), 3) if avg_sentiment == avg_sentiment else 0,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
        }
