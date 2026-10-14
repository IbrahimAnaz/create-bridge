#!/usr/bin/env python3
"""
Generate complete Bedrock geometry definitions for Create fluid pipes.
Covers all 64 connection permutations directly with accurate Create Mod models and UV coordinates.
"""

import json
from pathlib import Path

def uv_face(u, v, w, h):
    return {"uv": [float(u), float(v)], "uv_size": [float(w), float(h)]}

# Texture size 32x32:
# Copper pipe body from Create pipes.png:
# [8, 0] 16x16
UV_BODY = uv_face(8.0, 0.0, 16.0, 16.0)

# Arm connection UVs (each arm is 8x8x4 or 4x8x8 or 8x4x8)
# Length along axis is 4 units (8 pixels in 32x32)
# Circumference is 8 units (16 pixels in 32x32)
def make_core_cube():
    return {
        "origin": [-4.0, 4.0, -4.0],
        "size": [8.0, 8.0, 8.0],
        "uv": {
            "up": UV_BODY,
            "down": UV_BODY,
            "north": UV_BODY,
            "south": UV_BODY,
            "east": UV_BODY,
            "west": UV_BODY
        }
    }

def make_arm(direction):
    if direction == "up":
        origin = [-4.0, 12.0, -4.0]
        size = [8.0, 4.0, 8.0]
        uvs = {
            "north": uv_face(0.0, 0.0, 8.0, 4.0),
            "south": uv_face(0.0, 0.0, 8.0, 4.0),
            "east": uv_face(0.0, 0.0, 8.0, 4.0),
            "west": uv_face(0.0, 0.0, 8.0, 4.0),
            "up": UV_BODY,
            "down": UV_BODY
        }
    elif direction == "down":
        origin = [-4.0, 0.0, -4.0]
        size = [8.0, 4.0, 8.0]
        uvs = {
            "north": uv_face(0.0, 12.0, 8.0, 4.0),
            "south": uv_face(0.0, 12.0, 8.0, 4.0),
            "east": uv_face(0.0, 12.0, 8.0, 4.0),
            "west": uv_face(0.0, 12.0, 8.0, 4.0),
            "up": UV_BODY,
            "down": UV_BODY
        }
    elif direction == "north":
        origin = [-4.0, 4.0, -8.0]
        size = [8.0, 8.0, 4.0]
        uvs = {
            "east": uv_face(0.0, 0.0, 8.0, 4.0),
            "west": uv_face(0.0, 0.0, 8.0, 4.0),
            "up": uv_face(0.0, 0.0, 8.0, 4.0),
            "down": uv_face(0.0, 0.0, 8.0, 4.0),
            "north": UV_BODY,
            "south": UV_BODY
        }
    elif direction == "south":
        origin = [-4.0, 4.0, 4.0]
        size = [8.0, 8.0, 4.0]
        uvs = {
            "east": uv_face(0.0, 12.0, 8.0, 4.0),
            "west": uv_face(0.0, 12.0, 8.0, 4.0),
            "up": uv_face(0.0, 12.0, 8.0, 4.0),
            "down": uv_face(0.0, 12.0, 8.0, 4.0),
            "north": UV_BODY,
            "south": UV_BODY
        }
    elif direction == "east":
        origin = [4.0, 4.0, -4.0]
        size = [4.0, 8.0, 8.0]
        uvs = {
            "north": uv_face(0.0, 12.0, 8.0, 4.0),
            "south": uv_face(0.0, 12.0, 8.0, 4.0),
            "up": uv_face(0.0, 12.0, 8.0, 4.0),
            "down": uv_face(0.0, 12.0, 8.0, 4.0),
            "east": UV_BODY,
            "west": UV_BODY
        }
    elif direction == "west":
        origin = [-8.0, 4.0, -4.0]
        size = [4.0, 8.0, 8.0]
        uvs = {
            "north": uv_face(0.0, 0.0, 8.0, 4.0),
            "south": uv_face(0.0, 0.0, 8.0, 4.0),
            "up": uv_face(0.0, 0.0, 8.0, 4.0),
            "down": uv_face(0.0, 0.0, 8.0, 4.0),
            "east": UV_BODY,
            "west": UV_BODY
        }
    else:
        raise ValueError(direction)
    return {"origin": origin, "size": size, "uv": uvs}

def make_flange(direction):
    uv_front = uv_face(22.0, 22.0, 10.0, 10.0)
    uv_edge_thick = uv_face(19.0, 22.0, 2.0, 10.0)
    uv_edge_wide = uv_face(19.0, 22.0, 10.0, 2.0)

    if direction == "up":
        origin = [-5.0, 14.0, -5.0]
        size = [10.0, 2.0, 10.0]
        uvs = {"up": uv_front, "down": uv_front, "north": uv_edge_wide, "south": uv_edge_wide, "east": uv_edge_wide, "west": uv_edge_wide}
    elif direction == "down":
        origin = [-5.0, 0.0, -5.0]
        size = [10.0, 2.0, 10.0]
        uvs = {"up": uv_front, "down": uv_front, "north": uv_edge_wide, "south": uv_edge_wide, "east": uv_edge_wide, "west": uv_edge_wide}
    elif direction == "north":
        origin = [-5.0, 3.0, -8.0]
        size = [10.0, 10.0, 2.0]
        uvs = {"north": uv_front, "south": uv_front, "up": uv_edge_thick, "down": uv_edge_thick, "east": uv_edge_thick, "west": uv_edge_thick}
    elif direction == "south":
        origin = [-5.0, 3.0, 6.0]
        size = [10.0, 10.0, 2.0]
        uvs = {"north": uv_front, "south": uv_front, "up": uv_edge_thick, "down": uv_edge_thick, "east": uv_edge_thick, "west": uv_edge_thick}
    elif direction == "west":
        origin = [-8.0, 3.0, -5.0]
        size = [2.0, 10.0, 10.0]
        uvs = {"west": uv_front, "east": uv_front, "up": uv_edge_thick, "down": uv_edge_thick, "north": uv_edge_thick, "south": uv_edge_thick}
    elif direction == "east":
        origin = [6.0, 3.0, -5.0]
        size = [2.0, 10.0, 10.0]
        uvs = {"west": uv_front, "east": uv_front, "up": uv_edge_thick, "down": uv_edge_thick, "north": uv_edge_thick, "south": uv_edge_thick}
    else:
        raise ValueError(direction)
    return {"origin": origin, "size": size, "uv": uvs}

