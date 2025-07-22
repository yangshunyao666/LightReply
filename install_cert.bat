@echo off
chcp 65001 >nul

echo ==================================
echo   Install mitmproxy Certificate
echo ==================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script requires administrator privileges!
    echo Please run this script as administrator.
    echo.
    pause
    exit /b 1
)

REM Import certificate to trusted root certification authorities
echo Installing system certificate...
certutil -addstore root "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer"
if %errorlevel% neq 0 (
    echo [ERROR] Certificate installation failed!
    echo Please ensure the certificate file exists and has correct permissions.
    echo.
    pause
    exit /b 1
)

echo.
echo Certificate installed successfully!
echo Window will close in 3 seconds...
timeout /t 3
exit /b 0
