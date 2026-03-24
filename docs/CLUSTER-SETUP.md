# College Cluster Setup Guide

Simple command distribution system for your college cluster.

## Architecture

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
              │ (5000)  │   │ (5000)  │   │ (5000)  │
              └─────────┘   └─────────┘   └─────────┘
```

## Setup Steps

### 1. On Master Node (One machine in cluster)

```bash
# Install dependencies
pip install fastapi uvicorn requests

# Start master
python cluster_master.py
```

Master will run on port 8000.

### 2. On Worker Nodes (All other machines)

Edit `cluster_worker.py` line 15:
```python
MASTER_URL = 'http://MASTER_IP:8000'  # Replace MASTER_IP
```

Then start worker:
```bash
# Install dependencies
pip install flask requests

# Start worker
python cluster_worker.py
```

Workers will automatically register with master.

### 3. On Your Machine (Client)

Edit `cluster_client.py` line 7:
```python
MASTER_URL = "http://MASTER_IP:8000"  # Replace MASTER_IP
```

## Usage

### Interactive Mode

```bash
python cluster_client.py
```

Commands:
- `workers` - List all connected workers
- `exec <command>` - Execute command on all workers
- `status <id>` - Check command status
- `quit` - Exit

### Command Line Mode

```bash
# Execute single command
python cluster_client.py ls -la

# Check system info
python cluster_client.py uname -a

# Check Python version
python cluster_client.py python --version

# Run Python script
python cluster_client.py python myscript.py
```

## Examples

### Example 1: Check all workers

```bash
python cluster_client.py
> workers

Output:
Total Workers: 3
  - node1 (192.168.1.101) - online
  - node2 (192.168.1.102) - online
  - node3 (192.168.1.103) - online
```

### Example 2: Execute command

```bash
python cluster_client.py
> exec hostname

Output:
[node1]
node1.college.edu

[node2]
node2.college.edu

[node3]
node3.college.edu
```

### Example 3: Run Python script

```bash
# From command line
python cluster_client.py python -c "print('Hello from cluster')"

Output:
[node1]
Hello from cluster

[node2]
Hello from cluster

[node3]
Hello from cluster
```

### Example 4: Check disk space

```bash
python cluster_client.py df -h
```

### Example 5: Install package on all nodes

```bash
python cluster_client.py pip install numpy
```

## API Endpoints

### Master (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Master status |
| `/register` | POST | Worker registration |
| `/execute` | POST | Execute command |
| `/command/{id}` | GET | Get command status |
| `/workers` | GET | List workers |
| `/results` | GET | Get all results |

### Worker (Port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Worker status |
| `/health` | GET | Health check |
| `/execute` | POST | Execute command |

## Configuration

### Master
- Port: 8000 (change in `cluster_master.py` line 195)

### Worker
- Port: 5000 (change in `cluster_worker.py` line 158)
- Master URL: Set `MASTER_URL` environment variable or edit line 15

### Client
- Master URL: Edit `cluster_client.py` line 7

## Environment Variables

### Worker
```bash
# Set master URL
export MASTER_URL=http://192.168.1.100:8000

# Set custom worker ID
export WORKER_ID=my-worker-1

# Start worker
python cluster_worker.py
```

## Troubleshooting

### Workers not connecting

1. Check master is running:
   ```bash
   curl http://MASTER_IP:8000
   ```

2. Check firewall allows port 8000 and 5000

3. Check worker logs for connection errors

### Commands not executing

1. Check workers are registered:
   ```bash
   curl http://MASTER_IP:8000/workers
   ```

2. Check command syntax is correct

3. Check worker has permissions to execute command

## Security Notes

⚠️ **WARNING**: This system executes arbitrary commands on workers.

- Only use on trusted networks
- Don't expose master to internet
- Consider adding authentication
- Validate commands before execution

## Advanced Usage

### Target Specific Worker

Edit `cluster_client.py` to add target parameter:

```python
command_id = send_command("ls -la", target="node1")
```

### Custom Timeout

Edit `cluster_worker.py` line 107 to change timeout:

```python
timeout=600  # 10 minutes
```

### Add Authentication

Add API key check in master and worker:

```python
API_KEY = "your-secret-key"

@app.route('/execute', methods=['POST'])
def execute_command():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    # ... rest of code
```

## Files

- `cluster_master.py` - Master node (FastAPI)
- `cluster_worker.py` - Worker node (Flask)
- `cluster_client.py` - Client interface
- `CLUSTER-SETUP.md` - This file

## Requirements

Master:
```
fastapi>=0.104.0
uvicorn>=0.24.0
requests>=2.31.0
```

Worker:
```
flask>=3.0.0
requests>=2.31.0
```

Client:
```
requests>=2.31.0
```
