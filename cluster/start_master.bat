@echo off
echo ========================================
echo Starting Spark Master Node
echo ========================================
echo.
echo Master URL: spark://192.168.1.5:7077
echo Web UI: http://localhost:8080
echo.
echo Share with teammates: spark://192.168.1.5:7077
echo.
echo Keep this window open!
echo Press Ctrl+C to stop
echo ========================================
echo.

C:\spark\bin\spark-class.cmd org.apache.spark.deploy.master.Master --host 192.168.1.5 --port 7077 --webui-port 8080

pause
