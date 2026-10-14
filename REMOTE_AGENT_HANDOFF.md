# Remote Agent Handoff: Create Mod Bedrock-Java Bridge

> **Welcome!** You are stepping into the **Create Mod Bedrock-Java Bridge** codebase. This project connects vanilla **Minecraft Bedrock Edition** clients to a headless **NeoForge 1.21.1** server running the **Create Mod (v6.0.8)** with full kinetic parity, custom block models, and dynamic emulation.
> 
> All backend services are currently running on the host machine. You do **not** need a local Java environment or terminal `curl` access—you can read, write, hot-compile, and test everything directly via your **web browser** or **GitHub**.

---

## 1. Quick-Start Access Options

Choose whichever access method fits your environment:

### Method A: Browser Web Dashboard (Zero Terminal / Zero cURL)
The host runs a secure, authenticated Cloudflare HTTPS tunnel. Open this URL directly in your browser:

👉 **[https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/](https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/)**

**What you can do in this dashboard:**
* 🩺 **Run Diagnostics (Doctor)**: One-click check of all ports (25565, 25568, 19132) and bytecode patches.
* 🔨 **Hot Compile Extension**: Rebuilds `CreateBridge.jar` directly on the host in ~1.5s.
* 🤖 **Test Headless Bedrock Client**: Connects a virtual Bedrock protocol bot (`DummyBot`) to verify chunk streaming, packet interceptors, and block entity updates.
* 📝 **In-Browser Code Editor**: Read any source file, edit Java code in the textarea, and click **"Save & Recompile"**!
* 📋 **Live Server Logs**: View real-time logs from Geyser, NeoForge, or inventory debug streams.

#### Direct Browser / GET Endpoints:
Every action is packaged directly into the URL for simple HTTP `GET` fetching:
* **Diagnostics**: `https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/doctor`
* **Hot Compile**: `https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/compile`
* **Test Client**: `https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/test-client`
* **Read File**: `https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/read?path=HANDOFF.md`
* **Write File**: `https://navigator-lens-sheriff-rocks.trycloudflare.com/qu15LjCAbK85pfAsGZMKSYHm1KnRlZ68KWBwP1lSBjk/write?path=<file>&content=<encoded_text>`

---

### Method B: GitHub Repository (Git Push/Pull)
The repository is live on GitHub:
* **Repository**: **`https://github.com/IbrahimAnaz/create-bridge`**
* **Branch**: `master`

**Workflow:**
1. Clone: `git clone https://github.com/IbrahimAnaz/create-bridge.git`
2. Edit your files in your IDE.
3. Commit and push: `git commit -am "feat: ..." && git push origin master`
4. Trigger recompilation via the browser dashboard button or URL: `.../compile`.

---

### Method C: Google Colab SSH & Google Drive
* **Bootstrap Script**: `tools/COLAB_SSH_SETUP.md` contains a 1-cell notebook that boots the entire server stack inside a Colab Linux VM with direct Tmate / Cloudflare SSH.
* **Pre-Packaged Zip**: `create_bridge.zip` (20.8 MB in workspace root) can be mounted or unzipped directly in Google Drive / Colab.

---

