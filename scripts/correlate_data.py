"""
Step 3: Data Correlation
- Match news timestamps with stock price movements
- Calculate sentiment scores per company/stock
- Aggregate daily/hourly sentiment trends
- Identify correlation between sentiment and price changes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


class DataCorrelator:
    def __init__(self):
        self.news_df = None
        self.stock_df = None
        self.correlated_df = None
    
    def load_data(self):
        """Load processed news and stock price data"""
        print("="*60)
        print("LOADING DATA")
        print("="*60)
        
        # Load processed news
        try:
            self.news_df = pd.read_csv('data/processed_news.csv')
            print(f"[OK] Loaded {len(self.news_df)} processed news articles")
        except Exception as e:
            print(f"[ERROR] Failed to load news: {e}")
            return False
        
        # Load stock prices
        try:
            self.stock_df = pd.read_csv('data/stock_prices.csv')
            print(f"[OK] Loaded {len(self.stock_df)} stock price records")
        except Exception as e:
            print(f"[ERROR] Failed to load stock prices: {e}")
            return False
        
        return True
    
    def prepare_news_data(self):
        """Prepare news data for correlation"""
        print("\n" + "="*60)
        print("PREPARING NEWS DATA")
        print("="*60)
        
        # Parse dates (format: 20260308T111500Z)
        self.news_df['date'] = pd.to_datetime(self.news_df['seendate'], format='%Y%m%dT%H%M%SZ', errors='coerce')
        self.news_df['date_only'] = self.news_df['date'].dt.date
        
        print(f"Date range: {self.news_df['date_only'].min()} to {self.news_df['date_only'].max()}")
        
        # Filter news with stock mentions (regardless of market relevance)
        news_with_stocks = self.news_df[self.news_df['mentioned_stocks'].notna()].copy()
        print(f"[OK] Found {len(news_with_stocks)} news articles with stock mentions")
        
        # Expand news by mentioned stocks
        expanded_rows = []
        for idx, row in news_with_stocks.iterrows():
            stocks = row['mentioned_stocks']
            if pd.notna(stocks) and stocks:
                stock_list = stocks.split(', ')
                for stock in stock_list:
                    new_row = row.copy()
                    new_row['stock_ticker'] = stock
                    expanded_rows.append(new_row)
        
        if expanded_rows:
            self.news_df = pd.DataFrame(expanded_rows)
            print(f"[OK] Expanded to {len(self.news_df)} news-stock pairs")
        else:
            print("[WARN] No stock mentions found")
            self.news_df = pd.DataFrame()
        
        return len(self.news_df) > 0
    
    def prepare_stock_data(self):
        """Prepare stock price data"""
        print("\n" + "="*60)
        print("PREPARING STOCK DATA")
        print("="*60)
        
        # Parse dates with UTC timezone handling
        self.stock_df['Date'] = pd.to_datetime(self.stock_df['Date'], utc=True)
        self.stock_df['date_only'] = self.stock_df['Date'].dt.date
        
        # Calculate daily price change
        self.stock_df['price_change'] = self.stock_df.groupby('Ticker')['Close'].pct_change() * 100
        
        # Calculate next day price change (for prediction)
        self.stock_df['next_day_change'] = self.stock_df.groupby('Ticker')['price_change'].shift(-1)
        
        print(f"[OK] Prepared {len(self.stock_df)} stock records")
        print(f"Date range: {self.stock_df['date_only'].min()} to {self.stock_df['date_only'].max()}")
        
        return True
    
    def aggregate_daily_sentiment(self):
        """Aggregate sentiment scores by stock and date"""
        print("\n" + "="*60)
        print("AGGREGATING DAILY SENTIMENT")
        print("="*60)
        
        if len(self.news_df) == 0:
            print("[WARN] No news data to aggregate")
            return pd.DataFrame()
        
        # Group by stock and date
        daily_sentiment = self.news_df.groupby(['stock_ticker', 'date_only']).agg({
            'sentiment_score': ['mean', 'std', 'count'],
            'relevance_score': 'mean'
        }).reset_index()
        
        # Flatten column names
        daily_sentiment.columns = ['ticker', 'date', 'avg_sentiment', 'sentiment_std', 'news_count', 'avg_relevance']
        
        # Fill NaN std with 0
        daily_sentiment = daily_sentiment.copy()
        daily_sentiment.loc[:, 'sentiment_std'] = daily_sentiment['sentiment_std'].fillna(0)
        
        print(f"[OK] Aggregated sentiment for {len(daily_sentiment)} stock-date combinations")
        
        return daily_sentiment
    
    def correlate_sentiment_with_prices(self, daily_sentiment):
        """Correlate sentiment with stock price movements"""
        print("\n" + "="*60)
        print("CORRELATING SENTIMENT WITH PRICES")
        print("="*60)
        
        if len(daily_sentiment) == 0:
            print("[WARN] No sentiment data to correlate")
            return pd.DataFrame()
        
        # Merge sentiment with stock prices
        merged = pd.merge(
            daily_sentiment,
            self.stock_df[['Ticker', 'date_only', 'Close', 'price_change', 'next_day_change', 'Volume']],
            left_on=['ticker', 'date'],
            right_on=['Ticker', 'date_only'],
            how='inner'
        )
        
        print(f"[OK] Matched {len(merged)} sentiment-price pairs")
        
        if len(merged) == 0:
            print("[WARN] No matching dates between news and stock data")
            return merged
        
        # Calculate correlation metrics
        merged['sentiment_price_alignment'] = np.sign(merged['avg_sentiment']) == np.sign(merged['next_day_change'])
        
        self.correlated_df = merged
        
        return merged
    
    def calculate_correlations(self):
        """Calculate correlation statistics"""
        print("\n" + "="*60)
        print("CORRELATION ANALYSIS")
        print("="*60)
        
        if self.correlated_df is None or len(self.correlated_df) == 0:
            print("[WARN] No correlated data available")
            return
        
        df = self.correlated_df
        
        # Overall correlation
        overall_corr = df['avg_sentiment'].corr(df['next_day_change'])
        print(f"\nOverall Sentiment-Price Correlation: {overall_corr:.4f}")
        
        # Correlation by stock
        print("\nCorrelation by Stock:")
        for ticker in df['ticker'].unique():
            stock_data = df[df['ticker'] == ticker]
            if len(stock_data) > 1:
                corr = stock_data['avg_sentiment'].corr(stock_data['next_day_change'])
                print(f"  {ticker}: {corr:.4f} ({len(stock_data)} data points)")
        
        # Prediction accuracy
        accuracy = df['sentiment_price_alignment'].mean() * 100
        print(f"\nSentiment-Price Direction Alignment: {accuracy:.1f}%")
        
        # Strong sentiment impact
        strong_positive = df[df['avg_sentiment'] > 0.3]
        strong_negative = df[df['avg_sentiment'] < -0.3]
        
        if len(strong_positive) > 0:
            avg_change_pos = strong_positive['next_day_change'].mean()
            print(f"\nStrong Positive Sentiment ({len(strong_positive)} cases):")
            print(f"  Average next-day price change: {avg_change_pos:.2f}%")
        
        if len(strong_negative) > 0:
            avg_change_neg = strong_negative['next_day_change'].mean()
            print(f"\nStrong Negative Sentiment ({len(strong_negative)} cases):")
            print(f"  Average next-day price change: {avg_change_neg:.2f}%")
    
    def save_correlated_data(self):
        """Save correlated data"""
        if self.correlated_df is not None and len(self.correlated_df) > 0:
            filepath = 'data/correlated_data.csv'
            self.correlated_df.to_csv(filepath, index=False)
            print(f"\n[OK] Saved correlated data to {filepath}")
            return filepath
        return None
    
    def generate_insights(self):
        """Generate actionable insights"""
        print("\n" + "="*60)
        print("KEY INSIGHTS")
        print("="*60)
        
        if self.correlated_df is None or len(self.correlated_df) == 0:
            print("\n[WARN] Insufficient data for insights")
            print("\nRecommendations:")
            print("1. Fetch more financial news (run fetch_news.py again)")
            print("2. Use longer time period for stock data")
            print("3. Focus on company-specific news")
            return
        
        df = self.correlated_df
        
        # Most impactful news
        print("\nMost Impactful News Events:")
        df['impact_score'] = abs(df['avg_sentiment']) * abs(df['next_day_change'])
        top_impact = df.nlargest(5, 'impact_score')
        
        for idx, row in top_impact.iterrows():
            print(f"\n{row['ticker']} on {row['date']}:")
            print(f"  Sentiment: {row['avg_sentiment']:.3f}")
            print(f"  Price Change: {row['next_day_change']:.2f}%")
            print(f"  News Count: {int(row['news_count'])}")
        
        # Best performing stocks
        print("\n" + "="*60)
        print("Stock Performance Summary:")
        stock_summary = df.groupby('ticker').agg({
            'next_day_change': 'mean',
            'avg_sentiment': 'mean',
            'news_count': 'sum'
        }).round(3)
        print(stock_summary)


def main():
    correlator = DataCorrelator()
    
    print("="*60)
    print("STEP 3: DATA CORRELATION")
    print("="*60)
    
    # Load data
    if not correlator.load_data():
        print("[ERROR] Failed to load data")
        return
    
    # Prepare data
    if not correlator.prepare_news_data():
        print("[WARN] No relevant news with stock mentions")
    
    correlator.prepare_stock_data()
    
    # Aggregate sentiment
    daily_sentiment = correlator.aggregate_daily_sentiment()
    
    # Correlate with prices
    correlated = correlator.correlate_sentiment_with_prices(daily_sentiment)
    
    if len(correlated) > 0:
        # Calculate correlations
        correlator.calculate_correlations()
        
        # Save results
        correlator.save_correlated_data()
        
        # Generate insights
        correlator.generate_insights()
    else:
        print("\n[WARN] No correlation data available")
        print("\nPossible reasons:")
        print("1. News dates don't match stock trading dates")
        print("2. No stock mentions in market-relevant news")
        print("3. Need more recent news data")
    
    print("\n" + "="*60)
    print("STEP 3 COMPLETE!")
    print("="*60)
    print("\nNext Step: Feature Engineering")
    print("Create features for machine learning model")


if __name__ == "__main__":
    main()
