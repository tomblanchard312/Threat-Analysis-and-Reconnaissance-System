@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   HTB Pentest - Portable Tools Installer
echo ============================================
echo.

set "TOOLS_DIR=%~dp0"
set "TEMP_DIR=%TOOLS_DIR%temp"

:: Create temp directory
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

set TOTAL_TOOLS=8
set CURRENT=0

:: ============================================================================
:: 1. NMAP - Port Scanner (portable zip from nmap.org)
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Nmap (port scanner)...

set "NMAP_DIR=%TOOLS_DIR%nmap"
set NMAP_DOWNLOADED=0

for %%V in (7.95 7.94 7.93 7.92) do (
    if !NMAP_DOWNLOADED! equ 0 (
        echo       Trying nmap %%V...
        curl -L -s -o "%TEMP_DIR%\nmap.zip" "https://nmap.org/dist/nmap-%%V-win32.zip" 2>nul
        if !ERRORLEVEL! equ 0 (
            if exist "%TEMP_DIR%\nmap.zip" (
                echo       Extracting...
                powershell -Command "Expand-Archive -Path '%TEMP_DIR%\nmap.zip' -DestinationPath '%TEMP_DIR%' -Force" 2>nul
                if !ERRORLEVEL! equ 0 (
                    :: Find extracted directory
                    for /d %%D in ("%TEMP_DIR%\nmap*") do (
                        if exist "%NMAP_DIR%" rmdir /s /q "%NMAP_DIR%" 2>nul
                        move "%%D" "%NMAP_DIR%" >nul 2>&1
                        if exist "%NMAP_DIR%\nmap.exe" (
                            echo [OK] Nmap %%V installed to: %NMAP_DIR%
                            set NMAP_DOWNLOADED=1
                        )
                    )
                )
            )
        )
    )
)

if !NMAP_DOWNLOADED! equ 0 (
    echo [FAIL] Nmap: Could not download portable version
    echo       Please install manually from: https://nmap.org/download.html
)

:: ============================================================================
:: 2. WHOIS - Domain lookup (Sysinternals)
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Whois (domain lookup)...

curl -L -s -o "%TEMP_DIR%\whois.zip" "https://download.sysinternals.com/files/WhoIs.zip" 2>nul
if %ERRORLEVEL% equ 0 (
    powershell -Command "Expand-Archive -Path '%TEMP_DIR%\whois.zip' -DestinationPath '%TOOLS_DIR%' -Force" 2>nul
    if exist "%TOOLS_DIR%\whois.exe" (
        echo [OK] Whois installed!
    ) else if exist "%TOOLS_DIR%\Whois.exe" (
        echo [OK] Whois installed!
    ) else (
        echo [FAIL] Whois: Extraction failed
    )
) else (
    echo [FAIL] Whois: Download failed
)

:: ============================================================================
:: 3. WGET - Web downloader
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Wget (web downloader)...

curl -L -s -o "%TOOLS_DIR%\wget.exe" "https://eternallybored.org/misc/wget/1.21.4/64/wget.exe" 2>nul
if exist "%TOOLS_DIR%\wget.exe" (
    echo [OK] Wget installed!
) else (
    echo [FAIL] Wget: Download failed
)

:: ============================================================================
:: 4. CURL - HTTP client (for older Windows versions)
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Curl (HTTP client)...

curl -L -s -o "%TEMP_DIR%\curl.zip" "https://curl.se/windows/dl-8.11.1_1/curl-8.11.1_1-win64-mingw.zip" 2>nul
if %ERRORLEVEL% equ 0 (
    powershell -Command "Expand-Archive -Path '%TEMP_DIR%\curl.zip' -DestinationPath '%TEMP_DIR%' -Force" 2>nul
    for /d %%D in ("%TEMP_DIR%\curl*") do (
        if exist "%%D\bin\curl.exe" (
            copy "%%D\bin\curl.exe" "%TOOLS_DIR%\curl.exe" >nul
            copy "%%D\bin\curl-ca-bundle.crt" "%TOOLS_DIR%\curl-ca-bundle.crt" >nul 2>&1
            echo [OK] Curl installed!
        )
    )
) else (
    echo [FAIL] Curl: Download failed
)

