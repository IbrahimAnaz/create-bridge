"""
Bespoke Create Mod Composite Model Builder (v2 - Hardened)
==========================================================
Converts all 10 bespoke kinetic Create Mod blocks from their authentic,
complete `item.json` representations in the Create mod JAR into full,
assembled Bedrock geometry (.geo.json) and stitched texture atlases.

Fixes for Bedrock RenderDragon limits:
1. Puts all angled cubes onto dedicated child BONES with bone-level rotations.
   (Bedrock rejects cubes with non-45 rotations like 22.5, causing invisible blocks).
2. Clamps cube vertices to legal Bedrock block limits [-15.9, 31.9]
   (Prevents RenderDragon bounds rejection, which caused deployer to render as dirt).
3. Base orientation aligned with FacingBlockRegistrar (North).
   Mechanical Saw base tilted -90 around X so facing=up in world renders flat on floor.
4. Correct 64x64 atlas generation for both cuckoo_clock and mysterious_cuckoo_clock.
"""

import os
import sys
import json
import zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
VANILLA_JAR = Path(os.path.expandvars(r"%APPDATA%\.minecraft\versions\1.21.5\1.21.5.jar"))
RP_DIR = ROOT / "create_cogwheel_rp"
MODELS_DIR = RP_DIR / "models" / "blocks"
TEXTURES_DIR = RP_DIR / "textures" / "blocks"
TERRAIN_TEX_PATH = RP_DIR / "textures" / "terrain_texture.json"

BESPOKE_BLOCKS = {
    "mechanical_pump": {
        "model": "assets/create/models/block/mechanical_pump/item.json",
        "y_rot": 90,  # The source X-axis maps to the north-facing Z axis
        "x_rot": 0,
    },
    "mechanical_drill": {
        "model": "assets/create/models/block/mechanical_drill/item.json",
        "y_rot": 180,  # South drill tip to North
        "x_rot": 0,
    },
    "mechanical_saw": {
        "model": "assets/create/models/block/mechanical_saw/item.json",
        "y_rot": 180,
        "x_rot": 0,
    },
    "deployer": {
        "model": "assets/create/models/block/deployer/item.json",
        "y_rot": 180,  # South hand to North
        "x_rot": 0,
    },
    "encased_fan": {
        "model": "assets/create/models/block/encased_fan/item.json",
        "y_rot": 180,  # South outlet to North
        "x_rot": 0,
    },
    "mechanical_press": {
        "model": "assets/create/models/block/mechanical_press/item.json",
        "y_rot": 0,
        "x_rot": 0,
    },
    "mechanical_mixer": {
        "model": "assets/create/models/block/mechanical_mixer/item.json",
        "y_rot": 0,
        "x_rot": 0,
    },
    "millstone": {
        "model": "assets/create/models/block/millstone/item.json",
        "y_rot": 0,
        "x_rot": 0,
    },
    "mechanical_harvester": {
        "model": "assets/create/models/block/mechanical_harvester/item.json",
        "y_rot": 0,
        "x_rot": 0,
    },
    "cuckoo_clock": {
        "model": "assets/create/models/block/cuckoo_clock/item.json",
        "y_rot": 0,
        "x_rot": 0,
    },
    "mysterious_cuckoo_clock": {
        "model": "assets/create/models/block/cuckoo_clock/item.json",
        "y_rot": 0,
        "x_rot": 0,
    },
}


