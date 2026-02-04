# HTB Pentest Agent - Jetson Orin Nano Deployment

Deploy the HTB Pentest Agent to a Jetson Orin Nano for a dedicated AI-powered penetration testing workstation.

## Features

- **Edge AI** - Fully self-contained on Jetson hardware
- **GPU Acceleration** - CUDA-accelerated inference
- **Full Agent** - CLI and GUI interfaces with all features
- **Multi-Model Support** - HTB-Pentest (primary) + planning models
- **Case Management** - Investigation tracking with entity relationships
- **Knowledge Base (RAG)** - Document import for enhanced responses
- **Self-Learning** - Correction system to improve model behavior
- **Docker/Kali** - Optional 600+ tool toolkit with auto-install
- **Remote Access** - Ollama API exposed for network access

## Hardware Requirements

- **Jetson Orin Nano** (8GB recommended)
- **NVMe SSD** (64GB+ recommended for model + swap)
- **JetPack 6.x** installed
- Network connection for initial setup

## Quick Deploy (From USB/Network)

### Option 1: Deploy from USB

1. Copy the entire `orin-nano-deploy` folder to a USB drive
2. Insert USB into Jetson
3. Run:

   ```bash
   sudo bash /media/usb/orin-nano-deploy/deploy-to-jetson.sh
   ```

### Option 2: Deploy over Network (SSH)

From your local machine:

```bash
# Copy deployment files
scp -r ./orin-nano-deploy user@jetson-ip:/tmp/

# SSH and run
ssh user@jetson-ip
sudo bash /tmp/orin-nano-deploy/deploy-to-jetson.sh
```

### Option 3: Remote Deploy Script

Use the remote deployment helper:

```bash
./remote-deploy.sh user@jetson-ip [--with-model]
```

## Deployment Options

```bash
# Basic deployment
sudo ./deploy-to-jetson.sh

# With Docker/Kali support
sudo ./deploy-to-jetson.sh --with-docker

# With custom swap size (for larger models)
sudo ./deploy-to-jetson.sh --swap-size 48

# Full deployment
sudo ./deploy-to-jetson.sh --with-docker --with-training
```

## Post-Installation

### Start the Agent

```bash
# CLI mode
/opt/htb-pentest/start-agent.sh

# GUI mode (requires display)
/opt/htb-pentest/start-gui.sh
```

### Pull Additional Models

```bash
# Primary model
ollama pull sirrand/htb-pentest

# Planning model (for complex reasoning)
ollama pull glm4:9b
```

### Access Remotely

The Ollama API is exposed on port 11434:

```bash
curl http://jetson-ip:11434/api/tags
```

### Enable Auto-Start

```bash
sudo systemctl enable ollama
sudo systemctl enable htb-pentest-api  # Optional API service
```

## File Locations

| Component | Path |
|-----------|------|
| Agent code | `/opt/htb-pentest/agent/` |
| Tool catalog | `/opt/htb-pentest/agent/kali_tool_catalog.py` |
| Case files | `/opt/htb-pentest/agent/cases/` |
| Knowledge base | `/opt/htb-pentest/agent/knowledge_base/` |
| MCP servers | `/opt/htb-pentest/mcp-servers/` |
| Ollama models | `/opt/htb-pentest/ollama/models/` |
| Transcripts | `/opt/htb-pentest/agent/transcripts/` |
| Ollama service | `/etc/systemd/system/ollama.service` |

## Performance Tuning

### Memory Settings

For 7B models on 8GB Jetson:

```bash
# Ensure swap is enabled
sudo swapon --show

# Set swappiness
echo 60 | sudo tee /proc/sys/vm/swappiness
```

### Power Mode

Set to maximum performance:

```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

### Monitor Resources

```bash
# GPU usage
nvtop

# System resources
htop

# Ollama logs
journalctl -u ollama -f
```

## Troubleshooting

### Model Loading Slow

- Ensure NVMe SSD is installed (not SD card)
- Check swap is enabled: `free -h`
- Increase swap if needed

### Out of Memory

- Use a smaller quantized model (Q4_K_S instead of Q4_K_M)
- Reduce context size in Modelfile: `PARAMETER num_ctx 2048`
- Enable CUDA unified memory: `export CUDA_VISIBLE_DEVICES=0`

### Ollama Won't Start

```bash
# Check status
sudo systemctl status ollama

# View logs
journalctl -u ollama -n 50

# Restart
sudo systemctl restart ollama
```

## Uninstall

```bash
sudo systemctl stop ollama htb-pentest-api
sudo systemctl disable ollama htb-pentest-api
sudo rm -rf /opt/htb-pentest
sudo rm /etc/systemd/system/htb-pentest-api.service
# Optionally remove Ollama
sudo rm /usr/local/bin/ollama
```
