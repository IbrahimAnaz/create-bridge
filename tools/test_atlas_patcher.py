import os
import sys
import json
import zipfile
from pathlib import Path
from PIL import Image
import io

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
VANILLA_JAR = Path(os.path.expandvars(r"%APPDATA%\.minecraft\versions\1.21.5\1.21.5.jar"))

BESPOKE_BLOCKS = {
    "mechanical_pump": {
        "model": "assets/create/models/block/mechanical_pump/item.json",
        "y_rot": 90,
        "x_rot": -90,
    },
    "mechanical_drill": {
        "model": "assets/create/models/block/mechanical_drill/item.json",
        "y_rot": 180,
        "x_rot": 0,
    },
    "mechanical_saw": {
        "model": "assets/create/models/block/mechanical_saw/item.json",
        "y_rot": 180,
        "x_rot": -90,
    },
    "deployer": {
        "model": "assets/create/models/block/deployer/item.json",
        "y_rot": 180,
        "x_rot": 0,
    },
    "encased_fan": {
        "model": "assets/create/models/block/encased_fan/item.json",
        "y_rot": 180,
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

with zipfile.ZipFile(MOD_JAR, 'r') as jar:
    for name, cfg in BESPOKE_BLOCKS.items():
        raw_data = json.loads(jar.read(cfg["model"]).decode("utf-8"))
        elements = raw_data.get("elements", [])
        textures_map = raw_data.get("textures", {})
        
        # Count transformed faces
        tx_count = 0
        for el in elements:
            for f, fd in el.get("faces", {}).items():
                uv = fd.get("uv", [0, 0, 16, 16])
                rot = fd.get("rotation", 0)
                if uv[0] > uv[2] or uv[1] > uv[3] or rot != 0:
                    tx_count += 1
        print(f"Block '{name}': {len(elements)} elements, {tx_count} transformed faces")
