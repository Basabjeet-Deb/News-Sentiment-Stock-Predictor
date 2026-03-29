"""
Prediction service - generates stock predictions based on news sentiment
"""

import sys
import os
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Add parent directory to import existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import get_settings, STOCK_TICKERS, PREDICTION_WEIGHTS, RECOMMENDATION_THRESHOLDS
from app.services.sentiment_service import SentimentService


class PredictionService:
    """Service for generating stock predictions"""
    
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.settings = get_settings()
        self._cache: List[Dict] = []
        self._cache_timestamp: Optional[datetime] = None
    
    def generate_predictions(
        self,
        news_data: List[Dict],
        price_data: Dict[str, Dict],
        tickers: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Generate predictions for stocks
        
        Args:
            news_data: Analyzed news articles
            price_data: Current stock prices
            tickers: List of tickers to predict (defaults to all)
            
        Returns:
            List of prediction dictionaries
        """
        tickers = tickers or STOCK_TICKERS
        predictions = []
        
        for ticker in tickers:
            # Get sentiment for this stock
            sentiment_summary = self.sentiment_service.get_stock_sentiment_summary(
                news_data, ticker
            )
            
            # Get price data
            price_info = price_data.get(ticker, {})
            
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
                'prediction_score': round(prediction_score, 3),
                'recommendation': self._get_recommendation(prediction_score),
                'confidence': round(sentiment_summary.get('confidence', 0), 3),
                
                'timestamp': datetime.now().isoformat()
            })
        
        # Sort by prediction score
        predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        self._cache = predictions
        self._cache_timestamp = datetime.now()
        
        return predictions
    
    def _calculate_prediction_score(
        self,
        sentiment_summary: Dict,
        price_info: Dict
    ) -> float:
        """
        Calculate overall prediction score (-1 to 1)
        
        Combines:
        - News sentiment (weighted heavily)
        - Price momentum (recent change)
        - Number of articles (more = higher confidence)
        """
        # Sentiment component (60% weight)
        sentiment_score = sentiment_summary.get('avg_sentiment', 0) * PREDICTION_WEIGHTS['sentiment']
        
        # Price momentum component (30% weight)
        price_change = price_info.get('change_percent', 0)
        # Normalize to -1 to 1 range (assuming ±10% is extreme)
        price_momentum = max(min(price_change / 10, 1), -1) * PREDICTION_WEIGHTS['price_momentum']
        
        # Volume/confidence component (10% weight)
        article_count = sentiment_summary.get('article_count', 0)
        volume_boost = min(article_count / 20, 1) * PREDICTION_WEIGHTS['volume']
        
        total_score = sentiment_score + price_momentum + volume_boost
        
        # Clamp to -1 to 1
        return max(min(total_score, 1), -1)
    
    def _get_recommendation(self, score: float) -> str:
        """Convert score to recommendation"""
        if score >= RECOMMENDATION_THRESHOLDS['strong_buy']:
            return 'STRONG BUY'
        elif score >= RECOMMENDATION_THRESHOLDS['buy']:
            return 'BUY'
        elif score <= RECOMMENDATION_THRESHOLDS['sell']:
            return 'STRONG SELL'
        elif score <= RECOMMENDATION_THRESHOLDS['hold_lower']:
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_cached_predictions(self) -> List[Dict]:
        """Get cached predictions if available"""
        return self._cache
    
    def load_from_csv(self, filepath: str = None) -> List[Dict]:
        """
        Load predictions from CSV file
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of prediction dictionaries
        """
        filepath = filepath or self.settings.PREDICTIONS_CSV
        
        if not os.path.exists(filepath):
            return []
        
        try:
            df = pd.read_csv(filepath)
            # Replace NaN and inf for JSON compatibility
            df = df.replace([float('inf'), float('-inf')], None)
            df = df.fillna(0)
            predictions = df.to_dict('records')
            self._cache = predictions
            return predictions
        except Exception as e:
            print(f"Error loading predictions CSV: {e}")
            return []
    
    def filter_predictions(
        self,
        predictions: List[Dict],
        ticker: Optional[str] = None,
        sector: Optional[str] = None,
        recommendation: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        min_confidence: Optional[float] = None,
        min_news_count: Optional[int] = None,
        sort_by: str = "prediction_score",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Filter and sort predictions
        """
        filtered = predictions.copy()
        
        if ticker:
            filtered = [p for p in filtered if p.get('ticker', '').upper() == ticker.upper()]
        
        if sector:
            filtered = [p for p in filtered 
                       if sector.lower() in p.get('sector', '').lower()]
        
        if recommendation:
            filtered = [p for p in filtered 
                       if p.get('recommendation', '').upper() == recommendation.upper()]
        
        if min_score is not None:
            filtered = [p for p in filtered if p.get('prediction_score', 0) >= min_score]
        
        if max_score is not None:
            filtered = [p for p in filtered if p.get('prediction_score', 0) <= max_score]
        
        if min_confidence is not None:
            filtered = [p for p in filtered if p.get('confidence', 0) >= min_confidence]
        
        if min_news_count is not None:
            filtered = [p for p in filtered if p.get('news_count', 0) >= min_news_count]
        
        # Sort
        filtered.sort(key=lambda x: x.get(sort_by, 0), reverse=sort_desc)
        
        # Paginate
        return filtered[offset:offset + limit]
    
    def get_prediction_summary(self, predictions: List[Dict]) -> Dict:
        """
        Get summary statistics for predictions
        """
        if not predictions:
            return {
                "total_stocks": 0,
                "strong_buy_count": 0,
                "buy_count": 0,
                "hold_count": 0,
                "sell_count": 0,
                "strong_sell_count": 0,
                "avg_sentiment": 0,
                "avg_confidence": 0,
            }
        
        recommendations = [p.get('recommendation', 'HOLD') for p in predictions]
        sentiments = [p.get('avg_sentiment', 0) for p in predictions]
        confidences = [p.get('confidence', 0) for p in predictions]
        
        # Count by sector
        sectors = {}
        for p in predictions:
            sector = p.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = {'count': 0, 'avg_score': 0, 'scores': []}
            sectors[sector]['count'] += 1
            sectors[sector]['scores'].append(p.get('prediction_score', 0))
        
        for sector in sectors:
            scores = sectors[sector]['scores']
            sectors[sector]['avg_score'] = sum(scores) / len(scores) if scores else 0
            del sectors[sector]['scores']
        
        # Sort sectors by average score
        sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        return {
            "total_stocks": len(predictions),
            "strong_buy_count": recommendations.count('STRONG BUY'),
            "buy_count": recommendations.count('BUY'),
            "hold_count": recommendations.count('HOLD'),
            "sell_count": recommendations.count('SELL'),
            "strong_sell_count": recommendations.count('STRONG SELL'),
            "avg_sentiment": round(sum(sentiments) / len(sentiments), 3) if sentiments else 0,
            "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
            "top_sectors": [{"sector": s[0], **s[1]} for s in sorted_sectors[:5]],
            "bottom_sectors": [{"sector": s[0], **s[1]} for s in sorted_sectors[-5:]],
        }
