# Portable Docker Daemon - Complete Self-Contained Setup

This guide explains how to run a **completely self-contained** Docker daemon from the USB drive, eliminating the need for Docker Desktop installation on the host machine.

---

## Overview

### What This Enables

**Before (Requires Docker Desktop):**
```
Host Machine:
├── Docker Desktop installed ✓
├── Docker daemon running ✓
└── HTB Kali container ✓

USB Drive:
├── AI model & agent code
└── Kali image tarball (backup)
```

**After (Fully Self-Contained):**
```
Host Machine:
└── No Docker required! ✓

USB Drive:
├── AI model & agent code ✓
├── Docker binaries (portable) ✓
├── Docker daemon (auto-starts) ✓
├── Kali image & data ✓
└── Everything needed! ✓
```

### Benefits

- ✅ **Zero host installation** - No Docker Desktop needed
- ✅ **True portability** - Works on any Linux machine
- ✅ **Auto-start** - GUI starts daemon automatically
- ✅ **Self-contained** - Everything on USB
- ✅ **No root required** - Runs in rootless mode
- ✅ **Isolated** - Doesn't interfere with system Docker

### Limitations

- ⚠️ **Linux only** - Windows requires Docker Desktop
- ⚠️ **Network limitations** - No iptables/bridge networking (uses host network)
- ⚠️ **Some features disabled** - Rootless mode has restrictions
- ⚠️ **Performance** - USB 3.0+ required for acceptable speed

---

## Setup Instructions

### One-Time Setup (5 minutes)

**1. Download and extract Docker binaries:**

```bash
cd /media/usb/agent/docker
./setup-portable-daemon.sh
```

This script will:
- Download Docker static binaries (~60MB)
- Extract to `USB:/docker-runtime/bin/`
- Create necessary directory structure
- Set up helper scripts

**What gets downloaded:**
```
docker-runtime/
├── bin/
│   ├── dockerd          # Docker daemon
│   ├── docker           # Docker client
│   ├── docker-init      # Init process
│   ├── docker-proxy     # Networking
│   └── ...              # Other binaries
├── data/                # Container images & volumes
├── run/                 # Runtime files
├── tmp/                 # Temporary files
├── docker.sock          # Unix socket (created on start)
├── docker.pid           # Process ID file
├── docker.log           # Daemon logs
└── env.sh               # Environment setup script
```

**Size impact on USB:**
```
Docker binaries:    ~60MB
Docker data (initial): ~0MB
HTB Kali image:     ~9GB (when loaded)
Total additional:   ~9GB
```

---

## Usage

### Method 1: GUI Auto-Start (Recommended)

The HTB Pentest Agent GUI automatically detects and starts the portable Docker daemon:

```bash
# Just launch the GUI from USB
cd /media/usb
./start-gui.sh
```

**What happens:**
1. GUI checks if system Docker is running
2. If not, checks for portable Docker on USB
3. Auto-starts portable daemon (if available)
4. Loads HTB Kali image
5. Starts Kali container
6. GUI connects and is ready!

### Method 2: Manual Start

Start the daemon manually before launching GUI:

```bash
# Start portable Docker daemon
cd /media/usb/agent/docker
./portable-dockerd.sh
```

**Output:**
```
================================================
  Portable Docker Daemon
================================================

[1/3] Starting portable Docker daemon...
      Data directory: /media/usb/docker-runtime/data
      Socket: /media/usb/docker-runtime/docker.sock
      Docker daemon ready! (PID: 12345)

[2/3] Checking for HTB Kali image...
      Loading image from tarball...
      Image loaded successfully

[3/3] Starting HTB Kali container...
      Container started successfully

================================================
  Portable Docker Daemon Running!
================================================

Docker socket: /media/usb/docker-runtime/docker.sock
PID: 12345

To use this daemon:
  export DOCKER_HOST=unix:///media/usb/docker-runtime/docker.sock
```

### Method 3: Interactive Shell