DIRS = ["down", "up", "north", "south", "east", "west"]
DIR_MAP = {"d": "down", "u": "up", "n": "north", "s": "south", "e": "east", "w": "west"}

def build_cubes_for_active(active_dirs):
    # active_dirs is a set/list of strings among DIRS
    cubes = []
    count = len(active_dirs)

    # Standalone pipe (no connections): looks like Create mod's pipe item (straight along Y with top & bottom flanges)
    if count == 0:
        cubes.append(make_core_cube())
        cubes.append(make_arm("up"))
        cubes.append(make_arm("down"))
        cubes.append(make_flange("up"))
        cubes.append(make_flange("down"))
        return cubes

    # Always add central core
    cubes.append(make_core_cube())

    # Add arms for all active directions
    for d in active_dirs:
        cubes.append(make_arm(d))

    # Determine flange placement
    # 1. Single connection (dead end / open end): add flange on the connected side
    if count == 1:
        d = next(iter(active_dirs))
        cubes.append(make_flange(d))
    # 2. Elbow (count == 2 and not opposite axis): add flanges on both connection ends!
    elif count == 2:
        is_straight = (
            ("up" in active_dirs and "down" in active_dirs) or
            ("east" in active_dirs and "west" in active_dirs) or
            ("north" in active_dirs and "south" in active_dirs)
        )
        if not is_straight:
            # It's an elbow! Add flanges on both ends matching Create Mod's elbow model
            for d in active_dirs:
                cubes.append(make_flange(d))
        # If straight: continuous seamless pipe without flanges

    return cubes

def main():
    root = Path(r"c:\Users\ibrah\Downloads\crt aro")
    target_geo = root / "create_cogwheel_rp" / "models" / "blocks" / "fluid_pipe.geo.json"

    # All 64 combinations
    import itertools
    all_geos = []

    # Map of key -> cubes
    shape_to_cubes = {}

    for r in range(7):
        for combo in itertools.combinations(["d", "u", "n", "s", "e", "w"], r):
            key = "_".join(combo) if combo else "none"
            active_dirs = [DIR_MAP[k] for k in combo]
            cubes = build_cubes_for_active(active_dirs)
            shape_to_cubes[key] = cubes

            geo_id = "geometry.create.pipe_" + key
            all_geos.append({
                "description": {
                    "identifier": geo_id,
                    "texture_width": 32,
                    "texture_height": 32,
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
            })

    # Add aliases for legacy / compatibility
    aliases = {
        "geometry.create.fluid_pipe": shape_to_cubes["none"],
        "geometry.create.pipe_hub": shape_to_cubes["d_u_n_s_e_w"],
        "geometry.create.pipe_straight": shape_to_cubes["d_u"],
        "geometry.create.pipe_elbow": shape_to_cubes["s_w"],
        "geometry.create.pipe_straight_y": shape_to_cubes["d_u"],
        "geometry.create.pipe_straight_x": shape_to_cubes["e_w"],
        "geometry.create.pipe_straight_z": shape_to_cubes["n_s"],
        "geometry.create.pipe_elbow_us": shape_to_cubes["u_s"],
        "geometry.create.pipe_elbow_un": shape_to_cubes["u_n"],
        "geometry.create.pipe_elbow_ue": shape_to_cubes["u_e"],
        "geometry.create.pipe_elbow_uw": shape_to_cubes["u_w"],
        "geometry.create.pipe_elbow_ds": shape_to_cubes["d_s"],
        "geometry.create.pipe_elbow_dn": shape_to_cubes["d_n"],
        "geometry.create.pipe_elbow_de": shape_to_cubes["d_e"],
        "geometry.create.pipe_elbow_dw": shape_to_cubes["d_w"],
        "geometry.create.pipe_elbow_se": shape_to_cubes["s_e"],
        "geometry.create.pipe_elbow_sw": shape_to_cubes["s_w"],
        "geometry.create.pipe_elbow_ne": shape_to_cubes["n_e"],
        "geometry.create.pipe_elbow_nw": shape_to_cubes["n_w"],
    }

    for alias_id, cubes in aliases.items():
        all_geos.append({
            "description": {
                "identifier": alias_id,
                "texture_width": 32,
                "texture_height": 32,
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
        })

    payload = {
        "format_version": "1.12.0",
        "minecraft:geometry": all_geos
    }

    with open(target_geo, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {len(all_geos)} geometries into {target_geo}!")

if __name__ == "__main__":
    main()
