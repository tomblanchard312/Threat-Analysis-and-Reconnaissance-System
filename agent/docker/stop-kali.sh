#!/bin/bash
# Stop the Kali Linux Docker container

echo ""
echo "============================================"
echo "  Stopping Kali Linux Container"
echo "============================================"
echo ""

if docker stop htb-kali > /dev/null 2>&1; then
    echo "[OK] Kali container stopped"
else
    echo "[INFO] Container was not running"
fi

echo ""
