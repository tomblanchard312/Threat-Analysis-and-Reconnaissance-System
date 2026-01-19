# Pentesting Agent

AI-powered penetration testing assistant with tool execution capabilities. Trained on Hack The Box writeups for educational security testing.

## Deployment Options

### Option 1: Portable USB Drive (Windows)

Run the agent from any Windows machine without installation. Perfect for field work and air-gapped environments.

### Option 2: Jetson Orin Nano (Edge AI)

Deploy as a dedicated edge device with 8GB unified memory. Ideal for a persistent pentest workstation or lab environment.

---

## Directory Structure

```text
Pentesting Agent/
├── README.md                    # This file
├── htb-model-training/          # Model training scripts and data
│   ├── data/                    # Training data (writeups)
│   ├── scripts/                 # Utility scripts
│   ├── configs/                 # Training configurations
│   ├── train_model.py           # Main training script
│   ├── merge_lora.py            # LoRA merging script
│   └── requirements.txt         # Python dependencies
│
└── agent/                       # Deployable agent package
    ├── pentest-agent.py         # CLI interface
    ├── pentest-gui.py           # GUI interface (CustomTkinter)
    ├── Modelfile                # Ollama model configuration
    ├── start-agent.bat          # CLI launcher (Windows)
    ├── start-agent.sh           # CLI launcher (Linux/Jetson)
    ├── start-gui.bat            # GUI launcher (Windows)
    ├── start-gui.sh             # GUI launcher (Linux/Jetson)
    ├── tools/                   # Portable pentest tools
    │   ├── download-tools.bat   # Tool downloader (batch)
    │   ├── download-tools.ps1   # Tool downloader (PowerShell)
    │   └── install-npcap.bat    # Npcap installer helper
    ├── docker/                  # Docker Kali Linux setup
    │   ├── Dockerfile           # Kali container definition
    │   ├── docker-compose.yml   # Container orchestration
    │   ├── start-kali.bat       # Start container (Windows)
    │   ├── start-kali.sh        # Start container (Linux)
    │   └── shared/              # Host-container shared files
    └── anythingllm-skills/      # AnythingLLM integration
        └── pentest-tools/
            ├── plugin.json
            └── handler.js
```

---

## USB Drive Deployment (Windows)

### USB Prerequisites

- Windows 10/11 host machine
- Python 3.8+ installed on host
- USB drive (16GB+ recommended)

### USB Setup

1. **Prepare the USB Drive**

   ```text
   USB:\
   ├── Ollama\              # Portable Ollama installation
   │   └── ollama.exe
   ├── Models\              # GGUF model files
   │   └── htb-pentest-v3-q4_k_m.gguf
   └── Pentesting Agent\    # This folder
       └── agent\
   ```

2. **Download Portable Tools**

   ```cmd
   cd agent\tools
   download-tools.bat
   ```

3. **Run the Agent**

   ```cmd
   # CLI interface
   start-agent.bat

   # GUI interface
   start-gui.bat
   ```

### USB Features

- **Portable Execution**: No installation required on host
- **Bundled Tools**: nmap, whois, wget, curl, dig, netcat, tcping
- **WSL Support**: Uses Windows Subsystem for Linux when available
- **Offline Capable**: Works without internet once tools are downloaded

---

## Jetson Orin Nano Deployment

### Jetson Prerequisites

- Jetson Orin Nano Developer Kit (8GB)
- JetPack 6.x with CUDA support
- NVMe SSD recommended (for swap and model storage)

### Jetson Setup

1. **Install Ollama on Jetson**

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Configure Swap (for 7B models)**

   ```bash
   # Create 32GB swap on NVMe
   sudo fallocate -l 32G /mnt/nvme/swapfile
   sudo chmod 600 /mnt/nvme/swapfile
   sudo mkswap /mnt/nvme/swapfile
   sudo swapon /mnt/nvme/swapfile
   ```

3. **Deploy the Model**

   ```bash
   # Copy GGUF file to Jetson
   scp htb-pentest-v3-q4_k_m.gguf jetson@<ip>:~/models/

   # Create model in Ollama
   cd agent
   ollama create htb-pentest -f Modelfile
   ```

4. **Install Python Dependencies**

   ```bash
   pip3 install requests customtkinter
   ```

5. **Make Launchers Executable**

   ```bash
   chmod +x start-agent.sh start-gui.sh
   ```

6. **Run the Agent**

   ```bash
   # CLI interface
   ./start-agent.sh

   # GUI interface (requires display)
   ./start-gui.sh
   ```

### Jetson-Specific Notes

- **Memory**: 8GB unified RAM shared between CPU/GPU
- **Quantization**: Use Q4_K_M or smaller for reliable operation
- **Swap**: Essential for 7B parameter models
- **Performance**: ~2-5 tokens/second depending on context length
- **Cooling**: Active cooling recommended for sustained use

### Jetson Network Configuration

For headless operation, expose Ollama API:

```bash
# Edit Ollama service
sudo systemctl edit ollama

# Add environment variable
[Service]
Environment="OLLAMA_HOST=0.0.0.0"

# Restart
sudo systemctl restart ollama
```

Access from other devices: `http://<jetson-ip>:11434`

