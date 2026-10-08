import os, json, shutil
from PIL import Image

print("--- Generating Official Create Mod Assets for Bedrock ---")

# 1. Generate 64x64 Texture Atlas
atlas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
cog_tex = Image.open('official_assets/cogwheel.png').convert('RGBA')
axis_tex = Image.open('official_assets/cogwheel_axis.png').convert('RGBA')
axis_top_tex = Image.open('official_assets/axis_top.png').convert('RGBA')
axis_plain_tex = Image.open('official_assets/axis.png').convert('RGBA')

atlas.paste(cog_tex, (0, 0))
atlas.paste(axis_tex, (32, 0))
atlas.paste(axis_top_tex, (48, 0))
atlas.paste(axis_plain_tex, (32, 16))

atlas_path = 'official_assets/cogwheel_atlas.png'
atlas.save(atlas_path)
print(f"Created official atlas: {atlas_path} (64x64)")

# 2. Build Bedrock Geometry JSON
def convert_uv(u1, v1, u2, v2, tex_type):
    if tex_type == 'cog':
        return {"uv": [u1 * 2, v1 * 2], "uv_size": [(u2 - u1) * 2, (v2 - v1) * 2]}
    elif tex_type == 'axis_side':
        return {"uv": [32 + u1, v1], "uv_size": [u2 - u1, v2 - v1]}
    elif tex_type == 'axis_cap':
        return {"uv": [48 + u1, v1], "uv_size": [u2 - u1, v2 - v1]}

geo_data = {
    "format_version": "1.12.0",
    "minecraft:geometry": [
        {
            "description": {
                "identifier": "geometry.create.cogwheel",
                "texture_width": 64,
                "texture_height": 64,
                "visible_bounds_width": 3,
                "visible_bounds_height": 3,
                "visible_bounds_offset": [0, 0.5, 0]
            },
            "bones": [
                {
                    "name": "root",
                    "pivot": [0, 8, 0]
                },
                {
                    "name": "shaft",
                    "parent": "root",
                    "pivot": [0, 8, 0],
                    "cubes": [
                        {
                            "origin": [-2, 6, -8],
                            "size": [4, 4, 16],
                            "uv": {
                                "north": convert_uv(6, 6, 10, 10, 'axis_cap'),
                                "south": convert_uv(6, 6, 10, 10, 'axis_cap'),
                                "east":  convert_uv(6, 0, 10, 16, 'axis_side'),
                                "west":  convert_uv(6, 0, 10, 16, 'axis_side'),
                                "up":    convert_uv(6, 0, 10, 16, 'axis_side'),
                                "down":  convert_uv(6, 0, 10, 16, 'axis_side')
                            }
                        }
                    ]
                },
                {
                    "name": "cog",
                    "parent": "shaft",
                    "pivot": [0, 8, 0],
                    "cubes": [
                        # Gear 1: Horizontal tooth bar
                        {
                            "origin": [-9, 6.5, -1.5],
                            "size": [18, 3, 3],
                            "uv": {
                                "north": convert_uv(7, 6, 16, 7.5, 'cog'),
                                "south": convert_uv(7, 6, 16, 7.5, 'cog'),
                                "east":  convert_uv(5, 8, 6.5, 9.5, 'cog'),
                                "west":  convert_uv(5, 8, 6.5, 9.5, 'cog'),
                                "up":    convert_uv(7, 8, 16, 9.5, 'cog'),
                                "down":  convert_uv(7, 8, 16, 9.5, 'cog')
                            }
                        },
                        # Gear 4: Vertical tooth bar (90 deg)
                        {
                            "origin": [-1.5, -1, -1.5],
                            "size": [3, 18, 3],
                            "uv": {
                                "north": dict(convert_uv(7, 6, 16, 7.5, 'cog'), uv_rotation=90),
                                "south": dict(convert_uv(7, 6, 16, 7.5, 'cog'), uv_rotation=90),
                                "east":  convert_uv(7, 8, 16, 9.5, 'cog'),
                                "west":  convert_uv(7, 8, 16, 9.5, 'cog'),
                                "up":    convert_uv(5, 8, 6.5, 9.5, 'cog'),
                                "down":  convert_uv(5, 8, 6.5, 9.5, 'cog')
                            }
                        },
                        # GearCaseInner: 12x12 spruce face
                        {
                            "origin": [-6, 2, -1.45],
                            "size": [12, 12, 2.9],
                            "uv": {
                                "north": convert_uv(4, 0, 10, 6, 'cog'),
                                "south": convert_uv(4, 0, 10, 6, 'cog'),
                                "east":  convert_uv(0, 6, 6, 7.5, 'cog'),
                                "west":  convert_uv(0, 6, 6, 7.5, 'cog'),
                                "up":    convert_uv(0, 6, 6, 7.5, 'cog'),
                                "down":  convert_uv(0, 6, 6, 7.5, 'cog')
                            }
                        },
                        # GearCaseOuter: 8x8 hub ring
                        {
                            "origin": [-4, 4, -2],
                            "size": [8, 8, 4],
                            "uv": {
                                "north": convert_uv(0, 0, 4, 4, 'cog'),
                                "south": convert_uv(0, 0, 4, 4, 'cog'),
                                "east":  convert_uv(0, 4, 4, 6, 'cog'),
                                "west":  convert_uv(0, 4, 4, 6, 'cog'),
                                "up":    convert_uv(0, 4, 4, 6, 'cog'),
                                "down":  convert_uv(0, 4, 4, 6, 'cog')
                            }
                        }
                    ]
                },
                {
                    "name": "cog_diag",
                    "parent": "cog",
                    "pivot": [0, 8, 0],
                    "rotation": [0, 0, 45],
                    "cubes": [
                        # Gear 2: Tooth bar at 45 deg
                        {
                            "origin": [-9, 6.5, -1.5],
                            "size": [18, 3, 3],
                            "uv": {
                                "north": convert_uv(7, 6, 16, 7.5, 'cog'),
                                "south": convert_uv(7, 6, 16, 7.5, 'cog'),
                                "east":  convert_uv(5, 8, 6.5, 9.5, 'cog'),
                                "west":  convert_uv(5, 8, 6.5, 9.5, 'cog'),
                                "up":    convert_uv(7, 8, 16, 9.5, 'cog'),
                                "down":  convert_uv(7, 8, 16, 9.5, 'cog')
                            }
                        },
                        # Gear 3: Tooth bar at 135 deg
                        {
                            "origin": [-1.5, -1, -1.5],
                            "size": [3, 18, 3],
                            "uv": {
                                "north": dict(convert_uv(7, 6, 16, 7.5, 'cog'), uv_rotation=90),
                                "south": dict(convert_uv(7, 6, 16, 7.5, 'cog'), uv_rotation=90),
                                "east":  convert_uv(7, 8, 16, 9.5, 'cog'),
                                "west":  convert_uv(7, 8, 16, 9.5, 'cog'),
                                "up":    convert_uv(5, 8, 6.5, 9.5, 'cog'),
                                "down":  convert_uv(5, 8, 6.5, 9.5, 'cog')
                            }
                        }
                    ]
                }
            ]
        }
    ]
}

