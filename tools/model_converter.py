import os
import sys
import json
import zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"
PACK_ZIP = ROOT / "headless_server" / "geyser" / "packs" / "CreateKineticPack.zip"

def find_model_in_jar(block_name):
    """Searches the Create mod jar for the best matching block model."""
    candidates = [
        f"assets/create/models/block/{block_name}/block.json",
        f"assets/create/models/block/{block_name}.json",
        f"assets/create/models/block/{block_name}/block_single.json",
    ]
    with zipfile.ZipFile(MOD_JAR, "r") as z:
        names = set(z.namelist())
        for c in candidates:
            if c in names:
                return c
        # Fallback search
        for n in names:
            if n.startswith(f"assets/create/models/block/{block_name}") and n.endswith(".json"):
                return n
    return None

def convert_block_geometry(block_name, model_path=None, sound="metal"):
    """
    End-to-end tooling to convert a Java block model into Bedrock geometry,
    stitch textures, update resource pack manifests, and repack CreateKineticPack.zip.
    """
    if model_path is None:
        model_path = find_model_in_jar(block_name)
        if not model_path:
            print(f"Error: Could not locate model for '{block_name}' in {MOD_JAR.name}")
            return False

    geo_id = f"geometry.create.{block_name}"
    tex_key = f"create_{block_name}"
    print(f"[ModelConverter] Converting '{block_name}' from '{model_path}'...")

    with zipfile.ZipFile(MOD_JAR, "r") as z:
        raw_model = z.read(model_path).decode("utf-8")
        model = json.loads(raw_model)

        textures_map = model.get("textures", {})
        tex_images = {}
        for var_name, tex_path in textures_map.items():
            if var_name == "particle":
                continue
            clean_path = tex_path.replace("create:", "assets/create/textures/") + ".png"
            if clean_path in z.namelist():
                tex_images[var_name] = Image.open(z.open(clean_path)).convert("RGBA")
            else:
                print(f"  Warning: texture {clean_path} not found in jar")

    if not tex_images:
        print(f"  Error: No textures resolved for {block_name}")
        return False

    # 1. Stitch Atlas
    num_tex = len(tex_images)
    grid_w = 2 if num_tex > 1 else 1
    grid_h = ((num_tex + 1) // 2) if num_tex > 1 else 1
    atlas_w = grid_w * 16
    atlas_h = max(16, grid_h * 16)

    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    tex_offsets = {}
    idx = 0
    for var_name, img in tex_images.items():
        gx = (idx % grid_w) * 16
        gy = (idx // grid_w) * 16
        atlas.paste(img.resize((16, 16)), (gx, gy))
        tex_offsets[var_name] = (gx, gy)
        idx += 1

    out_tex_file = RP_DIR / "textures" / "blocks" / f"{block_name}.png"
    out_tex_file.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(out_tex_file)
    print(f"  + Generated texture atlas: {out_tex_file.name} ({atlas_w}x{atlas_h})")

    # 2. Build Bedrock Cubes
    bedrock_cubes = []
    for elem in model.get("elements", []):
        f = elem["from"]
        t = elem["to"]

        min_x, max_x = min(f[0], t[0]), max(f[0], t[0])
        min_y, max_y = min(f[1], t[1]), max(f[1], t[1])
        min_z, max_z = min(f[2], t[2]), max(f[2], t[2])

        origin = [round(min_x - 8.0, 3), round(min_y, 3), round(min_z - 8.0, 3)]
        size = [round(max_x - min_x, 3), round(max_y - min_y, 3), round(max_z - min_z, 3)]

        cube_dict = {
            "origin": origin,
            "size": size,
            "uv": {}
        }

        faces = elem.get("faces", {})
        for face_name, face_data in faces.items():
            tex_var = face_data.get("texture", "").replace("#", "")
            off_x, off_y = tex_offsets.get(tex_var, (0, 0))
            raw_uv = face_data.get("uv", [0, 0, 16, 16])

            u_min, u_max = min(raw_uv[0], raw_uv[2]), max(raw_uv[0], raw_uv[2])
            v_min, v_max = min(raw_uv[1], raw_uv[3]), max(raw_uv[1], raw_uv[3])

            bedrock_u = round(off_x + u_min, 3)
            bedrock_v = round(off_y + v_min, 3)
            uv_w = round(u_max - u_min, 3)
            uv_h = round(v_max - v_min, 3)

            cube_dict["uv"][face_name] = {
                "uv": [bedrock_u, bedrock_v],
                "uv_size": [uv_w, uv_h]
            }

        bedrock_cubes.append(cube_dict)

    # 3. Save Bedrock Geometry
    geo_file = RP_DIR / "models" / "blocks" / f"{block_name}.geo.json"
    geo_file.parent.mkdir(parents=True, exist_ok=True)
    geo_json = {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": geo_id,
                    "texture_width": atlas_w,
                    "texture_height": atlas_h,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2,
                    "visible_bounds_offset": [0, 0.5, 0]
                },
                "bones": [
                    {
                        "name": "root",
                        "pivot": [0, 0, 0],
                        "cubes": bedrock_cubes
                    }
                ]
            }
        ]
    }
    with open(geo_file, "w", encoding="utf-8") as f:
        json.dump(geo_json, f, indent=2)
    print(f"  + Generated Bedrock geometry: {geo_file.name}")

    # 4. Update blocks.json
    blocks_file = RP_DIR / "blocks.json"
    blocks_data = json.loads(blocks_file.read_text(encoding="utf-8")) if blocks_file.exists() else {"format_version": "1.20.10"}
    blocks_data[f"create:{block_name}"] = {
        "textures": tex_key,
        "geometry": geo_id,
        "sound": sound
    }
    blocks_file.write_text(json.dumps(blocks_data, indent=2), encoding="utf-8")

    # 5. Update terrain_texture.json
    terrain_file = RP_DIR / "textures" / "terrain_texture.json"
    terrain_data = json.loads(terrain_file.read_text(encoding="utf-8"))
    terrain_data["texture_data"][tex_key] = {
        "textures": f"textures/blocks/{block_name}"
    }
    terrain_file.write_text(json.dumps(terrain_data, indent=2), encoding="utf-8")

    # 6. Update item_texture.json
    item_file = RP_DIR / "textures" / "item_texture.json"
    item_data = json.loads(item_file.read_text(encoding="utf-8"))
    item_data["texture_data"][tex_key] = {
        "textures": f"textures/blocks/{block_name}"
    }
    item_file.write_text(json.dumps(item_data, indent=2), encoding="utf-8")

    # 7. Repack CreateKineticPack.zip
    if PACK_ZIP.exists():
        PACK_ZIP.unlink()
    with zipfile.ZipFile(PACK_ZIP, "w", zipfile.ZIP_DEFLATED) as zout:
        for f in RP_DIR.rglob("*"):
            if f.is_file():
                zout.write(f, str(f.relative_to(RP_DIR)).replace("\\", "/"))
    print(f"  + Repacked CreateKineticPack.zip ({PACK_ZIP.stat().st_size} bytes)")
    print(f"[ModelConverter] Geometry '{block_name}' successfully built and packaged!\n")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/model_converter.py <block_name> [model_path_in_jar]")
        sys.exit(1)
    bname = sys.argv[1]
    mpath = sys.argv[2] if len(sys.argv) > 2 else None
    convert_block_geometry(bname, mpath)
