@echo off
REM Usage: make_video.bat SP500 NVDA --start 2000-01-01
REM (use aliases SP500, NASDAQ, DOW, IPSA, ORO, BTC... — .bat files drop the "^" of ^GSPC)
REM All arguments go to fetch_data.py; then the MP4 is recorded with record_video.py
cd /d "%~dp0"
python fetch_data.py %*
if errorlevel 1 exit /b 1
python record_video.py
if errorlevel 1 exit /b 1
start "" fini_chart.mp4
