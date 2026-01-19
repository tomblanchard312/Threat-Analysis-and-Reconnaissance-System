@echo off
:: Start the Kali Linux Docker container

echo.
echo ============================================
echo   Starting Kali Linux Container
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

:: Check if container already exists
docker ps -a --filter "name=htb-kali" --format "{{.Names}}" | findstr /C:"htb-kali" >nul
if %ERRORLEVEL% equ 0 (
    :: Container exists, check if running
    docker ps --filter "name=htb-kali" --format "{{.Names}}" | findstr /C:"htb-kali" >nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] Kali container is already running
    ) else (
        echo [INFO] Starting existing container...
        docker start htb-kali
        echo [OK] Kali container started
    )
) else (
    :: Container doesn't exist, create it
    echo [INFO] Building and starting Kali container...
    echo        This may take a while on first run...
    echo.
    cd /d "%SCRIPT_DIR%"
    docker compose up -d --build
    if %ERRORLEVEL% equ 0 (
        echo.
        echo [OK] Kali container is now running
    ) else (
        echo.
        echo [ERROR] Failed to start container
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo   Kali Linux Ready!
echo ============================================
echo.
echo Container: htb-kali
echo.
echo To access shell: docker exec -it htb-kali bash
echo To stop:         docker stop htb-kali
echo.