---

## Docker Kali Linux (Optional)

Extend the agent with a full Kali Linux toolkit running in Docker. This enables advanced tools like Metasploit, Gobuster, SQLMap, and more.

### Docker Prerequisites

- Docker Desktop (Windows) or Docker Engine (Linux/Jetson)
- 4GB+ RAM available for container
- 10GB+ disk space for Kali image

### Docker Setup

1. **Start the Kali Container**

   ```bash
   cd agent/docker

   # Windows
   start-kali.bat

   # Linux/Jetson
   chmod +x start-kali.sh
   ./start-kali.sh
   ```

   First run will build the image (may take 10-15 minutes).

2. **Verify Container is Running**

   ```bash
   docker ps
   # Should show: htb-kali
   ```

3. **Run the Agent**

   The agent automatically detects the Docker container and enables extended commands.

   ```bash
   ./start-agent.sh
   # or
   start-agent.bat
   ```

### Docker Passthrough Mode

When the Kali container is running, **ANY command** available in Kali Linux can be executed (600+ tools). The agent automatically routes unknown commands to the Docker container.

**Example tools now available:**

| Category       | Example Commands                                       |
| -------------- | ------------------------------------------------------ |
| Web Testing    | `gobuster`, `dirb`, `ffuf`, `nikto`, `whatweb`, `wfuzz`|
| Exploitation   | `msfconsole`, `msfvenom`, `searchsploit`               |
| Password       | `john`, `hashcat`, `hydra`, `crackmapexec`             |
| SMB/Windows    | `smbclient`, `enum4linux`, `rpcclient`, `smbmap`       |
| SQL Injection  | `sqlmap`                                               |
| Impacket       | `impacket-psexec`, `impacket-secretsdump`, etc.        |
| Priv Esc       | `linpeas`, `linux-exploit-suggester`                   |
| Wireless       | `aircrack-ng`, `wifite`, `reaver`                      |
| Forensics      | `volatility`, `binwalk`, `foremost`                    |

**Blocked commands** (for safety): `rm`, `rmdir`, `format`, `dd`, `shutdown`, `passwd`, `chmod`, `iptables`, etc.

### Docker Management

```bash
# Access Kali shell directly
docker exec -it htb-kali bash

# Stop the container
docker stop htb-kali

# View container logs
docker logs htb-kali

# Remove container (keeps data volumes)
docker rm htb-kali

# Full cleanup (removes data)
docker compose -f agent/docker/docker-compose.yml down -v
```

### Shared Files

Place files in `agent/docker/shared/` to access them inside the container at `/shared/`.

---

## Model Training

### Training Requirements

- NVIDIA GPU with 24GB+ VRAM (RTX 3090/4090)
- CUDA 11.8+
- Python 3.10+

### Training Pipeline

```bash
cd htb-model-training

# Install dependencies
pip install -r requirements.txt

# Train with QLoRA
python train_model.py

# Merge LoRA weights
python merge_lora.py

# Convert to GGUF
python scripts/convert_to_gguf.py
```

### Training Data

- Hack The Box machine writeups
- Conceptual security knowledge
- Tool-calling examples for command execution

---

## Supported Commands

### Basic Commands (Always Available)

| Command            | Description                         |
| ------------------ | ----------------------------------- |
| `ping`             | Network connectivity test           |
| `nmap`             | Port scanning and service detection |
| `curl` / `wget`    | HTTP requests and downloads         |
| `dig` / `nslookup` | DNS lookups                         |
| `whois`            | Domain registration info            |
| `traceroute`       | Network path tracing                |
| `netstat`          | Network connections                 |
| `nc` / `ncat`      | Netcat for connections              |
| `tcping`           | TCP port ping                       |

### Extended Commands (Require Docker Kali)

When Docker is running, the agent has access to the **full Kali Linux toolkit** (600+ tools). Any command installed in the container can be executed.

| Category             | Example Commands                                   |
| -------------------- | -------------------------------------------------- |
| Web Testing          | `gobuster`, `nikto`, `sqlmap`, `ffuf`, `wfuzz`     |
| Exploitation         | `msfconsole`, `msfvenom`, `searchsploit`           |
| Password Attacks     | `john`, `hashcat`, `hydra`, `crackmapexec`         |
| SMB/AD Enumeration   | `enum4linux`, `smbclient`, `rpcclient`, `impacket` |
| Privilege Escalation | `linpeas`, `linux-exploit-suggester`               |
| Wireless             | `aircrack-ng`, `wifite`, `reaver`                  |
| Forensics            | `volatility`, `binwalk`, `foremost`, `strings`     |

---

## Security Features

- **Command Whitelisting**: Only approved commands can execute
- **Pattern Blocking**: Dangerous characters (`;`, `&&`, `|`, etc.) are blocked
- **Timeout Limits**: Commands have maximum execution time (300s)
- **No Shell Injection**: Arguments are sanitized before execution
- **Docker Isolation**: Extended tools run in isolated container
- **Network Capabilities**: Container has limited Linux capabilities (NET_RAW, NET_ADMIN)

---

## License

For educational purposes only. Use only in authorized testing environments. The creator is not responsible for misuse.
