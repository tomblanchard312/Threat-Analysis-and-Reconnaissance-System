# Quickstart Deployment Guide

Deploy the HTB Pentest AI Assistant to a USB drive (Windows) or Jetson Orin Nano (Linux ARM64).

---

## Prerequisites (Both Platforms)

- **Python 3.8+** with pip
- **Internet connection** for initial model download
- The full repository cloned locally

---

## USB Deployment (Windows)

### What You Need

- USB drive (32GB+ recommended, 64GB+ if bundling model)
- Windows 10/11 host with PowerShell
- Ollama installed locally (auto-copied to USB)

### Step 1: Deploy to USB

Open PowerShell as Administrator and run:

```powershell
cd F:\Repos\Pen-Testing-AI-Assistant\deploy\usb-deploy

# Basic deployment (downloads Ollama, model pulled from registry on first run)
.\deploy-to-usb.ps1 -TargetDrive E:

# With portable Node.js for MCP servers
.\deploy-to-usb.ps1 -TargetDrive E: -DownloadNodeJS

# Bundle a local GGUF model for air-gapped / offline use
.\deploy-to-usb.ps1 -TargetDrive E: -LocalModel "C:\models\htb-pentest-q4_k_m.gguf"

# Use a local Ollama install instead of downloading
.\deploy-to-usb.ps1 -TargetDrive E: -LocalOllama "C:\Program Files\Ollama"

# Full offline deployment (local Ollama + local model + Node.js)
.\deploy-to-usb.ps1 -TargetDrive E: -LocalModel "C:\models\htb-pentest-q4_k_m.gguf" -DownloadNodeJS

# Clean deploy (wipes existing deployment first)
.\deploy-to-usb.ps1 -TargetDrive E: -CleanDeploy
```

Or use the batch wrapper:

```cmd
deploy-to-usb.bat E:
deploy-to-usb.bat E: -LocalModel "C:\models\htb-pentest.gguf"
deploy-to-usb.bat E: -CleanDeploy
```

### Deploy Options

| Flag | Description |
|------|-------------|
| `-TargetDrive` | Drive letter (required), e.g. `E:` |
| `-LocalOllama` | Path to local Ollama install to copy instead of downloading |
| `-LocalModel` | Path to `.gguf` model file to bundle for offline use |
| `-DownloadNodeJS` | Download portable Node.js (~30MB) for MCP servers |
| `-SkipOllama` | Skip Ollama setup (if already on USB) |
| `-SkipModel` | Skip model setup (if already on USB) |
| `-CleanDeploy` | Remove existing files before deploying |

### Step 2: Launch on Any Windows Machine

Insert the USB and run:

```cmd
E:\start-gui.bat
```

The launcher will:
1. Check and install Python dependencies (requests, customtkinter, Pillow, scikit-learn, PyPDF2, pdfplumber)
2. Start portable Ollama with CUDA auto-detection
3. Start Docker Desktop and Kali container (if Docker is installed)
4. Build/pull the AI model (prompts for source if no local GGUF found)
5. Launch the GUI

### Step 3: First Run - Model Setup

If no `.gguf` file was bundled, the launcher prompts you to choose:

1. **Pull from Ollama Registry** (recommended) - Downloads `sirrand/htb-pentest` (~4.4GB)
2. **Lite Mode** - Uses `mistral:7b` as a base model
3. **Custom model** - Enter any Ollama model name

### USB Directory Structure

```
E:\
├── agent/              Agent code and configuration
│   ├── pentest-gui.py  Main GUI application
│   ├── docker/         Kali Docker configuration
│   ├── cases/          Investigation case files
│   └── knowledge_base/ RAG document index
├── mcp-servers/        MCP server implementations
├── models/             GGUF model file(s)
├── Ollama/             Portable Ollama installation
├── nodejs/             Portable Node.js (if deployed)
├── start-gui.bat       Launch GUI
├── start-agent.bat     Launch CLI
└── setup-models.bat    Pull additional models (run once)
```

---

## Jetson Orin Nano Deployment (Linux ARM64)

### What You Need

- Jetson Orin Nano (8GB recommended)
- JetPack 6.x installed
- NVMe SSD (64GB+ recommended)
- Network connection for package downloads

### Step 1: Copy Files to Jetson

**Option A: From USB**

```bash
# Mount USB on Jetson
sudo mount /dev/sda1 /mnt/usb

# Run directly from USB
sudo bash /mnt/usb/deploy/orin-nano-deploy/deploy-to-jetson.sh
```

**Option B: Over SSH**

```bash
# From your development machine
scp -r ./deploy/orin-nano-deploy user@jetson-ip:/tmp/
ssh user@jetson-ip
sudo bash /tmp/orin-nano-deploy/deploy-to-jetson.sh
```

### Step 2: Run the Deployment

