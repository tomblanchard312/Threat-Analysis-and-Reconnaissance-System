# Download portable penetration testing tools for Windows
# Run this script to equip the USB drive with pentest tools
# Covers all tools from HTB Pentest training data

$ToolsDir = $PSScriptRoot
$TempDir = "$ToolsDir\temp"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  HTB Pentest - Portable Tools Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Create temp directory
if (!(Test-Path $TempDir)) { New-Item -ItemType Directory -Path $TempDir | Out-Null }

$totalTools = 8
$current = 0

# ============================================================================
# 1. NMAP - Port Scanner (portable zip from nmap.org)
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Nmap (port scanner)..." -ForegroundColor Yellow
$NmapZip = "$TempDir\nmap.zip"
$NmapDir = "$ToolsDir\nmap"
$NmapDownloaded = $false

# Try multiple versions (nmap.org sometimes removes older zips)
$NmapVersions = @("7.95", "7.94", "7.93", "7.92")

foreach ($ver in $NmapVersions) {
    if ($NmapDownloaded) { break }
    $NmapUrl = "https://nmap.org/dist/nmap-$ver-win32.zip"
    Write-Host "      Trying nmap $ver..." -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $NmapUrl -OutFile $NmapZip -UseBasicParsing -ErrorAction Stop -TimeoutSec 60
        Write-Host "      Extracting..." -ForegroundColor Gray
        Expand-Archive -Path $NmapZip -DestinationPath $TempDir -Force

        $ExtractedDir = Get-ChildItem -Path $TempDir -Directory | Where-Object { $_.Name -like "nmap*" } | Select-Object -First 1
        if ($ExtractedDir) {
            if (Test-Path $NmapDir) { Remove-Item -Path $NmapDir -Recurse -Force }
            Move-Item -Path $ExtractedDir.FullName -Destination $NmapDir
            # Don't copy just nmap.exe - it needs DLLs! Agent will use tools/nmap/nmap.exe
            Write-Host "[OK] Nmap $ver installed to: $NmapDir" -ForegroundColor Green
            $NmapDownloaded = $true
        }
    } catch {
        # Try next version
    }
}

if (-not $NmapDownloaded) {
    Write-Host "[FAIL] Nmap: Could not download portable version" -ForegroundColor Red
    Write-Host "      Please install manually from: https://nmap.org/download.html" -ForegroundColor Yellow
    Write-Host "      (Download and run the .exe installer)" -ForegroundColor Gray
}

# ============================================================================
# 2. WHOIS - Domain lookup (Sysinternals)
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Whois (domain lookup)..." -ForegroundColor Yellow
$WhoisUrl = "https://download.sysinternals.com/files/WhoIs.zip"
$WhoisZip = "$TempDir\whois.zip"

