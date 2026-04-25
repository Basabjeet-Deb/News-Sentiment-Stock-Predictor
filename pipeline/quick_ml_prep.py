"""
Quick ML Data Preparation - Uses existing news data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.historical_data_manager import HistoricalDataManager
from pipeline.pattern_analyzer import PatternAnalyzer
import pandas as pd
from datetime import datetime


def quick_prepare():
    """Quick preparation using existing news data"""
    
    print("\n" + "=" * 70)
    print("QUICK ML DATA PREPARATION")
    print("=" * 70)
    
    # Step 1: Load existing news
    print("\n[1/4] Loading existing news data...")
    try:
        df = pd.read_csv('data/news_analyzed.csv')
        print(f"[OK] Loaded {len(df)} articles")
    except Exception as e:
        print(f"[ERROR] Could not load news data: {e}")
        return
    
    # Add batch_date if missing
    if 'batch_date' not in df.columns:
        df['batch_date'] = datetime.now().strftime("%Y-%m-%d")
    
    # Step 2: Add to historical data
    print("\n[2/4] Adding to historical data...")
    manager = HistoricalDataManager()
    articles = df.to_dict('records')
    stats = manager.add_daily_batch(articles)
    print(f"[OK] Added {stats['new_articles']} articles to historical data")
    
    # Step 3: Export for ML
    print("\n[3/4] Exporting for ML training...")
    ml_file = manager.export_for_ml_training()
    
    # Reload the exported data
    df_ml = pd.read_csv(ml_file)
    print(f"[OK] ML training data: {len(df_ml)} samples")
    
    # Step 4: Analyze patterns
    print("\n[4/4] Analyzing patterns...")
    analyzer = PatternAnalyzer()
    patterns = analyzer.analyze_historical_patterns(df_ml)
    analyzer.print_pattern_summary()
    analyzer.save_patterns()
    
    # Generate features
    print("\n[*] Generating ML features...")
    df_features = analyzer.generate_ml_features(df_ml)
    
    # Save
    output_file = 'data/ml_features_engineered.csv'
    df_features.to_csv(output_file, index=False)
    
    print("\n" + "=" * 70)
    print("PREPARATION COMPLETE!")
    print("=" * 70)
    print(f"\n[OK] ML-ready dataset: {output_file}")
    print(f"[OK] {len(df_features)} samples with {len(df_features.columns)} features")
    print(f"[OK] Patterns saved: data/discovered_patterns.json")
    print("\nFeatures created:")
    print(f"  - Sentiment features: {len([c for c in df_features.columns if 'sentiment' in c])}")
    print(f"  - Impact features: {len([c for c in df_features.columns if 'impact' in c])}")
    print(f"  - Keyword features: {len([c for c in df_features.columns if 'has_' in c])}")
    print(f"  - Temporal features: {len([c for c in df_features.columns if any(t in c for t in ['day', 'hour'])])}")
    print("\nNext steps:")
    print("  1. Train ML model: python pipeline/ml_predictor.py --train")
    print("  2. Make predictions: python pipeline/ml_predictor.py --predict")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    quick_prepare()