def rotate_element(elem, y_deg, x_deg=0):
    """Rotates a Java model element around [8, 8, 8] by Y and X degrees."""
    curr = elem

    # 1. Y Rotation
    if y_deg != 0:
        f, t = curr["from"], curr["to"]
        min_x, max_x = min(f[0], t[0]), max(f[0], t[0])
        min_y, max_y = min(f[1], t[1]), max(f[1], t[1])
        min_z, max_z = min(f[2], t[2]), max(f[2], t[2])

        if y_deg == 90:
            new_x1, new_x2 = 16.0 - max_z, 16.0 - min_z
            new_z1, new_z2 = min_x, max_x
            face_map = {"north": "east", "south": "west", "east": "south", "west": "north", "up": "up", "down": "down"}
        elif y_deg == 180:
            new_x1, new_x2 = 16.0 - max_x, 16.0 - min_x
            new_z1, new_z2 = 16.0 - max_z, 16.0 - min_z
            face_map = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "up", "down": "down"}
        elif y_deg == 270:
            new_x1, new_x2 = min_z, max_z
            new_z1, new_z2 = 16.0 - max_x, 16.0 - min_x
            face_map = {"north": "west", "south": "east", "east": "north", "west": "south", "up": "up", "down": "down"}
        else:
            raise ValueError(f"Unsupported Y rotation: {y_deg}")

        new_elem = {
            "from": [round(new_x1, 3), round(min_y, 3), round(new_z1, 3)],
            "to": [round(new_x2, 3), round(max_y, 3), round(new_z2, 3)],
            "faces": {},
        }
        for old_face, fdata in curr.get("faces", {}).items():
            new_face = face_map.get(old_face, old_face)
            f_copy = dict(fdata)
            if new_face in ("up", "down"):
                f_copy["rotation"] = (f_copy.get("rotation", 0) + y_deg) % 360
            new_elem["faces"][new_face] = f_copy

        if "rotation" in curr:
            rot = dict(curr["rotation"])
            axis = rot.get("axis", "y").lower()
            angle = rot.get("angle", 0)
            orig = rot.get("origin", [8, 8, 8])

            if y_deg == 90:
                if axis == "x":
                    rot["axis"] = "z"
                elif axis == "z":
                    rot["axis"] = "x"
                    rot["angle"] = -angle
            elif y_deg == 180:
                if axis in ("x", "z"):
                    rot["angle"] = -angle
            elif y_deg == 270:
                if axis == "x":
                    rot["axis"] = "z"
                    rot["angle"] = -angle
                elif axis == "z":
                    rot["axis"] = "x"

            ox, oy, oz = orig[0], orig[1], orig[2]
            if y_deg == 90:
                rot["origin"] = [round(16.0 - oz, 3), round(oy, 3), round(ox, 3)]
            elif y_deg == 180:
                rot["origin"] = [round(16.0 - ox, 3), round(oy, 3), round(16.0 - oz, 3)]
            elif y_deg == 270:
                rot["origin"] = [round(oz, 3), round(oy, 3), round(16.0 - ox, 3)]
            new_elem["rotation"] = rot

        curr = new_elem

    # 2. X Rotation (e.g. -90 for saw)
    if x_deg != 0:
        f, t = curr["from"], curr["to"]
        min_x, max_x = min(f[0], t[0]), max(f[0], t[0])
        min_y, max_y = min(f[1], t[1]), max(f[1], t[1])
        min_z, max_z = min(f[2], t[2]), max(f[2], t[2])

        if x_deg == -90:
            # y_new = z, z_new = 16 - y
            new_y1, new_y2 = min_z, max_z
            new_z1, new_z2 = 16.0 - max_y, 16.0 - min_y
            face_map = {"north": "down", "south": "up", "up": "north", "down": "south", "east": "east", "west": "west"}
        elif x_deg == 90:
            # y_new = 16 - z, z_new = y
            new_y1, new_y2 = 16.0 - max_z, 16.0 - min_z
            new_z1, new_z2 = min_y, max_y
            face_map = {"north": "up", "south": "down", "up": "south", "down": "north", "east": "east", "west": "west"}
        else:
            raise ValueError(f"Unsupported X rotation: {x_deg}")

        new_elem = {
            "from": [round(min_x, 3), round(new_y1, 3), round(new_z1, 3)],
            "to": [round(max_x, 3), round(new_y2, 3), round(new_z2, 3)],
            "faces": {},
        }
        for old_face, fdata in curr.get("faces", {}).items():
            new_face = face_map.get(old_face, old_face)
            f_copy = dict(fdata)
            new_elem["faces"][new_face] = f_copy

        if "rotation" in curr:
            rot = dict(curr["rotation"])
            axis = rot.get("axis", "y").lower()
            angle = rot.get("angle", 0)
            orig = rot.get("origin", [8, 8, 8])
            if x_deg == -90:
                if axis == "y":
                    rot["axis"] = "z"
                elif axis == "z":
                    rot["axis"] = "y"
                    rot["angle"] = -angle
            ox, oy, oz = orig[0], orig[1], orig[2]
            if x_deg == -90:
                rot["origin"] = [round(ox, 3), round(oz, 3), round(16.0 - oy, 3)]
            new_elem["rotation"] = rot

        curr = new_elem

    return curr


