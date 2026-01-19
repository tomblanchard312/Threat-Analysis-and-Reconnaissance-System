# HTB Pentest Agent - USB Deployment

Create a portable USB drive with the full HTB Pentest Agent for use on any Windows machine.

## Features

- **Portable Ollama** - No installation required
- **Full Agent** - CLI and GUI interfaces
- **Kali Docker Support** - Optional 600+ tool toolkit
- **Auto-launch** - USB autorun support (where enabled)
- **Transcripts** - Session history saved to USB

## Quick Deploy

### Windows (PowerShell)

```powershell
# Basic deployment
.\deploy-to-usb.bat E:

# With model file included
.\deploy-to-usb.bat E: -IncludeModel

# Full deployment with training code
.\deploy-to-usb.bat E: -IncludeModel -IncludeTraining
```

### Manual Deployment

If the script doesn't work, manually copy:

```
USB_DRIVE:\
├── Ollama\              # Copy from L:\Ollama
│   ├── ollama.exe
│   ├── app.ico
│   └── lib\
├── agent\               # Copy from L:\agent
│   ├── pentest-agent.py
│   ├── pentest-gui.py
│   ├── Modelfile
│   ├── settings.json
│   ├── kali_tools.json
│   ├── htb-pentest-v3-q4_k_m.gguf  # Model file
│   ├── docker\
│   └── transcripts\
├── start-gui.bat        # Copy from L:\
├── start-agent.bat
├── autorun.inf
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
   - Ollama started
   - Model registered
4. **Start using** the agent

### Requirements on Target Machine

- Windows 10/11
- Python 3.8+ installed and in PATH
- (Optional) Docker Desktop for Kali toolkit

## Deployment Options

### `-IncludeModel`

Copies the 4GB+ GGUF model file to the USB. Required for first use on machines without internet.

**Without model:** First launch will fail if the target machine can't download/create the model.

### `-IncludeTraining`

Includes the training code for fine-tuning models. Only needed if you want to train custom models on the target machine.

### `-DownloadOllama`

Downloads a fresh copy of Ollama instead of copying from source. Useful for creating deployment packages without a local Ollama installation.

## File Structure After Deployment

```
USB_DRIVE:\
├── Ollama\                    # Portable Ollama
│   ├── ollama.exe             # Main executable
│   ├── app.ico                # Icon
│   ├── lib\                   # Runtime libraries
│   └── models\                # Model storage (created on first run)
├── agent\
│   ├── pentest-agent.py       # CLI agent
│   ├── pentest-gui.py         # GUI agent
│   ├── Modelfile              # Model configuration
│   ├── settings.json          # User settings
│   ├── kali_tools.json        # Tool catalog
│   ├── htb-pentest-*.gguf     # Model file (if included)
│   ├── docker\                # Kali Docker setup
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── start-kali.bat
│   ├── tools\                 # Portable tools
│   └── transcripts\           # Session history
├── training\                  # Training code (if included)
├── start-gui.bat              # Launch GUI
├── start-agent.bat            # Launch CLI
├── autorun.inf                # USB autorun config
├── README.md                  # Documentation
└── DEPLOYMENT_INFO.txt        # Deployment timestamp
```

## Updating an Existing USB

To update agent code without redeploying everything:

```powershell
# Update just the agent files
Copy-Item L:\agent\*.py E:\agent\ -Force
Copy-Item L:\agent\Modelfile E:\agent\ -Force
Copy-Item L:\agent\settings.json E:\agent\ -Force
```

To update the model:
```powershell
Copy-Item L:\agent\htb-pentest-*.gguf E:\agent\ -Force
# Then re-register on next use (automatic)
```

## Troubleshooting

### "Python not found"

Install Python 3.8+ from [python.org](https://python.org) and ensure it's added to PATH.

### "Ollama failed to start"

- Check if another Ollama instance is running
- Try stopping it: `taskkill /IM ollama.exe /F`
- Re-run the launcher

### "Model not found"

- Ensure the `.gguf` file is in the `agent\` folder
- Delete `Ollama\models\` folder to force re-registration
- Re-run the launcher

### Slow Performance

- Use a USB 3.0+ drive
- Ensure the USB is plugged into a USB 3.0 port (usually blue)
- Consider an external SSD for best performance

### Kali Docker Not Working

Docker Desktop must be installed on the target machine. The USB only contains configuration files, not the Docker engine.

## Security Notes

- **Transcripts** are saved locally on the USB
- **No data** is sent to external servers
- **Model runs locally** via Ollama
- **Clear transcripts** regularly if using on shared machines

## Creating a Minimal Deployment

For situations with limited space:

```powershell
# Minimal deployment (no model, no training)
.\deploy-to-usb.bat E:

# Then download model on target machine
# (requires internet on first use)
```

The agent will attempt to create/download the model on first run if not present.
