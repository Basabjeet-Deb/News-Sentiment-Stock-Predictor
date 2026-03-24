"""
Run complete prototype pipeline
1. Fetch stock data
2. Fetch targeted news
3. Analyze and generate predictions
"""

import subprocess
import sys

def run_script(script_name, description):
    """Run a Python script"""
    print("\n" + "="*60)
    print(f"STEP: {description}")
    print("="*60)
    
    try:
        result = subprocess.run(
            [sys.executable, f"scripts/{script_name}"],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n[OK] {description} completed")
            return True
        else:
            print(f"\n[ERROR] {description} failed")
            return False
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False


def main():
    print("="*60)
    print("STOCK PREDICTOR PROTOTYPE - FULL PIPELINE")
    print("="*60)
    print("This will:")
    print("  1. Fetch stock data for 10 major stocks")
    print("  2. Scrape targeted news articles")
    print("  3. Analyze sentiment and generate predictions")
    print("="*60)
    
    input("\nPress Enter to start...")
    
    # Step 1: Fetch stock data
    if not run_script('fetch_prototype_data.py', 'Fetch Stock Data'):
        print("\n[ABORT] Pipeline stopped")
        return
    
    # Step 2: Fetch news
    if not run_script('fetch_targeted_news.py', 'Fetch Targeted News'):
        print("\n[ABORT] Pipeline stopped")
        return
    
    # Step 3: Analyze and predict
    if not run_script('analyze_prototype.py', 'Analyze & Generate Predictions'):
        print("\n[ABORT] Pipeline stopped")
        return
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print("  - data/prototype_stocks.csv")
    print("  - data/prototype_news.csv")
    print("  - data/sentiment_analysis.csv")
    print("  - data/predictions.csv")
    print("\nYou can now view the predictions in data/predictions.csv")


if __name__ == "__main__":
    main()
