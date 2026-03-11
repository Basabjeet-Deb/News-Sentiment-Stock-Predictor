@echo off
echo ======================================
echo Adding Firewall Rule for Port 5000
echo ======================================
echo.
echo This requires Administrator privileges
echo Right-click this file and select "Run as administrator"
echo.
pause

netsh advfirewall firewall add rule name="Stock Prediction Master Port 5000" dir=in action=allow protocol=TCP localport=5000

echo.
echo ======================================
echo Firewall rule added successfully!
echo ======================================
echo.
echo Workers can now connect to:
echo http://192.168.1.2:5000
echo.
pause
