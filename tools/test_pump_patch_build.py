import os
import sys
import json
import zipfile
from pathlib import Path
from PIL import Image
import io

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"

with zipfile.ZipFile(MOD_JAR, 'r') as jar:
    # Test on mechanical_pump
    name = "mechanical_pump"
    model_path = "assets/create/models/block/mechanical_pump/item.json"
    
    raw_data = json.loads(jar.read(model_path).decode("utf-8"))
    tex_size = raw_data.get("texture_size", [16, 16])
    tex_w = float(tex_size[0]) if len(tex_size) > 0 else 16.0
    tex_h = float(tex_size[1]) if len(tex_size) > 1 else 16.0
    
    textures_map = raw_data.get("textures", {})
    raw_elements = raw_data.get("elements", [])
    
    tex_path = "assets/create/textures/block/pump.png"
    img = Image.open(io.BytesIO(jar.read(tex_path))).convert("RGBA")
    tex_images = {"4": img}
    
    # Import rotate_element
    sys.path.insert(0, str(ROOT / "tools"))
    from build_bespoke_models import rotate_element
    rotated_elements = [rotate_element(el, 90, -90) for el in raw_elements]
    
    # Find all transformed patches
    patches = {}
    for elem in rotated_elements:
        for f, fdata in elem.get("faces", {}).items():
            tkey = fdata.get("texture", "").lstrip("#")
            raw_uv = fdata.get("uv", [0, 0, 16, 16])
            rot = fdata.get("rotation", 0) % 360
            u1, v1, u2, v2 = raw_uv
            if u1 > u2 or v1 > v2 or rot != 0:
                pk = (tkey, round(u1, 3), round(v1, 3), round(u2, 3), round(v2, 3), rot)
                if pk not in patches:
                    s_img = tex_images[tkey]
                    sx = s_img.width / 16.0
                    sy = s_img.height / 16.0
                    umin, umax = min(u1, u2), max(u1, u2)
                    vmin, vmax = min(v1, v2), max(v1, v2)
                    px1 = int(round(umin * sx))
                    px2 = max(px1 + 1, int(round(umax * sx)))
                    py1 = int(round(vmin * sy))
                    py2 = max(py1 + 1, int(round(vmax * sy)))
                    p = s_img.crop((px1, py1, px2, py2))
                    if u1 > u2: p = p.transpose(Image.FLIP_LEFT_RIGHT)
                    if v1 > v2: p = p.transpose(Image.FLIP_TOP_BOTTOM)
                    if rot == 90: p = p.transpose(Image.ROTATE_270)
                    elif rot == 180: p = p.transpose(Image.ROTATE_180)
                    elif rot == 270: p = p.transpose(Image.ROTATE_90)
                    patches[pk] = p
                    
    print(f"Created {len(patches)} unique transformed patches for {name}")
    for pk, p in patches.items():
        print(f"  {pk} -> size {p.size}")
