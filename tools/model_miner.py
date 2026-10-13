"""
Create Mod -> Bedrock Geometry (.geo.json) Model Miner & Converter
===================================================================
Automated pipeline to extract, resolve, and convert Create Java JSON block/item
models and OBJ models into Bedrock format (`minecraft:geometry` v1.12.0),
stitch per-model texture atlases, update Bedrock resource pack manifests,
and synchronize Geyser extension registries with automatic cache busting.

Usage:
    python tools/model_miner.py --mine <block_name>
    python tools/model_miner.py --batch <name1> <name2> ...
    python tools/model_miner.py --all
    python tools/model_miner.py --list
    python tools/model_miner.py --search <keyword>
    python tools/model_miner.py --repack
    python tools/model_miner.py --status
"""

import os
import sys
import json
import uuid
import shutil
import zipfile
import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_JAR = ROOT / "headless_server" / "mods" / "create-1.21.1-6.0.8.jar"
RP_DIR = ROOT / "create_cogwheel_rp"
PACK_ZIP = ROOT / "headless_server" / "geyser" / "packs" / "CreateKineticPack.zip"
PORTABLE_PACK_ZIP = ROOT / "portable_bridge" / "geyser" / "packs" / "CreateKineticPack.zip"
PORTABLE_EXT_JAR = ROOT / "portable_bridge" / "geyser" / "extensions" / "CreateBridge.jar"

# Known valve handle dye colors
VALVE_HANDLE_COLORS = [
    "copper", "white", "orange", "magenta", "light_blue", "yellow", "lime",
    "pink", "gray", "light_gray", "cyan", "purple", "blue", "brown",
    "green", "red", "black"
]

