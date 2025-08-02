@echo off
setlocal EnableDelayedExpansion

REM Ultra-Reliable Flask Auto-Restart Service
REM This will keep trying to start your Flask server no matter what

echo ========================================
echo  Flask Auto-Restart Service v2.0
echo  This service will NEVER give up!
echo ========================================

set PYTHON_EXE=C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe
set FLASK_SCRIPT=c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin\production_server.py
set WORKING_DIR=c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin
set CHECK_URL=http://localhost:25595/health
set LOG_FILE=c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin\db_logs\autostart.log

REM Create logs directory
if not exist "c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin\db_logs" (
    mkdir "c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin\db_logs"
)

:MAIN_LOOP
echo [%date% %time%] === Starting Flask Auto-Restart Loop === >> "%LOG_FILE%"
echo [%date% %time%] Starting Flask Server...

REM Kill any existing Python processes first
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start Flask server in background
start /b "" "%PYTHON_EXE%" "%FLASK_SCRIPT%"

REM Wait for server to start
echo [%date% %time%] Waiting for server to start... >> "%LOG_FILE%"
timeout /t 10 /nobreak >nul

:MONITOR_LOOP
REM Check if server is responding
curl -s -o nul -w "%%{http_code}" "%CHECK_URL%" > temp_status.txt 2>nul
set /p HTTP_STATUS=<temp_status.txt
del temp_status.txt 2>nul

if "!HTTP_STATUS!" == "200" (
    echo [%date% %time%] Server is healthy ^(HTTP 200^) >> "%LOG_FILE%"
    echo Server is healthy - monitoring...
) else (
    echo [%date% %time%] Server check failed ^(HTTP !HTTP_STATUS!^) - restarting >> "%LOG_FILE%"
    echo Server failed health check - restarting...
    goto RESTART_SERVER
)

REM Wait before next check
timeout /t 15 /nobreak >nul
goto MONITOR_LOOP

:RESTART_SERVER
echo [%date% %time%] Restarting server... >> "%LOG_FILE%"
taskkill /f /im python.exe >nul 2>&1
timeout /t 3 /nobreak >nul
goto MAIN_LOOP
