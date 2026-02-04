#!/bin/bash
# Portable Docker Daemon Launcher
# Runs a self-contained Docker daemon from USB without requiring system installation

set -e

# Get script directory (USB mount point)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Portable Docker paths on USB
DOCKER_ROOT="$USB_ROOT/docker-runtime"
DOCKER_BIN="$DOCKER_ROOT/bin"
DOCKER_DATA="$DOCKER_ROOT/data"
DOCKER_SOCK="$DOCKER_ROOT/docker.sock"
DOCKER_PID="$DOCKER_ROOT/docker.pid"
DOCKER_LOG="$DOCKER_ROOT/docker.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  Portable Docker Daemon${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Check if dockerd binary exists
if [ ! -f "$DOCKER_BIN/dockerd" ]; then
    echo -e "${RED}[ERROR] Docker binaries not found at: $DOCKER_BIN${NC}"
    echo -e "${YELLOW}Run setup-portable-daemon.sh first to download Docker binaries${NC}"
    exit 1
fi

# Check if already running
if [ -f "$DOCKER_PID" ]; then
    PID=$(cat "$DOCKER_PID")
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${GREEN}Docker daemon already running (PID: $PID)${NC}"
        echo "Socket: $DOCKER_SOCK"
        exit 0
    else
        echo -e "${YELLOW}Stale PID file found, removing...${NC}"
        rm "$DOCKER_PID"
    fi
fi

# Create necessary directories
mkdir -p "$DOCKER_DATA"
mkdir -p "$DOCKER_ROOT/run"
mkdir -p "$DOCKER_ROOT/tmp"

echo -e "${CYAN}[1/3] Starting portable Docker daemon...${NC}"
echo "      Data directory: $DOCKER_DATA"
echo "      Socket: $DOCKER_SOCK"

# Start dockerd in background
"$DOCKER_BIN/dockerd" \
    --data-root="$DOCKER_DATA" \
    --host="unix://$DOCKER_SOCK" \
    --pidfile="$DOCKER_PID" \
    --exec-root="$DOCKER_ROOT/run" \
    --storage-driver=overlay2 \
    --userland-proxy=false \
    --iptables=false \
    --ip-forward=false \
    --log-level=error \
    > "$DOCKER_LOG" 2>&1 &

DAEMON_PID=$!
echo "$DAEMON_PID" > "$DOCKER_PID"

echo -e "${YELLOW}      Waiting for daemon to start...${NC}"

# Wait for daemon to be ready (check socket)
TIMEOUT=30
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if [ -S "$DOCKER_SOCK" ]; then
        # Socket exists, test connection
        if DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" info >/dev/null 2>&1; then
            echo -e "${GREEN}      Docker daemon ready! (PID: $DAEMON_PID)${NC}"
            break
        fi
    fi

    # Check if process died
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        echo -e "${RED}      Docker daemon failed to start${NC}"
        echo -e "${YELLOW}      Check log: $DOCKER_LOG${NC}"
        cat "$DOCKER_LOG"
        rm "$DOCKER_PID"
        exit 1
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}      Timeout waiting for Docker daemon${NC}"
    kill "$DAEMON_PID" 2>/dev/null || true
    rm "$DOCKER_PID"
    exit 1
fi

# Check if HTB Kali image is loaded
echo ""
echo -e "${CYAN}[2/3] Checking for HTB Kali image...${NC}"
IMAGE_TAR="$SCRIPT_DIR/htb-pentest-kali.tar"

if DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" images | grep -q "htb-pentest-kali"; then
    echo -e "${GREEN}      Image already loaded${NC}"
else
    if [ -f "$IMAGE_TAR" ]; then
        echo -e "${YELLOW}      Loading image from tarball (this may take a minute)...${NC}"
        DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" load -i "$IMAGE_TAR"
        echo -e "${GREEN}      Image loaded successfully${NC}"
    else
        echo -e "${YELLOW}      [WARNING] Image tarball not found: $IMAGE_TAR${NC}"
        echo -e "${YELLOW}      You'll need to build or pull the image manually${NC}"
    fi
fi

# Start Kali container
echo ""
echo -e "${CYAN}[3/3] Starting HTB Kali container...${NC}"

cd "$SCRIPT_DIR"
DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" compose up -d 2>/dev/null || \
    DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker-compose" up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}      Container started successfully${NC}"
else
    echo -e "${YELLOW}      Could not start with compose, trying direct run...${NC}"
    DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" run -d \
        --name htb-kali \
        --network host \
        --cap-add NET_ADMIN \
        --cap-add NET_RAW \
        -v htb-kali-data:/pentest \
        -v htb-msf-data:/root/.msf4 \
        htb-pentest-kali:latest \
        tail -f /dev/null
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Portable Docker Daemon Running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Docker socket: $DOCKER_SOCK"
echo "PID: $DAEMON_PID"
echo "Log: $DOCKER_LOG"
echo ""
echo "To use this daemon:"
echo "  export DOCKER_HOST=unix://$DOCKER_SOCK"
echo ""
echo "To stop:"
echo "  $SCRIPT_DIR/stop-portable-dockerd.sh"
echo ""
