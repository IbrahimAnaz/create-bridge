import os
import json
import zipfile
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"
DUMP_FILE = ROOT / "headless_server" / "create_registry_dump.json"
OUT_PACK = ROOT / "headless_server" / "geyser" / "packs" / "CreateKineticPack.zip"

with open(DUMP_FILE, "r") as f:
    dump = json.load(f)

items = dump.get("items", {})
print(f"Total Create items: {len(items)}")

out_dir = RP_DIR / "textures" / "items" / "create"
out_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(MOD_JAR, "r") as z:
    all_files = set(z.namelist())
    
    # Map texture names in jar
    tex_files = {n.split("/")[-1].replace(".png", ""): n for n in all_files if n.startswith("assets/create/textures/") and n.endswith(".png")}
    
    def resolve_model_textures(model_path, depth=0):
        if depth > 5 or model_path not in all_files:
            return []
        try:
            m = json.loads(z.read(model_path).decode("utf-8"))
            texs = []
            if "textures" in m:
                for k, v in m["textures"].items():
                    if isinstance(v, str):
                        clean = v.replace("create:", "").replace("minecraft:", "")
                        clean_path = f"assets/create/textures/{clean}.png"
                        if clean_path in all_files:
                            texs.append(clean_path)
                        else:
                            base = clean.split("/")[-1]
                            if base in tex_files:
                                texs.append(tex_files[base])
            if "parent" in m:
                parent = m["parent"].replace("create:", "")
                p_path = f"assets/create/models/{parent}.json"
                texs.extend(resolve_model_textures(p_path, depth + 1))
            return texs
        except Exception:
            return []

    resolved_count = 0
    wrench_count = 0
    
    # Read wrench fallback only if completely impossible to find anything
    default_wrench = z.read("assets/create/textures/item/wrench.png")
    
    for full_id in items.keys():
        name = full_id.replace("create:", "")
        target_png = out_dir / f"{name}.png"
        
        found_data = None
        
        # Priority 1: Direct item texture
        p_item = f"assets/create/textures/item/{name}.png"
        p_block = f"assets/create/textures/block/{name}.png"
        
        if p_item in all_files:
            found_data = z.read(p_item)
        elif p_block in all_files:
            found_data = z.read(p_block)
        else:
            # Priority 2: Model inspection
            m_item = f"assets/create/models/item/{name}.json"
            model_texs = resolve_model_textures(m_item)
            if model_texs:
                found_data = z.read(model_texs[0])
            else:
                # Priority 3: Name matches in textures
                if name in tex_files:
                    found_data = z.read(tex_files[name])
                else:
                    # Strip prefixes/suffixes like _block, _casing, cut_
                    simple_name = name.replace("cut_", "").replace("_block", "").replace("polished_", "")
                    if simple_name in tex_files:
                        found_data = z.read(tex_files[simple_name])
                    else:
                        # Search any texture starting with name
                        candidates = [n for n in all_files if n.startswith("assets/create/textures/") and n.endswith(".png") and name in n]
                        if candidates:
                            found_data = z.read(candidates[0])
        
        if found_data:
            with open(target_png, "wb") as f_out:
                f_out.write(found_data)
            resolved_count += 1
        else:
            with open(target_png, "wb") as f_out:
                f_out.write(default_wrench)
            wrench_count += 1

print(f"Properly resolved {resolved_count} textures! Fallback wrench used: {wrench_count}")

# Update item_texture.json
item_tex_json_path = RP_DIR / "textures" / "item_texture.json"
texture_dict = {}
for full_id in items.keys():
    name = full_id.replace("create:", "")
    texture_dict[f"create_{name}"] = {
        "textures": f"textures/items/create/{name}"
    }

item_tex_data = {
    "resource_pack_name": "create_cogwheel_rp",
    "texture_name": "atlas.items",
    "texture_data": texture_dict
}

with open(item_tex_json_path, "w", encoding="utf-8") as f:
    json.dump(item_tex_data, f, indent=2)

print("Updated item_texture.json with all entries.")

# Repack into CreateKineticPack.zip
print("Repacking CreateKineticPack.zip...")
with zipfile.ZipFile(OUT_PACK, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
    for root, dirs, files in os.walk(RP_DIR):
        for file in files:
            p = Path(root) / file
            rel_path = p.relative_to(RP_DIR)
            z_out.write(p, str(rel_path).replace("\\", "/"))

print("Finished repacking CreateKineticPack.zip!")
