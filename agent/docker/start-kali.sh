#!/bin/bash
# Start the Kali Linux Docker container

echo ""
echo "============================================"
echo "  Starting Kali Linux Container"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker first: sudo systemctl start docker"
    exit 1
fi

# Check if container already exists
if docker ps -a --filter "name=htb-kali" --format "{{.Names}}" | grep -q "htb-kali"; then
    # Container exists, check if running
    if docker ps --filter "name=htb-kali" --format "{{.Names}}" | grep -q "htb-kali"; then
        echo "[OK] Kali container is already running"
    else
        echo "[INFO] Starting existing container..."
        docker start htb-kali
        echo "[OK] Kali container started"
    fi
else
    # Container doesn't exist, create it
    echo "[INFO] Building and starting Kali container..."
    echo "       This may take a while on first run..."
    echo ""
    cd "$SCRIPT_DIR"
    docker compose up -d --build
    if [ $? -eq 0 ]; then
        echo ""
        echo "[OK] Kali container is now running"
    else
        echo ""
        echo "[ERROR] Failed to start container"
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "  Kali Linux Ready!"
echo "============================================"
echo ""
echo "Container: htb-kali"
echo ""
echo "To access shell: docker exec -it htb-kali bash"
echo "To stop:         docker stop htb-kali"
echo ""