# Standard vanilla Minecraft block model templates referenced by Create mod blocks
VANILLA_TEMPLATES = {
    "minecraft:block/cube_all": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#all"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#all"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#all"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#all"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#all"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#all"}
            }
        }]
    },
    "block/cube_all": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#all"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#all"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#all"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#all"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#all"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#all"}
            }
        }]
    },
    "minecraft:block/cube_column": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#end"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#end"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#side"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#side"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#side"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#side"}
            }
        }]
    },
    "minecraft:block/cube_column_horizontal": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#side"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#side"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#end"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#end"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#side"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#side"}
            }
        }]
    },
    "minecraft:block/cube_bottom_top": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#side"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#side"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#side"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#side"}
            }
        }]
    },
    "minecraft:block/slab": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 8, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                "north": {"uv": [0, 8, 16, 16], "texture": "#side"},
                "south": {"uv": [0, 8, 16, 16], "texture": "#side"},
                "west":  {"uv": [0, 8, 16, 16], "texture": "#side"},
                "east":  {"uv": [0, 8, 16, 16], "texture": "#side"}
            }
        }]
    },
    "minecraft:block/slab_top": {
        "elements": [{
            "from": [0, 8, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                "north": {"uv": [0, 0, 16, 8],  "texture": "#side"},
                "south": {"uv": [0, 0, 16, 8],  "texture": "#side"},
                "west":  {"uv": [0, 0, 16, 8],  "texture": "#side"},
                "east":  {"uv": [0, 0, 16, 8],  "texture": "#side"}
            }
        }]
    },
    "minecraft:block/stairs": {
        "elements": [
            {
                "from": [0, 0, 0], "to": [16, 8, 16],
                "faces": {
                    "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                    "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                    "north": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "south": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "west":  {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "east":  {"uv": [0, 8, 16, 16], "texture": "#side"}
                }
            },
            {
                "from": [0, 8, 8], "to": [16, 16, 16],
                "faces": {
                    "up":    {"uv": [0, 8, 16, 16], "texture": "#top"},
                    "north": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "south": {"uv": [0, 0, 16, 8],  "texture": "#side"},
                    "west":  {"uv": [8, 0, 16, 8],  "texture": "#side"},
                    "east":  {"uv": [0, 0, 8, 8],   "texture": "#side"}
                }
            }
        ]
    },
    "minecraft:block/inner_stairs": {
        "elements": [
            {
                "from": [0, 0, 0], "to": [16, 8, 16],
                "faces": {
                    "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                    "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                    "north": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "south": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "west":  {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "east":  {"uv": [0, 8, 16, 16], "texture": "#side"}
                }
            },
            {
                "from": [0, 8, 8], "to": [16, 16, 16],
                "faces": {
                    "up":    {"uv": [0, 8, 16, 16], "texture": "#top"},
                    "north": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "south": {"uv": [0, 0, 16, 8],  "texture": "#side"},
                    "west":  {"uv": [8, 0, 16, 8],  "texture": "#side"},
                    "east":  {"uv": [0, 0, 8, 8],   "texture": "#side"}
                }
            },
            {
                "from": [0, 8, 0], "to": [8, 16, 8],
                "faces": {
                    "up":    {"uv": [0, 0, 8, 8],   "texture": "#top"},
                    "north": {"uv": [8, 0, 16, 8],  "texture": "#side"},
                    "west":  {"uv": [0, 0, 8, 8],   "texture": "#side"},
                    "east":  {"uv": [0, 8, 8, 16],  "texture": "#side"}
                }
            }
        ]
    },
    "minecraft:block/outer_stairs": {
        "elements": [
            {
                "from": [0, 0, 0], "to": [16, 8, 16],
                "faces": {
                    "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                    "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                    "north": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "south": {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "west":  {"uv": [0, 8, 16, 16], "texture": "#side"},
                    "east":  {"uv": [0, 8, 16, 16], "texture": "#side"}
                }
            },
            {
                "from": [8, 8, 8], "to": [16, 16, 16],
                "faces": {
                    "up":    {"uv": [8, 8, 16, 16], "texture": "#top"},
                    "north": {"uv": [0, 8, 8, 16],  "texture": "#side"},
                    "south": {"uv": [0, 0, 8, 8],   "texture": "#side"},
                    "west":  {"uv": [8, 8, 16, 16], "texture": "#side"},
                    "east":  {"uv": [0, 0, 8, 8],   "texture": "#side"}
                }
            }
        ]
    },
    "minecraft:block/template_wall_post": {
        "elements": [{
            "from": [4, 0, 4], "to": [12, 16, 12],
            "faces": {
                "down":  {"uv": [4, 4, 12, 12], "texture": "#wall"},
                "up":    {"uv": [4, 4, 12, 12], "texture": "#wall"},
                "north": {"uv": [4, 0, 12, 16], "texture": "#wall"},
                "south": {"uv": [4, 0, 12, 16], "texture": "#wall"},
                "west":  {"uv": [4, 0, 12, 16], "texture": "#wall"},
                "east":  {"uv": [4, 0, 12, 16], "texture": "#wall"}
            }
        }]
    },
    "minecraft:block/template_wall_side": {
        "elements": [{
            "from": [5, 0, 0], "to": [11, 14, 8],
            "faces": {
                "down":  {"uv": [5, 8, 11, 16], "texture": "#wall"},
                "up":    {"uv": [5, 0, 11, 8],  "texture": "#wall"},
                "north": {"uv": [5, 2, 11, 16], "texture": "#wall"},
                "south": {"uv": [5, 2, 11, 16], "texture": "#wall"},
                "west":  {"uv": [0, 2, 8, 16],  "texture": "#wall"},
                "east":  {"uv": [8, 2, 16, 16], "texture": "#wall"}
            }
        }]
    },
    "minecraft:block/template_wall_side_tall": {
        "elements": [{
            "from": [5, 0, 0], "to": [11, 16, 8],
            "faces": {
                "down":  {"uv": [5, 8, 11, 16], "texture": "#wall"},
                "up":    {"uv": [5, 0, 11, 8],  "texture": "#wall"},
                "north": {"uv": [5, 0, 11, 16], "texture": "#wall"},
                "south": {"uv": [5, 0, 11, 16], "texture": "#wall"},
                "west":  {"uv": [0, 0, 8, 16],  "texture": "#wall"},
                "east":  {"uv": [8, 0, 16, 16], "texture": "#wall"}
            }
        }]
    },
    "minecraft:block/template_glass_pane_post": {
        "elements": [{
            "from": [7, 0, 7], "to": [9, 16, 9],
            "faces": {
                "down":  {"uv": [7, 7, 9, 9], "texture": "#edge"},
                "up":    {"uv": [7, 7, 9, 9], "texture": "#edge"},
                "north": {"uv": [7, 0, 9, 16], "texture": "#pane"},
                "south": {"uv": [7, 0, 9, 16], "texture": "#pane"},
                "west":  {"uv": [7, 0, 9, 16], "texture": "#pane"},
                "east":  {"uv": [7, 0, 9, 16], "texture": "#pane"}
            }
        }]
    },
    "minecraft:block/template_glass_pane_side": {
        "elements": [{
            "from": [7, 0, 0], "to": [9, 16, 8],
            "faces": {
                "down":  {"uv": [7, 0, 9, 8], "texture": "#edge"},
                "up":    {"uv": [7, 0, 9, 8], "texture": "#edge"},
                "north": {"uv": [7, 0, 9, 16], "texture": "#edge"},
                "south": {"uv": [7, 0, 9, 16], "texture": "#edge"},
                "west":  {"uv": [0, 0, 8, 16], "texture": "#pane"},
                "east":  {"uv": [8, 0, 16, 16], "texture": "#pane"}
            }
        }]
    },
    "minecraft:block/template_glass_pane_noside": {
        "elements": [{
            "from": [7, 0, 0], "to": [9, 16, 8],
            "faces": {
                "down":  {"uv": [7, 0, 9, 8], "texture": "#edge"},
                "up":    {"uv": [7, 0, 9, 8], "texture": "#edge"},
                "west":  {"uv": [0, 0, 8, 16], "texture": "#pane"},
                "east":  {"uv": [8, 0, 16, 16], "texture": "#pane"}
            }
        }]
    },
    "minecraft:block/template_glass_pane_noside_alt": {
        "elements": [{
            "from": [7, 0, 0], "to": [9, 16, 8],
            "faces": {
                "down":  {"uv": [7, 0, 9, 8], "texture": "#edge"},
                "up":    {"uv": [7, 0, 9, 8], "texture": "#edge"},
                "west":  {"uv": [0, 0, 8, 16], "texture": "#pane"},
                "east":  {"uv": [8, 0, 16, 16], "texture": "#pane"}
            }
        }]
    },
    "minecraft:block/orientable": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#top"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#front"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#side"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#side"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#side"}
            }
        }]
    },
    "minecraft:block/orientable_with_bottom": {
        "elements": [{
            "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {
                "down":  {"uv": [0, 0, 16, 16], "texture": "#bottom"},
                "up":    {"uv": [0, 0, 16, 16], "texture": "#top"},
                "north": {"uv": [0, 0, 16, 16], "texture": "#front"},
                "south": {"uv": [0, 0, 16, 16], "texture": "#side"},
                "west":  {"uv": [0, 0, 16, 16], "texture": "#side"},
                "east":  {"uv": [0, 0, 16, 16], "texture": "#side"}
            }
        }]
    }
}


class CreateJarCatalog:
    """Indexes and caches files from the Create mod JAR."""
    def __init__(self, jar_path=MOD_JAR):
        self.jar_path = Path(jar_path)
        self.zip_file = zipfile.ZipFile(self.jar_path, "r")
        self.all_names = set(self.zip_file.namelist())
        self._json_cache = {}

    def has_file(self, path):
        return path in self.all_names

    def read_json(self, path):
        if path in self._json_cache:
            return self._json_cache[path]
        if path not in self.all_names:
            return None
        try:
            data = json.loads(self.zip_file.read(path).decode("utf-8"))
            self._json_cache[path] = data
            return data
        except Exception:
            return None

    def read_image(self, path):
        if path not in self.all_names:
            return None
        try:
            return Image.open(self.zip_file.open(path)).convert("RGBA")
        except Exception:
            return None

    def close(self):
        self.zip_file.close()


