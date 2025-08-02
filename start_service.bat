@echo off
REM Flask Server Auto-Restart Service
REM This batch file runs the watchdog that keeps the Flask server alive

echo Starting Flask Auto-Restart Service...
echo This service will keep your Flask server running 24/7

cd /d "c:\Users\Administrator\Desktop\DBSBMWEB"

REM Create logs directory if it doesn't exist
if not exist "cgi-bin\db_logs" mkdir "cgi-bin\db_logs"

REM Log the start time
echo [%date% %time%] Starting Flask Watchdog Service >> cgi-bin\db_logs\service.log

REM Start the watchdog (this will restart itself if it fails)
:START_WATCHDOG
echo [%date% %time%] Starting watchdog process... >> cgi-bin\db_logs\service.log

"C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe" watchdog.py

REM If we get here, the watchdog exited - restart it
echo [%date% %time%] Watchdog exited unexpectedly, restarting in 5 seconds... >> cgi-bin\db_logs\service.log
timeout /t 5 /nobreak > nul
goto START_WATCHDOG
