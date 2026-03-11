"""
Multi-source news scraper for latest financial news
Scrapes from multiple sources to build large dataset
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os


class NewsScraperMultiSource:
    def __init__(self):
        self.output_dir = "data"
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_reuters_business(self, max_articles=100):
        """Scrape Reuters business news"""
        print("\n[Reuters] Scraping business news...")
        articles = []
        
        try:
            url = "https://www.reuters.com/business/"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', {'data-testid': 'Heading'})
            
            for link in links[:max_articles]:
                title = link.get_text(strip=True)
                url = "https://www.reuters.com" + link.get('href', '')
                
                if title and url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Reuters',
                        'category': 'Business',
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_cnbc_markets(self, max_articles=100):
        """Scrape CNBC markets news with pagination"""
        print("\n[CNBC] Scraping markets news...")
        articles = []
        
        try:
            # Scrape multiple sections
            sections = [
                'https://www.cnbc.com/markets/',
                'https://www.cnbc.com/stocks/',
                'https://www.cnbc.com/world-markets/',
                'https://www.cnbc.com/commodities/'
            ]
            
            for section_url in sections:
                try:
                    response = requests.get(section_url, headers=self.headers, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find article cards
                    cards = soup.find_all('div', class_='Card-titleContainer')
                    
                    for card in cards[:max_articles//len(sections)]:
                        link = card.find('a')
                        if link:
                            title = link.get_text(strip=True)
                            url = link.get('href', '')
                            
                            if title and url:
                                articles.append({
                                    'title': title,
                                    'url': url,
                                    'source': 'CNBC',
                                    'category': 'Markets',
                                    'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                    
                    time.sleep(1)
                except:
                    continue
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_marketwatch(self, max_articles=100):
        """Scrape MarketWatch latest news"""
        print("\n[MarketWatch] Scraping latest news...")
        articles = []
        
        try:
            url = "https://www.marketwatch.com/latest-news"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', class_='link')
            
            for link in links[:max_articles]:
                title = link.get_text(strip=True)
                url = link.get('href', '')
                
                if title and url and 'story' in url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'MarketWatch',
                        'category': 'Finance',
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_yahoo_finance(self, max_articles=100):
        """Scrape Yahoo Finance news"""
        print("\n[Yahoo Finance] Scraping news...")
        articles = []
        
        try:
            url = "https://finance.yahoo.com/news/"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('h3')
            
            for h3 in links[:max_articles]:
                link = h3.find('a')
                if link:
                    title = link.get_text(strip=True)
                    url = "https://finance.yahoo.com" + link.get('href', '')
                    
                    if title and url:
                        articles.append({
                            'title': title,
                            'url': url,
                            'source': 'Yahoo Finance',
                            'category': 'Finance',
                            'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_bbc_business(self, max_articles=100):
        """Scrape BBC Business news"""
        print("\n[BBC] Scraping business news...")
        articles = []
        
        try:
            url = "https://www.bbc.com/business"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', {'data-testid': 'internal-link'})
            
            for link in links[:max_articles]:
                title_elem = link.find('h2')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = "https://www.bbc.com" + link.get('href', '')
                    
                    if title and 'business' in url:
                        articles.append({
                            'title': title,
                            'url': url,
                            'source': 'BBC',
                            'category': 'Business',
                            'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_investing_com(self, max_articles=100):
        """Scrape Investing.com news"""
        print("\n[Investing.com] Scraping news...")
        articles = []
        
        try:
            url = "https://www.investing.com/news/stock-market-news"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', class_='title')
            
            for link in links[:max_articles]:
                title = link.get_text(strip=True)
                url = "https://www.investing.com" + link.get('href', '')
                
                if title and url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Investing.com',
                        'category': 'Stock Market',
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_seeking_alpha(self, max_articles=100):
        """Scrape Seeking Alpha news"""
        print("\n[Seeking Alpha] Scraping market news...")
        articles = []
        
        try:
            url = "https://seekingalpha.com/market-news"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', {'data-test-id': 'post-list-item-title'})
            
            for link in links[:max_articles]:
                title = link.get_text(strip=True)
                url = "https://seekingalpha.com" + link.get('href', '')
                
                if title and url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Seeking Alpha',
                        'category': 'Markets',
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_google_news_finance(self, max_articles=100):
        """Scrape Google News finance section"""
        print("\n[Google News] Scraping finance news...")
        articles = []
        
        try:
            url = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JXVnVMVWRDR2dKSlRpZ0FQAQ?hl=en-IN&gl=IN&ceid=IN%3Aen"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', class_='gPFEn')
            
            for link in links[:max_articles]:
                title = link.get_text(strip=True)
                url = "https://news.google.com" + link.get('href', '')[1:]
                
                if title and url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Google News',
                        'category': 'Finance',
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_bloomberg_markets(self, max_articles=100):
        """Scrape Bloomberg markets"""
        print("\n[Bloomberg] Scraping markets news...")
        articles = []
        
        try:
            url = "https://www.bloomberg.com/markets"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', href=True)
            
            for link in links[:max_articles]:
                href = link.get('href', '')
                if '/news/articles/' in href:
                    title = link.get_text(strip=True)
                    url = "https://www.bloomberg.com" + href if not href.startswith('http') else href
                    
                    if title and len(title) > 20:
                        articles.append({
                            'title': title,
                            'url': url,
                            'source': 'Bloomberg',
                            'category': 'Markets',
                            'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            print(f"  [OK] Scraped {len(articles)} articles")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        return articles
    
    def scrape_all_sources(self):
        """Scrape from all sources"""
        print("="*60)
        print("MULTI-SOURCE NEWS SCRAPER")
        print("="*60)
        print("Scraping latest financial news from multiple sources...")
        
        all_articles = []
        
        # Scrape from each source
        all_articles.extend(self.scrape_reuters_business(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_cnbc_markets(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_marketwatch(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_yahoo_finance(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_bbc_business(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_investing_com(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_seeking_alpha(max_articles=50))
        time.sleep(2)
        
        all_articles.extend(self.scrape_google_news_finance(max_articles=100))
        time.sleep(2)
        
        all_articles.extend(self.scrape_bloomberg_markets(max_articles=50))
        
        return all_articles
    
    def save_to_csv(self, articles, filename='scraped_news.csv'):
        """Save scraped articles to CSV"""
        
        if not articles:
            print("\n[WARN] No articles scraped")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Remove duplicates based on title
        df = pd.DataFrame(articles)
        df = df.drop_duplicates(subset=['title'], keep='first')
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"\n[OK] Saved {len(df)} unique articles to {filepath}")
        return filepath
    
    def merge_with_existing(self, new_file='scraped_news.csv', existing_file='gdelt_english_news.csv'):
        """Merge scraped news with existing GDELT data"""
        
        try:
            # Load both files
            new_df = pd.read_csv(os.path.join(self.output_dir, new_file))
            existing_df = pd.read_csv(os.path.join(self.output_dir, existing_file))
            
            # Standardize columns
            new_df['seendate'] = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            new_df['domain'] = new_df['source']
            new_df['language'] = 'en'
            new_df['company'] = ''
            
            # Select common columns
            common_cols = ['title', 'url', 'domain', 'seendate', 'language', 'category', 'company']
            new_df = new_df[['title', 'url', 'source', 'scraped_date', 'category']].copy()
            new_df.columns = ['title', 'url', 'domain', 'seendate', 'category']
            new_df['language'] = 'en'
            new_df['company'] = ''
            
            # Merge
            merged_df = pd.concat([existing_df, new_df], ignore_index=True)
            merged_df = merged_df.drop_duplicates(subset=['title'], keep='first')
            
            # Save merged file
            merged_df.to_csv(os.path.join(self.output_dir, existing_file), index=False, encoding='utf-8')
            
            print(f"\n[OK] Merged datasets: {len(merged_df)} total articles")
            print(f"  Previous: {len(existing_df)}")
            print(f"  New: {len(new_df)}")
            print(f"  Total: {len(merged_df)}")
            
        except Exception as e:
            print(f"\n[ERROR] Merge failed: {e}")


def main():
    scraper = NewsScraperMultiSource()
    
    # Scrape from all sources
    articles = scraper.scrape_all_sources()
    
    if articles:
        # Save scraped articles
        scraper.save_to_csv(articles)
        
        # Merge with existing GDELT data
        scraper.merge_with_existing()
        
        print("\n" + "="*60)
        print("SCRAPING COMPLETE!")
        print("="*60)
        print(f"Total articles scraped: {len(articles)}")
        print("Data merged with existing news dataset")
        print("\nRun process_news.py to process the new articles")
    else:
        print("\n[ERROR] No articles scraped from any source")


if __name__ == "__main__":
    main()
