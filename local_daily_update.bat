@echo off
cd /d "%~dp0"
echo Starting moneyfinal local public-data update...
echo.
python scripts\local_daily_update.py
echo.
echo Done. Press any key to close this window.
pause >nul
