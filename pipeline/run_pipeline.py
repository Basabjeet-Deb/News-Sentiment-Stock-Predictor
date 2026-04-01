"""
Complete News-to-Prediction Pipeline
Combines news fetching, sentiment analysis, stock prices, and predictions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.news_fetcher import EnhancedNewsFetcher
from pipeline.sentiment_analyzer import SentimentAnalyzer
from pipeline.price_fetcher import StockPriceFetcher
import config
import pandas as pd
from datetime import datetime
import json

class StockPredictionPipeline:
    """Complete pipeline from news to predictions"""
    
    def __init__(self):
        self.news_fetcher = EnhancedNewsFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.price_fetcher = StockPriceFetcher()
        
        self.news_data = []
        self.price_data = {}
        self.predictions = {}
    
    def run_complete_pipeline(self):
        """Run the entire pipeline"""
        
        print("\n" + "=" * 80)
        print(" [*] STOCK PREDICTION PIPELINE - COMPREHENSIVE RUN")
        print("=" * 80 + "\n")
        
        # Step 1: Fetch News
        print("\n[NEWS] STEP 1: FETCHING NEWS FOR 500+ STOCKS")
        print("-" * 80)
        raw_news = self.news_fetcher.fetch_comprehensive_news(max_articles=1000)
        print(f"[OK] Fetched {len(raw_news)} articles\n")
        
        # Step 2: Analyze Sentiment
        print("\n[SENTIMENT] STEP 2: ANALYZING SENTIMENT & FILTERING FOR RELEVANCE")
        print("-" * 80)
        analyzed_news = self.sentiment_analyzer.analyze_batch(raw_news)
        
        # Filter for relevant/impactful news only
        self.news_data = self.sentiment_analyzer.filter_relevant_impactful(analyzed_news)
        print(f"[OK] {len(self.news_data)} relevant & impactful articles\n")
        
        # Step 3: Fetch Stock Prices
        print("\n[PRICES] STEP 3: FETCHING CURRENT STOCK PRICES")
        print("-" * 80)
        all_stocks = config.STOCK_TICKERS
        print(f"Fetching prices for {len(all_stocks)} stocks...")
        self.price_data = self.price_fetcher.fetch_current_prices(all_stocks)
        print(f"[OK] Fetched prices for {len(self.price_data)} stocks\n")
        
        # Step 4: Generate Predictions
        print("\n[PREDICT] STEP 4: GENERATING STOCK PREDICTIONS")
        print("-" * 80)
        self.predictions = self._generate_predictions()
        print(f"[OK] Generated predictions for {len(self.predictions)} stocks\n")
        
        # Step 5: Save Results
        print("\n[SAVE] STEP 5: SAVING RESULTS")
        print("-" * 80)
        self._save_results()
        print("[OK] All data saved to CSV files\n")
        
        # Step 6: Show Summary
        self._print_summary()
        
        return {
            'news': self.news_data,
            'prices': self.price_data,
            'predictions': self.predictions
        }
    
    def _generate_predictions(self):
        """Generate predictions for all stocks"""
        predictions = []
        
        for ticker in config.STOCK_TICKERS:
            # Get sentiment for this stock
            sentiment_summary = self.sentiment_analyzer.get_stock_sentiment_summary(
                self.news_data, ticker
            )
            
            # Get price data
            price_info = self.price_data.get(ticker, {})
            
            # Skip if no price data
            if 'error' in price_info or price_info.get('price', 0) == 0:
                continue
            
            # Calculate prediction score
            prediction_score = self._calculate_prediction_score(
                sentiment_summary, price_info
            )
            
            predictions.append({
                'ticker': ticker,
                'company_name': price_info.get('company_name', ticker),
                'current_price': price_info.get('price', 0),
                'price_change_percent': price_info.get('change_percent', 0),
                'sector': price_info.get('sector', 'Unknown'),
                
                # Sentiment data
                'news_count': sentiment_summary.get('article_count', 0),
                'avg_sentiment': sentiment_summary.get('avg_sentiment', 0),
                'positive_news': sentiment_summary.get('positive_count', 0),
                'negative_news': sentiment_summary.get('negative_count', 0),
                'sentiment_recommendation': sentiment_summary.get('recommendation', 'HOLD'),
                
                # Prediction
                'prediction_score': prediction_score,
                'recommendation': self._get_recommendation(prediction_score),
                'confidence': sentiment_summary.get('confidence', 0),
                
                'timestamp': datetime.now().isoformat()
            })
        
        # Sort by prediction score
        predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        return predictions
    
    def _calculate_prediction_score(self, sentiment_summary, price_info):
        """
        Calculate overall prediction score (-1 to 1)
        
        Enhanced algorithm combining:
        - News sentiment (weighted heavily with amplification)
        - Price momentum (recent change)
        - News volume (more articles = stronger signal)
        - Sentiment strength (strong positive/negative = higher confidence)
        """
        article_count = sentiment_summary.get('article_count', 0)
        avg_sentiment = sentiment_summary.get('avg_sentiment', 0)
        positive_count = sentiment_summary.get('positive_count', 0)
        negative_count = sentiment_summary.get('negative_count', 0)
        
        # Sentiment component (70% weight) - amplified for stronger signals
        if abs(avg_sentiment) > 0.3:
            # Strong sentiment - amplify it
            sentiment_score = avg_sentiment * 1.5 * 0.7
        else:
            sentiment_score = avg_sentiment * 0.7
        
        # Price momentum component (20% weight)
        price_change = price_info.get('change_percent', 0)
        # Normalize to -1 to 1 range (±5% is significant)
        price_momentum = max(min(price_change / 5, 1), -1) * 0.2
        
        # News volume boost (10% weight) - more articles = stronger signal
        if article_count >= 50:
            volume_boost = 0.1
        elif article_count >= 20:
            volume_boost = 0.08
        elif article_count >= 10:
            volume_boost = 0.05
        elif article_count >= 5:
            volume_boost = 0.03
        else:
            volume_boost = 0.01
        
        # Apply volume boost in direction of sentiment
        if avg_sentiment > 0:
            volume_boost = volume_boost
        elif avg_sentiment < 0:
            volume_boost = -volume_boost
        else:
            volume_boost = 0
        
        total_score = sentiment_score + price_momentum + volume_boost
        
        # Clamp to -1 to 1
        return max(min(total_score, 1), -1)
    
    def _get_recommendation(self, score):
        """Convert score to recommendation"""
        if score >= 0.5:
            return 'STRONG BUY'
        elif score >= 0.2:
            return 'BUY'
        elif score <= -0.5:
            return 'STRONG SELL'
        elif score <= -0.2:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _save_results(self):
        """Save all data to CSV files"""
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save news data
        if self.news_data:
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
                for n in self.news_data
            ])
            news_df.to_csv('data/news_analyzed.csv', index=False)
            print(f"  [OK] Saved {len(news_df)} articles to data/news_analyzed.csv")
        
        # Save predictions
        if self.predictions:
            pred_df = pd.DataFrame(self.predictions)
            pred_df.to_csv('data/predictions.csv', index=False)
            print(f"  [OK] Saved {len(pred_df)} predictions to data/predictions.csv")
        
        # Save stock prices
        if self.price_data:
            price_list = [v for v in self.price_data.values() if 'error' not in v]
            if price_list:
                price_df = pd.DataFrame(price_list)
                price_df.to_csv('data/stock_prices.csv', index=False)
                print(f"  [OK] Saved {len(price_df)} stock prices to data/stock_prices.csv")
    
    def _print_summary(self):
        """Print pipeline summary"""
        print("\n" + "=" * 80)
        print(" [SUMMARY] PIPELINE SUMMARY")
        print("=" * 80 + "\n")
        
        print(f"[NEWS] Articles Analyzed:       {len(self.news_data)}")
        print(f"[PRICE] Stock Prices Fetched:   {len(self.price_data)}")
        print(f"[PRED] Predictions Generated:   {len(self.predictions)}")
        
        # Show top recommendations
        if self.predictions:
            print("\n" + "-" * 80)
            print("[TOP 10] RECOMMENDATIONS:")
            print("-" * 80)
            print(f"{'Rank':<6} {'Ticker':<8} {'Recommendation':<15} {'Score':<8} {'Price':<10} {'News'}")
            print("-" * 80)
            
            for i, pred in enumerate(self.predictions[:10], 1):
                print(f"{i:<6} {pred['ticker']:<8} {pred['recommendation']:<15} "
                      f"{pred['prediction_score']:>6.3f}   ${pred['current_price']:>7.2f}   "
                      f"{pred['news_count']} articles")
            
            print("\n" + "-" * 80)
            print("[BOTTOM 10] SELL CANDIDATES:")
            print("-" * 80)
            print(f"{'Rank':<6} {'Ticker':<8} {'Recommendation':<15} {'Score':<8} {'Price':<10} {'News'}")
            print("-" * 80)
            
            for i, pred in enumerate(self.predictions[-10:], 1):
                print(f"{i:<6} {pred['ticker']:<8} {pred['recommendation']:<15} "
                      f"{pred['prediction_score']:>6.3f}   ${pred['current_price']:>7.2f}   "
                      f"{pred['news_count']} articles")
        
        print("\n" + "=" * 80)
        print(" [DONE] PIPELINE COMPLETE!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    pipeline = StockPredictionPipeline()
    results = pipeline.run_complete_pipeline()
