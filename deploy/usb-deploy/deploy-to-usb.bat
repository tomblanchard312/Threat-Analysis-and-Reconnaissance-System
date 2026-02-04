@echo off
setlocal

echo ============================================
echo   HTB Pentest Agent - USB Deployment
echo ============================================
echo.

if "%~1"=="" (
    echo Usage: deploy-to-usb.bat [TARGET_DRIVE] [OPTIONS]
    echo.
    echo Examples:
    echo   deploy-to-usb.bat E:
    echo   deploy-to-usb.bat F: -ModelPath "C:\models\htb-pentest.gguf"
    echo   deploy-to-usb.bat G: -CleanDeploy
    echo.
    echo Options:
    echo   -ModelPath [path]  : Path to GGUF model file
    echo   -DownloadOllama    : Download fresh Ollama
    echo   -DownloadNodeJS    : Download portable Node.js for MCP servers
    echo   -SkipModel         : Skip model deployment
    echo   -CleanDeploy       : Remove existing files first
    echo.
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0deploy-to-usb.ps1" -TargetDrive %*

pause
