@echo off
setlocal

echo.
echo ============================================================
echo   TARS - CLI Launcher
echo ============================================================
echo.

:: Get the drive letter where this script is located
set "DRIVE_LETTER=%~d0"
set "AGENT_DIR=%DRIVE_LETTER%\agent"
set "MODELS_DIR=%DRIVE_LETTER%\models"
set "OLLAMA_HOME=%DRIVE_LETTER%\Ollama"
set "OLLAMA_MODELS=%DRIVE_LETTER%\Ollama\models"
set "OLLAMA_EXE=%OLLAMA_HOME%\ollama.exe"
set "NODEJS_DIR=%DRIVE_LETTER%\nodejs"

echo Drive: %DRIVE_LETTER%
echo OLLAMA_HOME: %OLLAMA_HOME%

:: Add portable Node.js to PATH if it exists (for MCP servers)
if exist "%NODEJS_DIR%\node.exe" (
    echo Node.js: %NODEJS_DIR%
    set "PATH=%NODEJS_DIR%;%PATH%"
) else (
    echo Node.js: Not installed
)
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
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Auto-upgrade pip to suppress update notices
python -m pip install --upgrade pip --quiet >nul 2>&1

:: Check and install required packages
echo [1/4] Checking dependencies...

echo      Checking requests...
python -c "import requests" >nul 2>&1
if errorlevel 1 pip install requests

echo      Checking scikit-learn...
python -c "import sklearn" >nul 2>&1
if errorlevel 1 pip install scikit-learn --quiet

echo      Checking PyPDF2...
python -c "import PyPDF2" >nul 2>&1
if errorlevel 1 pip install PyPDF2

echo      Checking pdfplumber...
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 pip install pdfplumber

echo      Checking python-dotenv...
python -c "import dotenv" >nul 2>&1
if errorlevel 1 pip install python-dotenv

echo      Dependencies OK
echo.

:: Start Ollama if not running
echo [2/4] Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if not errorlevel 1 goto :ollama_running

echo      Starting portable Ollama...
:: Fix GPU discovery timeout when running from USB/portable drive
:: Tell Ollama exactly which CUDA library to use (skips slow auto-discovery)
set "OLLAMA_LLM_LIBRARY=cuda_v13"
set "CUDA_VISIBLE_DEVICES=0"
set "OLLAMA_KEEP_ALIVE=10m"
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
echo.

:: Start Docker Desktop and Kali container
echo [3/4] Starting Kali Docker...
call :start_docker
echo.

:: Setup model
echo [4/4] Building model...
cd /d "%AGENT_DIR%"

:: Check if local GGUF model exists in models folder
if exist "%MODELS_DIR%\htb-pentest.gguf" goto :build_full_model
if exist "%MODELS_DIR%\*.gguf" goto :build_full_model

:: Legacy: Check for model in agent folder
if exist "%AGENT_DIR%\htb-pentest*.gguf" goto :build_legacy_model
if exist "%AGENT_DIR%\*.gguf" goto :build_legacy_model

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
goto :start_agent

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
goto :start_agent

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
goto :start_agent

:model_exists
echo      Model htb-pentest found in Ollama
goto :start_agent

:build_full_model
echo      Found local GGUF model in models folder
if not exist "%AGENT_DIR%\Modelfile" goto :no_modelfile
echo      Rebuilding htb-pentest from local GGUF...
"%OLLAMA_EXE%" create htb-pentest -f Modelfile
echo      Model rebuilt successfully (full version)
goto :start_agent

:build_legacy_model
echo      Found local GGUF model in agent folder (legacy location)
echo      Rebuilding htb-pentest from local GGUF...
"%OLLAMA_EXE%" create htb-pentest -f Modelfile
echo      Model rebuilt successfully (full version)
goto :start_agent

:no_modelfile
echo      [WARN] No Modelfile found, skipping model build

:start_agent
echo.
echo ============================================================
echo   Starting TARS Agent...
echo ============================================================
echo.

:: Run the agent
cd /d "%AGENT_DIR%"
python pentest-agent.py

if errorlevel 1 (
    echo.
    echo [ERROR] Agent exited with error
    pause
)
goto :eof

:: ============================================================
:: SUBROUTINE: Start Docker Desktop and Kali container
:: ============================================================
:start_docker
docker info >nul 2>&1
if not errorlevel 1 goto :docker_is_running

:: Docker not running - try to start it
echo      Docker Desktop not running - attempting to start...
if not exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    echo      Docker Desktop not installed - Kali tools unavailable
    goto :eof
)

start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo      Waiting for Docker Desktop (up to 45s)...

:: Wait for Docker to start (simple sequential checks)
timeout /t 10 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto :docker_is_running

echo      Still waiting...
timeout /t 10 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto :docker_is_running

echo      Still waiting...
timeout /t 10 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto :docker_is_running

echo      Still waiting...
timeout /t 15 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto :docker_is_running

echo      [WARN] Docker Desktop took too long to start
echo      Kali tools will be unavailable this session
goto :eof

:docker_is_running
echo      Docker Desktop is ready

:: Start the Kali container
docker ps -a 2>nul | findstr /i "htb-kali" >nul 2>&1
if errorlevel 1 goto :build_container

:: Container exists - start if not running
docker ps 2>nul | findstr /i "htb-kali" >nul 2>&1
if not errorlevel 1 (
    echo      Kali container already running
    goto :eof
)

echo      Starting Kali container...
docker start htb-kali >nul 2>&1
timeout /t 2 /nobreak >nul
echo      Kali Docker ready!
goto :eof

:build_container
echo      Building Kali container (first run)...
if not exist "%AGENT_DIR%\docker\docker-compose.yml" (
    echo      [WARN] docker-compose.yml not found
    goto :eof
)
cd /d "%AGENT_DIR%\docker"
docker-compose up -d --build
cd /d "%AGENT_DIR%"
timeout /t 2 /nobreak >nul
echo      Kali Docker ready!
goto :eof
