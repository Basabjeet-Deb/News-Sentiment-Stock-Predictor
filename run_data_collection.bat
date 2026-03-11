@echo off
echo ======================================
echo Data Collection - Step 1
echo ======================================
echo.

echo Installing dependencies...
pip install -q yfinance requests pandas

echo.
echo [1/2] Fetching news data from GDELT...
python fetch_news.py

echo.
echo [2/2] Fetching stock price data...
python fetch_stock_prices.py

echo.
echo ======================================
echo Data Collection Complete!
echo ======================================
echo.
echo Check the 'data' folder for:
echo - gdelt_english_news.csv (news articles)
echo - stock_prices.csv (historical prices)
echo.
pause