Use the portable Docker daemon in your shell:

```bash
# Load portable Docker environment
source /media/usb/docker-runtime/env.sh

# Now use docker normally
docker ps
docker exec -it htb-kali bash
docker logs htb-kali
```

---

## Stopping the Daemon

### Auto-Stop (GUI)

The GUI automatically stops the portable daemon when closed (if it started it).

### Manual Stop

```bash
cd /media/usb/agent/docker
./stop-portable-dockerd.sh
```

This will:
1. Stop all running containers gracefully
2. Shutdown daemon (SIGTERM)
3. Force kill if needed (after 10s timeout)
4. Clean up socket and PID files

---

## Integration with GUI

### How the GUI Uses Portable Docker

The GUI includes `portable_docker.py` module that handles:

**1. Auto-detection:**
```python
# GUI checks on startup
if portable_docker.is_available():
    if not system_docker_running():
        portable_docker.start_daemon()
```

**2. Environment setup:**
```python
# All docker commands use portable socket
env = portable_docker.get_docker_env()
subprocess.run(["docker", "exec", ...], env=env)
```

**3. Status display:**
```
Docker Panel:
● Running (Portable Mode)
  Full Kali toolkit (600+ tools)
  Socket: /media/usb/docker-runtime/docker.sock

[Stop Daemon] [Open Shell]
```

**4. Cleanup on exit:**
```python
def on_closing():
    if portable_docker.was_started_by_us:
        portable_docker.stop_daemon()
    save_session()
    root.destroy()
```

---

## Platform Support

### ✅ Supported Platforms

| Platform | Support | Notes |
|----------|---------|-------|
| **Linux x86_64** | ✅ Full | Primary target |
| **Linux ARM64** | ✅ Full | Jetson Orin Nano, Raspberry Pi 4+ |
| **Linux ARMv7** | ✅ Limited | Raspberry Pi 3, older devices |
| **macOS** | ⚠️ Experimental | May require additional permissions |
| **Windows** | ❌ Not supported | Use Docker Desktop instead |

### Windows Users

Windows doesn't support portable Docker daemon due to:
- Requires Hyper-V or WSL2 backend
- Complex driver requirements
- Docker Desktop integration with Windows

**Recommended approach for Windows:**
1. Use [setup-portable-docker.ps1](setup-portable-docker.md) to configure Docker Desktop to use USB storage
2. OR use the current hybrid approach (image tarball + Docker Desktop)

---

## Performance Optimization

### USB Drive Recommendations

**Minimum (Basic Use):**
- USB 3.0 drive
- Speed: ~100 MB/s read
- Latency: <50ms

**Recommended (Good Experience):**
- USB 3.1/3.2 Gen 2 drive
- Speed: 300-500 MB/s read
- Latency: <20ms

**Best (Near-Native Performance):**
- Thunderbolt/USB4 NVMe enclosure
- Speed: 1000+ MB/s read
- Latency: <10ms

### Performance Comparison

| Operation | Local SSD | USB 3.0 | USB 3.2 | NVMe USB |
|-----------|-----------|---------|---------|----------|
| Container start | 1s | 3-5s | 2-3s | 1-2s |
| Image pull | 30s | 60s | 40s | 35s |
| File I/O | 100% | 70% | 85% | 95% |
| Tool execution | 100% | 90% | 95% | 98% |

---

## Troubleshooting

### Daemon fails to start

**Check binaries:**
```bash
ls -lh /media/usb/docker-runtime/bin/dockerd
# Should be executable: -rwxr-xr-x
```

**Check permissions:**
```bash
# Fix ownership
chown -R $(id -u):$(id -g) /media/usb/docker-runtime

# Fix permissions
chmod +x /media/usb/docker-runtime/bin/*
```

**Check logs:**
```bash
tail -f /media/usb/docker-runtime/docker.log
```

### "Permission denied" errors

Portable Docker runs in rootless mode, which has limitations:

