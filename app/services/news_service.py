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
    
    # Scrapy's reactor cannot be restarted within the same process.
    _scrapy_ran_in_process: bool = False

    # Module-level cache shared across all instances (survives request lifecycle)
    _global_cache: List[Dict] = []
    _global_cache_df: "pd.DataFrame | None" = None
    _global_cache_timestamp: Optional[datetime] = None
    
    def __init__(self):
        self._cache: List[Dict] = []
        self._cache_timestamp: Optional[datetime] = None
        self.settings = get_settings()
        self.news_file = os.path.join(self.settings.DATA_DIR, "news_analyzed.csv")
        self.scraped_news_file = os.path.join(self.settings.DATA_DIR, "scraped_news.json")
        # Full historical news store — used for the news API
        self.news_events_file = os.path.join(self.settings.DATA_DIR, "news_events.csv")
    
    def fetch_comprehensive_news(self, max_articles: int = 1000) -> List[Dict]:
        """
        Fetch news for the pipeline.
        
        Preference order:
        1) Freshly scraped output (cached on disk)
        2) Existing analyzed CSV (fallback)
        
        Args:
            max_articles: Maximum articles to fetch
            
        Returns:
            List of news article dictionaries
        """
        os.makedirs(self.settings.DATA_DIR, exist_ok=True)
        
        scraped = self._load_scraped_news(limit=max_articles)
        if scraped:
            self._cache = scraped
            self._cache_timestamp = datetime.now()
            return scraped
        
        # Fallback: use existing analyzed CSV if available
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
    
    def _load_scraped_news(self, limit: int) -> List[Dict]:
        """
        Load scraped news from disk; if missing/stale, attempt to run the spider once.
        """
        # If we already have a file, use it.
        if os.path.exists(self.scraped_news_file):
            try:
                with open(self.scraped_news_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    return data[:limit]
            except Exception:
                # If file is corrupted, fall through to scraping attempt
                pass
        
        # Attempt to scrape only once per process to avoid reactor restart errors.
        if not NewsService._scrapy_ran_in_process:
            try:
                NewsService._scrapy_ran_in_process = True
                self._run_scrapy_spider(output_file=self.scraped_news_file)
                with open(self.scraped_news_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    return data[:limit]
            except Exception as e:
                print(f"Error running Scrapy spider: {e}")
        
        return []
    
    def _run_scrapy_spider(self, output_file: str) -> None:
        """
        Run the Scrapy spider and write results to output_file.
        This is a blocking call.
        """
        # Ensure the output file is not appended to
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception:
                pass
        
        process = CrawlerProcess({
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "FEEDS": {output_file: {"format": "json", "overwrite": True}},
            "LOG_LEVEL": "ERROR",
            "ROBOTSTXT_OBEY": True,
        })
        
        # Let the spider choose its default tickers list.
        process.crawl(FinancialNewsSpider)
        process.start()
    
    def get_cached_news(self) -> List[Dict]:
        """Returns sentinel if DataFrame cache is warm, empty list if cold."""
        ts = NewsService._global_cache_timestamp
        if NewsService._global_cache_df is None or ts is None:
            return []
        age_min = (datetime.now() - ts).total_seconds() / 60
        if age_min > 30:
            return []
        return ["__loaded__"]  # non-empty sentinel — actual data served via filter_news
    
    def load_from_csv(self, filepath: str = None) -> List[Dict]:
        """
        Load news from the full historical store (news_events.csv).
        Falls back to news_analyzed.csv if events file not available.
        Uses chunked reading to avoid loading 242k rows into memory at once.
        Returns the most recent 5000 articles sorted newest-first.
        """
        # Prefer the full historical store
        events_path = self.news_events_file
        if not os.path.exists(events_path):
            events_path = filepath or self.settings.NEWS_CSV

        if not os.path.exists(events_path):
            return []

        try:
            # Read in chunks, keep only needed columns to save RAM
            cols_wanted = [
                "title", "source", "ticker", "published_at", "scraped_at",
                "sentiment_compound", "sentiment_label",
                "impact_level", "relevance_score", "url",
            ]
            chunks = []
            for chunk in pd.read_csv(events_path, usecols=lambda c: c in cols_wanted,
                                     chunksize=10000, on_bad_lines="skip"):
                chunks.append(chunk)

            df = pd.concat(chunks, ignore_index=True)

            # Sort newest-first using scraped_at
            if "scraped_at" in df.columns:
                df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
                df = df.sort_values("scraped_at", ascending=False)

            # Normalise column names to match what the rest of the app expects
            if "sentiment_compound" not in df.columns:
                df["sentiment_compound"] = 0.0
            if "impact_level" not in df.columns:
                df["impact_level"] = "low"

            df = df.replace([float("inf"), float("-inf")], None).fillna("")
            # Pre-parse scraped_at once so date filtering is instant on every request
            if "scraped_at" in df.columns:
                df["_scraped_at_dt"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
            # Store DataFrame in global cache — avoid converting 257k rows to dicts
            NewsService._global_cache_df = df
            NewsService._global_cache_timestamp = datetime.now()
            # Return sentinel so get_cached_news returns non-empty
            NewsService._global_cache = []
            self._cache = []
            return ["__loaded__"]
        except Exception as e:
            print(f"Error loading news events: {e}")
            # Hard fallback to today's analyzed CSV
            try:
                df = pd.read_csv(self.settings.NEWS_CSV)
                df = df.replace([float("inf"), float("-inf")], None).fillna("")
                NewsService._global_cache_df = df
                NewsService._global_cache_timestamp = datetime.now()
                NewsService._global_cache = []
                self._cache = []
                return ["__loaded__"]
            except Exception:
                return []
    
    def filter_news(
        self,
        news: List[Dict],
        ticker: Optional[str] = None,
        source: Optional[str] = None,
        min_sentiment: Optional[float] = None,
        max_sentiment: Optional[float] = None,
        impact_level: Optional[str] = None,
        days: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Filter news using pandas for speed on large datasets."""
        df = NewsService._global_cache_df
        if df is None or df.empty:
            return []

        mask = pd.Series([True] * len(df), index=df.index)

        if ticker:
            t = ticker.upper()
            if "ticker" in df.columns:
                mask &= df["ticker"].astype(str).str.upper() == t

        if source:
            if "source" in df.columns:
                mask &= df["source"].astype(str).str.lower().str.contains(source.lower(), na=False)

        if min_sentiment is not None and "sentiment_compound" in df.columns:
            mask &= pd.to_numeric(df["sentiment_compound"], errors="coerce").fillna(0) >= min_sentiment

        if max_sentiment is not None and "sentiment_compound" in df.columns:
            mask &= pd.to_numeric(df["sentiment_compound"], errors="coerce").fillna(0) <= max_sentiment

        if impact_level and "impact_level" in df.columns:
            mask &= df["impact_level"].astype(str) == impact_level

        if days is not None:
            from datetime import timezone, timedelta
            cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
            # Use pre-parsed column if available
            ts_col = "_scraped_at_dt" if "_scraped_at_dt" in df.columns else "scraped_at"
            if ts_col == "scraped_at":
                ts = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
            else:
                ts = df["_scraped_at_dt"]
            mask &= ts >= cutoff

        filtered_df = df[mask].iloc[offset: offset + limit]
        return filtered_df.fillna("").to_dict("records")
    
    def get_news_summary(self, news: List[Dict]) -> Dict:
        """Get summary statistics using pandas for speed."""
        df = NewsService._global_cache_df
        if df is None or df.empty:
            df = pd.DataFrame(news) if news else pd.DataFrame()
        if df.empty:
            return {"total_count": 0, "sources": {}, "tickers": {},
                    "avg_sentiment": 0, "positive_count": 0, "negative_count": 0, "neutral_count": 0}

        total = len(df)
        sources = df["source"].astype(str).value_counts().head(20).to_dict() if "source" in df.columns else {}
        tickers = df["ticker"].astype(str).value_counts().head(20).to_dict() if "ticker" in df.columns else {}

        sent = pd.to_numeric(df.get("sentiment_compound", pd.Series(dtype=float)), errors="coerce").fillna(0)
        avg_s  = float(sent.mean())
        pos    = int((sent > 0.05).sum())
        neg    = int((sent < -0.05).sum())
        neu    = total - pos - neg

        high_impact = 0
        if "impact_level" in df.columns:
            high_impact = int((df["impact_level"].astype(str) == "high").sum())

        return {
            "total_count": total,
            "sources": sources,
            "tickers": tickers,
            "avg_sentiment": round(avg_s, 3),
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "high_impact_count": high_impact,
        }
