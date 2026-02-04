#!/bin/bash
# HTB Pentest Agent - Jetson Orin Nano Deployment Script
#
# Prerequisites:
# - Jetson Orin Nano with JetPack 6.x installed
# - Internet connection for downloading packages
# - At least 32GB storage (NVMe recommended)
#
# Usage:
#   chmod +x deploy-to-jetson.sh
#   ./deploy-to-jetson.sh [OPTIONS]
#
# Options:
#   --with-docker    : Install Docker and Kali container
#   --with-training  : Include training code
#   --swap-size GB   : Create swap file (default: 32GB for 7B models)

set -e

# Configuration
INSTALL_DIR="/opt/htb-pentest"
OLLAMA_HOME="$INSTALL_DIR/ollama"
MODEL_NAME="htb-pentest"
SWAP_SIZE=32  # GB

# Parse arguments
WITH_DOCKER=false
WITH_TRAINING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-docker)
            WITH_DOCKER=true
            shift
            ;;
        --with-training)
            WITH_TRAINING=true
            shift
            ;;
        --swap-size)
            SWAP_SIZE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "============================================"
echo "  HTB Pentest Agent - Jetson Deployment"
echo "============================================"
echo ""
echo "Install directory: $INSTALL_DIR"
echo "With Docker: $WITH_DOCKER"
echo "Swap size: ${SWAP_SIZE}GB"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Please run as root (sudo ./deploy-to-jetson.sh)"
    exit 1
fi

# Check Jetson model
if [ -f /etc/nv_tegra_release ]; then
    echo "[INFO] Detected Jetson device"
    cat /etc/nv_tegra_release
else
    echo "[WARN] This doesn't appear to be a Jetson device"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[1/7] Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    jq \
    htop \
    nvtop

echo ""
echo "[2/7] Creating swap file for large model support..."
if [ ! -f /swapfile ]; then
    fallocate -l ${SWAP_SIZE}G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "  Swap file created: ${SWAP_SIZE}GB"
else
    echo "  Swap file already exists"
fi

echo ""
echo "[3/7] Installing Ollama for ARM64..."
curl -fsSL https://ollama.com/install.sh | sh

# Configure Ollama environment
mkdir -p "$OLLAMA_HOME"
cat > /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=$OLLAMA_HOME/models"
EOF

systemctl daemon-reload
systemctl enable ollama
systemctl start ollama

echo "  Waiting for Ollama to start..."
sleep 5

echo ""
echo "[4/7] Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/agent"
mkdir -p "$INSTALL_DIR/agent/docker"
mkdir -p "$INSTALL_DIR/agent/tools"
mkdir -p "$INSTALL_DIR/agent/transcripts"
mkdir -p "$INSTALL_DIR/agent/knowledge_base"
mkdir -p "$INSTALL_DIR/agent/cases"
mkdir -p "$INSTALL_DIR/mcp-servers"

echo ""
echo "[5/7] Copying agent files..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if we're running from the deploy folder or need to find files
if [ -f "$SCRIPT_DIR/../agent/pentest-agent.py" ]; then
    SOURCE_DIR="$SCRIPT_DIR/.."
elif [ -f "$SCRIPT_DIR/../../agent/pentest-agent.py" ]; then
    SOURCE_DIR="$SCRIPT_DIR/../.."
else
    echo "[ERROR] Cannot find agent files. Run from deployment package."
    exit 1
fi

# Copy agent files
cp "$SOURCE_DIR/agent/pentest-agent.py" "$INSTALL_DIR/agent/"
cp "$SOURCE_DIR/agent/pentest-gui.py" "$INSTALL_DIR/agent/"
cp "$SOURCE_DIR/agent/kali_tool_catalog.py" "$INSTALL_DIR/agent/" 2>/dev/null || true
cp "$SOURCE_DIR/agent/knowledge_base.py" "$INSTALL_DIR/agent/" 2>/dev/null || true
cp "$SOURCE_DIR/agent/portable_docker.py" "$INSTALL_DIR/agent/" 2>/dev/null || true
cp "$SOURCE_DIR/agent/case_analysis.ipynb" "$INSTALL_DIR/agent/" 2>/dev/null || true
cp "$SOURCE_DIR/agent/Modelfile" "$INSTALL_DIR/agent/"
cp "$SOURCE_DIR/agent/Modelfile.lite" "$INSTALL_DIR/agent/" 2>/dev/null || true
cp "$SOURCE_DIR/agent/settings.json" "$INSTALL_DIR/agent/"
cp "$SOURCE_DIR/agent/kali_tools.json" "$INSTALL_DIR/agent/" 2>/dev/null || true
cp "$SOURCE_DIR/agent/corrections.json" "$INSTALL_DIR/agent/" 2>/dev/null || true

