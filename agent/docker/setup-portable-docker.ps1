# Setup Portable Docker on USB Drive
# This configures Docker Desktop to use the USB drive for storage

param(
    [Parameter(Mandatory=$true)]
    [string]$UsbDrive = "L:"
)

Write-Host "================================================"
Write-Host "  Portable Docker Setup for USB Drive"
Write-Host "================================================"
Write-Host ""

$dockerDataPath = "$UsbDrive\docker-data"
$dockerDaemonConfig = "$env:ProgramData\Docker\config\daemon.json"

# Check if Docker Desktop is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker Desktop not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop first:" -ForegroundColor Yellow
    Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    exit 1
}

# Check if Docker is running
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "[ERROR] Docker Desktop is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop first" -ForegroundColor Yellow
    exit 1
}

# Create Docker data directory on USB
Write-Host "[1/4] Creating Docker data directory on USB..."
New-Item -ItemType Directory -Force -Path $dockerDataPath | Out-Null
New-Item -ItemType Directory -Force -Path "$dockerDataPath\volumes" | Out-Null
New-Item -ItemType Directory -Force -Path "$dockerDataPath\images" | Out-Null
Write-Host "      Created: $dockerDataPath" -ForegroundColor Green

# Backup existing daemon.json if it exists
Write-Host ""
Write-Host "[2/4] Configuring Docker daemon..."
if (Test-Path $dockerDaemonConfig) {
    $backup = "$dockerDaemonConfig.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $dockerDaemonConfig $backup
    Write-Host "      Backed up existing config to: $backup" -ForegroundColor Yellow
}

# Create new daemon.json with USB data root
$daemonConfig = @{
    "data-root" = $dockerDataPath
    "storage-driver" = "windowsfilter"
}

$configDir = Split-Path $dockerDaemonConfig -Parent
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
$daemonConfig | ConvertTo-Json | Set-Content $dockerDaemonConfig -Force
Write-Host "      Updated Docker daemon config" -ForegroundColor Green

# Restart Docker Desktop
Write-Host ""
Write-Host "[3/4] Restarting Docker Desktop..."
Write-Host "      This may take 1-2 minutes..." -ForegroundColor Yellow

# Stop Docker Desktop
Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start Docker Desktop
Start-Service -Name "com.docker.service"

# Wait for Docker to be ready
Write-Host "      Waiting for Docker to start..."
$timeout = 120
$elapsed = 0
while ($elapsed -lt $timeout) {
    $info = docker info 2>$null
    if ($info) {
        Write-Host "      Docker is ready!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if ($elapsed -ge $timeout) {
    Write-Host "      [WARNING] Docker restart timed out" -ForegroundColor Yellow
    Write-Host "      Please restart Docker Desktop manually" -ForegroundColor Yellow
}

# Load HTB Kali image
Write-Host ""
Write-Host "[4/4] Loading HTB Kali image to USB storage..."
$imageTar = "$UsbDrive\agent\docker\htb-pentest-kali.tar"

if (Test-Path $imageTar) {
    docker load -i $imageTar
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      Image loaded successfully!" -ForegroundColor Green
    } else {
        Write-Host "      [ERROR] Failed to load image" -ForegroundColor Red
    }
} else {
    Write-Host "      [WARNING] Image tarball not found: $imageTar" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================"
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================"
Write-Host ""
Write-Host "Docker is now configured to use USB storage:" -ForegroundColor Cyan
Write-Host "  Data Root: $dockerDataPath"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run: cd $UsbDrive\agent\docker"
Write-Host "  2. Run: docker compose up -d"
Write-Host ""
Write-Host "To restore default Docker settings:"
Write-Host "  - Delete: $dockerDaemonConfig"
Write-Host "  - Restart Docker Desktop"
Write-Host ""
