@echo off
cd /d "C:\Users\Basabjeet Deb\Desktop\Python\News Sentiment Based Stock Predictor"
python collect_missing_dates.py --today --run-pipeline >> logs\daily_update.log 2>&1
