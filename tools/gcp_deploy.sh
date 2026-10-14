#!/usr/bin/env bash
# ==============================================================================
# Google Cloud Compute Engine (GCE) Turnkey Deploy Script
# Run this from anywhere with 'gcloud' CLI installed:
#   chmod +x tools/gcp_deploy.sh && ./tools/gcp_deploy.sh [INSTANCE_NAME] [ZONE]
# ==============================================================================

set -e

INSTANCE_NAME="${1:-create-bridge-server}"
ZONE="${2:-us-central1-a}"
MACHINE_TYPE="e2-standard-4" # 4 vCPUs, 16 GB RAM (Ideal for Create Mod + Geyser)

echo "============================================================"
echo "  DEPLOYING CREATE MOD BRIDGE TO GOOGLE CLOUD VM"
echo "============================================================"
echo "Instance: $INSTANCE_NAME"
echo "Zone:     $ZONE"
echo "Machine:  $MACHINE_TYPE"
echo ""

# 1. Create Firewall Rule for Bedrock UDP 19132 and TCP 25565
echo "[1/3] Creating Google Cloud Firewall Rules..."
gcloud compute firewall-rules create allow-minecraft-bridge \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:25565,tcp:25568,udp:19132,tcp:8090 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=minecraft-bridge-server \
    --quiet || echo "Firewall rule already exists, skipping."

# 2. Write Startup Script for VM
STARTUP_SCRIPT=$(cat << 'EOF'
#!/bin/bash
set -e
echo "Starting Create Bridge VM Initialization..."
apt-get update -qq
apt-get install -y -qq openjdk-21-jdk nodejs npm tmux git python3 python3-pip

mkdir -p /opt/create-bridge
cd /opt/create-bridge
if [ ! -d ".git" ]; then
    git clone https://github.com/IbrahimAnaz/create-bridge.git .
else
    git pull origin master
fi

# Make scripts executable
chmod +x headless_server/run.sh tools/*.sh || true

# Start Daemons in TMUX
tmux new-session -d -s neoforge "cd /opt/create-bridge/headless_server && ./run.sh"
tmux new-session -d -s viaproxy "cd /opt/create-bridge/headless_server/viaproxy && java -jar ViaProxy.jar cli --bind-address 127.0.0.1:25568 --target-address 127.0.0.1:25565 --target-version 1.21-1.21.1"
tmux new-session -d -s geyser "cd /opt/create-bridge/headless_server/geyser && java -jar Geyser-Standalone.jar"

echo "Create Bridge Initialization Complete!"
EOF
)

TMP_STARTUP="/tmp/cb_startup.sh"
echo "$STARTUP_SCRIPT" > "$TMP_STARTUP"

# 3. Create Compute Instance
echo ""
echo "[2/3] Provisioning Compute Engine VM ($INSTANCE_NAME)..."
gcloud compute instances create "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --image-family="debian-12" \
    --image-project="debian-cloud" \
    --boot-disk-size="50GB" \
    --tags="minecraft-bridge-server" \
    --metadata-from-file="startup-script=$TMP_STARTUP" \
    --quiet

# 4. Fetch External IP
echo ""
echo "[3/3] Fetching VM External IP..."
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "============================================================"
echo ">>> DEPLOYMENT COMPLETE! <<<"
echo "VM Name:     $INSTANCE_NAME"
echo "External IP: $EXTERNAL_IP"
echo ""
echo "Bedrock Client Connection Address:"
echo "  IP:   $EXTERNAL_IP"
echo "  Port: 19132 (UDP)"
echo ""
echo "To SSH into the server as developer / agent:"
echo "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo "============================================================"
