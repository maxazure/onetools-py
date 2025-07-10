@echo off
echo Starting OneTools React Frontend with npm...
echo.

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

echo Starting React development server with npm...
echo Frontend will be available at: http://localhost:3000
echo API configured for: http://192.168.31.129:15008
echo.
echo Press Ctrl+C to stop the server
echo.

set DISABLE_ESLINT_PLUGIN=true
set ESLINT_NO_DEV_ERRORS=true
set TSC_COMPILE_ON_ERROR=true
set SKIP_PREFLIGHT_CHECK=true

npm start