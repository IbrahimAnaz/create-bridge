# Web IDE Remote Agent Integration Guide

This guide enables an external AI agent or engineer operating inside a **Web IDE** (GitHub Codespaces, cloud VM, or browser-based IDE) to read and write directly to the local **Create Mod Bedrock Bridge** directory.

---

## 1. How the Synchronization Works

Since the local backend (NeoForge, ViaProxy, Geyser) runs on the host machine, **GitHub acts as the real-time bridge**:

```
[Web IDE / Cloud Agent]
        │
     (push)
        ▼
 [GitHub Repository]
        ▲
     (pull)
        │
[Local Directory: c:\Users\ibrah\Downloads\crt aro]
(Automated watch daemon pulls & hot-reloads)
```

---

## 2. Setting Up the Connection

### On the Local Machine (Host):
Run the setup command to link to your GitHub repository:
```powershell
python tools/bridge.py github setup <owner/repo_or_url> [--token <PAT>] [--branch master]
```
*Example*:
```powershell
python tools/bridge.py github setup IbrahimAnaz/create-bridge --branch master
```

### Starting the Live Auto-Sync Daemon:
```powershell
python tools/bridge.py github watch --interval 5
```
*When running, the local machine polls GitHub every 5 seconds. As soon as the Web IDE pushes a commit, the local machine pulls it and automatically recompiles the Geyser extension (`compile_bridge.py`)!*

---

## 3. How the Web IDE Agent Reads & Writes

### In the Web IDE:
1. **Clone the repository**:
   ```bash
   git clone https://github.com/<owner>/<repo>.git
   cd <repo>
   ```
2. **Read codebase & handoffs**:
   * Master specification: `CLIENT_EMULATION_BACKEND_HANDOFF.md`
   * Companion mod source: `headless_server/companion_mod/src/`
   * Geyser extension: `portable_bridge/extension/src/com/createbridge/`
   * Dynamic registry dump: `tools/extension/classes/create_registry_dump.json`
3. **Write changes & push**:
   ```bash
   git add .
   git commit -m "feat(emulation): implement deployer arm animation cycle"
   git push origin master
   ```
4. **Local Execution**:
   The local `watch` daemon immediately receives the commit, stages it, and recompiles the bridge without any manual intervention!

---

## 4. Alternative: Direct REST API Read/Write (Zero Git CLI Needed)

If the Web IDE agent interacts exclusively via API calls or webhooks without a full Git terminal:

### Read a file from GitHub:
```powershell
python tools/bridge.py github api-read portable_bridge/extension/src/com/createbridge/network/BridgeSyncServer.java
```

### Write/commit a file directly to GitHub:
```powershell
python tools/bridge.py github api-write portable_bridge/extension/src/com/createbridge/network/BridgeSyncServer.java
```

---

## 5. Remote Server Execution & Live Iteration

The Web IDE agent can trigger commands and tests on the local Minecraft server using `tools/remote_cli.py`.

Inside the Web IDE terminal:
```bash
# 1. Run full system diagnostics (checks ports 25565, 25568, 19132, bytecode patches)
python tools/remote_cli.py doctor

# 2. Check service status, memory, and PIDs
python tools/remote_cli.py status

# 3. Trigger extension recompilation (CreateBridge.jar)
python tools/remote_cli.py compile

# 4. Run automated headless Bedrock client probe (verifies chunk streaming & packet pipeline)
python tools/remote_cli.py test-client

# 5. Fetch live logs from the host
python tools/remote_cli.py logs --service geyser --lines 50
python tools/remote_cli.py logs --service inventory --lines 50

# 6. Execute custom diagnostic scripts
python tools/remote_cli.py exec test_block.py
```

### How Remote Execution Works Under the Hood:
1. `remote_cli.py` writes an action request into `.bridge_actions/request.json` and pushes to GitHub.
2. The host machine's `python tools/bridge.py github watch` daemon pulls the request, executes the command locally, and writes the stdout, stderr, and return code to `.bridge_actions/response.json`.
3. The host daemon commits and pushes `response.json` back to GitHub.
4. `remote_cli.py` pulls the response and displays the live output directly in the Web IDE terminal!

