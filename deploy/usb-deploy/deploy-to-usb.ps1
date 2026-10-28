# HTB Pentest Agent - USB Deployment Script
# Deploys the self-contained pentest AI to a USB drive
# Run as Administrator: powershell -ExecutionPolicy Bypass -File deploy-to-usb.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetDrive,  # e.g., "E:"

    [Parameter(Mandatory=$false)]
    [string]$ModelPath,    # Path to GGUF model file (e.g., "C:\htb-model-training\htb-pentest-v4-gguf\model-q4_k_m.gguf")

    [switch]$DownloadOllama,   # Download fresh Ollama instead of copying existing
    [switch]$DownloadNodeJS,   # Download portable Node.js for MCP servers
    [switch]$SkipModel,        # Skip model deployment (use if model already on USB)
    [switch]$CleanDeploy       # Remove existing files before deploying
)

$ErrorActionPreference = "Stop"

# Get the repository root (two levels up from this script)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $ScriptDir

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
Write-Host "Source: $RepoRoot" -ForegroundColor Yellow
Write-Host ""

# Clean deploy if requested
if ($CleanDeploy) {
    Write-Host "[CLEAN] Removing existing deployment..." -ForegroundColor Yellow
    $foldersToRemove = @("agent", "Ollama", "models", "nodejs")
    foreach ($folder in $foldersToRemove) {
        $path = "$TargetDrive\$folder"
        if (Test-Path $path) {
            Remove-Item $path -Recurse -Force
            Write-Host "  Removed: $folder"
        }
    }
    $filesToRemove = @("start-gui.bat", "start-agent.bat", "autorun.inf", "DEPLOYMENT_INFO.txt", "README.md")
    foreach ($file in $filesToRemove) {
        $path = "$TargetDrive\$file"
        if (Test-Path $path) {
            Remove-Item $path -Force
            Write-Host "  Removed: $file"
        }
    }
    Write-Host ""
}

# Create directory structure
Write-Host "[1/6] Creating directory structure..." -ForegroundColor Green
$directories = @(
    "$TargetDrive\agent",
    "$TargetDrive\agent\docker",
    "$TargetDrive\agent\docker\shared",
    "$TargetDrive\agent\tools",
    "$TargetDrive\agent\transcripts",
    "$TargetDrive\agent\knowledge_base",
    "$TargetDrive\agent\cases",
    "$TargetDrive\mcp-servers",
    "$TargetDrive\models",
    "$TargetDrive\Ollama",
    "$TargetDrive\Ollama\models",
    "$TargetDrive\nodejs"
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
    "tool_process.py",
    "pentest-gui.py",
    "kali_tool_catalog.py",
    "knowledge_base.py",
    "portable_docker.py",
    "case_analysis.ipynb",
    "Modelfile",
    "Modelfile.lite",
    "settings.json",
    "kali_tools.json",
    "corrections.json"
)

foreach ($file in $agentFiles) {
    $src = "$RepoRoot\agent\$file"
    $dst = "$TargetDrive\agent\$file"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied: $file"
    } else {
        Write-Host "  [SKIP] Not found: $file" -ForegroundColor DarkGray
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
    $src = "$RepoRoot\agent\docker\$file"
    $dst = "$TargetDrive\agent\docker\$file"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied: $file"
    }
}

# Copy tools
if (Test-Path "$RepoRoot\agent\tools") {
    Write-Host "  Copying tools..."
    Copy-Item "$RepoRoot\agent\tools\*" "$TargetDrive\agent\tools\" -Force -ErrorAction SilentlyContinue
}

# Copy MCP servers
if (Test-Path "$RepoRoot\mcp-servers") {
    Write-Host "  Copying MCP servers..."
    Copy-Item "$RepoRoot\mcp-servers\*" "$TargetDrive\mcp-servers\" -Recurse -Force -ErrorAction SilentlyContinue
}

# Copy knowledge base data (if exists)
if (Test-Path "$RepoRoot\agent\knowledge_base") {
    Write-Host "  Copying knowledge base..."
    Copy-Item "$RepoRoot\agent\knowledge_base\*" "$TargetDrive\agent\knowledge_base\" -Recurse -Force -ErrorAction SilentlyContinue
}

# Copy case files (if exists)
if (Test-Path "$RepoRoot\agent\cases") {
    Write-Host "  Copying case files..."
    Copy-Item "$RepoRoot\agent\cases\*" "$TargetDrive\agent\cases\" -Recurse -Force -ErrorAction SilentlyContinue
}