### Method D: Google Cloud Platform & Cloud Shell (1-Click Browser Launch)
* **1-Click Open in Cloud Shell**: [**Open in Google Cloud Shell**](https://ssh.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/IbrahimAnaz/create-bridge) (launches in-browser Linux IDE with pre-installed `gcloud` and `git`).
* **Deploy to 24/7 GCE VM**: Run `tools/gcp_deploy.sh` to provision an `e2-standard-4` instance with open firewall ports (`19132` UDP) and background server daemons. Full documentation in `GCP_SETUP.md`.

---

## 2. Architecture & Service Map

The bridge architecture routes packets between Bedrock and Java NeoForge:

```
[Bedrock Client / DummyBot (UDP 19132)]
                 ▲
                 │ RakNet
                 ▼
[Geyser Standalone (Port 19132) + CreateBridge.jar Extension]
                 ▲
                 │ (Internal Port 25575 Event Subscription)
                 ├─── [Companion Mod Mixins (NeoForge)]
                 │
                 ▼
[ViaProxy 3.4 (TCP 25568 -> 25565)]
                 ▲
                 │ Java TCP
                 ▼
[NeoForge 1.21.1 Dedicated Server (Port 25565) + Create Mod 6.0.8]
```

### Current Operational Ports (All 100% PASS):
* **TCP 25565**: NeoForge 1.21.1 Dedicated Server (Create Mod v6.0.8).
* **TCP 25568**: ViaProxy Bridge (Translates packets and component registries).
* **UDP 19132**: Geyser Bedrock Server (Handles Bedrock RakNet protocol).
* **TCP 25575**: Companion Subscription Port (Streams real-time block entity events).
* **TCP 8088**: Pack Viewer (Local web viewer for Bedrock custom resource packs).
* **HTTPS Tunnel**: Cloudflare Quick Tunnel serving the Web Dashboard.

---

## 3. Core Problems to Solve & Technical Tasks

### Task 1: Depot Flat Item Display (Parity Fix)
* **The Problem**: Currently, `spawnOrUpdateDepotItem` in `PacketInterceptorManager.java` uses `AddItemEntityPacket`. In Minecraft Bedrock C++, dropped items (`minecraft:item`) are hardcoded to continuously spin 360° and bob vertically. On a Create Mod depot, items should rest stationary and completely flat.
* **The Parity Fix**:
  1. Use Bedrock's floor item frame (`UpdateBlockPacket` with `minecraft:frame`, `facing_direction = 1` [UP] and `BlockEntityDataPacket` with `id: "ItemFrame"`, `ItemRotation = 0.0f` at `pos.up()`).
  2. Frame borders are already transparent in `create_cogwheel_rp`.
  3. **Crucial Guard**: Only dispatch packets after `CLIENT_READY_SESSIONS.contains(session)` (delayed 2.0s post-join) to prevent client-side world-join access violations (`0xc0000005`).
* **Source Location**: `portable_bridge/extension/src/com/createbridge/network/PacketInterceptorManager.java` lines 360–420.

---

### Task 2: Deployer Interaction & State Emulation
* **The Problem**: 
  - Clicking an existing Deployer without sneaking inserts the held item into the Deployer's `HeldItem` or `Filter` slot on the server (`SET_SLOT [EMPTY]`). Because Bedrock lacks the Java client-side renderer, the item disappeared from the hotbar with no visual feedback, making it appear "broken".
  - Empty-hand clicking extracts the held item (`id=11421`).
  - Placing adjacent blocks against interactive blocks requires crouching/sneaking.
* **The Parity Fix**:
  1. When a player interacts with a Deployer without sneaking, provide immediate Bedrock feedback:
     * Send a client-side sound packet (`LevelSoundEventPacket` with `ARMOR_EQUIP_GENERIC`).
     * Display a temporary action bar HUD tip: `session.sendMessage("Deployer holding: " + itemName)`.
  2. Connect the companion mod's `deployer_update` event stream (over port 25575) to render the held tool on the deployer's face or update its state.
* **Source Locations**:
  - `portable_bridge/extension/src/com/createbridge/network/PacketInterceptorManager.java` (`handleBlockPick`, `handleDepotInteraction`)
  - `portable_bridge/extension/src/com/createbridge/network/BridgeSyncServer.java`

---

### Task 3: Kinetic Motion Parity (RPM -> Bedrock Permutations)
* **The Architecture**:
  - NeoForge companion mod (`KineticBlockEntityMixin.java`) streams RPM and overstress changes via port 25575 JSON:
    ```json
    {"t": "kinetic_update", "x": 20, "y": -60, "z": 5, "speed": 64.0, "overstressed": false}
    ```
  - Map `speed` into directional Bedrock block permutation states or Molang variables in `create_cogwheel_rp` to trigger smooth 60 FPS rotation client-side.
* **Source Location**: `portable_bridge/extension/src/com/createbridge/network/BridgeSyncServer.java`.

---

## 4. Key Files Directory

| Path | Purpose |
| :--- | :--- |
| `portable_bridge/extension/src/com/createbridge/network/PacketInterceptorManager.java` | Main packet interceptor; handles depot item displays, block picks, and Bedrock client-ready lifecycle. |
| `portable_bridge/extension/src/com/createbridge/network/BridgeSyncServer.java` | Port 25575 TCP socket listener; receives authoritative JSON events from NeoForge and triggers emulation. |
| `headless_server/companion_mod/src/main/java/com/createbridge/companion/mixin/` | Java server Mixins (`DepotBehaviourMixin`, `KineticBlockEntityMixin`) injecting into Create Mod methods. |
| `tools/dummy_bedrock/dummy_client.js` | Headless Bedrock protocol client; simulates joining Bedrock player, logs packets, verifies chunk stream. |
| `tools/compile_bridge.py` | Cross-platform build script; compiles Java sources into `CreateBridge.jar` for both Geyser and ViaProxy. |
| `tools/bridge.py` | Unified host CLI; runs diagnostics (`doctor`), monitors health (`status`), inspects logs (`logs`). |
| `tools/http_bridge.py` | Cloudflare tunnel daemon serving the browser dashboard and URL-packaged API endpoints. |

---

## 5. Iteration & Testing Workflow

Whenever you edit Java or configuration files:
1. **Save your changes** (via the Web Dashboard editor or Git push).
2. **Click "Hot Compile Extension"** in the Web Dashboard (or navigate to `/compile`).
3. **Click "Test Headless Bedrock Client"** in the Web Dashboard (or navigate to `/test-client`) to verify packet flow without needing the Minecraft game client open.
4. Check the **Action Console Output** on the page for instant build logs and verification results.
