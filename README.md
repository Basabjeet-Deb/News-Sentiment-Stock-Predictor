# News Sentiment Stock Predictor - Distributed System

Distributed stock prediction system using news sentiment analysis on local network.

## Architecture

```
Master Node (Docker)          Worker Nodes (Local Network)
┌──────────────┐             ┌──────────────┐
│   Master     │◄────────────│   Worker 1   │
│  Port 8000   │             │  Port 5000   │
└──────────────┘             └──────────────┘
       ▲                     ┌──────────────┐
       └─────────────────────│   Worker 2   │
                             │  Port 5001   │
                             └──────────────┘
                             ┌──────────────┐
                             │   Worker 3   │
                             │  Port 5002   │
                             └──────────────┘
```

## Setup

### 1. Start Master (Docker)

```bash
docker-compose up -d
```

Master runs at `http://YOUR_IP:8000`

### 2. Start Workers (On Teammate Machines)

Each teammate runs:

```bash
# Set master IP
$env:MASTER_URL="http://192.168.1.100:8000"

# Start worker
python worker.py
```

Or with custom settings:

```bash
$env:MASTER_URL="http://192.168.1.100:8000"
$env:WORKER_ID="worker1"
$env:WORKER_PORT="5000"
python worker.py
```

### 3. Start Processing

```bash
curl -X POST http://YOUR_IP:8000/start
```

### 4. Get Results

```bash
curl http://YOUR_IP:8000/results
```

## API Endpoints

### Master Node

- `GET /` - Status
- `POST /register` - Worker registration
- `POST /start` - Start processing
- `GET /results` - Get all predictions
- `GET /results/{ticker}` - Get specific stock
- `GET /workers` - Worker status

### Worker Node

- `GET /` - Worker status
- `POST /process` - Process stocks (called by master)

## Stock Distribution

- Worker 1: 17 stocks (AAPL, AMD, AMZN, ...)
- Worker 2: 17 stocks (MCD, MMM, MSFT, ...)
- Worker 3: 16 stocks (NFLX, INTC, IBM, ...)

## Requirements

```bash
pip install -r requirements.txt
```

## Data Files

- `data/stock_prices.csv` - Stock price data
- `data/processed_news.csv` - Processed news with sentiment

## Troubleshooting

### Workers can't connect

1. Check master IP: `ipconfig` (Windows) or `ifconfig` (Linux)
2. Update `MASTER_URL` in worker
3. Check firewall allows port 8000

### No results

1. Check workers registered: `curl http://YOUR_IP:8000/workers`
2. Check master logs: `docker logs stock-master`
3. Ensure data files exist in `data/` folder
