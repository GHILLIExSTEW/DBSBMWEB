@echo off
echo ====================================
echo VPS Migration Setup Script
echo ====================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)

echo.
echo Checking current directory...
cd /d "%~dp0"
echo Current directory: %CD%

echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies failed to install.
    echo Please check the output above for errors.
    pause
)

echo.
echo Checking .env file...
if exist "cgi-bin\.env" (
    echo ✅ .env file found in cgi-bin directory
) else (
    echo ❌ .env file not found! Please configure cgi-bin\.env
    echo See MIGRATION_CHECKLIST.md for details
)

echo.
echo Testing database connection...
cd cgi-bin
python test_database.py
cd ..

echo.
echo Testing Flask application (5 second test)...
timeout /t 5 /nobreak >nul
python flask_service.py test &
timeout /t 5 /nobreak >nul
taskkill /f /im python.exe >nul 2>&1

echo.
echo ====================================
echo Migration Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Configure .env file in cgi-bin directory
echo 2. Set up MySQL database
echo 3. Update Discord OAuth settings
echo 4. Test the application
echo.
echo Run: python flask_service.py test
echo For production: python flask_service.py service
echo.
pause
