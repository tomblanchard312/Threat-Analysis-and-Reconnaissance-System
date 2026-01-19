#!/bin/bash
# Deploy trained HTB model to Jetson Orin Nano
#
# Usage:
#   ./deploy_to_jetson.sh <jetson_ip> [model_path]
#
# Example:
#   ./deploy_to_jetson.sh 192.168.1.100
#   ./deploy_to_jetson.sh jetson.local ../output/gguf/model-q4_k_m.gguf

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
JETSON_USER="${JETSON_USER:-jetson}"
JETSON_MODEL_DIR="/home/${JETSON_USER}/models"
MODEL_NAME="htb-pentest"
DEFAULT_GGUF="../output/gguf/model-q4_k_m.gguf"

# Parse arguments
JETSON_IP="$1"
GGUF_PATH="${2:-$DEFAULT_GGUF}"

if [ -z "$JETSON_IP" ]; then
    echo -e "${RED}Error: Jetson IP address required${NC}"
    echo "Usage: $0 <jetson_ip> [model_path]"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

if [ ! -f "$GGUF_PATH" ]; then
    echo -e "${RED}Error: GGUF file not found: $GGUF_PATH${NC}"
    echo "Run convert_to_gguf.py first to create the GGUF file"
    exit 1
fi

GGUF_DIR=$(dirname "$GGUF_PATH")
MODELFILE_PATH="${GGUF_DIR}/Modelfile"

if [ ! -f "$MODELFILE_PATH" ]; then
    echo -e "${RED}Error: Modelfile not found: $MODELFILE_PATH${NC}"
    exit 1
fi

echo "=============================================="
echo "HTB Model Deployment to Jetson"
echo "=============================================="
echo "Jetson: ${JETSON_USER}@${JETSON_IP}"
echo "Model: $GGUF_PATH"
echo "=============================================="

# Get file sizes
GGUF_SIZE=$(du -h "$GGUF_PATH" | cut -f1)
echo -e "${YELLOW}GGUF size: $GGUF_SIZE${NC}"
echo ""

# Step 1: Create model directory on Jetson
echo -e "${GREEN}[1/5] Creating model directory on Jetson...${NC}"
ssh "${JETSON_USER}@${JETSON_IP}" "mkdir -p ${JETSON_MODEL_DIR}"

# Step 2: Copy GGUF file
echo -e "${GREEN}[2/5] Copying GGUF file (this may take a while)...${NC}"
scp "$GGUF_PATH" "${JETSON_USER}@${JETSON_IP}:${JETSON_MODEL_DIR}/"

GGUF_FILENAME=$(basename "$GGUF_PATH")

# Step 3: Create Modelfile with correct path for Jetson
echo -e "${GREEN}[3/5] Creating Modelfile on Jetson...${NC}"
ssh "${JETSON_USER}@${JETSON_IP}" "cat > ${JETSON_MODEL_DIR}/Modelfile" << EOF
# HTB Pentest Model - Trained on Hack The Box writeups
FROM ${JETSON_MODEL_DIR}/${GGUF_FILENAME}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

SYSTEM """You are a helpful penetration testing assistant trained on Hack The Box writeups. You provide detailed, educational explanations of security concepts, tools, and techniques.

Your expertise includes:
- Reconnaissance and enumeration techniques
- Web application security testing
- Network exploitation
- Privilege escalation (Linux and Windows)
- Post-exploitation techniques
- Common security tools (nmap, burp suite, metasploit, etc.)

Important guidelines:
- Always emphasize that techniques should only be used in authorized environments
- Provide educational context for security concepts
- Explain the "why" behind techniques, not just the "how"
"""

TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>"""
EOF

# Step 4: Create Ollama model
echo -e "${GREEN}[4/5] Creating Ollama model...${NC}"
ssh "${JETSON_USER}@${JETSON_IP}" "docker exec ollama-orin ollama create ${MODEL_NAME} -f ${JETSON_MODEL_DIR}/Modelfile"

# Step 5: Verify
echo -e "${GREEN}[5/5] Verifying model...${NC}"
ssh "${JETSON_USER}@${JETSON_IP}" "docker exec ollama-orin ollama list"

echo ""
echo "=============================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo "=============================================="
echo ""
echo "Test the model:"
echo "  ssh ${JETSON_USER}@${JETSON_IP}"
echo "  docker exec -it ollama-orin ollama run ${MODEL_NAME}"
echo ""
echo "Or via API:"
echo "  curl http://${JETSON_IP}:11434/api/generate -d '{"
echo "    \"model\": \"${MODEL_NAME}\","
echo "    \"prompt\": \"How would you approach a web application pentest?\""
echo "  }'"
echo ""
