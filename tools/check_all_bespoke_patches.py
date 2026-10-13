import zipfile, json
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"

BESPOKE_BLOCKS = [
    ("mechanical_pump", "assets/create/models/block/mechanical_pump/item.json"),
    ("mechanical_drill", "assets/create/models/block/mechanical_drill/item.json"),
    ("mechanical_saw", "assets/create/models/block/mechanical_saw/item.json"),
    ("deployer", "assets/create/models/block/deployer/item.json"),
    ("encased_fan", "assets/create/models/block/encased_fan/item.json"),
    ("mechanical_press", "assets/create/models/block/mechanical_press/item.json"),
    ("mechanical_mixer", "assets/create/models/block/mechanical_mixer/item.json"),
    ("millstone", "assets/create/models/block/millstone/item.json"),
    ("mechanical_harvester", "assets/create/models/block/mechanical_harvester/item.json"),
    ("cuckoo_clock", "assets/create/models/block/cuckoo_clock/item.json"),
    ("mysterious_cuckoo_clock", "assets/create/models/block/cuckoo_clock/item.json"),
]

with zipfile.ZipFile(MOD_JAR, 'r') as jar:
    for name, path in BESPOKE_BLOCKS:
        d = json.loads(jar.read(path).decode("utf-8"))
        patches = set()
        has_rot_or_flip = 0
        total_faces = 0
        for el in d.get("elements", []):
            for f, fd in el.get("faces", {}).items():
                total_faces += 1
                tex = fd.get("texture")
                uv = tuple(fd.get("uv", []))
                rot = fd.get("rotation", 0)
                if len(uv) == 4 and (uv[0] > uv[2] or uv[1] > uv[3] or rot != 0):
                    has_rot_or_flip += 1
                patches.add((tex, uv, rot))
        print(f"{name}: {len(d.get('elements', []))} elements, {total_faces} faces, {has_rot_or_flip} faces with rot/flip, {len(patches)} unique patches")
