#!/usr/bin/env bash
# ==============================================================================
# Google Cloud Shell 1-Click Bootstrap Script
# Run this inside Google Cloud Shell or any Debian/Ubuntu cloud VM:
#   chmod +x tools/open_cloudshell.sh && ./tools/open_cloudshell.sh
# ==============================================================================

set -e

echo "============================================================"
echo "  CREATE MOD BEDROCK BRIDGE - GOOGLE CLOUD SHELL SETUP"
echo "============================================================"

# 1. Install Java 21 & Node.js if missing
echo "[1/4] Checking Java 21 & Node.js..."
if ! java -version 2>&1 | grep -q "21"; then
    echo "  Installing OpenJDK 21..."
    sudo apt-get update -qq && sudo apt-get install -y -qq openjdk-21-jdk > /dev/null
fi

if ! command -v node > /dev/null; then
    echo "  Installing Node.js..."
    sudo apt-get install -y -qq nodejs npm > /dev/null
fi

echo "  Java version: $(java -version 2>&1 | head -n 1)"
echo "  Node version: $(node -v)"

# 2. Run system diagnostics
echo ""
echo "[2/4] Running bridge diagnostics..."
python3 tools/bridge.py doctor

# 3. Test headless Bedrock client
echo ""
echo "[3/4] Running headless Bedrock client verification..."
python3 tools/bridge.py test-client || true

# 4. Optional: Start all daemons in tmux
echo ""
echo "[4/4] Setup complete!"
echo "To launch all 3 server daemons in background tmux sessions, run:"
echo "  tmux new-session -d -s neoforge 'cd headless_server && ./run.sh'"
echo "  tmux new-session -d -s viaproxy 'cd headless_server/viaproxy && java -jar ViaProxy.jar cli --bind-address 127.0.0.1:25568 --target-address 127.0.0.1:25565 --target-version 1.21-1.21.1'"
echo "  tmux new-session -d -s geyser 'cd headless_server/geyser && java -jar Geyser-Standalone.jar'"
echo ""
echo "To recompile extension: python3 tools/compile_bridge.py"
echo "To monitor status:      python3 tools/bridge.py status"
echo "============================================================"
