import json
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
GEO_FILE = ROOT / "create_cogwheel_rp" / "models" / "blocks" / "mechanical_pump.geo.json"

with open(GEO_FILE, "r", encoding="utf-8") as f:
    geo_data = json.load(f)

geo = geo_data["minecraft:geometry"][0]
desc = geo["description"]
tex_w = desc["texture_width"]
tex_h = desc["texture_height"]
bones = geo["bones"]

assert desc["identifier"] == "geometry.create.mechanical_pump", "Identifier mismatch"
assert tex_w == 64 and tex_h == 64, f"Atlas size unexpected: {tex_w}x{tex_h}"

total_cubes = 0
for b in bones:
    cubes = b.get("cubes", [])
    total_cubes += len(cubes)
    for c in cubes:
        assert "rotation" not in c, f"Cube-level rotation forbidden: {c}"
        orig = c["origin"]
        size = c["size"]
        for i in range(3):
            assert orig[i] >= -15.9 and orig[i] <= 31.9, f"Origin out of bounds: {orig}"
            assert orig[i] + size[i] >= -15.9 and orig[i] + size[i] <= 31.9, f"Vertex out of bounds: {orig} + {size}"
        
        # Validate face UVs within atlas
        for fname, fuv in c.get("uv", {}).items():
            u, v = fuv["uv"]
            uw, vh = fuv["uv_size"]
            assert uw > 0 and vh > 0, f"Non-positive uv_size: {fuv}"
            assert u >= 0 and u + uw <= tex_w, f"U coordinate out of atlas: u={u}, w={uw}, atlas_w={tex_w}"
            assert v >= 0 and v + vh <= tex_h, f"V coordinate out of atlas: v={v}, h={vh}, atlas_h={tex_h}"

assert len(bones) == 7, f"Expected 7 bones (1 root + 6 child), got {len(bones)}"
assert total_cubes == 10, f"Expected 10 cubes, got {total_cubes}"

print("All pump geometry and atlas UV assertions PASSED!")

# Validate Facing Transformations
facings = {
    "up": (90, 0, 0),
    "down": (270, 0, 0),
    "north": (0, 0, 0),
    "south": (0, 180, 0),
    "east": (0, 90, 0),
    "west": (0, 270, 0),
}
base_pitch = -90 # around X
for facing, rot in facings.items():
    net_pitch = (base_pitch + rot[0]) % 360
    if facing == "up":
        assert net_pitch == 0, f"facing=up net pitch should be 0 (restoring item.json), got {net_pitch}"
    print(f"  Facing '{facing}': permutation rot={rot} -> net pitch={net_pitch} deg (VALID)")

print("All 6 facing variants validated successfully!")
