# HTB Pentest Agent

AI-powered penetration testing assistant with real-time tool execution, case management, and professional reporting. Built on a custom HTB-trained model with multi-model architecture, running locally via Ollama.

## Quick Start

**Pull the model from Ollama:**
```bash
ollama pull sirrand/htb-pentest
```

**Launch the GUI:**

```cmd
start-gui.bat
```

**Or deploy to USB:**
```powershell
.\deploy\usb-deploy\deploy-to-usb.ps1 -TargetDrive E: -RemoteModel "sirrand/htb-pentest"
```

---

## Features

### Core Capabilities

- **HTB-Trained Model**: Fine-tuned on Hack The Box writeups for realistic pentesting assistance
- **Tool Execution**: Direct command execution via Kali Docker container (600+ tools)
- **Multi-Model Architecture**: Intelligent routing between domain-specific and planning models
- **Pen Test Scoping**: Guided engagement setup with 7 engagement types and 4 intensity levels
- **Case Management**: Full investigation tracking with entities, relationships, and findings
- **Professional Reporting**: Export to HTML, Markdown, or JSON with entity-relationship diagrams
- **Knowledge Base (RAG)**: Import PDFs and documents to enhance model responses
- **Self-Learning**: Feedback system to correct and improve model behavior over time
- **Auto-Install Tools**: Missing Kali Docker tools installed automatically on demand
- **OSINT Intelligence**: Target-type-aware OSINT with username, email, domain, and IP detection
- **Live Terminal**: Real-time streaming output from all tool executions
- **Portable Deployment**: USB drive, Docker, or Jetson Nano deployment options
- **MCP Integration**: Model Context Protocol support for extended capabilities

---

## GUI Interface

The application is a full-featured CustomTkinter desktop application with:

| Component | Description |
|-----------|-------------|
| **Chat Area** | Streaming AI conversation with tool execution results |
| **Task Plan Panel** | Collapsible panel showing planned tasks with individual Run and Run All buttons |
| **Live Terminal** | Real-time streaming output from tool execution |
| **Docker Panel** | Kali container status, shell access, and tool update controls |
| **Sidebar** | Case management, Docker controls, and session tools |
| **Settings Window** | Tabbed configuration for model, API keys, learning, knowledge base, and MCP servers |

---

## Pen Test Scoping

Launch structured penetration tests with the **Pen Test** button. The scoping dialog provides:

### Engagement Types

| Type | Description |
|------|-------------|
| Network Penetration Test | Full network scanning, service enumeration, vulnerability assessment |
| Web Application Test | Web server fingerprinting, directory enumeration, vulnerability scanning |
| Vulnerability Assessment | Non-invasive vulnerability identification and reporting |
| OSINT / Reconnaissance | Passive intelligence gathering (auto-selects Passive intensity) |
| Local Machine Assessment | Automated security audit of the local system |
| Red Team Exercise | Full-scope adversary simulation |
| Wireless Assessment | Wireless network security testing |

### Intensity Levels

| Level | Description |
|-------|-------------|
| Passive | No direct target interaction (OSINT only) |
| Light | Basic scanning with minimal footprint |
| Standard | Comprehensive scanning and enumeration |
| Aggressive | Full scanning with exploit attempts |

### OSINT Target Detection

OSINT scans automatically detect the target type and select appropriate tools:

| Target Type | Tools Used |
|-------------|------------|
| Username | sherlock, holehe (common email domains), h8mail |
| Email | holehe, theHarvester, whois (domain), h8mail |
| Domain | whois, dig, theHarvester, fierce, sublist3r |
| IP Address | reverse DNS, whois, light nmap |
| URL | whatweb + domain-based tools |

---

## Multi-Model Architecture

The agent uses intelligent model routing for optimal performance:

| Model | Role | Strengths |
|-------|------|-----------|
| `htb-pentest` (Mistral 7B) | Primary | Domain knowledge, tool execution, quick responses |
| `glm-4.7-flash` (30B MoE) | Planning | Complex reasoning, 200K context, extended thinking |

- **Auto-Routing**: Queries are automatically routed to the best model based on task type
- **Extended Thinking**: Enable reasoning mode for complex planning tasks
- **Manual Override**: Disable auto-routing for consistent model usage via Settings

---

## Task Planning & Execution

When a pen test or complex task is initiated:

1. **Plan Generation** - AI generates a structured task plan based on engagement scope
2. **Pre-Check** - Missing tools are automatically detected and installed in Kali Docker
3. **Execution** - Tasks can be run individually or all at once with Run All
4. **Live Output** - Real-time streaming output in the Live Terminal panel
5. **Status Tracking** - Progress bar and status text show current action

