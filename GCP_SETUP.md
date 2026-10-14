# Google Cloud Integration Guide: Create Mod Bedrock Bridge

This guide allows you or your remote AI agent to operate, test, or host the **Create Mod Bedrock Bridge** directly inside the **Google Cloud Platform (GCP)** ecosystem.

---

## 1. One-Click: Open in Google Cloud Shell (Fastest & Free)

Google Cloud Shell provides a free in-browser Linux development environment with 5 GB persistent storage, pre-installed `gcloud`, `git`, `python3`, and a web-based IDE (VS Code / Code-OSS).

Click this link in any browser to clone the repository and launch the Cloud Shell editor immediately:

👉 **[Open in Google Cloud Shell](https://ssh.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/IbrahimAnaz/create-bridge)**

### Quick Setup inside Cloud Shell:
Once Cloud Shell opens, run the 1-click bootstrap script in the terminal:
```bash
chmod +x tools/open_cloudshell.sh
./tools/open_cloudshell.sh
```
This automatically verifies Java 21, Node.js, runs system diagnostics (`python3 tools/bridge.py doctor`), and tests the headless Bedrock client.

---

## 2. Deploy Dedicated 24/7 Server on Google Compute Engine (GCE)

If you want the entire Minecraft server hosted permanently in Google Cloud with a public external IP (no dependency on keeping your local PC awake):

### Run from Google Cloud Shell (or any machine with `gcloud`):
```bash
chmod +x tools/gcp_deploy.sh
./tools/gcp_deploy.sh create-bridge-host us-central1-a
```

### What this automated script does:
1. **Opens GCP Firewall**: Opens incoming UDP `19132` (Bedrock), TCP `25565` (NeoForge), TCP `25568` (ViaProxy), and TCP `8090` (Web Bridge).
2. **Provisions VM**: Creates an `e2-standard-4` instance (4 vCPUs, 16 GB RAM) with Debian 12.
3. **Auto-Initializes**: Installs OpenJDK 21, pulls the repository from GitHub, and launches the 3 background services in `tmux`.
4. **Prints Public Connection IP**: Gives you the public IP address for your Bedrock client to connect directly!

### Connecting Bedrock to the GCP VM:
* **Server Name**: `Create Bridge GCP`
* **Server Address**: `<EXTERNAL_IP_PRINTED_BY_SCRIPT>`
* **Port**: `19132`

---

## 3. Remote Agent Access & Iteration on Google Cloud

The remote agent can manage the Google Cloud VM using standard `gcloud` commands:

```bash
# SSH into the server instance
gcloud compute ssh create-bridge-host --zone=us-central1-a

# Check live service status
python3 /opt/create-bridge/tools/bridge.py status

# Recompile extension hot
python3 /opt/create-bridge/tools/compile_bridge.py

# Attach to live NeoForge console
tmux attach -t neoforge

# Attach to live Geyser console
tmux attach -t geyser
```

---

## 4. Google Cloud Storage (GCS) Fast Sync

If the agent prefers syncing directly via Cloud Storage buckets instead of Git:

```bash
# Push updates from local to GCS bucket
gcloud storage rsync . gs://<your-gcs-bucket>/create-bridge --recursive

# Pull updates from GCS into the server
gcloud storage rsync gs://<your-gcs-bucket>/create-bridge /opt/create-bridge --recursive
```
