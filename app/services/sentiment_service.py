"""
Sentiment analysis service - wraps existing sentiment logic
"""

import sys
import os
from typing import List, Dict, Optional

# Add parent directory to import existing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.sentiment_analyzer import SentimentAnalyzer as BaseSentimentAnalyzer


class SentimentService:
    """Service for sentiment analysis of news articles"""
    
    def __init__(self):
        self.analyzer = BaseSentimentAnalyzer()
    
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment of a single article
        
        Args:
            article: News article dictionary
            
        Returns:
            Article with sentiment data added
        """
        return self.analyzer.analyze_article(article)
    
    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for multiple articles
        
        Args:
            articles: List of news articles
            
        Returns:
            Articles with sentiment data added
        """
        return self.analyzer.analyze_batch(articles)
    
    def filter_relevant_impactful(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter to keep only relevant and impactful articles
        
        Args:
            articles: List of analyzed articles
            
        Returns:
            Filtered list of relevant articles
        """
        return self.analyzer.filter_relevant_impactful(articles)
    
    def get_stock_sentiment_summary(self, articles: List[Dict], ticker: str) -> Dict:
        """
        Get sentiment summary for a specific stock
        
        Args:
            articles: List of analyzed articles
            ticker: Stock ticker symbol
            
        Returns:
            Sentiment summary for the stock
        """
        return self.analyzer.get_stock_sentiment_summary(articles, ticker)
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of arbitrary text
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment scores
        """
        scores = self.analyzer.analyzer.polarity_scores(text)
        
        # Determine label
        compound = scores['compound']
        if compound >= 0.5:
            label = 'Very Positive'
        elif compound >= 0.05:
            label = 'Positive'
        elif compound <= -0.5:
            label = 'Very Negative'
        elif compound <= -0.05:
            label = 'Negative'
        else:
            label = 'Neutral'
        
        return {
            'compound': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'label': label,
        }
    
    def get_sentiment_distribution(self, articles: List[Dict]) -> Dict:
        """
        Get distribution of sentiment across articles
        
        Args:
            articles: List of analyzed articles
            
        Returns:
            Distribution statistics
        """
        if not articles:
            return {
                "total": 0,
                "very_positive": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "very_negative": 0,
                "average": 0,
            }
        
        sentiments = []
        for a in articles:
            if 'sentiment' in a and isinstance(a['sentiment'], dict):
                sentiments.append(a['sentiment'].get('compound', 0))
            elif 'sentiment_compound' in a:
                sentiments.append(a['sentiment_compound'])
        
        if not sentiments:
            return {
                "total": len(articles),
                "very_positive": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "very_negative": 0,
                "average": 0,
            }
        
        return {
            "total": len(sentiments),
            "very_positive": sum(1 for s in sentiments if s >= 0.5),
            "positive": sum(1 for s in sentiments if 0.05 <= s < 0.5),
            "neutral": sum(1 for s in sentiments if -0.05 < s < 0.05),
            "negative": sum(1 for s in sentiments if -0.5 < s <= -0.05),
            "very_negative": sum(1 for s in sentiments if s <= -0.5),
            "average": round(sum(sentiments) / len(sentiments), 3),
        }