### Auto-Install Missing Tools

If a requested tool is not present in the Kali Docker container:

1. The system checks if the tool binary exists via `which`
2. Looks up the install method in `TOOL_INSTALL_REGISTRY` (70+ tools mapped)
3. Falls back to LLM-assisted package resolution for unknown tools
4. Installs via apt, pip, or git clone as appropriate
5. Verifies installation and proceeds with the original command

The **Update Kali Tools** button in the Docker panel updates all installed packages with streaming output.

---

## Case Management

Track investigations with structured case files:

### Case Features

- **Create/Open/List** cases from the sidebar
- **Auto-save** findings, entities, and timeline entries
- **Entity tracking**: IPs, domains, services, credentials, vulnerabilities, users
- **Relationship mapping**: Link entities with evidence-backed relationships
- **Timeline**: Chronological log of all actions and findings
- **Tags**: Categorize cases for easy retrieval

### Report Export

Export cases in three formats:

| Format | Description |
|--------|-------------|
| **HTML** | Professional executive-quality report with cover page, Mermaid.js diagrams, severity-rated findings, and remediation recommendations |
| **Markdown** | Structured text report for documentation and wikis |
| **JSON** | Machine-readable structured data for integration |

### Entity Relationship Graph

Interactive visualization of discovered entities and their relationships using force-directed layout with node selection and highlighting.

---

## Docker Kali Linux

Extend the agent with a full Kali Linux toolkit (600+ tools).

### Docker Setup

Docker is automatically started and configured by `start-gui.bat`. Manual setup:

```bash
cd agent/docker
docker-compose up -d --build
```

The agent automatically detects the Docker container and enables extended commands.

### Available Tools (Docker Mode)

| Category | Tools |
|----------|-------|
| Network Scanning | nmap, masscan, arp-scan, netdiscover, hping3 |
| Web Testing | gobuster, dirb, ffuf, nikto, whatweb, wfuzz, wpscan, feroxbuster |
| Exploitation | msfconsole, msfvenom, searchsploit |
| Password Attacks | john, hashcat, hydra, medusa, crackmapexec |
| SMB/Windows | smbclient, enum4linux, smbmap, rpcclient, evil-winrm, responder |
| Active Directory | bloodhound, certipy, impacket-scripts |
| DNS | dig, dnsrecon, dnsenum, fierce |
| OSINT | theHarvester, amass, sublist3r, sherlock, holehe, h8mail, recon-ng |
| SQL Injection | sqlmap, commix |
| Web App Testing | wapiti, xsser, wafw00f |
| Network Tools | netcat, socat, tcpdump |
| Forensics | binwalk, foremost, steghide, exiftool, volatility3 |

### Docker Panel

The sidebar Docker panel provides:

- Container status indicator (Running/Stopped)
- **Open Kali Shell** - Interactive terminal session
- **Update Kali Tools** - Stream apt upgrade and pip updates in live terminal
- **Download Tools** - Install additional tool packages

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

---

## Self-Learning Feedback System

Correct model mistakes and improve responses over time.

### How It Works

1. **Thumbs Down**: Click the thumbs down icon on any assistant response to provide a correction
2. **Correction Dialog**: Select detected issues or write custom corrections
3. **Context Injection**: Relevant corrections are automatically injected into future similar queries
4. **Apply to Model**: Permanently update the Modelfile with learned corrections

### Auto-Detected Issues

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

## MCP Server Integration

Model Context Protocol servers extend the agent's capabilities:

| Server | Description |
|--------|-------------|
| **Pentest MCP** | nmap, gobuster, nikto, john, hashcat via MCP |
| **Ollama Claude** | Self-hosted AI assistant for code generation and security analysis |
| **Shell Server** | Secure shell command execution |
| **Filesystem** | Secure file read/write operations |
| **Web Fetch** | Retrieve and analyze web content |
| **Memory** | Knowledge graph-based persistent memory |

MCP servers are configured in `settings.json` and can be enabled/disabled individually in Settings.

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

1. Check `model_config.json` for remote model -> pull and use
2. Check for local `.gguf` file -> build from `Modelfile`
3. Fall back to lite mode -> pull `mistral:7b`, use `Modelfile.lite`

---

## Directory Structure

