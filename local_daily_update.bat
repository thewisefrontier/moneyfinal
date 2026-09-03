@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 머니파이널 로컬 공공데이터 갱신을 시작합니다...
echo.
python scripts\local_daily_update.py
echo.
echo 창을 닫으려면 아무 키나 누르세요.
pause >nul
