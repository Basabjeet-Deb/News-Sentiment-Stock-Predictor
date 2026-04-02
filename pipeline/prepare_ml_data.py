"""
ML Data Preparation Pipeline
Fetches historical data, analyzes patterns, and creates ML-ready dataset
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.historical_data_manager import HistoricalDataManager
from pipeline.pattern_analyzer import PatternAnalyzer
from pipeline.price_fetcher import StockPriceFetcher
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict
import config


class MLDataPreparation:
    """Prepares historical data for ML training"""
    
    def __init__(self):
        self.historical_manager = HistoricalDataManager()
        self.pattern_analyzer = PatternAnalyzer()
        self.price_fetcher = StockPriceFetcher()
        
        self.data_dir = self.historical_manager.data_dir
    
    def fetch_and_prepare_complete_dataset(self, months: int = 3):
        """
        Complete pipeline: fetch historical data, analyze patterns, prepare ML dataset
        
        Args:
            months: Number of months of historical data to fetch
        """
        print("\n" + "=" * 80)
        print(" ML DATA PREPARATION PIPELINE")
        print("=" * 80)
        print(f"\nPreparing {months} months of historical data for ML training...\n")
        
        # Step 1: Check existing historical data
        print("\n[STEP 1/6] CHECKING EXISTING HISTORICAL DATA")
        print("-" * 80)
        self.historical_manager.print_summary()
        
        metadata = self.historical_manager.get_metadata()
        
        if metadata['total_articles'] < 1000:
            print(f"\n⚠️  Only {metadata['total_articles']} articles in historical data")
            print("   Recommendation: Collect more historical data")
            print(f"   Run: python pipeline/collect_historical_data.py --months {months}")
            
            response = input("\n   Continue with existing data? (y/n): ")
            if response.lower() != 'y':
                print("\n   Exiting. Please collect more historical data first.")
                return
        
        # Step 2: Export historical data
        print("\n[STEP 2/6] EXPORTING HISTORICAL DATA")
        print("-" * 80)
        ml_file = self.historical_manager.export_for_ml_training()
        print(f"[OK] Exported to {ml_file}")
        
        # Step 3: Load and validate data
        print("\n[STEP 3/6] LOADING AND VALIDATING DATA")
        print("-" * 80)
        df = pd.read_csv(ml_file)
        print(f"[OK] Loaded {len(df)} articles")
        print(f"     Date range: {df['batch_date'].min()} to {df['batch_date'].max()}")
        print(f"     Unique tickers: {df['ticker'].nunique()}")
        print(f"     Unique sources: {df['source'].nunique()}")
        
        # Step 4: Analyze patterns
        print("\n[STEP 4/6] ANALYZING PATTERNS")
        print("-" * 80)
        patterns = self.pattern_analyzer.analyze_historical_patterns(df)
        self.pattern_analyzer.print_pattern_summary()
        self.pattern_analyzer.save_patterns()
        
        # Step 5: Fetch historical prices for labels
        print("\n[STEP 5/6] FETCHING HISTORICAL PRICES FOR LABELS")
        print("-" * 80)
        price_changes = self._fetch_price_changes(df)
        
        # Step 6: Generate ML features
        print("\n[STEP 6/6] GENERATING ML FEATURES")
        print("-" * 80)
        df_ml = self.pattern_analyzer.create_training_dataset(df, price_changes)
        
        # Save final dataset
        output_file = os.path.join(self.data_dir, "ml_features_engineered.csv")
        df_ml.to_csv(output_file, index=False)
        print(f"\n[OK] ML-ready dataset saved to {output_file}")
        
        # Generate summary report
        self._generate_summary_report(df_ml, patterns)
        
        print("\n" + "=" * 80)
        print(" ML DATA PREPARATION COMPLETE!")
        print("=" * 80)
        print(f"\n✅ Training dataset ready: {output_file}")
        print(f"✅ {len(df_ml)} samples with {len(df_ml.columns)} features")
        print(f"✅ Patterns discovered and saved")
        print("\nNext steps:")
        print("  1. Train ML model: python pipeline/ml_predictor.py --train")
        print("  2. Evaluate model: python pipeline/ml_predictor.py --evaluate")
        print("  3. Make predictions: python pipeline/ml_predictor.py --predict")
        print("=" * 80 + "\n")
        
        return df_ml
    
    def _fetch_price_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fetch historical price changes for each article
        
        Returns:
            DataFrame with price changes
        """
        print("[*] Fetching historical price data...")
        
        # Get unique ticker-date combinations
        ticker_dates = df[['batch_date', 'ticker']].drop_duplicates()
        
        price_changes = []
        total = len(ticker_dates)
        
        for idx, row in ticker_dates.iterrows():
            if idx % 50 == 0:
                print(f"    Progress: {idx}/{total} ({idx/total*100:.1f}%)")
            
            ticker = row['ticker']
            date = pd.to_datetime(row['batch_date'])
            
            try:
                # Fetch price for the day and next day
                hist = self.price_fetcher.fetch_historical_prices(
                    ticker,
                    period='5d',
                    interval='1d'
                )
                
                if hist is not None and len(hist) >= 2:
                    # Find the closest dates
                    hist['date'] = pd.to_datetime(hist.index).date
                    target_date = date.date()
                    
                    # Get price on news date
                    news_day = hist[hist['date'] == target_date]
                    
                    # Get price next day
                    next_date = (date + timedelta(days=1)).date()
                    next_day = hist[hist['date'] == next_date]
                    
                    if len(news_day) > 0 and len(next_day) > 0:
                        price_before = news_day['Close'].iloc[0]
                        price_after = next_day['Close'].iloc[0]
                        price_change = price_after - price_before
                        price_change_pct = (price_change / price_before) * 100
                        
                        price_changes.append({
                            'batch_date': row['batch_date'],
                            'ticker': ticker,
                            'price_before': price_before,
                            'price_after': price_after,
                            'price_change': price_change,
                            'price_change_pct': price_change_pct
                        })
            except Exception as e:
                # Skip if price data not available
                pass
        
        print(f"[OK] Fetched price changes for {len(price_changes)} ticker-date combinations")
        
        if price_changes:
            return pd.DataFrame(price_changes)
        return None
    
    def _generate_summary_report(self, df_ml: pd.DataFrame, patterns: Dict):
        """Generate summary report of ML dataset"""
        
        report_file = os.path.join(self.data_dir, "ml_data_report.txt")
        
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ML TRAINING DATA REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            # Dataset Statistics
            f.write("DATASET STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Samples: {len(df_ml)}\n")
            f.write(f"Total Features: {len(df_ml.columns)}\n")
            f.write(f"Date Range: {df_ml['batch_date'].min()} to {df_ml['batch_date'].max()}\n")
            f.write(f"Unique Tickers: {df_ml['ticker'].nunique()}\n")
            f.write(f"Unique Sources: {df_ml['source'].nunique()}\n\n")
            
            # Feature Categories
            f.write("FEATURE CATEGORIES\n")
            f.write("-" * 80 + "\n")
            
            feature_categories = {
                'Sentiment': [c for c in df_ml.columns if 'sentiment' in c.lower()],
                'Impact': [c for c in df_ml.columns if 'impact' in c.lower()],
                'Keyword': [c for c in df_ml.columns if 'has_' in c.lower()],
                'Temporal': [c for c in df_ml.columns if any(t in c.lower() for t in ['day', 'hour', 'weekend'])],
                'Aggregated': [c for c in df_ml.columns if 'daily_' in c.lower()],
                'Interaction': [c for c in df_ml.columns if '_x_' in c.lower()]
            }
            
            for category, features in feature_categories.items():
                f.write(f"{category} Features ({len(features)}): {', '.join(features[:5])}")
                if len(features) > 5:
                    f.write(f" ... and {len(features)-5} more")
                f.write("\n")
            
            f.write("\n")
            
            # Label Distribution (if available)
            if 'price_up' in df_ml.columns:
                f.write("LABEL DISTRIBUTION\n")
                f.write("-" * 80 + "\n")
                f.write(f"Price Up: {df_ml['price_up'].sum()} ({df_ml['price_up'].mean()*100:.1f}%)\n")
                f.write(f"Price Down: {df_ml['price_down'].sum()} ({df_ml['price_down'].mean()*100:.1f}%)\n")
                f.write(f"Significant Moves: {df_ml['significant_move'].sum()} ({df_ml['significant_move'].mean()*100:.1f}%)\n\n")
            
            # Pattern Summary
            f.write("KEY PATTERNS DISCOVERED\n")
            f.write("-" * 80 + "\n")
            
            if 'sentiment_impact' in patterns:
                f.write(f"Sentiment: {patterns['sentiment_impact']['insight']}\n")
            
            if 'keyword_impact' in patterns:
                f.write(f"High-Impact Keywords: {len(patterns['keyword_impact'])} categories identified\n")
            
            if 'source_reliability' in patterns:
                top_sources = list(patterns['source_reliability']['top_by_volume'].keys())[:5]
                f.write(f"Top Sources: {', '.join(top_sources)}\n")
            
            f.write("\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS FOR ML TRAINING\n")
            f.write("-" * 80 + "\n")
            f.write("1. Use sentiment features as primary predictors\n")
            f.write("2. Include keyword features for specific event detection\n")
            f.write("3. Consider temporal features for time-based patterns\n")
            f.write("4. Use aggregated features for ticker-level insights\n")
            f.write("5. Try ensemble models (Random Forest, XGBoost, LightGBM)\n")
            f.write("6. Perform feature selection to reduce dimensionality\n")
            f.write("7. Use cross-validation with time-based splits\n")
            f.write("8. Monitor for overfitting on recent data\n\n")
            
            f.write("=" * 80 + "\n")
        
        print(f"\n[OK] Summary report saved to {report_file}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare ML training data from historical news')
    parser.add_argument('--months', type=int, default=3, help='Months of historical data (default: 3)')
    parser.add_argument('--skip-prices', action='store_true', help='Skip fetching historical prices')
    
    args = parser.parse_args()
    
    # Run preparation pipeline
    prep = MLDataPreparation()
    df_ml = prep.fetch_and_prepare_complete_dataset(months=args.months)
    
    if df_ml is not None:
        print("\n✅ ML data preparation successful!")
        print(f"   Dataset: data/ml_features_engineered.csv")
        print(f"   Patterns: data/discovered_patterns.json")
        print(f"   Report: data/ml_data_report.txt")
    else:
        print("\n❌ ML data preparation failed")


if __name__ == "__main__":
    main()
