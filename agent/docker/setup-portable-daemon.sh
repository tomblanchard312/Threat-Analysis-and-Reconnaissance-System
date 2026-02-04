#!/bin/bash
# Setup Portable Docker Daemon
# Downloads Docker static binaries and prepares them for portable use

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCKER_ROOT="$USB_ROOT/docker-runtime"
DOCKER_BIN="$DOCKER_ROOT/bin"

# Docker version to download
DOCKER_VERSION="24.0.7"  # Latest stable as of early 2024
ARCH="$(uname -m)"

# Map architecture names
case "$ARCH" in
    x86_64)
        DOCKER_ARCH="x86_64"
        ;;
    aarch64|arm64)
        DOCKER_ARCH="aarch64"
        ;;
    armv7l)
        DOCKER_ARCH="armhf"
        ;;
    *)
        echo "[ERROR] Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

DOCKER_URL="https://download.docker.com/linux/static/stable/$DOCKER_ARCH/docker-$DOCKER_VERSION.tgz"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  Portable Docker Daemon Setup${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""
echo "Architecture: $DOCKER_ARCH"
echo "Docker version: $DOCKER_VERSION"
echo "USB root: $USB_ROOT"
echo ""

# Check if already set up
if [ -f "$DOCKER_BIN/dockerd" ]; then
    echo -e "${YELLOW}Docker binaries already exist at: $DOCKER_BIN${NC}"
    read -p "Reinstall? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled"
        exit 0
    fi
    rm -rf "$DOCKER_BIN"
fi

# Create directories
echo -e "${CYAN}[1/4] Creating directory structure...${NC}"
mkdir -p "$DOCKER_BIN"
mkdir -p "$DOCKER_ROOT/data"
mkdir -p "$DOCKER_ROOT/run"
mkdir -p "$DOCKER_ROOT/tmp"
echo -e "${GREEN}      Created: $DOCKER_ROOT${NC}"

# Download Docker binaries
echo ""
echo -e "${CYAN}[2/4] Downloading Docker binaries...${NC}"
echo "      URL: $DOCKER_URL"

TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

if command -v wget >/dev/null 2>&1; then
    wget -q --show-progress "$DOCKER_URL" -O docker.tgz
elif command -v curl >/dev/null 2>&1; then
    curl -L --progress-bar "$DOCKER_URL" -o docker.tgz
else
    echo -e "${RED}[ERROR] Neither wget nor curl found${NC}"
    echo "Please install wget or curl and try again"
    exit 1
fi

echo -e "${GREEN}      Downloaded successfully${NC}"

# Extract binaries
echo ""
echo -e "${CYAN}[3/4] Extracting binaries...${NC}"
tar xzf docker.tgz
mv docker/* "$DOCKER_BIN/"
chmod +x "$DOCKER_BIN"/*
cd - >/dev/null
rm -rf "$TEMP_DIR"

echo -e "${GREEN}      Extracted to: $DOCKER_BIN${NC}"
echo "      Binaries:"
ls -1 "$DOCKER_BIN" | sed 's/^/        /'

# Create helper scripts
echo ""
echo -e "${CYAN}[4/4] Creating helper scripts...${NC}"

# Create environment setup script
cat > "$DOCKER_ROOT/env.sh" << 'EOF'
#!/bin/bash
# Source this file to use the portable Docker daemon
# Usage: source env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DOCKER_HOST="unix://$SCRIPT_DIR/docker.sock"
export PATH="$SCRIPT_DIR/bin:$PATH"

echo "Portable Docker environment loaded"
echo "Socket: $DOCKER_HOST"
EOF

chmod +x "$DOCKER_ROOT/env.sh"

# Create quick start script
cat > "$DOCKER_ROOT/start.sh" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
./portable-dockerd.sh
EOF
chmod +x "$DOCKER_ROOT/start.sh"

# Create quick stop script
cat > "$DOCKER_ROOT/stop.sh" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
./stop-portable-dockerd.sh
EOF
chmod +x "$DOCKER_ROOT/stop.sh"

echo -e "${GREEN}      Created helper scripts${NC}"

# Summary
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Docker binaries installed to:"
echo "  $DOCKER_BIN"
echo ""
echo "Binaries ($(du -sh "$DOCKER_BIN" | cut -f1)):"
ls -1 "$DOCKER_BIN" | sed 's/^/  - /'
echo ""
echo "To start the portable Docker daemon:"
echo "  cd $SCRIPT_DIR"
echo "  ./portable-dockerd.sh"
echo ""
echo "Or use the quick start:"
echo "  $DOCKER_ROOT/start.sh"
echo ""
echo "To use the daemon in your shell:"
echo "  source $DOCKER_ROOT/env.sh"
echo "  docker ps"
echo ""
echo "Storage location:"
echo "  Data: $DOCKER_ROOT/data"
echo "  Socket: $DOCKER_ROOT/docker.sock"
echo ""
echo -e "${YELLOW}Note: The daemon runs without sudo using rootless mode${NC}"
echo -e "${YELLOW}Some features may be limited (no iptables, no bridge network)${NC}"
echo ""
