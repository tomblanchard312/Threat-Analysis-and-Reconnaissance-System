# HTB Model Training Script with Real-time Progress
# Installs Unsloth and runs training

$ErrorActionPreference = "Continue"
$pythonPath = "C:\Users\sirra\AppData\Local\Programs\Python\Python311\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HTB Pentest Model Training" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install training dependencies
Write-Host "[1/3] Installing training dependencies..." -ForegroundColor Yellow
Write-Host "      This includes: transformers, peft, trl, bitsandbytes, datasets" -ForegroundColor Gray
Write-Host ""

& $pythonPath -m pip install --upgrade transformers peft trl datasets accelerate bitsandbytes sentencepiece protobuf --progress-bar on

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Some packages may have failed, continuing anyway..." -ForegroundColor Yellow
}

# Step 2: Verify GPU
Write-Host ""
Write-Host "[2/3] Verifying GPU setup..." -ForegroundColor Yellow

$gpuCheck = @"
import torch
print(f'  PyTorch: {torch.__version__}')
print(f'  CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
    mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'  VRAM: {mem:.1f} GB')
"@

& $pythonPath -c $gpuCheck

# Step 3: Run training
Write-Host ""
Write-Host "[3/3] Starting model training..." -ForegroundColor Yellow
Write-Host "      Training ~5000 examples on Mistral 7B with QLoRA" -ForegroundColor Gray
Write-Host "      Estimated time: 2-4 hours on RTX 3090" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Training Progress:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Set-Location "f:\Repos\Orin_Nano_Super_Lab\htb-model-training"

& $pythonPath -u "f:\Repos\Orin_Nano_Super_Lab\htb-model-training\train_model.py"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Training script finished!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