# Copy Docker files
if [ -d "$SOURCE_DIR/agent/docker" ]; then
    cp -r "$SOURCE_DIR/agent/docker/"* "$INSTALL_DIR/agent/docker/"
fi

# Copy MCP servers
if [ -d "$SOURCE_DIR/mcp-servers" ]; then
    cp -r "$SOURCE_DIR/mcp-servers/"* "$INSTALL_DIR/mcp-servers/" 2>/dev/null || true
    echo "  MCP servers copied"
fi

# Copy knowledge base data
if [ -d "$SOURCE_DIR/agent/knowledge_base" ]; then
    cp -r "$SOURCE_DIR/agent/knowledge_base/"* "$INSTALL_DIR/agent/knowledge_base/" 2>/dev/null || true
fi

echo "  Agent files copied"

# Copy model file if exists
if ls "$SOURCE_DIR/agent/"*.gguf 1>/dev/null 2>&1; then
    echo "  Copying model file (this may take a while)..."
    cp "$SOURCE_DIR/agent/"*.gguf "$INSTALL_DIR/agent/"
    echo "  Model file copied"
fi

echo ""
echo "[6/7] Registering model with Ollama..."
cd "$INSTALL_DIR/agent"
ollama create "$MODEL_NAME" -f Modelfile || {
    echo "[WARN] Model registration failed. You may need to copy the .gguf file manually."
}

# Install Python dependencies
echo ""
echo "[7/7] Installing Python dependencies..."
pip3 install --break-system-packages requests customtkinter pillow scikit-learn PyPDF2 pdfplumber notebook matplotlib

# Docker installation (optional)
if [ "$WITH_DOCKER" = true ]; then
    echo ""
    echo "[EXTRA] Installing Docker..."
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
        usermod -aG docker $SUDO_USER
    fi

    echo "  Building Kali container..."
    cd "$INSTALL_DIR/agent/docker"
    docker compose build || docker build -t htb-kali .
fi

# Create launcher scripts
cat > "$INSTALL_DIR/start-agent.sh" << 'EOF'
#!/bin/bash
cd /opt/htb-pentest/agent
export OLLAMA_HOST=localhost:11434
python3 pentest-agent.py
EOF
chmod +x "$INSTALL_DIR/start-agent.sh"

cat > "$INSTALL_DIR/start-gui.sh" << 'EOF'
#!/bin/bash
cd /opt/htb-pentest/agent
export OLLAMA_HOST=localhost:11434
export DISPLAY=:0
python3 pentest-gui.py
EOF
chmod +x "$INSTALL_DIR/start-gui.sh"

# Create systemd service for remote access
cat > /etc/systemd/system/htb-pentest-api.service << EOF
[Unit]
Description=HTB Pentest Agent API
After=network.target ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/agent
ExecStart=/usr/bin/python3 $INSTALL_DIR/agent/pentest-agent.py --api-mode
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "============================================"
echo "  Deployment Complete!"
echo "============================================"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "Usage:"
echo "  CLI agent:  $INSTALL_DIR/start-agent.sh"
echo "  GUI agent:  $INSTALL_DIR/start-gui.sh"
echo "  Case analysis: jupyter notebook $INSTALL_DIR/agent/case_analysis.ipynb"
echo ""
echo "Ollama API accessible at: http://$(hostname -I | awk '{print $1}'):11434"
echo ""
echo "To enable on boot:"
echo "  sudo systemctl enable htb-pentest-api"
echo ""

# Show system info
echo "System Info:"
echo "  Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "  Swap: $(free -h | grep Swap | awk '{print $2}')"
echo "  GPU: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
