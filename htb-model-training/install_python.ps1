# Install Python 3.11 on Windows
# Run as Administrator for best results

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python 3.11 Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Python already exists
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if ($pythonPath -and -not ($pythonPath.Source -like "*WindowsApps*")) {
    Write-Host "Python already installed at: $($pythonPath.Source)" -ForegroundColor Green
    python --version
    exit 0
}

# Download Python installer
$installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$installerPath = Join-Path $env:TEMP "python-3.11.9-amd64.exe"

Write-Host "`n[1/3] Downloading Python 3.11.9..." -ForegroundColor Yellow
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
Write-Host "Downloaded to: $installerPath" -ForegroundColor Green

# Install Python silently with pip and add to PATH
Write-Host "`n[2/3] Installing Python (this may take a minute)..." -ForegroundColor Yellow
$installArgs = @(
    "/quiet",
    "InstallAllUsers=0",
    "PrependPath=1",
    "Include_pip=1",
    "Include_test=0"
)

Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow

Write-Host "`n[3/3] Verifying installation..." -ForegroundColor Yellow

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Find Python
$userPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"
if (Test-Path $userPython) {
    Write-Host "Python installed at: $userPython" -ForegroundColor Green
    & $userPython --version
    & $userPython -m pip --version
} else {
    Write-Host "Python installed. Please restart your terminal/IDE to use it." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Please restart your terminal or IDE" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
