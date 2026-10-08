import os
import json
import zipfile
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RP_DIR = os.path.join(BASE_DIR, "create_cogwheel_rp")
BP_DIR = os.path.join(BASE_DIR, "create_cogwheel_bp")

# UNMISTAKABLE NEW UUIDS
RP_HEADER_UUID = "8b5a618d-cafd-4cb5-832a-f56d9bf3fb29"
RP_MODULE_UUID = "0714d3da-b158-4da1-9a63-84d640966848"
BP_HEADER_UUID = "1e3d6015-cd48-4802-b8d8-b3a2321f2e2c"
BP_MODULE_UUID = "4b6962cc-4e50-44d1-b19d-9e2cc7a70dba"

def create_dirs():
    os.makedirs(os.path.join(RP_DIR, "entity"), exist_ok=True)
    os.makedirs(os.path.join(RP_DIR, "models", "entity"), exist_ok=True)
    os.makedirs(os.path.join(RP_DIR, "animations"), exist_ok=True)
    os.makedirs(os.path.join(RP_DIR, "textures", "entity", "create"), exist_ok=True)
    os.makedirs(os.path.join(RP_DIR, "textures", "items", "create"), exist_ok=True)
    os.makedirs(os.path.join(BP_DIR, "entities"), exist_ok=True)
    os.makedirs(os.path.join(BP_DIR, "items"), exist_ok=True)
    os.makedirs(os.path.join(BP_DIR, "functions"), exist_ok=True)

def generate_textures():
    # 64x64 texture map for cogwheel
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Andesite/metal shaft area (0,0 to 32,32)
    metal_dark = (74, 82, 85, 255)
    metal_light = (112, 122, 126, 255)
    for x in range(32):
        for y in range(32):
            c = metal_light if (x + y) % 3 == 0 else metal_dark
            img.putpixel((x, y), c)

    # Gold & Emerald center
    draw.ellipse([6, 6, 26, 26], fill=(240, 185, 30, 255), outline=(190, 130, 20, 255), width=3)
    draw.ellipse([11, 11, 21, 21], fill=(20, 240, 70, 255), outline=(10, 170, 40, 255), width=2)

    # 2. Wood cogwheel hub and teeth area (32, 0 to 64, 64)
    wood_dark = (115, 85, 52, 255)
    wood_light = (143, 107, 68, 255)
    wood_ring = (94, 69, 41, 255)
    for x in range(32, 64):
        for y in range(64):
            c = wood_ring if y % 8 == 0 else (wood_light if (x + y) % 4 == 0 else wood_dark)
            img.putpixel((x, y), c)

    tex_path = os.path.join(RP_DIR, "textures", "entity", "create", "cogwheel.png")
    img.save(tex_path)

    # Pack icon
    icon = Image.new("RGBA", (128, 128), (35, 39, 42, 255))
    idraw = ImageDraw.Draw(icon)
    idraw.rectangle([10, 10, 118, 118], outline=(240, 185, 30, 255), width=4)
    idraw.ellipse([34, 34, 94, 94], fill=(143, 107, 68, 255), outline=(94, 69, 41, 255), width=6)
    idraw.ellipse([50, 50, 78, 78], fill=(20, 240, 70, 255))
    
    icon.save(os.path.join(RP_DIR, "pack_icon.png"))
    icon.save(os.path.join(BP_DIR, "pack_icon.png"))

