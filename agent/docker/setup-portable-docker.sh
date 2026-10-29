#!/bin/bash
# Setup Portable Docker on USB Drive
# This configures Docker to use the USB drive for storage

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get USB mount point (first argument or auto-detect)
if [ -n "$1" ]; then
    USB_MOUNT="$1"
else
    # Try to auto-detect USB mount
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    USB_MOUNT="$(dirname "$(dirname "$SCRIPT_DIR")")"
fi

echo "================================================"
echo "  Portable Docker Setup for USB Drive"
echo "================================================"
echo ""
echo "USB Mount: $USB_MOUNT"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker not installed${NC}"
    echo -e "${YELLOW}Please install Docker first:${NC}"
    echo -e "${CYAN}https://docs.docker.com/engine/install/${NC}"
    exit 1
fi

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] This script must be run as root or with sudo${NC}"
    echo -e "${YELLOW}Usage: sudo $0 [usb_mount_point]${NC}"
    exit 1
fi

DOCKER_DATA_PATH="$USB_MOUNT/docker-data"
DOCKER_DAEMON_CONFIG="/etc/docker/daemon.json"

# Create Docker data directory on USB
echo -e "${CYAN}[1/4] Creating Docker data directory on USB...${NC}"
mkdir -p "$DOCKER_DATA_PATH/volumes"
mkdir -p "$DOCKER_DATA_PATH/overlay2"
echo -e "${GREEN}      Created: $DOCKER_DATA_PATH${NC}"

# Backup existing daemon.json if it exists
echo ""
echo -e "${CYAN}[2/4] Configuring Docker daemon...${NC}"
if [ -f "$DOCKER_DAEMON_CONFIG" ]; then
    BACKUP="$DOCKER_DAEMON_CONFIG.backup-$(date +%Y%m%d-%H%M%S)"
    cp "$DOCKER_DAEMON_CONFIG" "$BACKUP"
    echo -e "${YELLOW}      Backed up existing config to: $BACKUP${NC}"
fi

# Create new daemon.json with USB data root
cat > "$DOCKER_DAEMON_CONFIG" << EOF
{
  "data-root": "$DOCKER_DATA_PATH",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo -e "${GREEN}      Updated Docker daemon config${NC}"

# Restart Docker daemon
echo ""
echo -e "${CYAN}[3/4] Restarting Docker daemon...${NC}"
echo -e "${YELLOW}      This may take 1-2 minutes...${NC}"

systemctl restart docker

# Wait for Docker to be ready
echo "      Waiting for Docker to start..."
TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker info &> /dev/null; then
        echo -e "${GREEN}      Docker is ready!${NC}"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${YELLOW}      [WARNING] Docker restart timed out${NC}"
    echo -e "${YELLOW}      Please restart Docker manually: sudo systemctl restart docker${NC}"
fi

# Load HTB Kali image
echo ""
echo -e "${CYAN}[4/4] Loading HTB Kali image to USB storage...${NC}"
IMAGE_TAR="$USB_MOUNT/agent/docker/htb-pentest-kali.tar"

if [ -f "$IMAGE_TAR" ]; then
    docker load -i "$IMAGE_TAR"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}      Image loaded successfully!${NC}"
    else
        echo -e "${RED}      [ERROR] Failed to load image${NC}"
    fi
else
    echo -e "${YELLOW}      [WARNING] Image tarball not found: $IMAGE_TAR${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "================================================"
echo ""
echo -e "${CYAN}Docker is now configured to use USB storage:${NC}"
echo "  Data Root: $DOCKER_DATA_PATH"
echo ""
echo "Next steps:"
echo "  1. cd $USB_MOUNT/agent/docker"
echo "  2. docker compose up -d"
echo ""
echo "To restore default Docker settings:"
echo "  - Remove: $DOCKER_DAEMON_CONFIG"
echo "  - Run: sudo systemctl restart docker"
echo ""
