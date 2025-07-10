@echo off
echo 正在清理端口15008上的进程...

REM 查找并终止所有监听端口15008的进程
for /f "tokens=5" %%i in ('netstat -aon ^| findstr :15008 ^| findstr LISTENING') do (
    echo 正在终止进程 %%i
    taskkill /PID %%i /F 2>nul
)

echo 清理完成。
pause