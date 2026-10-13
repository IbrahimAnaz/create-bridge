import json
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
RP_MODELS = ROOT / "create_cogwheel_rp" / "models" / "blocks"

scaffold_cubes = [
    {
        "origin": [-8.0, 0.0, -8.0],
        "size": [16.0, 16.0, 16.0],
        "uv": {
            "north": {"uv": [0.0, 0.0], "uv_size": [16.0, 16.0]},
            "south": {"uv": [0.0, 0.0], "uv_size": [16.0, 16.0]},
            "east": {"uv": [0.0, 0.0], "uv_size": [16.0, 16.0]},
            "west": {"uv": [0.0, 0.0], "uv_size": [16.0, 16.0]},
            "up": {"uv": [0.0, 16.0], "uv_size": [16.0, 16.0]}
        }
    },
    {
        "origin": [-8.0, 15.9, -8.0],
        "size": [16.0, 0.1, 16.0],
        "uv": {
            "down": {"uv": [0.0, 16.0], "uv_size": [16.0, 16.0]}
        }
    },
    {
        "origin": [-7.95, 0.0, -8.0],
        "size": [15.9, 16.0, 16.0],
        "uv": {
            "east": {"uv": [16.0, 0.0], "uv_size": [16.0, 16.0]},
            "west": {"uv": [16.0, 0.0], "uv_size": [16.0, 16.0]}
        }
    },
    {
        "origin": [-8.0, 0.0, -7.95],
        "size": [16.0, 16.0, 15.9],
        "uv": {
            "north": {"uv": [16.0, 0.0], "uv_size": [16.0, 16.0]},
            "south": {"uv": [16.0, 0.0], "uv_size": [16.0, 16.0]}
        }
    }
]

for mat in ["andesite", "brass", "copper"]:
    file_path = RP_MODELS / f"{mat}_scaffolding.geo.json"
    if not file_path.exists():
        print(f"Skipping {file_path}, does not exist")
        continue

    geo = json.loads(file_path.read_text(encoding="utf-8"))
    geo["minecraft:geometry"][0]["bones"][0]["cubes"] = scaffold_cubes
    file_path.write_text(json.dumps(geo, indent=2), encoding="utf-8")
    print(f"[+] Cleaned {mat}_scaffolding.geo.json -> exactly 4 non-conflicting cubes!")

print("All scaffolding geometries updated successfully!")
