import os
import zipfile
import json
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"
GEYSER_DIR = ROOT / "headless_server" / "geyser"
PACKS_DIR = GEYSER_DIR / "packs"
CUSTOM_MAPPINGS_DIR = GEYSER_DIR / "custom_mappings"

def build():
    print("=== EXTRACTING CREATE BLOCK TEXTURES ===")
    blocks_tex_dir = RP_DIR / "textures" / "blocks"
    blocks_tex_dir.mkdir(parents=True, exist_ok=True)
    
    models_blocks_dir = RP_DIR / "models" / "blocks"
    models_blocks_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy cogwheel geometry to models/blocks as well
    geo_src = RP_DIR / "models" / "entity" / "cogwheel.geo.json"
    if geo_src.exists():
        (models_blocks_dir / "cogwheel.geo.json").write_text(geo_src.read_text(encoding="utf-8"), encoding="utf-8")
        print("Copied cogwheel.geo.json to models/blocks/")

    extract_map = {
        "assets/create/textures/block/andesite_casing.png": "andesite_casing.png",
        "assets/create/textures/block/brass_casing.png": "brass_casing.png",
        "assets/create/textures/block/copper_casing.png": "copper_casing.png",
        "assets/create/textures/block/railway_casing.png": "railway_casing.png",
        "assets/create/textures/block/zinc_block.png": "zinc_block.png",
        "assets/create/textures/block/brass_block.png": "brass_block.png",
        "assets/create/textures/block/raw_zinc_block.png": "raw_zinc_block.png",
    }

    with zipfile.ZipFile(MOD_JAR, "r") as z:
        for jar_path, out_name in extract_map.items():
            dest = blocks_tex_dir / out_name
            with z.open(jar_path) as src_file, open(dest, "wb") as out_file:
                out_file.write(src_file.read())
            print(f"Extracted: {out_name}")

    # Build terrain_texture.json
    terrain_tex = {
        "resource_pack_name": "create_bedrock",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {
            "create_andesite_casing": {"textures": "textures/blocks/andesite_casing"},
            "create_brass_casing": {"textures": "textures/blocks/brass_casing"},
            "create_copper_casing": {"textures": "textures/blocks/copper_casing"},
            "create_railway_casing": {"textures": "textures/blocks/railway_casing"},
            "create_zinc_block": {"textures": "textures/blocks/zinc_block"},
            "create_brass_block": {"textures": "textures/blocks/brass_block"},
            "create_raw_zinc_block": {"textures": "textures/blocks/raw_zinc_block"},
            "create_cogwheel": {"textures": "textures/entity/create/cogwheel"}
        }
    }
    (RP_DIR / "textures" / "terrain_texture.json").write_text(json.dumps(terrain_tex, indent=2), encoding="utf-8")
    print("Generated terrain_texture.json")

    # Build blocks.json for Bedrock RP
    blocks_json = {
        "format_version": "1.20.10",
        "create:andesite_casing": {
            "textures": "create_andesite_casing",
            "sound": "wood"
        },
        "create:brass_casing": {
            "textures": "create_brass_casing",
            "sound": "wood"
        },
        "create:copper_casing": {
            "textures": "create_copper_casing",
            "sound": "copper"
        },
        "create:railway_casing": {
            "textures": "create_railway_casing",
            "sound": "metal"
        },
        "create:zinc_block": {
            "textures": "create_zinc_block",
            "sound": "metal"
        },
        "create:brass_block": {
            "textures": "create_brass_block",
            "sound": "metal"
        },
        "create:raw_zinc_block": {
            "textures": "create_raw_zinc_block",
            "sound": "stone"
        },
        "create:cogwheel": {
            "textures": "create_cogwheel",
            "sound": "wood"
        }
    }
    (RP_DIR / "blocks.json").write_text(json.dumps(blocks_json, indent=2), encoding="utf-8")
    print("Generated blocks.json")

    # Update manifest to increment version or keep fresh
    manifest_file = RP_DIR / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["header"]["version"][2] += 1
    for m in manifest.get("modules", []):
        m["version"][2] += 1
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Incremented RP version to {manifest['header']['version']}")

    # Repack CreateKineticPack.zip
    pack_zip = PACKS_DIR / "CreateKineticPack.zip"
    if pack_zip.exists():
        pack_zip.unlink()

    with zipfile.ZipFile(pack_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for f in RP_DIR.rglob("*"):
            if f.is_file():
                rel = f.relative_to(RP_DIR)
                z.write(f, str(rel).replace("\\", "/"))
    print(f"Repacked {pack_zip} ({pack_zip.stat().st_size} bytes)")

    # Generate Geyser custom_mappings/create_blocks.json
    CUSTOM_MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    geyser_mapping = {
        "format_version": 1,
        "blocks": {
            "create:andesite_casing": {
                "name": "create:andesite_casing",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_andesite_casing"
                    }
                }
            },
            "create:brass_casing": {
                "name": "create:brass_casing",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_brass_casing"
                    }
                }
            },
            "create:copper_casing": {
                "name": "create:copper_casing",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_copper_casing"
                    }
                }
            },
            "create:railway_casing": {
                "name": "create:railway_casing",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_railway_casing"
                    }
                }
            },
            "create:zinc_block": {
                "name": "create:zinc_block",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_zinc_block"
                    }
                }
            },
            "create:brass_block": {
                "name": "create:brass_block",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_brass_block"
                    }
                }
            },
            "create:raw_zinc_block": {
                "name": "create:raw_zinc_block",
                "unit_cube": True,
                "material_instances": {
                    "*": {
                        "texture": "create_raw_zinc_block"
                    }
                }
            },
            "create:cogwheel": {
                "name": "create:cogwheel",
                "geometry": "geometry.create.cogwheel",
                "material_instances": {
                    "*": {
                        "texture": "create_cogwheel",
                        "render_method": "alpha_test"
                    }
                }
            }
        }
    }
    geyser_mapping_file = CUSTOM_MAPPINGS_DIR / "create_blocks.json"
    geyser_mapping_file.write_text(json.dumps(geyser_mapping, indent=2), encoding="utf-8")
    print(f"Generated Geyser mapping: {geyser_mapping_file}")
    print("=== BUILD COMPLETE ===")

if __name__ == "__main__":
    build()
