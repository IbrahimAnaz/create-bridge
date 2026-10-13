import json
import zipfile
from pathlib import Path
from PIL import Image
import io

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"

with zipfile.ZipFile(MOD_JAR, "r") as z:
    raw_model = z.read("assets/create/models/block/large_cogwheel.json").decode("utf-8")
    axis_side_img = Image.open(io.BytesIO(z.read("assets/create/textures/block/cogwheel_axis.png"))).convert("RGBA")
    axis_top_img = Image.open(io.BytesIO(z.read("assets/create/textures/block/axis_top.png"))).convert("RGBA")
    gear_img = Image.open(io.BytesIO(z.read("assets/create/textures/block/large_cogwheel.png"))).convert("RGBA")

model = json.loads(raw_model)

# 1. Build 64x64 Atlas
# (0, 0) -> gear_img (32x32)
# (32, 0) -> axis_side_img (16x16)
# (32, 16) -> axis_top_img (16x16)
atlas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
atlas.paste(gear_img, (0, 0))
atlas.paste(axis_side_img, (32, 0))
atlas.paste(axis_top_img, (32, 16))

atlas_path = RP_DIR / "textures" / "blocks" / "large_cogwheel.png"
atlas.save(atlas_path, "PNG")
print(f"Saved 64x64 texture atlas to {atlas_path}")

# 2. Convert Java Model Elements into Bedrock Bones
bones = []
root_cubes = []
rot_groups = {}

for el in model.get("elements", []):
    f = el["from"]
    t = el["to"]
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

    for face_name, face_data in el.get("faces", {}).items():
        tex_ref = face_data.get("texture", "#4")
        raw_uv = face_data.get("uv", [0, 0, 16, 16])
        u_min, u_max = min(raw_uv[0], raw_uv[2]), max(raw_uv[0], raw_uv[2])
        v_min, v_max = min(raw_uv[1], raw_uv[3]), max(raw_uv[1], raw_uv[3])
        u_w = u_max - u_min
        v_h = v_max - v_min

        # Compute atlas pixel coordinates on 64x64
        if tex_ref == "#4":
            # gear texture: 32x32 at (0, 0). Java range 0..16 maps to 0..32
            u_px = u_min * 2.0
            v_px = v_min * 2.0
            w_px = u_w * 2.0
            h_px = v_h * 2.0
        elif tex_ref == "#0":
            # axis side: 16x16 at (32, 0). Java range 0..16 maps to 0..16
            u_px = 32.0 + u_min
            v_px = 0.0 + v_min
            w_px = u_w
            h_px = v_h
        elif tex_ref == "#3":
            # axis top: 16x16 at (32, 16). Java range 0..16 maps to 0..16
            u_px = 32.0 + u_min
            v_px = 16.0 + v_min
            w_px = u_w
            h_px = v_h
        else:
            u_px = u_min * 2.0
            v_px = v_min * 2.0
            w_px = u_w * 2.0
            h_px = v_h * 2.0

        cube_dict["uv"][face_name] = {
            "uv": [round(u_px, 3), round(v_px, 3)],
            "uv_size": [round(w_px, 3), round(h_px, 3)]
        }
        if "rotation" in face_data:
            cube_dict["uv"][face_name]["uv_rotation"] = face_data["rotation"]

    rot = el.get("rotation")
    if rot and rot.get("angle", 0) != 0:
        angle = rot["angle"]
        if angle not in rot_groups:
            rot_groups[angle] = []
        rot_groups[angle].append(cube_dict)
    else:
        root_cubes.append(cube_dict)

bones.append({
    "name": "root",
    "pivot": [0, 8, 0],
    "cubes": root_cubes
})

for angle, cubes in rot_groups.items():
    safe_name = f"gear_rot_{str(angle).replace('.', '_').replace('-', 'neg_')}"
    bones.append({
        "name": safe_name,
        "parent": "root",
        "pivot": [0, 8, 0],
        "rotation": [0, -angle, 0],
        "cubes": cubes
    })

geo_json = {
    "format_version": "1.12.0",
    "minecraft:geometry": [
        {
            "description": {
                "identifier": "geometry.create.large_cogwheel",
                "texture_width": 64,
                "texture_height": 64,
                "visible_bounds_width": 3,
                "visible_bounds_height": 3,
                "visible_bounds_offset": [0, 0.5, 0]
            },
            "bones": bones
        }
    ]
}

out_geo = RP_DIR / "models" / "blocks" / "large_cogwheel.geo.json"
out_geo.write_text(json.dumps(geo_json, indent=2), encoding="utf-8")
print(f"Generated {out_geo} with 64x64 texture atlas UVs and {len(bones)} bones!")
