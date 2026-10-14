#!/usr/bin/env python3
"""
Generate complete Bedrock geometry definitions for Create fluid pipes.
Eliminates all runtime transformation rotations by generating pre-aligned geometries for all 16 canonical configurations.
"""

import json
import os

def uv_box(u, v, w, h):
    return {"uv": [float(u), float(v)], "uv_size": [float(w), float(h)]}

def make_pipe_cube(origin, size, is_axis='y'):
    """
    Creates a pipe segment cube with proper UVs matching Create mod's pipes.png (32x32).
    """
    u_base = 0.0
    v_base = 0.0
    return {
        "origin": [float(origin[0]), float(origin[1]), float(origin[2])],
        "size": [float(size[0]), float(size[1]), float(size[2])],
        "uv": {
            "up": uv_box(u_base, v_base, size[0], size[2]),
            "down": uv_box(u_base, v_base, size[0], size[2]),
            "north": uv_box(u_base, v_base, size[0], size[1]),
            "south": uv_box(u_base, v_base, size[0], size[1]),
            "east": uv_box(u_base, v_base, size[2], size[1]),
            "west": uv_box(u_base, v_base, size[2], size[1])
        }
    }

def make_flange(direction):
    """
    Creates a 10x10x2 flange rim at the block border for the given direction.
    """
    # Flange UV in 32x32 pipes.png:
    # front/back rim face: u=22, v=22, w=10, h=10
    # rim side: u=19, v=22, w=2, h=10
    uv_front = uv_box(22.0, 22.0, 10.0, 10.0)
    uv_side = uv_box(19.0, 22.0, 2.0, 10.0)

    if direction == "up":
        origin = [-5.0, 14.0, -5.0]
        size = [10.0, 2.0, 10.0]
        uvs = {"up": uv_front, "down": uv_front, "north": uv_side, "south": uv_side, "east": uv_side, "west": uv_side}
    elif direction == "down":
        origin = [-5.0, 0.0, -5.0]
        size = [10.0, 2.0, 10.0]
        uvs = {"up": uv_front, "down": uv_front, "north": uv_side, "south": uv_side, "east": uv_side, "west": uv_side}
    elif direction == "north":
        origin = [-5.0, 3.0, -8.0]
        size = [10.0, 10.0, 2.0]
        uvs = {"north": uv_front, "south": uv_front, "up": uv_side, "down": uv_side, "east": uv_side, "west": uv_side}
    elif direction == "south":
        origin = [-5.0, 3.0, 6.0]
        size = [10.0, 10.0, 2.0]
        uvs = {"north": uv_front, "south": uv_front, "up": uv_side, "down": uv_side, "east": uv_side, "west": uv_side}
    elif direction == "west":
        origin = [-8.0, 3.0, -5.0]
        size = [2.0, 10.0, 10.0]
        uvs = {"west": uv_front, "east": uv_front, "up": uv_side, "down": uv_side, "north": uv_side, "south": uv_side}
    elif direction == "east":
        origin = [6.0, 3.0, -5.0]
        size = [2.0, 10.0, 10.0]
        uvs = {"west": uv_front, "east": uv_front, "up": uv_side, "down": uv_side, "north": uv_side, "south": uv_side}
    else:
        raise ValueError(f"Unknown direction: {direction}")

    return {
        "origin": origin,
        "size": size,
        "uv": uvs
    }

def build_straight(axis):
    cubes = []
    if axis == "y":
        cubes.append(make_pipe_cube([-4.0, 0.0, -4.0], [8.0, 16.0, 8.0], 'y'))
        cubes.append(make_flange("up"))
        cubes.append(make_flange("down"))
    elif axis == "x":
        cubes.append(make_pipe_cube([-8.0, 4.0, -4.0], [16.0, 8.0, 8.0], 'x'))
        cubes.append(make_flange("east"))
        cubes.append(make_flange("west"))
    elif axis == "z":
        cubes.append(make_pipe_cube([-4.0, 4.0, -8.0], [8.0, 8.0, 16.0], 'z'))
        cubes.append(make_flange("north"))
        cubes.append(make_flange("south"))
    return cubes

