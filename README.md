# Create Mod Cross-Play: Bedrock Kinetic Puppet PoC

This test package proves the **RenderDragon-compliant Kinetic Molang Puppet Architecture** for bringing Create Mod mechanics to vanilla Bedrock Edition (Windows, Xbox, PlayStation, Switch, iOS, Android).

It eliminates network lag and client scripting bans by utilizing:
1. **Dynamic Actor Properties** (`create:rpm`) synchronized via vanilla entity metadata.
2. **Native Molang continuous math evaluation** running at display refresh rates (60Hz / 120Hz).

---

## ⚡ How to Test in Minecraft Bedrock (60 Seconds)

### Option 1: One-Click Install (.mcaddon)
1. Double-click **`Create_CrossPlay_Test.mcaddon`** (or open it on mobile/console).
2. Minecraft Bedrock will automatically import both the **Resource Pack** and **Behavior Pack**.
3. Create a new World (or edit an existing one):
   - Under **Resource Packs**, activate: `Create Cross-Play RP [Cogwheel PoC]`
   - Under **Behavior Packs**, activate: `Create Cross-Play BP [Cogwheel PoC]`
   - Ensure **Cheats** are enabled.
4. Enter the world.

### In-Game Test Commands:

#### 1. Spawn the Cogwheel
```mcfunction
/summon create:cogwheel ~ ~1 ~
```
*(The cogwheel appears and immediately begins rotating smoothly at its default 32 RPM!)*

#### 2. Test Live Speed Overrides (Variable RPM)
Change the RPM dynamically without re-summoning:
```mcfunction
# Fast Speed (128 RPM)
/event entity @e[type=create:cogwheel] event_speed_128

# Reverse Direction (-64 RPM)
/event entity @e[type=create:cogwheel] event_speed_reverse

# Full Halt (0 RPM)
/event entity @e[type=create:cogwheel] event_speed_stop

# Return to Standard Speed (32 RPM)
/event entity @e[type=create:cogwheel] event_speed_32
```

Or adjust the property directly:
```mcfunction
/execute as @e[type=create:cogwheel] run property @s "create:rpm" 96.0
```

---

## 🖥️ How to Test in Blockbench (Without Opening Minecraft)

If you have [Blockbench](https://www.blockbench.net/) installed:
1. Open Blockbench and choose **Bedrock Model**.
2. Go to **File -> Open Model** and open:
   `create_cogwheel_rp/models/entity/cogwheel.geo.json`
3. Load the texture:
   `create_cogwheel_rp/textures/entity/create/cogwheel.png`
4. Switch to the **Animate** tab at the top right.
5. Go to **Animation -> Import Animation** and select:
   `create_cogwheel_rp/animations/cogwheel.animation.json`
6. Press the **Play** button!

---

## 📦 What Was Built

```
crt aro/
├── Create_CrossPlay_Test.mcaddon   <-- Ready to double-click & install
├── Create_Cogwheel_RP.mcpack       <-- Standalone Resource Pack
├── Create_Cogwheel_BP.mcpack       <-- Standalone Behavior Pack
├── create_cogwheel_rp/             <-- Unpacked Resource Pack source
│   ├── entity/cogwheel.entity.json
│   ├── models/entity/cogwheel.geo.json
│   ├── animations/cogwheel.animation.json
│   └── textures/entity/create/cogwheel.png
├── create_cogwheel_bp/             <-- Unpacked Behavior Pack source
│   └── entities/cogwheel.json
├── build_poc.py                    <-- Pack compilation script
└── README.md
```
