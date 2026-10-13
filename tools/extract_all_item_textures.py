import os
import json
import zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"
DUMP_FILE = ROOT / "headless_server" / "create_registry_dump.json"

with open(DUMP_FILE, "r") as f:
    dump = json.load(f)

items = dump.get("items", {})
print(f"Total items in Create: {len(items)}")

out_dir = RP_DIR / "textures" / "items" / "create"
out_dir.mkdir(parents=True, exist_ok=True)

item_tex_json_path = RP_DIR / "textures" / "item_texture.json"
if item_tex_json_path.exists():
    with open(item_tex_json_path, "r", encoding="utf-8") as f:
        item_tex_data = json.load(f)
else:
    item_tex_data = {
        "resource_pack_name": "create_cogwheel_rp",
        "texture_name": "atlas.items",
        "texture_data": {}
    }

texture_dict = item_tex_data.setdefault("texture_data", {})

fallback_img = Image.new("RGBA", (16, 16), (128, 128, 128, 255))
if (out_dir / "wrench.png").exists():
    fallback_img = Image.open(out_dir / "wrench.png")

with zipfile.ZipFile(MOD_JAR, "r") as z:
    jar_names = set(z.namelist())
    
    extracted = 0
    resolved = 0
    
    for full_id in items.keys():
        name = full_id.replace("create:", "")
        tex_key = f"create_{name}"
        target_png = out_dir / f"{name}.png"
        
        # Check if already present on disk
        if not target_png.exists():
            # Try 1: assets/create/textures/item/{name}.png
            p1 = f"assets/create/textures/item/{name}.png"
            # Try 2: assets/create/textures/block/{name}.png
            p2 = f"assets/create/textures/block/{name}.png"
            # Try 3: search jar for textures/item/{name}
            p3 = f"assets/create/textures/item/{name.replace('_block', '')}.png"
            
            found_path = None
            if p1 in jar_names:
                found_path = p1
            elif p2 in jar_names:
                found_path = p2
            elif p3 in jar_names:
                found_path = p3
            else:
                # Search by prefix or model
                for jn in jar_names:
                    if jn.startswith(f"assets/create/textures/item/{name}") and jn.endswith(".png"):
                        found_path = jn
                        break
                if not found_path:
                    for jn in jar_names:
                        if jn.startswith(f"assets/create/textures/block/{name}") and jn.endswith(".png"):
                            found_path = jn
                            break
            
            if found_path:
                with z.open(found_path) as src, open(target_png, "wb") as dst:
                    dst.write(src.read())
                extracted += 1
            else:
                # Use fallback image so Bedrock never errors
                fallback_img.save(target_png)
                extracted += 1

        # Register in item_texture.json
        texture_dict[tex_key] = {
            "textures": f"textures/items/create/{name}"
        }
        resolved += 1

with open(item_tex_json_path, "w", encoding="utf-8") as f:
    json.dump(item_tex_data, f, indent=2)

print(f"Extracted/saved {extracted} textures.")
print(f"Registered {resolved} items in item_texture.json (total now: {len(texture_dict)}).")