def build_elbow(d1, d2):
    cubes = []
    # Central core
    cubes.append(make_pipe_cube([-4.0, 4.0, -4.0], [8.0, 8.0, 8.0]))

    # Branch 1
    if d1 == "up":
        cubes.append(make_pipe_cube([-4.0, 12.0, -4.0], [8.0, 4.0, 8.0]))
        cubes.append(make_flange("up"))
    elif d1 == "down":
        cubes.append(make_pipe_cube([-4.0, 0.0, -4.0], [8.0, 4.0, 8.0]))
        cubes.append(make_flange("down"))
    elif d1 == "north":
        cubes.append(make_pipe_cube([-4.0, 4.0, -8.0], [8.0, 8.0, 4.0]))
        cubes.append(make_flange("north"))
    elif d1 == "south":
        cubes.append(make_pipe_cube([-4.0, 4.0, 4.0], [8.0, 8.0, 4.0]))
        cubes.append(make_flange("south"))
    elif d1 == "east":
        cubes.append(make_pipe_cube([4.0, 4.0, -4.0], [4.0, 8.0, 8.0]))
        cubes.append(make_flange("east"))
    elif d1 == "west":
        cubes.append(make_pipe_cube([-8.0, 4.0, -4.0], [4.0, 8.0, 8.0]))
        cubes.append(make_flange("west"))

    # Branch 2
    if d2 == "up":
        cubes.append(make_pipe_cube([-4.0, 12.0, -4.0], [8.0, 4.0, 8.0]))
        cubes.append(make_flange("up"))
    elif d2 == "down":
        cubes.append(make_pipe_cube([-4.0, 0.0, -4.0], [8.0, 4.0, 8.0]))
        cubes.append(make_flange("down"))
    elif d2 == "north":
        cubes.append(make_pipe_cube([-4.0, 4.0, -8.0], [8.0, 8.0, 4.0]))
        cubes.append(make_flange("north"))
    elif d2 == "south":
        cubes.append(make_pipe_cube([-4.0, 4.0, 4.0], [8.0, 8.0, 4.0]))
        cubes.append(make_flange("south"))
    elif d2 == "east":
        cubes.append(make_pipe_cube([4.0, 4.0, -4.0], [4.0, 8.0, 8.0]))
        cubes.append(make_flange("east"))
    elif d2 == "west":
        cubes.append(make_pipe_cube([-8.0, 4.0, -4.0], [4.0, 8.0, 8.0]))
        cubes.append(make_flange("west"))

    return cubes

def build_hub():
    cubes = []
    # Central junction core
    cubes.append(make_pipe_cube([-4.0, 4.0, -4.0], [8.0, 8.0, 8.0]))
    return cubes

def make_geo(identifier, cubes):
    return {
        "description": {
            "identifier": identifier,
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
    }

def main():
    geometries = []

    # 1. Straight lines
    geometries.append(make_geo("geometry.create.pipe_straight_y", build_straight("y")))
    geometries.append(make_geo("geometry.create.pipe_straight_x", build_straight("x")))
    geometries.append(make_geo("geometry.create.pipe_straight_z", build_straight("z")))

    # 2. 12 Corner Elbows
    elbow_defs = {
        "us": ("up", "south"),
        "un": ("up", "north"),
        "ue": ("up", "east"),
        "uw": ("up", "west"),
        "ds": ("down", "south"),
        "dn": ("down", "north"),
        "de": ("down", "east"),
        "dw": ("down", "west"),
        "se": ("south", "east"),
        "sw": ("south", "west"),
        "ne": ("north", "east"),
        "nw": ("north", "west"),
    }
    for code, (d1, d2) in elbow_defs.items():
        geometries.append(make_geo(f"geometry.create.pipe_elbow_{code}", build_elbow(d1, d2)))

    # 3. Hub & Fallbacks
    geometries.append(make_geo("geometry.create.pipe_hub", build_hub()))
    geometries.append(make_geo("geometry.create.fluid_pipe", build_straight("y")))
    geometries.append(make_geo("geometry.create.pipe_straight", build_straight("y")))
    geometries.append(make_geo("geometry.create.pipe_elbow", build_elbow("up", "south")))

    doc = {
        "format_version": "1.12.0",
        "minecraft:geometry": geometries
    }

    out_path = "create_cogwheel_rp/models/blocks/fluid_pipe.geo.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)

    print(f"Generated {len(geometries)} geometries in {out_path} successfully!")

if __name__ == "__main__":
    main()
