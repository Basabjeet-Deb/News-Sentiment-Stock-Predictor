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
                   mode="artlist", max_records=5000, timespan="1d"):
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
    print("NEWS DATA FETCHER - LARGE DATASET (15,000+ articles)")
    print("="*60)
    print("Strategy: Time-window approach to avoid rate limits")
    print("Estimated time: 10-11 minutes\n")
    
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
    days_per_category = 9  # 9 days × 7 categories = 63 requests
    
    total_requests = len(categories) * days_per_category
    current_request = 0
    
    print(f"Total requests: {total_requests}")
    print(f"Target articles: ~{total_requests * 250:,}\n")
    
    for cat_idx, (category, query) in enumerate(categories):
        print(f"\n[{cat_idx+1}/{len(categories)}] {category}")
        print(f"Fetching {days_per_category} days of data...")
        
        category_articles = []
        
        for day in range(1, days_per_category + 1):
            current_request += 1
            
            print(f"  Day {day}/{days_per_category} (Request {current_request}/{total_requests})...", end=" ")
            
            articles = fetcher.fetch_news_by_day(
                query=query,
                days_ago=day,
                max_records=250
            )
            
            if articles:
                print(f"{len(articles)} articles")
                for article in articles:
                    article['category'] = category
                category_articles.extend(articles)
            else:
                print("0 articles")
            
            # Delay between requests (15 seconds to be safe)
            if current_request < total_requests:
                time.sleep(15)
        
        all_news.extend(category_articles)
        print(f"  Category total: {len(category_articles)} articles")
        print(f"  Overall total: {len(all_news)} articles")
    
    if all_news:
        filepath = fetcher.save_to_csv(all_news, filename="gdelt_english_news.csv")
        
        print("\n" + "="*60)
        print("COLLECTION COMPLETE!")
        print("="*60)
        print(f"Total articles: {len(all_news):,}")
        print(f"Categories: {len(categories)}")
        print(f"Saved to: {filepath}")
        print(f"\nReady for distributed processing across 3 workers!")
        print(f"Each worker will process ~{len(all_news) // 3:,} articles")
    else:
        print("\n[ERROR] No news fetched")
            
            try:
                response = requests.get(fetcher.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'articles' in data:
                    articles = data['articles']
                    
                    # Tag with category
                    for article in articles:
                        article['category'] = category
                        article['fetch_day'] = day
                    
                    all_news.extend(articles)
                    print(f"  [OK] Fetched {len(articles)} articles")
                else:
                    print(f"  [WARN] No articles found")
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
            
            print(f"  Total collected: {len(all_news):,} articles")
            
            # Progress bar
            progress = (current_request / total_requests) * 100
            print(f"  Progress: {progress:.1f}%")
            
            # Delay between requests (10 seconds)
            if current_request < total_requests:
                print(f"  Waiting 10 seconds...")
                time.sleep(10)
    
    # Save results
    if all_news:
        filepath = fetcher.save_to_csv(all_news, filename="gdelt_english_news.csv")
        
        print("\n" + "="*60)
        print("COLLECTION COMPLETE!")
        print("="*60)
        print(f"Total articles: {len(all_news):,}")
        print(f"Categories: {len(categories)}")
        print(f"Days per category: 9")
        print(f"Saved to: {filepath}")
        print(f"\nDataset ready for distributed processing!")
        print(f"Each worker will process ~{len(all_news) // 3:,} articles")
    else:
        print("\n[ERROR] No news fetched")
            
            all_news.extend(articles)
            
            print(f"{len(articles)} articles | Total: {len(all_news)}")
            
            # Progress indicator
            progress = (current_request / total_requests) * 100
            elapsed = time.time() - start_time
            estimated_total = (elapsed / current_request) * total_requests if current_request > 0 else 0
            remaining = estimated_total - elapsed
            
            print(f"  Progress: {progress:.1f}% | Elapsed: {elapsed/60:.1f}m | Remaining: ~{remaining/60:.1f}m")
            
            # Delay between requests (10 seconds)
            if current_request < total_requests:
                print(f"  Waiting 10 seconds...")
                time.sleep(10)
    
    # Save results
    if all_news:
        filepath = fetcher.save_to_csv(all_news, filename="gdelt_english_news.csv")
        
        total_time = time.time() - start_time
        
        print("\n" + "="*60)
        print("COLLECTION COMPLETE!")
        print("="*60)
        print(f"Total articles: {len(all_news)}")
        print(f"Categories: {len(categories)}")
        print(f"Requests made: {current_request}")
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Saved to: {filepath}")
        print(f"\nReady for distributed processing across 3 workers!")
        print(f"Each worker will process ~{len(all_news) / 3:.0f} articles")
    else:
        print("\n[ERROR] No news fetched")
            
            all_news.extend(articles)
            
            # Progress update
            elapsed = time.time() - start_time
            progress = (current_request / total_requests) * 100
            eta = (elapsed / current_request) * (total_requests - current_request)
            
            print(f"  Total collected: {len(all_news)} articles")
            print(f"  Progress: {progress:.1f}%")
            print(f"  ETA: {eta/60:.1f} minutes")
            
            # Delay between requests (except last one)
            if current_request < total_requests:
                print(f"  Waiting 10 seconds...")
                time.sleep(10)
    
    # Save results
    if all_news:
        filepath = fetcher.save_to_csv(all_news, filename="gdelt_english_news.csv")
        
        total_time = time.time() - start_time
        
        print("\n" + "="*60)
        print("COLLECTION COMPLETE!")
        print("="*60)
        print(f"Total articles: {len(all_news)}")
        print(f"Categories: {len(categories)}")
        print(f"Time taken: {total_time/60:.1f} minutes")
        print(f"Saved to: {filepath}")
        print(f"\nDataset ready for distributed processing!")
        print(f"Each worker will process ~{len(all_news) / 3:.0f} articles")
    else:
        print("\n[ERROR] No news fetched")


if __name__ == "__main__":
    main()
