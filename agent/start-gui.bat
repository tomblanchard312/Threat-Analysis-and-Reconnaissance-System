@echo off
setlocal

echo.
echo ============================================================
echo   HTB Pentest Agent - GUI Launcher
echo ============================================================
echo.

:: Get the directory of this batch file
set "SCRIPT_DIR=%~dp0"

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
    echo      Starting Ollama...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo      Ollama is running
)

:: Check if model is registered
echo [3/3] Checking model registration...
ollama list 2>nul | findstr /C:"htb-pentest" >nul
if %ERRORLEVEL% neq 0 (
    echo      Registering htb-pentest model...
    cd /d "%SCRIPT_DIR%"
    ollama create htb-pentest -f Modelfile
) else (
    echo      Model htb-pentest is registered
)

echo.
echo ============================================================
echo   Starting GUI...
echo ============================================================
echo.

:: Run the GUI
cd /d "%SCRIPT_DIR%"
pythonw pentest-gui.py 2>nul || python pentest-gui.py
