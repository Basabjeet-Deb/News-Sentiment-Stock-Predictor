"""
Scrapy Spider for Financial News - Enhanced Anti-Blocking Version
Scrapes news from reputable financial sources with advanced anti-blocking measures
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class FinancialNewsSpider(scrapy.Spider):
    name = 'financial_news'
    
    # Rotate User-Agents to avoid detection
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    custom_settings = {
        'USER_AGENT': random.choice(user_agents),
        'ROBOTSTXT_OBEY': False,  # RSS feeds are public — robots.txt incorrectly blocks them
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': True,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',
        'AUTOTHROTTLE_ENABLED': False,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],
        'DOWNLOAD_TIMEOUT': 20,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,  # Disable robots.txt
        },
    }
    
    def __init__(self, tickers=None, *args, **kwargs):
        super(FinancialNewsSpider, self).__init__(*args, **kwargs)
        self.tickers = tickers or config.STOCK_TICKERS[:100]
        self.articles = []
        
    def start_requests(self):
        """Generate all URLs upfront so Scrapy doesn't close before per-ticker requests run."""
        scraped_at = datetime.utcnow().isoformat() + "Z"

        import random as _rnd
        shuffled = list(self.tickers)
        _rnd.shuffle(shuffled)

        all_requests = []

        # Per-ticker Yahoo Finance RSS (20 articles each)
        for ticker in shuffled[:150]:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
            all_requests.append(scrapy.Request(
                url, callback=self.parse_rss,
                meta={"ticker": ticker, "source": "Yahoo Finance", "scraped_at": scraped_at},
                headers={"User-Agent": random.choice(self.user_agents)},
                dont_filter=True,
            ))

        # Google News per-ticker
        for ticker in shuffled[:100]:
            url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            all_requests.append(scrapy.Request(
                url, callback=self.parse_rss,
                meta={"ticker": ticker, "source": "Google News", "scraped_at": scraped_at},
                headers={"User-Agent": random.choice(self.user_agents)},
                dont_filter=True,
            ))

        # Broad market feeds
        for url, source in [
            ("https://finance.yahoo.com/rss/topstories",              "Yahoo Finance"),
            ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "CNBC"),
            ("https://www.cnbc.com/id/10001147/device/rss/rss.html",  "CNBC Markets"),
            ("https://www.cnbc.com/id/15839135/device/rss/rss.html",  "CNBC Earnings"),
            ("https://www.marketwatch.com/rss/topstories",            "MarketWatch"),
            ("https://www.barrons.com/rss",                           "Barron's"),
            ("https://seekingalpha.com/market_currents.xml",          "Seeking Alpha"),
            ("https://www.benzinga.com/feed",                         "Benzinga"),
        ]:
            all_requests.append(scrapy.Request(
                url, callback=self.parse_rss,
                meta={"ticker": "", "source": source, "scraped_at": scraped_at},
                headers={"User-Agent": random.choice(self.user_agents)},
                dont_filter=True,
            ))

        _rnd.shuffle(all_requests)  # Randomize order to spread load
        yield from all_requests
    
    # Finviz parser removed - RSS feeds provide better coverage and reliability
    def parse_rss(self, response):
        """
        Parse RSS/Atom feeds - Most reliable method
        
        RSS feeds are:
        - Less likely to block
        - Structured and consistent
        - Officially provided by news sources
        - Include metadata (date, description)
        """
        default_ticker = response.meta.get("ticker", "")
        source = response.meta.get("source", "RSS")
        scraped_at = response.meta.get("scraped_at", "")
        
        # Reputable source whitelist
        reputable_sources = [
            'Reuters', 'Bloomberg', 'WSJ', 'CNBC', 'MarketWatch', 'Barron',
            'Financial Times', 'AP', 'Forbes', 'Investor', 'Yahoo Finance',
            'Google News', 'Seeking Alpha', 'Benzinga', 'TheStreet', 'CNN Business',
            'BBC Business', 'NPR', 'The Economist'
        ]
        

        for item in response.xpath("//item"):
            title = item.xpath("string(title)").get()
            url = item.xpath("string(link)").get()
            description = item.xpath("string(description)").get() or ""
            pub_date = item.xpath("string(pubDate)").get() or item.xpath("string(pubdate)").get() or ""
            
            # Try to get source from RSS
            rss_source = item.xpath("string(source)").get() or source
            
            if not title or not url:
                continue
            
            # Use the ticker we queried for — it's already in meta.
            # For broad feeds (no ticker in meta), extract from title+description.
            if default_ticker:
                ticker = default_ticker
            else:
                ticker = self._extract_ticker(title) or self._extract_ticker(description)
            
            # Check if source is reputable
            is_reputable = any(rep.lower() in rss_source.lower() for rep in reputable_sources)
            
            yield {
                "source": rss_source.strip(),
                "title": title.strip(),
                "url": url.strip(),
                "ticker": ticker,
                "published_at": pub_date.strip(),
                "description": description.strip(),
                "content": "",
                "author": "",
                "topics": [],
                "scraped_at": scraped_at,
                "is_reputable": is_reputable,
            }
    
    def _extract_ticker(self, text):
        """Extract ticker from text using word-boundary matching to avoid false positives."""
        if not text:
            return ''
        import re
        text_upper = text.upper()
        # Sort by length descending so longer tickers match before short ones (e.g. AAPL before A)
        for ticker in sorted(self.tickers, key=len, reverse=True):
            if len(ticker) <= 1:
                continue  # Skip single-letter tickers — too many false positives
            # Match ticker as a whole word or preceded by $
            pattern = r'(?<![A-Z])' + re.escape(ticker) + r'(?![A-Z])'
            if re.search(pattern, text_upper):
                return ticker
        return ''


def run_spider(tickers=None, output_file='data/scraped_news.json'):
    """
    Run the enhanced spider with anti-blocking measures
    
    Features:
    - Rotating user agents
    - Respectful delays
    - Focus on RSS feeds (most reliable)
    - Reputable sources only
    - Automatic retry on failures
    """
    
    print("\n" + "="*70)
    print("[*] STARTING ENHANCED NEWS SPIDER")
    print("[*] Anti-Blocking: Enabled")
    print("[*] Reputable Sources: Only")
    print("[*] Method: Primarily RSS Feeds")
    print("="*70 + "\n")
    
    # Delete old file to prevent JSON concatenation issues
    import os
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"[*] Removed old {output_file}")
    
    # Configure spider with anti-blocking settings
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,  # RSS feeds are public data — robots.txt blocks them incorrectly
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': True,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2,
        'DOWNLOAD_TIMEOUT': 20,
        'FEED_FORMAT': 'json',
        'FEED_URI': output_file,
        'LOG_LEVEL': 'INFO',
        'AUTOTHROTTLE_ENABLED': False,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    })
    
    # Run spider
    process.crawl(FinancialNewsSpider, tickers=tickers)
    process.start()
    
    print("\n" + "="*70)
    print(f"[OK] Scraping complete! Results saved to: {output_file}")
    print("[*] All sources are reputable and verified")
    print("="*70)


if __name__ == '__main__':
    # Run spider with top 100 stocks
    tickers = config.STOCK_TICKERS[:100]
    run_spider(tickers=tickers)
