#!/bin/bash
# Stop Portable Docker Daemon

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCKER_ROOT="$USB_ROOT/docker-runtime"
DOCKER_BIN="$DOCKER_ROOT/bin"
DOCKER_SOCK="$DOCKER_ROOT/docker.sock"
DOCKER_PID="$DOCKER_ROOT/docker.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Stopping portable Docker daemon..."

# Check if daemon is running
if [ ! -f "$DOCKER_PID" ]; then
    echo -e "${YELLOW}No PID file found - daemon may not be running${NC}"
    exit 0
fi

PID=$(cat "$DOCKER_PID")

# Check if process exists
if ! kill -0 "$PID" 2>/dev/null; then
    echo -e "${YELLOW}Process $PID not running - cleaning up${NC}"
    rm "$DOCKER_PID"
    exit 0
fi

# Stop all containers first
if [ -S "$DOCKER_SOCK" ]; then
    echo "Stopping containers..."
    DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" stop $(DOCKER_HOST="unix://$DOCKER_SOCK" "$DOCKER_BIN/docker" ps -q) 2>/dev/null || true
fi

# Stop daemon gracefully
echo "Stopping daemon (PID: $PID)..."
kill -TERM "$PID"

# Wait for graceful shutdown
TIMEOUT=10
ELAPSED=0
while kill -0 "$PID" 2>/dev/null && [ $ELAPSED -lt $TIMEOUT ]; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

# Force kill if still running
if kill -0 "$PID" 2>/dev/null; then
    echo -e "${YELLOW}Daemon didn't stop gracefully, force killing...${NC}"
    kill -KILL "$PID" 2>/dev/null || true
fi

# Clean up
rm -f "$DOCKER_PID"
rm -f "$DOCKER_SOCK"

echo -e "${GREEN}Portable Docker daemon stopped${NC}"
