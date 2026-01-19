# CUDA Toolkit 12.1 Installer with Progress
# Run this script in PowerShell as Administrator

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CUDA Toolkit 12.1 Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# CUDA 12.1 Update 1 - matches PyTorch cu121
$cudaUrl = "https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda_12.1.1_531.14_windows.exe"
$installerPath = Join-Path $env:TEMP "cuda_12.1.1_installer.exe"
$installerSize = 3.1  # GB approximate

Write-Host "[1/3] Downloading CUDA Toolkit 12.1.1 (~3.1 GB)..." -ForegroundColor Yellow
Write-Host "      This will take several minutes depending on your connection." -ForegroundColor Gray
Write-Host ""

# Download with progress
$webClient = New-Object System.Net.WebClient
$downloadComplete = $false

# Progress tracking
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$lastBytes = 0
$lastTime = 0

Register-ObjectEvent -InputObject $webClient -EventName DownloadProgressChanged -Action {
    $percent = $EventArgs.ProgressPercentage
    $received = [math]::Round($EventArgs.BytesReceived / 1GB, 2)
    $total = [math]::Round($EventArgs.TotalBytesToReceive / 1GB, 2)

    # Calculate speed
    $elapsed = $stopwatch.Elapsed.TotalSeconds
    if ($elapsed -gt 0) {
        $speed = [math]::Round($EventArgs.BytesReceived / $elapsed / 1MB, 1)
    } else {
        $speed = 0
    }

    # Progress bar
    $barLength = 40
    $filled = [math]::Floor($percent / 100 * $barLength)
    $empty = $barLength - $filled
    $bar = "[" + ("=" * $filled) + (">" * [math]::Min(1, $empty)) + (" " * [math]::Max(0, $empty - 1)) + "]"

    Write-Host -NoNewline "`r      $bar $percent% | ${received}GB / ${total}GB | ${speed} MB/s    "
} | Out-Null

Register-ObjectEvent -InputObject $webClient -EventName DownloadFileCompleted -Action {
    $script:downloadComplete = $true
} | Out-Null

try {
    $webClient.DownloadFileAsync([Uri]$cudaUrl, $installerPath)

    while (-not $downloadComplete) {
        Start-Sleep -Milliseconds 500
    }

    Write-Host ""
    Write-Host "      Download complete!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "      Download failed: $_" -ForegroundColor Red
    exit 1
} finally {
    $webClient.Dispose()
    Get-EventSubscriber | Unregister-Event
}

Write-Host ""
Write-Host "[2/3] Installing CUDA Toolkit (this takes 5-10 minutes)..." -ForegroundColor Yellow
Write-Host "      A separate installer window will open." -ForegroundColor Gray
Write-Host "      Select 'Express Installation' for quickest setup." -ForegroundColor Gray
Write-Host ""

# Run installer - using GUI mode so user can see progress
Start-Process -FilePath $installerPath -ArgumentList "-s" -Wait

Write-Host "[3/3] Verifying installation..." -ForegroundColor Yellow

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check for nvcc
$nvccPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin\nvcc.exe"
if (Test-Path $nvccPath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "CUDA Toolkit installed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    & $nvccPath --version
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Installation may have completed." -ForegroundColor Yellow
    Write-Host "Please restart your terminal/IDE." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next: Restart your terminal, then run the training script." -ForegroundColor Cyan
