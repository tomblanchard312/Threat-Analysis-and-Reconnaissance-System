#!/bin/bash

echo ""
echo "============================================================"
echo "  HTB Pentest Agent Launcher"
echo "============================================================"
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found"
    echo "Install with: sudo apt install python3 python3-pip"
    exit 1
fi

# Check if requests is installed
if ! python3 -c "import requests" &> /dev/null; then
    echo "[INFO] Installing required package: requests"
    pip3 install requests
fi

# Start Ollama if not running
echo "[1/2] Checking Ollama..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "     Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 3
else
    echo "     Ollama is running"
fi

# Check if model is registered
echo "[2/2] Checking model registration..."
if ! ollama list 2>/dev/null | grep -q "htb-pentest"; then
    echo "     Registering htb-pentest model..."
    cd "$SCRIPT_DIR"
    ollama create htb-pentest -f Modelfile
else
    echo "     Model htb-pentest is registered"
fi

echo ""
echo "============================================================"
echo "  Starting Pentest Agent..."
echo "============================================================"
echo ""

# Run the agent
cd "$SCRIPT_DIR"
python3 pentest-agent.py
