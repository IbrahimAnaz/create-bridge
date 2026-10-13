import json
import zipfile
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"

with zipfile.ZipFile(MOD_JAR, "r") as z:
    raw = z.read("assets/create/models/block/large_cogwheel.json").decode("utf-8")
model = json.loads(raw)

# Elements in Java Create:
# center is at [8, 8, 8]
# In Bedrock geometry, block center is [0, 8, 0]
# Elements have from: [x, y, z] to: [x, y, z]
# Bedrock cube origin = [from[0] - 8, from[1], from[2] - 8]
# When element has rotation: { "angle": A, "axis": "y", "origin": [8, 8, 8] }
# In Bedrock, we create a bone with pivot: [0, 8, 0], rotation: [0, -A, 0] (or A)

bones = []
# 1. Root bone for non-rotated elements
root_cubes = []

# Group elements by their rotation angle around Y
rot_groups = {} # angle -> list of cubes

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
        raw_uv = face_data.get("uv", [0, 0, 16, 16])
        u_min, u_max = min(raw_uv[0], raw_uv[2]), max(raw_uv[0], raw_uv[2])
        v_min, v_max = min(raw_uv[1], raw_uv[3]), max(raw_uv[1], raw_uv[3])

        # Java model uses 32x32 texture atlas where texture #4 or #0 has specific coords
        # In large_cogwheel.png (32x32):
        # We preserve the UV coordinates directly
        cube_dict["uv"][face_name] = {
            "uv": [round(u_min, 3), round(v_min, 3)],
            "uv_size": [round(u_max - u_min, 3), round(v_max - v_min, 3)]
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

# Add bones for each rotation angle
# In Java model rotation around Y: positive angle is clockwise (or counter-clockwise)
# In Bedrock geometry: rotation around Y is [0, -angle, 0] or [0, angle, 0]
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
                "texture_width": 32,
                "texture_height": 32,
                "visible_bounds_width": 3,
                "visible_bounds_height": 3,
                "visible_bounds_offset": [0, 0.5, 0]
            },
            "bones": bones
        }
    ]
}

out_geo_file = RP_DIR / "models" / "blocks" / "large_cogwheel.geo.json"
with open(out_geo_file, "w", encoding="utf-8") as f:
    json.dump(geo_json, f, indent=2)

print(f"Generated {out_geo_file.name} with {len(bones)} bones:")
for b in bones:
    print(f"  Bone '{b['name']}': rot={b.get('rotation', [0,0,0])}, cubes={len(b.get('cubes', []))}")
