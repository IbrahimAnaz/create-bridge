import json, uuid, zipfile, os, shutil
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
RP_DIR = ROOT / "create_cogwheel_rp"
HEADLESS_PACK = ROOT / "headless_server" / "geyser" / "packs" / "CreateKineticPack.zip"
MANIFEST = RP_DIR / "manifest.json"

with open(MANIFEST, "r", encoding="utf-8") as f:
    data = json.load(f)

# Increment version and generate fresh UUIDs to bust Bedrock client cache
curr_ver = data["header"]["version"]
new_ver = [curr_ver[0], curr_ver[1], curr_ver[2] + 1]
data["header"]["version"] = new_ver
data["header"]["uuid"] = str(uuid.uuid4())
data["modules"][0]["version"] = new_ver
data["modules"][0]["uuid"] = str(uuid.uuid4())

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Updated manifest.json to version {new_ver} and fresh UUIDs!")

HEADLESS_PACK.parent.mkdir(parents=True, exist_ok=True)

file_count = 0
with zipfile.ZipFile(HEADLESS_PACK, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
    for root, dirs, files in os.walk(RP_DIR):
        for file in files:
            p = Path(root) / file
            rel_path = p.relative_to(RP_DIR)
            z_out.write(p, str(rel_path).replace("\\", "/"))
            file_count += 1

size = HEADLESS_PACK.stat().st_size
print(f"Successfully repacked {file_count} files into CreateKineticPack.zip ({size} bytes) in {HEADLESS_PACK}!")