**Can't bind to privileged ports (<1024):**
```bash
# Use port mapping to higher ports
docker run -p 8080:80 ...  # Maps port 80 to 8080
```

**Can't use some kernel features:**
- No iptables rules
- No bridge networking
- No --privileged mode

**Workaround:**
```bash
# Use host network mode (works for most pentest tools)
docker run --network host ...
```

### "Image not found" error

Reload the image:
```bash
cd /media/usb/agent/docker
docker load -i htb-pentest-kali.tar
```

### Container networking issues

Portable Docker uses host networking by default:

```yaml
# docker-compose.yml
services:
  kali:
    network_mode: host  # Required for portable mode
```

This means:
- Container shares host's network stack
- All ports directly accessible
- No port mapping needed
- Perfect for pentesting!

---

## Advanced Usage

### Running Multiple Containers

The portable daemon can run multiple containers:

```bash
# Source environment
source /media/usb/docker-runtime/env.sh

# Run additional containers
docker run -d --name web-server nginx
docker run -it --name ubuntu ubuntu bash

# List all containers
docker ps -a
```

### Persistent Data

Data is stored on USB in volumes:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect htb-kali-data

# Backup volume
docker run --rm \
  -v htb-kali-data:/data \
  -v /media/usb/backups:/backup \
  ubuntu tar czf /backup/kali-data.tar.gz /data
```

### Custom Containers

Build custom images:

```bash
# Source environment
source /media/usb/docker-runtime/env.sh

# Build custom image
cd /media/usb/my-container
docker build -t my-tool .

# Run it
docker run -it my-tool
```

---

## Security Considerations

### Rootless Mode

Portable Docker runs without root privileges, which:
- ✅ Increases security (isolated from system)
- ✅ Doesn't require sudo
- ✅ Can't modify system files
- ⚠️ Has limited capabilities

### Data Protection

**Encrypt the USB drive:**
```bash
# Linux: LUKS encryption
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup open /dev/sdX usbcrypt
mkfs.ext4 /dev/mapper/usbcrypt
```

**Sensitive data locations:**
```
docker-runtime/data/volumes/htb-kali-data/    # Scan results
docker-runtime/data/volumes/htb-msf-data/     # Metasploit DB (may have creds)
agent/transcripts/                            # Chat logs
agent/session.json                            # Session data
```

### Cleanup on Untrusted Machines

After using on an untrusted machine:

```bash
# Stop daemon
./stop-portable-dockerd.sh

# Remove container data (keeps image)
docker system prune -a --volumes

# Or completely reset
rm -rf /media/usb/docker-runtime/data/*
```

---

## Comparison with Other Approaches

| Feature | Portable Daemon | Docker Desktop + USB Storage | Docker Desktop (Standard) |
|---------|----------------|------------------------------|---------------------------|
| **Host install required** | None | Docker Desktop | Docker Desktop |
| **True portability** | ✅ Yes | ⚠️ Partial | ❌ No |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Setup complexity** | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Storage on USB** | ✅ All | ✅ All | ❌ None |
| **Root required** | ❌ No | ⚠️ For install | ⚠️ For install |
| **Windows support** | ❌ No | ✅ Yes | ✅ Yes |
| **Linux support** | ✅ Yes | ✅ Yes | ✅ Yes |

---

## Summary

**Portable Docker Daemon provides:**
- ✅ **Complete independence** from host system
- ✅ **True "plug-and-play"** experience
- ✅ **Maximum portability** across Linux machines
- ✅ **Integrated with GUI** for seamless experience

**Best for:**
- Moving between multiple Linux machines
- Environments where you can't install Docker
- Maximum security (rootless, isolated)
- Learning/education scenarios

**Not recommended for:**
- Windows machines (use Docker Desktop setup)
- Machines with existing Docker installations (may conflict)
- Production deployments (use system Docker)

---

*Last Updated: 2026-01-22*
*Compatible with: HTB Pentest Agent v4, Docker 24.0+*
