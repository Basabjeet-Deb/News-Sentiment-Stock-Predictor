"""
Sentiment Analyzer
Analyzes news sentiment using VADER and relevance filtering
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict
import re
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class SentimentAnalyzer:
    """Analyze sentiment of news articles with relevance filtering"""
    
    # Keywords that indicate impactful financial news
    IMPACT_KEYWORDS = {
        'high': ['earnings', 'revenue', 'profit', 'loss', 'bankruptcy', 'acquisition', 'merger', 
                 'lawsuit', 'scandal', 'fraud', 'investigation', 'SEC', 'FDA', 'approval', 'rejection',
                 'layoffs', 'hiring', 'expansion', 'shutdown', 'recall', 'upgrade', 'downgrade',
                 'dividend', 'stock split', 'buyback', 'IPO', 'delisting'],
        
        'medium': ['partnership', 'contract', 'deal', 'agreement', 'investment', 'funding',
                   'product launch', 'new product', 'innovation', 'patent', 'competitor',
                   'market share', 'growth', 'decline', 'forecast', 'guidance', 'outlook',
                   'rating', 'analyst', 'target price'],
        
        'macro': ['inflation', 'interest rate', 'federal reserve', 'GDP', 'unemployment',
                  'trade war', 'tariff', 'sanctions', 'war', 'military', 'defense spending',
                  'oil price', 'gold price', 'commodity', 'recession', 'bull market', 'bear market',
                  'market crash', 'rally', 'correction']
    }
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment and relevance of a single article
        
        Returns:
            Article with added sentiment scores and relevance flags
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        # Get VADER sentiment scores
        scores = self.analyzer.polarity_scores(text)
        
        # Determine relevance and impact
        relevance = self._calculate_relevance(article, text)
        impact_level = self._calculate_impact(text)
        
        # Add sentiment and relevance data
        article['sentiment'] = {
            'compound': scores['compound'],  # -1 to 1
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'label': self._get_sentiment_label(scores['compound']),
        }
        
        article['relevance'] = {
            'score': relevance,
            'is_relevant': relevance >= 0.3,  # Threshold for relevance
            'impact_level': impact_level,
            'is_impactful': impact_level in ['high', 'macro'],
        }
        
        return article
    
    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """Analyze multiple articles"""
        print(f"[*] Analyzing sentiment for {len(articles)} articles...")
        
        analyzed = []
        for article in articles:
            try:
                analyzed_article = self.analyze_article(article)
                analyzed.append(analyzed_article)
            except Exception as e:
                print(f"  Error analyzing article: {e}")
                continue
        
        print(f"[OK] Analyzed {len(analyzed)} articles")
        return analyzed
    
    def filter_relevant_impactful(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter to keep only relevant and impactful articles
        
        This ensures we only use news that actually matters for stock predictions
        """
        filtered = [
            article for article in articles
            if article.get('relevance', {}).get('is_relevant', False)
            or article.get('relevance', {}).get('is_impactful', False)
            or article.get('ticker', '')  # Keep if ticker is mentioned
        ]
        
        print(f"[FILTER] Filtered: {len(filtered)}/{len(articles)} relevant articles")
        return filtered
    
    def get_stock_sentiment_summary(self, articles: List[Dict], ticker: str) -> Dict:
        """
        Get sentiment summary for a specific stock
        
        Returns:
            Aggregate sentiment data for the stock
        """
        # Filter articles for this ticker
        stock_articles = [
            a for a in articles
            if a.get('ticker') == ticker or ticker in a.get('title', '').upper()
        ]
        
        if not stock_articles:
            return {
                'ticker': ticker,
                'article_count': 0,
                'avg_sentiment': 0,
                'recommendation': 'HOLD',
            }
        
        # Calculate average sentiment
        sentiments = [a['sentiment']['compound'] for a in stock_articles 
                     if 'sentiment' in a]
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Count sentiment types
        positive = sum(1 for s in sentiments if s > 0.05)
        negative = sum(1 for s in sentiments if s < -0.05)
        neutral = len(sentiments) - positive - negative
        
        # Generate recommendation
        recommendation = self._generate_recommendation(avg_sentiment, positive, negative)
        
        return {
            'ticker': ticker,
            'article_count': len(stock_articles),
            'avg_sentiment': avg_sentiment,
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'recommendation': recommendation,
            'confidence': self._calculate_confidence(len(stock_articles), sentiments),
            'recent_articles': stock_articles[:5],  # Most recent 5
        }
    
    def _calculate_relevance(self, article: Dict, text: str) -> float:
        """
        Calculate how relevant an article is to stock prediction
        
        Returns score 0-1
        """
        score = 0.0
        text_lower = text.lower()
        
        # Has stock ticker mentioned?
        if article.get('ticker'):
            score += 0.4
        
        # Has financial keywords?
        financial_keywords = ['stock', 'share', 'market', 'trading', 'investor', 
                             'wall street', 'nasdaq', 'dow', 's&p', 'price', 'equity']
        matches = sum(1 for kw in financial_keywords if kw in text_lower)
        score += min(matches * 0.1, 0.3)
        
        # Has impact keywords?
        all_impact_keywords = (self.IMPACT_KEYWORDS['high'] + 
                              self.IMPACT_KEYWORDS['medium'] + 
                              self.IMPACT_KEYWORDS['macro'])
        matches = sum(1 for kw in all_impact_keywords if kw in text_lower)
        score += min(matches * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _calculate_impact(self, text: str) -> str:
        """
        Determine impact level of news
        
        Returns: 'high', 'medium', 'macro', or 'low'
        """
        text_lower = text.lower()
        
        # Check high impact keywords
        high_matches = sum(1 for kw in self.IMPACT_KEYWORDS['high'] if kw in text_lower)
        if high_matches >= 1:
            return 'high'
        
        # Check macro impact keywords
        macro_matches = sum(1 for kw in self.IMPACT_KEYWORDS['macro'] if kw in text_lower)
        if macro_matches >= 1:
            return 'macro'
        
        # Check medium impact keywords
        medium_matches = sum(1 for kw in self.IMPACT_KEYWORDS['medium'] if kw in text_lower)
        if medium_matches >= 1:
            return 'medium'
        
        return 'low'
    
    def _get_sentiment_label(self, compound: float) -> str:
        """Convert compound score to label"""
        if compound >= 0.5:
            return 'Very Positive'
        elif compound >= 0.05:
            return 'Positive'
        elif compound <= -0.5:
            return 'Very Negative'
        elif compound <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
    
    def _generate_recommendation(self, avg_sentiment: float, positive: int, negative: int) -> str:
        """Generate buy/hold/sell recommendation"""
        if avg_sentiment >= 0.4 and positive > negative * 2:
            return 'STRONG BUY'
        elif avg_sentiment >= 0.15:
            return 'BUY'
        elif avg_sentiment <= -0.4 and negative > positive * 2:
            return 'STRONG SELL'
        elif avg_sentiment <= -0.15:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_confidence(self, article_count: int, sentiments: List[float]) -> float:
        """
        Calculate confidence in recommendation
        
        Based on number of articles and sentiment consistency
        """
        if article_count == 0:
            return 0.0
        
        # More articles = higher confidence (up to a point)
        volume_confidence = min(article_count / 20, 1.0)
        
        # Consistent sentiment = higher confidence
        if sentiments:
            avg = sum(sentiments) / len(sentiments)
            variance = sum((s - avg) ** 2 for s in sentiments) / len(sentiments)
            consistency_confidence = 1.0 - min(variance, 1.0)
        else:
            consistency_confidence = 0.0
        
        return (volume_confidence + consistency_confidence) / 2


if __name__ == "__main__":
    print("=" * 70)
    print("[TEST] SENTIMENT ANALYZER TEST")
    print("=" * 70 + "\n")
    
    analyzer = SentimentAnalyzer()
    
    # Test articles
    test_articles = [
        {
            'title': 'Apple Reports Record Earnings, Stock Surges',
            'description': 'Apple Inc exceeded earnings expectations with strong iPhone sales',
            'ticker': 'AAPL',
        },
        {
            'title': 'Tesla Faces Major Recall Over Safety Concerns',
            'description': 'Tesla recalls 2 million vehicles due to autopilot issues',
            'ticker': 'TSLA',
        },
        {
            'title': 'Gold Prices Rally on Inflation Fears',
            'description': 'Gold hits new highs as investors flee to safe havens',
            'ticker': '',
            'topics': ['gold'],
        },
    ]
    
    # Analyze
    analyzed = analyzer.analyze_batch(test_articles)
    
    print("[RESULTS] ANALYSIS RESULTS:\n")
    for article in analyzed:
        print(f"Title: {article['title']}")
        print(f"  Sentiment: {article['sentiment']['label']} ({article['sentiment']['compound']:.3f})")
        print(f"  Impact: {article['relevance']['impact_level'].upper()}")
        relevant_mark = "[YES]" if article['relevance']['is_relevant'] else "[NO]"
        print(f"  Relevant: {relevant_mark}")
        print()
    
    # Filter
    filtered = analyzer.filter_relevant_impactful(analyzed)
    print(f"[OK] {len(filtered)}/{len(analyzed)} articles are relevant/impactful")
