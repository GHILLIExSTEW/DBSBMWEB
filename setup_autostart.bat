@echo off
REM Setup Windows Task Scheduler to auto-start Flask service on boot
REM This ensures the service starts automatically when Windows starts

echo Setting up Windows Task Scheduler for Flask Auto-Start...

REM Delete existing task if it exists
schtasks /delete /tn "FlaskAutoStart" /f 2>nul

REM Create new scheduled task
schtasks /create /tn "FlaskAutoStart" ^
    /tr "powershell.exe -ExecutionPolicy Bypass -File 'c:\Users\Administrator\Desktop\DBSBMWEB\service.ps1' -Action start" ^
    /sc onstart ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo ✅ Successfully created Windows scheduled task "FlaskAutoStart"
    echo ✅ Your Flask server will now auto-start when Windows boots
    echo.
    echo To manually control the service:
    echo   Start:   schtasks /run /tn "FlaskAutoStart"
    echo   Stop:    taskkill /f /im python.exe
    echo   Status:  powershell -File service.ps1 -Action status
) else (
    echo ❌ Failed to create scheduled task
    echo Please run this script as Administrator
)

pause
