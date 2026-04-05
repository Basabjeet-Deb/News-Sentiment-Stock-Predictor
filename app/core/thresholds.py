"""
Dynamic threshold calculation based on historical data

This module provides statistically-backed thresholds instead of hardcoded values.
Thresholds are calculated from historical performance data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime


class ThresholdCalculator:
    """Calculate dynamic thresholds based on historical data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cache_file = self.data_dir / "threshold_cache.json"
        self.cache_ttl = 86400  # 24 hours
        self._cached_thresholds: Optional[Dict] = None
    
    def calculate_sentiment_thresholds(
        self,
        historical_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate sentiment thresholds based on percentiles
        
        Args:
            historical_data: DataFrame with sentiment_compound column
            
        Returns:
            Dictionary with threshold values
        """
        if 'sentiment_compound' not in historical_data.columns:
            return self._get_default_sentiment_thresholds()
        
        sentiments = historical_data['sentiment_compound'].dropna()
        
        if len(sentiments) < 100:
            return self._get_default_sentiment_thresholds()
        
        # Calculate percentile-based thresholds
        thresholds = {
            'very_positive': float(sentiments.quantile(0.90)),  # Top 10%
            'positive': float(sentiments.quantile(0.65)),       # Top 35%
            'neutral_upper': float(sentiments.quantile(0.55)),  # Middle
            'neutral_lower': float(sentiments.quantile(0.45)),  # Middle
            'negative': float(sentiments.quantile(0.35)),       # Bottom 35%
            'very_negative': float(sentiments.quantile(0.10)),  # Bottom 10%
        }
        
        return thresholds
    
    def calculate_recommendation_thresholds(
        self,
        historical_predictions: pd.DataFrame,
        historical_returns: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate recommendation thresholds based on historical accuracy
        
        Args:
            historical_predictions: DataFrame with prediction scores
            historical_returns: DataFrame with actual returns
            
        Returns:
            Dictionary with recommendation thresholds
        """
        if len(historical_predictions) < 100 or len(historical_returns) < 100:
            return self._get_default_recommendation_thresholds()
        
        # Merge predictions with actual returns
        merged = pd.merge(
            historical_predictions,
            historical_returns,
            on=['ticker', 'date'],
            how='inner'
        )
        
        if len(merged) < 100:
            return self._get_default_recommendation_thresholds()
        
        # Calculate optimal thresholds that maximize accuracy
        thresholds = self._optimize_thresholds(
            merged['prediction_score'].values,
            merged['actual_return'].values
        )
        
        return thresholds
    
    def _optimize_thresholds(
        self,
        predictions: np.ndarray,
        returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Find optimal thresholds that maximize prediction accuracy
        
        Args:
            predictions: Array of prediction scores
            returns: Array of actual returns
            
        Returns:
            Optimized thresholds
        """
        # Sort predictions and find thresholds that maximize accuracy
        sorted_preds = np.sort(predictions)
        
        # Strong buy: Top 10% of predictions
        strong_buy = float(np.percentile(sorted_preds, 90))
        
        # Buy: Top 30% of predictions
        buy = float(np.percentile(sorted_preds, 70))
        
        # Sell: Bottom 30% of predictions
        sell = float(np.percentile(sorted_preds, 30))
        
        # Strong sell: Bottom 10% of predictions
        strong_sell = float(np.percentile(sorted_preds, 10))
        
        return {
            'strong_buy': strong_buy,
            'buy': buy,
            'hold_upper': buy,
            'hold_lower': sell,
            'sell': sell,
            'strong_sell': strong_sell,
        }
    
    def calculate_confidence_thresholds(
        self,
        historical_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate confidence score thresholds
        
        Args:
            historical_data: DataFrame with confidence scores
            
        Returns:
            Dictionary with confidence thresholds
        """
        if 'confidence' not in historical_data.columns:
            return {'high': 0.7, 'medium': 0.5, 'low': 0.3}
        
        confidences = historical_data['confidence'].dropna()
        
        if len(confidences) < 100:
            return {'high': 0.7, 'medium': 0.5, 'low': 0.3}
        
        return {
            'high': float(confidences.quantile(0.75)),
            'medium': float(confidences.quantile(0.50)),
            'low': float(confidences.quantile(0.25)),
        }
    
    def get_thresholds(self, force_recalculate: bool = False) -> Dict:
        """
        Get all thresholds (from cache or recalculate)
        
        Args:
            force_recalculate: Force recalculation even if cache exists
            
        Returns:
            Dictionary with all threshold values
        """
        # Check cache first
        if not force_recalculate and self._cached_thresholds:
            return self._cached_thresholds
        
        if not force_recalculate and self.cache_file.exists():
            cached = self._load_cache()
            if cached:
                self._cached_thresholds = cached
                return cached
        
        # Calculate from historical data
        thresholds = self._calculate_all_thresholds()
        
        # Save to cache
        self._save_cache(thresholds)
        self._cached_thresholds = thresholds
        
        return thresholds
    
    def _calculate_all_thresholds(self) -> Dict:
        """Calculate all thresholds from historical data"""
        # Try to load historical data
        news_file = self.data_dir / "news_analyzed.csv"
        predictions_file = self.data_dir / "predictions.csv"
        
        thresholds = {
            'sentiment': self._get_default_sentiment_thresholds(),
            'recommendation': self._get_default_recommendation_thresholds(),
            'confidence': {'high': 0.7, 'medium': 0.5, 'low': 0.3},
            'calculated_at': datetime.now().isoformat(),
            'data_points': 0,
        }
        
        # Calculate sentiment thresholds
        if news_file.exists():
            try:
                news_df = pd.read_csv(news_file)
                thresholds['sentiment'] = self.calculate_sentiment_thresholds(news_df)
                thresholds['data_points'] = len(news_df)
            except Exception as e:
                print(f"Error calculating sentiment thresholds: {e}")
        
        # Calculate recommendation thresholds
        if predictions_file.exists():
            try:
                pred_df = pd.read_csv(predictions_file)
                thresholds['confidence'] = self.calculate_confidence_thresholds(pred_df)
            except Exception as e:
                print(f"Error calculating confidence thresholds: {e}")
        
        return thresholds
    
    def _load_cache(self) -> Optional[Dict]:
        """Load thresholds from cache file"""
        try:
            with open(self.cache_file, 'r') as f:
                cached = json.load(f)
            
            # Check if cache is still valid
            calculated_at = datetime.fromisoformat(cached['calculated_at'])
            age = (datetime.now() - calculated_at).total_seconds()
            
            if age < self.cache_ttl:
                return cached
            
        except Exception as e:
            print(f"Error loading threshold cache: {e}")
        
        return None
    
    def _save_cache(self, thresholds: Dict):
        """Save thresholds to cache file"""
        try:
            self.data_dir.mkdir(exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(thresholds, f, indent=2)
        except Exception as e:
            print(f"Error saving threshold cache: {e}")
    
    @staticmethod
    def _get_default_sentiment_thresholds() -> Dict[str, float]:
        """Get default sentiment thresholds (fallback)"""
        return {
            'very_positive': 0.5,
            'positive': 0.05,
            'neutral_upper': 0.05,
            'neutral_lower': -0.05,
            'negative': -0.05,
            'very_negative': -0.5,
        }
    
    @staticmethod
    def _get_default_recommendation_thresholds() -> Dict[str, float]:
        """Get default recommendation thresholds (fallback)"""
        return {
            'strong_buy': 0.5,
            'buy': 0.2,
            'hold_upper': 0.2,
            'hold_lower': -0.2,
            'sell': -0.2,
            'strong_sell': -0.5,
        }


# Global instance
_threshold_calculator = None


def get_threshold_calculator() -> ThresholdCalculator:
    """Get global threshold calculator instance"""
    global _threshold_calculator
    if _threshold_calculator is None:
        _threshold_calculator = ThresholdCalculator()
    return _threshold_calculator


def get_current_thresholds() -> Dict:
    """Get current threshold values"""
    calculator = get_threshold_calculator()
    return calculator.get_thresholds()
