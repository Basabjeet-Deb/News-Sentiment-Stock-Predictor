"""
Fetch news data from GDELT API
GDELT provides free access to global news articles
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os


class NewsDataFetcher:
    def __init__(self):
        self.base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        self.output_dir = "data"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_news(self, query="stock market OR economy OR finance", 
                   mode="artlist", max_records=250, timespan="1d"):
        """
        Fetch news articles from GDELT
        
        Parameters:
        - query: Search terms
        - mode: artlist (article list) or timeline
        - max_records: Number of articles to fetch (max 250 per request)
        - timespan: Time range (1h, 6h, 1d, 3d, 7d, 30d)
        """
        
        params = {
            'query': query,
            'mode': mode,
            'maxrecords': max_records,
            'timespan': timespan,
            'format': 'json',
            'sort': 'datedesc'
        }
        
        print(f"Fetching news for: {query}")
        print(f"Timespan: {timespan}, Max records: {max_records}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'articles' in data:
                articles = data['articles']
                print(f"[OK] Fetched {len(articles)} articles")
                return articles
            else:
                print("[WARN] No articles found")
                return []
                
        except Exception as e:
            print(f"[ERROR] Error fetching news: {e}")
            return []
    
    def fetch_stock_news(self, companies=None, timespan="1d"):
        """
        Fetch news for specific companies/stocks
        
        Parameters:
        - companies: List of company names or stock tickers
        - timespan: Time range
        """
        
        if companies is None:
            companies = [
                "Apple", "Microsoft", "Google", "Amazon", "Tesla",
                "Meta", "Netflix", "NVIDIA", "Intel", "AMD"
            ]
        
        all_articles = []
        
        for company in companies:
            print(f"\nFetching news for: {company}")
            query = f"{company} AND (stock OR shares OR market OR earnings)"
            articles = self.fetch_news(query=query, timespan=timespan, max_records=50)
            
            # Tag articles with company name
            for article in articles:
                article['company'] = company
            
            all_articles.extend(articles)
            time.sleep(1)  # Rate limiting
        
        return all_articles
    
    def save_to_csv(self, articles, filename=None):
        """Save articles to CSV file"""
        
        if not articles:
            print("No articles to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_data_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Extract relevant fields
        data = []
        for article in articles:
            data.append({
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'domain': article.get('domain', ''),
                'seendate': article.get('seendate', ''),
                'socialimage': article.get('socialimage', ''),
                'language': article.get('language', ''),
                'category': article.get('category', 'general'),
                'company': article.get('company', '')
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"\n[OK] Saved {len(df)} articles to {filepath}")
        return filepath


def main():
    fetcher = NewsDataFetcher()
    
    print("="*60)
    print("NEWS DATA FETCHER - GDELT (Optimized)")
    print("="*60)
    
    # Simplified categories with longer delays
    categories = [
        ("Business", "business economy"),
        ("Technology", "technology AI"),
        ("Finance", "stock market finance"),
        ("Energy", "oil energy"),
        ("Healthcare", "healthcare medical"),
        ("Corporate", "earnings CEO"),
        ("Crypto", "bitcoin crypto")
    ]
    
    all_news = []
    
    print(f"\nFetching from {len(categories)} categories...")
    print(f"Timespan: 30 days")
    print(f"Strategy: Slow and steady to avoid rate limits\n")
    
    for i, (category, query) in enumerate(categories):
        print(f"[{i+1}/{len(categories)}] {category}")
        
        # Fetch with smaller batches
        articles = fetcher.fetch_news(
            query=query,
            timespan="30d",
            max_records=250
        )
        
        for article in articles:
            article['category'] = category
        
        all_news.extend(articles)
        print(f"  Total: {len(all_news)} articles\n")
        
        # Long delay between requests (10 seconds)
        if i < len(categories) - 1:
            print(f"  Waiting 10 seconds before next category...")
            time.sleep(10)
    
    if all_news:
        filepath = fetcher.save_to_csv(all_news, filename="gdelt_english_news.csv")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total articles: {len(all_news)}")
        print(f"Categories: {len(categories)}")
        print(f"Saved to: {filepath}")
        print(f"\nReady for distributed processing!")
    else:
        print("\n[ERROR] No news fetched")


if __name__ == "__main__":
    main()
