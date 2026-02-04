# HTB Pentest Agent - Docker Infrastructure

This directory contains the Docker configuration and portable daemon setup for the HTB Pentest Agent.

## Quick Start

### Option 1: Use System Docker (Standard)

**Requirements:** Docker Desktop (Windows) or Docker Engine (Linux)

```bash
# Start the Kali container
docker compose up -d

# Or use the helper scripts
./start-kali.sh    # Linux/Mac
start-kali.bat     # Windows
```

### Option 2: Portable Docker Daemon (Linux Only - No Installation Required!)

**One-time setup:**
```bash
./setup-portable-daemon.sh
```

**Then just launch the GUI - it auto-starts everything:**
```bash
cd ../..
./start-gui.sh
```

**Or start manually:**
```bash
./portable-dockerd.sh
```

---

## Files

### Core Configuration
- `Dockerfile` - Kali Linux container build instructions
- `docker-compose.yml` - Container orchestration config
- `htb-pentest-kali.tar` - Portable image (2.1GB)

### Portable Daemon (Linux)
- `setup-portable-daemon.sh` - Download Docker binaries (one-time)
- `portable-dockerd.sh` - Start portable daemon
- `stop-portable-dockerd.sh` - Stop portable daemon

### Legacy Portable Storage (Windows/Linux)
- `setup-portable-docker.ps1` - Configure Docker Desktop to use USB storage
- `setup-portable-docker.sh` - Configure Docker Engine to use USB storage

### Utilities
- `start-kali.sh` / `start-kali.bat` - Start container helpers
- `stop-kali.sh` / `stop-kali.bat` - Stop container helpers
- `load-docker-image.sh` - Load image from tarball

### Generated at Runtime
- `shared/` - Shared folder between host and container
- `docker-runtime/` - Portable daemon data (created by setup)

---

## Approach Comparison

### 1. System Docker (Standard)
**Pros:** Fast, full features, well-supported
**Cons:** Requires Docker installation on host
**Best for:** Primary development machine

### 2. Portable Daemon (Linux)
**Pros:** Zero installation, true portability, auto-starts with GUI
**Cons:** Linux only, some features limited (rootless mode)
**Best for:** Moving between Linux machines, Jetson devices

### 3. Portable Storage (Windows/Linux)
**Pros:** Fast, all features, data on USB
**Cons:** Still requires Docker installed, needs admin setup
**Best for:** Keeping work isolated, easy backup

---

## Portable Daemon Details

The portable daemon is a **self-contained Docker installation** that runs entirely from the USB drive.

**What it does:**
- Downloads Docker static binaries (~60MB)
- Runs dockerd without system installation
- Stores all data on USB
- Auto-starts with GUI
- No root/sudo required

**Limitations:**
- **Linux only** (Windows needs Docker Desktop)
- Uses host networking (no bridge mode)
- No iptables rules
- Rootless mode restrictions

**Storage:**
```
USB:/docker-runtime/
├── bin/           # Docker binaries (60MB)
├── data/          # Images, volumes, containers (9GB+)
├── docker.sock    # Unix socket
├── docker.pid     # Process ID
└── docker.log     # Daemon logs
```

---

## Documentation

- [Portable Docker Daemon Guide](../../docs/Portable-Docker-Daemon-Guide.md) - Complete setup and usage
- [Portable Docker Storage Guide](../../docs/Portable-Docker-Guide.md) - Configure Docker Desktop for USB
- [OSINT API Setup Guide](../../docs/OSINT-API-Setup-Guide.md) - Configure API keys

---

## Troubleshooting

### Container won't start
```bash
# Check if Docker is running
docker info

# Or check portable daemon
cat docker-runtime/docker.log
```

### Image not found
```bash
# Load from tarball
docker load -i htb-pentest-kali.tar

# Or rebuild
docker compose build
```

### Permission errors (portable mode)
```bash
# Fix ownership
chown -R $(id -u):$(id -g) docker-runtime/

# Fix permissions
chmod +x docker-runtime/bin/*
```

### Slow performance
```bash
# Check USB speed
sudo hdparm -Tt /dev/sdX

# Expect: >100 MB/s for USB 3.0
```

---

## Container Details

**Base Image:** `kalilinux/kali-rolling:latest`

**Installed Tools (600+):**
- Network: nmap, masscan, netcat, whois, dig, traceroute
- Web: gobuster, nikto, whatweb, wfuzz, ffuf, sqlmap
- Exploitation: metasploit-framework, exploitdb, impacket
- Passwords: john, hashcat, hydra, wordlists
- OSINT: theHarvester, sherlock, holehe, amass, sublist3r
- SMB/Windows: smbclient, enum4linux, crackmapexec

**Volumes:**
- `htb-kali-data` - Persistent data (/pentest)
- `htb-msf-data` - Metasploit database (/root/.msf4)
- `./shared` - File exchange with host

**Networking:**
- Mode: host (direct access to host network)
- Capabilities: NET_ADMIN, NET_RAW, SYS_PTRACE

---

## Support

For issues or questions:
1. Check the logs: `docker logs htb-kali`
2. Check daemon logs: `cat docker-runtime/docker.log`
3. Review documentation in `docs/`
4. Check GitHub issues

---

*Last Updated: 2026-01-22*
*HTB Pentest Agent v4*