# Copy root launchers
Write-Host "[4/6] Copying launcher scripts..." -ForegroundColor Green
$rootFiles = @(
    @{src="start-gui.bat"; dst="start-gui.bat"},
    @{src="start-agent.bat"; dst="start-agent.bat"},
    @{src="autorun.inf"; dst="autorun.inf"},
    @{src="README.md"; dst="README.md"}
)

foreach ($item in $rootFiles) {
    $src = "$RepoRoot\$($item.src)"
    $dst = "$TargetDrive\$($item.dst)"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied: $($item.dst)"
    }
}

# Handle Ollama
Write-Host "[5/6] Setting up Ollama and model..." -ForegroundColor Green

# Check for existing Ollama installation to copy
$ollamaSources = @(
    "$RepoRoot\Ollama",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama",
    "$env:LOCALAPPDATA\Programs\Ollama"
)

$ollamaFound = $false
if ($DownloadOllama) {
    Write-Host "  Downloading Ollama..."
    $ollamaUrl = "https://ollama.com/download/ollama-windows-amd64.zip"
    $ollamaZip = "$env:TEMP\ollama.zip"
    Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaZip
    Expand-Archive -Path $ollamaZip -DestinationPath "$TargetDrive\Ollama" -Force
    Remove-Item $ollamaZip
    Write-Host "  Ollama downloaded and extracted"
    $ollamaFound = $true
} else {
    foreach ($ollamaPath in $ollamaSources) {
        if (Test-Path "$ollamaPath\ollama.exe") {
            Write-Host "  Found Ollama at: $ollamaPath"
            Copy-Item "$ollamaPath\ollama.exe" "$TargetDrive\Ollama\" -Force
            if (Test-Path "$ollamaPath\app.ico") {
                Copy-Item "$ollamaPath\app.ico" "$TargetDrive\Ollama\" -Force
            }
            if (Test-Path "$ollamaPath\lib") {
                Copy-Item "$ollamaPath\lib" "$TargetDrive\Ollama\" -Recurse -Force
            }
            Write-Host "  Ollama copied"
            $ollamaFound = $true
            break
        }
    }
}

if (-not $ollamaFound) {
    Write-Host "  [WARN] Ollama not found. Run with -DownloadOllama or install manually." -ForegroundColor Yellow
}

# Create model setup script for additional models (GLM-4.7-Flash, GLM-4.6V)
$modelSetupScript = @'
@echo off
echo ============================================
echo   HTB Pentest Agent - Model Setup
echo ============================================
echo.
echo This script will pull the required AI models.
echo Make sure Ollama is running before continuing.
echo.
pause

echo.
echo [1/3] Pulling HTB-Pentest model...
Ollama\ollama.exe pull sirrand/htb-pentest
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Could not pull htb-pentest. Will build from local Modelfile if available.
)

echo.
echo [2/3] Pulling GLM-4.7-Flash (planning/tool calling model)...
echo Note: This is a 30B MoE model - download may take a while.
Ollama\ollama.exe pull glm4:9b
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] GLM-4.7-Flash not available. Using htb-pentest for all tasks.
)

echo.
echo [3/3] Pulling GLM-4.6V (vision model - optional)...
Ollama\ollama.exe pull minicpm-v:8b
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Vision model not available. Image analysis will be disabled.
)

echo.
echo ============================================
echo   Model setup complete!
echo ============================================
echo.
echo Available models:
Ollama\ollama.exe list
echo.
pause
'@
$modelSetupScript | Out-File "$TargetDrive\setup-models.bat" -Encoding ASCII
Write-Host "  Created: setup-models.bat (run after first launch to pull additional models)"

# Copy model file
if (-not $SkipModel) {
    if ($ModelPath -and (Test-Path $ModelPath)) {
        Write-Host "  Copying model file (this may take a while)..."
        $modelName = Split-Path $ModelPath -Leaf
        # Standardize name to htb-pentest.gguf
        $targetModelName = "htb-pentest.gguf"
        Copy-Item $ModelPath "$TargetDrive\models\$targetModelName" -Force
        Write-Host "  Model copied: $modelName -> models\$targetModelName"
    } else {
        # Look for existing model files
        $modelPaths = @(
            "C:\htb-model-training\htb-pentest-v4-gguf\model-q4_k_m.gguf",
            "$RepoRoot\models\*.gguf",
            "$RepoRoot\agent\*.gguf"
        )
        $foundModel = $null
        foreach ($pattern in $modelPaths) {
            $found = Get-ChildItem $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) {
                $foundModel = $found.FullName
                break
            }
        }

        if ($foundModel) {
            Write-Host "  Found model: $foundModel"
            Write-Host "  Copying model file (this may take a while)..."
            Copy-Item $foundModel "$TargetDrive\models\htb-pentest.gguf" -Force
            Write-Host "  Model copied to: models\htb-pentest.gguf"
        } else {
            Write-Host "  [INFO] No model file found. Specify with -ModelPath or the agent will pull from registry." -ForegroundColor Cyan
        }
    }
}

