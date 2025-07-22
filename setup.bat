@echo off
chcp 65001 >nul

echo ==================================
echo   LightReply Setup Utility
echo ==================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check and install required Python packages
echo Installing required Python packages...
echo.

pip install mitmproxy
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install mitmproxy
    pause
    exit /b 1
)

pip install markdown
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install markdown
    pause
    exit /b 1
)

pip install ttkbootstrap
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install ttkbootstrap
    pause
    exit /b 1
)

pip install pywin32
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install pywin32
    pause
    exit /b 1
)

echo.
echo All Python packages installed successfully!
echo.

REM Generate and install certificate
echo Generating mitmproxy certificate...
start /B mitmdump --set ssl_insecure=true --set block_global=false -q
timeout /t 5 /nobreak >nul
taskkill /F /IM mitmdump.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Check if certificate file exists
if not exist "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer" (
    echo [ERROR] Failed to generate certificate
    echo Please try running 'mitmdump' manually first
    pause
    exit /b 1
)

echo.
echo Installing certificate (requires administrator privileges)...
echo.
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d ""%~dp0"" && ""%~dp0install_cert.bat""' -Verb RunAs"

echo.
echo Setup completed! Exiting...
timeout /t 3
exit /b 0