class ModelResolver:
    """Recursively resolves Java models, element inheritance, and texture maps."""
    def __init__(self, catalog):
        self.catalog = catalog

    def model_path_from_id(self, model_id):
        """Converts model ID like 'create:block/depot/block' into jar entry path."""
        clean_id = model_id
        if clean_id.startswith("create:"):
            clean_id = clean_id[7:]
        elif clean_id.startswith("minecraft:"):
            clean_id = clean_id[10:]

        if not clean_id.endswith(".json") and not clean_id.endswith(".obj"):
            clean_id += ".json"

        # Check in create assets
        candidate1 = f"assets/create/models/{clean_id}"
        if self.catalog.has_file(candidate1):
            return candidate1

        # Check in minecraft assets
        candidate2 = f"assets/minecraft/models/{clean_id}"
        if self.catalog.has_file(candidate2):
            return candidate2

        return None

    def find_best_model_for_block(self, block_name):
        """Finds the most complete and authentic static block model path for a block name."""
        # 1. Check blockstate first for authentic placed block model
        bs_path = f"assets/create/blockstates/{block_name}.json"
        if self.catalog.has_file(bs_path):
            bs = self.catalog.read_json(bs_path)
            model_ref = None
            if bs and "variants" in bs:
                for v in bs["variants"].values():
                    if isinstance(v, list) and len(v) > 0 and "model" in v[0]:
                        model_ref = v[0]["model"]
                        break
                    elif isinstance(v, dict) and "model" in v:
                        model_ref = v["model"]
                        break
            elif bs and "multipart" in bs:
                for part in bs["multipart"]:
                    app = part.get("apply", {})
                    if isinstance(app, list) and len(app) > 0 and "model" in app[0]:
                        model_ref = app[0]["model"]
                        break
                    elif isinstance(app, dict) and "model" in app:
                        model_ref = app["model"]
                        break
            if model_ref:
                p = self.model_path_from_id(model_ref)
                if p:
                    return p

        # 2. Check direct block model candidates (prefer clean block casing/bases over item assembly)
        candidates = [
            f"assets/create/models/block/{block_name}/block.json",
            f"assets/create/models/block/{block_name}.json",
            f"assets/create/models/block/{block_name}/horizontal.json",
            f"assets/create/models/block/{block_name}/vertical.json",
            f"assets/create/models/block/{block_name}/block_single.json",
            f"assets/create/models/item/{block_name}.json",
            f"assets/create/models/block/{block_name}/item.json",  # Fallback only if no static block model exists
        ]
        for c in candidates:
            if self.catalog.has_file(c):
                return c

        return None

    def resolve_model(self, model_path, depth=0):
        """
        Recursively resolves model elements, texture variables, and parent templates.
        Returns a dict: { 'elements': [...], 'textures': {...}, 'loader': str|None, 'raw': dict }
        """
        if depth > 25 or not model_path:
            return None

        data = self.catalog.read_json(model_path)
        if not data:
            return None

        # Check for OBJ loader
        if data.get("loader") == "neoforge:obj" or model_path.endswith(".obj"):
            return {
                "elements": [],
                "textures": data.get("textures", {}),
                "loader": "neoforge:obj",
                "obj_model": data.get("model"),
                "raw": data
            }

        textures = dict(data.get("textures", {}))
        elements = list(data.get("elements", []))

        # Check for composite loader with sub-children (e.g. display_link, nixie_tube, stock_link)
        if "children" in data:
            for child_name, child_data in data.get("children", {}).items():
                if isinstance(child_data, dict):
                    textures.update(child_data.get("textures", {}))
                    elements.extend(child_data.get("elements", []))

        # Follow parent if elements missing or for inherited textures
        if "parent" in data:
            parent_id = data["parent"]
            parent_path = self.model_path_from_id(parent_id)
            parent_resolved = None

            if parent_path:
                parent_resolved = self.resolve_model(parent_path, depth + 1)
            elif parent_id in VANILLA_TEMPLATES:
                parent_resolved = dict(VANILLA_TEMPLATES[parent_id])

            if parent_resolved:
                # Inherit parent textures (current model overrides parent)
                merged_tex = dict(parent_resolved.get("textures", {}))
                merged_tex.update(textures)
                textures = merged_tex

                # If this model has no elements, inherit parent elements
                if not elements and parent_resolved.get("elements"):
                    elements = list(parent_resolved["elements"])

                if not elements and parent_resolved.get("loader") == "neoforge:obj":
                    return {
                        "elements": [],
                        "textures": textures,
                        "loader": "neoforge:obj",
                        "obj_model": parent_resolved.get("obj_model"),
                        "raw": data
                    }

        return {
            "elements": elements,
            "textures": textures,
            "loader": data.get("loader"),
            "raw": data
        }

    def resolve_texture_path(self, tex_var_or_path, textures_map, depth=0):
        """Resolves texture variable references like '#0' -> '#base' -> 'create:block/andesite'."""
        if depth > 15:
            return None
        target = tex_var_or_path
        if target.startswith("#"):
            key = target[1:]
            if key in textures_map:
                return self.resolve_texture_path(textures_map[key], textures_map, depth + 1)
            # Smart fallback aliases
            for fallback_key in ["all", "texture", "casing", "0", "side", "top", "bottom", "end", "wall", "pane"]:
                if fallback_key in textures_map:
                    return self.resolve_texture_path(textures_map[fallback_key], textures_map, depth + 1)
            return None

        # Format full asset path
        clean = target
        if clean.startswith("create:"):
            clean = "assets/create/textures/" + clean[7:] + ".png"
        elif clean.startswith("minecraft:"):
            clean = "assets/minecraft/textures/" + clean[10:] + ".png"
        elif clean.startswith("block/"):
            clean = "assets/create/textures/" + clean + ".png"
        else:
            clean = "assets/create/textures/" + clean + ".png"

        return clean


