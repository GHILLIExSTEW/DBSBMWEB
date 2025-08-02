@echo off
echo Starting Flask Production Service...

cd /d "c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin"

REM Kill any existing Flask processes
taskkill /f /im python.exe 2>nul

REM Start Flask in production mode with Waitress
echo Starting Flask webapp with Waitress on port 25595...
"C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe" production_server.py

pause
