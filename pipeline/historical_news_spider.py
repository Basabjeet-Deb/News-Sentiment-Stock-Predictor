"""
Historical Financial News Spider
Scrapes historical news from multiple financial websites with date ranges
Supports both real-time and historical data collection
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime, timedelta
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class HistoricalFinancialNewsSpider(scrapy.Spider):
    name = 'historical_financial_news'
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 8,  # Lower for historical scraping
        'DOWNLOAD_DELAY': 1.0,  # Be respectful with historical requests
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 30,
    }
    
    def __init__(self, tickers=None, start_date=None, end_date=None, mode='realtime', *args, **kwargs):
        super(HistoricalFinancialNewsSpider, self).__init__(*args, **kwargs)
        self.tickers = tickers or config.STOCK_TICKERS[:100]
        self.mode = mode  # 'realtime' or 'historical'
        
        # Date range for historical scraping
        if start_date:
            self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            self.start_date = datetime.now() - timedelta(days=180)  # Default: 6 months
        
        if end_date:
            self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            self.end_date = datetime.now()
        
        self.articles = []
        
        self.logger.info(f"Mode: {self.mode}")
        self.logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
        self.logger.info(f"Tickers: {len(self.tickers)}")
        
    def start_requests(self):
        """Generate URLs to scrape based on mode"""
        
        if self.mode == 'historical':
            yield from self._historical_requests()
        else:
            yield from self._realtime_requests()
    
    def _realtime_requests(self):
        """Real-time scraping (current news)"""
        
        # 1. Finviz - Stock-specific news
        for ticker in self.tickers[:50]:
            url = f'https://finviz.com/quote.ashx?t={ticker}'
            yield scrapy.Request(url, callback=self.parse_finviz, meta={'ticker': ticker})
        
        # 2. MarketWatch - Latest news
        yield scrapy.Request('https://www.marketwatch.com/latest-news', callback=self.parse_marketwatch)
        
        # 3. Seeking Alpha - Market news
        yield scrapy.Request('https://seekingalpha.com/market-news', callback=self.parse_seeking_alpha)
        
        # 4. Reuters - Business news
        yield scrapy.Request('https://www.reuters.com/business/', callback=self.parse_reuters)
        
        # 5. Bloomberg - Markets
        yield scrapy.Request('https://www.bloomberg.com/markets', callback=self.parse_bloomberg)
    
    def _historical_requests(self):
        """Historical scraping with date ranges"""
        
        # Generate date range (weekly intervals for efficiency)
        current_date = self.start_date
        date_ranges = []
        
        while current_date < self.end_date:
            week_end = min(current_date + timedelta(days=7), self.end_date)
            date_ranges.append((current_date, week_end))
            current_date = week_end
        
        self.logger.info(f"Scraping {len(date_ranges)} weekly periods")
        
        # 1. Finviz - Historical news by date
        for ticker in self.tickers[:100]:  # More tickers for historical
            for start, end in date_ranges:
                # Finviz doesn't have date filtering in URL, but we can filter results
                url = f'https://finviz.com/quote.ashx?t={ticker}'
                yield scrapy.Request(
                    url, 
                    callback=self.parse_finviz_historical,
                    meta={'ticker': ticker, 'start_date': start, 'end_date': end}
                )
        
        # 2. MarketWatch - Archive by date
        for start, end in date_ranges:
            # MarketWatch has date-based archives
            date_str = start.strftime('%Y/%m/%d')
            yield scrapy.Request(
                f'https://www.marketwatch.com/latest-news?mod=top_nav',
                callback=self.parse_marketwatch,
                meta={'date': start}
            )
        
        # 3. Seeking Alpha - Historical articles
        for ticker in self.tickers[:50]:
            # Seeking Alpha has ticker-specific news pages
            yield scrapy.Request(
                f'https://seekingalpha.com/symbol/{ticker}/news',
                callback=self.parse_seeking_alpha_ticker,
                meta={'ticker': ticker}
            )
        
        # 4. Yahoo Finance RSS - Historical (if available)
        for ticker in self.tickers[:200]:
            url = f'https://finance.yahoo.com/quote/{ticker}/news'
            yield scrapy.Request(
                url,
                callback=self.parse_yahoo_finance,
                meta={'ticker': ticker}
            )
    
    def parse_finviz(self, response):
        """Parse Finviz news table (real-time)"""
        ticker = response.meta['ticker']
        
        news_table = response.css('table.fullview-news-outer')
        
        for row in news_table.css('tr'):
            try:
                date_elem = row.css('td:first-child::text').get()
                link_elem = row.css('a')
                
                if link_elem:
                    title = link_elem.css('::text').get()
                    url = link_elem.css('::attr(href)').get()
                    source = row.css('span::text').get()
                    
                    if title and url:
                        article = {
                            'source': source or 'Finviz',
                            'title': title.strip(),
                            'url': url,
                            'ticker': ticker,
                            'published_at': date_elem or '',
                            'description': '',
                            'content': '',
                            'author': 'Unknown',
                            'topics': [],
                            'scraped_at': datetime.now().isoformat(),
                        }
                        self.articles.append(article)
                        yield article
            except Exception as e:
                self.logger.error(f"Error parsing Finviz row: {e}")
    
    def parse_finviz_historical(self, response):
        """Parse Finviz with date filtering"""
        ticker = response.meta['ticker']
        start_date = response.meta['start_date']
        end_date = response.meta['end_date']
        
        news_table = response.css('table.fullview-news-outer')
        
        for row in news_table.css('tr'):
            try:
                date_elem = row.css('td:first-child::text').get()
                link_elem = row.css('a')
                
                if link_elem and date_elem:
                    # Parse date and filter
                    article_date = self._parse_finviz_date(date_elem)
                    
                    if article_date and start_date <= article_date <= end_date:
                        title = link_elem.css('::text').get()
                        url = link_elem.css('::attr(href)').get()
                        source = row.css('span::text').get()
                        
                        if title and url:
                            article = {
                                'source': source or 'Finviz',
                                'title': title.strip(),
                                'url': url,
                                'ticker': ticker,
                                'published_at': article_date.isoformat(),
                                'description': '',
                                'content': '',
                                'author': 'Unknown',
                                'topics': [],
                                'scraped_at': datetime.now().isoformat(),
                            }
                            self.articles.append(article)
                            yield article
            except Exception as e:
                self.logger.error(f"Error parsing Finviz historical: {e}")
    
    def parse_marketwatch(self, response):
        """Parse MarketWatch latest news"""
        
        articles = response.css('div.article__content')
        
        for article in articles:
            try:
                title = article.css('h3.article__headline a::text').get()
                url = article.css('h3.article__headline a::attr(href)').get()
                description = article.css('p.article__summary::text').get()
                time = article.css('span.article__timestamp::text').get()
                
                if title and url:
                    article_data = {
                        'source': 'MarketWatch',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': self._extract_ticker(title),
                        'published_at': time or '',
                        'description': description.strip() if description else '',
                        'content': '',
                        'author': 'MarketWatch',
                        'topics': [],
                        'scraped_at': datetime.now().isoformat(),
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing MarketWatch: {e}")
    
    def parse_seeking_alpha(self, response):
        """Parse Seeking Alpha market news"""
        
        articles = response.css('article')
        
        for article in articles[:20]:
            try:
                title = article.css('a[data-test-id="post-list-item-title"]::text').get()
                url = article.css('a[data-test-id="post-list-item-title"]::attr(href)').get()
                description = article.css('span[data-test-id="post-list-content"]::text').get()
                
                if title and url:
                    article_data = {
                        'source': 'Seeking Alpha',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': self._extract_ticker(title),
                        'published_at': '',
                        'description': description.strip() if description else '',
                        'content': '',
                        'author': 'Seeking Alpha',
                        'topics': [],
                        'scraped_at': datetime.now().isoformat(),
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Seeking Alpha: {e}")
    
    def parse_seeking_alpha_ticker(self, response):
        """Parse Seeking Alpha ticker-specific news"""
        ticker = response.meta['ticker']
        
        articles = response.css('article')
        
        for article in articles[:50]:  # More articles for historical
            try:
                title = article.css('a::text').get()
                url = article.css('a::attr(href)').get()
                date = article.css('time::attr(datetime)').get()
                
                if title and url:
                    article_data = {
                        'source': 'Seeking Alpha',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': ticker,
                        'published_at': date or '',
                        'description': '',
                        'content': '',
                        'author': 'Seeking Alpha',
                        'topics': [],
                        'scraped_at': datetime.now().isoformat(),
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Seeking Alpha ticker: {e}")
    
    def parse_reuters(self, response):
        """Parse Reuters business news"""
        
        articles = response.css('div[data-testid="MediaStoryCard"]')
        
        for article in articles[:30]:
            try:
                title = article.css('a[data-testid="Heading"]::text').get()
                url = article.css('a[data-testid="Heading"]::attr(href)').get()
                description = article.css('p[data-testid="Body"]::text').get()
                
                if title and url:
                    article_data = {
                        'source': 'Reuters',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': self._extract_ticker(title),
                        'published_at': '',
                        'description': description.strip() if description else '',
                        'content': '',
                        'author': 'Reuters',
                        'topics': [],
                        'scraped_at': datetime.now().isoformat(),
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Reuters: {e}")
    
    def parse_bloomberg(self, response):
        """Parse Bloomberg markets"""
        
        articles = response.css('article')
        
        for article in articles[:30]:
            try:
                title = article.css('a::text').get()
                url = article.css('a::attr(href)').get()
                
                if title and url and 'news' in url:
                    article_data = {
                        'source': 'Bloomberg',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': self._extract_ticker(title),
                        'published_at': '',
                        'description': '',
                        'content': '',
                        'author': 'Bloomberg',
                        'topics': [],
                        'scraped_at': datetime.now().isoformat(),
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Bloomberg: {e}")
    
    def parse_yahoo_finance(self, response):
        """Parse Yahoo Finance news"""
        ticker = response.meta['ticker']
        
        articles = response.css('li.js-stream-content')
        
        for article in articles[:20]:
            try:
                title = article.css('h3 a::text').get()
                url = article.css('h3 a::attr(href)').get()
                description = article.css('p::text').get()
                time = article.css('time::attr(datetime)').get()
                
                if title and url:
                    article_data = {
                        'source': 'Yahoo Finance',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': ticker,
                        'published_at': time or '',
                        'description': description.strip() if description else '',
                        'content': '',
                        'author': 'Yahoo Finance',
                        'topics': [],
                        'scraped_at': datetime.now().isoformat(),
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Yahoo Finance: {e}")
    
    def _extract_ticker(self, text):
        """Extract ticker from text"""
        if not text:
            return ''
        
        text_upper = text.upper()
        for ticker in self.tickers:
            if ticker in text_upper or f'${ticker}' in text_upper:
                return ticker
        return ''
    
    def _parse_finviz_date(self, date_str):
        """Parse Finviz date format"""
        try:
            # Finviz formats: "Today 10:30AM", "Yesterday 3:45PM", "Mar-29-26 08:00AM"
            if 'Today' in date_str:
                return datetime.now()
            elif 'Yesterday' in date_str:
                return datetime.now() - timedelta(days=1)
            else:
                # Try parsing date
                date_part = date_str.split()[0]
                return datetime.strptime(date_part, '%b-%d-%y')
        except:
            return None


def run_historical_spider(tickers=None, start_date=None, end_date=None, 
                         mode='realtime', output_file=None):
    """
    Run the historical spider
    
    Args:
        tickers: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        mode: 'realtime' or 'historical'
        output_file: Output JSON file path
    """
    
    if output_file is None:
        if mode == 'historical':
            output_file = f'data/historical_news_{start_date}_to_{end_date}.json'
        else:
            output_file = 'data/scraped_news.json'
    
    print("\n" + "="*70)
    print(f"[*] STARTING {mode.upper()} NEWS SPIDER")
    print("="*70)
    print(f"Mode: {mode}")
    if mode == 'historical':
        print(f"Date Range: {start_date} to {end_date}")
    print(f"Tickers: {len(tickers) if tickers else 'default'}")
    print(f"Output: {output_file}")
    print("="*70 + "\n")
    
    # Configure spider
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 8 if mode == 'historical' else 16,
        'DOWNLOAD_DELAY': 1.0 if mode == 'historical' else 0.5,
        'FEED_FORMAT': 'json',
        'FEED_URI': output_file,
        'LOG_LEVEL': 'INFO',
    })
    
    # Run spider
    process.crawl(
        HistoricalFinancialNewsSpider, 
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        mode=mode
    )
    process.start()
    
    print("\n" + "="*70)
    print(f"[OK] Scraping complete! Results saved to: {output_file}")
    print("="*70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape financial news')
    parser.add_argument('--mode', choices=['realtime', 'historical'], default='realtime',
                       help='Scraping mode')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--tickers', type=int, default=100,
                       help='Number of tickers to scrape')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Get tickers
    tickers = config.STOCK_TICKERS[:args.tickers]
    
    # Run spider
    run_historical_spider(
        tickers=tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        mode=args.mode,
        output_file=args.output
    )
