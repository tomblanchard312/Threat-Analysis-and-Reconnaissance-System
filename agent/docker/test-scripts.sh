#!/bin/bash
# Test script validator for portable Docker scripts
# Tests for common issues without actually running Docker

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Portable Docker Scripts - Validation Tests${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PASS_COUNT=0
FAIL_COUNT=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Testing: $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# Test 1: Script syntax
echo -e "${CYAN}[1/6] Syntax Tests${NC}"
run_test "portable-dockerd.sh syntax" "bash -n $SCRIPT_DIR/portable-dockerd.sh"
run_test "stop-portable-dockerd.sh syntax" "bash -n $SCRIPT_DIR/stop-portable-dockerd.sh"
run_test "setup-portable-daemon.sh syntax" "bash -n $SCRIPT_DIR/setup-portable-daemon.sh"
echo ""

# Test 2: File permissions
echo -e "${CYAN}[2/6] File Permission Tests${NC}"
run_test "portable-dockerd.sh executable" "test -x $SCRIPT_DIR/portable-dockerd.sh"
run_test "stop-portable-dockerd.sh executable" "test -x $SCRIPT_DIR/stop-portable-dockerd.sh"
run_test "setup-portable-daemon.sh executable" "test -x $SCRIPT_DIR/setup-portable-daemon.sh"
echo ""

# Test 3: Required commands
echo -e "${CYAN}[3/6] Required Command Tests${NC}"
run_test "bash available" "command -v bash"
run_test "mkdir available" "command -v mkdir"
run_test "kill available" "command -v kill"
run_test "uname available" "command -v uname"
echo ""

# Test 4: Script structure
echo -e "${CYAN}[4/6] Script Structure Tests${NC}"
run_test "portable-dockerd has shebang" "head -1 $SCRIPT_DIR/portable-dockerd.sh | grep -q '^#!/bin/bash'"
run_test "portable-dockerd has set -e" "grep -q 'set -e' $SCRIPT_DIR/portable-dockerd.sh"
run_test "stop-dockerd has shebang" "head -1 $SCRIPT_DIR/stop-portable-dockerd.sh | grep -q '^#!/bin/bash'"
run_test "setup-daemon has shebang" "head -1 $SCRIPT_DIR/setup-portable-daemon.sh | grep -q '^#!/bin/bash'"
echo ""

# Test 5: Path handling
echo -e "${CYAN}[5/6] Path Handling Tests${NC}"
run_test "portable-dockerd calculates SCRIPT_DIR" "grep -q 'SCRIPT_DIR=' $SCRIPT_DIR/portable-dockerd.sh"
run_test "portable-dockerd calculates USB_ROOT" "grep -q 'USB_ROOT=' $SCRIPT_DIR/portable-dockerd.sh"
run_test "portable-dockerd creates directories" "grep -q 'mkdir -p' $SCRIPT_DIR/portable-dockerd.sh"
run_test "stop-dockerd handles PID file" "grep -q 'DOCKER_PID' $SCRIPT_DIR/stop-portable-dockerd.sh"
echo ""

# Test 6: Error handling
echo -e "${CYAN}[6/6] Error Handling Tests${NC}"
run_test "portable-dockerd checks binaries" "grep -q 'if \[ ! -f' $SCRIPT_DIR/portable-dockerd.sh"
run_test "portable-dockerd has timeout logic" "grep -q 'TIMEOUT=' $SCRIPT_DIR/portable-dockerd.sh"
run_test "stop-dockerd checks if running" "grep -q 'kill -0' $SCRIPT_DIR/stop-portable-dockerd.sh"
run_test "setup-daemon checks architecture" "grep -q 'uname -m' $SCRIPT_DIR/setup-portable-daemon.sh"
echo ""

# Summary
echo -e "${CYAN}============================================================${NC}"
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}  All tests passed! ($PASS_COUNT/$((PASS_COUNT + FAIL_COUNT)))${NC}"
    echo -e "${CYAN}============================================================${NC}"
    exit 0
else
    echo -e "${YELLOW}  Some tests failed: $PASS_COUNT passed, $FAIL_COUNT failed${NC}"
    echo -e "${CYAN}============================================================${NC}"
    exit 1
fi
