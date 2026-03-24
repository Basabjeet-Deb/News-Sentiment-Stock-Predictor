"""
Step 2: News Processing & Sentiment Analysis
- Classify news relevance to stock market
- Extract company/stock mentions
- Perform sentiment analysis
- Tag news with affected stocks
"""

import pandas as pd
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os


class NewsProcessor:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Stock ticker to company name mapping (expanded to 50 stocks)
        self.stock_mapping = {
            # Tech Giants
            'AAPL': ['Apple', 'iPhone', 'iPad', 'Mac', 'iOS', 'Tim Cook'],
            'MSFT': ['Microsoft', 'Windows', 'Azure', 'Office', 'Xbox', 'Satya Nadella'],
            'GOOGL': ['Google', 'Alphabet', 'YouTube', 'Android', 'Chrome', 'Sundar Pichai'],
            'AMZN': ['Amazon', 'AWS', 'Alexa', 'Prime', 'Jeff Bezos', 'Andy Jassy'],
            'TSLA': ['Tesla', 'Elon Musk', 'electric vehicle', 'EV', 'Model'],
            'META': ['Meta', 'Facebook', 'Instagram', 'WhatsApp', 'Zuckerberg'],
            'NVDA': ['NVIDIA', 'GPU', 'graphics card', 'AI chip', 'Jensen Huang'],
            'AMD': ['AMD', 'Ryzen', 'Radeon', 'Lisa Su'],
            'INTC': ['Intel', 'processor', 'chip maker'],
            'ORCL': ['Oracle', 'database', 'Larry Ellison'],
            'NFLX': ['Netflix', 'streaming'],
            'DIS': ['Disney', 'Marvel', 'Star Wars', 'theme park'],
            
            # Finance
            'JPM': ['JPMorgan', 'JP Morgan', 'Chase', 'Jamie Dimon'],
            'BAC': ['Bank of America', 'BofA'],
            'WFC': ['Wells Fargo'],
            'GS': ['Goldman Sachs', 'Goldman'],
            'MS': ['Morgan Stanley'],
            'C': ['Citigroup', 'Citi'],
            'BLK': ['BlackRock'],
            'SCHW': ['Charles Schwab', 'Schwab'],
            'AXP': ['American Express', 'Amex'],
            'V': ['Visa'],
            
            # Healthcare
            'JNJ': ['Johnson & Johnson', 'J&J'],
            'UNH': ['UnitedHealth', 'United Health'],
            'PFE': ['Pfizer'],
            'ABBV': ['AbbVie'],
            'TMO': ['Thermo Fisher'],
            'MRK': ['Merck'],
            'ABT': ['Abbott'],
            'DHR': ['Danaher'],
            'BMY': ['Bristol Myers', 'Bristol-Myers'],
            'LLY': ['Eli Lilly', 'Lilly'],
            
            # Consumer
            'WMT': ['Walmart', 'Wal-Mart'],
            'HD': ['Home Depot'],
            'MCD': ['McDonald', 'McDonalds'],
            'NKE': ['Nike'],
            'SBUX': ['Starbucks'],
            'TGT': ['Target'],
            'COST': ['Costco'],
            'LOW': ['Lowes', "Lowe's"],
            
            # Energy
            'XOM': ['Exxon', 'ExxonMobil'],
            'CVX': ['Chevron'],
            'COP': ['ConocoPhillips'],
            'SLB': ['Schlumberger'],
            'EOG': ['EOG Resources'],
            
            # Industrial
            'BA': ['Boeing'],
            'CAT': ['Caterpillar'],
            'GE': ['General Electric', 'GE'],
            'MMM': ['3M'],
            'HON': ['Honeywell']
        }
        
        # Market-relevant keywords
        self.market_keywords = [
            'stock', 'market', 'shares', 'trading', 'investor', 'wall street',
            'earnings', 'revenue', 'profit', 'loss', 'quarter', 'fiscal',
            'merger', 'acquisition', 'IPO', 'dividend', 'buyback',
            'CEO', 'CFO', 'executive', 'board', 'shareholder',
            'economy', 'GDP', 'inflation', 'interest rate', 'federal reserve',
            'recession', 'growth', 'unemployment', 'consumer spending',
            'tariff', 'trade war', 'regulation', 'antitrust',
            'bankruptcy', 'layoff', 'hiring', 'expansion'
        ]
    
    def load_news(self, filepath='data/gdelt_english_news.csv'):
        """Load news data from CSV"""
        try:
            df = pd.read_csv(filepath)
            print(f"[OK] Loaded {len(df)} news articles")
            return df
        except Exception as e:
            print(f"[ERROR] Failed to load news: {e}")
            return None
    
    def classify_market_relevance(self, text):
        """
        Classify if news is relevant to stock market
        Returns: (is_relevant, relevance_score, matched_keywords)
        """
        if pd.isna(text):
            return False, 0.0, []
        
        text_lower = text.lower()
        matched = []
        
        for keyword in self.market_keywords:
            if keyword in text_lower:
                matched.append(keyword)
        
        relevance_score = len(matched) / len(self.market_keywords)
        is_relevant = len(matched) >= 2  # At least 2 keywords
        
        return is_relevant, relevance_score, matched
    
    def extract_stock_mentions(self, text):
        """
        Extract mentioned stocks/companies from text
        Returns: list of stock tickers
        """
        if pd.isna(text):
            return []
        
        text_lower = text.lower()
        mentioned_stocks = []
        
        for ticker, keywords in self.stock_mapping.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    mentioned_stocks.append(ticker)
                    break
        
        return list(set(mentioned_stocks))  # Remove duplicates
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of text using VADER
        Returns: (compound_score, sentiment_label)
        """
        if pd.isna(text):
            return 0.0, 'neutral'
        
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        
        # Classify sentiment
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return compound, label
    
    def determine_market_impact(self, sentiment_score, relevance_score, num_stocks):
        """
        Determine potential market impact
        Returns: impact_level (high/medium/low)
        """
        # Calculate impact score
        impact_score = abs(sentiment_score) * relevance_score * (1 + num_stocks * 0.1)
        
        if impact_score >= 0.3:
            return 'high'
        elif impact_score >= 0.15:
            return 'medium'
        else:
            return 'low'
    
    def process_all_news(self, df):
        """Process all news articles"""
        print("\n" + "="*60)
        print("PROCESSING NEWS ARTICLES")
        print("="*60)
        
        results = []
        
        for idx, row in df.iterrows():
            title = row.get('title', '')
            
            # Classify market relevance
            is_relevant, relevance_score, keywords = self.classify_market_relevance(title)
            
            # Extract stock mentions
            stocks = self.extract_stock_mentions(title)
            
            # Analyze sentiment
            sentiment_score, sentiment_label = self.analyze_sentiment(title)
            
            # Determine impact
            impact = self.determine_market_impact(sentiment_score, relevance_score, len(stocks))
            
            results.append({
                'title': title,
                'url': row.get('url', ''),
                'domain': row.get('domain', ''),
                'seendate': row.get('seendate', ''),
                'category': row.get('category', ''),
                'is_market_relevant': is_relevant,
                'relevance_score': round(relevance_score, 3),
                'matched_keywords': ', '.join(keywords[:5]),  # Top 5
                'mentioned_stocks': ', '.join(stocks),
                'num_stocks': len(stocks),
                'sentiment_score': round(sentiment_score, 4),
                'sentiment_label': sentiment_label,
                'market_impact': impact
            })
            
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1}/{len(df)} articles...")
        
        print(f"[OK] Processed all {len(df)} articles")
        
        return pd.DataFrame(results)
    
    def save_processed_data(self, df, filename='processed_news.csv'):
        """Save processed news data"""
        filepath = os.path.join('data', filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"[OK] Saved processed data to {filepath}")
        return filepath
    
    def generate_summary(self, df):
        """Generate summary statistics"""
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        
        total = len(df)
        relevant = df['is_market_relevant'].sum()
        
        print(f"\nTotal articles: {total}")
        print(f"Market-relevant: {relevant} ({relevant/total*100:.1f}%)")
        print(f"Not relevant: {total - relevant} ({(total-relevant)/total*100:.1f}%)")
        
        print(f"\nSentiment Distribution:")
        sentiment_counts = df['sentiment_label'].value_counts()
        for label, count in sentiment_counts.items():
            print(f"  {label.capitalize()}: {count} ({count/total*100:.1f}%)")
        
        print(f"\nMarket Impact:")
        impact_counts = df['market_impact'].value_counts()
        for level, count in impact_counts.items():
            print(f"  {level.capitalize()}: {count} ({count/total*100:.1f}%)")
        
        print(f"\nMost Mentioned Stocks:")
        all_stocks = []
        for stocks in df['mentioned_stocks']:
            if pd.notna(stocks) and stocks:
                all_stocks.extend(stocks.split(', '))
        
        if all_stocks:
            stock_counts = pd.Series(all_stocks).value_counts().head(10)
            for stock, count in stock_counts.items():
                print(f"  {stock}: {count} mentions")
        else:
            print("  No stock mentions found")
        
        print(f"\nTop Categories:")
        category_counts = df['category'].value_counts().head(5)
        for cat, count in category_counts.items():
            print(f"  {cat}: {count} articles")
        
        # High impact news
        high_impact = df[df['market_impact'] == 'high']
        if len(high_impact) > 0:
            print(f"\n" + "="*60)
            print(f"HIGH IMPACT NEWS ({len(high_impact)} articles)")
            print("="*60)
            for idx, row in high_impact.head(5).iterrows():
                print(f"\n[{row['sentiment_label'].upper()}] {row['title'][:80]}...")
                print(f"  Stocks: {row['mentioned_stocks']}")
                print(f"  Sentiment: {row['sentiment_score']:.3f}")


def main():
    processor = NewsProcessor()
    
    print("="*60)
    print("STEP 2: NEWS PROCESSING & SENTIMENT ANALYSIS")
    print("="*60)
    
    # Load news data
    df = processor.load_news()
    
    if df is None or len(df) == 0:
        print("[ERROR] No news data to process")
        return
    
    # Process all news
    processed_df = processor.process_all_news(df)
    
    # Save processed data
    processor.save_processed_data(processed_df)
    
    # Generate summary
    processor.generate_summary(processed_df)
    
    print("\n" + "="*60)
    print("STEP 2 COMPLETE!")
    print("="*60)
    print("\nNext Step: Data Correlation")
    print("Match news sentiment with stock price movements")


if __name__ == "__main__":
    main()
