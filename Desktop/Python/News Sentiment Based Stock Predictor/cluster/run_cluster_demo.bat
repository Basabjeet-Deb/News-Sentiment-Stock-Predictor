@echo off
REM Distributed Stock Prediction Cluster - Demo Launcher
REM Runs master and 3 slaves on local machine

echo ========================================
echo  DISTRIBUTED STOCK PREDICTION CLUSTER
echo ========================================
echo.
echo Starting Master and 3 Slave nodes...
echo.

REM Start master in new window
start "Master Node" cmd /k "python master.py --slaves 3 --timeout 60"

REM Wait for master to start
timeout /t 3 /nobreak > nul

REM Start 3 slaves in new windows
start "Slave Node 1" cmd /k "python slave.py --master localhost --port 5000"
timeout /t 1 /nobreak > nul

start "Slave Node 2" cmd /k "python slave.py --master localhost --port 5000"
timeout /t 1 /nobreak > nul

start "Slave Node 3" cmd /k "python slave.py --master localhost --port 5000"

echo.
echo ========================================
echo All nodes started!
echo Check the individual windows for progress
echo ========================================
pause