```text
Pentesting Agent/
├── README.md                    # This file
├── start-gui.bat                # GUI launcher (Windows)
├── start-agent.bat              # CLI launcher (Windows)
├── deploy/
│   ├── usb-deploy/
│   │   └── deploy-to-usb.ps1   # USB deployment script
│   └── orin-nano-deploy/
│       └── deploy-to-jetson.sh  # Jetson deployment script
│
├── agent/                       # Deployable agent package
│   ├── pentest-gui.py           # GUI interface (CustomTkinter)
│   ├── pentest-agent.py         # CLI interface
│   ├── kali_tool_catalog.py     # 600+ tool definitions and install registry
│   ├── knowledge_base.py        # RAG system for document retrieval
│   ├── portable_docker.py       # Portable Docker daemon management
│   ├── Modelfile                # Full model config (requires GGUF)
│   ├── Modelfile.lite           # Lite model config (pulls mistral:7b)
│   ├── corrections.json         # Self-learning corrections database
│   ├── settings.json            # User settings and API keys
│   ├── cases/                   # Case files (JSON)
│   ├── knowledge_base/          # RAG index and document chunks
│   ├── docker/                  # Docker Kali Linux setup
│   │   ├── Dockerfile           # Kali container with 600+ tools
│   │   ├── docker-compose.yml   # Container orchestration
│   │   └── shared/              # Host-container shared files
│   └── tools/                   # Portable pentest tools
│
├── mcp-servers/                 # MCP server implementations
│   └── ollama-claude/           # Local AI MCP server
│
└── htb-model-training/          # Model training pipeline
    ├── data/                    # Training data sources
    │   ├── training/            # Processed JSONL datasets
    │   ├── hacktricks/          # HackTricks content
    │   ├── gtfobins/            # GTFOBins data
    │   ├── lolbas/              # LOLBAS payloads
    │   ├── kali_tools/          # Kali tool documentation
    │   ├── osint/               # OSINT methodology
    │   ├── owasp/               # OWASP testing guide
    │   └── payloads/            # Security payloads
    ├── scripts/                 # Data scrapers and processors
    ├── configs/                 # Training configuration
    ├── train_model.py           # LoRA fine-tuning script
    └── merge_lora.py            # LoRA adapter merger
```

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
   - Start portable Ollama with GPU acceleration
   - Pull the model (if remote/lite mode)
   - Start Docker Desktop and Kali container (if available)
   - Launch the GUI

### USB Features

- **Portable Execution**: No installation required on host
- **Auto Model Setup**: Pulls model automatically if not present
- **Bundled Tools**: nmap, whois, wget, curl, dig, netcat, tcping
- **GPU Acceleration**: CUDA auto-detection for fast inference
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

## Local Machine Assessment

Run an automated security assessment of the current machine:

1. Click **Pen Test** and select **Local Machine Assessment**
2. The assessment checks:
   - Network configuration and open ports
   - Installed software inventory
   - Startup programs and scheduled tasks
   - Credential storage (browsers, managers)
   - Windows Defender and firewall status
   - User accounts and privileges
   - Missing security updates
3. Results are analyzed by the AI and summarized with recommendations

---

## Security Features

- **Command Whitelisting**: Only approved commands can execute
- **Pattern Blocking**: Dangerous characters and destructive commands blocked
- **Timeout Limits**: Per-tool timeouts (nmap: 15min, hashcat: 30min, default: 5min)
- **Docker Isolation**: Extended tools run in isolated container
- **Network Capabilities**: Limited Linux capabilities (NET_RAW, NET_ADMIN)
- **Non-Destructive Mode**: Rules of engagement enforce read-only operations
- **API Key Security**: Keys loaded from environment variables, stored outside git

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

When Docker is running, the agent has access to the **full Kali Linux toolkit** with 600+ tools across all security testing categories.

---

## Model Training

### Training Requirements

- NVIDIA GPU with 24GB+ VRAM (RTX 3090/4090)
- CUDA 11.8+
- Python 3.10+

### Training Data Sources

| Source | Description |
|--------|-------------|
| HTB Writeups | Hack The Box machine walkthroughs |
| HackTricks | Security methodology and techniques |
| GTFOBins | Unix privilege escalation binaries |
| LOLBAS | Living Off The Land Binaries (Windows) |
| Kali Tools | Tool documentation and usage |
| OWASP | Web application security testing guide |
| OSINT | Open source intelligence methodology |
| Payloads | Security payload collections |

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

## Dependencies

```bash
pip install requests customtkinter Pillow scikit-learn PyPDF2 pdfplumber
```

Optional for full functionality:

- Docker Desktop (for Kali Linux container)
- Node.js (for MCP servers)
- Ollama (model runtime)

---

## License

For educational purposes only. Use only in authorized testing environments. The creator is not responsible for misuse.
