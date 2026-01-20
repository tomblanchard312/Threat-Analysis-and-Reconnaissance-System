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

:: Check if htb-pentest model already exists in Ollama
"%OLLAMA_EXE%" list 2>nul | findstr /i "htb-pentest" >nul 2>&1
if %ERRORLEVEL%==0 goto :model_exists

:: No local GGUF found - ask user what to do
echo.
echo      No local GGUF model found.
echo.
echo      Choose model source:
echo        [1] Pull from Ollama Registry (sirrand/htb-pentest - recommended)
echo        [2] Use Lite Mode (pulls mistral:7b base model)
echo        [3] Enter custom Ollama model name
echo.
choice /c 123 /n /m "      Select option (1-3): "
if errorlevel 3 goto :custom_model
if errorlevel 2 goto :lite_mode
if errorlevel 1 goto :pull_registry

:pull_registry
echo.
echo      Pulling sirrand/htb-pentest from Ollama Registry...
"%OLLAMA_EXE%" pull sirrand/htb-pentest
if errorlevel 1 goto :pull_failed
echo      Creating local htb-pentest alias...
"%OLLAMA_EXE%" cp sirrand/htb-pentest htb-pentest
echo      Model ready (from registry)
goto :start_gui

:custom_model
echo.
set /p "CUSTOM_MODEL=      Enter Ollama model name (e.g., username/model): "
if "%CUSTOM_MODEL%"=="" goto :lite_mode
echo      Pulling %CUSTOM_MODEL%...
"%OLLAMA_EXE%" pull %CUSTOM_MODEL%
if errorlevel 1 goto :pull_failed
echo      Creating local htb-pentest alias...
"%OLLAMA_EXE%" cp %CUSTOM_MODEL% htb-pentest
echo      Model ready (from %CUSTOM_MODEL%)
goto :start_gui

:pull_failed
echo      [WARN] Failed to pull model, falling back to lite mode...

:lite_mode
if not exist "%AGENT_DIR%\Modelfile.lite" goto :no_modelfile
echo      Using lite mode...
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

:model_exists
echo      Model htb-pentest found, rebuilding with current Modelfile...
if exist "%AGENT_DIR%\Modelfile.lite" goto :rebuild_lite
goto :start_gui

:rebuild_lite
"%OLLAMA_EXE%" create htb-pentest -f Modelfile.lite
echo      Model rebuilt successfully
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
