"""
Multi-Source News Fetcher
Fetches financial news from multiple free APIs and combines them
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from ratelimit import limits, sleep_and_retry
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class NewsAggregator:
    """Aggregates news from multiple free sources"""
    
    def __init__(self):
        self.news_cache = []
        self.last_fetch = None
        
    def fetch_all_news(self, stocks: List[str] = None, topics: List[str] = None) -> List[Dict]:
        """
        Fetch news from all available sources
        
        Args:
            stocks: List of stock tickers to fetch news for
            topics: List of topics to fetch news for (gold, military, etc.)
            
        Returns:
            List of news articles with metadata
        """
        all_news = []
        
        stocks = stocks or config.STOCK_TICKERS
        topics = topics or config.NEWS_TOPICS
        
        print("[*] Starting multi-source news fetch...")
        
        # Fetch from each source
        try:
            news = self.fetch_from_newsapi(stocks, topics)
            all_news.extend(news)
            print(f"[OK] NewsAPI: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] NewsAPI failed: {e}")
        
        try:
            news = self.fetch_from_finnhub(stocks)
            all_news.extend(news)
            print(f"[OK] Finnhub: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Finnhub failed: {e}")
        
        try:
            news = self.fetch_from_alpha_vantage(stocks, topics)
            all_news.extend(news)
            print(f"[OK] Alpha Vantage: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Alpha Vantage failed: {e}")
        
        try:
            news = self.fetch_from_yahoo_rss(stocks)
            all_news.extend(news)
            print(f"[OK] Yahoo RSS: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Yahoo RSS failed: {e}")
        
        try:
            news = self.fetch_from_marketaux(stocks, topics)
            all_news.extend(news)
            print(f"[OK] Marketaux: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Marketaux failed: {e}")
        
        # Remove duplicates based on title
        unique_news = self._remove_duplicates(all_news)
        
        print(f"\n[OK] Total: {len(unique_news)} unique articles from {len(all_news)} total")
        
        self.news_cache = unique_news
        self.last_fetch = datetime.now()
        
        return unique_news
    
    @sleep_and_retry
    @limits(calls=5, period=60)
    def fetch_from_newsapi(self, stocks: List[str], topics: List[str]) -> List[Dict]:
        """Fetch from NewsAPI.org (100 requests/day free)"""
        
        if config.NEWSAPI_KEY == 'YOUR_NEWSAPI_KEY_HERE':
            return []
        
        news = []
        
        # Build query combining stocks and topics
        # Example: (AAPL OR MSFT OR gold OR military) AND (stock OR finance)
        stock_query = ' OR '.join(stocks[:10])  # Limit to 10 stocks per query
        topic_query = ' OR '.join([f'"{topic}"' for topic in topics[:5]])
        
        query = f'({stock_query} OR {topic_query}) AND (stock OR finance OR market)'
        
        params = {
            'q': query,
            'apiKey': config.NEWSAPI_KEY,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 100,
            'from': (datetime.now() - timedelta(days=config.HISTORICAL_DAYS)).isoformat(),
        }
        
        try:
            response = requests.get(config.API_ENDPOINTS['newsapi'], params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                for article in data.get('articles', []):
                    news.append({
                        'source': 'NewsAPI',
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'author': article.get('author', 'Unknown'),
                        'ticker': self._extract_ticker(article.get('title', '') + ' ' + article.get('description', ''), stocks),
                        'topics': self._extract_topics(article.get('title', '') + ' ' + article.get('description', ''), topics),
                    })
        except Exception as e:
            print(f"NewsAPI error: {e}")
        
        return news
    
    @sleep_and_retry
    @limits(calls=50, period=60)
    def fetch_from_finnhub(self, stocks: List[str]) -> List[Dict]:
        """Fetch from Finnhub (60 calls/minute free)"""
        
        if config.FINNHUB_KEY == 'YOUR_FINNHUB_KEY_HERE':
            return []
        
        news = []
        from_date = (datetime.now() - timedelta(days=config.HISTORICAL_DAYS)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        # Fetch news for each stock (limited to avoid rate limits)
        for ticker in stocks[:20]:  # Limit to 20 stocks to stay under rate limit
            try:
                url = f"https://finnhub.io/api/v1/company-news"
                params = {
                    'symbol': ticker,
                    'from': from_date,
                    'to': to_date,
                    'token': config.FINNHUB_KEY
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                articles = response.json()
                
                for article in articles[:5]:  # Limit articles per stock
                    news.append({
                        'source': 'Finnhub',
                        'title': article.get('headline', ''),
                        'description': article.get('summary', ''),
                        'content': article.get('summary', ''),
                        'url': article.get('url', ''),
                        'published_at': datetime.fromtimestamp(article.get('datetime', 0)).isoformat(),
                        'author': article.get('source', 'Unknown'),
                        'ticker': ticker,
                        'topics': [],
                    })
                
                time.sleep(0.1)  # Small delay between requests
                
            except Exception as e:
                print(f"Finnhub error for {ticker}: {e}")
                continue
        
        return news
    
    @sleep_and_retry
    @limits(calls=2, period=60)
    def fetch_from_alpha_vantage(self, stocks: List[str], topics: List[str]) -> List[Dict]:
        """Fetch from Alpha Vantage News Sentiment API (25 requests/day free)"""
        
        if config.ALPHA_VANTAGE_KEY == 'YOUR_ALPHA_VANTAGE_KEY_HERE':
            return []
        
        news = []
        
        # Combine top stocks and topics
        queries = stocks[:3] + topics[:2]  # Very limited due to daily cap
        
        for query in queries:
            try:
                params = {
                    'function': 'NEWS_SENTIMENT',
                    'tickers': query if query in stocks else None,
                    'topics': query if query in topics else None,
                    'apikey': config.ALPHA_VANTAGE_KEY,
                    'limit': 50,
                }
                
                # Remove None values
                params = {k: v for k, v in params.items() if v is not None}
                
                response = requests.get(config.API_ENDPOINTS['alphavantage'], params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                # Check if response has error message
                if isinstance(data, dict) and 'Error Message' in data:
                    print(f"  Alpha Vantage API Error: {data['Error Message']}")
                    continue
                
                if isinstance(data, dict) and 'Information' in data:
                    print(f"  Alpha Vantage rate limit: {data['Information']}")
                    continue
                
                for article in data.get('feed', [])[:20]:
                    if isinstance(article, dict):  # Make sure it's a dictionary
                        news.append({
                            'source': 'AlphaVantage',
                            'title': article.get('title', ''),
                            'description': article.get('summary', ''),
                            'content': article.get('summary', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('time_published', ''),
                            'author': ', '.join([s.get('name', '') for s in article.get('authors', [])]) if article.get('authors') else 'Unknown',
                            'ticker': self._extract_ticker(article.get('title', ''), stocks),
                            'topics': [t.get('topic', '') for t in article.get('topics', [])] if article.get('topics') else [],
                            'sentiment_score': article.get('overall_sentiment_score', 0),
                            'sentiment_label': article.get('overall_sentiment_label', 'Neutral'),
                        })
                
                time.sleep(15)  # Rate limit: only 5 per minute on free tier
                
            except Exception as e:
                print(f"Alpha Vantage error for {query}: {e}")
                continue
        
        return news
    
    def fetch_from_yahoo_rss(self, stocks: List[str]) -> List[Dict]:
        """Fetch from Yahoo Finance RSS (Free, unlimited)"""
        
        news = []
        
        # Fetch general finance news
        try:
            feed = feedparser.parse('https://finance.yahoo.com/news/rssindex')
            for entry in feed.entries[:30]:
                news.append({
                    'source': 'Yahoo Finance',
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published_at': entry.get('published', ''),
                    'author': 'Yahoo Finance',
                    'ticker': self._extract_ticker(entry.get('title', ''), stocks),
                    'topics': [],
                })
        except Exception as e:
            print(f"Yahoo RSS error: {e}")
        
        return news
    
    @sleep_and_retry
    @limits(calls=5, period=60)
    def fetch_from_marketaux(self, stocks: List[str], topics: List[str]) -> List[Dict]:
        """Fetch from Marketaux (100 requests/day free)"""
        
        if config.MARKETAUX_KEY == 'YOUR_MARKETAUX_KEY_HERE':
            return []
        
        news = []
        
        # Marketaux supports multiple symbols in one request
        symbols = ','.join(stocks[:10])
        
        try:
            params = {
                'api_token': config.MARKETAUX_KEY,
                'symbols': symbols,
                'limit': 50,
                'language': 'en',
            }
            
            response = requests.get(config.API_ENDPOINTS['marketaux'], params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for article in data.get('data', []):
                news.append({
                    'source': 'Marketaux',
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('snippet', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('published_at', ''),
                    'author': article.get('source', 'Unknown'),
                    'ticker': ','.join([e.get('symbol', '') for e in article.get('entities', []) if e.get('type') == 'equity']),
                    'topics': [e.get('name', '') for e in article.get('entities', []) if e.get('type') == 'topic'],
                })
        except Exception as e:
            print(f"Marketaux error: {e}")
        
        return news
    
    def _extract_ticker(self, text: str, stocks: List[str]) -> str:
        """Extract stock ticker from text"""
        text_upper = text.upper()
        for ticker in stocks:
            if ticker in text_upper or ticker.lower() in text.lower():
                return ticker
        return ''
    
    def _extract_topics(self, text: str, topics: List[str]) -> List[str]:
        """Extract topics from text"""
        found_topics = []
        text_lower = text.lower()
        for topic in topics:
            if topic.lower() in text_lower:
                found_topics.append(topic)
        return found_topics
    
    def _remove_duplicates(self, news: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on similar titles"""
        seen_titles = set()
        unique_news = []
        
        for article in news:
            title = article.get('title', '').lower().strip()
            # Simple deduplication - could use fuzzy matching for better results
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(article)
        
        return unique_news

if __name__ == "__main__":
    # Test the aggregator
    aggregator = NewsAggregator()
    news = aggregator.fetch_all_news()
    
    print(f"\n[INFO] Fetched {len(news)} unique articles")
    
    if news:
        print("\n[SAMPLE] Sample articles:")
        for article in news[:5]:
            print(f"\n- {article['title']}")
            print(f"  Source: {article['source']} | Ticker: {article.get('ticker', 'N/A')}")
            print(f"  URL: {article['url']}")