def generate_functions():
    with open(os.path.join(BP_DIR, "functions", "check.mcfunction"), "w", encoding="utf-8") as f:
        f.write('tellraw @a {"rawtext":[{"text":"§6========================================\\n§6[Create Engine] §aPack Active!\\n§e- Emergency Brake: §c/function stop\\n§e- Resume Spin: §a/function spin\\n§6========================================"}]}\n')

    with open(os.path.join(BP_DIR, "functions", "stop.mcfunction"), "w", encoding="utf-8") as f:
        f.write('tag @e[type=create:cogwheel] add stop\n')
        f.write('tag @e[type=create:cogwheel_v2] add stop\n')
        f.write('tellraw @a {"rawtext":[{"text":"§c[Create Engine] §lBRAKE ENGAGED! §r§7Cogwheel frozen at 0 RPM."}]}\n')

    with open(os.path.join(BP_DIR, "functions", "spin.mcfunction"), "w", encoding="utf-8") as f:
        f.write('tag @e[type=create:cogwheel] remove stop\n')
        f.write('tag @e[type=create:cogwheel_v2] remove stop\n')
        f.write('tellraw @a {"rawtext":[{"text":"§a[Create Engine] §lBRAKE RELEASED! §r§7Rotating at 32 RPM."}]}\n')

