import os
import json
import zipfile
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORLD_DIR = os.path.join(BASE_DIR, "create_test_world_pkg")
RP_DIR = os.path.join(BASE_DIR, "create_cogwheel_rp")
BP_DIR = os.path.join(BASE_DIR, "create_cogwheel_bp")

RP_UUID = "a8b023e1-ac8a-41e0-a933-f3011f2bb75c"
BP_UUID = "8392280e-c392-4924-89df-754b48cc4ada"

def build_world(title, filename):
    if os.path.exists(WORLD_DIR):
        shutil.rmtree(WORLD_DIR)
    os.makedirs(WORLD_DIR, exist_ok=True)
    
    # 1. levelname.txt
    with open(os.path.join(WORLD_DIR, "levelname.txt"), "w", encoding="utf-8") as f:
        f.write(title)

    # 2. world_resource_packs.json
    wrp = [
        {
            "pack_id": RP_UUID,
            "version": [2, 0, 0]
        }
    ]
    with open(os.path.join(WORLD_DIR, "world_resource_packs.json"), "w") as f:
        json.dump(wrp, f, indent=2)

    # 3. world_behavior_packs.json
    wbp = [
        {
            "pack_id": BP_UUID,
            "version": [2, 0, 0]
        }
    ]
    with open(os.path.join(WORLD_DIR, "world_behavior_packs.json"), "w") as f:
        json.dump(wbp, f, indent=2)

    # 4. Embed resource_packs and behavior_packs into the world folder
    world_rp = os.path.join(WORLD_DIR, "resource_packs", "create_cogwheel_rp")
    world_bp = os.path.join(WORLD_DIR, "behavior_packs", "create_cogwheel_bp")
    os.makedirs(world_rp, exist_ok=True)
    os.makedirs(world_bp, exist_ok=True)

    for root, dirs, files in os.walk(RP_DIR):
        for file in files:
            src = os.path.join(root, file)
            rel = os.path.relpath(src, RP_DIR)
            dst = os.path.join(world_rp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, "rb") as sf, open(dst, "wb") as df:
                df.write(sf.read())

    for root, dirs, files in os.walk(BP_DIR):
        for file in files:
            src = os.path.join(root, file)
            rel = os.path.relpath(src, BP_DIR)
            dst = os.path.join(world_bp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, "rb") as sf, open(dst, "wb") as df:
                df.write(sf.read())

    # 5. Zip into mcworld
    mcworld_file = os.path.join(BASE_DIR, filename)
    with zipfile.ZipFile(mcworld_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(WORLD_DIR):
            for file in files:
                src = os.path.join(root, file)
                rel = os.path.relpath(src, WORLD_DIR)
                zf.write(src, rel)
    print(f"Created {mcworld_file}")

if __name__ == "__main__":
    build_world("Create V2 - Fresh Cache & Brakes", "Create_V2_World.mcworld")
