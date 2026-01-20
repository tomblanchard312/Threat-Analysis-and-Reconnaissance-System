# HTB Pentest Agent

AI-powered penetration testing assistant with tool execution capabilities. Trained on Hack The Box writeups for educational security testing.

## Quick Start

**Pull the model from Ollama:**
```bash
ollama pull sirrand/htb-pentest
```

**Or deploy to USB:**
```powershell
.\deploy\usb-deploy\deploy-to-usb.ps1 -TargetDrive E: -RemoteModel "sirrand/htb-pentest"
```

## Features

- **HTB-Trained Model**: Fine-tuned on Hack The Box writeups for realistic pentesting assistance
- **Tool Execution**: Direct command execution via Kali Docker container (600+ tools)
- **Knowledge Base (RAG)**: Import PDFs and documents to enhance model responses
- **Self-Learning**: Feedback system to correct and improve model behavior over time
- **Portable Deployment**: USB drive or Jetson Nano deployment options
- **MCP Integration**: Model Context Protocol support for extended capabilities

---

## Deployment Options

### Option 1: Remote Model (Easiest)

Pull directly from Ollama registry - no GGUF file needed:

```bash
ollama pull sirrand/htb-pentest
```

### Option 2: USB Drive Deployment

Deploy to a USB drive for portable use on any Windows machine:

```powershell
# Lite mode - pulls model at runtime (~4GB download on first run)
.\deploy\usb-deploy\deploy-to-usb.ps1 -TargetDrive E: -LiteMode

# Remote model - uses published model from Ollama registry
.\deploy\usb-deploy\deploy-to-usb.ps1 -TargetDrive E: -RemoteModel "sirrand/htb-pentest"

# Full mode - includes GGUF file (4GB+ USB space required)
.\deploy\usb-deploy\deploy-to-usb.ps1 -TargetDrive E: -IncludeModel
```

### Option 3: Jetson Orin Nano

Deploy as a dedicated edge AI device with 8GB unified memory.

### Deployment Script Options

| Parameter | Description |
|-----------|-------------|
| `-TargetDrive` | Target drive letter (e.g., "E:") |
| `-LiteMode` | Deploy without GGUF, pulls mistral:7b at runtime |
| `-RemoteModel` | Specify remote model to pull (e.g., "sirrand/htb-pentest") |
| `-IncludeModel` | Copy local GGUF file to USB (4GB+) |
| `-DownloadOllama` | Download fresh Ollama installation |
| `-IncludeTraining` | Include training code |

---

## Directory Structure

```text
Pentesting Agent/
├── README.md                    # This file
├── start-gui.bat                # GUI launcher (Windows)
├── start-agent.bat              # CLI launcher (Windows)
├── deploy/
│   └── usb-deploy/
│       └── deploy-to-usb.ps1    # USB deployment script
│
├── agent/                       # Deployable agent package
│   ├── pentest-agent.py         # CLI interface
│   ├── pentest-gui.py           # GUI interface (CustomTkinter)
│   ├── knowledge_base.py        # RAG system for document retrieval
│   ├── Modelfile                # Full model config (requires GGUF)
│   ├── Modelfile.lite           # Lite model config (pulls mistral:7b)
│   ├── corrections.json         # Self-learning corrections database
│   ├── settings.json            # User settings
│   ├── kali_tools.json          # Kali tool definitions
│   ├── docker/                  # Docker Kali Linux setup
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── shared/              # Host-container shared files
│   └── tools/                   # Portable pentest tools
│
└── htb-model-training/          # Model training scripts and data
    ├── data/                    # Training data (writeups)
    ├── scripts/                 # Utility scripts
    └── train_model.py           # Main training script
```

---

## Knowledge Base (RAG)

Import books, PDFs, and documents to enhance model responses without retraining.

### How It Works

1. Documents are chunked and indexed using TF-IDF
2. When you ask a question, relevant chunks are retrieved
3. Retrieved context is injected into the model prompt
4. Model responds with knowledge from your documents

### Usage

1. Click the **book icon** in the GUI sidebar
2. Click **"Add Document"** and select a PDF or text file
3. Wait for indexing to complete
4. Ask questions - relevant content is automatically retrieved

### Supported Formats

- PDF files (`.pdf`)
- Text files (`.txt`, `.md`, `.rst`)

### Dependencies

```bash
pip install scikit-learn PyPDF2 pdfplumber
```

---

## Self-Learning Feedback System

Correct model mistakes and improve responses over time.

### How It Works

1. **Thumbs Down**: Click 👎 on any assistant response to provide a correction
2. **Correction Dialog**: Select detected issues or write custom corrections
3. **Context Injection**: Relevant corrections are automatically injected into future similar queries
4. **Apply to Model**: Permanently update the Modelfile with learned corrections

### Auto-Detected Issues

The correction dialog automatically detects common problems:

| Issue | Description |
|-------|-------------|
| Wrong Target | Model scanned wrong IP address |
| Localhost Default | Used 127.0.0.1 instead of specified target |
| No Execution | Explained instead of running command |
| Ignored Parameters | Didn't use user-specified options |
| Wrong Tool | Used inappropriate tool for the task |

### Settings

