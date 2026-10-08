import os
import sys
import json
import zipfile
import subprocess
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"
GEYSER_DIR = ROOT / "headless_server" / "geyser"
EXT_DIR = GEYSER_DIR / "extensions"
EXT_BUILD_DIR = ROOT / "tools" / "extension"

CASING_BLOCKS = [
    ("create:andesite_casing", "create_andesite_casing", "assets/create/textures/block/andesite_casing.png", [32328, 32329]),
    ("create:brass_casing", "create_brass_casing", "assets/create/textures/block/brass_casing.png", [32330, 32331]),
    ("create:copper_casing", "create_copper_casing", "assets/create/textures/block/copper_casing.png", [32332, 32333]),
    ("create:railway_casing", "create_railway_casing", "assets/create/textures/block/railway_casing.png", [32336, 32337]),
    ("create:raw_zinc_block", "create_raw_zinc_block", "assets/create/textures/block/raw_zinc_block.png", [32338]),
    ("create:zinc_block", "create_zinc_block", "assets/create/textures/block/zinc_block.png", [32339]),
    ("create:brass_block", "create_brass_block", "assets/create/textures/block/brass_block.png", [32342]),
    # Other placed blocks from Section Y=4
    ("create:large_cogwheel", "create_cogwheel", "assets/create/textures/block/andesite_casing.png", [27289]),
    ("create:depot", "create_brass_casing", "assets/create/textures/block/brass_casing.png", [47909]),
    ("create:chute", "create_andesite_casing", "assets/create/textures/block/andesite_casing.png", [46215]),
    ("create:schematicannon", "create_copper_casing", "assets/create/textures/block/copper_casing.png", [51297]),
]

