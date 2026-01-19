@echo off
setlocal

echo ============================================
echo   HTB Pentest Agent - USB Deployment
echo ============================================
echo.

if "%~1"=="" (
    echo Usage: deploy-to-usb.bat [TARGET_DRIVE]
    echo.
    echo Examples:
    echo   deploy-to-usb.bat E:
    echo   deploy-to-usb.bat F: -IncludeModel
    echo.
    echo Options:
    echo   -IncludeModel    : Include the 4GB+ model file
    echo   -IncludeTraining : Include training code
    echo   -DownloadOllama  : Download fresh Ollama
    echo.
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0deploy-to-usb.ps1" -TargetDrive %*

pause