```bash
# Basic deployment
sudo ./deploy-to-jetson.sh

# With Docker and Kali toolkit
sudo ./deploy-to-jetson.sh --with-docker

# With training code included
sudo ./deploy-to-jetson.sh --with-training

# Custom swap size (default is 32GB, increase for larger models)
sudo ./deploy-to-jetson.sh --swap-size 48

# Full deployment
sudo ./deploy-to-jetson.sh --with-docker --with-training --swap-size 48
```

### Deploy Options

| Flag | Description |
|------|-------------|
| `--with-docker` | Install Docker and build Kali container |
| `--with-training` | Include LoRA training code |
| `--swap-size GB` | Swap file size in GB (default: 32) |

### What the Script Does

1. Installs system dependencies (Python3, curl, wget, git, htop, nvtop)
2. Creates swap file for large model support
3. Installs Ollama for ARM64 with CUDA support
4. Configures Ollama as a systemd service (listens on 0.0.0.0:11434)
5. Copies agent files to `/opt/htb-pentest/`
6. Registers the model with Ollama
7. Installs Python dependencies
8. (Optional) Installs Docker and builds Kali container

### Step 3: Pull the Model

```bash
# Primary pentest model
ollama pull sirrand/htb-pentest

# Planning model (for multi-step task reasoning)
ollama pull glm4:9b
```

### Step 4: Launch

```bash
# CLI mode
/opt/htb-pentest/start-agent.sh

# GUI mode (requires display connected or X forwarding)
/opt/htb-pentest/start-gui.sh

# Jupyter case analysis
jupyter notebook /opt/htb-pentest/agent/case_analysis.ipynb
```

### Jetson Directory Structure

```
/opt/htb-pentest/
├── agent/
│   ├── pentest-gui.py
│   ├── pentest-agent.py
│   ├── kali_tool_catalog.py
│   ├── knowledge_base.py
│   ├── docker/
│   ├── cases/
│   └── knowledge_base/
├── mcp-servers/
├── ollama/models/
├── start-agent.sh
└── start-gui.sh
```

---

## Post-Deployment Steps (Both Platforms)

### 1. Configure API Keys (Optional)

Edit `settings.json` in the agent directory to add API keys for enhanced OSINT:

```json
{
  "shodan_api_key": "YOUR_SHODAN_KEY",
  "github_token": "YOUR_GITHUB_TOKEN"
}
```

Or configure via the GUI: **Settings > General** tab.

### 2. Verify Docker / Kali Tools

If Docker is available, the GUI sidebar shows a Docker status indicator:
- **Green** - Container running, tools available
- **Yellow** - Docker running, container needs setup
- **Red** - Docker not available

To manually start the Kali container:

```bash
# Windows
cd agent\docker
docker-compose up -d

# Linux
cd /opt/htb-pentest/agent/docker
docker compose up -d
```

### 3. Import Knowledge Base Documents

1. Open the GUI
2. Click **Knowledge Base** in the sidebar
3. Go to the **Documents** tab
4. Click **Add Document** and select PDF or text files
5. Documents are chunked and indexed for RAG retrieval

### 4. Run a Quick Smoke Test

1. Launch the GUI and confirm the status bar shows the model name
2. Type: `scan 192.168.1.1 with nmap` - A task plan should generate and execute in Docker
3. Click **New Case** to create an investigation case file
4. Click **Pen Test** to open the scoping dialog, set a target, and start
5. Check Docker panel shows green status, click **Open Shell** to verify Kali terminal

### 5. Enable Auto-Start (Jetson Only)

```bash
sudo systemctl enable ollama
sudo systemctl enable htb-pentest-api
```

### 6. Performance Tuning (Jetson Only)

```bash
# Set maximum GPU performance
sudo nvpmodel -m 0
sudo jetson_clocks

# Verify swap is active
free -h

# Monitor GPU usage
nvtop
```

### 7. Update Kali Tools

In the GUI, click **Update Kali Tools** in the Docker panel to run `apt upgrade` inside the container. Missing tools are auto-installed when first used.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama won't start on USB | Check `OLLAMA_LLM_LIBRARY=cuda_v13` is set. Try running `ollama serve` manually. |
| Model not found | Run `ollama list` to check installed models. Pull with `ollama pull sirrand/htb-pentest`. |
| Docker container missing | Run `docker-compose up -d` from the `agent/docker/` directory. |
| GUI fails to launch | Verify Python dependencies: `pip install customtkinter requests Pillow scikit-learn` |
| Slow inference on Jetson | Ensure NVMe SSD (not SD card). Check swap: `free -h`. Set `nvpmodel -m 0`. |
| Out of memory on Jetson | Use Q4_K_S quantization. Reduce context: edit `PARAMETER num_ctx 2048` in Modelfile. |
| Tools not found in Docker | Click **Update Kali Tools** or the tool will auto-install on first use. |
