# Distributed Stock Analysis Demo

Quick guide to demonstrate distributed computing with your college cluster.

## What This Does

Analyzes 10 stocks in parallel across multiple cluster nodes:
- Each worker processes stocks independently
- Results are collected and combined
- Shows distributed computing in action

## Quick Start

### 1. Start Master (One machine)

```bash
python cluster_master.py
```

Note the master IP (e.g., 192.168.1.100)

### 2. Start Workers (Other machines)

Edit `cluster_worker.py` line 15:
```python
MASTER_URL = 'http://192.168.1.100:8000'  # Your master IP
```

Then on each worker machine:
```bash
python cluster_worker.py
```

### 3. Setup Cluster (From your machine)

Edit `setup_cluster.py` and `distributed_analyze.py` line 8:
```python
MASTER_URL = "http://192.168.1.100:8000"  # Your master IP
```

Run setup:
```bash
python setup_cluster.py
```

### 4. Copy Data to Workers

Option A - Manual copy to each worker:
```bash
scp data/prototype_stocks.csv user@worker1:/path/to/data/
scp data/prototype_news.csv user@worker1:/path/to/data/
```

Option B - Use shared network storage (if available)

### 5. Run Distributed Analysis

```bash
python distributed_analyze.py
```

## What You'll See

```
DISTRIBUTED STOCK ANALYSIS
============================================================
Master URL: http://192.168.1.100:8000
Stocks to analyze: 10
============================================================

[OK] Found 3 workers
  - node1 (192.168.1.101) - online
  - node2 (192.168.1.102) - online
  - node3 (192.168.1.103) - online

[OK] Stock distribution:
  Worker 1: AAPL, MSFT, GOOGL, TSLA (4 stocks)
  Worker 2: AMZN, NVDA, META (3 stocks)
  Worker 3: JPM, V, WMT (3 stocks)

[SENDING] Analysis command to cluster...
[OK] Command ID: abc-123
[WAITING] Processing on cluster...

[OK] Received results from 3 workers

============================================================
PREDICTIONS
============================================================

[AAPL] Apple Inc.
  Current Price: $175.50
  Predicted Change: +1.20%
  Sentiment: +0.450 (15 articles)
  Confidence: 0.85
  Recommendation: BUY
  Processed by: node1

[MSFT] Microsoft Corporation
  Current Price: $380.25
  Predicted Change: +0.80%
  Sentiment: +0.320 (12 articles)
  Confidence: 0.75
  Recommendation: BUY
  Processed by: node1

...

============================================================
SUMMARY
============================================================
Total Stocks Analyzed: 10
BUY: 6
SELL: 1
HOLD: 3
Workers Used: 3

Saved to: data/distributed_predictions.csv
```

## For Presentation

### Show Distributed Computing

1. **Start with single machine:**
   ```bash
   python run_prototype.py
   ```
   Show it works but takes time.

2. **Then show distributed:**
   ```bash
   python distributed_analyze.py
   ```
   Show multiple workers processing in parallel.

3. **Compare results:**
   - Single machine: Sequential processing
   - Distributed: Parallel processing across cluster
   - Same results, faster execution

### Key Points to Highlight

✅ **Scalability**: Add more workers = faster processing  
✅ **Fault Tolerance**: If one worker fails, others continue  
✅ **Real Cluster**: Using actual college infrastructure  
✅ **Practical Application**: Stock analysis with real data  

## Architecture Diagram

```
Your Machine                College Cluster
┌─────────────┐            ┌──────────────┐
│   Client    │──command──>│    Master    │
│             │<──result───│  (Port 8000) │
└─────────────┘            └──────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌─────────┐   ┌─────────┐   ┌─────────┐
              │ Worker1 │   │ Worker2 │   │ Worker3 │
              │ AAPL    │   │ AMZN    │   │ JPM     │
              │ MSFT    │   │ NVDA    │   │ V       │
              │ GOOGL   │   │ META    │   │ WMT     │
              │ TSLA    │   │         │   │         │
              └─────────┘   └─────────┘   └─────────┘
```

## Troubleshooting

### Workers not connecting
- Check master is running: `curl http://MASTER_IP:8000`
- Check firewall allows ports 8000 and 5000
- Verify MASTER_URL is correct in worker code

### Data not found
- Ensure data files are copied to workers
- Check path: `data/prototype_stocks.csv` and `data/prototype_news.csv`
- Verify workers have read permissions

### Command timeout
- Increase timeout in `distributed_analyze.py` line 120
- Check worker logs for errors
- Ensure dependencies are installed on workers

## Files

- `cluster_master.py` - Master node
- `cluster_worker.py` - Worker node
- `cluster_client.py` - Command interface
- `distributed_analyze.py` - Distributed stock analysis
- `setup_cluster.py` - Cluster setup script
- `CLUSTER-SETUP.md` - Detailed cluster guide
- `DISTRIBUTED-DEMO.md` - This file

## Comparison

| Feature | Single Machine | Distributed |
|---------|---------------|-------------|
| Processing | Sequential | Parallel |
| Time | ~30 seconds | ~10 seconds |
| Scalability | Limited | Add more workers |
| Fault Tolerance | No | Yes |
| Complexity | Simple | Moderate |

## Demo Script

1. Show single machine version running
2. Explain limitations (sequential, slow for large datasets)
3. Show cluster setup (master + workers)
4. Run distributed version
5. Show results from multiple workers
6. Compare execution time
7. Explain how it scales with more stocks/workers
