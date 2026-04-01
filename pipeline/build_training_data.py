"""
Build Training Dataset from Historical News and Price Data
Combines historical news sentiment with actual price movements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from sentiment_analyzer import SentimentAnalyzer
from impact_analyzer import ImpactAnalyzer


class TrainingDataBuilder:
    """Build training dataset from historical news and prices"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.impact_analyzer = ImpactAnalyzer()
        
    def load_historical_news(self, news_file):
        """Load historical news from JSON"""
        print(f"\n[*] Loading historical news from {news_file}...")
        
        with open(news_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        print(f"[OK] Loaded {len(articles)} articles")
        return articles
    
    def analyze_historical_news(self, articles):
        """Analyze sentiment and impact for historical news"""
        print(f"\n[*] Analyzing {len(articles)} articles...")
        
        # Analyze sentiment
        articles = self.sentiment_analyzer.analyze_batch(articles)
        
        # Analyze impact
        for article in articles:
            impact = self.impact_analyzer.analyze_news_impact(article)
            article['impact_analysis'] = impact
        
        print(f"[OK] Analysis complete")
        return articles
    
    def fetch_historical_prices(self, tickers, start_date, end_date):
        """Fetch historical prices for tickers"""
        print(f"\n[*] Fetching historical prices for {len(tickers)} tickers...")
        print(f"    Date range: {start_date} to {end_date}")
        
        price_data = {}
        
        for i, ticker in enumerate(tickers, 1):
            try:
                if i % 50 == 0:
                    print(f"    Progress: {i}/{len(tickers)}")
                
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    price_data[ticker] = hist
                    
            except Exception as e:
                print(f"    Error fetching {ticker}: {e}")
        
        print(f"[OK] Fetched prices for {len(price_data)} tickers")
        return price_data
    
    def build_training_dataset(self, articles, price_data, prediction_horizon=1):
        """
        Build training dataset by matching news with price movements
        
        Args:
            articles: List of analyzed articles
            price_data: Dict of {ticker: price_dataframe}
            prediction_horizon: Days ahead to measure price change (default: 1)
        
        Returns:
            DataFrame with training data
        """
        print(f"\n[*] Building training dataset...")
        print(f"    Prediction horizon: {prediction_horizon} day(s)")
        
        training_data = []
        
        for article in articles:
            try:
                ticker = article.get('ticker')
                if not ticker or ticker not in price_data:
                    continue
                
                # Parse article date
                published_at = article.get('published_at', '')
                article_date = self._parse_date(published_at)
                
                if not article_date:
                    continue
                
                # Get price data
                prices = price_data[ticker]
                
                # Find price on article date
                article_date_str = article_date.strftime('%Y-%m-%d')
                
                if article_date_str not in prices.index:
                    # Try next trading day
                    next_dates = prices.index[prices.index > article_date_str]
                    if len(next_dates) == 0:
                        continue
                    article_date_str = next_dates[0]
                
                # Get price before and after
                article_idx = prices.index.get_loc(article_date_str)
                
                if article_idx + prediction_horizon >= len(prices):
                    continue
                
                price_before = prices.iloc[article_idx]['Close']
                price_after = prices.iloc[article_idx + prediction_horizon]['Close']
                
                # Calculate price change
                price_change = ((price_after - price_before) / price_before) * 100
                direction = 1 if price_change > 0 else 0  # Binary: UP or DOWN
                
                # Extract features
                impact = article.get('impact_analysis', {})
                
                training_row = {
                    # Identifiers
                    'ticker': ticker,
                    'date': article_date_str,
                    'title': article.get('title', '')[:100],
                    
                    # Sentiment features
                    'sentiment_compound': article.get('sentiment_compound', 0),
                    'sentiment_positive': article.get('sentiment_positive', 0),
                    'sentiment_negative': article.get('sentiment_negative', 0),
                    'sentiment_neutral': article.get('sentiment_neutral', 0),
                    
                    # Impact features
                    'impact_level': article.get('impact_level', 'low'),
                    'impact_confidence': impact.get('confidence', 0),
                    'num_stocks_affected': len(impact.get('impacted_stocks', [])),
                    'impact_type': impact.get('impact_type', 'unknown'),
                    
                    # Relevance features
                    'relevance_score': article.get('relevance_score', 0),
                    'is_relevant': article.get('is_relevant', False),
                    
                    # Price features
                    'price_before': price_before,
                    'price_after': price_after,
                    'price_change_percent': price_change,
                    'direction': direction,  # Target variable
                    
                    # Source
                    'source': article.get('source', ''),
                }
                
                training_data.append(training_row)
                
            except Exception as e:
                continue
        
        df = pd.DataFrame(training_data)
        
        print(f"[OK] Built training dataset with {len(df)} samples")
        print(f"\n    Distribution:")
        print(f"    UP (1):   {(df['direction'] == 1).sum()} ({(df['direction'] == 1).sum() / len(df) * 100:.1f}%)")
        print(f"    DOWN (0): {(df['direction'] == 0).sum()} ({(df['direction'] == 0).sum() / len(df) * 100:.1f}%)")
        
        return df
    
    def _parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass
        
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%b-%d-%y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def save_training_data(self, df, output_file):
        """Save training dataset"""
        print(f"\n[*] Saving training data to {output_file}...")
        
        df.to_csv(output_file, index=False)
        
        print(f"[OK] Saved {len(df)} training samples")
        
        # Print statistics
        print(f"\n{'='*70}")
        print("TRAINING DATA STATISTICS")
        print("="*70)
        print(f"\nTotal samples: {len(df)}")
        print(f"\nSentiment distribution:")
        print(df['sentiment_compound'].describe())
        print(f"\nPrice change distribution:")
        print(df['price_change_percent'].describe())
        print(f"\nImpact level distribution:")
        print(df['impact_level'].value_counts())
        print(f"\nTop sources:")
        print(df['source'].value_counts().head(10))
        print("="*70)


def run_full_pipeline(start_date, end_date, news_file=None, output_file=None):
    """
    Run full pipeline: scrape historical news → analyze → match with prices → build dataset
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        news_file: Path to historical news JSON (if already scraped)
        output_file: Output CSV file for training data
    """
    
    print("\n" + "="*70)
    print("BUILDING TRAINING DATASET FROM HISTORICAL DATA")
    print("="*70)
    print(f"Date range: {start_date} to {end_date}")
    print("="*70)
    
    builder = TrainingDataBuilder()
    
    # Step 1: Load or scrape historical news
    if news_file and os.path.exists(news_file):
        articles = builder.load_historical_news(news_file)
    else:
        print("\n[!] No historical news file provided")
        print("[!] Run historical spider first:")
        print(f"    python pipeline/historical_news_spider.py --mode historical --start-date {start_date} --end-date {end_date}")
        return
    
    # Step 2: Analyze news
    articles = builder.analyze_historical_news(articles)
    
    # Step 3: Get unique tickers
    tickers = list(set([a.get('ticker') for a in articles if a.get('ticker')]))
    print(f"\n[*] Found {len(tickers)} unique tickers in news")
    
    # Step 4: Fetch historical prices
    price_data = builder.fetch_historical_prices(tickers, start_date, end_date)
    
    # Step 5: Build training dataset
    df = builder.build_training_dataset(articles, price_data, prediction_horizon=1)
    
    # Step 6: Save
    if output_file is None:
        output_file = f'data/training_data_{start_date}_to_{end_date}.csv'
    
    builder.save_training_data(df, output_file)
    
    print(f"\n{'='*70}")
    print("[OK] TRAINING DATASET READY!")
    print(f"[OK] File: {output_file}")
    print("="*70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Build training dataset from historical data')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--news-file', help='Historical news JSON file')
    parser.add_argument('--output', help='Output CSV file')
    
    args = parser.parse_args()
    
    run_full_pipeline(
        start_date=args.start_date,
        end_date=args.end_date,
        news_file=args.news_file,
        output_file=args.output
    )
