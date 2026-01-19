# HTB Pentest Agent - USB Deployment Script
# Deploys the full pentest agent to a USB drive
# Run as Administrator: powershell -ExecutionPolicy Bypass -File deploy-to-usb.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetDrive,  # e.g., "E:"

    [Parameter(Mandatory=$false)]
    [string]$SourceDir = $PSScriptRoot + "\..",  # Parent of deploy folder

    [switch]$IncludeModel,  # Include the GGUF model file (4GB+)
    [switch]$IncludeTraining,  # Include training code
    [switch]$DownloadOllama  # Download fresh Ollama
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  HTB Pentest Agent - USB Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Validate target drive
if (-not (Test-Path $TargetDrive)) {
    Write-Host "[ERROR] Target drive $TargetDrive not found!" -ForegroundColor Red
    exit 1
}

$TargetDrive = $TargetDrive.TrimEnd('\')
Write-Host "Target: $TargetDrive" -ForegroundColor Yellow
Write-Host "Source: $SourceDir" -ForegroundColor Yellow
Write-Host ""

# Create directory structure
Write-Host "[1/6] Creating directory structure..." -ForegroundColor Green
$directories = @(
    "$TargetDrive\agent",
    "$TargetDrive\agent\docker",
    "$TargetDrive\agent\docker\shared",
    "$TargetDrive\agent\tools",
    "$TargetDrive\agent\transcripts",
    "$TargetDrive\Ollama",
    "$TargetDrive\Ollama\models"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir"
    }
}

# Copy agent files
Write-Host "[2/6] Copying agent files..." -ForegroundColor Green
$agentFiles = @(
    "pentest-agent.py",
    "pentest-gui.py",
    "Modelfile",
    "settings.json",
    "kali_tools.json"
)

foreach ($file in $agentFiles) {
    $src = "$SourceDir\agent\$file"
    $dst = "$TargetDrive\agent\$file"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied: $file"
    } else {
        Write-Host "  [WARN] Not found: $file" -ForegroundColor Yellow
    }
}

# Copy Docker files
Write-Host "[3/6] Copying Docker configuration..." -ForegroundColor Green
$dockerFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "start-kali.bat",
    "start-kali.sh",
    "stop-kali.bat",
    "stop-kali.sh"
)

foreach ($file in $dockerFiles) {
    $src = "$SourceDir\agent\docker\$file"
    $dst = "$TargetDrive\agent\docker\$file"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied: $file"
    }
}

# Copy root launchers
Write-Host "[4/6] Copying launcher scripts..." -ForegroundColor Green
Copy-Item "$SourceDir\start-gui.bat" "$TargetDrive\start-gui.bat" -Force
Copy-Item "$SourceDir\start-agent.bat" "$TargetDrive\start-agent.bat" -Force
Copy-Item "$SourceDir\autorun.inf" "$TargetDrive\autorun.inf" -Force
Copy-Item "$SourceDir\README.md" "$TargetDrive\README.md" -Force -ErrorAction SilentlyContinue
Write-Host "  Copied launcher scripts"

# Handle Ollama
Write-Host "[5/6] Setting up Ollama..." -ForegroundColor Green
if ($DownloadOllama) {
    Write-Host "  Downloading Ollama..."
    $ollamaUrl = "https://ollama.com/download/ollama-windows-amd64.zip"
    $ollamaZip = "$env:TEMP\ollama.zip"
    Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaZip
    Expand-Archive -Path $ollamaZip -DestinationPath "$TargetDrive\Ollama" -Force
    Remove-Item $ollamaZip
    Write-Host "  Ollama downloaded and extracted"
} elseif (Test-Path "$SourceDir\Ollama\ollama.exe") {
    Write-Host "  Copying existing Ollama installation..."
    # Copy Ollama executable and libs
    Copy-Item "$SourceDir\Ollama\ollama.exe" "$TargetDrive\Ollama\" -Force
    Copy-Item "$SourceDir\Ollama\app.ico" "$TargetDrive\Ollama\" -Force -ErrorAction SilentlyContinue
    if (Test-Path "$SourceDir\Ollama\lib") {
        Copy-Item "$SourceDir\Ollama\lib" "$TargetDrive\Ollama\" -Recurse -Force
    }
    Write-Host "  Ollama copied"
} else {
    Write-Host "  [WARN] Ollama not found. Run with -DownloadOllama to download." -ForegroundColor Yellow
}

# Copy model file if requested
if ($IncludeModel) {
    Write-Host "  Copying model file (this may take a while)..."
    $modelFile = Get-ChildItem "$SourceDir\agent\*.gguf" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($modelFile) {
        Copy-Item $modelFile.FullName "$TargetDrive\agent\" -Force
        Write-Host "  Model copied: $($modelFile.Name)"
    } else {
        Write-Host "  [WARN] No .gguf model file found in agent folder" -ForegroundColor Yellow
    }
}

# Copy training code if requested
if ($IncludeTraining) {
    Write-Host "  Copying training code..."
    if (Test-Path "$SourceDir\training") {
        Copy-Item "$SourceDir\training" "$TargetDrive\training" -Recurse -Force
        Write-Host "  Training code copied"
    } elseif (Test-Path "$SourceDir\htb-model-training") {
        Copy-Item "$SourceDir\htb-model-training" "$TargetDrive\training" -Recurse -Force
        Write-Host "  Training code copied"
    }
}

# Create deployment info
Write-Host "[6/6] Creating deployment info..." -ForegroundColor Green
$deployInfo = @"
HTB Pentest Agent - USB Deployment
===================================
Deployed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Source: $SourceDir

Contents:
- agent/          : Agent code and configuration
- Ollama/         : Portable Ollama installation
- start-gui.bat   : Launch GUI interface
- start-agent.bat : Launch CLI interface

First-time setup:
1. Ensure Python 3.8+ is installed
2. Run start-gui.bat or start-agent.bat
3. The launcher will install dependencies and register the model

For Kali Docker support:
1. Install Docker Desktop
2. Click "Start Kali" in the GUI sidebar
3. Full Kali toolkit becomes available
"@

$deployInfo | Out-File "$TargetDrive\DEPLOYMENT_INFO.txt" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To use: Insert USB and run start-gui.bat" -ForegroundColor Cyan
Write-Host ""

# Show disk usage
$usedSpace = (Get-ChildItem $TargetDrive -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Total size: $([math]::Round($usedSpace, 2)) MB" -ForegroundColor Yellow