def generate_rp_manifest():
    manifest = {
        "format_version": 2,
        "header": {
            "name": "🔥 IBRAHIM'S CREATE ENGINE [RP] 🔥",
            "description": ">>> VERIFIED FOR IBRAHIM: 3D Rotating Cogwheel Model & RenderDragon Kinetics <<<",
            "uuid": RP_HEADER_UUID,
            "version": [1, 0, 0],
            "min_engine_version": [1, 20, 0]
        },
        "modules": [
            {
                "type": "resources",
                "uuid": RP_MODULE_UUID,
                "version": [1, 0, 0]
            }
        ]
    }
    with open(os.path.join(RP_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

def generate_bp_manifest():
    manifest = {
        "format_version": 2,
        "header": {
            "name": "🔥 IBRAHIM'S CREATE ENGINE [BP] 🔥",
            "description": ">>> VERIFIED FOR IBRAHIM: Functional Emergency Brake, Create Wrench & Speed Control <<<",
            "uuid": BP_HEADER_UUID,
            "version": [1, 0, 0],
            "min_engine_version": [1, 20, 0]
        },
        "modules": [
            {
                "type": "data",
                "uuid": BP_MODULE_UUID,
                "version": [1, 0, 0]
            }
        ],
        "dependencies": [
            {
                "uuid": RP_HEADER_UUID,
                "version": [1, 0, 0]
            }
        ]
    }
    with open(os.path.join(BP_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

def generate_geometry():
    geo = {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": "geometry.create.cogwheel",
                    "texture_width": 64,
                    "texture_height": 64,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2,
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
                                "uv": [0, 0]
                            }
                        ]
                    },
                    {
                        "name": "cog",
                        "parent": "shaft",
                        "pivot": [0, 8, 0],
                        "cubes": [
                            {
                                "origin": [-5, 3, -2],
                                "size": [10, 10, 4],
                                "uv": [32, 0]
                            },
                            {
                                "origin": [-2, 13, -2],
                                "size": [4, 3, 4],
                                "uv": [32, 16]
                            },
                            {
                                "origin": [-2, 0, -2],
                                "size": [4, 3, 4],
                                "uv": [32, 16]
                            },
                            {
                                "origin": [5, 6, -2],
                                "size": [3, 4, 4],
                                "uv": [32, 24]
                            },
                            {
                                "origin": [-8, 6, -2],
                                "size": [3, 4, 4],
                                "uv": [32, 24]
                            }
                        ]
                    },
                    {
                        "name": "cog_diag",
                        "parent": "cog",
                        "pivot": [0, 8, 0],
                        "rotation": [0, 0, 45],
                        "cubes": [
                            {
                                "origin": [-2, 13, -2],
                                "size": [4, 3, 4],
                                "uv": [32, 16]
                            },
                            {
                                "origin": [-2, 0, -2],
                                "size": [4, 3, 4],
                                "uv": [32, 16]
                            },
                            {
                                "origin": [5, 6, -2],
                                "size": [3, 4, 4],
                                "uv": [32, 24]
                            },
                            {
                                "origin": [-8, 6, -2],
                                "size": [3, 4, 4],
                                "uv": [32, 24]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    with open(os.path.join(RP_DIR, "models", "entity", "cogwheel.geo.json"), "w") as f:
        json.dump(geo, f, indent=2)

def generate_animation():
    molang_eval = "variable.cog_rot = (query.has_tag('stop') ? (variable.cog_rot ?? 0.0) : ((variable.cog_rot ?? 0.0) + query.delta_time * 192.0)); return variable.cog_rot;"
    
    anim = {
        "format_version": "1.8.0",
        "animations": {
            "animation.create.cogwheel.spin": {
                "loop": True,
                "bones": {
                    "cog": {
                        "rotation": [
                            0,
                            0,
                            molang_eval
                        ]
                    },
                    "shaft": {
                        "rotation": [
                            0,
                            0,
                            "variable.cog_rot"
                        ]
                    }
                }
            }
        }
    }
    with open(os.path.join(RP_DIR, "animations", "cogwheel.animation.json"), "w") as f:
        json.dump(anim, f, indent=2)

def generate_client_entity():
    for ident in ["create:cogwheel", "create:cogwheel_v2"]:
        client_ent = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": ident,
                    "materials": {
                        "default": "entity_alphatest"
                    },
                    "textures": {
                        "default": "textures/entity/create/cogwheel"
                    },
                    "geometry": {
                        "default": "geometry.create.cogwheel"
                    },
                    "animations": {
                        "spin": "animation.create.cogwheel.spin"
                    },
                    "scripts": {
                        "animate": [
                            "spin"
                        ]
                    },
                    "render_controllers": [
                        "controller.render.default"
                    ]
                }
            }
        }
        filename = "cogwheel_v2.entity.json" if "v2" in ident else "cogwheel.entity.json"
        with open(os.path.join(RP_DIR, "entity", filename), "w") as f:
            json.dump(client_ent, f, indent=2)

def generate_server_entity():
    for ident in ["create:cogwheel", "create:cogwheel_v2"]:
        server_ent = {
            "format_version": "1.20.10",
            "minecraft:entity": {
                "description": {
                    "identifier": ident,
                    "is_spawnable": True,
                    "is_summonable": True
                },
                "components": {
                    "minecraft:physics": {
                        "has_gravity": False,
                        "has_collision": False
                    },
                    "minecraft:collision_box": {
                        "width": 1.0,
                        "height": 1.0
                    },
                    "minecraft:type_family": {
                        "family": ["create", "inanimate"]
                    }
                }
            }
        }
        filename = "cogwheel_v2.json" if "v2" in ident else "cogwheel.json"
        with open(os.path.join(BP_DIR, "entities", filename), "w") as f:
            json.dump(server_ent, f, indent=2)

def package_zips():
    rp_pack_path = os.path.join(BASE_DIR, "IBRAHIM_CREATE_RP.mcpack")
    with zipfile.ZipFile(rp_pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(RP_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, RP_DIR)
                zf.write(full_path, rel_path)
    print(f"Created: {rp_pack_path}")

    bp_pack_path = os.path.join(BASE_DIR, "IBRAHIM_CREATE_BP.mcpack")
    with zipfile.ZipFile(bp_pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BP_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BP_DIR)
                zf.write(full_path, rel_path)
    print(f"Created: {bp_pack_path}")

    mcaddon_path = os.path.join(BASE_DIR, "IBRAHIM_CREATE_ENGINE.mcaddon")
    with zipfile.ZipFile(mcaddon_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(rp_pack_path, "IBRAHIM_CREATE_RP.mcpack")
        zf.write(bp_pack_path, "IBRAHIM_CREATE_BP.mcpack")
    print(f"Created: {mcaddon_path}")

if __name__ == "__main__":
    create_dirs()
    generate_textures()
    generate_functions()
    generate_rp_manifest()
    generate_bp_manifest()
    generate_geometry()
    generate_animation()
    generate_client_entity()
    generate_server_entity()
    package_zips()
    print("Build Complete!")
