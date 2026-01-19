@echo off
:: Stop the Kali Linux Docker container

echo.
echo ============================================
echo   Stopping Kali Linux Container
echo ============================================
echo.

docker stop htb-kali >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Kali container stopped
) else (
    echo [INFO] Container was not running
)

echo.
