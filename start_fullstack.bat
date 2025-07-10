@echo off
echo ===================================================
echo           OneTools Python Fullstack Startup
echo ===================================================
echo.

REM Check if we're in the right directory
if not exist "app\main.py" (
    echo ERROR: Please run this script from the onetools-py directory
    pause
    exit /b 1
)

echo [1/3] Starting Python API Server...

taskkill /F /IM python.exe

echo.
start "OneTools API" cmd /c "venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 15008 --reload"

echo Waiting for API to start...
timeout /t 5 >nul

echo [2/3] Testing API Connection...
curl -X GET "http://192.168.31.129:15008/health" --max-time 5 --silent --fail >nul
if %errorlevel% neq 0 (
    echo WARNING: API health check failed, but continuing...
) else (
    echo ✓ API is running successfully
)
echo.

echo [3/3] Starting React Frontend...
echo.
cd frontend

REM Kill any existing processes on port 3000
echo Checking for existing processes on port 3000...
netstat -ano | findstr :3000 > nul
if %errorlevel% equ 0 (
    echo Port 3000 is in use, terminating existing processes...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
        echo Killing process %%a
        taskkill /f /pid %%a > nul 2>&1
    )
    echo Waiting for processes to terminate...
    timeout /t 3 > nul
    echo Port 3000 freed successfully.
) else (
    echo Port 3000 is available.
)
echo.

start "OneTools Frontend" cmd /c "pnpm start"
cd ..

echo.
echo ===================================================
echo              🚀 OneTools is Starting! 🚀
echo ===================================================
echo.
echo Python API:      http://192.168.31.129:15008
echo API Documentation: http://192.168.31.129:15008/api/docs  
echo React Frontend:  http://localhost:3000 (starting...)
echo Test Interface: Open test_integration.html in browser
echo.
echo Press Ctrl+C in each window to stop the services
echo ===================================================
echo.

pause