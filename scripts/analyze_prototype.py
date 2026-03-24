"""
Analyze prototype stocks with news sentiment
Generate predictions for demonstration
"""

import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import os
from config import TARGET_STOCKS, STOCK_NAMES, SENTIMENT_POSITIVE, SENTIMENT_NEGATIVE

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(news_df):
    """Analyze sentiment of news articles"""
    
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS")
    print("="*60)
    
    sentiments = []
    
    for idx, row in news_df.iterrows():
        title = str(row['title'])
        
        # Get sentiment scores
        scores = analyzer.polarity_scores(title)
        
        sentiments.append({
            'title': title,
            'ticker': row['ticker'],
            'compound': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        })
    
    sentiment_df = pd.DataFrame(sentiments)
    
    # Save sentiment analysis
    output_file = 'data/sentiment_analysis.csv'
    sentiment_df.to_csv(output_file, index=False)
    
    print(f"[OK] Analyzed {len(sentiment_df)} articles")
    print(f"Saved to: {output_file}")
    
    # Show sentiment distribution
    print("\nSentiment Distribution:")
    positive = len(sentiment_df[sentiment_df['compound'] > SENTIMENT_POSITIVE])
    negative = len(sentiment_df[sentiment_df['compound'] < SENTIMENT_NEGATIVE])
    neutral = len(sentiment_df) - positive - negative
    
    print(f"  Positive: {positive} ({positive/len(sentiment_df)*100:.1f}%)")
    print(f"  Negative: {negative} ({negative/len(sentiment_df)*100:.1f}%)")
    print(f"  Neutral: {neutral} ({neutral/len(sentiment_df)*100:.1f}%)")
    
    return sentiment_df


def generate_predictions(stock_df, sentiment_df):
    """Generate stock predictions based on data and sentiment"""
    
    print("\n" + "="*60)
    print("GENERATING PREDICTIONS")
    print("="*60)
    
    predictions = []
    
    for ticker in TARGET_STOCKS:
        try:
            # Get stock data
            ticker_data = stock_df[stock_df['Ticker'] == ticker].copy()
            
            if len(ticker_data) == 0:
                print(f"[WARN] {ticker}: No stock data")
                continue
            
            # Calculate technical indicators
            ticker_data['MA_7'] = ticker_data['Close'].rolling(window=7).mean()
            ticker_data['MA_30'] = ticker_data['Close'].rolling(window=30).mean()
            ticker_data['MA_90'] = ticker_data['Close'].rolling(window=90).mean()
            ticker_data['volatility'] = ticker_data['Close'].rolling(window=7).std()
            
            # Get latest data
            latest = ticker_data.iloc[-1]
            
            # Get sentiment for this stock
            ticker_sentiment = sentiment_df[sentiment_df['ticker'] == ticker]
            
            if len(ticker_sentiment) > 0:
                avg_sentiment = ticker_sentiment['compound'].mean()
                news_count = len(ticker_sentiment)
                
                # Sentiment classification
                if avg_sentiment > SENTIMENT_POSITIVE:
                    sentiment_label = "Positive"
                elif avg_sentiment < SENTIMENT_NEGATIVE:
                    sentiment_label = "Negative"
                else:
                    sentiment_label = "Neutral"
            else:
                avg_sentiment = 0.0
                news_count = 0
                sentiment_label = "No News"
            
            # Technical analysis
            ma_7 = latest['MA_7']
            ma_30 = latest['MA_30']
            ma_90 = latest['MA_90']
            
            # Price trend
            if pd.notna(ma_7) and pd.notna(ma_30):
                if ma_7 > ma_30:
                    trend = "Uptrend"
                    trend_score = 1
                else:
                    trend = "Downtrend"
                    trend_score = -1
            else:
                trend = "Insufficient Data"
                trend_score = 0
            
            # Combined prediction
            sentiment_factor = avg_sentiment * 2
            predicted_change = (trend_score * 0.5) + sentiment_factor
            
            # Recommendation
            if predicted_change > 0.3:
                recommendation = 'BUY'
                action_color = 'green'
            elif predicted_change < -0.3:
                recommendation = 'SELL'
                action_color = 'red'
            else:
                recommendation = 'HOLD'
                action_color = 'yellow'
            
            # Confidence calculation
            confidence = min(abs(predicted_change) * 0.5 + (news_count / 20), 1.0)
            
            # Price prediction (simple)
            current_price = latest['Close']
            predicted_price = current_price * (1 + predicted_change/100)
            
            predictions.append({
                'ticker': ticker,
                'company': STOCK_NAMES[ticker],
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'predicted_change_pct': round(predicted_change, 2),
                'trend': trend,
                'sentiment': sentiment_label,
                'sentiment_score': round(avg_sentiment, 3),
                'news_count': news_count,
                'confidence': round(confidence, 2),
                'recommendation': recommendation,
                'ma_7': round(ma_7, 2) if pd.notna(ma_7) else None,
                'ma_30': round(ma_30, 2) if pd.notna(ma_30) else None,
                'volatility': round(latest['volatility'], 2) if pd.notna(latest['volatility']) else None,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            print(f"[{ticker}] {recommendation} - Confidence: {confidence:.2f}")
        
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")
    
    # Save predictions
    predictions_df = pd.DataFrame(predictions)
    output_file = 'data/predictions.csv'
    predictions_df.to_csv(output_file, index=False)
    
    print(f"\n[OK] Generated {len(predictions)} predictions")
    print(f"Saved to: {output_file}")
    
    # Summary
    print("\nRecommendation Summary:")
    buy_count = len(predictions_df[predictions_df['recommendation'] == 'BUY'])
    sell_count = len(predictions_df[predictions_df['recommendation'] == 'SELL'])
    hold_count = len(predictions_df[predictions_df['recommendation'] == 'HOLD'])
    
    print(f"  BUY: {buy_count}")
    print(f"  SELL: {sell_count}")
    print(f"  HOLD: {hold_count}")
    
    return predictions_df


def main():
    print("="*60)
    print("PROTOTYPE STOCK ANALYSIS")
    print("="*60)
    
    # Load data
    try:
        stock_df = pd.read_csv('data/prototype_stocks.csv')
        print(f"[OK] Loaded {len(stock_df)} stock records")
    except Exception as e:
        print(f"[ERROR] Failed to load stock data: {e}")
        return
    
    try:
        news_df = pd.read_csv('data/prototype_news.csv')
        print(f"[OK] Loaded {len(news_df)} news articles")
    except Exception as e:
        print(f"[ERROR] Failed to load news data: {e}")
        return
    
    # Analyze sentiment
    sentiment_df = analyze_sentiment(news_df)
    
    # Generate predictions
    predictions_df = generate_predictions(stock_df, sentiment_df)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    print("  - data/sentiment_analysis.csv")
    print("  - data/predictions.csv")


if __name__ == "__main__":
    main()
