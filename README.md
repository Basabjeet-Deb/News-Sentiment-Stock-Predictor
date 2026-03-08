# Distributed News Sentiment Analysis Cluster

A Python-based distributed computing system where a master node coordinates sentiment analysis tasks across multiple worker nodes.

## Architecture

```
┌─────────────────┐
│  Master Node    │ (You)
│  Port: 5000     │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│Worker1│ │Worker2│ │Worker3│ │Worker4│
│ 5000  │ │ 5000  │ │ 5000  │ │ 5000  │
└───────┘ └──────┘ └──────┘ └──────┘
(Teammates' machines)
```

## Setup Instructions

### For Master (You)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the master node:**
   ```bash
   start-master-local.bat
   ```
   Or directly:
   ```bash
   python master_node.py
   ```

3. **Access the dashboard:**
   - Open browser: http://localhost:5000
   - You'll see connected workers and processing status

4. **Share your IP with teammates:**
   - Share this URL: `http://192.168.1.2:5000`

### For Workers (Teammates)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update worker configuration:**
   - Open `worker_node.py`
   - Change line: `MASTER_URL = 'http://192.168.1.2:5000'`
   - Replace with actual master IP

3. **Start the worker node:**
   ```bash
   start-worker-local.bat
   ```
   Or directly:
   ```bash
   python worker_node.py
   ```

4. **Verify connection:**
   - Worker will automatically register with master
   - Check master dashboard to see your worker listed

## How It Works

1. **Master Node:**
   - Provides web dashboard at port 5000
   - Accepts worker registrations
   - Distributes news data to workers
   - Collects and aggregates results

2. **Worker Nodes:**
   - Register with master on startup
   - Send heartbeat every 10 seconds
   - Process sentiment analysis tasks
   - Submit results back to master

3. **Processing Flow:**
   - Master loads news data
   - Splits data into chunks
   - Distributes chunks to available workers
   - Workers analyze sentiment using VADER
   - Master aggregates results and displays statistics

## Usage

### Start Processing

1. Ensure workers are connected (check dashboard)
2. Click "Start Processing" on master dashboard
3. Watch results appear in real-time

### Monitor Cluster

- **Master Dashboard:** http://localhost:5000
- **Worker Status:** http://localhost:5000 (on worker machine)
- **View Logs:** Check terminal output

### Stop Nodes

Press `Ctrl+C` in the terminal running the node

## Data

Place your news data in `data/gdelt_english_news.csv`

If no data file exists, the system uses sample news headlines.

## Troubleshooting

### Workers can't connect to master

1. Check firewall settings - allow port 5000
2. Verify master IP address is correct
3. Ensure both machines are on same network
4. Check master is running: `docker ps`

### Worker shows as offline

1. Check worker logs: `docker-compose -f docker-compose-worker.yml logs`
2. Verify MASTER_URL is correct in worker_node.py
3. Restart worker: `docker-compose -f docker-compose-worker.yml restart`

### No results appearing

1. Check if workers are online in dashboard
2. Verify data file exists or sample data is being used
3. Check master logs for errors

## Network Requirements

- Master and workers must be on the same network (or have network connectivity)
- Port 5000 must be accessible on master machine
- Firewall must allow incoming connections on port 5000

## Commands Reference

```bash
# Build images
docker-compose -f docker-compose-master.yml build
docker-compose -f docker-compose-worker.yml build

# Start nodes
docker-compose -f docker-compose-master.yml up -d
docker-compose -f docker-compose-worker.yml up -d

# View logs
docker-compose -f docker-compose-master.yml logs -f
docker-compose -f docker-compose-worker.yml logs -f

# Stop nodes
docker-compose -f docker-compose-master.yml down
docker-compose -f docker-compose-worker.yml down

# Restart nodes
docker-compose -f docker-compose-master.yml restart
docker-compose -f docker-compose-worker.yml restart
```

## Features

- ✅ Real-time worker registration
- ✅ Automatic heartbeat monitoring
- ✅ Distributed sentiment analysis
- ✅ Web-based dashboard
- ✅ Result aggregation
- ✅ Task distribution
- ✅ Worker health monitoring

## Tech Stack

- **Python 3.11**
- **Flask** - Web framework
- **Docker** - Containerization
- **VADER** - Sentiment analysis
- **Pandas** - Data processing
