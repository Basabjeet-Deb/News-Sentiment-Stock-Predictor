#!/bin/bash
# Distributed Stock Prediction Cluster - Demo Launcher
# Runs master and 3 slaves on local machine

echo "========================================"
echo " DISTRIBUTED STOCK PREDICTION CLUSTER"
echo "========================================"
echo ""
echo "Starting Master and 3 Slave nodes..."
echo ""

# Start master in background
python master.py --slaves 3 --timeout 60 &
MASTER_PID=$!
echo "Master started (PID: $MASTER_PID)"

# Wait for master to start
sleep 3

# Start 3 slaves in background
python slave.py --master localhost --port 5000 &
SLAVE1_PID=$!
echo "Slave 1 started (PID: $SLAVE1_PID)"
sleep 1

python slave.py --master localhost --port 5000 &
SLAVE2_PID=$!
echo "Slave 2 started (PID: $SLAVE2_PID)"
sleep 1

python slave.py --master localhost --port 5000 &
SLAVE3_PID=$!
echo "Slave 3 started (PID: $SLAVE3_PID)"

echo ""
echo "========================================"
echo "All nodes started!"
echo "Master PID: $MASTER_PID"
echo "Slave 1 PID: $SLAVE1_PID"
echo "Slave 2 PID: $SLAVE2_PID"
echo "Slave 3 PID: $SLAVE3_PID"
echo "========================================"
echo ""
echo "Waiting for completion..."

# Wait for master to finish
wait $MASTER_PID

echo ""
echo "Cluster execution complete!"
