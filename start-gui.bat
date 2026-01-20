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

python -c "import PIL" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Installing Pillow...
    pip install Pillow
)

:: Knowledge Base dependencies (optional but recommended)
python -c "import sklearn" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Installing scikit-learn (for Knowledge Base)...
    pip install scikit-learn
)

python -c "import PyPDF2" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Installing PyPDF2 (for PDF support)...
    pip install PyPDF2
)

python -c "import pdfplumber" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Installing pdfplumber (for better PDF extraction)...
    pip install pdfplumber
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

:: Determine which Modelfile to use based on available resources
echo [3/3] Setting up model...
cd /d "%AGENT_DIR%"

:: Check for model_config.json (remote model or forced lite mode)
set "USE_REMOTE=0"
set "FORCE_LITE=0"
if exist "%AGENT_DIR%\model_config.json" (
    :: Parse JSON using PowerShell
    for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content '%AGENT_DIR%\model_config.json' | ConvertFrom-Json).remote_model"') do set "REMOTE_MODEL=%%i"
    for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content '%AGENT_DIR%\model_config.json' | ConvertFrom-Json).use_lite"') do set "CONFIG_LITE=%%i"
    if not "%REMOTE_MODEL%"=="" if not "%REMOTE_MODEL%"=="null" (
        set "USE_REMOTE=1"
    )
    if "%CONFIG_LITE%"=="True" (
        set "FORCE_LITE=1"
    )
)

:: Option 1: Remote model specified in config
if "%USE_REMOTE%"=="1" (
    echo      Remote model configured: %REMOTE_MODEL%
    echo      Checking if model is available locally...
    "%OLLAMA_EXE%" list | findstr /i "%REMOTE_MODEL%" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo      Pulling remote model (this may take a while)...
        "%OLLAMA_EXE%" pull %REMOTE_MODEL%
    )
    echo      Creating htb-pentest alias from remote model...
    echo FROM %REMOTE_MODEL%> "%AGENT_DIR%\Modelfile.remote"
    type "%AGENT_DIR%\Modelfile" | findstr /v "^FROM" >> "%AGENT_DIR%\Modelfile.remote"
    "%OLLAMA_EXE%" create htb-pentest -f Modelfile.remote
    if %ERRORLEVEL% equ 0 (
        echo      Model htb-pentest is ready (remote: %REMOTE_MODEL%)
    ) else (
        echo      [ERROR] Failed to create model from remote
    )
    goto :modelready
)

:: Option 2: Check if we have a custom GGUF model file (unless forced lite)
set "HAS_GGUF=0"
if not "%FORCE_LITE%"=="1" (
    for %%f in ("%AGENT_DIR%\*.gguf") do (
        set "HAS_GGUF=1"
        set "GGUF_FILE=%%f"
    )
)

if "%HAS_GGUF%"=="1" (
    echo      Found custom GGUF model: %GGUF_FILE%
    echo      Building htb-pentest from full Modelfile...
    "%OLLAMA_EXE%" create htb-pentest -f Modelfile
    if %ERRORLEVEL% equ 0 (
        echo      Model htb-pentest is ready (full version)
    ) else (
        echo      [WARNING] Full model build failed - trying lite version...
        goto :trylite
    )
) else (
    echo      No custom GGUF found - using lite version with pullable base
    :trylite
    :: Check if Modelfile.lite exists
    if exist "%AGENT_DIR%\Modelfile.lite" (
        echo      Checking if mistral:7b base model is available...
        "%OLLAMA_EXE%" list | findstr /i "mistral:7b" >nul 2>&1
        if %ERRORLEVEL% neq 0 (
            echo      Pulling mistral:7b base model (this may take a while)...
            "%OLLAMA_EXE%" pull mistral:7b
        )
        echo      Building htb-pentest from lite Modelfile...
        "%OLLAMA_EXE%" create htb-pentest -f Modelfile.lite
        if %ERRORLEVEL% equ 0 (
            echo      Model htb-pentest is ready (lite version)
        ) else (
            echo      [ERROR] Model build failed
        )
    ) else (
        echo      [ERROR] No Modelfile.lite found and no GGUF available
        echo      Please add a .gguf model file or Modelfile.lite
    )
)

:modelready

echo.
echo ============================================================
echo   Starting GUI...
echo ============================================================
echo.

:: Run the GUI
cd /d "%AGENT_DIR%"
pythonw pentest-gui.py 2>nul || python pentest-gui.py
