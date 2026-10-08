import json
from PIL import Image

with open('official_assets/cogwheel.json') as f:
    m = json.load(f)

print("Texture size in json:", m.get("texture_size"))

# Check each element face UV
for el in m['elements']:
    print(f"Element: {el['name']}")
    for face, fval in el['faces'].items():
        tex = fval.get('texture')
        uv = fval.get('uv')
        rot = fval.get('rotation')
        print(f"  {face:5s}: tex={tex} uv={uv} rot={rot}")
