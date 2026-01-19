@echo off
:: Install Npcap driver for full nmap functionality
:: Must be run as Administrator

echo.
echo ============================================
echo   Npcap Driver Installer
echo ============================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "NPCAP_INSTALLER=%SCRIPT_DIR%npcap-installer.exe"

if not exist "%NPCAP_INSTALLER%" (
    echo [ERROR] Npcap installer not found!
    echo.
    echo Run download-tools.bat first to download it.
    echo Or download manually from: https://npcap.com/
    echo.
    pause
    exit /b 1
)

echo Installing Npcap...
echo.
echo This will enable:
echo   - SYN stealth scans (nmap -sS)
echo   - OS detection (nmap -O)
echo   - Raw packet capture
echo.

"%NPCAP_INSTALLER%"

echo.
echo ============================================
echo   Installation complete!
echo ============================================
echo.
echo Restart the HTB Pentest Agent to use full nmap features.
echo.
pause