class ModelConverter:
    """Converts resolved Java models/OBJ models to Bedrock geometry and texture atlases."""
    def __init__(self, catalog):
        self.catalog = catalog
        self.resolver = ModelResolver(catalog)

    def convert(self, block_name, custom_model_path=None):
        """Main entry point to convert a single block."""
        model_path = custom_model_path or self.resolver.find_best_model_for_block(block_name)
        if not model_path:
            # Check if this is a valve handle variant
            if "valve_handle" in block_name:
                return self.build_valve_handle_geometry(block_name)
            print(f"[-] Could not find Java model for '{block_name}' in JAR.")
            return False

        resolved = self.resolver.resolve_model(model_path)
        if not resolved:
            print(f"[-] Failed to resolve model hierarchy for '{block_name}'.")
            return False

        if resolved.get("loader") == "neoforge:obj" or "valve_handle" in block_name:
            if "valve_handle" in block_name:
                return self.build_valve_handle_geometry(block_name, resolved)
            print(f"[*] Block '{block_name}' uses OBJ loader ({resolved.get('obj_model')}).")
            return self.build_obj_proxy_geometry(block_name, resolved)

        elements = resolved.get("elements", [])
        if not elements:
            print(f"[-] No 3D elements found for '{block_name}' (model: {model_path}).")
            return False

        return self.build_bedrock_geometry_from_elements(block_name, resolved, model_path)

    def build_bedrock_geometry_from_elements(self, block_name, resolved, model_path):
        """Converts Java elements and texture maps into Bedrock .geo.json & atlas."""
        elements = resolved["elements"]
        textures_map = resolved["textures"]
        geo_id = f"geometry.create.{block_name}"
        tex_key = f"create_{block_name}"

        # Check model native texture_size
        raw_model = resolved.get("raw", {})
        tex_size_decl = raw_model.get("texture_size", [16, 16])
        model_tex_w = float(tex_size_decl[0]) if len(tex_size_decl) > 0 else 16.0
        model_tex_h = float(tex_size_decl[1]) if len(tex_size_decl) > 1 else 16.0

        # 1. Resolve all unique textures used by element faces
        face_tex_vars = set()
        for elem in elements:
            for face_name, face_data in elem.get("faces", {}).items():
                raw_tex = face_data.get("texture", "")
                if raw_tex:
                    face_tex_vars.add(raw_tex)

        # Load images from JAR
        tex_images = {}
        for tvar in face_tex_vars:
            tpath = self.resolver.resolve_texture_path(tvar, textures_map)
            clean_key = tvar.lstrip("#")
            if tpath and self.catalog.has_file(tpath):
                img = self.catalog.read_image(tpath)
                if img:
                    tex_images[clean_key] = img
            else:
                # Fallbacks: check direct paths
                for alt_cand in [
                    f"assets/create/textures/block/{clean_key}.png",
                    f"assets/create/textures/block/{block_name}.png",
                    f"assets/create/textures/{clean_key}.png"
                ]:
                    if self.catalog.has_file(alt_cand):
                        img = self.catalog.read_image(alt_cand)
                        if img:
                            tex_images[clean_key] = img
                            break

        if not tex_images:
            # Fallback 16x16 placeholder
            tex_images["default"] = Image.new("RGBA", (16, 16), (150, 150, 150, 255))

        # 2. Stitch Texture Atlas
        num_tex = len(tex_images)
        if num_tex == 1:
            single_key = next(iter(tex_images.keys()))
            atlas = tex_images[single_key]
            atlas_w, atlas_h = atlas.size
            tex_offsets = {single_key: (0, 0)}
            tex_scales = {single_key: (atlas_w / model_tex_w, atlas_h / model_tex_h)}
        else:
            tile_w = max(16, max(img.width for img in tex_images.values()))
            tile_h = max(16, max(img.height for img in tex_images.values()))
            cols = 2 if num_tex <= 4 else 4
            rows = ((num_tex + cols - 1) // cols)
            atlas_w = cols * tile_w
            atlas_h = rows * tile_h
            atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
            tex_offsets = {}
            tex_scales = {}
            for idx, (tkey, img) in enumerate(tex_images.items()):
                gx = (idx % cols) * tile_w
                gy = (idx // cols) * tile_h
                atlas.paste(img.resize((tile_w, tile_h)), (gx, gy))
                tex_offsets[tkey] = (gx, gy)
                tex_scales[tkey] = (tile_w / model_tex_w, tile_h / model_tex_h)

        out_tex_file = RP_DIR / "textures" / "blocks" / f"{block_name}.png"
        out_tex_file.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(out_tex_file)

        # 3. Build Bedrock Cubes
        bedrock_cubes = []
        for elem in elements:
            f = elem.get("from", [0, 0, 0])
            t = elem.get("to", [16, 16, 16])

            min_x, max_x = min(f[0], t[0]), max(f[0], t[0])
            min_y, max_y = min(f[1], t[1]), max(f[1], t[1])
            min_z, max_z = min(f[2], t[2]), max(f[2], t[2])

            origin = [round(min_x - 8.0, 3), round(min_y, 3), round(min_z - 8.0, 3)]
            size = [round(max_x - min_x, 3), round(max_y - min_y, 3), round(max_z - min_z, 3)]

            cube_dict = {
                "origin": origin,
                "size": size,
                "uv": {}
            }

            # Handle element rotation
            if "rotation" in elem:
                rot = elem["rotation"]
                orig = rot.get("origin", [8, 8, 8])
                axis = rot.get("axis", "y").lower()
                angle = float(rot.get("angle", 0))

                cube_dict["pivot"] = [round(orig[0] - 8.0, 3), round(orig[1], 3), round(orig[2] - 8.0, 3)]
                if axis == "x":
                    cube_dict["rotation"] = [-angle, 0, 0]
                elif axis == "y":
                    cube_dict["rotation"] = [0, -angle, 0]
                elif axis == "z":
                    cube_dict["rotation"] = [0, 0, angle]

            # Map faces
            faces = elem.get("faces", {})
            for face_name in ["north", "south", "east", "west", "up", "down"]:
                if face_name not in faces:
                    continue
                face_data = faces[face_name]
                raw_tex = face_data.get("texture", "").lstrip("#")
                
                # Resolve texture offset & scale
                off_x, off_y = (0, 0)
                scale_x, scale_y = (1.0, 1.0)
                if raw_tex in tex_offsets:
                    off_x, off_y = tex_offsets[raw_tex]
                    scale_x, scale_y = tex_scales[raw_tex]
                elif tex_offsets:
                    first_k = next(iter(tex_offsets.keys()))
                    off_x, off_y = tex_offsets[first_k]
                    scale_x, scale_y = tex_scales[first_k]

                # Default UV if not specified in Java model
                if "uv" in face_data:
                    raw_uv = face_data["uv"]
                else:
                    if face_name in ("north", "south"):
                        raw_uv = [min_x, 16 - max_y, max_x, 16 - min_y]
                    elif face_name in ("east", "west"):
                        raw_uv = [min_z, 16 - max_y, max_z, 16 - min_y]
                    else:
                        raw_uv = [min_x, min_z, max_x, max_z]

                u_min, u_max = min(raw_uv[0], raw_uv[2]), max(raw_uv[0], raw_uv[2])
                v_min, v_max = min(raw_uv[1], raw_uv[3]), max(raw_uv[1], raw_uv[3])

                bedrock_u = round(off_x + u_min * scale_x, 3)
                bedrock_v = round(off_y + v_min * scale_y, 3)
                uv_w = round((u_max - u_min) * scale_x, 3)
                uv_h = round((v_max - v_min) * scale_y, 3)

                face_uv_entry = {
                    "uv": [bedrock_u, bedrock_v],
                    "uv_size": [uv_w, uv_h]
                }
                
                # Handle face UV rotation
                if "rotation" in face_data and face_data["rotation"] != 0:
                    face_uv_entry["uv_rotation"] = face_data["rotation"]

                cube_dict["uv"][face_name] = face_uv_entry

            bedrock_cubes.append(cube_dict)

        # 4. Save Bedrock Geometry (.geo.json)
        geo_file = RP_DIR / "models" / "blocks" / f"{block_name}.geo.json"
        geo_file.parent.mkdir(parents=True, exist_ok=True)
        geo_json = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": geo_id,
                        "texture_width": atlas_w,
                        "texture_height": atlas_h,
                        "visible_bounds_width": 2,
                        "visible_bounds_height": 2,
                        "visible_bounds_offset": [0, 0.5, 0]
                    },
                    "bones": [
                        {
                            "name": "root",
                            "pivot": [0, 0, 0],
                            "cubes": bedrock_cubes
                        }
                    ]
                }
            ]
        }
        with open(geo_file, "w", encoding="utf-8") as f:
            json.dump(geo_json, f, indent=2)

        # 5. Update Manifests
        self.register_in_manifests(block_name, geo_id, tex_key)
        print(f"[+] Successfully mined '{block_name}': {len(bedrock_cubes)} cubes, atlas ({atlas_w}x{atlas_h}) -> {geo_file.name}")
        return True

    def build_valve_handle_geometry(self, block_name, resolved=None):
        """Constructs authentic 3D valve handle Bedrock geometry with wheel rim, spokes, and hub."""
        geo_id = f"geometry.create.{block_name}"
        tex_key = f"create_{block_name}"

        # Resolve color from name
        color = "copper"
        for c in VALVE_HANDLE_COLORS:
            if c in block_name:
                color = c
                break

        tex_jar_path = f"assets/create/textures/block/valve_handle/valve_handle_{color}.png"
        tex_img = self.catalog.read_image(tex_jar_path)
        if not tex_img:
            tex_img = self.catalog.read_image("assets/create/textures/block/valve_handle/valve_handle_copper.png")

        out_tex_file = RP_DIR / "textures" / "blocks" / f"{block_name}.png"
        out_tex_file.parent.mkdir(parents=True, exist_ok=True)
        if tex_img:
            tex_img.save(out_tex_file)

        # Build authentic valve handle cubes matching Create's valve_handle.obj
        cubes = [
            # 1. Central Hub Base
            {
                "origin": [-3, 0, -3],
                "size": [6, 2, 6],
                "uv": {
                    "north": {"uv": [5, 2], "uv_size": [6, 2]},
                    "south": {"uv": [5, 2], "uv_size": [6, 2]},
                    "east": {"uv": [5, 2], "uv_size": [6, 2]},
                    "west": {"uv": [5, 2], "uv_size": [6, 2]},
                    "up": {"uv": [5, 0], "uv_size": [6, 6]},
                    "down": {"uv": [5, 0], "uv_size": [6, 6]}
                }
            },
            # 2. Central Hub Stem
            {
                "origin": [-2, 2, -2],
                "size": [4, 3, 4],
                "uv": {
                    "north": {"uv": [6, 1], "uv_size": [4, 3]},
                    "south": {"uv": [6, 1], "uv_size": [4, 3]},
                    "east": {"uv": [6, 1], "uv_size": [4, 3]},
                    "west": {"uv": [6, 1], "uv_size": [4, 3]},
                    "up": {"uv": [6, 0], "uv_size": [4, 4]},
                    "down": {"uv": [6, 0], "uv_size": [4, 4]}
                }
            },
            # 3. Spoke X
            {
                "origin": [-6, 5, -1],
                "size": [12, 1.5, 2],
                "uv": {
                    "north": {"uv": [2, 2], "uv_size": [12, 1.5]},
                    "south": {"uv": [2, 2], "uv_size": [12, 1.5]},
                    "east": {"uv": [2, 2], "uv_size": [2, 1.5]},
                    "west": {"uv": [2, 2], "uv_size": [2, 1.5]},
                    "up": {"uv": [2, 0], "uv_size": [12, 2]},
                    "down": {"uv": [2, 0], "uv_size": [12, 2]}
                }
            },
            # 4. Spoke Z
            {
                "origin": [-1, 5, -6],
                "size": [2, 1.5, 12],
                "uv": {
                    "north": {"uv": [2, 2], "uv_size": [2, 1.5]},
                    "south": {"uv": [2, 2], "uv_size": [2, 1.5]},
                    "east": {"uv": [2, 2], "uv_size": [12, 1.5]},
                    "west": {"uv": [2, 2], "uv_size": [12, 1.5]},
                    "up": {"uv": [2, 0], "uv_size": [2, 12]},
                    "down": {"uv": [2, 0], "uv_size": [2, 12]}
                }
            },
            # 5. Rim: North Bar
            {
                "origin": [-3, 5, -7],
                "size": [6, 2.5, 2],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [6, 2]},
                    "down": {"uv": [0, 0], "uv_size": [6, 2]}
                }
            },
            # 6. Rim: South Bar
            {
                "origin": [-3, 5, 5],
                "size": [6, 2.5, 2],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [6, 2]},
                    "down": {"uv": [0, 0], "uv_size": [6, 2]}
                }
            },
            # 7. Rim: East Bar
            {
                "origin": [5, 5, -3],
                "size": [2, 2.5, 6],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [2, 6]},
                    "down": {"uv": [0, 0], "uv_size": [2, 6]}
                }
            },
            # 8. Rim: West Bar
            {
                "origin": [-7, 5, -3],
                "size": [2, 2.5, 6],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [6, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [2, 6]},
                    "down": {"uv": [0, 0], "uv_size": [2, 6]}
                }
            },
            # 9. Rim: Northeast Diagonal
            {
                "origin": [3.2, 5, -5.5],
                "size": [2, 2.5, 3.5],
                "pivot": [4.2, 6, -3.7],
                "rotation": [0, 45, 0],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [2, 3.5]},
                    "down": {"uv": [0, 0], "uv_size": [2, 3.5]}
                }
            },
            # 10. Rim: Northwest Diagonal
            {
                "origin": [-5.2, 5, -5.5],
                "size": [2, 2.5, 3.5],
                "pivot": [-4.2, 6, -3.7],
                "rotation": [0, -45, 0],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [2, 3.5]},
                    "down": {"uv": [0, 0], "uv_size": [2, 3.5]}
                }
            },
            # 11. Rim: Southeast Diagonal
            {
                "origin": [3.2, 5, 2.0],
                "size": [2, 2.5, 3.5],
                "pivot": [4.2, 6, 3.7],
                "rotation": [0, -45, 0],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [2, 3.5]},
                    "down": {"uv": [0, 0], "uv_size": [2, 3.5]}
                }
            },
            # 12. Rim: Southwest Diagonal
            {
                "origin": [-5.2, 5, 2.0],
                "size": [2, 2.5, 3.5],
                "pivot": [-4.2, 6, 3.7],
                "rotation": [0, 45, 0],
                "uv": {
                    "north": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "south": {"uv": [0, 5], "uv_size": [2, 2.5]},
                    "east": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "west": {"uv": [0, 5], "uv_size": [3.5, 2.5]},
                    "up": {"uv": [0, 0], "uv_size": [2, 3.5]},
                    "down": {"uv": [0, 0], "uv_size": [2, 3.5]}
                }
            }
        ]

        geo_file = RP_DIR / "models" / "blocks" / f"{block_name}.geo.json"
        geo_file.parent.mkdir(parents=True, exist_ok=True)
        geo_json = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": geo_id,
                        "texture_width": 16,
                        "texture_height": 16,
                        "visible_bounds_width": 2,
                        "visible_bounds_height": 2,
                        "visible_bounds_offset": [0, 0.5, 0]
                    },
                    "bones": [
                        {
                            "name": "root",
                            "pivot": [0, 0, 0],
                            "cubes": cubes
                        }
                    ]
                }
            ]
        }
        with open(geo_file, "w", encoding="utf-8") as f:
            json.dump(geo_json, f, indent=2)

        self.register_in_manifests(block_name, geo_id, tex_key)
        print(f"[+] Successfully mined 3D valve handle '{block_name}' ({len(cubes)} cubes) -> {geo_file.name}")
        return True

    def build_obj_proxy_geometry(self, block_name, resolved):
        """Constructs an authentic multi-element kinetic geometry approximation for OBJ blocks."""
        geo_id = f"geometry.create.{block_name}"
        tex_key = f"create_{block_name}"

        # Resolve primary texture
        tex_map = resolved.get("textures", {})
        tvar = next(iter(tex_map.values()), f"create:block/{block_name}") if tex_map else f"create:block/{block_name}"
        tpath = self.resolver.resolve_texture_path(tvar, tex_map)
        img = self.catalog.read_image(tpath) if tpath else None
        if not img:
            img = self.catalog.read_image(f"assets/create/textures/block/{block_name}.png")
        if not img:
            img = Image.new("RGBA", (16, 16), (140, 140, 140, 255))

        out_tex_file = RP_DIR / "textures" / "blocks" / f"{block_name}.png"
        out_tex_file.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_tex_file)

        # Build high-fidelity kinetic geometry
        if "crushing_wheel" in block_name:
            # 8-faceted crushing wheel with central shaft
            cubes = [
                {"origin": [-4, 0, -4], "size": [8, 16, 8], "uv": {"north": {"uv": [4, 0], "uv_size": [8, 16]}, "south": {"uv": [4, 0], "uv_size": [8, 16]}, "east": {"uv": [4, 0], "uv_size": [8, 16]}, "west": {"uv": [4, 0], "uv_size": [8, 16]}, "up": {"uv": [4, 4], "uv_size": [8, 8]}, "down": {"uv": [4, 4], "uv_size": [8, 8]}}},
                {"origin": [-8, 2, -7], "size": [16, 12, 14], "uv": {"north": {"uv": [0, 2], "uv_size": [16, 12]}, "south": {"uv": [0, 2], "uv_size": [16, 12]}, "east": {"uv": [1, 2], "uv_size": [14, 12]}, "west": {"uv": [1, 2], "uv_size": [14, 12]}, "up": {"uv": [0, 1], "uv_size": [16, 14]}, "down": {"uv": [0, 1], "uv_size": [16, 14]}}},
                {"origin": [-7, 2, -8], "size": [14, 12, 16], "pivot": [0, 8, 0], "rotation": [0, 45, 0], "uv": {"north": {"uv": [1, 2], "uv_size": [14, 12]}, "south": {"uv": [1, 2], "uv_size": [14, 12]}, "east": {"uv": [0, 2], "uv_size": [16, 12]}, "west": {"uv": [0, 2], "uv_size": [16, 12]}, "up": {"uv": [1, 0], "uv_size": [14, 16]}, "down": {"uv": [1, 0], "uv_size": [14, 16]}}}
            ]
        elif "water_wheel" in block_name:
            # Water wheel hub + 4 radial paddles
            cubes = [
                {"origin": [-3, 0, -3], "size": [6, 16, 6], "uv": {"north": {"uv": [5, 0], "uv_size": [6, 16]}, "south": {"uv": [5, 0], "uv_size": [6, 16]}, "east": {"uv": [5, 0], "uv_size": [6, 16]}, "west": {"uv": [5, 0], "uv_size": [6, 16]}, "up": {"uv": [5, 5], "uv_size": [6, 6]}, "down": {"uv": [5, 5], "uv_size": [6, 6]}}},
                {"origin": [-1, 0, -8], "size": [2, 16, 16], "uv": {"north": {"uv": [7, 0], "uv_size": [2, 16]}, "south": {"uv": [7, 0], "uv_size": [2, 16]}, "east": {"uv": [0, 0], "uv_size": [16, 16]}, "west": {"uv": [0, 0], "uv_size": [16, 16]}, "up": {"uv": [7, 0], "uv_size": [2, 16]}, "down": {"uv": [7, 0], "uv_size": [2, 16]}}},
                {"origin": [-8, 0, -1], "size": [16, 16, 2], "uv": {"north": {"uv": [0, 0], "uv_size": [16, 16]}, "south": {"uv": [0, 0], "uv_size": [16, 16]}, "east": {"uv": [7, 0], "uv_size": [2, 16]}, "west": {"uv": [7, 0], "uv_size": [2, 16]}, "up": {"uv": [0, 7], "uv_size": [16, 2]}, "down": {"uv": [0, 7], "uv_size": [16, 2]}}}
            ]
        elif "flywheel" in block_name:
            # Heavy kinetic flywheel rim and axle
            cubes = [
                {"origin": [-2, 0, -2], "size": [4, 16, 4], "uv": {"north": {"uv": [6, 0], "uv_size": [4, 16]}, "south": {"uv": [6, 0], "uv_size": [4, 16]}, "east": {"uv": [6, 0], "uv_size": [4, 16]}, "west": {"uv": [6, 0], "uv_size": [4, 16]}, "up": {"uv": [6, 6], "uv_size": [4, 4]}, "down": {"uv": [6, 6], "uv_size": [4, 4]}}},
                {"origin": [-7, 2, -7], "size": [14, 12, 14], "uv": {"north": {"uv": [1, 2], "uv_size": [14, 12]}, "south": {"uv": [1, 2], "uv_size": [14, 12]}, "east": {"uv": [1, 2], "uv_size": [14, 12]}, "west": {"uv": [1, 2], "uv_size": [14, 12]}, "up": {"uv": [1, 1], "uv_size": [14, 14]}, "down": {"uv": [1, 1], "uv_size": [14, 14]}}}
            ]
        else:
            cubes = [
                {"origin": [-7, 1, -7], "size": [14, 14, 14], "uv": {"north": {"uv": [1, 1], "uv_size": [14, 14]}, "south": {"uv": [1, 1], "uv_size": [14, 14]}, "east": {"uv": [1, 1], "uv_size": [14, 14]}, "west": {"uv": [1, 1], "uv_size": [14, 14]}, "up": {"uv": [1, 1], "uv_size": [14, 14]}, "down": {"uv": [1, 1], "uv_size": [14, 14]}}}
            ]

        geo_file = RP_DIR / "models" / "blocks" / f"{block_name}.geo.json"
        geo_file.parent.mkdir(parents=True, exist_ok=True)
        geo_json = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": geo_id,
                        "texture_width": 16,
                        "texture_height": 16,
                        "visible_bounds_width": 2,
                        "visible_bounds_height": 2,
                        "visible_bounds_offset": [0, 0.5, 0]
                    },
                    "bones": [
                        {
                            "name": "root",
                            "pivot": [0, 0, 0],
                            "cubes": cubes
                        }
                    ]
                }
            ]
        }
        with open(geo_file, "w", encoding="utf-8") as f:
            json.dump(geo_json, f, indent=2)

        self.register_in_manifests(block_name, geo_id, tex_key)
        print(f"[+] Generated kinetic geometry for OBJ block '{block_name}' ({len(cubes)} cubes) -> {geo_file.name}")
        return True

    def register_in_manifests(self, block_name, geo_id, tex_key):
        """Updates blocks.json, terrain_texture.json, and item_texture.json."""
        # 1. blocks.json (Strictly spec-compliant: textures and sound only)
        blocks_file = RP_DIR / "blocks.json"
        blocks_data = json.loads(blocks_file.read_text(encoding="utf-8")) if blocks_file.exists() else {"format_version": "1.20.10"}
        sound = "wood" if "casing" in block_name else "metal"
        blocks_data[f"create:{block_name}"] = {
            "textures": tex_key,
            "sound": sound
        }
        blocks_file.write_text(json.dumps(blocks_data, indent=2), encoding="utf-8")

        # 2. terrain_texture.json
        terrain_file = RP_DIR / "textures" / "terrain_texture.json"
        if terrain_file.exists():
            terrain_data = json.loads(terrain_file.read_text(encoding="utf-8"))
            terrain_data["texture_data"][tex_key] = {
                "textures": f"textures/blocks/{block_name}"
            }
            terrain_file.write_text(json.dumps(terrain_data, indent=2), encoding="utf-8")

        # 3. item_texture.json
        item_file = RP_DIR / "textures" / "item_texture.json"
        if item_file.exists():
            item_data = json.loads(item_file.read_text(encoding="utf-8"))
            item_data["texture_data"][tex_key] = {
                "textures": f"textures/blocks/{block_name}"
            }
            item_file.write_text(json.dumps(item_data, indent=2), encoding="utf-8")


