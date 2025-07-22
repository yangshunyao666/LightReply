@echo off
chcp 65001
:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run
) else (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit
)

:run
echo Active code page: 65001
echo 注意！！！如果你没有遇到报错、闪退、功能异常等问题，不要使用此脚本！只适用于调试或获取错误信息！
echo 注意！！！如果你没有遇到报错、闪退、功能异常等问题，不要使用此脚本！只适用于调试或获取错误信息！
echo 注意！！！如果你没有遇到报错、闪退、功能异常等问题，不要使用此脚本！只适用于调试或获取错误信息！
echo 如果你确定遇到问题请按下回车键继续，否则请关闭此窗口并使用 start.bat 启动 LightReply！
pause

:: Check Python installation
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo Python is installed
) else (
    echo Python is not installed
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

:: Check required packages
echo.
echo Checking required packages...

python -c "import mitmproxy" >nul 2>&1
if %errorLevel% == 0 (
    echo mitmproxy: OK
) else (
    echo Installing mitmproxy...
    pip install mitmproxy
)

python -c "import ttkbootstrap" >nul 2>&1
if %errorLevel% == 0 (
    echo ttkbootstrap: OK
) else (
    echo Installing ttkbootstrap...
    pip install ttkbootstrap
)

python -c "import win32con" >nul 2>&1
if %errorLevel% == 0 (
    echo pywin32: OK
) else (
    echo Installing pywin32...
    pip install pywin32
)

echo.
echo Starting LightReply...
python "%~dp0LightReply.py"
pause
