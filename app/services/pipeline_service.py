"""
Pipeline service - orchestrates the complete prediction pipeline
"""

import sys
import os
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
from typing import Callable, Any

# Add parent directory to import existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time

from app.core.config import get_settings, STOCK_TICKERS
from pipeline.article_prep import prepare_articles_for_pipeline
from app.services.news_service import NewsService
from app.services.sentiment_service import SentimentService
from app.services.price_service import PriceService
from app.services.prediction_service import PredictionService

from pipeline.time_series_dataset import TimeSeriesDatasetBuilder
from pipeline.forecaster import DailyPanelForecaster
from pipeline.sector_mapper import SectorCache


class PipelineService:
    """Service for running the complete prediction pipeline"""
    
    def __init__(self):
        self.news_service = NewsService()
        self.sentiment_service = SentimentService()
        self.price_service = PriceService()
        self.prediction_service = PredictionService()
        self.settings = get_settings()
        
        self._last_run: Optional[datetime] = None
        self._last_results: Optional[Dict] = None
    
    def run_full_pipeline(
        self,
        max_articles: int = 1000,
        progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict:
        """
        Run the complete prediction pipeline
        
        Steps:
        1. Fetch news from all sources
        2. Analyze sentiment
        3. Fetch current stock prices
        4. Generate predictions
        5. Save results
        
        Args:
            max_articles: Maximum news articles to fetch
            
        Returns:
            Pipeline results dictionary
        """
        results = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "steps": {},
            "step_timings_seconds": {},
        }
        settings = self.settings
        
        try:
            # Step 1: Fetch News
            print("[PIPELINE] Step 1: Fetching news...")
            if progress_cb:
                progress_cb({"stage": "news_fetch", "percent": 10, "message": "Fetching news..."})
            t0 = time.monotonic()
            raw_news = self.news_service.fetch_comprehensive_news(max_articles)
            t1 = time.monotonic()
            cap = min(int(settings.PIPELINE_ARTICLE_CAP), int(max_articles), len(raw_news))
            prepared_news = prepare_articles_for_pipeline(raw_news, cap)
            t2 = time.monotonic()
            results["steps"]["news_fetch"] = {
                "status": "complete",
                "articles_fetched": len(raw_news),
                "articles_after_dedupe_cap": len(prepared_news),
                "article_cap": cap,
            }
            results["step_timings_seconds"]["news_fetch"] = round(t1 - t0, 3)
            results["step_timings_seconds"]["news_dedupe_sort_cap"] = round(t2 - t1, 3)
            
            # Step 2: Analyze Sentiment
            print("[PIPELINE] Step 2: Analyzing sentiment...")
            if progress_cb:
                progress_cb({"stage": "sentiment_analysis", "percent": 35, "message": "Analyzing sentiment..."})
            t3 = time.monotonic()
            analyzed_news = self.sentiment_service.analyze_batch(prepared_news)
            filtered_news = self.sentiment_service.filter_relevant_impactful(analyzed_news)
            t4 = time.monotonic()
            results["steps"]["sentiment_analysis"] = {
                "status": "complete",
                "analyzed": len(analyzed_news),
                "relevant": len(filtered_news),
            }
            results["step_timings_seconds"]["sentiment_analysis"] = round(t4 - t3, 3)
            
            # Step 3: Fetch Stock Prices
            print("[PIPELINE] Step 3: Fetching prices...")
            if progress_cb:
                progress_cb({"stage": "price_fetch", "percent": 55, "message": "Fetching stock prices..."})
            t5 = time.monotonic()
            try:
                SectorCache(self.settings.DATA_DIR).ensure(
                    STOCK_TICKERS, max_new=40, sleep_s=0.2
                )
            except Exception:
                pass
            prices = self.price_service.fetch_prices(STOCK_TICKERS)
            valid_prices = {k: v for k, v in prices.items() if 'error' not in v}
            t6 = time.monotonic()
            results["steps"]["price_fetch"] = {
                "status": "complete",
                "stocks_fetched": len(valid_prices),
            }
            results["step_timings_seconds"]["price_fetch"] = round(t6 - t5, 3)
            
            # Step 4: Generate Predictions
            print("[PIPELINE] Step 4: Generating predictions...")
            if progress_cb:
                progress_cb({"stage": "prediction_generation", "percent": 75, "message": "Generating predictions..."})
            t7 = time.monotonic()
            predictions = self.prediction_service.generate_predictions(
                filtered_news, prices
            )
            t8 = time.monotonic()
            results["steps"]["prediction_generation"] = {
                "status": "complete",
                "predictions_generated": len(predictions),
            }
            results["step_timings_seconds"]["prediction_generation"] = round(t8 - t7, 3)
            
            # Step 5: Save Results
            print("[PIPELINE] Step 5: Saving results...")
            if progress_cb:
                progress_cb({"stage": "save_results", "percent": 90, "message": "Saving results..."})
            t9 = time.monotonic()
            self._save_results(filtered_news, predictions, prices)
            t10 = time.monotonic()
            results["steps"]["save_results"] = {
                "status": "complete",
            }
            results["step_timings_seconds"]["save_results"] = round(t10 - t9, 3)

            # Step 6: Append to time-series store (events + daily panel)
            try:
                if progress_cb:
                    progress_cb({"stage": "timeseries", "percent": 95, "message": "Updating time-series dataset..."})
                ds = TimeSeriesDatasetBuilder(data_dir=self.settings.DATA_DIR)
                appended = ds.append_news_events(filtered_news)
                # Build a proper daily panel for the full universe (zero-news days included).
                # This is what makes the ML forecaster truly time-series based.
                panel = ds.build_daily_panel(tickers=STOCK_TICKERS, horizon_days=1, lookback_days=180)
                results["steps"]["timeseries"] = {
                    "status": "complete",
                    "events_appended": appended,
                    "panel_rows": int(len(panel)),
                }
            except Exception as e:
                results["steps"]["timeseries"] = {"status": "error", "error": str(e)}

            # Step 7: Train + infer next-day model-based predictions
            try:
                panel_path = os.path.join(self.settings.DATA_DIR, "daily_panel.csv")
                if os.path.exists(panel_path):
                    if progress_cb:
                        progress_cb({"stage": "forecast_train", "percent": 97, "message": "Training forecaster..."})
                    forecaster = DailyPanelForecaster(data_dir=self.settings.DATA_DIR)
                    meta = forecaster.train(panel_path)

                    if progress_cb:
                        progress_cb({"stage": "forecast_predict", "percent": 98, "message": "Predicting next-day moves..."})
                    ml_preds = forecaster.predict_latest(panel_path)

                    ml_map = {}
                    for _, r in ml_preds.iterrows():
                        ml_map[str(r["ticker"]).upper()] = {
                            "ml_probability_up": float(r["ml_probability_up"]),
                            "ml_confidence": float(r["ml_confidence"]),
                            "ml_recommendation": str(r["ml_recommendation"]),
                            "ml_score": float(r["ml_score"]),
                            "ml_date": str(r["date"]),
                        }

                    # Merge ML outputs into existing predictions and switch recommendation to ML-based.
                    for p in predictions:
                        t = str(p.get("ticker", "")).upper()
                        if t in ml_map:
                            p.update(ml_map[t])
                            p["prediction_score"] = round(p.get("ml_score", p.get("prediction_score", 0.0)), 3)
                            try:
                                base_conf = float(p.get("confidence", 0.0) or 0.0)
                            except Exception:
                                base_conf = 0.0
                            try:
                                ml_conf = float(p.get("ml_confidence", 0.0) or 0.0)
                            except Exception:
                                ml_conf = 0.0
                            p["confidence"] = round(max(base_conf, ml_conf), 3)

                            # Blend ML and sentiment when they strongly disagree.
                            # If sentiment is strongly negative (< -0.3) but ML says BUY/STRONG BUY,
                            # or sentiment is strongly positive (> 0.3) but ML says SELL/STRONG SELL,
                            # downgrade to HOLD to avoid misleading signals.
                            ml_rec  = p.get("ml_recommendation", "HOLD")
                            sent    = float(p.get("avg_sentiment", 0.0) or 0.0)
                            news_ct = int(p.get("news_count", 0) or 0)

                            strong_conflict = (
                                news_ct > 0 and (
                                    (sent < -0.3 and ml_rec in ("BUY", "STRONG BUY")) or
                                    (sent >  0.3 and ml_rec in ("SELL", "STRONG SELL"))
                                )
                            )
                            if strong_conflict:
                                # Downgrade: strong disagreement → HOLD
                                p["recommendation"] = "HOLD"
                                p["ml_recommendation"] = "HOLD"
                            else:
                                p["recommendation"] = ml_rec
                        else:
                            # Not in ML panel — fall back to sentiment-driven values
                            # so the UI never shows prob=0 or a flat HOLD for everything.
                            sent = float(p.get("avg_sentiment", 0.0) or 0.0)
                            # Map sentiment [-1,1] to probability [0,1]
                            prob = round(0.5 + sent * 0.3, 4)
                            prob = max(0.05, min(0.95, prob))
                            score = round((prob - 0.5) * 2, 4)
                            conf = round(abs(sent) * 0.6, 4)
                            # Recommendation from sentiment score
                            if sent >= 0.5:
                                rec = "STRONG BUY"
                            elif sent >= 0.15:
                                rec = "BUY"
                            elif sent <= -0.5:
                                rec = "STRONG SELL"
                            elif sent <= -0.15:
                                rec = "SELL"
                            else:
                                rec = "HOLD"
                            p["ml_probability_up"] = prob
                            p["ml_confidence"] = conf
                            p["ml_score"] = score
                            p["ml_recommendation"] = rec
                            p["ml_date"] = "sentiment-only"
                            p["prediction_score"] = round(p.get("prediction_score", score), 3)
                            p["recommendation"] = p.get("sentiment_recommendation", rec)
                            p["confidence"] = round(max(float(p.get("confidence", 0.0) or 0.0), conf), 3)

                    # Re-save predictions.csv with ML columns included
                    self._save_results(filtered_news, predictions, prices)

                    results["steps"]["forecast"] = {
                        "status": "complete",
                        "trained_at": meta.get("trained_at"),
                        "model": meta.get("model"),
                        "metrics": meta.get("metrics", {}),
                        "predicted_date": ml_preds["date"].iloc[0] if len(ml_preds) else None,
                        "predicted_tickers": int(len(ml_preds)),
                    }
                else:
                    results["steps"]["forecast"] = {"status": "skipped", "reason": "daily_panel.csv not found"}
            except Exception as e:
                results["steps"]["forecast"] = {"status": "error", "error": str(e)}
            
            # Complete
            results["status"] = "complete"
            results["completed_at"] = datetime.now().isoformat()
            st = results.get("step_timings_seconds") or {}
            results["step_timings_seconds"]["total_tracked"] = round(sum(st.values()), 3)
            if progress_cb:
                progress_cb({"stage": "complete", "percent": 100, "message": "Pipeline complete."})
            results["summary"] = {
                "news_articles": len(filtered_news),
                "stocks_with_prices": len(valid_prices),
                "predictions": len(predictions),
                "top_picks": predictions[:5] if predictions else [],
                "sell_candidates": predictions[-5:] if predictions else [],
            }
            
            self._last_run = datetime.now()
            self._last_results = results
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["completed_at"] = datetime.now().isoformat()
        
        return results
    
    def run_quick_update(self) -> Dict:
        """
        Run a quick update - only fetch new news and regenerate predictions
        Uses cached prices if available
        """
        results = {
            "status": "running",
            "type": "quick_update",
            "started_at": datetime.now().isoformat(),
            "step_timings_seconds": {},
        }
        
        try:
            t0 = time.monotonic()
            raw_news = self.news_service.fetch_comprehensive_news(500)
            cap = min(500, int(self.settings.PIPELINE_ARTICLE_CAP), len(raw_news))
            prepared = prepare_articles_for_pipeline(raw_news, cap)
            t1 = time.monotonic()
            results["step_timings_seconds"]["news_fetch_prep"] = round(t1 - t0, 3)
            results["articles_after_dedupe_cap"] = len(prepared)

            analyzed_news = self.sentiment_service.analyze_batch(prepared)
            filtered_news = self.sentiment_service.filter_relevant_impactful(analyzed_news)
            t2 = time.monotonic()
            results["step_timings_seconds"]["sentiment_analysis"] = round(t2 - t1, 3)
            
            t3 = time.monotonic()
            prices = self.price_service.get_cached_prices()
            if not prices:
                try:
                    SectorCache(self.settings.DATA_DIR).ensure(
                        STOCK_TICKERS, max_new=40, sleep_s=0.2
                    )
                except Exception:
                    pass
                prices = self.price_service.fetch_prices(STOCK_TICKERS)
            t4 = time.monotonic()
            results["step_timings_seconds"]["price_fetch"] = round(t4 - t3, 3)

            predictions = self.prediction_service.generate_predictions(
                filtered_news, prices
            )
            t5 = time.monotonic()
            results["step_timings_seconds"]["prediction_generation"] = round(t5 - t4, 3)

            self._save_results(filtered_news, predictions, prices)
            t6 = time.monotonic()
            results["step_timings_seconds"]["save_results"] = round(t6 - t5, 3)
            
            results["status"] = "complete"
            results["news_articles"] = len(filtered_news)
            results["predictions"] = len(predictions)
            results["completed_at"] = datetime.now().isoformat()
            results["step_timings_seconds"]["total_tracked"] = round(
                sum(results["step_timings_seconds"].values()), 3
            )
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def get_last_run_status(self) -> Dict:
        """Get status of last pipeline run"""
        if self._last_results:
            return self._last_results
        
        # Check if data files exist
        news_exists = os.path.exists(self.settings.NEWS_CSV)
        pred_exists = os.path.exists(self.settings.PREDICTIONS_CSV)
        prices_exists = os.path.exists(self.settings.PRICES_CSV)
        
        return {
            "status": "no_run",
            "data_available": {
                "news": news_exists,
                "predictions": pred_exists,
                "prices": prices_exists,
            },
            "message": "Run the pipeline to generate fresh predictions",
        }
    
    def load_existing_data(self) -> Dict:
        """Load existing data from CSV files"""
        news = self.news_service.load_from_csv()
        predictions = self.prediction_service.load_from_csv()
        prices = self.price_service.load_from_csv()
        
        return {
            "news": news,
            "predictions": predictions,
            "prices": prices,
            "news_count": len(news),
            "predictions_count": len(predictions),
            "prices_count": len(prices),
        }
    
    def _save_results(
        self,
        news: list,
        predictions: list,
        prices: dict
    ) -> None:
        """Save all results to CSV files"""
        
        # Create data directory if needed
        os.makedirs(self.settings.DATA_DIR, exist_ok=True)
        
        # Save news
        if news:
            # The sentiment analyzer used by this service (`pipeline/sentiment_analyzer.py`)
            # produces *flat* keys like `sentiment_compound`, `impact_level`, `relevance_score`.
            # Persist those directly so downstream API/UI doesn't lose data to schema mismatches.
            news_df = pd.DataFrame([
                {
                    'title': n.get('title', ''),
                    'source': n.get('source', ''),
                    'ticker': n.get('ticker', ''),
                    'published_at': n.get('published_at', ''),
                    'sentiment_compound': n.get('sentiment_compound', 0),
                    'sentiment_positive': n.get('sentiment_positive', 0),
                    'sentiment_negative': n.get('sentiment_negative', 0),
                    'sentiment_neutral': n.get('sentiment_neutral', 0),
                    'sentiment_label': n.get('sentiment_label', 'Neutral'),
                    'impact_level': n.get('impact_level', 'low'),
                    'relevance_score': n.get('relevance_score', 0),
                    'is_relevant': n.get('is_relevant', False),
                    'is_impactful': n.get('is_impactful', False),
                    'url': n.get('url', ''),
                }
                for n in news
            ])
            news_df.to_csv(self.settings.NEWS_CSV, index=False)
        
        # Save predictions
        if predictions:
            pred_df = pd.DataFrame(predictions)
            pred_df.to_csv(self.settings.PREDICTIONS_CSV, index=False)
        
        # Save prices
        if prices:
            price_list = [v for v in prices.values() if 'error' not in v]
            if price_list:
                price_df = pd.DataFrame(price_list)
                price_df.to_csv(self.settings.PRICES_CSV, index=False)
