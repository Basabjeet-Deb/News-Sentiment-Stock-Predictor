"""
Incremental Updater - Update only new/changed data instead of full refresh
"""
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.news_spider import FinancialNewsSpider
from pipeline.sentiment_analyzer import SentimentAnalyzer
from pipeline.price_fetcher import StockPriceFetcher
from pipeline.historical_data_manager import HistoricalDataManager
import config


class IncrementalUpdater:
    """Updates only new data since last run and adds to historical batches"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(current_dir), "data")
        else:
            self.data_dir = data_dir
        
        self.state_file = os.path.join(self.data_dir, ".last_update.json")
        self.sentiment_analyzer = SentimentAnalyzer()
        self.price_fetcher = StockPriceFetcher()
        self.historical_manager = HistoricalDataManager()
    
    def _load_state(self) -> Dict:
        """Load last update state"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'last_news_update': None,
            'last_price_update': None,
            'last_prediction_update': None
        }
    
    def _save_state(self, state: Dict):
        """Save update state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def should_update_news(self, max_age_hours: int = 1) -> bool:
        """Check if news should be updated"""
        state = self._load_state()
        last_update = state.get('last_news_update')
        
        if not last_update:
            return True
        
        last_time = datetime.fromisoformat(last_update)
        age = datetime.now() - last_time
        
        return age > timedelta(hours=max_age_hours)
    
    def should_update_prices(self, max_age_minutes: int = 5) -> bool:
        """Check if prices should be updated"""
        state = self._load_state()
        last_update = state.get('last_price_update')
        
        if not last_update:
            return True
        
        last_time = datetime.fromisoformat(last_update)
        age = datetime.now() - last_time
        
        return age > timedelta(minutes=max_age_minutes)
    
    def update_news_incremental(self, max_articles: int = 500) -> int:
        """
        Fetch and analyze only new news articles
        
        Returns:
            Number of new articles added
        """
        print("\n[*] Checking for new news articles...")
        
        # Load existing news
        news_file = os.path.join(self.data_dir, "news_analyzed.csv")
        existing_news = []
        existing_titles = set()
        
        if os.path.exists(news_file):
            df = pd.read_csv(news_file)
            existing_news = df.to_dict('records')
            existing_titles = set(df['title'].tolist())
            print(f"[*] Found {len(existing_news)} existing articles")
        
        # Fetch new articles (limited to max_articles)
        print(f"[*] Fetching up to {max_articles} recent articles...")
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        
        # Run spider to get new articles
        output_file = os.path.join(self.data_dir, "scraped_news.json")
        
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/5.0',
            'FEEDS': {output_file: {'format': 'json', 'overwrite': True}},
            'LOG_LEVEL': 'ERROR'
        })
        
        process.crawl(FinancialNewsSpider, tickers=config.STOCK_TICKERS[:100])  # Top 100 stocks
        process.start()
        
        # Load scraped articles
        if not os.path.exists(output_file):
            print("[!] No new articles found")
            return 0
        
        with open(output_file, 'r') as f:
            new_articles = json.load(f)
        
        # Filter out duplicates
        truly_new = [a for a in new_articles if a.get('title') not in existing_titles]
        
        if not truly_new:
            print("[!] No new unique articles found")
            return 0
        
        print(f"[*] Found {len(truly_new)} new unique articles")
        
        # Analyze sentiment for new articles
        print("[*] Analyzing sentiment for new articles...")
        analyzed_new = self.sentiment_analyzer.analyze_batch(truly_new)
        
        # Combine with existing
        all_articles = existing_news + analyzed_new
        
        # Save updated news
        df_all = pd.DataFrame(all_articles)
        df_all.to_csv(news_file, index=False)
        
        print(f"[OK] Added {len(analyzed_new)} new articles (total: {len(all_articles)})")
        
        # Add to historical data
        print("[*] Adding to historical data...")
        hist_stats = self.historical_manager.add_daily_batch(analyzed_new, datetime.now())
        print(f"[OK] Historical data updated: {hist_stats['total_batches']} batches, {hist_stats['total_historical_articles']} total articles")
        
        # Update state
        state = self._load_state()
        state['last_news_update'] = datetime.now().isoformat()
        self._save_state(state)
        
        return len(analyzed_new)
    
    def update_prices_incremental(self) -> int:
        """
        Update stock prices (always full update since it's fast)
        
        Returns:
            Number of prices updated
        """
        print("\n[*] Updating stock prices...")
        
        # Fetch current prices
        prices = self.price_fetcher.fetch_current_prices(config.STOCK_TICKERS)
        
        # Convert to DataFrame
        price_data = []
        for ticker, data in prices.items():
            if data:
                price_data.append({
                    'ticker': ticker,
                    'current_price': data.get('current_price', 0),
                    'previous_close': data.get('previous_close', 0),
                    'price_change': data.get('price_change', 0),
                    'price_change_percent': data.get('price_change_percent', 0),
                    'volume': data.get('volume', 0),
                    'market_cap': data.get('market_cap', 0),
                    'updated_at': datetime.now().isoformat()
                })
        
        # Save prices
        df_prices = pd.DataFrame(price_data)
        price_file = os.path.join(self.data_dir, "stock_prices.csv")
        df_prices.to_csv(price_file, index=False)
        
        print(f"[OK] Updated {len(price_data)} stock prices")
        
        # Update state
        state = self._load_state()
        state['last_price_update'] = datetime.now().isoformat()
        self._save_state(state)
        
        return len(price_data)
    
    def quick_update(self) -> Dict:
        """
        Perform quick incremental update
        
        Returns:
            Update statistics
        """
        print("=" * 70)
        print("INCREMENTAL UPDATE")
        print("=" * 70)
        
        stats = {
            'news_updated': False,
            'prices_updated': False,
            'new_articles': 0,
            'updated_prices': 0,
            'duration_seconds': 0
        }
        
        start_time = datetime.now()
        
        # Check if news needs update
        if self.should_update_news():
            stats['new_articles'] = self.update_news_incremental()
            stats['news_updated'] = True
        else:
            print("\n[*] News is up-to-date (< 1 hour old)")
        
        # Check if prices need update
        if self.should_update_prices():
            stats['updated_prices'] = self.update_prices_incremental()
            stats['prices_updated'] = True
        else:
            print("\n[*] Prices are up-to-date (< 5 minutes old)")
        
        end_time = datetime.now()
        stats['duration_seconds'] = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("UPDATE COMPLETE")
        print("=" * 70)
        print(f"Duration: {stats['duration_seconds']:.1f} seconds")
        print(f"New articles: {stats['new_articles']}")
        print(f"Updated prices: {stats['updated_prices']}")
        print("=" * 70 + "\n")
        
        return stats


if __name__ == "__main__":
    updater = IncrementalUpdater()
    
    # Perform quick update
    stats = updater.quick_update()
    
    print(f"\nUpdate Statistics:")
    print(f"  News updated: {stats['news_updated']}")
    print(f"  Prices updated: {stats['prices_updated']}")
    print(f"  New articles: {stats['new_articles']}")
    print(f"  Updated prices: {stats['updated_prices']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")
