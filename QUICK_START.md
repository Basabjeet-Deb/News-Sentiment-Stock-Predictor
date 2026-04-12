# Quick Start Guide - Performance Optimized Pipeline

## What's New? 🚀

Your pipeline now has:
- ⏱️ **Timing logs** for each stage
- 🎯 **Article cap** at 600 (prevents RAM overflow)
- 🔄 **Smart deduplication** (removes duplicate news)
- ✅ **No broken code** (all files checked)

---

## Run the Pipeline

### Option 1: Default (600 articles, ~1GB RAM)
```bash
python pipeline/run_pipeline.py
```

### Option 2: Custom Article Limit
```python
from pipeline.run_pipeline import StockPredictionPipeline

# Lower RAM (400 articles)
pipeline = StockPredictionPipeline(max_articles=400)
results = pipeline.run_complete_pipeline()

# Higher RAM (1000 articles)
pipeline = StockPredictionPipeline(max_articles=1000)
results = pipeline.run_complete_pipeline()
```

---

## What You'll See

### New Output Format:
```
[*] STOCK PREDICTION PIPELINE - COMPREHENSIVE RUN
[*] Max Articles: 600 (RAM Budget: ~1GB)

[NEWS] STEP 1: FETCHING NEWS FOR 500+ STOCKS
[INFO] Capping articles: 4914 -> 600
[INFO] After deduplication: 598 unique articles
[OK] Fetched 598 articles in 45.23s

[SENTIMENT] STEP 2: ANALYZING SENTIMENT & FILTERING
[OK] 487 relevant & impactful articles in 52.18s

[PRICES] STEP 3: FETCHING CURRENT STOCK PRICES
[OK] Fetched prices for 503 stocks in 15.67s

[PREDICT] STEP 4: GENERATING STOCK PREDICTIONS
[OK] Generated predictions for 166 stocks in 8.45s

[PERFORMANCE] TIMING BREAKDOWN:
  News Fetch                      45.23s  (35.2%)
  Sentiment Analysis              52.18s  (40.6%)
  Price Fetch                     15.67s  (12.2%)
  Prediction Generation            8.45s   (6.6%)
  Save Results                     3.21s   (2.5%)
  Historical Update                2.15s   (1.7%)
  Validation                       1.54s   (1.2%)
  ----------------------------------------
  TOTAL PIPELINE TIME            128.43s  (100.0%)
```

---

## Performance Tips

### Target Runtime: ~2 minutes
- With 600 articles: ~2 min
- With 400 articles: ~1.5 min
- With 1000 articles: ~3 min

### RAM Usage:
- 400 articles: ~700MB
- 600 articles: ~1GB ✅ (recommended)
- 1000 articles: ~1.5GB

### Bottleneck Analysis:
Look at the timing breakdown:
- If **Sentiment Analysis** is slow → Consider GPU acceleration (Option B2)
- If **News Fetch** is slow → Check internet connection
- If **Price Fetch** is slow → Consider parallel fetching (Option B4)

---

## Files Generated

After running the pipeline:
- `data/news_analyzed.csv` - Analyzed news articles
- `data/predictions.csv` - Stock predictions
- `data/stock_prices.csv` - Current stock prices
- `data/historical_news_batched.json` - Historical data

---

## API Usage

### Start API Server:
```bash
cd app
uvicorn main:app --reload --port 8000
```

### Start Frontend:
```bash
cd frontend
python -m http.server 3000
```

### Access:
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Troubleshooting

### RAM Issues?
```python
# Reduce article cap
pipeline = StockPredictionPipeline(max_articles=400)
```

### Slow Performance?
- Check timing breakdown
- Optimize slowest stage first
- See UPGRADE_AND_UI_PLAN.md for Option B

### Import Errors?
```bash
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ Run pipeline and check timing logs
2. ✅ Verify RAM usage stays under 1GB
3. ✅ Check if runtime is ~2 minutes
4. If needed, implement Option B optimizations (see UPGRADE_AND_UI_PLAN.md)

---

© 2026 Basabjeet Deb - News Sentiment Based Stock Predictor
