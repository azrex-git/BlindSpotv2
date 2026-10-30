@echo off
chcp 65001 > nul
echo ========================================================
echo  Launching BlindSpot Flipkart Live Interactive Demo...
echo ========================================================
"%USERPROFILE%\.blindspot\venv\Scripts\python.exe" "%~dp0live_flipkart_demo.py"
pause
