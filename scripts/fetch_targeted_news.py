"""
Fetch news specifically for target stocks
Uses multiple sources and filters for relevance
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TARGET_STOCKS, STOCK_NAMES

class TargetedNewsScraper:
    def __init__(self):
        self.output_dir = "data"
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_yahoo_finance(self):
        """Scrape Yahoo Finance for stock-specific news"""
        print("\n[Yahoo Finance] Scraping stock news...")
        articles = []
        
        for ticker in TARGET_STOCKS:
            try:
                url = f"https://finance.yahoo.com/quote/{ticker}/news"
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news articles
                news_items = soup.find_all('h3', class_='Mb(5px)')
                
                for item in news_items[:5]:  # Top 5 per stock
                    link = item.find('a')
                    if link:
                        title = link.get_text(strip=True)
                        url = "https://finance.yahoo.com" + link.get('href', '')
                        
                        if title:
                            articles.append({
                                'title': title,
                                'url': url,
                                'source': 'Yahoo Finance',
                                'ticker': ticker,
                                'company': STOCK_NAMES[ticker],
                                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                
                print(f"  {ticker}: {len([a for a in articles if a['ticker'] == ticker])} articles")
                time.sleep(1)
            
            except Exception as e:
                print(f"  {ticker}: ERROR - {e}")
        
        print(f"  [OK] Total: {len(articles)} articles")
        return articles
    
    def scrape_google_news(self):
        """Scrape Google News for stock mentions"""
        print("\n[Google News] Scraping stock mentions...")
        articles = []
        
        for ticker in TARGET_STOCKS:
            try:
                # Search for company name
                company = STOCK_NAMES[ticker]
                query = company.replace(' ', '+')
                url = f"https://news.google.com/search?q={query}+stock&hl=en-US&gl=US&ceid=US:en"
                
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find articles
                news_items = soup.find_all('article')
                
                for item in news_items[:3]:  # Top 3 per stock
                    title_elem = item.find('a', class_='gPFEn')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        if title:
                            articles.append({
                                'title': title,
                                'url': f"https://news.google.com",
                                'source': 'Google News',
                                'ticker': ticker,
                                'company': STOCK_NAMES[ticker],
                                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                
                print(f"  {ticker}: {len([a for a in articles if a['ticker'] == ticker])} articles")
                time.sleep(1)
            
            except Exception as e:
                print(f"  {ticker}: ERROR - {e}")
        
        print(f"  [OK] Total: {len(articles)} articles")
        return articles
    
    def scrape_cnbc(self):
        """Scrape CNBC for market news"""
        print("\n[CNBC] Scraping market news...")
        articles = []
        
        try:
            url = "https://www.cnbc.com/markets/"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article cards
            cards = soup.find_all('div', class_='Card-titleContainer')
            
            for card in cards[:20]:  # Get 20 articles
                link = card.find('a')
                if link:
                    title = link.get_text(strip=True)
                    url = link.get('href', '')
                    
                    # Check if any stock ticker is mentioned
                    mentioned_tickers = []
                    for ticker in TARGET_STOCKS:
                        if ticker in title.upper() or STOCK_NAMES[ticker].upper() in title.upper():
                            mentioned_tickers.append(ticker)
                    
                    if mentioned_tickers:
                        for ticker in mentioned_tickers:
                            articles.append({
                                'title': title,
                                'url': url,
                                'source': 'CNBC',
                                'ticker': ticker,
                                'company': STOCK_NAMES[ticker],
                                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
            
            print(f"  [OK] Found {len(articles)} relevant articles")
        
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_all(self):
        """Scrape from all sources"""
        print("="*60)
        print("TARGETED NEWS SCRAPER - PROTOTYPE STOCKS")
        print("="*60)
        print(f"Target stocks: {', '.join(TARGET_STOCKS)}")
        
        all_articles = []
        
        # Scrape from each source
        all_articles.extend(self.scrape_yahoo_finance())
        time.sleep(2)
        
        all_articles.extend(self.scrape_google_news())
        time.sleep(2)
        
        all_articles.extend(self.scrape_cnbc())
        
        return all_articles
    
    def save_to_csv(self, articles, filename='prototype_news.csv'):
        """Save articles to CSV"""
        
        if not articles:
            print("\n[WARN] No articles scraped")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Remove duplicates based on title
        df = pd.DataFrame(articles)
        df = df.drop_duplicates(subset=['title'], keep='first')
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total articles: {len(df)}")
        print(f"Saved to: {filepath}")
        
        # Show articles per stock
        print("\nArticles per stock:")
        for ticker in TARGET_STOCKS:
            count = len(df[df['ticker'] == ticker])
            print(f"  {ticker} ({STOCK_NAMES[ticker]}): {count}")
        
        return filepath


def main():
    scraper = TargetedNewsScraper()
    
    # Scrape from all sources
    articles = scraper.scrape_all()
    
    if articles:
        # Save articles
        scraper.save_to_csv(articles)
    else:
        print("\n[ERROR] No articles scraped from any source")


if __name__ == "__main__":
    main()
