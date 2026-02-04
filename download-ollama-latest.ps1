# Download and install latest Ollama from GitHub releases
param(
    [string]$TargetDir = "L:\Ollama"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Downloading Latest Ollama from GitHub" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get latest release info
Write-Host "Fetching latest release info..." -ForegroundColor Green
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/ollama/ollama/releases/latest"
Write-Host "  Latest version: $($release.tag_name)"

# Find Windows AMD64 zip asset
$winAsset = $release.assets | Where-Object { $_.name -eq "ollama-windows-amd64.zip" }
if (-not $winAsset) {
    Write-Host "ERROR: Windows asset not found in release" -ForegroundColor Red
    Write-Host "Available assets:"
    $release.assets | ForEach-Object { Write-Host "  - $($_.name)" }
    exit 1
}

Write-Host "  Asset: $($winAsset.name)"
Write-Host "  Size: $([math]::Round($winAsset.size / 1MB, 2)) MB"
Write-Host "  URL: $($winAsset.browser_download_url)"

# Download
$tempZip = Join-Path $env:TEMP "ollama-latest.zip"
Write-Host ""
Write-Host "Downloading..." -ForegroundColor Green
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Use WebClient for more reliable download with progress
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile($winAsset.browser_download_url, $tempZip)

$downloadedSize = (Get-Item $tempZip).Length
Write-Host "  Downloaded: $([math]::Round($downloadedSize / 1MB, 2)) MB"

if ($downloadedSize -ne $winAsset.size) {
    Write-Host "WARNING: Downloaded size ($downloadedSize) doesn't match expected ($($winAsset.size))" -ForegroundColor Yellow
}

# Extract
$tempExtract = Join-Path $env:TEMP "ollama-extract"
Write-Host ""
Write-Host "Extracting..." -ForegroundColor Green
if (Test-Path $tempExtract) {
    Remove-Item $tempExtract -Recurse -Force
}
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
Write-Host "  Extracted"

# Backup existing
if (Test-Path "$TargetDir\ollama.exe") {
    Write-Host "  Backing up existing ollama.exe..."
    Copy-Item "$TargetDir\ollama.exe" "$TargetDir\ollama.exe.old" -Force
}

# Copy new files
Write-Host "  Installing to $TargetDir..."
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}
Copy-Item "$tempExtract\*" $TargetDir -Recurse -Force
Write-Host "  Done"

# Verify version
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Green
$newVersion = & "$TargetDir\ollama.exe" --version 2>&1
Write-Host "  Version: $newVersion"

# Test launch command
Write-Host ""
Write-Host "Testing 'ollama launch'..." -ForegroundColor Cyan
$launchOutput = & "$TargetDir\ollama.exe" launch 2>&1
if ($launchOutput -match "error|unknown") {
    Write-Host "  Launch command not available: $launchOutput" -ForegroundColor Yellow
} else {
    Write-Host "  Launch command available!" -ForegroundColor Green
    Write-Host $launchOutput
}

# Cleanup
Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  ollama launch claude    - Claude Code with local models"
Write-Host "  ollama launch codex     - OpenAI Codex CLI"
Write-Host "  ollama launch opencode  - OpenCode"
Write-Host "  ollama launch clawdbot  - Clawdbot"
Write-Host "  ollama launch droid     - Droid"
Write-Host ""