geo_path = 'create_cogwheel_rp/models/entity/cogwheel.geo.json'
with open(geo_path, 'w', encoding='utf-8') as f:
    json.dump(geo_data, f, indent=2)
print(f"Written official geometry to: {geo_path}")

# 3. Copy official textures to workspace
tex_cog_path = 'create_cogwheel_rp/textures/entity/create/cogwheel.png'
os.makedirs(os.path.dirname(tex_cog_path), exist_ok=True)
atlas.save(tex_cog_path)

wrench_src = 'official_assets/wrench.png'
wrench_dst = 'create_cogwheel_rp/textures/items/create/wrench.png'
os.makedirs(os.path.dirname(wrench_dst), exist_ok=True)
shutil.copyfile(wrench_src, wrench_dst)
print(f"Copied official textures to workspace!")

# 4. Deploy to target directories
deploy_targets = [
    r'C:\Users\ibrah\AppData\Roaming\Minecraft Bedrock\Users\Shared\games\com.mojang\resource_packs\CreateCros',
    r'C:\Users\ibrah\AppData\Roaming\Minecraft Bedrock\Users\2397517056789112588\games\com.mojang\minecraftWorlds\CFKVdHQ+Ac0=\resource_packs\CreateCros'
]

# Find any additional worlds
import glob
all_world_rps = glob.glob(r'C:\Users\ibrah\AppData\Roaming\Minecraft Bedrock\Users\*\games\com.mojang\minecraftWorlds\*\resource_packs\CreateCros')
for wrp in all_world_rps:
    if wrp not in deploy_targets:
        deploy_targets.append(wrp)

for target_rp in deploy_targets:
    if os.path.exists(target_rp):
        t_geo = os.path.join(target_rp, 'models', 'entity', 'cogwheel.geo.json')
        t_cog = os.path.join(target_rp, 'textures', 'entity', 'create', 'cogwheel.png')
        t_wrench = os.path.join(target_rp, 'textures', 'items', 'create', 'wrench.png')
        
        os.makedirs(os.path.dirname(t_geo), exist_ok=True)
        os.makedirs(os.path.dirname(t_cog), exist_ok=True)
        os.makedirs(os.path.dirname(t_wrench), exist_ok=True)
        
        shutil.copyfile(geo_path, t_geo)
        shutil.copyfile(tex_cog_path, t_cog)
        shutil.copyfile(wrench_src, t_wrench)
        print(f"Deployed to: {target_rp}")

print("--- Deployment Completed Successfully! ---")
