import zipfile
import json
import os

jar_path = 'headless_server/mods/create-1.21.1-6.0.8.jar'

with zipfile.ZipFile(jar_path, 'r') as z:
    names = z.namelist()

visuals = sorted([n for n in names if (n.endswith('Visual.class') or 'visual' in n.lower()) and n.endswith('.class')])
renderers = sorted([n for n in names if n.endswith('Renderer.class')])
ct_behaviours = sorted([n for n in names if 'CTBehaviour' in n and n.endswith('.class')])

output = {
    "visuals_count": len(visuals),
    "visuals": visuals,
    "renderers_count": len(renderers),
    "renderers": renderers,
    "ct_count": len(ct_behaviours),
    "ct_behaviours": ct_behaviours
}

with open('tools/flywheel_and_renderers.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Extracted {len(visuals)} visuals, {len(renderers)} renderers, {len(ct_behaviours)} CT behaviours.")
