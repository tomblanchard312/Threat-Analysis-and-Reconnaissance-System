# Portable Docker Infrastructure on USB

This guide explains how to make the HTB Pentest Agent's Docker infrastructure fully self-contained on a USB drive.

---

## Current Setup (Semi-Portable)

**What's on USB:**
- ✅ Docker image tarball (2.1GB)
- ✅ Configuration files (Dockerfile, docker-compose.yml)
- ✅ Shared folder for file exchange

**What's on Host:**
- ❌ Docker daemon/engine (must be installed)
- ❌ Loaded images (stored in Docker's data directory)
- ❌ Container volumes (persistent data)

**Portability Level:** Medium - Requires Docker installed on host, but image can be quickly loaded

---

## Option 1: Reconfigure Docker Data Root ⭐ (Recommended)

**Concept:** Point Docker's data directory to the USB drive, so all images and volumes live on USB.

### Advantages:
- Truly portable - all Docker data on USB
- No additional software needed
- Fast switching between machines
- Easy to backup entire environment

### Disadvantages:
- Requires administrative access to configure Docker
- USB must be fast (USB 3.0+ recommended)
- Still requires Docker installed on host

### Setup:

**Windows:**
```powershell
# Run as Administrator
.\agent\docker\setup-portable-docker.ps1 -UsbDrive L:
```

**Linux:**
```bash
# Run as root
sudo ./agent/docker/setup-portable-docker.sh /media/usb
```

### How It Works:

1. Script modifies `/etc/docker/daemon.json` (Linux) or `%ProgramData%\Docker\config\daemon.json` (Windows)
2. Sets `data-root` to USB drive location
3. Restarts Docker daemon
4. Loads HTB Kali image to USB storage

**After setup, your USB structure:**
```
L:\
├── agent\                      # Application
├── models\                     # AI models
├── docker-data\                # NEW - Docker's storage
│   ├── images\                 # Container images
│   ├── volumes\                # Persistent volumes
│   │   ├── htb-kali-data\      # Pentest data
│   │   └── htb-msf-data\       # Metasploit DB
│   └── overlay2\               # Container layers
└── Ollama\                     # Ollama models
```

### To Restore Default Docker:
```bash
# Delete daemon.json
sudo rm /etc/docker/daemon.json

# Restart Docker
sudo systemctl restart docker
```

---

## Option 2: Use Podman (Daemonless) 🐧

**Concept:** Replace Docker with Podman, which doesn't require a daemon and is more portable.

### Advantages:
- No daemon required
- Rootless containers (more secure)
- Drop-in Docker replacement (same CLI)
- Better for Linux portability

### Disadvantages:
- Different tool (not Docker Desktop)
- Some Docker Compose features may differ
- Windows support is experimental

### Setup:

**Install Podman:**
```bash
# Linux (Debian/Ubuntu)
sudo apt install podman podman-compose

# Arch Linux
sudo pacman -S podman podman-compose
```

**Convert Docker Compose:**
```bash
cd L:/agent/docker
podman-compose up -d
```

**Podman uses local storage by default:**
```bash
# Configure Podman storage on USB
export PODMAN_ROOT=/media/usb/podman
mkdir -p $PODMAN_ROOT
```

---

## Option 3: Docker in a VM 💻

**Concept:** Run a lightweight Linux VM from USB that includes Docker pre-installed.

### Advantages:
- Completely self-contained
- No host modification needed
- Works on any platform with virtualization
- Full control over environment

### Disadvantages:
- Slower performance (VM overhead)
- Larger USB space requirement (10GB+)
- Requires virtualization software on host

### Recommended Setup:

**Use QEMU Portable + Alpine Linux:**

1. **Create Alpine VM with Docker:**
   ```bash
   # Download Alpine Linux
   wget https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/x86_64/alpine-virt-3.18.4-x86_64.iso

   # Create VM disk on USB
   qemu-img create -f qcow2 /media/usb/alpine-docker.qcow2 10G

   # Install Alpine with Docker
   qemu-system-x86_64 -hda /media/usb/alpine-docker.qcow2 -cdrom alpine-virt.iso -m 2048
   ```

2. **Inside Alpine VM:**
   ```bash
   # Install Docker
   apk add docker docker-compose
   rc-update add docker boot
   service docker start

   # Load HTB Kali image
   docker load -i /mnt/usb/agent/docker/htb-pentest-kali.tar
   ```

3. **Run VM from USB:**
   ```bash
   qemu-system-x86_64 \
     -hda /media/usb/alpine-docker.qcow2 \
     -m 2048 \
     -net nic -net user,hostfwd=tcp::2222-:22 \
     -nographic
   ```

---

## Option 4: Singularity/Apptainer 📦

**Concept:** Use Singularity containers (designed for HPC/portability) instead of Docker.

### Advantages:
- Single-file container images (easy to copy)
- No daemon required
- Designed for portability
- Better for restricted environments

### Disadvantages:
- Different tooling from Docker
- Requires conversion from Docker
- Smaller ecosystem

### Setup:

**Convert Docker image to Singularity:**
```bash
# Install Singularity/Apptainer
sudo apt install singularity-container

# Convert Docker image
singularity build htb-kali.sif docker-archive://htb-pentest-kali.tar

# Run container
singularity shell htb-kali.sif
```

---

## Comparison Table

| Solution | Host Install Required | Portability | Speed | Complexity | Storage on USB |
|----------|----------------------|-------------|-------|------------|----------------|
| **Docker Data Root** | Docker Desktop | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ~3GB |
| **Podman** | Podman | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ~3GB |
| **VM (QEMU)** | QEMU/VirtualBox | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ~10GB |
| **Singularity** | Singularity | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~2GB |
| **Current (Hybrid)** | Docker Desktop | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ~2GB |

---

## Recommended Approach

### For Maximum Portability:
**Use Option 1 (Docker Data Root)** with a setup script:

1. **On first use on a new machine:**
   ```bash
   # Run setup script (requires admin/sudo)
   sudo ./agent/docker/setup-portable-docker.sh /media/usb
   ```

2. **This configures Docker to use USB for everything**

3. **When done, restore defaults:**
   ```bash
   # Remove config
   sudo rm /etc/docker/daemon.json
   sudo systemctl restart docker
   ```

### For Linux/Advanced Users:
**Use Option 2 (Podman)** for true daemonless portability

### For Maximum Isolation:
**Use Option 3 (VM)** if you need a completely self-contained environment

---

## Performance Considerations

**USB Drive Speed:**
- Minimum: USB 3.0 (5 Gbps)
- Recommended: USB 3.1/3.2 (10+ Gbps)
- Best: Thunderbolt/USB4 (40 Gbps) or NVMe USB enclosure

**File System:**
- Linux: ext4 or btrfs
- Windows: NTFS (with Docker WSL2)
- Avoid: FAT32/exFAT (compatibility issues)

**Expected Performance:**
- Container start time: 2-5 seconds (vs 1-2 on local SSD)
- Tool execution: ~90% of local SSD speed
- Image pull/load: Limited by USB read speed

---

## Security Considerations

1. **Encrypt USB drive** (especially with sensitive pentest data)
   - Linux: LUKS encryption
   - Windows: BitLocker To Go
   - Cross-platform: VeraCrypt

2. **Sensitive data in volumes:**
   - Metasploit database may contain credentials
   - Scan results may have sensitive findings
   - Consider clearing volumes after each use

3. **API keys in settings:**
   - Store in encrypted section
   - Use environment variables
   - Rotate after USB is lost/stolen

---

## Troubleshooting

### "Permission denied" when accessing USB Docker data
```bash
# Fix ownership
sudo chown -R $(id -u):$(id -g) /media/usb/docker-data
```

### Docker can't find images after switching machines
```bash
# Reload image from tarball
docker load -i /media/usb/agent/docker/htb-pentest-kali.tar
```

### Slow container performance
```bash
# Check USB speed
sudo hdparm -Tt /dev/sdX

# Expected: >100 MB/sec for USB 3.0
```

---

## Summary

**Best option for most users:** Option 1 (Docker Data Root)
- Fast, simple, truly portable
- Requires setup script on each machine
- All data lives on USB

**Alternative:** Keep current hybrid approach if you frequently switch between machines and don't mind loading the image each time.

For the HTB Pentest Agent, **Option 1 is recommended** as it provides the best balance of portability, performance, and simplicity.
