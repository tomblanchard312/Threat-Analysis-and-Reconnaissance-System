@echo off
setlocal

echo.
echo ============================================================
echo   HTB Pentest Agent - CLI Launcher
echo ============================================================
echo.

:: Get the drive letter where this script is located
set "DRIVE_LETTER=%~d0"
set "AGENT_DIR=%DRIVE_LETTER%\agent"

:: Configure portable Ollama paths
set "OLLAMA_HOME=%DRIVE_LETTER%\Ollama"
set "OLLAMA_MODELS=%DRIVE_LETTER%\Ollama\models"
set "OLLAMA_EXE=%OLLAMA_HOME%\ollama.exe"

echo Drive: %DRIVE_LETTER%
echo OLLAMA_HOME: %OLLAMA_HOME%
echo.

:: Check if portable Ollama exists
if not exist "%OLLAMA_EXE%" (
    echo [ERROR] Portable Ollama not found at %OLLAMA_EXE%
    echo Please ensure Ollama is installed on this drive.
    pause
    exit /b 1
)

:: Check if agent directory exists
if not exist "%AGENT_DIR%\pentest-agent.py" (
    echo [ERROR] Agent not found at %AGENT_DIR%
    pause
    exit /b 1
)

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Check if requests is installed
python -c "import requests" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required package: requests
    pip install requests
)

:: Start Ollama if not running
echo [1/2] Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if %ERRORLEVEL% neq 0 (
    echo      Starting portable Ollama...
    start "" "%OLLAMA_EXE%" serve
    echo      Waiting for Ollama to start...
    :waitloop
    timeout /t 1 /nobreak >nul
    "%OLLAMA_EXE%" list >nul 2>&1
    if errorlevel 1 goto waitloop
    echo      Ollama is ready!
) else (
    echo      Ollama is running
)

:: Check if model is registered
echo [2/2] Checking model registration...
"%OLLAMA_EXE%" list 2>nul | findstr /C:"htb-pentest" >nul
if %ERRORLEVEL% neq 0 (
    echo      Registering htb-pentest model...
    cd /d "%AGENT_DIR%"
    "%OLLAMA_EXE%" create htb-pentest -f Modelfile
) else (
    echo      Model htb-pentest is registered
)

echo.
echo ============================================================
echo   Starting Pentest Agent...
echo ============================================================
echo.

:: Run the agent
cd /d "%AGENT_DIR%"
python pentest-agent.py

pause