def bump_pack_manifest():
    """Bumps pack version and generates fresh UUIDs to bust Bedrock client cache."""
    manifest_file = RP_DIR / "manifest.json"
    if not manifest_file.exists():
        return None
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        curr_ver = manifest.get("header", {}).get("version", [1, 0, 0])
        next_ver = [curr_ver[0], curr_ver[1], curr_ver[2] + 1]
        
        new_header_uuid = str(uuid.uuid4())
        new_module_uuid = str(uuid.uuid4())

        manifest["header"]["version"] = next_ver
        manifest["header"]["uuid"] = new_header_uuid
        if manifest.get("modules"):
            manifest["modules"][0]["version"] = next_ver
            manifest["modules"][0]["uuid"] = new_module_uuid

        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"[+] Bumped pack manifest to version {next_ver} (UUID: {new_header_uuid[:8]}...)")
        return next_ver
    except Exception as e:
        print(f"[-] Warning: Failed to bump manifest: {e}")
        return None


def repack_pack():
    """Zips create_cogwheel_rp into CreateKineticPack.zip and synchronizes to portable_bridge."""
    print("[*] Repacking CreateKineticPack.zip with fresh cache buster...")
    bump_pack_manifest()

    if PACK_ZIP.exists():
        PACK_ZIP.unlink()
    PACK_ZIP.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(PACK_ZIP, "w", zipfile.ZIP_DEFLATED) as zout:
        for f in RP_DIR.rglob("*"):
            if f.is_file():
                zout.write(f, str(f.relative_to(RP_DIR)).replace("\\", "/"))

    print(f"[+] Repacked {PACK_ZIP.name} ({PACK_ZIP.stat().st_size:,} bytes).")

    # Sync to portable_bridge
    if PORTABLE_PACK_ZIP.parent.exists():
        shutil.copy2(PACK_ZIP, PORTABLE_PACK_ZIP)
        print(f"[+] Synchronized pack to portable_bridge: {PORTABLE_PACK_ZIP.name}")


