@echo off
REM Background Service Manager for DBSBM Web Application
REM Easy batch file to manage web services

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if "%1"=="" (
    echo.
    echo ====================================================
    echo   DBSBM Background Service Manager
    echo ====================================================
    echo.
    echo Usage: %0 [command]
    echo.
    echo Commands:
    echo   start   - Start all web services in background
    echo   stop    - Stop all web services
    echo   restart - Restart all web services
    echo   status  - Show current service status
    echo   logs    - Show recent service logs
    echo.
    echo Examples:
    echo   %0 start
    echo   %0 status
    echo.
    goto :eof
)

if /i "%1"=="start" (
    echo Starting DBSBM web services...
    python background_service_manager.py start
) else if /i "%1"=="stop" (
    echo Stopping DBSBM web services...
    python background_service_manager.py stop
) else if /i "%1"=="restart" (
    echo Restarting DBSBM web services...
    python background_service_manager.py restart
) else if /i "%1"=="status" (
    python background_service_manager.py status
) else if /i "%1"=="logs" (
    echo.
    echo Recent service logs:
    echo ==================
    if exist "service_logs\service_manager_*.log" (
        for /f %%i in ('dir /b /o-d "service_logs\service_manager_*.log" 2^>nul') do (
            echo.
            echo Latest log file: %%i
            echo.
            type "service_logs\%%i" | findstr /v "GET /" | tail -20
            goto :done_logs
        )
    ) else (
        echo No log files found.
    )
    :done_logs
) else (
    echo Unknown command: %1
    echo Use "%0" without arguments to see usage help.
)
