@echo off
rem 작업 스케줄러용: 창·pause 없이 로컬 공공데이터 갱신을 돌리고 로그를 data\kr_fin_cache\local_daily_update.log 에 남긴다.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
if not exist data\kr_fin_cache mkdir data\kr_fin_cache
echo ===== %date% %time% ===== >> data\kr_fin_cache\local_daily_update.log
"C:\Users\forgo\AppData\Local\Programs\Python\Python310\python.exe" scripts\local_daily_update.py >> data\kr_fin_cache\local_daily_update.log 2>&1