def get_all_create_blocks(catalog):
    """Returns a list of all block names from blockstates in Create mod."""
    prefix = "assets/create/blockstates/"
    blocks = []
    for name in catalog.all_names:
        if name.startswith(prefix) and name.endswith(".json"):
            bname = name[len(prefix):-5]
            blocks.append(bname)
    return sorted(blocks)


def list_blocks(catalog):
    """Prints a status table of all Create blocks."""
    resolver = ModelResolver(catalog)
    blocks = get_all_create_blocks(catalog)
    print(f"\n{'BLOCK NAME':<35} {'STATUS':<20} {'DETAILS'}")
    print("=" * 75)

    custom_geo_dir = RP_DIR / "models" / "blocks"
    existing_geos = set(f.stem.replace(".geo", "") for f in custom_geo_dir.glob("*.geo.json"))

    custom_count = 0
    mined_count = 0
    for b in blocks:
        is_mined = b in existing_geos
        mpath = resolver.find_best_model_for_block(b)
        res = resolver.resolve_model(mpath) if mpath else None

        if is_mined:
            mined_count += 1
            status = "[MINED GEO]"
        elif res and res.get("elements"):
            custom_count += 1
            status = f"CUSTOM ({len(res['elements'])} cubes)"
        elif res and res.get("loader") == "neoforge:obj" or "valve_handle" in b:
            custom_count += 1
            status = "OBJ MODEL"
        else:
            status = "VANILLA CUBE"

        details = mpath or "No direct model"
        if len(details) > 38:
            details = "..." + details[-35:]
        print(f"{b:<35} {status:<20} {details}")

    print("=" * 75)
    print(f"Total Blocks: {len(blocks)} | Mined in Pack: {mined_count} | Unmined 3D Models: {custom_count}\n")


