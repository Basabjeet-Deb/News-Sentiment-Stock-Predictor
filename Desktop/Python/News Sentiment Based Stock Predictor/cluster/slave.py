"""
Slave Node - Distributed Stock Prediction Pipeline
Receives tasks from master and processes assigned stocks
"""

import sys
import os
import socket
import pickle
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.enhanced_news_fetcher import EnhancedNewsFetcher
from scripts.sentiment_analyzer import SentimentAnalyzer
from scripts.stock_price_fetcher import StockPriceFetcher
import config


class SlaveNode:
    """Slave node that processes assigned work"""
    
    def __init__(self, master_host='localhost', master_port=5000):
        self.master_host = master_host
        self.master_port = master_port
        self.slave_id = None
        self.conn = None
        
        # Initialize services
        self.news_fetcher = EnhancedNewsFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.price_fetcher = StockPriceFetcher()
    
    def connect_to_master(self):
        """Connect to master node"""
        print("=" * 80)
        print(f"[SLAVE] Connecting to master at {self.master_host}:{self.master_port}")
        print("=" * 80)
        
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.master_host, self.master_port))
            
            # Receive slave ID from master
            data = self.conn.recv(4096)
            info = pickle.loads(data)
            self.slave_id = info['slave_id']
            
            print(f"[SLAVE {self.slave_id}] Connected successfully!")
            return True
            
        except Exception as e:
            print(f"[SLAVE] Connection failed: {e}")
            return False
    
    def process_task(self, task):
        """Process assigned task"""
        print(f"\n[SLAVE {self.slave_id}] Received task: {task['task_type']}")
        print(f"[SLAVE {self.slave_id}] Processing {len(task['stocks'])} stocks")
        print("=" * 80)
        
        results = {
            'news': [],
            'prices': {},
            'predictions': []
        }
        
        stocks = task['stocks']
        
        # Step 1: Fetch news for assigned stocks
        print(f"[SLAVE {self.slave_id}] Step 1: Fetching news...")
        try:
            # Fetch news for this subset of stocks
            raw_news = []
            for stock in stocks[:10]:  # Limit to avoid overwhelming
                try:
                    news = self.news_fetcher.fetch_stock_news(stock, max_articles=5)
                    raw_news.extend(news)
                except:
                    pass
            
            # Analyze sentiment
            analyzed_news = self.sentiment_analyzer.analyze_batch(raw_news)
            results['news'] = self.sentiment_analyzer.filter_relevant_impactful(analyzed_news)
            
            print(f"[SLAVE {self.slave_id}] Fetched {len(results['news'])} news articles")
        except Exception as e:
            print(f"[SLAVE {self.slave_id}] News fetch error: {e}")
        
        # Step 2: Fetch stock prices
        print(f"[SLAVE {self.slave_id}] Step 2: Fetching stock prices...")
        try:
            results['prices'] = self.price_fetcher.fetch_current_prices(stocks)
            print(f"[SLAVE {self.slave_id}] Fetched {len(results['prices'])} stock prices")
        except Exception as e:
            print(f"[SLAVE {self.slave_id}] Price fetch error: {e}")
        
        # Step 3: Generate predictions
        print(f"[SLAVE {self.slave_id}] Step 3: Generating predictions...")
        try:
            for ticker in stocks:
                sentiment_summary = self.sentiment_analyzer.get_stock_sentiment_summary(
                    results['news'], ticker
                )
                
                price_info = results['prices'].get(ticker, {})
                
                if 'error' not in price_info and price_info.get('price', 0) > 0:
                    prediction_score = self._calculate_prediction_score(
                        sentiment_summary, price_info
                    )
                    
                    results['predictions'].append({
                        'ticker': ticker,
                        'company_name': price_info.get('company_name', ticker),
                        'current_price': price_info.get('price', 0),
                        'price_change_percent': price_info.get('change_percent', 0),
                        'sector': price_info.get('sector', 'Unknown'),
                        'news_count': sentiment_summary.get('article_count', 0),
                        'avg_sentiment': sentiment_summary.get('avg_sentiment', 0),
                        'prediction_score': prediction_score,
                        'recommendation': self._get_recommendation(prediction_score),
                        'confidence': sentiment_summary.get('confidence', 0),
                        'timestamp': datetime.now().isoformat(),
                        'processed_by': f'slave_{self.slave_id}'
                    })
            
            print(f"[SLAVE {self.slave_id}] Generated {len(results['predictions'])} predictions")
        except Exception as e:
            print(f"[SLAVE {self.slave_id}] Prediction error: {e}")
        
        return results
    
    def _calculate_prediction_score(self, sentiment_summary, price_info):
        """Calculate prediction score"""
        sentiment_score = sentiment_summary.get('avg_sentiment', 0) * 0.6
        price_change = price_info.get('change_percent', 0)
        price_momentum = max(min(price_change / 10, 1), -1) * 0.3
        article_count = sentiment_summary.get('article_count', 0)
        volume_boost = min(article_count / 20, 1) * 0.1
        
        total_score = sentiment_score + price_momentum + volume_boost
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
    
    def send_results(self, results):
        """Send results back to master"""
        print(f"\n[SLAVE {self.slave_id}] Sending results to master...")
        try:
            data = pickle.dumps(results)
            self.conn.sendall(data)
            print(f"[SLAVE {self.slave_id}] Results sent successfully")
        except Exception as e:
            print(f"[SLAVE {self.slave_id}] Error sending results: {e}")
    
    def run(self):
        """Main execution flow"""
        print("\n" + "=" * 80)
        print(f" DISTRIBUTED STOCK PREDICTION PIPELINE - SLAVE NODE")
        print("=" * 80)
        print(f"[SLAVE] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Connect to master
        if not self.connect_to_master():
            print("[SLAVE] Failed to connect to master. Exiting.")
            return
        
        try:
            # Wait for task
            print(f"[SLAVE {self.slave_id}] Waiting for task from master...")
            data = self.conn.recv(8192)
            task = pickle.loads(data)
            
            if task.get('command') == 'shutdown':
                print(f"[SLAVE {self.slave_id}] Shutdown command received")
                return
            
            # Process task
            results = self.process_task(task)
            
            # Send results back
            self.send_results(results)
            
            print(f"\n[SLAVE {self.slave_id}] Work completed!")
            
        except Exception as e:
            print(f"[SLAVE {self.slave_id}] Error: {e}")
        
        finally:
            if self.conn:
                self.conn.close()
            print(f"[SLAVE {self.slave_id}] Connection closed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Slave Node for Distributed Stock Prediction')
    parser.add_argument('--master', type=str, default='localhost', help='Master node hostname/IP')
    parser.add_argument('--port', type=int, default=5000, help='Master node port')
    
    args = parser.parse_args()
    
    slave = SlaveNode(master_host=args.master, master_port=args.port)
    slave.run()
