@echo off
setlocal

echo.
echo ============================================================
echo   HTB Pentest Agent - GUI Launcher
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
if not exist "%AGENT_DIR%\pentest-gui.py" (
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

:: Check and install required packages
echo [1/3] Checking dependencies...

python -c "import requests" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Installing requests...
    pip install requests
)

python -c "import customtkinter" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Installing customtkinter...
    pip install customtkinter
)

:: Start Ollama if not running
echo [2/3] Checking Ollama...
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

:: Always rebuild model to pick up Modelfile changes
echo [3/3] Building model from Modelfile...
cd /d "%AGENT_DIR%"
"%OLLAMA_EXE%" create htb-pentest -f Modelfile
if %ERRORLEVEL% equ 0 (
    echo      Model htb-pentest is ready
) else (
    echo      [WARNING] Model build failed - using existing model if available
)

echo.
echo ============================================================
echo   Starting GUI...
echo ============================================================
echo.

:: Run the GUI
cd /d "%AGENT_DIR%"
pythonw pentest-gui.py 2>nul || python pentest-gui.py
