"""
Pipeline service - orchestrates the complete prediction pipeline
"""

import sys
import os
from typing import Dict, Optional
from datetime import datetime
import pandas as pd

# Add parent directory to import existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import get_settings, STOCK_TICKERS
from app.services.news_service import NewsService
from app.services.sentiment_service import SentimentService
from app.services.price_service import PriceService
from app.services.prediction_service import PredictionService


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
    
    def run_full_pipeline(self, max_articles: int = 1000) -> Dict:
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
        }
        
        try:
            # Step 1: Fetch News
            print("[PIPELINE] Step 1: Fetching news...")
            raw_news = self.news_service.fetch_comprehensive_news(max_articles)
            results["steps"]["news_fetch"] = {
                "status": "complete",
                "articles_fetched": len(raw_news),
            }
            
            # Step 2: Analyze Sentiment
            print("[PIPELINE] Step 2: Analyzing sentiment...")
            analyzed_news = self.sentiment_service.analyze_batch(raw_news)
            filtered_news = self.sentiment_service.filter_relevant_impactful(analyzed_news)
            results["steps"]["sentiment_analysis"] = {
                "status": "complete",
                "analyzed": len(analyzed_news),
                "relevant": len(filtered_news),
            }
            
            # Step 3: Fetch Stock Prices
            print("[PIPELINE] Step 3: Fetching prices...")
            prices = self.price_service.fetch_prices(STOCK_TICKERS)
            valid_prices = {k: v for k, v in prices.items() if 'error' not in v}
            results["steps"]["price_fetch"] = {
                "status": "complete",
                "stocks_fetched": len(valid_prices),
            }
            
            # Step 4: Generate Predictions
            print("[PIPELINE] Step 4: Generating predictions...")
            predictions = self.prediction_service.generate_predictions(
                filtered_news, prices
            )
            results["steps"]["prediction_generation"] = {
                "status": "complete",
                "predictions_generated": len(predictions),
            }
            
            # Step 5: Save Results
            print("[PIPELINE] Step 5: Saving results...")
            self._save_results(filtered_news, predictions, prices)
            results["steps"]["save_results"] = {
                "status": "complete",
            }
            
            # Complete
            results["status"] = "complete"
            results["completed_at"] = datetime.now().isoformat()
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
        }
        
        try:
            # Fetch news
            raw_news = self.news_service.fetch_comprehensive_news(500)
            analyzed_news = self.sentiment_service.analyze_batch(raw_news)
            filtered_news = self.sentiment_service.filter_relevant_impactful(analyzed_news)
            
            # Use cached prices or fetch new
            prices = self.price_service.get_cached_prices()
            if not prices:
                prices = self.price_service.fetch_prices(STOCK_TICKERS)
            
            # Generate predictions
            predictions = self.prediction_service.generate_predictions(
                filtered_news, prices
            )
            
            # Save
            self._save_results(filtered_news, predictions, prices)
            
            results["status"] = "complete"
            results["news_articles"] = len(filtered_news)
            results["predictions"] = len(predictions)
            results["completed_at"] = datetime.now().isoformat()
            
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
            news_df = pd.DataFrame([
                {
                    'title': n.get('title', ''),
                    'source': n.get('source', ''),
                    'ticker': n.get('ticker', ''),
                    'published_at': n.get('published_at', ''),
                    'sentiment_compound': n.get('sentiment', {}).get('compound', 0),
                    'sentiment_label': n.get('sentiment', {}).get('label', 'Neutral'),
                    'impact_level': n.get('relevance', {}).get('impact_level', 'low'),
                    'relevance_score': n.get('relevance', {}).get('score', 0),
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
