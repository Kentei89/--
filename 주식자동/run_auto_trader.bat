@echo off
cd /d "%~dp0"
echo [%date% %time%] 자동 매매 시작 >> data\auto_trader.log
python auto_trader.py
echo [%date% %time%] 자동 매매 완료 >> data\auto_trader.log