# Create Modelfile for the models folder structure
$modelfileContent = @'
# HTB Pentest Model - Trained on Hack The Box writeups
# Fine-tuned Mistral 7B with QLoRA

FROM ../models/htb-pentest.gguf

# Model parameters optimized for pentest assistance
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

# System prompt
SYSTEM """You are a helpful penetration testing assistant trained on Hack The Box writeups. You can execute commands using the pentest-tools skill when asked to scan, ping, or perform network operations. For action requests, respond with a tool call in this format: <tool_call>{"name": "pentest-tools", "arguments": {"command": "cmd", "args": "args"}}</tool_call>. For questions and explanations, provide detailed educational responses. Always emphasize authorized use only.

Your expertise includes:
- Reconnaissance and enumeration techniques
- Web application security testing
- Network exploitation
- Privilege escalation (Linux and Windows)
- Post-exploitation techniques
- Common security tools (nmap, burp suite, metasploit, etc.)

Important guidelines:
- Always emphasize that techniques should only be used in authorized environments
- Provide educational context for security concepts
- Explain the "why" behind techniques, not just the "how"
- Reference real-world scenarios from HTB machines when relevant
"""

# ChatML template format
TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>"""

# License notice
LICENSE """
This model is trained on publicly available Hack The Box writeups for educational purposes.
Use only in authorized testing environments. The creator is not responsible for misuse.
"""
'@

$modelfileContent | Out-File "$TargetDrive\agent\Modelfile" -Encoding UTF8
Write-Host "  Updated Modelfile for models folder structure"

# Handle Node.js (for MCP servers)
Write-Host "[6/6] Setting up portable Node.js..." -ForegroundColor Green
$nodeJsFound = $false

if ($DownloadNodeJS) {
    Write-Host "  Downloading portable Node.js (LTS)..."
    $nodeVersion = "v20.11.0"
    $nodeUrl = "https://nodejs.org/dist/$nodeVersion/node-$nodeVersion-win-x64.zip"
    $nodeZip = "$env:TEMP\nodejs.zip"

    try {
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeZip
        Write-Host "  Extracting..."
        Expand-Archive -Path $nodeZip -DestinationPath "$env:TEMP\nodejs_temp" -Force

        # Move contents from nested folder to nodejs folder
        $extractedFolder = Get-ChildItem "$env:TEMP\nodejs_temp" -Directory | Select-Object -First 1
        if ($extractedFolder) {
            Copy-Item "$($extractedFolder.FullName)\*" "$TargetDrive\nodejs\" -Recurse -Force
        }

        Remove-Item $nodeZip -Force
        Remove-Item "$env:TEMP\nodejs_temp" -Recurse -Force
        Write-Host "  Node.js $nodeVersion installed to: nodejs\"
        $nodeJsFound = $true
    } catch {
        Write-Host "  [WARN] Failed to download Node.js: $_" -ForegroundColor Yellow
    }
} else {
    # Check if Node.js already exists on USB
    if (Test-Path "$TargetDrive\nodejs\node.exe") {
        Write-Host "  Node.js already present on USB"
        $nodeJsFound = $true
    } else {
        Write-Host "  [INFO] No Node.js on USB. MCP servers require Node.js." -ForegroundColor Cyan
        Write-Host "  [INFO] Run with -DownloadNodeJS to add portable Node.js (~30MB)" -ForegroundColor Cyan
    }
}

# Install MCP server dependencies if Node.js is available
if (Test-Path "$TargetDrive\nodejs\node.exe") {
    $mcpServerDirs = Get-ChildItem "$TargetDrive\agent\mcp-servers" -Directory -ErrorAction SilentlyContinue
    foreach ($mcpDir in $mcpServerDirs) {
        if (Test-Path "$($mcpDir.FullName)\package.json") {
            Write-Host "  Installing dependencies for $($mcpDir.Name)..."
            Push-Location $mcpDir.FullName
            try {
                & "$TargetDrive\nodejs\npm.cmd" install --silent 2>&1 | Out-Null
                Write-Host "    Done"
            } catch {
                Write-Host "    [WARN] Failed to install: $_" -ForegroundColor Yellow
            }
            Pop-Location
        }
    }
}

# Determine deployment info
$hasModel = Test-Path "$TargetDrive\models\htb-pentest.gguf"
$hasNodeJs = Test-Path "$TargetDrive\nodejs\node.exe"
$deploymentMode = if ($hasModel) { "Full (local GGUF model)" } else { "Lite (will pull from registry)" }
$mcpStatus = if ($hasNodeJs) { "Enabled (portable Node.js included)" } else { "Disabled (no Node.js)" }

# Create deployment info
$deployInfo = @"
HTB Pentest Agent - USB Deployment
===================================
Deployed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Mode: $deploymentMode
MCP Servers: $mcpStatus

Directory Structure:
- agent/          : Agent code and configuration
- agent/cases/    : Case files for investigation tracking
- agent/knowledge_base/ : RAG document index
- mcp-servers/    : MCP server implementations
- models/         : GGUF model file(s)
- Ollama/         : Portable Ollama installation
- nodejs/         : Portable Node.js (for MCP servers)
- start-gui.bat   : Launch GUI interface
- start-agent.bat : Launch CLI interface
- setup-models.bat: Pull additional AI models (run once)
- README.md       : Full documentation

Case File Analysis:
- agent/case_analysis.ipynb : Jupyter notebook for post-engagement analysis
- Open in VS Code or run: jupyter notebook agent/case_analysis.ipynb
- Features: Target analysis, findings visualization, cross-case comparison, CSV export

First-time setup:
1. Ensure Python 3.8+ is installed with pip
2. Run start-gui.bat or start-agent.bat
3. The launcher will install dependencies and set up the model
4. (Optional) Run setup-models.bat to pull additional models

Multi-Model Architecture:
The agent uses intelligent model routing for optimal performance:

  HTB-Pentest (Primary)     - Domain knowledge, methodology, quick answers
  GLM-4.7-Flash (Planning)  - Attack planning, tool calling, large context (200K)
  GLM-4.6V (Vision)         - Screenshot/image analysis

The agent automatically selects the best model based on your query:
- "How do I enumerate SMB?" → HTB-Pentest (domain knowledge)
- "Plan an attack on 192.168.1.0/24" → GLM-4.7-Flash (planning)
- [Paste screenshot] "What vulnerability is this?" → GLM-4.6V (vision)

Model Setup:
- If models/htb-pentest.gguf exists, builds from local Modelfile (full version)
- If no local model exists, pulls from Ollama registry (sirrand/htb-pentest)
- Run setup-models.bat to pull GLM-4.7-Flash and GLM-4.6V for full features
- Fallback: Uses mistral:7b base with Modelfile.lite

Settings > Model Routing:
- Auto-route queries: Let the agent choose the best model
- Show model indicator: See which model is responding
- Extended thinking: Enable step-by-step reasoning for planning tasks

MCP Server Setup:
- Requires Node.js (included in nodejs/ if deployed with -DownloadNodeJS)
- Enable MCP servers in Settings > MCP Servers
- Available: ollama-claude (self-hosted AI), pentest-mcp, filesystem, shell, git, fetch, memory

Ollama Launch (v0.15.2+):
- ollama launch claude    - Run Claude Code with local models
- ollama launch codex     - Run OpenAI Codex CLI
- ollama launch opencode  - Run OpenCode
- ollama launch clawdbot  - Run Clawdbot
- ollama launch droid     - Run Droid

For Kali Docker support:
1. Install Docker Desktop
2. Click "Start Kali" in the GUI sidebar
3. Full Kali toolkit becomes available

Requirements:
- Python 3.8+ (python.org)
- Windows 10/11 (for portable Ollama)
- Docker Desktop (optional, for Kali tools)
- 16GB+ RAM recommended for GLM-4.7-Flash
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
Write-Host ""

# Show what's deployed
Write-Host "Deployed contents:" -ForegroundColor Cyan
Get-ChildItem $TargetDrive -Name | ForEach-Object {
    $item = "$TargetDrive\$_"
    if (Test-Path $item -PathType Container) {
        $size = (Get-ChildItem $item -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  [$_/] $([math]::Round($size, 1)) MB"
    } else {
        $size = (Get-Item $item).Length / 1MB
        Write-Host "  $_ ($([math]::Round($size, 2)) MB)"
    }
}
