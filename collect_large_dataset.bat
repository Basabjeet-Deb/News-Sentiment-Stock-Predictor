@echo off
echo ======================================
echo LARGE DATASET COLLECTION
echo For Distributed Cluster Processing
echo ======================================
echo.

echo This will collect:
echo - 2 years of stock data for 50 companies
echo - 1 week of news from 16 categories
echo - Target: 2000+ news articles
echo - Target: 25,000+ stock records
echo.
echo Estimated time: 10-15 minutes
echo.
pause

echo.
echo [1/2] Fetching stock price data...
echo This may take 5-10 minutes...
python fetch_stock_prices.py

echo.
echo [2/2] Fetching news data...
echo This may take 5-10 minutes...
python fetch_news.py

echo.
echo ======================================
echo DATA COLLECTION COMPLETE!
echo ======================================
echo.
echo Check the 'data' folder for:
echo - stock_prices.csv (2 years, 50 stocks)
echo - gdelt_english_news.csv (1 week, 16 categories)
echo.
echo Next step: Process with distributed cluster
echo Run: docker-compose -f docker-compose-master.yml up
echo.
pause
