"""
Master Node - Distributed Stock Prediction Pipeline
Distributes tasks to slave nodes and aggregates results
"""

import sys
import os
import socket
import pickle
import json
import time
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class MasterNode:
    """Master node that distributes work to slaves"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.slaves = []
        self.results = {
            'news': [],
            'prices': {},
            'predictions': []
        }
        
    def start_server(self):
        """Start master server and wait for slave connections"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        print("=" * 80)
        print(f"[MASTER] Server started on {self.host}:{self.port}")
        print(f"[MASTER] Waiting for slave nodes to connect...")
        print("=" * 80)
        
        return server
    
    def register_slaves(self, server, num_slaves=3, timeout=30):
        """Wait for slave nodes to register"""
        server.settimeout(timeout)
        start_time = time.time()
        
        while len(self.slaves) < num_slaves:
            try:
                if time.time() - start_time > timeout:
                    print(f"[MASTER] Timeout waiting for slaves. Got {len(self.slaves)}/{num_slaves}")
                    break
                    
                conn, addr = server.accept()
                slave_id = len(self.slaves) + 1
                self.slaves.append({
                    'id': slave_id,
                    'conn': conn,
                    'addr': addr,
                    'status': 'connected'
                })
                print(f"[MASTER] Slave {slave_id} connected from {addr}")
                
                # Send slave ID
                conn.send(pickle.dumps({'slave_id': slave_id}))
                
            except socket.timeout:
                print(f"[MASTER] Timeout. Proceeding with {len(self.slaves)} slaves")
                break
        
        print(f"[MASTER] Total slaves registered: {len(self.slaves)}")
        return len(self.slaves) > 0
    
    def distribute_work(self):
        """Distribute stock analysis work to slaves"""
        if not self.slaves:
            print("[MASTER] No slaves available. Running in standalone mode.")
            return self.run_standalone()
        
        print("\n" + "=" * 80)
        print("[MASTER] DISTRIBUTING WORK TO SLAVES")
        print("=" * 80)
        
        # Split stocks among slaves
        all_stocks = config.STOCK_TICKERS
        chunk_size = len(all_stocks) // len(self.slaves)
        
        tasks = []
        for i, slave in enumerate(self.slaves):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < len(self.slaves) - 1 else len(all_stocks)
            stock_chunk = all_stocks[start_idx:end_idx]
            
            task = {
                'task_type': 'analyze_stocks',
                'stocks': stock_chunk,
                'slave_id': slave['id']
            }
            tasks.append(task)
            
            print(f"[MASTER] Assigning {len(stock_chunk)} stocks to Slave {slave['id']}")
            
            # Send task to slave
            try:
                slave['conn'].send(pickle.dumps(task))
                slave['status'] = 'working'
            except Exception as e:
                print(f"[MASTER] Error sending task to Slave {slave['id']}: {e}")
                slave['status'] = 'error'
        
        return tasks
    
    def collect_results(self):
        """Collect results from all slaves"""
        print("\n" + "=" * 80)
        print("[MASTER] COLLECTING RESULTS FROM SLAVES")
        print("=" * 80)
        
        for slave in self.slaves:
            if slave['status'] != 'working':
                continue
            
            try:
                print(f"[MASTER] Waiting for results from Slave {slave['id']}...")
                
                # Receive result
                data = b''
                while True:
                    chunk = slave['conn'].recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if len(chunk) < 4096:
                        break
                
                result = pickle.loads(data)
                
                # Aggregate results
                if 'news' in result:
                    self.results['news'].extend(result['news'])
                if 'prices' in result:
                    self.results['prices'].update(result['prices'])
                if 'predictions' in result:
                    self.results['predictions'].extend(result['predictions'])
                
                print(f"[MASTER] Received results from Slave {slave['id']}")
                print(f"         News: {len(result.get('news', []))} articles")
                print(f"         Prices: {len(result.get('prices', {}))} stocks")
                print(f"         Predictions: {len(result.get('predictions', []))} stocks")
                
                slave['status'] = 'completed'
                
            except Exception as e:
                print(f"[MASTER] Error receiving from Slave {slave['id']}: {e}")
                slave['status'] = 'error'
    
    def save_results(self):
        """Save aggregated results to CSV files"""
        print("\n" + "=" * 80)
        print("[MASTER] SAVING AGGREGATED RESULTS")
        print("=" * 80)
        
        os.makedirs('../data', exist_ok=True)
        
        # Save news
        if self.results['news']:
            news_df = pd.DataFrame(self.results['news'])
            news_df.to_csv('../data/news_analyzed.csv', index=False)
            print(f"[MASTER] Saved {len(news_df)} news articles")
        
        # Save prices
        if self.results['prices']:
            prices_list = [v for v in self.results['prices'].values() if 'error' not in v]
            if prices_list:
                prices_df = pd.DataFrame(prices_list)
                prices_df.to_csv('../data/stock_prices.csv', index=False)
                print(f"[MASTER] Saved {len(prices_df)} stock prices")
        
        # Save predictions
        if self.results['predictions']:
            pred_df = pd.DataFrame(self.results['predictions'])
            pred_df.to_csv('../data/predictions.csv', index=False)
            print(f"[MASTER] Saved {len(pred_df)} predictions")
    
    def run_standalone(self):
        """Run pipeline without slaves (fallback mode)"""
        print("\n[MASTER] Running in STANDALONE mode (no slaves)")
        
        # Import and run regular pipeline
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.run_pipeline import StockPredictionPipeline
        
        pipeline = StockPredictionPipeline()
        results = pipeline.run_complete_pipeline()
        
        return results
    
    def shutdown(self):
        """Close all slave connections"""
        print("\n[MASTER] Shutting down...")
        for slave in self.slaves:
            try:
                slave['conn'].send(pickle.dumps({'command': 'shutdown'}))
                slave['conn'].close()
            except:
                pass
        print("[MASTER] All connections closed")
    
    def run(self, num_slaves=3, wait_timeout=30):
        """Main execution flow"""
        print("\n" + "=" * 80)
        print(" DISTRIBUTED STOCK PREDICTION PIPELINE - MASTER NODE")
        print("=" * 80)
        print(f"[MASTER] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[MASTER] Expecting {num_slaves} slave nodes")
        print("=" * 80)
        
        server = self.start_server()
        
        # Wait for slaves to connect
        if self.register_slaves(server, num_slaves, wait_timeout):
            # Distribute work
            self.distribute_work()
            
            # Collect results
            self.collect_results()
            
            # Save aggregated results
            self.save_results()
            
            # Print summary
            self.print_summary()
        else:
            print("[MASTER] No slaves connected. Running standalone...")
            self.run_standalone()
        
        # Cleanup
        self.shutdown()
        server.close()
        
        print("\n" + "=" * 80)
        print("[MASTER] PIPELINE COMPLETE")
        print("=" * 80)
    
    def print_summary(self):
        """Print execution summary"""
        print("\n" + "=" * 80)
        print("[MASTER] EXECUTION SUMMARY")
        print("=" * 80)
        
        for slave in self.slaves:
            status_icon = "✓" if slave['status'] == 'completed' else "✗"
            print(f"{status_icon} Slave {slave['id']}: {slave['status']}")
        
        print(f"\nTotal News Articles: {len(self.results['news'])}")
        print(f"Total Stock Prices: {len(self.results['prices'])}")
        print(f"Total Predictions: {len(self.results['predictions'])}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Master Node for Distributed Stock Prediction')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--slaves', type=int, default=3, help='Number of slave nodes to expect')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for slave connections (seconds)')
    
    args = parser.parse_args()
    
    master = MasterNode(port=args.port)
    master.run(num_slaves=args.slaves, wait_timeout=args.timeout)
