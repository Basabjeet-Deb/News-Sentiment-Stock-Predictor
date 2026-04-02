"""
Fix sentiment analysis for existing news data
"""
import pandas as pd
import sys
import os

# Add pipeline directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline'))

from sentiment_analyzer import SentimentAnalyzer

def fix_sentiment():
    """Re-analyze sentiment for existing news data"""
    
    print("=" * 70)
    print("FIXING SENTIMENT ANALYSIS")
    print("=" * 70)
    
    # Load existing news
    news_file = 'data/news_analyzed.csv'
    print(f"\n[*] Loading news from {news_file}...")
    
    try:
        df = pd.read_csv(news_file)
        print(f"[OK] Loaded {len(df)} articles")
    except Exception as e:
        print(f"[ERROR] Failed to load news: {e}")
        return
    
    # Convert to list of dicts
    articles = df.to_dict('records')
    
    # Initialize sentiment analyzer
    print("\n[*] Initializing sentiment analyzer...")
    analyzer = SentimentAnalyzer()
    
    # Re-analyze sentiment
    print("\n[*] Re-analyzing sentiment...")
    analyzed_articles = []
    
    for i, article in enumerate(articles, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(articles)} articles...")
        
        try:
            analyzed = analyzer.analyze_article(article)
            analyzed_articles.append(analyzed)
        except Exception as e:
            print(f"  Error analyzing article {i}: {e}")
            continue
    
    print(f"[OK] Analyzed {len(analyzed_articles)} articles")
    
    # Convert back to DataFrame
    df_analyzed = pd.DataFrame(analyzed_articles)
    
    # Show sentiment distribution
    print("\n[*] Sentiment Distribution:")
    print(f"  Positive: {sum(1 for a in analyzed_articles if a.get('sentiment_compound', 0) > 0.05)}")
    print(f"  Neutral: {sum(1 for a in analyzed_articles if -0.05 <= a.get('sentiment_compound', 0) <= 0.05)}")
    print(f"  Negative: {sum(1 for a in analyzed_articles if a.get('sentiment_compound', 0) < -0.05)}")
    
    # Show average sentiment
    avg_sentiment = df_analyzed['sentiment_compound'].mean()
    print(f"\n[*] Average Sentiment: {avg_sentiment:.3f}")
    
    # Save back to file
    output_file = 'data/news_analyzed.csv'
    print(f"\n[*] Saving to {output_file}...")
    
    # Keep only the original columns plus sentiment columns
    columns_to_keep = ['title', 'source', 'ticker', 'published_at', 
                       'sentiment_compound', 'sentiment_label', 
                       'impact_level', 'relevance_score', 'url']
    
    df_output = df_analyzed[columns_to_keep]
    df_output.to_csv(output_file, index=False)
    
    print(f"[OK] Saved {len(df_output)} articles with sentiment scores")
    print("\n" + "=" * 70)
    print("SENTIMENT ANALYSIS FIXED!")
    print("=" * 70)
    print("\nYou can now run the chatbot again to see proper sentiment analysis.")

if __name__ == "__main__":
    fix_sentiment()
