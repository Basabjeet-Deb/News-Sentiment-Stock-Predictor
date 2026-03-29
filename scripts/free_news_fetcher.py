"""
FREE News Fetcher - NO API KEYS REQUIRED!
Uses free sources: Yahoo Finance RSS, Google News RSS, and web scraping
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import time
import re

class FreeNewsFetcher:
    """Fetch financial news without any API keys"""
    
    def __init__(self):
        self.news_cache = []
        
    def fetch_all_news(self, stocks: List[str] = None) -> List[Dict]:
        """
        Fetch news from free sources (NO API KEYS NEEDED)
        
        Sources:
        1. Yahoo Finance RSS - General market news
        2. Yahoo Finance per-stock pages - Stock-specific news
        3. Google News RSS - Financial news
        4. Finviz - Stock news scraping
        """
        all_news = []
        
        if stocks is None:
            stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'JPM']
        
        print("[*] Fetching news from FREE sources (no API keys needed)...\n")
        
        # 1. Yahoo Finance general news (RSS)
        try:
            news = self.fetch_yahoo_finance_rss()
            all_news.extend(news)
            print(f"[OK] Yahoo Finance General: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Yahoo General failed: {e}")
        
        # 2. Yahoo Finance per stock
        try:
            news = self.fetch_yahoo_stock_news(stocks[:10])  # Limit to 10 stocks
            all_news.extend(news)
            print(f"[OK] Yahoo Stock News: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Yahoo Stock failed: {e}")
        
        # 3. Google News RSS
        try:
            news = self.fetch_google_news_rss(stocks[:5])
            all_news.extend(news)
            print(f"[OK] Google News: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Google News failed: {e}")
        
        # 4. Finviz scraping
        try:
            news = self.fetch_finviz_news(stocks[:10])
            all_news.extend(news)
            print(f"[OK] Finviz: {len(news)} articles")
        except Exception as e:
            print(f"[WARN] Finviz failed: {e}")
        
        # Remove duplicates
        unique_news = self._remove_duplicates(all_news)
        
        print(f"\n[OK] TOTAL: {len(unique_news)} unique articles\n")
        
        return unique_news
    
    def fetch_yahoo_finance_rss(self) -> List[Dict]:
        """Fetch from Yahoo Finance RSS feed (FREE, no key needed)"""
        news = []
        
        rss_urls = [
            'https://finance.yahoo.com/news/rssindex',  # General news
            'https://finance.yahoo.com/rss/topstories',  # Top stories
        ]
        
        for rss_url in rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:20]:  # Limit per feed
                    news.append({
                        'source': 'Yahoo Finance RSS',
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'published_at': entry.get('published', datetime.now().isoformat()),
                        'ticker': '',
                        'topics': [],
                    })
                time.sleep(1)  # Be polite
            except Exception as e:
                print(f"  Error with {rss_url}: {e}")
        
        return news
    
    def fetch_yahoo_stock_news(self, stocks: List[str]) -> List[Dict]:
        """Fetch news for specific stocks from Yahoo Finance"""
        news = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for ticker in stocks:
            try:
                # Yahoo Finance stock page has an RSS feed
                rss_url = f'https://finance.yahoo.com/rss/headline?s={ticker}'
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:5]:  # 5 articles per stock
                    news.append({
                        'source': f'Yahoo Finance',
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'published_at': entry.get('published', datetime.now().isoformat()),
                        'ticker': ticker,
                        'topics': [],
                    })
                
                time.sleep(0.5)  # Be polite
                
            except Exception as e:
                print(f"  Error fetching {ticker}: {e}")
        
        return news
    
    def fetch_google_news_rss(self, stocks: List[str]) -> List[Dict]:
        """Fetch from Google News RSS (FREE, no key needed)"""
        news = []
        
        # Topics that impact stocks
        topics = ['stock market', 'gold', 'oil prices', 'inflation', 'federal reserve']
        
        queries = stocks[:5] + topics  # Combine stocks and topics
        
        for query in queries:
            try:
                # Google News RSS feed
                rss_url = f'https://news.google.com/rss/search?q={query}+stock&hl=en-US&gl=US&ceid=US:en'
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:5]:  # Limit per query
                    news.append({
                        'source': 'Google News',
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'published_at': entry.get('published', datetime.now().isoformat()),
                        'ticker': query if query in stocks else '',
                        'topics': [query] if query in topics else [],
                    })
                
                time.sleep(1)  # Be polite
                
            except Exception as e:
                print(f"  Error with query '{query}': {e}")
        
        return news
    
    def fetch_finviz_news(self, stocks: List[str]) -> List[Dict]:
        """Scrape news from Finviz (FREE, no key needed)"""
        news = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for ticker in stocks:
            try:
                url = f'https://finviz.com/quote.ashx?t={ticker}'
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news table
                news_table = soup.find('table', {'class': 'fullview-news-outer'})
                
                if news_table:
                    rows = news_table.find_all('tr')
                    
                    for row in rows[:5]:  # Limit per stock
                        try:
                            link = row.find('a')
                            if link:
                                title = link.get_text(strip=True)
                                href = link.get('href', '')
                                
                                # Get timestamp
                                time_cell = row.find('td', {'align': 'right'})
                                timestamp = time_cell.get_text(strip=True) if time_cell else ''
                                
                                news.append({
                                    'source': 'Finviz',
                                    'title': title,
                                    'description': '',
                                    'url': href,
                                    'published_at': timestamp or datetime.now().isoformat(),
                                    'ticker': ticker,
                                    'topics': [],
                                })
                        except:
                            continue
                
                time.sleep(1)  # Be polite
                
            except Exception as e:
                print(f"  Error scraping {ticker}: {e}")
        
        return news
    
    def _remove_duplicates(self, news: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title"""
        seen_titles = set()
        unique_news = []
        
        for article in news:
            title = article.get('title', '').lower().strip()
            # Clean title (remove source prefix like "Reuters - ")
            title = re.sub(r'^[^-]+-\s*', '', title)
            
            if title and len(title) > 10 and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(article)
        
        return unique_news


# ============================================================================
# QUICK TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("[FREE] FREE NEWS FETCHER - NO API KEYS REQUIRED!")
    print("=" * 70 + "\n")
    
    fetcher = FreeNewsFetcher()
    
    # Test with a few stocks
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    news = fetcher.fetch_all_news(test_stocks)
    
    print("\n" + "=" * 70)
    print("[SAMPLE] ARTICLES:")
    print("=" * 70 + "\n")
    
    for i, article in enumerate(news[:10], 1):
        print(f"{i}. {article['title']}")
        print(f"   Source: {article['source']} | Ticker: {article.get('ticker', 'N/A')}")
        print(f"   URL: {article['url'][:80]}...")
        print()
    
    print("=" * 70)
    print(f"[OK] SUCCESS! Fetched {len(news)} articles WITHOUT any API keys!")
    print("=" * 70)