try {
    Invoke-WebRequest -Uri $WhoisUrl -OutFile $WhoisZip -UseBasicParsing -ErrorAction Stop
    Expand-Archive -Path $WhoisZip -DestinationPath $ToolsDir -Force
    Write-Host "[OK] Whois installed!" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Whois: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================================
# 3. WGET - Web downloader
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Wget (web downloader)..." -ForegroundColor Yellow
$WgetUrl = "https://eternallybored.org/misc/wget/1.21.4/64/wget.exe"

try {
    Invoke-WebRequest -Uri $WgetUrl -OutFile "$ToolsDir\wget.exe" -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Wget installed!" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Wget: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================================
# 4. CURL - HTTP client (for older Windows versions)
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Curl (HTTP client)..." -ForegroundColor Yellow
$CurlUrl = "https://curl.se/windows/dl-8.11.1_1/curl-8.11.1_1-win64-mingw.zip"
$CurlZip = "$TempDir\curl.zip"

try {
    Invoke-WebRequest -Uri $CurlUrl -OutFile $CurlZip -UseBasicParsing -ErrorAction Stop
    Expand-Archive -Path $CurlZip -DestinationPath $TempDir -Force
    $CurlDir = Get-ChildItem -Path $TempDir -Directory | Where-Object { $_.Name -like "curl*" } | Select-Object -First 1
    if ($CurlDir) {
        Copy-Item "$($CurlDir.FullName)\bin\curl.exe" "$ToolsDir\curl.exe" -Force
        Copy-Item "$($CurlDir.FullName)\bin\curl-ca-bundle.crt" "$ToolsDir\curl-ca-bundle.crt" -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Curl installed!" -ForegroundColor Green
    }
} catch {
    Write-Host "[FAIL] Curl: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================================
# 5. DIG - DNS lookup (standalone Windows build)
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Dig (DNS lookup)..." -ForegroundColor Yellow
# Use ISC BIND release or GitHub mirror
$DigUrls = @(
    "https://downloads.isc.org/isc/bind9/9.18.21/BIND9.18.21.x64.zip",
    "https://downloads.isc.org/isc/bind9/9.16.44/BIND9.16.44.x64.zip"
)
$DigZip = "$TempDir\bind.zip"
$DigDownloaded = $false

foreach ($DigUrl in $DigUrls) {
    if ($DigDownloaded) { break }
    try {
        Write-Host "      Trying: $DigUrl" -ForegroundColor Gray
        Invoke-WebRequest -Uri $DigUrl -OutFile $DigZip -UseBasicParsing -ErrorAction Stop -TimeoutSec 30
        Expand-Archive -Path $DigZip -DestinationPath "$TempDir\bind" -Force

        # Find and copy dig.exe
        $DigExe = Get-ChildItem -Path "$TempDir\bind" -Recurse -Filter "dig.exe" | Select-Object -First 1
        if ($DigExe) {
            Copy-Item $DigExe.FullName "$ToolsDir\dig.exe" -Force
            # Copy required DLLs
            $BindDir = $DigExe.Directory
            Get-ChildItem -Path $BindDir -Filter "*.dll" | ForEach-Object {
                Copy-Item $_.FullName "$ToolsDir\$($_.Name)" -Force -ErrorAction SilentlyContinue
            }
            Write-Host "[OK] Dig installed!" -ForegroundColor Green
            $DigDownloaded = $true
        }
    } catch {
        Write-Host "      Failed, trying next..." -ForegroundColor Gray
    }
}

if (-not $DigDownloaded) {
    Write-Host "[SKIP] Dig: Could not download. Use nslookup (built-in) instead." -ForegroundColor Yellow
    Write-Host "      Or install BIND: https://www.isc.org/download/" -ForegroundColor Gray
}

# ============================================================================
# 6. NETCAT (ncat from nmap) - Network utility
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Setting up Netcat (from Nmap)..." -ForegroundColor Yellow
if (Test-Path "$NmapDir\ncat.exe") {
    Copy-Item "$NmapDir\ncat.exe" "$ToolsDir\nc.exe" -Force
    Copy-Item "$NmapDir\ncat.exe" "$ToolsDir\ncat.exe" -Force
    Write-Host "[OK] Netcat (ncat) installed!" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Netcat: Nmap installation required" -ForegroundColor Gray
}

# ============================================================================
# 7. TCPING - TCP ping utility
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Tcping (TCP ping)..." -ForegroundColor Yellow
$TcpingUrl = "https://download.elifulkerson.com/files/tcping/0.39/tcping.exe"

try {
    Invoke-WebRequest -Uri $TcpingUrl -OutFile "$ToolsDir\tcping.exe" -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Tcping installed!" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Tcping: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================================
# 8. NPCAP - Packet capture driver (installer only - requires admin to install)
# ============================================================================
$current++
Write-Host "[$current/$totalTools] Downloading Npcap installer..." -ForegroundColor Yellow
$NpcapUrl = "https://npcap.com/dist/npcap-1.86.exe"
$NpcapInstaller = "$ToolsDir\npcap-installer.exe"

try {
    Invoke-WebRequest -Uri $NpcapUrl -OutFile $NpcapInstaller -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Npcap installer downloaded!" -ForegroundColor Green
    Write-Host "      To install: Run npcap-installer.exe as Administrator" -ForegroundColor Gray
} catch {
    Write-Host "[FAIL] Npcap: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      Download manually from: https://npcap.com/" -ForegroundColor Gray
}

# ============================================================================
# Cleanup
# ============================================================================
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor Gray
Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Cyan
Write-Host "  Location: $ToolsDir" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Portable tools installed:" -ForegroundColor Green
$exeFiles = Get-ChildItem -Path $ToolsDir -Filter "*.exe" | Where-Object { $_.Name -notlike "*64*" -or $_.Name -eq "whois64.exe" }
$exeFiles | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 0)
    Write-Host "  - $($_.Name) ($size KB)"
}

Write-Host ""
Write-Host "Windows built-in tools (no download needed):" -ForegroundColor Gray
Write-Host "  - ping, nslookup, tracert, netstat, arp"
Write-Host ""

Write-Host "Note: Some tools may require Npcap driver for full functionality." -ForegroundColor Yellow
Write-Host "      Download from: https://npcap.com/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Run 'start-agent.bat' to use these tools with HTB Pentest AI!" -ForegroundColor Cyan
