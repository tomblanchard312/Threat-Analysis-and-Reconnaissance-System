@echo off
setlocal

:: Minimal launcher - GUI handles all startup tasks internally
:: This script just sets environment variables and launches Python quickly

:: Get the drive letter where this script is located
set "DRIVE_LETTER=%~d0"
set "AGENT_DIR=%DRIVE_LETTER%\agent"
set "OLLAMA_HOME=%DRIVE_LETTER%\Ollama"
set "OLLAMA_MODELS=%DRIVE_LETTER%\Ollama\models"
set "NODEJS_DIR=%DRIVE_LETTER%\nodejs"

:: Set Ollama environment for portable mode
set "OLLAMA_LLM_LIBRARY=cuda_v13"
set "CUDA_VISIBLE_DEVICES=0"
set "OLLAMA_KEEP_ALIVE=10m"

:: Add portable Node.js to PATH if it exists (for MCP servers)
if exist "%NODEJS_DIR%\node.exe" set "PATH=%NODEJS_DIR%;%PATH%"

:: Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

:: Check if agent exists
if not exist "%AGENT_DIR%\pentest-gui.py" (
    echo [ERROR] Agent not found at %AGENT_DIR%
    pause
    exit /b 1
)

:: Quick dependency check - only install if missing (silent)
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install customtkinter requests Pillow python-dotenv sounddevice websockets pydub scipy numpy keyboard --quiet
)

:: Launch GUI immediately - it handles all other startup tasks
cd /d "%AGENT_DIR%"
python pentest-gui.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] GUI exited with error
    pause
)
