"""
Collect data for a single date
Usage: python collect_one_date.py 20260410
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import json
from pipeline.news_spider import run_spider
import config

def collect_single_date(date_str):
    """
    Collect data for a single date
    """
    
    cache_dir = 'data/gdelt_cache'
    os.makedirs(cache_dir, exist_ok=True)
    
    print("\n" + "="*80)
    print(f" COLLECTING DATA FOR {date_str}")
    print("="*80)
    
    # Format date for display
    date_obj = datetime.strptime(date_str, '%Y%m%d')
    formatted_date = date_obj.strftime('%B %d, %Y')
    print(f"Date: {formatted_date}\n")
    
    # Check if already collected
    done_file = f'{cache_dir}/{date_str}.done.json'
    if os.path.exists(done_file):
        print(f"[SKIP] Data already collected for {date_str}")
        return
    
    # Run spider for this date
    output_file = f'{cache_dir}/{date_str}.raw.json'
    
    try:
        # Run spider
        print(f"[*] Running spider...")
        run_spider(tickers=config.STOCK_TICKERS[:200], output_file=output_file)
        
        # Mark as done
        with open(done_file, 'w') as f:
            json.dump({
                'date': date_str,
                'collected_at': datetime.now().isoformat(),
                'status': 'completed'
            }, f, indent=2)
        
        print(f"\n[OK] Data collected for {date_str}")
        print(f"     Raw data: {output_file}")
        print(f"     Status: {done_file}\n")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to collect data for {date_str}: {e}\n")
        raise


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python collect_one_date.py YYYYMMDD")
        print("Example: python collect_one_date.py 20260410")
        sys.exit(1)
    
    date_str = sys.argv[1]
    collect_single_date(date_str)
