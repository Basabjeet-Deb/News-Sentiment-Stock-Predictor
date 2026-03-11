# Docker + Ngrok Setup Guide

## How to Run Master in Docker with Ngrok

### Step 1: Start Master in Docker
Open Terminal 1 and run:
```bash
start-docker-master.bat
```
OR manually:
```bash
docker-compose -f docker-compose-master.yml up --build
```

This will:
- Build the Docker image
- Start the master node container
- Expose port 5000 on localhost
- Master API available at http://localhost:5000

### Step 2: Start Ngrok Tunnel
Open Terminal 2 and run:
```bash
start-ngrok.bat
```
OR manually:
```bash
ngrok http 5000
```

This will:
- Create a public tunnel to localhost:5000
- Give you a public URL like: https://xxxxx.ngrok-free.dev
- Keep this terminal open!

### Step 3: Update Worker Configuration
Copy the ngrok URL from Terminal 2 and update `worker_node.py`:
```python
MASTER_URL = "https://your-ngrok-url.ngrok-free.dev"
```

### Step 4: Workers Connect
Your teammates run on their machines:
```bash
python worker_node.py
```

## Architecture

```
[Your Machine]
├── Docker Container (Master Node)
│   └── Port 5000 → localhost:5000
│
├── Ngrok Tunnel
│   └── localhost:5000 → https://xxxxx.ngrok-free.dev
│
└── Internet
    └── Worker 1 (Teammate 1) → connects to ngrok URL
    └── Worker 2 (Teammate 2) → connects to ngrok URL
    └── Worker 3 (Teammate 3) → connects to ngrok URL
```

## Useful Commands

### Check if Docker is running:
```bash
docker ps
```

### View master logs:
```bash
docker logs cluster-master
```

### Stop master:
```bash
docker-compose -f docker-compose-master.yml down
```

### Restart master:
```bash
docker-compose -f docker-compose-master.yml restart
```

### Access master API:
- Local: http://localhost:5000/api/workers
- Public: https://your-ngrok-url.ngrok-free.dev/api/workers

## Benefits of Docker + Ngrok

1. **Isolated Environment**: Master runs in clean container
2. **Easy Deployment**: One command to start everything
3. **Global Access**: Ngrok makes it accessible from anywhere
4. **Consistent Setup**: Same environment every time
5. **Easy Scaling**: Can add more containers if needed

## Troubleshooting

### Docker not starting?
- Make sure Docker Desktop is running
- Check if port 5000 is free: `netstat -ano | findstr :5000`

### Ngrok not connecting?
- Make sure master is running first (Terminal 1)
- Check if localhost:5000 is accessible: `curl http://localhost:5000/api/workers`

### Workers can't connect?
- Verify ngrok URL is correct in worker_node.py
- Make sure ngrok terminal is still open
- Check master logs: `docker logs cluster-master`
