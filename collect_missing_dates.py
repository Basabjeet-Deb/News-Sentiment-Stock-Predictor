"""
Collect missing dates, ingest into news_events.csv,
rebuild daily_panel.csv, and retrain the forecaster.

Usage:
  python collect_missing_dates.py              # auto-detect missing up to today
  python collect_missing_dates.py --no-collect # skip spider, just rebuild panel
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import glob
import argparse
from datetime import datetime, timedelta, timezone

import pandas as pd

from pipeline.news_spider import run_spider
from pipeline.sentiment_analyzer import SentimentAnalyzer
from pipeline.time_series_dataset import TimeSeriesDatasetBuilder
from pipeline.forecaster import DailyPanelForecaster
import config

# Pre-build a fast title→ticker lookup from config.STOCK_TICKERS
# Maps each ticker symbol to itself for word-boundary matching
def _build_ticker_lookup():
    import re
    tickers = [t.strip().upper() for t in config.STOCK_TICKERS if t.strip()]
    # Sort longest first so BRK.B matches before BRK
    tickers = sorted(set(tickers), key=len, reverse=True)
    patterns = [(t, re.compile(r'\b' + re.escape(t.replace('.', r'\.')) + r'\b')) for t in tickers]
    return patterns

_TICKER_PATTERNS = None

def _assign_ticker(article: dict) -> str:
    """Extract the first matching ticker from title+description."""
    global _TICKER_PATTERNS
    if _TICKER_PATTERNS is None:
        _TICKER_PATTERNS = _build_ticker_lookup()
    text = ((article.get("title") or "") + " " + (article.get("description") or "")).upper()
    for ticker, pat in _TICKER_PATTERNS:
        if pat.search(text):
            return ticker
    return ""

CACHE_DIR = "data/gdelt_cache"
DATA_DIR  = "data"


# ── helpers ──────────────────────────────────────────────────────────────────

def _cached_dates():
    os.makedirs(CACHE_DIR, exist_ok=True)
    return {
        os.path.basename(f).replace(".done.json", "")
        for f in glob.glob(os.path.join(CACHE_DIR, "*.done.json"))
    }

def _ingested_dates():
    events_path = os.path.join(DATA_DIR, "news_events.csv")
    if not os.path.exists(events_path):
        return set()
    try:
        df = pd.read_csv(events_path, usecols=["scraped_at"], on_bad_lines="skip")
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
        return set(df["scraped_at"].dt.strftime("%Y%m%d").dropna().unique())
    except Exception:
        return set()


# ── step 1: collect ───────────────────────────────────────────────────────────

def collect_missing(start: datetime, end: datetime):
    cached = _cached_dates()

    missing = []
    cur = start
    while cur <= end:
        ds = cur.strftime("%Y%m%d")
        if ds not in cached:
            missing.append(ds)
        cur += timedelta(days=1)

    print(f"\n{'='*70}")
    print(" STEP 1: COLLECT MISSING DATES")
    print(f"{'='*70}")
    print(f"  Cached : {len(cached)} dates")
    print(f"  Missing: {len(missing)} dates -> {missing}")

    if not missing:
        print("  [OK] Nothing to collect.")
        return

    analyzer = SentimentAnalyzer()
    for i, date_str in enumerate(missing, 1):
        print(f"\n  [{i}/{len(missing)}] {date_str}")
        raw_file  = os.path.join(CACHE_DIR, f"{date_str}.raw.json")
        done_file = os.path.join(CACHE_DIR, f"{date_str}.done.json")
        try:
            # Run spider as a subprocess — Scrapy's reactor can only start once per process
            import subprocess
            result = subprocess.run(
                ["python", "collect_one_date.py", date_str],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print(f"  [OK] {date_str} collected")
            else:
                print(f"  [ERROR] {date_str}: {result.stderr[-200:] if result.stderr else 'unknown'}")
        except Exception as e:
            print(f"  [ERROR] {date_str}: {e}")


# ── step 2: ingest into news_events.csv ──────────────────────────────────────

def ingest_cached():
    cached   = _cached_dates()
    ingested = _ingested_dates()
    pending  = sorted(cached - ingested)

    print(f"\n{'='*70}")
    print(" STEP 2: INGEST INTO news_events.csv")
    print(f"{'='*70}")
    print(f"  Cached: {len(cached)}  Already ingested: {len(ingested)}  Pending: {len(pending)}")

    if not pending:
        print("  [OK] All dates already ingested.")
        return

    ds_builder = TimeSeriesDatasetBuilder(DATA_DIR)
    analyzer   = SentimentAnalyzer()
    total_new  = 0

    for date_str in pending:
        raw_file = os.path.join(CACHE_DIR, f"{date_str}.raw.json")
        if not os.path.exists(raw_file):
            continue
        with open(raw_file, "r", encoding="utf-8") as f:
            try:
                raw = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  [SKIP] {date_str}: corrupted JSON ({e})")
                continue
        # Handle both formats: plain list OR {"articles": [...], "meta": {...}}
        articles = raw if isinstance(raw, list) else raw.get("articles", [])

        # For old GDELT-format articles (no ticker), extract ticker from title
        for a in articles:
            if isinstance(a, dict) and not a.get("ticker", "").strip():
                a["ticker"] = _assign_ticker(a)

        # Force scraped_at to the cache date regardless of what the spider set.
        # Articles scraped today for a past date must carry that past date,
        # otherwise they all land on today and miss price labels.
        date_obj = datetime.strptime(date_str, "%Y%m%d").replace(
            hour=12, tzinfo=timezone.utc
        )
        for a in articles:
            a["scraped_at"] = date_obj.isoformat()

        analyzed = analyzer.analyze_batch(articles)
        appended = ds_builder.append_news_events(analyzed)
        total_new += appended
        print(f"  [OK] {date_str}: {len(articles)} articles -> {appended} new rows")

    print(f"\n  Total new rows appended: {total_new}")


# ── step 3: rebuild daily panel ───────────────────────────────────────────────

def rebuild_panel():
    print(f"\n{'='*70}")
    print(" STEP 3: REBUILD daily_panel.csv")
    print(f"{'='*70}")

    ds_builder = TimeSeriesDatasetBuilder(DATA_DIR)
    panel = ds_builder.build_daily_panel(
        tickers=config.STOCK_TICKERS,
        horizon_days=1,
        lookback_days=60,
    )
    print(f"  [OK] {len(panel)} rows | {panel['ticker'].nunique()} tickers")
    print(f"       Date range: {panel['date'].min()} -> {panel['date'].max()}")
    return panel


# ── step 4: retrain forecaster ────────────────────────────────────────────────

def retrain():
    print(f"\n{'='*70}")
    print(" STEP 4: RETRAIN FORECASTER")
    print(f"{'='*70}")

    panel_path = os.path.join(DATA_DIR, "daily_panel.csv")
    forecaster = DailyPanelForecaster(DATA_DIR)
    meta = forecaster.train(panel_path)

    print(f"  [OK] Model    : {meta['model']}")
    print(f"       Accuracy : {meta['metrics']['accuracy']:.4f}")
    print(f"       AUC      : {meta['metrics']['auc']:.4f}")
    print(f"       F1       : {meta['metrics']['f1']:.4f}")
    print(f"       Rows     : {meta['rows']}")

    preds = forecaster.predict_latest(panel_path)
    if not preds.empty:
        print(f"\n  [OK] Predictions for: {preds['date'].iloc[0]}")
        print(f"       Tickers : {len(preds)}")
        print(f"       Prob range: {preds['ml_probability_up'].min():.4f} - {preds['ml_probability_up'].max():.4f}")
        print(f"       Recs: {preds['ml_recommendation'].value_counts().to_dict()}")
    else:
        print("  [!] No predictions generated")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Collect, ingest, rebuild panel, retrain")
    parser.add_argument("--no-collect", action="store_true",
                        help="Skip spider collection, just ingest + rebuild + retrain")
    parser.add_argument("--start", default="20260309",
                        help="Start date YYYYMMDD (default: 20260309)")
    parser.add_argument("--today", action="store_true",
                        help="Only collect today if missing, then ingest + rebuild + retrain")
    parser.add_argument("--run-pipeline", action="store_true",
                        help="After retraining, trigger the API pipeline to refresh predictions")
    args = parser.parse_args()

    end = datetime.now()

    if args.today:
        # Only care about today — fast daily update
        start = datetime(end.year, end.month, end.day)
    else:
        start = datetime.strptime(args.start, "%Y%m%d")

    print(f"\n{'='*70}")
    print(" NEWS PANEL MAINTENANCE")
    print(f" Range: {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')}")
    print(f"{'='*70}")

    if not args.no_collect:
        collect_missing(start, end)

    ingest_cached()
    rebuild_panel()
    retrain()

    # Optionally kick the live API so predictions refresh immediately
    if args.run_pipeline:
        print(f"\n{'='*70}")
        print(" STEP 5: TRIGGERING API PIPELINE")
        print(f"{'='*70}")
        try:
            import requests as _req
            r = _req.post("http://localhost:8000/api/v1/pipeline/run", timeout=10)
            print(f"  [OK] Pipeline triggered: {r.json().get('status')}")
        except Exception as e:
            print(f"  [!] Could not reach API: {e} (start the server first)")

    print(f"\n{'='*70}")
    print(" ALL DONE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
