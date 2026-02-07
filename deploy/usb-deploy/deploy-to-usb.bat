@echo off
setlocal

echo ============================================
echo   TARS - USB Deployment
echo ============================================
echo.

if "%~1"=="" (
    echo Usage: deploy-to-usb.bat [TARGET_DRIVE] [OPTIONS]
    echo.
    echo Examples:
    echo   deploy-to-usb.bat E:
    echo   deploy-to-usb.bat E: -DownloadNodeJS
    echo   deploy-to-usb.bat E: -LocalModel "C:\models\htb-pentest.gguf"
    echo   deploy-to-usb.bat E: -LocalOllama "C:\Program Files\Ollama"
    echo   deploy-to-usb.bat G: -CleanDeploy
    echo.
    echo Ollama and model are downloaded automatically by default.
    echo Use -LocalOllama / -LocalModel to copy from local paths instead.
    echo.
    echo Options:
    echo   -LocalOllama [path]  : Copy Ollama from local path instead of downloading
    echo   -LocalModel [path]   : Copy GGUF model from local path (for air-gapped use)
    echo   -DownloadNodeJS      : Download portable Node.js for MCP servers
    echo   -SkipOllama          : Skip Ollama setup (already on USB)
    echo   -SkipModel           : Skip model setup (already on USB)
    echo   -CleanDeploy         : Remove existing files first
    echo.
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0deploy-to-usb.ps1" -TargetDrive %*

pause