def status_report():
    """Prints which blocks currently have custom .geo.json files in the pack."""
    custom_geo_dir = RP_DIR / "models" / "blocks"
    geos = sorted([f.name for f in custom_geo_dir.glob("*.geo.json")])
    print(f"\n[Status] Mined Bedrock Geometries in {custom_geo_dir}: ({len(geos)} total)")
    for g in geos:
        print(f"  - {g}")
    print()


def sync_extension_geo_blocks():
    """Scans all generated .geo.json models and synchronizes geo_blocks.json across all bridge targets."""
    custom_geo_dir = RP_DIR / "models" / "blocks"
    geo_dict = {}
    for f in custom_geo_dir.glob("*.geo.json"):
        bname = f.stem.replace(".geo", "")
        geo_dict[bname] = f"geometry.create.{bname}"
    
    json_bytes = json.dumps(geo_dict, indent=2).encode("utf-8")

    # Target destinations
    targets = [
        ROOT / "tools" / "extension" / "resources" / "geo_blocks.json",
        ROOT / "portable_bridge" / "extension" / "resources" / "geo_blocks.json",
        ROOT / "portable_bridge" / "extension" / "bin" / "geo_blocks.json",
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(json_bytes)
        print(f"[+] Synchronized {len(geo_dict)} models to {target.relative_to(ROOT)}")


def mine_blocks(catalog, block_names, repack=True):
    """Mines a list of blocks, synchronizes extension registry, and repacks."""
    converter = ModelConverter(catalog)
    success = 0
    failed = 0
    for name in block_names:
        print(f"\n--> Mining: {name}")
        ok = converter.convert(name)
        if ok:
            success += 1
        else:
            failed += 1

    if success > 0:
        sync_extension_geo_blocks()
        if repack:
            repack_pack()

    print(f"\n[Complete] Successfully mined: {success}, Failed: {failed}")
    return success


def main():
    parser = argparse.ArgumentParser(description="Mine out .geo.json Bedrock models from Create mod JAR.")
    parser.add_argument("--mine", "-m", help="Mine a specific block by name (e.g. water_wheel, basin, depot)")
    parser.add_argument("--batch", "-b", nargs="+", help="Mine a list of blocks by name")
    parser.add_argument("--all", "-a", action="store_true", help="Mine all custom 3D element and OBJ blocks")
    parser.add_argument("--valve-handles", action="store_true", help="Mine all 17 valve handles")
    parser.add_argument("--list", "-l", action="store_true", help="List all Create blocks and their model types")
    parser.add_argument("--status", "-s", action="store_true", help="Show currently mined .geo.json models")
    parser.add_argument("--repack", "-r", action="store_true", help="Repack CreateKineticPack.zip")
    parser.add_argument("--search", help="Search for blocks matching a keyword")
    args = parser.parse_args()

    if not MOD_JAR.exists():
        print(f"Error: Create mod JAR not found at {MOD_JAR}")
        sys.exit(1)

    catalog = CreateJarCatalog(MOD_JAR)

    try:
        if args.status:
            status_report()
        elif args.list:
            list_blocks(catalog)
        elif args.search:
            blocks = get_all_create_blocks(catalog)
            matches = [b for b in blocks if args.search.lower() in b.lower()]
            print(f"\nSearch results for '{args.search}' ({len(matches)} matches):")
            for m in matches:
                print(f"  - {m}")
            print()
        elif args.valve_handles:
            valve_names = [f"{c}_valve_handle" for c in VALVE_HANDLE_COLORS] + ["valve_handle"]
            mine_blocks(catalog, valve_names, repack=True)
        elif args.mine:
            mine_blocks(catalog, [args.mine], repack=True)
        elif args.batch:
            mine_blocks(catalog, args.batch, repack=True)
        elif args.all:
            blocks = get_all_create_blocks(catalog)
            resolver = ModelResolver(catalog)
            targets = []
            for b in blocks:
                if "valve_handle" in b:
                    targets.append(b)
                    continue
                mpath = resolver.find_best_model_for_block(b)
                if mpath:
                    res = resolver.resolve_model(mpath)
                    if res and (res.get("elements") or res.get("loader") == "neoforge:obj"):
                        targets.append(b)
            print(f"[*] Found {len(targets)} blocks with custom 3D geometry to mine...")
            mine_blocks(catalog, targets, repack=True)
        elif args.repack:
            repack_pack()
        else:
            parser.print_help()
    finally:
        catalog.close()

if __name__ == "__main__":
    main()