def step1_extract_textures_and_pack():
    print("[1/4] Extracting Create block textures...")
    tex_dir = RP_DIR / "textures" / "blocks"
    tex_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(MOD_JAR, "r") as z:
        for block_id, tex_key, jar_path, _ in CASING_BLOCKS:
            out_file = tex_dir / f"{tex_key.replace('create_', '')}.png"
            with z.open(jar_path) as s, open(out_file, "wb") as d:
                d.write(s.read())
            print(f"  + Extracted {out_file.name}")

    # Generate Sanity Check Dirt Texture (Neon Magenta with Yellow border & Cyan cross)
    from PIL import Image
    dirt_file = tex_dir / "dirt.png"
    img = Image.new('RGBA', (16, 16), (255, 0, 255, 255))
    px = img.load()
    for x in range(16):
        px[x, 0] = (255, 255, 0, 255)
        px[x, 15] = (255, 255, 0, 255)
    for y in range(16):
        px[0, y] = (255, 255, 0, 255)
        px[15, y] = (255, 255, 0, 255)
    for i in range(16):
        px[i, 7] = (0, 255, 255, 255)
        px[i, 8] = (0, 255, 255, 255)
        px[7, i] = (0, 255, 255, 255)
        px[8, i] = (0, 255, 255, 255)
    img.save(dirt_file)
    print(f"  + Generated sanity check texture: {dirt_file.name}")

    print("[2/4] Updating Bedrock terrain_texture.json & blocks.json...")
    terrain_data = {
        "resource_pack_name": "create_bedrock",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {}
    }
    blocks_data = {
        "format_version": "1.20.10"
    }

    for block_id, tex_key, _, _ in CASING_BLOCKS:
        fname = tex_key.replace('create_', '')
        terrain_data["texture_data"][tex_key] = {
            "textures": f"textures/blocks/{fname}"
        }
        blocks_data[block_id] = {
            "textures": tex_key,
            "sound": "wood" if "casing" in block_id else "metal"
        }
    
    # Also keep cogwheel entity texture
    terrain_data["texture_data"]["create_cogwheel"] = {
        "textures": "textures/entity/create/cogwheel"
    }
    blocks_data["create:cogwheel"] = {
        "textures": "create_cogwheel",
        "sound": "wood"
    }

    # Sanity check: Distinct neon dirt texture to verify resource pack delivery
    terrain_data["texture_data"]["dirt"] = {
        "textures": "textures/blocks/dirt"
    }

    (RP_DIR / "textures" / "terrain_texture.json").write_text(json.dumps(terrain_data, indent=2), encoding="utf-8")
    (RP_DIR / "blocks.json").write_text(json.dumps(blocks_data, indent=2), encoding="utf-8")

    # Repack into geyser packs
    pack_zip = GEYSER_DIR / "packs" / "CreateKineticPack.zip"
    pack_zip.parent.mkdir(parents=True, exist_ok=True)
    if pack_zip.exists():
        pack_zip.unlink()

    with zipfile.ZipFile(pack_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for f in RP_DIR.rglob("*"):
            if f.is_file():
                z.write(f, str(f.relative_to(RP_DIR)).replace("\\", "/"))
    print(f"  + Repacked {pack_zip.name} ({pack_zip.stat().st_size} bytes)")

def step2_generate_extension_source():
    print("[3/4] Generating Geyser extension source...")
    src_dir = EXT_BUILD_DIR / "src" / "com" / "createbridge"
    src_dir.mkdir(parents=True, exist_ok=True)

    block_registrations = []
    for block_id, tex_key, _, java_ids in CASING_BLOCKS:
        fname = block_id.replace("create:", "")
        overrides_code = []
        for jid in java_ids:
            overrides_code.append(f"""
            event.registerOverride(
                JavaBlockState.builder()
                    .identifier("{block_id}")
                    .javaId({jid})
                    .stateGroupId({jid})
                    .build(),
                data.defaultBlockState()
            );""")
        overrides_str = "".join(overrides_code)
        block_registrations.append(f"""
        // {block_id}
        {{
            CustomBlockComponents comps = CustomBlockComponents.builder()
                .unitCube(true)
                .materialInstance("*", MaterialInstance.builder().texture("{tex_key}").build())
                .build();
            NonVanillaCustomBlockData data = NonVanillaCustomBlockData.builder()
                .namespace("create")
                .name("{fname}")
                .components(comps)
                .build();
            event.register(data);
{overrides_str}
        }}""")

    java_code = f"""package com.createbridge;

import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;

public class CreateBridgeExtension implements Extension {{
    @Subscribe
    public void onDefineCustomBlocks(GeyserDefineCustomBlocksEvent event) {{
        System.out.println("[CreateBridge] Registering Create blocks in Geyser...");
        {"".join(block_registrations)}
        System.out.println("[CreateBridge] Successfully registered " + {len(CASING_BLOCKS)} + " Create blocks with Java ID overrides!");
    }}
}}
"""
    (src_dir / "CreateBridgeExtension.java").write_text(java_code, encoding="utf-8")

    yml_code = """id: createbridge
name: CreateBridge
version: 1.0.0
main: com.createbridge.CreateBridgeExtension
api: 2.11.3
authors:
  - Antigravity
"""
    res_dir = EXT_BUILD_DIR / "resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "extension.yml").write_text(yml_code, encoding="utf-8")
    print("  + Created CreateBridgeExtension.java & extension.yml")

def step3_compile_and_package():
    print("[4/4] Compiling and packaging CreateBridge.jar...")
    classes_dir = EXT_BUILD_DIR / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)

    javac = r"C:\Program Files\Java\jdk-21.0.12\bin\javac.exe"
    jar_bin = r"C:\Program Files\Java\jdk-21.0.12\bin\jar.exe"
    geyser_jar = str(GEYSER_DIR / "Geyser-Standalone.jar")
    src_file = str(EXT_BUILD_DIR / "src" / "com" / "createbridge" / "CreateBridgeExtension.java")

    compile_cmd = [
        javac,
        "-cp", geyser_jar,
        "-d", str(classes_dir),
        src_file
    ]
    res = subprocess.run(compile_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Compilation FAILED:\n{res.stderr}")
        sys.exit(1)
    print("  + Compiled successfully.")

    # Copy extension.yml to classes dir
    (classes_dir / "extension.yml").write_text(
        (EXT_BUILD_DIR / "resources" / "extension.yml").read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    EXT_DIR.mkdir(parents=True, exist_ok=True)
    out_jar = EXT_DIR / "CreateBridge.jar"
    package_cmd = [
        jar_bin, "cf", str(out_jar),
        "-C", str(classes_dir), "."
    ]
    res = subprocess.run(package_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Packaging FAILED:\n{res.stderr}")
        sys.exit(1)
    print(f"  + Generated {out_jar.name} ({out_jar.stat().st_size} bytes)")
    print("=== AUTOMATION RUN COMPLETE ===")

if __name__ == "__main__":
    step1_extract_textures_and_pack()
    step2_generate_extension_source()
    step3_compile_and_package()
