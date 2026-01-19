# PyTorch Installation with Real-time Progress
# For CUDA 12.4 (compatible with driver 581.29)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PyTorch + CUDA 12.4 Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonPath = "C:\Users\sirra\AppData\Local\Programs\Python\Python311\python.exe"

# Set longer timeout
Write-Host "[1/4] Configuring pip timeout..." -ForegroundColor Yellow
& $pythonPath -m pip config set global.timeout 1000 2>$null

# Upgrade pip first
Write-Host "[2/4] Upgrading pip..." -ForegroundColor Yellow
& $pythonPath -m pip install --upgrade pip --quiet

# Install PyTorch with progress
Write-Host ""
Write-Host "[3/4] Installing PyTorch + CUDA 12.4 (~2.5GB download)" -ForegroundColor Yellow
Write-Host "      This will take several minutes. Progress shown below:" -ForegroundColor Gray
Write-Host ""

# Run pip with progress visible
& $pythonPath -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --progress-bar on

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[!] Installation failed. Retrying..." -ForegroundColor Red
    & $pythonPath -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --progress-bar on
}

# Verify installation
Write-Host ""
Write-Host "[4/4] Verifying installation..." -ForegroundColor Yellow

$verifyScript = @"
import torch
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA Version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"@

& $pythonPath -c $verifyScript

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "PyTorch installed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Installation may have issues." -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}
