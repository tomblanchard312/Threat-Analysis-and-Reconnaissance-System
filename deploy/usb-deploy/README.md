# HTB Pentest Agent - USB Deployment

Create a portable USB drive with the full HTB Pentest Agent for use on any Windows machine.

## Features

- **Portable Ollama** - No installation required
- **Full Agent** - CLI and GUI interfaces with CustomTkinter
- **Multi-Model Architecture** - HTB-Pentest (primary) + GLM-4.7-Flash (planning)
- **Kali Docker Support** - Optional 600+ tool toolkit with auto-install
- **Case Management** - Track investigations with entity relationships and export reports
- **Knowledge Base (RAG)** - Import PDFs and documents to enhance responses
- **Self-Learning** - Correction system to improve model behavior
- **MCP Servers** - Model Context Protocol for extended capabilities
- **Auto-launch** - USB autorun support (where enabled)
- **Transcripts** - Session history saved to USB

## Quick Deploy

### Windows (PowerShell)

```powershell
# Basic deployment (pulls model from registry on first run)
.\deploy-to-usb.bat E:

# With model file included (offline capable)
.\deploy-to-usb.bat E: -ModelPath "C:\models\htb-pentest.gguf"

# Full deployment with Node.js for MCP servers
.\deploy-to-usb.bat E: -DownloadOllama -DownloadNodeJS

# Clean redeploy
.\deploy-to-usb.bat E: -CleanDeploy
```

### Manual Deployment

If the script doesn't work, manually copy:

```
USB_DRIVE:\
├── Ollama\              # Copy from local Ollama installation
│   ├── ollama.exe
│   └── lib\
├── agent\               # Copy from agent\
│   ├── pentest-gui.py
│   ├── pentest-agent.py
│   ├── kali_tool_catalog.py
│   ├── knowledge_base.py
│   ├── portable_docker.py
│   ├── Modelfile
│   ├── Modelfile.lite
│   ├── settings.json
│   ├── corrections.json
│   ├── cases\
│   ├── knowledge_base\
│   ├── docker\
│   └── tools\
├── mcp-servers\         # Copy from mcp-servers\
├── start-gui.bat        # Copy from root
├── start-agent.bat
└── README.md
```

## USB Drive Requirements

| Use Case | Minimum Size | Recommended |
|----------|--------------|-------------|
| Agent only (no model) | 500 MB | 1 GB |
| With model | 8 GB | 16 GB |
| With model + training | 16 GB | 32 GB |
| Full (with Docker image) | 32 GB | 64 GB |

**Recommended:** USB 3.0+ drive for better performance

## First-Time Use

1. **Insert USB** into target Windows machine
2. **Run** `start-gui.bat` (or `start-agent.bat` for CLI)
3. **Wait** for first-time setup:
   - Python dependencies installed
   - Ollama started with GPU acceleration
   - Model pulled from registry (if not bundled)
   - Docker started (if available)
4. **Start using** the agent

### Requirements on Target Machine

- Windows 10/11
- Python 3.8+ installed and in PATH
- (Optional) Docker Desktop for Kali toolkit
- (Optional) Node.js for MCP servers (or bundle with -DownloadNodeJS)

## Deployment Options

### `-ModelPath [path]`

Copies a specific GGUF model file to the USB for offline use.

### `-DownloadOllama`

Downloads a fresh copy of Ollama instead of copying from local installation.

### `-DownloadNodeJS`

Downloads portable Node.js (~30MB) for MCP server support without requiring Node.js on the target machine.

### `-SkipModel`

Skip model deployment (use if model already on USB or will be pulled at runtime).

### `-CleanDeploy`

Remove existing files before deploying. Useful for clean updates.

## File Structure After Deployment

```
USB_DRIVE:\
├── Ollama\                    # Portable Ollama
│   ├── ollama.exe             # Main executable
│   ├── lib\                   # Runtime libraries
│   └── models\                # Model storage (created on first run)
├── agent\
│   ├── pentest-gui.py         # GUI agent (CustomTkinter)
│   ├── pentest-agent.py       # CLI agent
│   ├── kali_tool_catalog.py   # 600+ tool definitions and auto-install registry
│   ├── knowledge_base.py      # RAG system for document retrieval
│   ├── portable_docker.py     # Portable Docker daemon management
│   ├── Modelfile              # Model configuration
│   ├── Modelfile.lite         # Lite mode configuration
│   ├── settings.json          # User settings and API keys
│   ├── corrections.json       # Self-learning corrections database
│   ├── cases\                 # Case files (investigation tracking)
│   ├── knowledge_base\        # RAG index and document chunks
│   ├── docker\                # Kali Docker setup
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── shared\
│   └── tools\                 # Portable pentest tools
├── mcp-servers\               # MCP server implementations
│   └── ollama-claude\         # Local AI MCP server
├── models\                    # GGUF model file (if included)
├── nodejs\                    # Portable Node.js (if included)
├── start-gui.bat              # Launch GUI
├── start-agent.bat            # Launch CLI
├── setup-models.bat           # Pull additional models (run once)
├── README.md                  # Documentation
└── DEPLOYMENT_INFO.txt        # Deployment details
```

## Updating an Existing USB

To update agent code without redeploying everything:

```powershell
# Update agent files
Copy-Item agent\pentest-gui.py E:\agent\ -Force
Copy-Item agent\kali_tool_catalog.py E:\agent\ -Force
Copy-Item agent\knowledge_base.py E:\agent\ -Force
Copy-Item start-gui.bat E:\ -Force
```

## Troubleshooting

### "Python not found"

Install Python 3.8+ from [python.org](https://python.org) and ensure it's added to PATH.

### "Ollama failed to start"

- Check if another Ollama instance is running
- Try stopping it: `taskkill /IM ollama.exe /F`
- Re-run the launcher

### "Model not found"

- The launcher auto-pulls `sirrand/htb-pentest` from Ollama registry
- For offline use, deploy with `-ModelPath` to include the GGUF file
- Run `setup-models.bat` to pull additional models (GLM-4.7-Flash, etc.)

### Slow Performance

- Use a USB 3.0+ drive
- Ensure the USB is plugged into a USB 3.0 port (usually blue)
- Consider an external SSD for best performance

### Kali Docker Not Working

Docker Desktop must be installed on the target machine. The USB only contains Docker configuration files, not the Docker engine itself.

## Security Notes

- **Transcripts** are saved locally on the USB
- **No data** is sent to external servers (all models run locally via Ollama)
- **API keys** in settings.json - review before sharing the USB
- **Case files** may contain sensitive findings - handle accordingly
- **Clear transcripts** regularly if using on shared machines
