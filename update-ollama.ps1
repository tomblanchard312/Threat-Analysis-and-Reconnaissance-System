# Update Ollama to latest version (v0.15.2+ with ollama launch support)
param(
    [string]$TargetDir = "L:\Ollama"
)

$ErrorActionPreference = "Stop"
$tempZip = Join-Path $env:TEMP "ollama-new.zip"
$tempExtract = Join-Path $env:TEMP "ollama-extract"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Updating Ollama to latest version" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check current version
if (Test-Path "$TargetDir\ollama.exe") {
    $currentVersion = & "$TargetDir\ollama.exe" --version 2>&1
    Write-Host "Current version: $currentVersion" -ForegroundColor Yellow
} else {
    Write-Host "No existing Ollama found at $TargetDir" -ForegroundColor Yellow
}

# Download latest
Write-Host ""
Write-Host "Downloading latest Ollama for Windows..." -ForegroundColor Green
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

try {
    Invoke-WebRequest -Uri "https://ollama.com/download/ollama-windows-amd64.zip" -OutFile $tempZip -UseBasicParsing
    $size = [math]::Round((Get-Item $tempZip).Length / 1MB, 2)
    Write-Host "  Downloaded: $size MB" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Download failed - $_" -ForegroundColor Red
    exit 1
}

# Extract
Write-Host ""
Write-Host "Extracting..." -ForegroundColor Green
if (Test-Path $tempExtract) {
    Remove-Item $tempExtract -Recurse -Force
}
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

# Backup existing ollama.exe
if (Test-Path "$TargetDir\ollama.exe") {
    Write-Host "  Backing up existing ollama.exe..." -ForegroundColor Yellow
    Copy-Item "$TargetDir\ollama.exe" "$TargetDir\ollama.exe.bak" -Force
}

# Copy new files
Write-Host "  Copying new files to $TargetDir..." -ForegroundColor Green
Copy-Item "$tempExtract\*" $TargetDir -Recurse -Force

# Verify
Write-Host ""
$newVersion = & "$TargetDir\ollama.exe" --version 2>&1
Write-Host "New version: $newVersion" -ForegroundColor Green

# Test ollama launch
Write-Host ""
Write-Host "Testing ollama launch command..." -ForegroundColor Cyan
$launchHelp = & "$TargetDir\ollama.exe" launch --help 2>&1
if ($launchHelp -match "launch") {
    Write-Host "  ollama launch is available!" -ForegroundColor Green
} else {
    Write-Host "  ollama launch output: $launchHelp" -ForegroundColor Yellow
}

# Cleanup
Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Update Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "New features available:" -ForegroundColor Cyan
Write-Host "  ollama launch claude    - Run Claude Code with local models"
Write-Host "  ollama launch codex     - Run OpenAI Codex CLI"
Write-Host "  ollama launch opencode  - Run OpenCode"
Write-Host "  ollama launch clawdbot  - Run Clawdbot"
Write-Host "  ollama launch droid     - Run Droid"
Write-Host ""
