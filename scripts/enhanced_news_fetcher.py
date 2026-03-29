"""
Enhanced News Fetcher - Optimized for 500+ stocks
Fetches MORE news and ensures relevance/impact
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.news_aggregator import NewsAggregator
from scripts.free_news_fetcher import FreeNewsFetcher
import config

class EnhancedNewsFetcher:
    """
    Enhanced fetcher that combines multiple sources and 
    fetches in batches to cover 500+ stocks
    """
    
    def __init__(self):
        self.api_fetcher = NewsAggregator()
        self.free_fetcher = FreeNewsFetcher()
        
    def fetch_comprehensive_news(self, max_articles: int = 1000) -> list:
        """
        Fetch comprehensive news from all sources in batches
        
        Strategy:
        1. Fetch general market news (affects all stocks)
        2. Fetch sector-specific news (affects groups of stocks)
        3. Fetch stock-specific news for top stocks
        4. Combine and deduplicate
        """
        print("=" * 70)
        print("[*] ENHANCED NEWS FETCHER - Optimized for 500+ stocks")
        print("=" * 70 + "\n")
        
        all_news = []
        
        # 1. General Market News (affects ALL stocks)
        print("\n[NEWS] Step 1: Fetching General Market News...")
        print("-" * 70)
        general_topics = ['stock market', 'S&P 500', 'nasdaq', 'dow jones', 
                         'wall street', 'market crash', 'bull market', 'bear market']
        
        try:
            market_news = self.api_fetcher.fetch_from_newsapi([], general_topics)
            all_news.extend(market_news)
            print(f"[OK] General Market: {len(market_news)} articles")
        except Exception as e:
            print(f"[WARN] Market news failed: {e}")
        
        # 2. Macro Economic News (affects most stocks)
        print("\n[MACRO] Step 2: Fetching Macro Economic News...")
        print("-" * 70)
        macro_topics = config.NEWS_TOPICS  # inflation, rates, gold, oil, etc.
        
        try:
            # Use free fetcher for macro topics
            free_news = self.free_fetcher.fetch_google_news_rss(macro_topics[:10])
            all_news.extend(free_news)
            print(f"[OK] Macro News: {len(free_news)} articles")
        except Exception as e:
            print(f"[WARN] Macro news failed: {e}")
        
        # 3. Sector-Specific News (affects groups of stocks)
        print("\n[SECTOR] Step 3: Fetching Sector News...")
        print("-" * 70)
        sectors = ['technology', 'finance', 'energy', 'healthcare', 'defense',
                  'retail', 'automotive', 'semiconductors', 'cloud computing']
        
        for sector in sectors:
            try:
                sector_query = f"{sector} stocks"
                sector_news = self.free_fetcher.fetch_google_news_rss([sector_query])
                all_news.extend(sector_news)
            except:
                pass
        
        print(f"[OK] Sector News: Added articles")
        
        # 4. Top Stocks News (via APIs)
        print("\n[STOCKS] Step 4: Fetching Top 100 Stock News...")
        print("-" * 70)
        
        # Prioritize top stocks by market cap
        top_stocks = config.STOCK_TICKERS[:100]  # First 100 from config
        
        try:
            # Finnhub for stock-specific news
            stock_news = self.api_fetcher.fetch_from_finnhub(top_stocks)
            all_news.extend(stock_news)
            print(f"[OK] Top 100 Stocks: {len(stock_news)} articles")
        except Exception as e:
            print(f"[WARN] Stock news failed: {e}")
        
        # 5. Yahoo Finance RSS (free backup)
        print("\n[YAHOO] Step 5: Fetching Yahoo Finance News...")
        print("-" * 70)
        
        try:
            yahoo_news = self.free_fetcher.fetch_yahoo_finance_rss()
            all_news.extend(yahoo_news)
            print(f"[OK] Yahoo Finance: {len(yahoo_news)} articles")
        except Exception as e:
            print(f"[WARN] Yahoo failed: {e}")
        
        # 6. Finviz scraping for additional stocks
        print("\n[FINVIZ] Step 6: Scraping Additional Stock News...")
        print("-" * 70)
        
        try:
            # Scrape next batch of stocks
            next_batch = config.STOCK_TICKERS[100:150]
            finviz_news = self.free_fetcher.fetch_finviz_news(next_batch)
            all_news.extend(finviz_news)
            print(f"[OK] Finviz: {len(finviz_news)} articles")
        except Exception as e:
            print(f"[WARN] Finviz failed: {e}")
        
        # 7. Marketaux for diverse coverage
        print("\n[MARKETAUX] Step 7: Fetching Marketaux News...")
        print("-" * 70)
        
        try:
            marketaux_news = self.api_fetcher.fetch_from_marketaux(top_stocks[:20], macro_topics[:5])
            all_news.extend(marketaux_news)
            print(f"[OK] Marketaux: {len(marketaux_news)} articles")
        except Exception as e:
            print(f"[WARN] Marketaux failed: {e}")
        
        # Remove duplicates
        unique_news = self._remove_duplicates(all_news)
        
        # Limit to max articles
        if len(unique_news) > max_articles:
            unique_news = unique_news[:max_articles]
        
        print("\n" + "=" * 70)
        print(f"[OK] TOTAL: {len(unique_news)} unique articles")
        print(f"   Coverage: All 500+ stocks via general market + sector news")
        print(f"   Direct mentions: Top 150 stocks")
        print("=" * 70)
        
        return unique_news
    
    def _remove_duplicates(self, news: list) -> list:
        """Remove duplicate articles"""
        seen_titles = set()
        unique = []
        
        for article in news:
            title = article.get('title', '').lower().strip()
            if title and len(title) > 10 and title not in seen_titles:
                seen_titles.add(title)
                unique.append(article)
        
        return unique


if __name__ == "__main__":
    fetcher = EnhancedNewsFetcher()
    news = fetcher.fetch_comprehensive_news(max_articles=1000)
    
    print("\n" + "=" * 70)
    print("[SAMPLE] ARTICLES:")
    print("=" * 70 + "\n")
    
    for i, article in enumerate(news[:10], 1):
        print(f"{i}. {article['title'][:80]}")
        print(f"   Source: {article['source']} | Ticker: {article.get('ticker', 'General Market')}")
        print()
    
    # Count by source
    from collections import Counter
    sources = Counter(a['source'] for a in news)
    
    print("\n" + "=" * 70)
    print("[STATS] ARTICLES BY SOURCE:")
    print("=" * 70)
    for source, count in sources.most_common():
        print(f"  {source:20s}: {count:4d} articles")