:: ============================================================================
:: 5. DIG - DNS lookup (standalone Windows build)
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Dig (DNS lookup)...

set DIG_DOWNLOADED=0
for %%U in (
    "https://downloads.isc.org/isc/bind9/9.18.21/BIND9.18.21.x64.zip"
    "https://downloads.isc.org/isc/bind9/9.16.44/BIND9.16.44.x64.zip"
) do (
    if !DIG_DOWNLOADED! equ 0 (
        echo       Trying: %%~U
        curl -L -s -o "%TEMP_DIR%\bind.zip" %%U 2>nul
        if !ERRORLEVEL! equ 0 (
            if exist "%TEMP_DIR%\bind" rmdir /s /q "%TEMP_DIR%\bind" 2>nul
            powershell -Command "Expand-Archive -Path '%TEMP_DIR%\bind.zip' -DestinationPath '%TEMP_DIR%\bind' -Force" 2>nul
            :: Find dig.exe recursively
            for /r "%TEMP_DIR%\bind" %%F in (dig.exe) do (
                if !DIG_DOWNLOADED! equ 0 (
                    copy "%%F" "%TOOLS_DIR%\dig.exe" >nul
                    :: Copy DLLs from same directory
                    for %%D in ("%%~dpF*.dll") do (
                        copy "%%D" "%TOOLS_DIR%\" >nul 2>&1
                    )
                    echo [OK] Dig installed!
                    set DIG_DOWNLOADED=1
                )
            )
        )
    )
)

if !DIG_DOWNLOADED! equ 0 (
    echo [SKIP] Dig: Could not download. Use nslookup (built-in) instead.
)

:: ============================================================================
:: 6. NETCAT (ncat from nmap) - Network utility
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Setting up Netcat (from Nmap)...

if exist "%NMAP_DIR%\ncat.exe" (
    copy "%NMAP_DIR%\ncat.exe" "%TOOLS_DIR%\nc.exe" >nul
    copy "%NMAP_DIR%\ncat.exe" "%TOOLS_DIR%\ncat.exe" >nul
    echo [OK] Netcat (ncat) installed!
) else (
    echo [SKIP] Netcat: Nmap installation required
)

:: ============================================================================
:: 7. TCPING - TCP ping utility
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Tcping (TCP ping)...

curl -L -s -o "%TOOLS_DIR%\tcping.exe" "https://download.elifulkerson.com/files/tcping/0.39/tcping.exe" 2>nul
if exist "%TOOLS_DIR%\tcping.exe" (
    echo [OK] Tcping installed!
) else (
    echo [FAIL] Tcping: Download failed
)

:: ============================================================================
:: 8. NPCAP - Packet capture driver (installer only - requires admin to install)
:: ============================================================================
set /a CURRENT+=1
echo [%CURRENT%/%TOTAL_TOOLS%] Downloading Npcap installer...

curl -L -s -o "%TOOLS_DIR%\npcap-installer.exe" "https://npcap.com/dist/npcap-1.86.exe" 2>nul
if exist "%TOOLS_DIR%\npcap-installer.exe" (
    echo [OK] Npcap installer downloaded!
    echo       To install: Run npcap-installer.exe as Administrator
) else (
    echo [FAIL] Npcap: Download failed
    echo       Download manually from: https://npcap.com/
)

:: ============================================================================
:: Cleanup
:: ============================================================================
echo.
echo Cleaning up temporary files...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul

:: ============================================================================
:: Summary
:: ============================================================================
echo.
echo ============================================
echo   Installation Complete!
echo   Location: %TOOLS_DIR%
echo ============================================
echo.

echo Portable tools installed:
for %%F in ("%TOOLS_DIR%*.exe") do (
    echo   - %%~nxF
)
if exist "%NMAP_DIR%\nmap.exe" echo   - nmap\nmap.exe

echo.
echo Windows built-in tools (no download needed):
echo   - ping, nslookup, tracert, netstat, arp
echo.
echo Note: Some tools may require Npcap driver for full functionality.
echo       Download from: https://npcap.com/
echo.
echo Run 'start-agent.bat' to use these tools with HTB Pentest AI!
echo.

pause
