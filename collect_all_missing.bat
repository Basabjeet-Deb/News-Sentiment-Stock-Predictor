@echo off
echo ================================================================================
echo  COLLECTING ALL MISSING DATES (April 10-19, 2026)
echo ================================================================================
echo.

python collect_one_date.py 20260410
python collect_one_date.py 20260411
python collect_one_date.py 20260412
python collect_one_date.py 20260413
python collect_one_date.py 20260414
python collect_one_date.py 20260415
python collect_one_date.py 20260416
python collect_one_date.py 20260417
python collect_one_date.py 20260418
python collect_one_date.py 20260419

echo.
echo ================================================================================
echo  COLLECTION COMPLETE!
echo ================================================================================
echo.
pause
