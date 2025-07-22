@echo off
chcp 65001 >nul

echo ==================================
echo   LightReply Integrity Check
echo ==================================
echo.

set ERROR_COUNT=0

REM Check required files
echo Checking required files...
echo.

if not exist "LightReply.py" (
    echo [ERROR] Main program file LightReply.py is missing
    set /a ERROR_COUNT+=1
)

if not exist "config.json" (
    echo [INFO] config.json not found, will be created when program starts
    echo.
)

REM Check Python environment
echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    set /a ERROR_COUNT+=1
) else (
    for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
    echo [√] Python version: %PYTHON_VERSION%
)
echo.

REM Check required Python packages
echo Checking Python packages...
echo.

python -c "import mitmproxy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Not installed: mitmproxy
    set /a ERROR_COUNT+=1
) else (
    echo [√] mitmproxy installed
)

python -c "import ttkbootstrap" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Not installed: ttkbootstrap
    set /a ERROR_COUNT+=1
) else (
    echo [√] ttkbootstrap installed
)

python -c "import win32api" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Not installed: pywin32
    set /a ERROR_COUNT+=1
) else (
    echo [√] pywin32 installed
)
echo.

REM Check certificate
echo Checking mitmproxy certificate...
if exist "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer" (
    echo [√] mitmproxy certificate exists
) else (
    echo [!] mitmproxy certificate not found, please run setup.bat
)
echo.

REM Output check results
echo ==================================
if %ERROR_COUNT% gtr 0 (
    echo Check completed with %ERROR_COUNT% error^(s^)!
    echo Please run setup.bat to fix issues.
) else (
    echo Check completed successfully!
    echo The program is ready to run.
)
echo ==================================
echo.

pause
