@echo off
chcp 65001 >nul

:: Try to run with admin privileges
if not "%1"=="am_admin" (
    powershell -Command "Start-Process -Verb RunAs -FilePath '%0' -ArgumentList 'am_admin'"
    exit /b
)

:: Check Python installation silently
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

::切换到脚本目录
cd /d "%~dp0"
:: Change to script directory
cd /d "%~dp0"

:: Check Python environment
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo Python is installed
) else (
    echo Error: Python is not detected. Please install Python 3.8 or higher
    pause
    exit
)

:: Check required packages
echo Checking required packages...
python -c "import mitmproxy" >nul 2>&1
if %errorLevel% == 1 (
    echo Installing mitmproxy...
    pip install mitmproxy
)

python -c "import ttkbootstrap" >nul 2>&1
if %errorLevel% == 1 (
    echo Installing ttkbootstrap...
    pip install ttkbootstrap
)

:: Run main program
echo Starting LightReply...
python LightReply.py

pause
