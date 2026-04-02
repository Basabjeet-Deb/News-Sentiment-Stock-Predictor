"""
Data Validator - Ensures data quality before saving
"""
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime


class DataValidator:
    """Validates data quality for news, prices, and predictions"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_news_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate news data quality
        
        Returns:
            (is_valid, error_messages)
        """
        self.errors = []
        self.warnings = []
        
        # Check required columns
        required_cols = ['title', 'source', 'ticker', 'sentiment_compound', 'sentiment_label']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for empty dataframe
        if len(df) == 0:
            self.errors.append("News dataframe is empty")
            return False, self.errors
        
        # Check sentiment scores
        if 'sentiment_compound' in df.columns:
            # Check if all sentiment scores are 0 (not analyzed)
            if df['sentiment_compound'].sum() == 0 and len(df) > 10:
                self.errors.append("All sentiment scores are 0 - sentiment analysis not run")
            
            # Check for invalid sentiment range
            invalid_sentiment = df[(df['sentiment_compound'] < -1) | (df['sentiment_compound'] > 1)]
            if len(invalid_sentiment) > 0:
                self.errors.append(f"{len(invalid_sentiment)} articles have invalid sentiment scores (must be -1 to 1)")
        
        # Check for missing titles
        if 'title' in df.columns:
            missing_titles = df[df['title'].isna() | (df['title'] == '')]
            if len(missing_titles) > 0:
                self.warnings.append(f"{len(missing_titles)} articles have missing titles")
        
        # Check for missing tickers
        if 'ticker' in df.columns:
            missing_tickers = df[df['ticker'].isna() | (df['ticker'] == '')]
            if len(missing_tickers) > len(df) * 0.5:  # More than 50% missing
                self.warnings.append(f"{len(missing_tickers)} articles have missing tickers (>50%)")
        
        # Check for duplicates
        if 'title' in df.columns:
            duplicates = df[df.duplicated(subset=['title'], keep=False)]
            if len(duplicates) > 0:
                self.warnings.append(f"{len(duplicates)} duplicate articles found")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors + self.warnings
    
    def validate_price_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate stock price data quality
        
        Returns:
            (is_valid, error_messages)
        """
        self.errors = []
        self.warnings = []
        
        # Check required columns
        required_cols = ['ticker', 'current_price', 'price_change_percent']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for empty dataframe
        if len(df) == 0:
            self.errors.append("Price dataframe is empty")
            return False, self.errors
        
        # Check for invalid prices
        if 'current_price' in df.columns:
            invalid_prices = df[(df['current_price'] <= 0) | (df['current_price'] > 100000)]
            if len(invalid_prices) > 0:
                self.warnings.append(f"{len(invalid_prices)} stocks have suspicious prices")
        
        # Check for missing prices
        if 'current_price' in df.columns:
            missing_prices = df[df['current_price'].isna()]
            if len(missing_prices) > 0:
                self.warnings.append(f"{len(missing_prices)} stocks have missing prices")
        
        # Check for extreme price changes
        if 'price_change_percent' in df.columns:
            extreme_changes = df[(df['price_change_percent'] < -50) | (df['price_change_percent'] > 50)]
            if len(extreme_changes) > 0:
                self.warnings.append(f"{len(extreme_changes)} stocks have extreme price changes (>50%)")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors + self.warnings
    
    def validate_prediction_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate prediction data quality
        
        Returns:
            (is_valid, error_messages)
        """
        self.errors = []
        self.warnings = []
        
        # Check required columns
        required_cols = ['ticker', 'recommendation', 'prediction_score', 'confidence']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for empty dataframe
        if len(df) == 0:
            self.errors.append("Prediction dataframe is empty")
            return False, self.errors
        
        # Check recommendation values
        if 'recommendation' in df.columns:
            valid_recommendations = ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL']
            invalid_recs = df[~df['recommendation'].isin(valid_recommendations)]
            if len(invalid_recs) > 0:
                self.errors.append(f"{len(invalid_recs)} predictions have invalid recommendations")
        
        # Check confidence scores
        if 'confidence' in df.columns:
            invalid_confidence = df[(df['confidence'] < 0) | (df['confidence'] > 1)]
            if len(invalid_confidence) > 0:
                self.errors.append(f"{len(invalid_confidence)} predictions have invalid confidence scores (must be 0-1)")
        
        # Check prediction scores
        if 'prediction_score' in df.columns:
            invalid_scores = df[(df['prediction_score'] < -1) | (df['prediction_score'] > 1)]
            if len(invalid_scores) > 0:
                self.errors.append(f"{len(invalid_scores)} predictions have invalid scores (must be -1 to 1)")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors + self.warnings
    
    def generate_quality_report(self, news_df: pd.DataFrame, price_df: pd.DataFrame, 
                               pred_df: pd.DataFrame) -> Dict:
        """Generate comprehensive data quality report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'news': {
                'total_articles': len(news_df),
                'valid': False,
                'issues': []
            },
            'prices': {
                'total_stocks': len(price_df),
                'valid': False,
                'issues': []
            },
            'predictions': {
                'total_predictions': len(pred_df),
                'valid': False,
                'issues': []
            },
            'overall_valid': False
        }
        
        # Validate each dataset
        news_valid, news_issues = self.validate_news_data(news_df)
        price_valid, price_issues = self.validate_price_data(price_df)
        pred_valid, pred_issues = self.validate_prediction_data(pred_df)
        
        report['news']['valid'] = news_valid
        report['news']['issues'] = news_issues
        report['prices']['valid'] = price_valid
        report['prices']['issues'] = price_issues
        report['predictions']['valid'] = pred_valid
        report['predictions']['issues'] = pred_issues
        report['overall_valid'] = news_valid and price_valid and pred_valid
        
        return report
    
    def print_report(self, report: Dict):
        """Print quality report in readable format"""
        print("\n" + "=" * 70)
        print("DATA QUALITY REPORT")
        print("=" * 70)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {'✅ VALID' if report['overall_valid'] else '❌ INVALID'}")
        
        print(f"\n📰 News Data: {report['news']['total_articles']} articles")
        print(f"   Status: {'✅ Valid' if report['news']['valid'] else '❌ Invalid'}")
        if report['news']['issues']:
            for issue in report['news']['issues']:
                print(f"   - {issue}")
        
        print(f"\n💰 Price Data: {report['prices']['total_stocks']} stocks")
        print(f"   Status: {'✅ Valid' if report['prices']['valid'] else '❌ Invalid'}")
        if report['prices']['issues']:
            for issue in report['prices']['issues']:
                print(f"   - {issue}")
        
        print(f"\n🎯 Prediction Data: {report['predictions']['total_predictions']} predictions")
        print(f"   Status: {'✅ Valid' if report['predictions']['valid'] else '❌ Invalid'}")
        if report['predictions']['issues']:
            for issue in report['predictions']['issues']:
                print(f"   - {issue}")
        
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test validator
    validator = DataValidator()
    
    # Load data
    try:
        news_df = pd.read_csv('../data/news_analyzed.csv')
        price_df = pd.read_csv('../data/stock_prices.csv')
        pred_df = pd.read_csv('../data/predictions.csv')
        
        # Generate report
        report = validator.generate_quality_report(news_df, price_df, pred_df)
        validator.print_report(report)
        
    except Exception as e:
        print(f"Error: {e}")
