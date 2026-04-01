"""
Scrapy Spider for Financial News
Scrapes news from multiple financial websites
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class FinancialNewsSpider(scrapy.Spider):
    name = 'financial_news'
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, tickers=None, *args, **kwargs):
        super(FinancialNewsSpider, self).__init__(*args, **kwargs)
        self.tickers = tickers or config.STOCK_TICKERS[:100]
        self.articles = []
        
    def start_requests(self):
        """Generate URLs to scrape"""
        
        # 1. Finviz - Stock-specific news
        for ticker in self.tickers[:50]:  # Top 50 stocks
            url = f'https://finviz.com/quote.ashx?t={ticker}'
            yield scrapy.Request(url, callback=self.parse_finviz, meta={'ticker': ticker})
        
        # 2. MarketWatch - Latest news
        yield scrapy.Request('https://www.marketwatch.com/latest-news', callback=self.parse_marketwatch)
        
        # 3. Seeking Alpha - Market news
        yield scrapy.Request('https://seekingalpha.com/market-news', callback=self.parse_seeking_alpha)
        
        # 4. Investing.com - Stock news
        for ticker in self.tickers[:30]:
            # Note: Investing.com URLs vary, this is a simplified example
            yield scrapy.Request(f'https://www.investing.com/search/?q={ticker}', 
                               callback=self.parse_investing, 
                               meta={'ticker': ticker})
        
        # 5. Reuters - Business news
        yield scrapy.Request('https://www.reuters.com/business/', callback=self.parse_reuters)
        
        # 6. Bloomberg - Markets
        yield scrapy.Request('https://www.bloomberg.com/markets', callback=self.parse_bloomberg)
    
    def parse_finviz(self, response):
        """Parse Finviz news table"""
        ticker = response.meta['ticker']
        
        # Finviz news table
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
                        }
                        self.articles.append(article)
                        yield article
            except Exception as e:
                self.logger.error(f"Error parsing Finviz row: {e}")
    
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
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing MarketWatch article: {e}")
    
    def parse_seeking_alpha(self, response):
        """Parse Seeking Alpha market news"""
        
        articles = response.css('article')
        
        for article in articles[:20]:  # Limit to 20 articles
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
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Seeking Alpha article: {e}")
    
    def parse_investing(self, response):
        """Parse Investing.com search results"""
        ticker = response.meta['ticker']
        
        # This is simplified - Investing.com structure varies
        articles = response.css('article.js-article-item')
        
        for article in articles[:5]:  # Limit per ticker
            try:
                title = article.css('a.title::text').get()
                url = article.css('a.title::attr(href)').get()
                
                if title and url:
                    article_data = {
                        'source': 'Investing.com',
                        'title': title.strip(),
                        'url': response.urljoin(url),
                        'ticker': ticker,
                        'published_at': '',
                        'description': '',
                        'content': '',
                        'author': 'Investing.com',
                        'topics': [],
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Investing.com article: {e}")
    
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
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Reuters article: {e}")
    
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
                    }
                    self.articles.append(article_data)
                    yield article_data
            except Exception as e:
                self.logger.error(f"Error parsing Bloomberg article: {e}")
    
    def _extract_ticker(self, text):
        """Extract ticker from text"""
        if not text:
            return ''
        
        text_upper = text.upper()
        for ticker in self.tickers:
            if ticker in text_upper or f'${ticker}' in text_upper:
                return ticker
        return ''


def run_spider(tickers=None, output_file='data/scraped_news.json'):
    """Run the spider and save results"""
    
    print("\n" + "="*70)
    print("[*] STARTING SCRAPY NEWS SPIDER")
    print("="*70 + "\n")
    
    # Delete old file to prevent JSON concatenation issues
    import os
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"[*] Removed old {output_file}")
    
    # Configure spider
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        'FEED_FORMAT': 'json',
        'FEED_URI': output_file,
        'LOG_LEVEL': 'INFO',
    })
    
    # Run spider
    process.crawl(FinancialNewsSpider, tickers=tickers)
    process.start()
    
    print("\n" + "="*70)
    print(f"[OK] Scraping complete! Results saved to: {output_file}")
    print("="*70)


if __name__ == '__main__':
    # Run spider with top 100 stocks
    tickers = config.STOCK_TICKERS[:100]
    run_spider(tickers=tickers)
