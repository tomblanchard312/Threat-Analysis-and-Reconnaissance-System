#!/bin/bash
# Remote deployment script for Jetson Orin Nano
# Deploys HTB Pentest Agent over SSH
#
# Usage: ./remote-deploy.sh user@jetson-ip [OPTIONS]
#
# Options:
#   --with-model     Copy the model file (4GB+, slow)
#   --with-docker    Install Docker on Jetson
#   --with-training  Include training code

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 user@jetson-ip [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --with-model     Copy the model file (4GB+)"
    echo "  --with-docker    Install Docker on Jetson"
    echo "  --with-training  Include training code"
    exit 1
fi

TARGET="$1"
shift

WITH_MODEL=false
DEPLOY_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-model)
            WITH_MODEL=true
            shift
            ;;
        --with-docker)
            DEPLOY_ARGS="$DEPLOY_ARGS --with-docker"
            shift
            ;;
        --with-training)
            DEPLOY_ARGS="$DEPLOY_ARGS --with-training"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/../.."

echo "============================================"
echo "  Remote Deployment to Jetson"
echo "============================================"
echo ""
echo "Target: $TARGET"
echo "Source: $SOURCE_DIR"
echo ""

# Create temporary deployment package
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/htb-pentest-deploy"
mkdir -p "$PACKAGE_DIR/agent/docker"

echo "[1/4] Creating deployment package..."

# Copy essential files
cp "$SOURCE_DIR/agent/pentest-agent.py" "$PACKAGE_DIR/agent/"
cp "$SOURCE_DIR/agent/pentest-gui.py" "$PACKAGE_DIR/agent/"
cp "$SOURCE_DIR/agent/Modelfile" "$PACKAGE_DIR/agent/"
cp "$SOURCE_DIR/agent/settings.json" "$PACKAGE_DIR/agent/"
cp "$SOURCE_DIR/agent/kali_tools.json" "$PACKAGE_DIR/agent/" 2>/dev/null || true
cp -r "$SOURCE_DIR/agent/docker/"* "$PACKAGE_DIR/agent/docker/" 2>/dev/null || true
cp "$SCRIPT_DIR/deploy-to-jetson.sh" "$PACKAGE_DIR/"

# Copy model if requested
if [ "$WITH_MODEL" = true ]; then
    MODEL_FILE=$(ls "$SOURCE_DIR/agent/"*.gguf 2>/dev/null | head -1)
    if [ -n "$MODEL_FILE" ]; then
        echo "  Including model file: $(basename $MODEL_FILE)"
        cp "$MODEL_FILE" "$PACKAGE_DIR/agent/"
    else
        echo "  [WARN] No model file found"
    fi
fi

echo "[2/4] Copying files to Jetson..."
scp -r "$PACKAGE_DIR" "$TARGET:/tmp/"

echo "[3/4] Running deployment script..."
ssh -t "$TARGET" "sudo bash /tmp/htb-pentest-deploy/deploy-to-jetson.sh $DEPLOY_ARGS"

echo "[4/4] Cleaning up..."
rm -rf "$TEMP_DIR"
ssh "$TARGET" "rm -rf /tmp/htb-pentest-deploy"

echo ""
echo "============================================"
echo "  Remote Deployment Complete!"
echo "============================================"
echo ""
echo "SSH to Jetson and run:"
echo "  /opt/htb-pentest/start-agent.sh"
echo ""
