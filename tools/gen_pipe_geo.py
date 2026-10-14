import json

geo = {
  "format_version": "1.12.0",
  "minecraft:geometry": [
    {
      "description": {
        "identifier": "geometry.create.pipe_straight",
        "texture_width": 32,
        "texture_height": 32,
        "visible_bounds_width": 2,
        "visible_bounds_height": 2,
        "visible_bounds_offset": [0, 0.5, 0]
      },
      "bones": [
        {
          "name": "root",
          "pivot": [0, 8, 0],
          "cubes": [
            {
              "origin": [-4.0, 0.0, -4.0],
              "size": [8.0, 16.0, 8.0],
              "uv": {
                "up": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "down": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "north": {"uv": [0.0, 0.0], "uv_size": [8.0, 16.0]},
                "south": {"uv": [0.0, 0.0], "uv_size": [8.0, 16.0]},
                "east": {"uv": [0.0, 0.0], "uv_size": [8.0, 16.0]},
                "west": {"uv": [0.0, 0.0], "uv_size": [8.0, 16.0]}
              }
            }
          ]
        }
      ]
    },
    {
      "description": {
        "identifier": "geometry.create.pipe_elbow",
        "texture_width": 32,
        "texture_height": 32,
        "visible_bounds_width": 2,
        "visible_bounds_height": 2,
        "visible_bounds_offset": [0, 0.5, 0]
      },
      "bones": [
        {
          "name": "root",
          "pivot": [0, 8, 0],
          "cubes": [
            {
              "origin": [-4.0, 4.0, -4.0],
              "size": [8.0, 8.0, 8.0],
              "uv": {
                "up": {"uv": [0.0, 0.0], "uv_size": [8.0, 8.0]},
                "down": {"uv": [0.0, 0.0], "uv_size": [8.0, 8.0]},
                "north": {"uv": [0.0, 0.0], "uv_size": [8.0, 8.0]},
                "south": {"uv": [0.0, 0.0], "uv_size": [8.0, 8.0]},
                "east": {"uv": [0.0, 0.0], "uv_size": [8.0, 8.0]},
                "west": {"uv": [0.0, 0.0], "uv_size": [8.0, 8.0]}
              }
            },
            {
              "origin": [-4.0, 12.0, -4.0],
              "size": [8.0, 4.0, 8.0],
              "uv": {
                "up": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "north": {"uv": [0.0, 0.0], "uv_size": [8.0, 4.0]},
                "south": {"uv": [0.0, 0.0], "uv_size": [8.0, 4.0]},
                "east": {"uv": [0.0, 0.0], "uv_size": [8.0, 4.0]},
                "west": {"uv": [0.0, 0.0], "uv_size": [8.0, 4.0]}
              }
            },
            {
              "origin": [-4.0, 4.0, 4.0],
              "size": [8.0, 8.0, 4.0],
              "uv": {
                "south": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "up": {"uv": [0.0, 0.0], "uv_size": [8.0, 4.0]},
                "down": {"uv": [0.0, 0.0], "uv_size": [8.0, 4.0]},
                "east": {"uv": [0.0, 0.0], "uv_size": [4.0, 8.0]},
                "west": {"uv": [0.0, 0.0], "uv_size": [4.0, 8.0]}
              }
            }
          ]
        }
      ]
    },
    {
      "description": {
        "identifier": "geometry.create.pipe_hub",
        "texture_width": 32,
        "texture_height": 32,
        "visible_bounds_width": 2,
        "visible_bounds_height": 2,
        "visible_bounds_offset": [0, 0.5, 0]
      },
      "bones": [
        {
          "name": "root",
          "pivot": [0, 8, 0],
          "cubes": [
            {
              "origin": [-4.0, 4.0, -4.0],
              "size": [8.0, 8.0, 8.0],
              "uv": {
                "up": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "down": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "north": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "south": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "east": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "west": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]}
              }
            }
          ]
        }
      ]
    },
    {
      "description": {
        "identifier": "geometry.create.fluid_pipe",
        "texture_width": 32,
        "texture_height": 32,
        "visible_bounds_width": 2,
        "visible_bounds_height": 2,
        "visible_bounds_offset": [0, 0.5, 0]
      },
      "bones": [
        {
          "name": "root",
          "pivot": [0, 8, 0],
          "cubes": [
            {
              "origin": [-4.0, 4.0, -4.0],
              "size": [8.0, 8.0, 8.0],
              "uv": {
                "up": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "down": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "north": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "south": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "east": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]},
                "west": {"uv": [24.0, 8.0], "uv_size": [8.0, 8.0]}
              }
            }
          ]
        }
      ]
    }
  ]
}

with open("create_cogwheel_rp/models/blocks/fluid_pipe.geo.json", "w", encoding="utf-8") as f:
    json.dump(geo, f, indent=2)

print("Generated clean fluid_pipe.geo.json with straight, elbow, and hub geometries!")
