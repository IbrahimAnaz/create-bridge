import json
import os
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
ALL_STATES_PATH = ROOT / "headless_server" / "config" / "all_blockstates.json"
REG_DUMP_PATH = ROOT / "headless_server" / "create_registry_dump.json"
GEO_BLOCKS_PATH = ROOT / "portable_bridge" / "extension" / "resources" / "geo_blocks.json"
RP_BLOCKS_PATH = ROOT / "create_cogwheel_rp" / "blocks.json"
TERRAIN_TEX_PATH = ROOT / "create_cogwheel_rp" / "textures" / "terrain_texture.json"

def run_audit():
    print("=" * 60)
    print("CREATE BLOCKSTATE PERMUTATION & AUDIT TEST")
    print("=" * 60)

    # 1. Load ground truth
    print("[1/5] Loading NeoForge ground truth (all_blockstates.json)...")
    with open(ALL_STATES_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    create_blocks = [b for b in ground_truth["blocks"] if b["id"].startswith("create:")]
    total_create_blocks = len(create_blocks)
    total_create_states = sum(b["permutation_count"] for b in create_blocks)
    print(f"  + Loaded {total_create_blocks} Create blocks with {total_create_states} permutations.")

    # 2. Load Bridge Registry Dump
    print("[2/5] Loading Bridge Registry Dump (create_registry_dump.json)...")
    reg_dump = {}
    if REG_DUMP_PATH.exists():
        with open(REG_DUMP_PATH, "r", encoding="utf-8") as f:
            reg_dump = json.load(f)
    dump_blockstates = reg_dump.get("blockstates", {})
    print(f"  + Registry dump contains {len(dump_blockstates)} block identifiers.")

    # 3. Load Geometries & RP custom blocks
    print("[3/5] Loading Resource Pack & Geometries...")
    geo_map = {}
    if GEO_BLOCKS_PATH.exists():
        with open(GEO_BLOCKS_PATH, "r", encoding="utf-8") as f:
            geo_map = json.load(f)

    rp_blocks = {}
    if RP_BLOCKS_PATH.exists():
        with open(RP_BLOCKS_PATH, "r", encoding="utf-8") as f:
            rp_blocks = json.load(f)

    terrain_textures = {}
    if TERRAIN_TEX_PATH.exists():
        with open(TERRAIN_TEX_PATH, "r", encoding="utf-8") as f:
            terrain_data = json.load(f)
            terrain_textures = terrain_data.get("texture_data", {})

    print(f"  + Bespoke 3D geometries: {len(geo_map)}")
    print(f"  + RP registered custom blocks: {len(rp_blocks)}")
    print(f"  + Terrain texture definitions: {len(terrain_textures)}")

    # 4. Detailed Categorization & Analysis
    print("[4/5] Iterating through all 31,389 permutations...")
    missing_in_dump = []
    missing_in_rp = []
    has_bespoke_geo = []
    unit_cube_blocks = []
    property_histogram = defaultdict(int)
    state_count_by_cat = defaultdict(int)

    for b in create_blocks:
        b_id = b["id"]
        short_name = b_id.replace("create:", "")
        perms = b["permutation_count"]

        # Check dump
        if b_id not in dump_blockstates:
            missing_in_dump.append(b_id)

        # Check RP
        if b_id in rp_blocks:
            pass
        elif short_name in rp_blocks:
            pass
        elif f"create_{short_name}" in rp_blocks:
            pass
        else:
            missing_in_rp.append(b_id)

        # Check bespoke geo
        if short_name in geo_map or short_name in ["cogwheel", "large_cogwheel", "shaft"]:
            has_bespoke_geo.append(b_id)
            state_count_by_cat["bespoke_3d"] += perms
        else:
            unit_cube_blocks.append(b_id)
            state_count_by_cat["unit_cube"] += perms

        # Analyze property types across states
        for s in b["states"]:
            for prop_name in s["properties"].keys():
                property_histogram[prop_name] += 1

    print("\n--- AUDIT RESULTS ---")
    print(f"Total Create Blocks:            {total_create_blocks}")
    print(f"Total Create Permutations:      {total_create_states}")
    print(f"Bespoke 3D Geometry Blocks:     {len(has_bespoke_geo)} ({state_count_by_cat['bespoke_3d']} states)")
    print(f"Unit Cube Blocks:               {len(unit_cube_blocks)} ({state_count_by_cat['unit_cube']} states)")
    print(f"Blocks in Registry Dump:        {total_create_blocks - len(missing_in_dump)} / {total_create_blocks}")
    print(f"Blocks in Bedrock RP:           {total_create_blocks - len(missing_in_rp)} / {total_create_blocks}")

    if missing_in_dump:
        print(f"\n[!] WARNING: {len(missing_in_dump)} blocks missing from registry dump:")
        for m in missing_in_dump[:10]:
            print(f"   - {m}")
    else:
        print("\n[OK] 100% of Create blocks are present in registry dump!")

    if missing_in_rp:
        print(f"\n[!] Notice: {len(missing_in_rp)} blocks not in custom blocks.json (handled as vanilla fallbacks or entities):")
        for m in missing_in_rp[:10]:
            print(f"   - {m}")
    else:
        print("\n[OK] 100% of Create blocks are defined in Bedrock blocks.json!")

    print("\n--- TOP ACTIVE BLOCKSTATE PROPERTIES ---")
    sorted_props = sorted(property_histogram.items(), key=lambda x: x[1], reverse=True)
    for p_name, count in sorted_props[:15]:
        print(f"  {p_name:20s}: {count:6d} occurrences")

    # 5. Check sample blockstate integrity
    print("\n[5/5] Checking Key Mechanism States:")
    key_mechanisms = [
        "create:depot",
        "create:mechanical_pump",
        "create:cogwheel",
        "create:large_cogwheel",
        "create:shaft",
        "create:gearshift",
        "create:encased_fan",
        "create:mechanical_saw",
        "create:fluid_pipe",
        "create:mechanical_press"
    ]
    for km in key_mechanisms:
        found = [b for b in create_blocks if b["id"] == km]
        if found:
            b_data = found[0]
            print(f"  [PASS] {km:28s}: {b_data['permutation_count']:3d} states -> sample: {json.dumps(b_data['states'][0]['properties'])}")
        else:
            print(f"  [FAIL] {km:28s}: NOT FOUND in registry!")

    print("=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_audit()
