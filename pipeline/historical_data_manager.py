"""
Historical Data Manager - Manages historical news data in batches by date
Stores past data for pattern recognition and adds new daily data
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd


class HistoricalDataManager:
    """Manages historical news data in date-batched JSON format"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(current_dir), "data")
        else:
            self.data_dir = data_dir
        
        self.historical_file = os.path.join(self.data_dir, "historical_news_batched.json")
        self.metadata_file = os.path.join(self.data_dir, "historical_metadata.json")
    
    def _load_historical_data(self) -> Dict:
        """Load existing historical data"""
        if os.path.exists(self.historical_file):
            with open(self.historical_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_batches": 0,
                "total_articles": 0,
                "date_range": {
                    "earliest": None,
                    "latest": None
                }
            },
            "batches": {}
        }
    
    def _save_historical_data(self, data: Dict):
        """Save historical data to JSON"""
        with open(self.historical_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_batch_key(self, date: datetime) -> str:
        """Get batch key for a date (format: YYYY-MM-DD)"""
        return date.strftime("%Y-%m-%d")
    
    def add_daily_batch(self, articles: List[Dict], date: datetime = None) -> Dict:
        """
        Add a daily batch of news articles
        
        Args:
            articles: List of analyzed news articles
            date: Date for this batch (defaults to today)
        
        Returns:
            Statistics about the addition
        """
        if date is None:
            date = datetime.now()
        
        batch_key = self._get_batch_key(date)
        
        print(f"\n[*] Adding daily batch for {batch_key}...")
        
        # Load existing data
        historical_data = self._load_historical_data()
        
        # Check if batch already exists
        if batch_key in historical_data["batches"]:
            print(f"[!] Batch for {batch_key} already exists")
            existing_count = len(historical_data["batches"][batch_key]["articles"])
            
            # Merge with existing (avoid duplicates)
            existing_titles = {a["title"] for a in historical_data["batches"][batch_key]["articles"]}
            new_articles = [a for a in articles if a.get("title") not in existing_titles]
            
            if new_articles:
                historical_data["batches"][batch_key]["articles"].extend(new_articles)
                historical_data["batches"][batch_key]["article_count"] += len(new_articles)
                historical_data["batches"][batch_key]["updated_at"] = datetime.now().isoformat()
                print(f"[*] Added {len(new_articles)} new articles to existing batch")
            else:
                print(f"[*] No new articles to add (all duplicates)")
                return {
                    "batch_date": batch_key,
                    "new_articles": 0,
                    "total_articles": existing_count,
                    "status": "no_new_articles"
                }
            
            new_article_count = len(new_articles)
        else:
            # Create new batch
            sentiment_stats = self._calculate_sentiment_stats(articles)
            
            historical_data["batches"][batch_key] = {
                "date": batch_key,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "article_count": len(articles),
                "sentiment_stats": sentiment_stats,
                "articles": articles
            }
            print(f"[*] Created new batch with {len(articles)} articles")
            new_article_count = len(articles)
        
        # Update metadata
        historical_data["metadata"]["last_updated"] = datetime.now().isoformat()
        historical_data["metadata"]["total_batches"] = len(historical_data["batches"])
        historical_data["metadata"]["total_articles"] = sum(
            batch["article_count"] for batch in historical_data["batches"].values()
        )
        
        # Update date range
        batch_dates = sorted(historical_data["batches"].keys())
        historical_data["metadata"]["date_range"]["earliest"] = batch_dates[0]
        historical_data["metadata"]["date_range"]["latest"] = batch_dates[-1]
        
        # Save
        self._save_historical_data(historical_data)
        
        stats = {
            "batch_date": batch_key,
            "new_articles": new_article_count,
            "total_articles": historical_data["batches"][batch_key]["article_count"],
            "total_batches": historical_data["metadata"]["total_batches"],
            "total_historical_articles": historical_data["metadata"]["total_articles"],
            "status": "success"
        }
        
        print(f"[OK] Batch added successfully")
        print(f"     Total batches: {stats['total_batches']}")
        print(f"     Total articles: {stats['total_historical_articles']}")
        
        return stats
    
    def _calculate_sentiment_stats(self, articles: List[Dict]) -> Dict:
        """Calculate sentiment statistics for a batch"""
        if not articles:
            return {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "avg_sentiment": 0
            }
        
        sentiments = [a.get("sentiment_compound", 0) for a in articles]
        
        positive = sum(1 for s in sentiments if s > 0.05)
        negative = sum(1 for s in sentiments if s < -0.05)
        neutral = len(sentiments) - positive - negative
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "avg_sentiment": round(avg_sentiment, 4),
            "positive_pct": round(positive / len(articles) * 100, 2),
            "negative_pct": round(negative / len(articles) * 100, 2),
            "neutral_pct": round(neutral / len(articles) * 100, 2)
        }
    
    def get_batch(self, date: datetime) -> Dict:
        """Get a specific batch by date"""
        batch_key = self._get_batch_key(date)
        historical_data = self._load_historical_data()
        return historical_data["batches"].get(batch_key)
    
    def get_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all articles within a date range"""
        historical_data = self._load_historical_data()
        
        articles = []
        current_date = start_date
        
        while current_date <= end_date:
            batch_key = self._get_batch_key(current_date)
            if batch_key in historical_data["batches"]:
                articles.extend(historical_data["batches"][batch_key]["articles"])
            current_date += timedelta(days=1)
        
        return articles
    
    def get_recent_days(self, days: int = 7) -> List[Dict]:
        """Get articles from the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.get_date_range(start_date, end_date)
    
    def get_all_historical_data(self) -> Dict:
        """Get all historical data"""
        return self._load_historical_data()
    
    def get_metadata(self) -> Dict:
        """Get metadata about historical data"""
        historical_data = self._load_historical_data()
        return historical_data["metadata"]
    
    def get_batch_summary(self) -> List[Dict]:
        """Get summary of all batches"""
        historical_data = self._load_historical_data()
        
        summaries = []
        for batch_key, batch_data in sorted(historical_data["batches"].items()):
            summaries.append({
                "date": batch_key,
                "article_count": batch_data["article_count"],
                "sentiment_stats": batch_data["sentiment_stats"],
                "created_at": batch_data["created_at"],
                "updated_at": batch_data["updated_at"]
            })
        
        return summaries
    
    def export_for_ml_training(self, output_file: str = None) -> str:
        """
        Export historical data in format suitable for ML training
        
        Returns:
            Path to exported CSV file
        """
        if output_file is None:
            output_file = os.path.join(self.data_dir, "ml_training_data.csv")
        
        print(f"\n[*] Exporting historical data for ML training...")
        
        historical_data = self._load_historical_data()
        
        # Flatten all articles
        all_articles = []
        for batch_key, batch_data in historical_data["batches"].items():
            for article in batch_data["articles"]:
                article_copy = article.copy()
                article_copy["batch_date"] = batch_key
                all_articles.append(article_copy)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_articles)
        
        # Select relevant columns for ML
        ml_columns = [
            "batch_date", "ticker", "title", "source",
            "sentiment_compound", "sentiment_label",
            "impact_level", "relevance_score",
            "published_at"
        ]
        
        # Keep only columns that exist
        available_columns = [col for col in ml_columns if col in df.columns]
        df_ml = df[available_columns]
        
        # Save to CSV
        df_ml.to_csv(output_file, index=False)
        
        print(f"[OK] Exported {len(df_ml)} articles to {output_file}")
        
        return output_file
    
    def print_summary(self):
        """Print summary of historical data"""
        metadata = self.get_metadata()
        
        print("\n" + "=" * 70)
        print("HISTORICAL DATA SUMMARY")
        print("=" * 70)
        print(f"Total Batches: {metadata['total_batches']}")
        print(f"Total Articles: {metadata['total_articles']}")
        print(f"Date Range: {metadata['date_range']['earliest']} to {metadata['date_range']['latest']}")
        print(f"Last Updated: {metadata['last_updated']}")
        
        # Show recent batches
        summaries = self.get_batch_summary()
        if summaries:
            print("\n" + "-" * 70)
            print("RECENT BATCHES (Last 10):")
            print("-" * 70)
            print(f"{'Date':<12} {'Articles':<10} {'Pos%':<8} {'Neg%':<8} {'Neu%':<8}")
            print("-" * 70)
            
            for summary in summaries[-10:]:
                stats = summary["sentiment_stats"]
                print(f"{summary['date']:<12} {summary['article_count']:<10} "
                      f"{stats['positive_pct']:<8.1f} {stats['negative_pct']:<8.1f} "
                      f"{stats['neutral_pct']:<8.1f}")
        
        print("=" * 70 + "\n")
    
    def cleanup_old_batches(self, keep_days: int = 365):
        """
        Remove batches older than specified days
        
        Args:
            keep_days: Number of days to keep (default: 365 = 1 year)
        """
        print(f"\n[*] Cleaning up batches older than {keep_days} days...")
        
        historical_data = self._load_historical_data()
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cutoff_key = self._get_batch_key(cutoff_date)
        
        # Find old batches
        old_batches = [key for key in historical_data["batches"].keys() if key < cutoff_key]
        
        if not old_batches:
            print("[*] No old batches to remove")
            return
        
        # Remove old batches
        for batch_key in old_batches:
            del historical_data["batches"][batch_key]
        
        # Update metadata
        historical_data["metadata"]["total_batches"] = len(historical_data["batches"])
        historical_data["metadata"]["total_articles"] = sum(
            batch["article_count"] for batch in historical_data["batches"].values()
        )
        
        if historical_data["batches"]:
            batch_dates = sorted(historical_data["batches"].keys())
            historical_data["metadata"]["date_range"]["earliest"] = batch_dates[0]
            historical_data["metadata"]["date_range"]["latest"] = batch_dates[-1]
        
        # Save
        self._save_historical_data(historical_data)
        
        print(f"[OK] Removed {len(old_batches)} old batches")
        print(f"     Remaining batches: {historical_data['metadata']['total_batches']}")


if __name__ == "__main__":
    # Test historical data manager
    manager = HistoricalDataManager()
    
    # Show current summary
    manager.print_summary()
    
    # Test adding today's data
    test_articles = [
        {
            "title": "Test Article 1",
            "ticker": "AAPL",
            "source": "Test Source",
            "sentiment_compound": 0.5,
            "sentiment_label": "Positive",
            "impact_level": "high",
            "relevance_score": 0.8,
            "published_at": datetime.now().isoformat()
        }
    ]
    
    stats = manager.add_daily_batch(test_articles)
    print(f"\nAdded batch: {stats}")
    
    # Show updated summary
    manager.print_summary()