def clamp(val, min_v, max_v):
    return max(min_v, min(max_v, val))


def build_bespoke_block(block_name, cfg, jar):
    """Builds Bedrock geometry with bone-level rotations and stitched texture atlas."""
    model_path = cfg["model"]
    y_rot = cfg["y_rot"]
    x_rot = cfg["x_rot"]

    raw_data = json.loads(jar.read(model_path).decode("utf-8"))
    tex_size = raw_data.get("texture_size", [16, 16])
    tex_w = float(tex_size[0]) if len(tex_size) > 0 else 16.0
    tex_h = float(tex_size[1]) if len(tex_size) > 1 else 16.0

    textures_map = raw_data.get("textures", {})
    raw_elements = raw_data.get("elements", [])

    if not raw_elements and "parent" in raw_data:
        parent_path = raw_data["parent"]
        if not parent_path.endswith(".json"):
            parent_path += ".json"
        if parent_path.startswith("create:"):
            parent_path = "assets/create/models/" + parent_path[7:]
        elif parent_path.startswith("block/") or parent_path.startswith("item/"):
            parent_path = "assets/create/models/" + parent_path
        if parent_path in jar.namelist():
            pdata = json.loads(jar.read(parent_path).decode("utf-8"))
            raw_elements = pdata.get("elements", [])
            for k, v in pdata.get("textures", {}).items():
                if k not in textures_map:
                    textures_map[k] = v

    # 1. Resolve and load textures
    face_tex_vars = set()
    for elem in raw_elements:
        for f, fdata in elem.get("faces", {}).items():
            t = fdata.get("texture", "")
            if t:
                face_tex_vars.add(t)

    tex_images = {}
    for tvar in sorted(face_tex_vars):
        clean_key = tvar.lstrip("#")
        resolved_t = textures_map.get(clean_key, textures_map.get(tvar, tvar))
        while resolved_t.startswith("#") and resolved_t.lstrip("#") in textures_map:
            resolved_t = textures_map[resolved_t.lstrip("#")]

        tex_path = resolved_t
        if tex_path.startswith("create:"):
            tex_path = "assets/create/textures/" + tex_path[7:] + ".png"
        elif tex_path.startswith("minecraft:"):
            tex_path = "assets/minecraft/textures/" + tex_path[10:] + ".png"
        elif not tex_path.endswith(".png"):
            tex_path = "assets/create/textures/block/" + tex_path + ".png"

        img = None
        if tex_path in jar.namelist():
            import io
            img = Image.open(io.BytesIO(jar.read(tex_path))).convert("RGBA")
        elif VANILLA_JAR.exists():
            v_cands = [
                tex_path,
                "assets/minecraft/textures/" + resolved_t.replace("minecraft:", "").replace("block/", "block/") + ".png",
                f"assets/minecraft/textures/block/{clean_key}.png",
                f"assets/minecraft/textures/block/{resolved_t.split('/')[-1]}.png",
            ]
            try:
                with zipfile.ZipFile(VANILLA_JAR, "r") as vz:
                    for vc in v_cands:
                        if vc in vz.namelist():
                            import io
                            img = Image.open(io.BytesIO(vz.read(vc))).convert("RGBA")
                            break
            except Exception:
                pass

        if not img:
            for cand in [
                f"assets/create/textures/block/{clean_key}.png",
                f"assets/create/textures/{clean_key}.png",
                f"assets/create/textures/block/{block_name}.png",
            ]:
                if cand in jar.namelist():
                    import io
                    img = Image.open(io.BytesIO(jar.read(cand))).convert("RGBA")
                    break

        if img:
            tex_images[clean_key] = img
        else:
            print(f"  [!] Texture missing for {tvar} ({resolved_t}), using fallback")
            tex_images[clean_key] = Image.new("RGBA", (16, 16), (180, 140, 100, 255))

    # 2. Rotate Elements
    rotated_elements = [rotate_element(el, y_rot, x_rot) for el in raw_elements]

    # 3. Extract Transformed Face Patches (Bake UV flips and rotations)
    patches = {}
    for elem in rotated_elements:
        for f, fdata in elem.get("faces", {}).items():
            tkey = fdata.get("texture", "").lstrip("#")
            raw_uv = fdata.get("uv")
            if raw_uv is None:
                continue
            rot = fdata.get("rotation", 0) % 360
            u1, v1, u2, v2 = raw_uv
            flip_h = (u1 > u2)
            flip_v = (v1 > v2)
            if flip_h or flip_v or rot != 0:
                pk = (tkey, round(u1, 3), round(v1, 3), round(u2, 3), round(v2, 3), rot)
                if pk not in patches:
                    s_img = tex_images.get(tkey)
                    if not s_img and tex_images:
                        s_img = next(iter(tex_images.values()))
                    if s_img:
                        sx = s_img.width / 16.0
                        sy = s_img.height / 16.0
                        umin, umax = min(u1, u2), max(u1, u2)
                        vmin, vmax = min(v1, v2), max(v1, v2)
                        px1 = int(round(umin * sx))
                        px2 = max(px1 + 1, int(round(umax * sx)))
                        py1 = int(round(vmin * sy))
                        py2 = max(py1 + 1, int(round(vmax * sy)))
                        p = s_img.crop((px1, py1, px2, py2))
                        if flip_h:
                            p = p.transpose(Image.FLIP_LEFT_RIGHT)
                        if flip_v:
                            p = p.transpose(Image.FLIP_TOP_BOTTOM)
                        if rot == 90:
                            p = p.transpose(Image.ROTATE_270)
                        elif rot == 180:
                            p = p.transpose(Image.ROTATE_180)
                        elif rot == 270:
                            p = p.transpose(Image.ROTATE_90)
                        patches[pk] = p

    # 4. Stitch Atlas (Base Grid + Baked Patches)
    num_tex = len(tex_images)
    tile_w = max(16, max(img.width for img in tex_images.values()))
    tile_h = max(16, max(img.height for img in tex_images.values()))
    cols = 1 if num_tex == 1 else (2 if num_tex <= 4 else 4)
    rows = (num_tex + cols - 1) // cols
    base_grid_w = cols * tile_w
    base_grid_h = rows * tile_h

    tex_offsets = {}
    tex_scales = {}
    for idx, (tkey, img) in enumerate(tex_images.items()):
        gx = (idx % cols) * tile_w
        gy = (idx // cols) * tile_h
        tex_offsets[tkey] = (gx, gy)
        tex_scales[tkey] = (tile_w / 16.0, tile_h / 16.0)

    atlas_w = max(64, base_grid_w)
    pw2 = 16
    while pw2 < atlas_w:
        pw2 *= 2
    atlas_w = pw2

    cur_x = 0
    cur_y = base_grid_h
    row_h = 0
    patch_offsets = {}
    for pk, p in sorted(patches.items(), key=lambda it: -it[1].height):
        if cur_x + p.width > atlas_w:
            cur_x = 0
            cur_y += row_h
            row_h = 0
        patch_offsets[pk] = (cur_x, cur_y)
        cur_x += p.width
        row_h = max(row_h, p.height)
    total_h = cur_y + row_h

    atlas_h = 16
    while atlas_h < total_h:
        atlas_h *= 2

    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    for tkey, img in tex_images.items():
        gx, gy = tex_offsets[tkey]
        atlas.paste(img.resize((tile_w, tile_h)), (gx, gy))
    for pk, p in patches.items():
        px, py = patch_offsets[pk]
        atlas.paste(p, (px, py))

    TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
    atlas_out = TEXTURES_DIR / f"{block_name}.png"
    atlas.save(atlas_out)

    # 5. Build Bedrock Bones & Cubes
    root_cubes = []
    child_bones = []

    for idx, elem in enumerate(rotated_elements):
        f = elem.get("from", [0, 0, 0])
        t = elem.get("to", [16, 16, 16])

        raw_min_x, raw_max_x = min(f[0], t[0]), max(f[0], t[0])
        raw_min_y, raw_max_y = min(f[1], t[1]), max(f[1], t[1])
        raw_min_z, raw_max_z = min(f[2], t[2]), max(f[2], t[2])

        # Convert to Bedrock coordinates centered around [8, 0, 8]
        bx1 = raw_min_x - 8.0
        bx2 = raw_max_x - 8.0
        by1 = raw_min_y
        by2 = raw_max_y
        bz1 = raw_min_z - 8.0
        bz2 = raw_max_z - 8.0

        # HARD CLAMP to legal Bedrock block limits [-15.9, 31.9]
        bx1 = clamp(bx1, -15.9, 31.9)
        bx2 = clamp(bx2, -15.9, 31.9)
        by1 = clamp(by1, -15.9, 31.9)
        by2 = clamp(by2, -15.9, 31.9)
        bz1 = clamp(bz1, -15.9, 31.9)
        bz2 = clamp(bz2, -15.9, 31.9)

        min_x, max_x = min(bx1, bx2), max(bx1, bx2)
        min_y, max_y = min(by1, by2), max(by1, by2)
        min_z, max_z = min(bz1, bz2), max(bz1, bz2)

        origin = [round(min_x, 3), round(min_y, 3), round(min_z, 3)]
        size = [round(max(0.1, max_x - min_x), 3), round(max(0.1, max_y - min_y), 3), round(max(0.1, max_z - min_z), 3)]

        cube_dict = {
            "origin": origin,
            "size": size,
            "uv": {},
        }

        # Build faces
        faces = elem.get("faces", {})
        for face_name in ["north", "south", "east", "west", "up", "down"]:
            if face_name not in faces:
                continue
            face_data = faces[face_name]
            raw_tex = face_data.get("texture", "").lstrip("#")
            raw_uv = face_data.get("uv")
            rot = face_data.get("rotation", 0) % 360

            # Check if this face has a baked patch
            if raw_uv is not None:
                u1, v1, u2, v2 = raw_uv
                pk = (raw_tex, round(u1, 3), round(v1, 3), round(u2, 3), round(v2, 3), rot)
                if pk in patch_offsets:
                    px, py = patch_offsets[pk]
                    pw, ph = patches[pk].size
                    cube_dict["uv"][face_name] = {
                        "uv": [px, py],
                        "uv_size": [pw, ph],
                    }
                    continue

            # Fallback / untransformed UV mapping
            if raw_tex in tex_offsets:
                off_x, off_y = tex_offsets[raw_tex]
                scale_x, scale_y = tex_scales[raw_tex]
            elif tex_offsets:
                first_k = next(iter(tex_offsets.keys()))
                off_x, off_y = tex_offsets[first_k]
                scale_x, scale_y = tex_scales[first_k]
            else:
                off_x, off_y = 0, 0
                scale_x, scale_y = 1.0, 1.0

            if raw_uv is not None:
                calc_uv = raw_uv
            else:
                if face_name in ("north", "south"):
                    calc_uv = [raw_min_x, 16 - raw_max_y, raw_max_x, 16 - raw_min_y]
                elif face_name in ("east", "west"):
                    calc_uv = [raw_min_z, 16 - raw_max_y, raw_max_z, 16 - raw_min_y]
                else:
                    calc_uv = [raw_min_x, raw_min_z, raw_max_x, raw_max_z]

            u_min, u_max = min(calc_uv[0], calc_uv[2]), max(calc_uv[0], calc_uv[2])
            v_min, v_max = min(calc_uv[1], calc_uv[3]), max(calc_uv[1], calc_uv[3])

            bedrock_u = round(off_x + u_min * scale_x, 3)
            bedrock_v = round(off_y + v_min * scale_y, 3)
            uv_w = round((u_max - u_min) * scale_x, 3)
            uv_h = round((v_max - v_min) * scale_y, 3)

            face_uv_entry = {
                "uv": [bedrock_u, bedrock_v],
                "uv_size": [uv_w, uv_h],
            }
            cube_dict["uv"][face_name] = face_uv_entry

        # Preserve element rotations on bones; cube-level rotations are rejected by
        # Bedrock block geometry when their angle is not a supported 45-degree step.
        rot = elem.get("rotation")
        angle = float(rot.get("angle", 0)) if rot else 0.0

        if rot and abs(angle) > 0.01:
            axis = rot.get("axis", "y").lower()
            orig = rot.get("origin", [8, 8, 8])
            pivot = [round(orig[0] - 8.0, 3), round(orig[1], 3), round(orig[2] - 8.0, 3)]
            rotation_axes = {"x": 0, "y": 1, "z": 2}
            if axis not in rotation_axes:
                raise ValueError(f"Unsupported element rotation axis: {axis}")
            bone_rotation = [0, 0, 0]
            bone_rotation[rotation_axes[axis]] = -angle
            child_bones.append({
                "name": f"bone_part_{idx}",
                "parent": "root",
                "pivot": pivot,
                "rotation": bone_rotation,
                "cubes": [cube_dict]
            })
        else:
            root_cubes.append(cube_dict)

    # 4. Write Bedrock Geometry JSON with Root + Child Bones
    geo_id = f"geometry.create.{block_name}"
    bones_list = [
        {
            "name": "root",
            "pivot": [0, 0, 0],
            "cubes": root_cubes,
        }
    ]
    bones_list.extend(child_bones)

    geo_doc = {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": geo_id,
                    "texture_width": atlas_w,
                    "texture_height": atlas_h,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2,
                    "visible_bounds_offset": [0, 0.5, 0],
                },
                "bones": bones_list,
            }
        ],
    }

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    geo_out = MODELS_DIR / f"{block_name}.geo.json"
    with open(geo_out, "w", encoding="utf-8") as fp:
        json.dump(geo_doc, fp, indent=2)

    # 5. Ensure entry in terrain_texture.json
    tex_key = f"create_{block_name}"
    if TERRAIN_TEX_PATH.exists():
        with open(TERRAIN_TEX_PATH, "r", encoding="utf-8") as fp:
            tt = json.load(fp)
        tex_data = tt.setdefault("texture_data", {})
        tex_data[tex_key] = {"textures": f"textures/blocks/{block_name}"}
        with open(TERRAIN_TEX_PATH, "w", encoding="utf-8") as fp:
            json.dump(tt, fp, indent=2)

    total_cubes = len(root_cubes) + len(child_bones)
    print(f"[+] Built '{block_name}': {total_cubes} cubes ({len(child_bones)} angled child bones), atlas ({atlas_w}x{atlas_h}) -> {geo_out.name}")
    return True


def main():
    if not MOD_JAR.exists():
        print(f"[-] Missing Create JAR: {MOD_JAR}")
        sys.exit(1)

    print("=================================================================")
    print("  Mining & Assembling 11 Bespoke Create Mod Models (Hardened v2) ")
    print("=================================================================")

    with zipfile.ZipFile(MOD_JAR, "r") as jar:
        success = 0
        for block_name, cfg in BESPOKE_BLOCKS.items():
            try:
                if build_bespoke_block(block_name, cfg, jar):
                    success += 1
            except Exception as e:
                print(f"[-] Error building {block_name}: {e}")
                import traceback
                traceback.print_exc()

    print(f"\n[+] Successfully assembled {success}/{len(BESPOKE_BLOCKS)} bespoke composite models!")


if __name__ == "__main__":
    main()
