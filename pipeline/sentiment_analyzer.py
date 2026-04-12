"""
Advanced Sentiment Analyzer
- VADER sentiment analysis
- Intelligent relevance filtering
- Fuzzy duplicate detection
- Stock prediction relevance scoring
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict
from difflib import SequenceMatcher
import re
import sys
import os
from datetime import datetime
from math import exp

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from pipeline.article_prep import parse_article_datetime

class SentimentAnalyzer:
    """Advanced sentiment analyzer with relevance filtering and deduplication"""
    
    # Keywords that indicate impactful financial news
    IMPACT_KEYWORDS = {
        'high': ['earnings', 'revenue', 'profit', 'loss', 'bankruptcy', 'acquisition', 'merger', 
                 'lawsuit', 'scandal', 'fraud', 'investigation', 'SEC', 'FDA', 'approval', 'rejection',
                 'layoffs', 'hiring', 'expansion', 'shutdown', 'recall', 'upgrade', 'downgrade',
                 'dividend', 'stock split', 'buyback', 'IPO', 'delisting', 'CEO', 'CFO'],
        
        'medium': ['partnership', 'contract', 'deal', 'agreement', 'investment', 'funding',
                   'product launch', 'new product', 'innovation', 'patent', 'competitor',
                   'market share', 'growth', 'decline', 'forecast', 'guidance', 'outlook',
                   'rating', 'analyst', 'target price', 'quarterly', 'annual'],
        
        'macro': ['inflation', 'interest rate', 'federal reserve', 'fed', 'GDP', 'unemployment',
                  'trade war', 'tariff', 'sanctions', 'war', 'military', 'defense spending',
                  'oil price', 'gold price', 'commodity', 'recession', 'bull market', 'bear market',
                  'market crash', 'rally', 'correction', 'volatility', 'dow', 'nasdaq', 's&p 500',
                  'wall street', 'stock market', 'market sell-off', 'market rout', 'market turnaround',
                  'magnificent 7', 'mag 7', 'big tech', 'tech stocks', 'market losses', 'market gains',
                  'market uncertainty', 'economic downturn', 'economic growth', 'market sentiment']
    }
    
    # Irrelevant keywords (not about stocks/finance)
    IRRELEVANT_KEYWORDS = [
        'recipe', 'cooking', 'fashion', 'celebrity', 'entertainment', 'sports score',
        'weather', 'horoscope', 'dating', 'travel tips', 'movie review', 'music album',
        'video game', 'pokemon', 'betting', 'casino', 'lottery'
    ]
    
    def __init__(
        self,
        sentiment_backend: str = "vader",
        finbert_batch_size: int = 4,
        finbert_max_length: int = 128,
        sentiment_half_life_hours: float = 24.0,
    ):
        self.analyzer = SentimentIntensityAnalyzer()
        self.sentiment_backend = (sentiment_backend or "vader").lower().strip()
        self.finbert_batch_size = int(finbert_batch_size)
        self.finbert_max_length = int(finbert_max_length)
        self.sentiment_half_life_hours = float(sentiment_half_life_hours)

    def _apply_sentiment_and_relevance(
        self,
        article: Dict,
        text: str,
        compound: float,
        pos: float,
        neg: float,
        neu: float,
    ) -> Dict:
        relevance = self._calculate_relevance(article, text)
        impact_level = self._calculate_impact(text)
        is_irrelevant = self._is_irrelevant(text)

        article["sentiment_compound"] = compound
        article["sentiment_positive"] = pos
        article["sentiment_negative"] = neg
        article["sentiment_neutral"] = neu
        article["sentiment_label"] = self._get_sentiment_label(compound)

        article["relevance_score"] = relevance
        article["is_relevant"] = relevance >= 0.25 and not is_irrelevant
        article["impact_level"] = impact_level
        article["is_impactful"] = impact_level in ["high", "macro"]
        article["is_irrelevant"] = is_irrelevant
        article["sentiment_backend"] = self.sentiment_backend
        return article
        
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment and relevance of a single article
        
        Returns:
            Article with added sentiment scores and relevance flags
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        scores = self.analyzer.polarity_scores(text)
        return self._apply_sentiment_and_relevance(
            article,
            text,
            scores["compound"],
            scores["pos"],
            scores["neg"],
            scores["neu"],
        )
    
    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """Analyze multiple articles (VADER per-item, or batched FinBERT + release)."""
        print(f"\n[*] Analyzing sentiment for {len(articles)} articles (backend={self.sentiment_backend})...")

        if self.sentiment_backend == "finbert":
            analyzed = self._analyze_batch_finbert(articles)
        else:
            analyzed = []
            for article in articles:
                try:
                    analyzed.append(self.analyze_article(dict(article)))
                except Exception as e:
                    print(f"  Error analyzing article: {e}")
                    continue

        print(f"[OK] Analyzed {len(analyzed)} articles")
        return analyzed

    def _analyze_batch_finbert(self, articles: List[Dict]) -> List[Dict]:
        try:
            from pipeline.finbert_engine import (
                finbert_available,
                predict_sentiment_for_texts,
                release_finbert,
            )
        except ImportError as e:
            print(f"  FinBERT unavailable ({e}); falling back to VADER.")
            return [self.analyze_article(dict(a)) for a in articles]

        if not finbert_available():
            print("  torch/transformers not installed; falling back to VADER.")
            return [self.analyze_article(dict(a)) for a in articles]

        texts = [
            f"{a.get('title', '')} {a.get('description', '')}"[:2000]
            for a in articles
        ]
        analyzed: List[Dict] = []
        try:
            rows = predict_sentiment_for_texts(
                texts,
                batch_size=self.finbert_batch_size,
                max_length=self.finbert_max_length,
            )
        except Exception as e:
            print(f"  FinBERT inference failed ({e}); falling back to VADER.")
            return [self.analyze_article(dict(a)) for a in articles]
        finally:
            release_finbert()

        for article, text, row in zip(articles, texts, rows):
            try:
                compound, ppos, pneg, pneu = row
                a = dict(article)
                analyzed.append(
                    self._apply_sentiment_and_relevance(a, text, compound, ppos, pneg, pneu)
                )
            except Exception as e:
                print(f"  Error analyzing article: {e}")
                continue
        return analyzed
    
    def remove_duplicates_fuzzy(self, articles: List[Dict], similarity_threshold: float = 0.85) -> List[Dict]:
        """
        Remove duplicate articles using fuzzy string matching
        
        Args:
            similarity_threshold: 0-1, higher = more strict (0.85 = 85% similar)
        """
        print(f"\n[*] Removing duplicates (threshold: {similarity_threshold})...")
        
        unique_articles = []
        seen_titles = []
        duplicates_removed = 0
        
        for article in articles:
            title = article.get('title', '').lower().strip()
            
            if not title or len(title) < 10:
                continue
            
            # Check similarity with existing titles
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = SequenceMatcher(None, title, seen_title).ratio()
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    duplicates_removed += 1
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.append(title)
        
        print(f"[OK] Removed {duplicates_removed} duplicates, kept {len(unique_articles)} unique articles")
        return unique_articles
    
    def filter_relevant_impactful(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter to keep only relevant and impactful articles for stock prediction
        """
        print(f"\n[*] Filtering for relevance and impact...")
        
        filtered = [
            article for article in articles
            if (article.get('is_relevant', False) or 
                article.get('is_impactful', False) or 
                article.get('ticker', '') or  # Keep all articles with tickers
                article.get('relevance_score', 0) >= 0.25)  # Lower threshold from 0.3
            and not article.get('is_irrelevant', False)  # Remove irrelevant
        ]
        
        removed = len(articles) - len(filtered)
        print(f"[OK] Filtered: {len(filtered)}/{len(articles)} relevant articles ({removed} removed)")
        
        # Show breakdown
        high_impact = sum(1 for a in filtered if a.get('impact_level') == 'high')
        macro_impact = sum(1 for a in filtered if a.get('impact_level') == 'macro')
        with_ticker = sum(1 for a in filtered if a.get('ticker'))
        
        print(f"     High impact: {high_impact}, Macro: {macro_impact}, With ticker: {with_ticker}")
        
        return filtered
    
    def get_stock_sentiment_summary(self, articles: List[Dict], ticker: str) -> Dict:
        """
        Get sentiment summary for a specific stock
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
        
        sentiments = [float(a.get('sentiment_compound', 0) or 0) for a in stock_articles]
        now = datetime.now()
        half_life = max(self.sentiment_half_life_hours, 1e-6)

        weighted_sum = 0.0
        weight_total = 0.0
        for a, s in zip(stock_articles, sentiments):
            dt = parse_article_datetime(a)
            if dt is not None:
                if dt.tzinfo is not None:
                    dt = dt.astimezone().replace(tzinfo=None)
                age_h = max(0.0, (now - dt).total_seconds() / 3600.0)
            else:
                age_h = 0.0
            w = exp(-age_h / half_life)
            weighted_sum += w * s
            weight_total += w

        avg_sentiment = weighted_sum / weight_total if weight_total > 0 else 0.0
        
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
        Calculate how relevant an article is to stock prediction (0-1)
        """
        score = 0.0
        text_lower = text.lower()
        
        # Has stock ticker mentioned?
        if article.get('ticker'):
            score += 0.5  # Increased from 0.4 - if ticker is present, it's likely relevant
        
        # Check source - financial sources are automatically relevant
        source = article.get('source', '').lower()
        financial_sources = ['bloomberg', 'reuters', 'wall street', 'marketwatch', 
                            'seeking alpha', 'finviz', 'investing.com', 'yahoo finance',
                            'motley fool', 'zacks', 'barron', 'cnbc', 'financial times']
        if any(fs in source for fs in financial_sources):
            score += 0.3
        
        # Has financial keywords?
        financial_keywords = ['stock', 'share', 'market', 'trading', 'investor', 
                             'wall street', 'nasdaq', 'dow', 's&p', 'price', 'equity',
                             'portfolio', 'fund', 'etf', 'index', 'futures', 'options']
        matches = sum(1 for kw in financial_keywords if kw in text_lower)
        score += min(matches * 0.1, 0.2)
        
        # Has impact keywords?
        all_impact_keywords = (self.IMPACT_KEYWORDS['high'] + 
                              self.IMPACT_KEYWORDS['medium'] + 
                              self.IMPACT_KEYWORDS['macro'])
        matches = sum(1 for kw in all_impact_keywords if kw in text_lower)
        score += min(matches * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _is_irrelevant(self, text: str) -> bool:
        """Check if article is about non-financial topics"""
        text_lower = text.lower()
        
        # Check for irrelevant keywords
        for keyword in self.IRRELEVANT_KEYWORDS:
            if keyword in text_lower:
                return True
        
        return False
    
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
        Based on number of articles, sentiment consistency, and strength
        """
        if article_count == 0:
            return 0.0
        
        # More articles = higher confidence (logarithmic scale)
        if article_count >= 50:
            volume_confidence = 0.95
        elif article_count >= 20:
            volume_confidence = 0.85
        elif article_count >= 10:
            volume_confidence = 0.75
        elif article_count >= 5:
            volume_confidence = 0.65
        else:
            volume_confidence = 0.50
        
        # Sentiment strength and consistency
        if sentiments:
            avg = sum(sentiments) / len(sentiments)
            abs_avg = abs(avg)
            
            # Strong sentiment = higher confidence
            strength_confidence = min(abs_avg * 2, 1.0)
            
            # Consistent sentiment = higher confidence
            variance = sum((s - avg) ** 2 for s in sentiments) / len(sentiments)
            consistency_confidence = max(0, 1.0 - variance * 2)
            
            # Combine all factors
            final_confidence = (volume_confidence * 0.4 + 
                              strength_confidence * 0.4 + 
                              consistency_confidence * 0.2)
        else:
            final_confidence = volume_confidence * 0.5
        
        return min(final_confidence, 0.99)  # Cap at 99%


if __name__ == "__main__":
    print("=" * 70)
    print("[TEST] ADVANCED SENTIMENT ANALYZER TEST")
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
            'title': 'Apple Reports Record Earnings, Shares Surge',  # Duplicate
            'description': 'Apple exceeded earnings with strong iPhone sales',
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
        {
            'title': 'Best Pokemon Cards to Invest In',  # Irrelevant
            'description': 'Logan Paul sold a Pokemon card for millions',
            'ticker': '',
        },
    ]
    
    # Analyze
    analyzed = analyzer.analyze_batch(test_articles)
    
    # Remove duplicates
    unique = analyzer.remove_duplicates_fuzzy(analyzed)
    
    # Filter relevant
    filtered = analyzer.filter_relevant_impactful(unique)
    
    print("\n[RESULTS] FINAL FILTERED ARTICLES:\n")
    for article in filtered:
        print(f"Title: {article['title']}")
        print(f"  Sentiment: {article['sentiment_label']} ({article['sentiment_compound']:.3f})")
        print(f"  Impact: {article['impact_level'].upper()}")
        print(f"  Relevance: {article['relevance_score']:.2f}")
        print()
    
    print(f"\n[SUMMARY]")
    print(f"  Original: {len(test_articles)}")
    print(f"  After dedup: {len(unique)}")
    print(f"  After filter: {len(filtered)}")
    print(f"  Removed: {len(test_articles) - len(filtered)}")