Access in **Settings > Learning**:
- **Auto-inject corrections**: Enable/disable context injection
- **Max corrections**: Number of corrections to inject (1-10)
- **View Corrections**: Manage saved corrections
- **Apply to Model**: Permanently update Modelfile

---

## Model Options

### Remote Model (Recommended)

```bash
ollama pull sirrand/htb-pentest
```

Published to Ollama registry at: https://ollama.com/sirrand/htb-pentest

### Lite Mode

Uses `mistral:7b` as base model (pulled automatically):
- No custom GGUF required
- ~4GB download on first run
- Good for testing and light use

### Full Mode

Uses custom HTB-trained GGUF model:
- Best performance for pentesting tasks
- Requires 4GB+ GGUF file
- Build with: `ollama create htb-pentest -f Modelfile`

### Model Fallback Logic

The launcher automatically selects the best available option:

1. Check `model_config.json` for remote model → pull and use
2. Check for local `.gguf` file → build from `Modelfile`
3. Fall back to lite mode → pull `mistral:7b`, use `Modelfile.lite`

---

## USB Drive Deployment (Windows)

### USB Prerequisites

- Windows 10/11 host machine
- Python 3.8+ installed on host
- USB drive (8GB+ for lite mode, 16GB+ for full mode)

### USB Setup

1. **Run the deployment script**

   ```powershell
   cd deploy\usb-deploy
   .\deploy-to-usb.ps1 -TargetDrive E: -RemoteModel "sirrand/htb-pentest" -DownloadOllama
   ```

2. **Insert USB on target machine and run**

   ```cmd
   E:\start-gui.bat
   ```

   First run will:
   - Install Python dependencies
   - Pull the model (if remote/lite mode)
   - Launch the GUI

### USB Features

- **Portable Execution**: No installation required on host
- **Auto Model Setup**: Pulls model automatically if not present
- **Bundled Tools**: nmap, whois, wget, curl, dig, netcat, tcping
- **Offline Capable**: Works offline after initial model download

---

## Jetson Orin Nano Deployment

### Jetson Prerequisites

- Jetson Orin Nano Developer Kit (8GB)
- JetPack 6.x with CUDA support
- NVMe SSD recommended

### Jetson Setup

1. **Install Ollama**

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull the model**

   ```bash
   ollama pull sirrand/htb-pentest
   ```

3. **Configure Swap (for 7B models)**

   ```bash
   sudo fallocate -l 32G /mnt/nvme/swapfile
   sudo chmod 600 /mnt/nvme/swapfile
   sudo mkswap /mnt/nvme/swapfile
   sudo swapon /mnt/nvme/swapfile
   ```

4. **Install Dependencies**

   ```bash
   pip3 install requests customtkinter scikit-learn PyPDF2 pdfplumber
   ```

5. **Run the Agent**

   ```bash
   chmod +x start-agent.sh start-gui.sh
   ./start-gui.sh
   ```

---

## Docker Kali Linux (Optional)

Extend the agent with a full Kali Linux toolkit (600+ tools).

### Docker Setup

1. **Start the Kali Container**

   ```bash
   cd agent/docker

   # Windows
   start-kali.bat

   # Linux
   ./start-kali.sh
   ```

2. **Run the Agent**

   The agent automatically detects the Docker container and enables extended commands.

### Available Tools (Docker Mode)

| Category | Tools |
|----------|-------|
| Web Testing | gobuster, dirb, ffuf, nikto, whatweb, wfuzz |
| Exploitation | msfconsole, msfvenom, searchsploit |
| Password | john, hashcat, hydra, crackmapexec |
| SMB/Windows | smbclient, enum4linux, rpcclient, smbmap |
| SQL Injection | sqlmap |
| Impacket | impacket-psexec, impacket-secretsdump, etc. |
| Priv Esc | linpeas, linux-exploit-suggester |

---

## Supported Commands

### Basic Commands (Always Available)

| Command | Description |
|---------|-------------|
| `ping` | Network connectivity test |
| `nmap` | Port scanning and service detection |
| `curl` / `wget` | HTTP requests and downloads |
| `dig` / `nslookup` | DNS lookups |
| `whois` | Domain registration info |
| `traceroute` | Network path tracing |
| `netstat` | Network connections |
| `nc` / `ncat` | Netcat for connections |

### Extended Commands (Docker Kali)

When Docker is running, the agent has access to the **full Kali Linux toolkit**.

---

## Security Features

- **Command Whitelisting**: Only approved commands can execute
- **Pattern Blocking**: Dangerous characters blocked
- **Timeout Limits**: Maximum execution time (300s)
- **Docker Isolation**: Extended tools run in isolated container
- **Network Capabilities**: Limited Linux capabilities (NET_RAW, NET_ADMIN)

---

## Model Training

### Training Requirements

- NVIDIA GPU with 24GB+ VRAM (RTX 3090/4090)
- CUDA 11.8+
- Python 3.10+

### Training Pipeline

```bash
cd htb-model-training
pip install -r requirements.txt
python train_model.py
python merge_lora.py
python scripts/convert_to_gguf.py
```

### Publishing to Ollama

```bash
# Tag with your username
ollama cp htb-pentest yourname/htb-pentest

# Push to registry
ollama push yourname/htb-pentest
```

---

## License

For educational purposes only. Use only in authorized testing environments. The creator is not responsible for misuse.
