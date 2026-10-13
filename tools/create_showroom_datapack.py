import json
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
DP_DIR = ROOT / "headless_server" / "world" / "datapacks" / "showroom"
FUNC_DIR = DP_DIR / "data" / "showroom" / "function"
FUNC_DIR.mkdir(parents=True, exist_ok=True)

# 1. pack.mcmeta
mcmeta = {
    "pack": {
        "pack_format": 48,
        "description": "Create Mod Bespoke Showcase Datapack"
    }
}
(DP_DIR / "pack.mcmeta").write_text(json.dumps(mcmeta, indent=2), encoding="utf-8")

# 2. Only the 10 bespoke categories (and all blocks in them)
SHOWCASE_BLOCKS = [
    # 1. Pump
    ("create:mechanical_pump", "Mechanical Pump", "Fluid Kinetics"),
    # 2. Drill
    ("create:mechanical_drill", "Mechanical Drill", "Excavation"),
    # 3. Saw
    ("create:mechanical_saw", "Mechanical Saw", "Tree Felling"),
    # 4. Deployer
    ("create:deployer", "Deployer", "Item Automation"),
    # 5. Encased Fan
    ("create:encased_fan", "Encased Fan", "Air & Bulk Processing"),
    # 6. Press
    ("create:mechanical_press", "Mechanical Press", "Compacting"),
    # 7. Mixer
    ("create:mechanical_mixer", "Mechanical Mixer", "Brewing & Blending"),
    # 8. Millstone
    ("create:millstone", "Millstone", "Milling & Grinding"),
    # 9. Harvester
    ("create:mechanical_harvester", "Mechanical Harvester", "Crop Gathering"),
    # 10. Clocks
    ("create:cuckoo_clock", "Cuckoo Clock", "Timekeeping"),
    ("create:mysterious_cuckoo_clock", "Mysterious Clock", "Timekeeping"),
]

commands = []
commands.append("# ==========================================")
commands.append("# CREATE MOD BESPOKE SHOWCASE (10 CATEGORIES)")
commands.append("# ==========================================")

# Clean entire previous large showroom area in slices under 32,768 block limit
commands.append("# --- CLEAR OLD SHOWROOM AREA ---")
commands.append("fill -10 -60 -15 65 -45 35 minecraft:air replace")
commands.append("fill -10 -60 36 65 -45 85 minecraft:air replace")
commands.append("fill -10 -60 86 65 -45 135 minecraft:air replace")
commands.append("fill -10 -60 136 65 -45 190 minecraft:air replace")

commands.append("# --- FLOORING ---")
commands.append("fill -5 -61 -15 55 -61 35 minecraft:smooth_stone replace")
commands.append("fill -5 -61 36 55 -61 85 minecraft:smooth_stone replace")
commands.append("fill -5 -61 86 55 -61 140 minecraft:smooth_stone replace")

# Layout parameters: 2 grand rows with wide spacing
# Row 1: X=6, 12, 18, 24, 30, 36 at Z=5
# Row 2: X=6, 12, 18, 24, 30 at Z=15
col_count = 6
spacing_x = 6
row_spacing_z = 10
x_start = 6
z_start = 5

for idx, (bname, display_title, subtitle) in enumerate(SHOWCASE_BLOCKS):
    col = idx % col_count
    row = idx // col_count

    bx = x_start + (col * spacing_x)
    bz = z_start + (row * row_spacing_z)

    short_name = bname.replace("create:", "")

    # Sign formatting
    line1 = f'{{"text":"{display_title}","color":"gold","bold":true}}'
    line2 = f'{{"text":"{subtitle}","color":"aqua"}}'
    line3 = '{"text":"[PRESS BUTTON]","color":"dark_green","bold":true}'
    line4 = f'{{"text":"create:{short_name}","color":"gray"}}'

    # Platform around pedestal
    commands.append(f"fill {bx-1} -61 {bz-1} {bx+1} -61 {bz+3} minecraft:smooth_stone")
    # Pedestal under display block
    commands.append(f"setblock {bx} -61 {bz} create:polished_cut_andesite")
    # Display block
    commands.append(f"setblock {bx} -60 {bz} {bname} replace")
    # Air buffer
    commands.append(f"setblock {bx} -60 {bz+1} minecraft:air replace")
    # Command block giving the item
    cmd_nbt = f'{{Command:"give @p {bname} 1"}}'
    commands.append(f"setblock {bx} -60 {bz+2} minecraft:command_block{cmd_nbt} replace")
    # Button on South face of command block
    commands.append(f"setblock {bx} -60 {bz+3} minecraft:oak_button[facing=south,face=wall] replace")
    # Sign on top of command block
    sign_nbt = f'{{front_text:{{messages:[\'{line1}\',\'{line2}\',\'{line3}\',\'{line4}\']}}}}'
    commands.append(f"setblock {bx} -59 {bz+2} minecraft:oak_sign[rotation=0]{sign_nbt} replace")

# Teleport arrival command helper
commands.append("# Welcome & teleport helper")
commands.append("teleport @a 21.0 -60.0 -2.0 0.0 0.0")

(FUNC_DIR / "build.mcfunction").write_text("\n".join(commands) + "\n", encoding="utf-8")
print(f"[+] Successfully wrote {len(commands)} commands for {len(SHOWCASE_BLOCKS)} bespoke blocks to {FUNC_DIR / 'build.mcfunction'}")
