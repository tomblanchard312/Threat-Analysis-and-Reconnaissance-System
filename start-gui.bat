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
set "OLLAMA_HOME=%DRIVE_LETTER%\Ollama"
set "OLLAMA_MODELS=%DRIVE_LETTER%\Ollama\models"
set "OLLAMA_EXE=%OLLAMA_HOME%\ollama.exe"

echo Drive: %DRIVE_LETTER%
echo OLLAMA_HOME: %OLLAMA_HOME%
echo.

:: Check if portable Ollama exists
if not exist "%OLLAMA_EXE%" (
    echo [ERROR] Portable Ollama not found at %OLLAMA_EXE%
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
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

:: Check and install required packages
echo [1/3] Checking dependencies...

echo      Checking requests...
python -c "import requests" >nul 2>&1
if errorlevel 1 pip install requests

echo      Checking customtkinter...
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 pip install customtkinter

echo      Checking Pillow...
python -c "import PIL" >nul 2>&1
if errorlevel 1 pip install Pillow

echo      Checking scikit-learn...
python -c "import sklearn" >nul 2>&1
if errorlevel 1 pip install scikit-learn --quiet

echo      Checking PyPDF2...
python -c "import PyPDF2" >nul 2>&1
if errorlevel 1 pip install PyPDF2

echo      Checking pdfplumber...
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 pip install pdfplumber

echo      Dependencies OK
echo.

:: Start Ollama if not running
echo [2/3] Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if not errorlevel 1 goto :ollama_running

echo      Starting portable Ollama...
start "" "%OLLAMA_EXE%" serve
echo      Waiting for Ollama to start...

:waitloop
timeout /t 1 /nobreak >nul
"%OLLAMA_EXE%" list >nul 2>&1
if errorlevel 1 goto :waitloop
echo      Ollama is ready!
goto :ollama_done

:ollama_running
echo      Ollama is running

:ollama_done

:: Setup model - always rebuild to pick up Modelfile changes
echo [3/3] Building model...
cd /d "%AGENT_DIR%"

:: Check if local GGUF model exists (full version)
if exist "%AGENT_DIR%\htb-pentest-v3-q4_k_m.gguf" goto :build_full_model
if exist "%AGENT_DIR%\*.gguf" goto :build_full_model

:: No GGUF found - use lite mode with mistral:7b
if not exist "%AGENT_DIR%\Modelfile.lite" goto :no_modelfile

echo      No local GGUF found, using lite mode...
echo      Checking mistral:7b...
"%OLLAMA_EXE%" list | findstr /i "mistral:7b" >nul 2>&1
if not errorlevel 1 goto :build_lite_model

echo      Pulling mistral:7b...
"%OLLAMA_EXE%" pull mistral:7b

:build_lite_model
echo      Rebuilding htb-pentest from Modelfile.lite...
"%OLLAMA_EXE%" create htb-pentest -f Modelfile.lite
echo      Model rebuilt successfully (lite mode)
goto :start_gui

:build_full_model
echo      Found local GGUF model, using full Modelfile...
if not exist "%AGENT_DIR%\Modelfile" goto :no_modelfile
echo      Rebuilding htb-pentest from local GGUF...
"%OLLAMA_EXE%" create htb-pentest -f Modelfile
echo      Model rebuilt successfully (full version)
goto :start_gui

:no_modelfile
echo      [WARN] No Modelfile found, skipping model build

:start_gui
echo.
echo ============================================================
echo   Starting GUI...
echo ============================================================
echo.

:: Run the GUI
cd /d "%AGENT_DIR%"
python pentest-gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] GUI exited with error
    pause
)
