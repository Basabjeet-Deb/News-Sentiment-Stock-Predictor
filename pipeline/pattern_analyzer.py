"""
Pattern Analyzer - Extracts patterns from historical data for ML training
Analyzes news-to-price relationships and generates actionable insights
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import os
from collections import defaultdict


class PatternAnalyzer:
    """Analyzes historical patterns for ML feature engineering"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(current_dir), "data")
        else:
            self.data_dir = data_dir
        
        self.patterns = {}
        self.insights = {}
    
    def analyze_historical_patterns(self, historical_df: pd.DataFrame, 
                                   price_df: pd.DataFrame = None) -> Dict:
        """
        Analyze historical news data to find patterns
        
        Args:
            historical_df: DataFrame with historical news
            price_df: Optional DataFrame with historical prices
        
        Returns:
            Dictionary of discovered patterns
        """
        print("\n" + "=" * 70)
        print("PATTERN ANALYSIS")
        print("=" * 70)
        
        patterns = {}
        
        # 1. Sentiment Impact Patterns
        print("\n[1/7] Analyzing sentiment impact patterns...")
        patterns['sentiment_impact'] = self._analyze_sentiment_impact(historical_df)
        
        # 2. Keyword Impact Patterns
        print("[2/7] Analyzing keyword impact patterns...")
        patterns['keyword_impact'] = self._analyze_keyword_impact(historical_df)
        
        # 3. Source Reliability Patterns
        print("[3/7] Analyzing source reliability patterns...")
        patterns['source_reliability'] = self._analyze_source_reliability(historical_df)
        
        # 4. Temporal Patterns
        print("[4/7] Analyzing temporal patterns...")
        patterns['temporal'] = self._analyze_temporal_patterns(historical_df)
        
        # 5. Volume Patterns
        print("[5/7] Analyzing news volume patterns...")
        patterns['volume'] = self._analyze_volume_patterns(historical_df)
        
        # 6. Impact Level Patterns
        print("[6/7] Analyzing impact level patterns...")
        patterns['impact_level'] = self._analyze_impact_patterns(historical_df)
        
        # 7. Ticker-Specific Patterns
        print("[7/7] Analyzing ticker-specific patterns...")
        patterns['ticker_specific'] = self._analyze_ticker_patterns(historical_df)
        
        self.patterns = patterns
        
        print("\n[OK] Pattern analysis complete!")
        return patterns
    
    def _analyze_sentiment_impact(self, df: pd.DataFrame) -> Dict:
        """Analyze how sentiment correlates with outcomes"""
        
        # Group by sentiment ranges
        df['sentiment_range'] = pd.cut(
            df['sentiment_compound'],
            bins=[-1, -0.5, -0.1, 0.1, 0.5, 1],
            labels=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
        )
        
        sentiment_stats = df.groupby('sentiment_range').agg({
            'sentiment_compound': ['count', 'mean'],
            'impact_level': lambda x: (x == 'high').sum()
        }).round(3)
        
        return {
            'distribution': df['sentiment_range'].value_counts().to_dict(),
            'avg_by_range': df.groupby('sentiment_range')['sentiment_compound'].mean().to_dict(),
            'high_impact_by_sentiment': df.groupby('sentiment_range')['impact_level'].apply(
                lambda x: (x == 'high').sum()
            ).to_dict(),
            'insight': self._generate_sentiment_insight(df)
        }
    
    def _analyze_keyword_impact(self, df: pd.DataFrame) -> Dict:
        """Analyze which keywords have highest impact"""
        
        # High-impact keywords
        high_impact_keywords = {
            'earnings': ['earnings', 'revenue', 'profit', 'eps'],
            'regulatory': ['fda', 'sec', 'approval', 'investigation'],
            'corporate': ['merger', 'acquisition', 'ceo', 'layoff'],
            'product': ['launch', 'recall', 'innovation', 'patent'],
            'financial': ['dividend', 'buyback', 'debt', 'bankruptcy']
        }
        
        keyword_patterns = {}
        
        for category, keywords in high_impact_keywords.items():
            matches = df[df['title'].str.lower().str.contains('|'.join(keywords), na=False)]
            
            if len(matches) > 0:
                keyword_patterns[category] = {
                    'count': len(matches),
                    'avg_sentiment': matches['sentiment_compound'].mean(),
                    'high_impact_pct': (matches['impact_level'] == 'high').sum() / len(matches) * 100,
                    'keywords': keywords
                }
        
        return keyword_patterns
    
    def _analyze_source_reliability(self, df: pd.DataFrame) -> Dict:
        """Analyze reliability of different news sources"""
        
        source_stats = df.groupby('source').agg({
            'sentiment_compound': ['count', 'mean', 'std'],
            'impact_level': lambda x: (x == 'high').sum(),
            'relevance_score': 'mean'
        }).round(3)
        
        # Top sources by volume
        top_sources = df['source'].value_counts().head(10).to_dict()
        
        # Sources with high impact articles
        high_impact_sources = df[df['impact_level'] == 'high']['source'].value_counts().head(10).to_dict()
        
        return {
            'top_by_volume': top_sources,
            'top_by_impact': high_impact_sources,
            'avg_relevance_by_source': df.groupby('source')['relevance_score'].mean().to_dict()
        }
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns by time (day of week, time of day)"""
        
        # Convert published_at to datetime
        df['published_dt'] = pd.to_datetime(df['published_at'], errors='coerce')
        df['day_of_week'] = df['published_dt'].dt.day_name()
        df['hour'] = df['published_dt'].dt.hour
        
        # Day of week patterns
        dow_patterns = df.groupby('day_of_week').agg({
            'sentiment_compound': ['count', 'mean'],
            'impact_level': lambda x: (x == 'high').sum()
        }).round(3)
        
        # Hour of day patterns
        hour_patterns = df.groupby('hour').agg({
            'sentiment_compound': ['count', 'mean']
        }).round(3)
        
        return {
            'by_day_of_week': df.groupby('day_of_week')['sentiment_compound'].mean().to_dict(),
            'volume_by_day': df['day_of_week'].value_counts().to_dict(),
            'by_hour': df.groupby('hour')['sentiment_compound'].mean().to_dict(),
            'peak_hours': df['hour'].value_counts().head(5).to_dict()
        }
    
    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns based on news volume"""
        
        # Group by date and ticker
        if 'batch_date' in df.columns:
            daily_volume = df.groupby(['batch_date', 'ticker']).size().reset_index(name='article_count')
            
            # Categorize volume
            daily_volume['volume_category'] = pd.cut(
                daily_volume['article_count'],
                bins=[0, 2, 5, 10, 100],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            
            return {
                'avg_daily_articles': df.groupby('batch_date').size().mean(),
                'max_daily_articles': df.groupby('batch_date').size().max(),
                'volume_distribution': daily_volume['volume_category'].value_counts().to_dict(),
                'high_volume_tickers': df['ticker'].value_counts().head(20).to_dict()
            }
        
        return {
            'total_articles': len(df),
            'unique_tickers': df['ticker'].nunique(),
            'avg_articles_per_ticker': len(df) / df['ticker'].nunique() if df['ticker'].nunique() > 0 else 0
        }
    
    def _analyze_impact_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns by impact level"""
        
        impact_stats = df.groupby('impact_level').agg({
            'sentiment_compound': ['count', 'mean', 'std'],
            'relevance_score': 'mean'
        }).round(3)
        
        return {
            'distribution': df['impact_level'].value_counts().to_dict(),
            'avg_sentiment_by_impact': df.groupby('impact_level')['sentiment_compound'].mean().to_dict(),
            'high_impact_sentiment': df[df['impact_level'] == 'high']['sentiment_compound'].mean()
        }
    
    def _analyze_ticker_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns for specific tickers"""
        
        ticker_stats = df.groupby('ticker').agg({
            'sentiment_compound': ['count', 'mean', 'std'],
            'impact_level': lambda x: (x == 'high').sum()
        }).round(3)
        
        # Top tickers by article count
        top_tickers = df['ticker'].value_counts().head(20).to_dict()
        
        # Tickers with most positive sentiment
        positive_tickers = df.groupby('ticker')['sentiment_compound'].mean().nlargest(10).to_dict()
        
        # Tickers with most negative sentiment
        negative_tickers = df.groupby('ticker')['sentiment_compound'].mean().nsmallest(10).to_dict()
        
        return {
            'top_by_volume': top_tickers,
            'most_positive': positive_tickers,
            'most_negative': negative_tickers,
            'high_impact_tickers': df[df['impact_level'] == 'high']['ticker'].value_counts().head(10).to_dict()
        }
    
    def _generate_sentiment_insight(self, df: pd.DataFrame) -> str:
        """Generate insight from sentiment analysis"""
        
        positive = (df['sentiment_compound'] > 0.05).sum()
        negative = (df['sentiment_compound'] < -0.05).sum()
        total = len(df)
        
        pos_pct = positive / total * 100
        neg_pct = negative / total * 100
        
        if pos_pct > 60:
            return f"Strong bullish sentiment: {pos_pct:.1f}% positive articles"
        elif neg_pct > 60:
            return f"Strong bearish sentiment: {neg_pct:.1f}% negative articles"
        else:
            return f"Mixed sentiment: {pos_pct:.1f}% positive, {neg_pct:.1f}% negative"
    
    def generate_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate ML-ready features from historical data
        
        Returns:
            DataFrame with engineered features
        """
        print("\n" + "=" * 70)
        print("FEATURE ENGINEERING FOR ML")
        print("=" * 70)
        
        df = df.copy()
        
        # 1. Sentiment Features
        print("\n[1/8] Creating sentiment features...")
        df['sentiment_strength'] = df['sentiment_compound'].abs()
        df['is_positive'] = (df['sentiment_compound'] > 0.05).astype(int)
        df['is_negative'] = (df['sentiment_compound'] < -0.05).astype(int)
        df['is_neutral'] = ((df['sentiment_compound'] >= -0.05) & 
                           (df['sentiment_compound'] <= 0.05)).astype(int)
        
        # 2. Impact Features
        print("[2/8] Creating impact features...")
        df['is_high_impact'] = (df['impact_level'] == 'high').astype(int)
        df['is_macro_impact'] = (df['impact_level'] == 'macro').astype(int)
        df['relevance_high'] = (df['relevance_score'] > 0.7).astype(int)
        
        # 3. Keyword Features
        print("[3/8] Creating keyword features...")
        keywords = {
            'has_earnings': ['earnings', 'revenue', 'profit'],
            'has_regulatory': ['fda', 'sec', 'approval'],
            'has_merger': ['merger', 'acquisition'],
            'has_product': ['launch', 'recall', 'innovation'],
            'has_executive': ['ceo', 'cfo', 'executive']
        }
        
        for feature, words in keywords.items():
            df[feature] = df['title'].str.lower().str.contains('|'.join(words), na=False).astype(int)
        
        # 4. Temporal Features
        print("[4/8] Creating temporal features...")
        df['published_dt'] = pd.to_datetime(df['published_at'], errors='coerce')
        df['day_of_week'] = df['published_dt'].dt.dayofweek
        df['hour_of_day'] = df['published_dt'].dt.hour
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_market_hours'] = ((df['hour_of_day'] >= 9) & (df['hour_of_day'] <= 16)).astype(int)
        
        # 5. Source Features
        print("[5/8] Creating source features...")
        top_sources = df['source'].value_counts().head(10).index
        df['is_top_source'] = df['source'].isin(top_sources).astype(int)
        
        # 6. Aggregated Features (by ticker and date)
        print("[6/8] Creating aggregated features...")
        if 'batch_date' in df.columns and 'ticker' in df.columns:
            # Daily ticker aggregations
            daily_agg = df.groupby(['batch_date', 'ticker']).agg({
                'sentiment_compound': ['mean', 'std', 'min', 'max'],
                'is_high_impact': 'sum',
                'relevance_score': 'mean'
            }).reset_index()
            
            daily_agg.columns = ['batch_date', 'ticker', 
                                'daily_avg_sentiment', 'daily_sentiment_std',
                                'daily_min_sentiment', 'daily_max_sentiment',
                                'daily_high_impact_count', 'daily_avg_relevance']
            
            # Merge back
            df = df.merge(daily_agg, on=['batch_date', 'ticker'], how='left')
            
            # Article count per day per ticker
            article_counts = df.groupby(['batch_date', 'ticker']).size().reset_index(name='daily_article_count')
            df = df.merge(article_counts, on=['batch_date', 'ticker'], how='left')
        
        # 7. Sentiment Momentum Features
        print("[7/8] Creating momentum features...")
        df['sentiment_squared'] = df['sentiment_compound'] ** 2
        df['sentiment_momentum'] = df['sentiment_compound'] * df['sentiment_strength']
        
        # 8. Interaction Features
        print("[8/8] Creating interaction features...")
        df['sentiment_x_impact'] = df['sentiment_compound'] * df['is_high_impact']
        df['sentiment_x_relevance'] = df['sentiment_compound'] * df['relevance_score']
        
        print(f"\n[OK] Generated {len(df.columns)} features")
        
        return df
    
    def create_training_dataset(self, df: pd.DataFrame, 
                               price_changes: pd.DataFrame = None) -> pd.DataFrame:
        """
        Create final training dataset with features and labels
        
        Args:
            df: DataFrame with engineered features
            price_changes: Optional DataFrame with actual price changes
        
        Returns:
            Training-ready DataFrame
        """
        print("\n" + "=" * 70)
        print("CREATING TRAINING DATASET")
        print("=" * 70)
        
        # Generate features
        df_features = self.generate_ml_features(df)
        
        # If price changes provided, add labels
        if price_changes is not None:
            print("\n[*] Adding price change labels...")
            df_features = df_features.merge(
                price_changes,
                on=['batch_date', 'ticker'],
                how='left'
            )
            
            # Create binary labels
            df_features['price_up'] = (df_features['price_change_pct'] > 0).astype(int)
            df_features['price_down'] = (df_features['price_change_pct'] < 0).astype(int)
            df_features['significant_move'] = (df_features['price_change_pct'].abs() > 2).astype(int)
        
        print(f"\n[OK] Training dataset created: {len(df_features)} samples, {len(df_features.columns)} features")
        
        return df_features
    
    def save_patterns(self, output_file: str = None):
        """Save discovered patterns to JSON"""
        if output_file is None:
            output_file = os.path.join(self.data_dir, "discovered_patterns.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.patterns, f, indent=2, default=str)
        
        print(f"\n[OK] Patterns saved to {output_file}")
    
    def print_pattern_summary(self):
        """Print summary of discovered patterns"""
        if not self.patterns:
            print("No patterns analyzed yet")
            return
        
        print("\n" + "=" * 70)
        print("PATTERN DISCOVERY SUMMARY")
        print("=" * 70)
        
        # Sentiment Impact
        if 'sentiment_impact' in self.patterns:
            print("\n📊 SENTIMENT IMPACT:")
            print(f"   {self.patterns['sentiment_impact']['insight']}")
        
        # Keyword Impact
        if 'keyword_impact' in self.patterns:
            print("\n🔑 HIGH-IMPACT KEYWORDS:")
            for category, data in list(self.patterns['keyword_impact'].items())[:5]:
                print(f"   {category.upper()}: {data['count']} articles, "
                      f"avg sentiment: {data['avg_sentiment']:.3f}")
        
        # Source Reliability
        if 'source_reliability' in self.patterns:
            print("\n📰 TOP NEWS SOURCES:")
            for source, count in list(self.patterns['source_reliability']['top_by_volume'].items())[:5]:
                print(f"   {source}: {count} articles")
        
        # Volume Patterns
        if 'volume' in self.patterns:
            print("\n📈 VOLUME PATTERNS:")
            print(f"   Avg daily articles: {self.patterns['volume'].get('avg_daily_articles', 0):.0f}")
            print(f"   Max daily articles: {self.patterns['volume'].get('max_daily_articles', 0)}")
        
        # Ticker Patterns
        if 'ticker_specific' in self.patterns:
            print("\n🎯 TOP TICKERS BY COVERAGE:")
            for ticker, count in list(self.patterns['ticker_specific']['top_by_volume'].items())[:10]:
                print(f"   {ticker}: {count} articles")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    # Test pattern analyzer
    analyzer = PatternAnalyzer()
    
    # Load historical data
    try:
        df = pd.read_csv('../data/ml_training_data.csv')
        print(f"Loaded {len(df)} historical articles")
        
        # Analyze patterns
        patterns = analyzer.analyze_historical_patterns(df)
        
        # Print summary
        analyzer.print_pattern_summary()
        
        # Save patterns
        analyzer.save_patterns()
        
        # Generate ML features
        df_ml = analyzer.create_training_dataset(df)
        
        # Save training dataset
        df_ml.to_csv('../data/ml_features_engineered.csv', index=False)
        print(f"\n[OK] ML-ready dataset saved: {len(df_ml)} samples")
        
    except Exception as e:
        print(f"Error: {e}")
