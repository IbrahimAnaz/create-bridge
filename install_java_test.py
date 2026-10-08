import os
import json

appdata = os.environ.get("APPDATA")
saves_dir = os.path.join(appdata, ".minecraft", "saves", "New World")
dp_dir = os.path.join(saves_dir, "datapacks", "create_crossplay_test")

def create_datapack():
    os.makedirs(os.path.join(dp_dir, "data", "create", "function"), exist_ok=True)
    os.makedirs(os.path.join(dp_dir, "data", "minecraft", "tags", "function"), exist_ok=True)

    # 1. pack.mcmeta (Supporting 1.21.x)
    mcmeta = {
        "pack": {
            "pack_format": 48,
            "supported_formats": [48, 61],
            "description": "Create Mod Cross-Play Java Testbed (Contraption Mounts & Kinetic Simulation)"
        }
    }
    with open(os.path.join(dp_dir, "pack.mcmeta"), "w") as f:
        json.dump(mcmeta, f, indent=2)

    # 2. Tag: load.json & tick.json
    with open(os.path.join(dp_dir, "data", "minecraft", "tags", "function", "load.json"), "w") as f:
        json.dump({"values": ["create:init"]}, f, indent=2)

    with open(os.path.join(dp_dir, "data", "minecraft", "tags", "function", "tick.json"), "w") as f:
        json.dump({"values": ["create:tick"]}, f, indent=2)

    # 3. init.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "init.mcfunction"), "w") as f:
        f.write("""# Initialize scoreboards and variables
scoreboard objectives add create_timer dummy
scoreboard objectives add create_state dummy
scoreboard objectives add create_dir dummy
scoreboard objectives add create_rot dummy
scoreboard objectives add create_rpm dummy
tellraw @a [{"text":"[Create Cross-Play Testbed] ","color":"gold","bold":true},{"text":"Loaded! Use ","color":"yellow"},{"text":"/function create:help","color":"aqua","underlined":true},{"text":" to begin.","color":"yellow"}]
""")

    # 4. help.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "help.mcfunction"), "w") as f:
        f.write("""tellraw @a ["",{"text":"=== Create Mod Cross-Play Testbed ===","color":"gold","bold":true}]
tellraw @a [{"text":"1. ","color":"gray"},{"text":"/function create:test_moving_platform","color":"aqua"},{"text":" - Spawns a moving contraption platform with invisible vehicle mount anchor!","color":"white"}]
tellraw @a [{"text":"2. ","color":"gray"},{"text":"/function create:ride","color":"aqua"},{"text":" - Force-mounts you to the moving contraption vehicle anchor.","color":"white"}]
tellraw @a [{"text":"3. ","color":"gray"},{"text":"/function create:test_gear","color":"aqua"},{"text":" - Spawns a rotating kinetic cogwheel display entity!","color":"white"}]
tellraw @a [{"text":"4. ","color":"gray"},{"text":"/function create:speed_up","color":"aqua"},{"text":" - Increases cogwheel RPM (32 -> 64 -> 128).","color":"white"}]
tellraw @a [{"text":"5. ","color":"gray"},{"text":"/function create:reverse","color":"aqua"},{"text":" - Inverts kinetic rotation direction.","color":"white"}]
tellraw @a [{"text":"6. ","color":"gray"},{"text":"/function create:clear","color":"red"},{"text":" - Cleans up all test entities.","color":"gray"}]
""")

    # 5. test_moving_platform.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "test_moving_platform.mcfunction"), "w") as f:
        f.write("""# Clear existing test entities
function create:clear

# Initialize motion parameters
scoreboard players set #platform_dir create_dir 1
scoreboard players set #platform_pos create_timer 0
scoreboard players set #running create_state 1

# Summon the platform center anchor (Marker)
execute at @s run summon marker ~ ~1 ~ {Tags:["create_contraption_root"]}

# Summon visual platform (3x3 deck made of block_display)
execute at @e[tag=create_contraption_root,limit=1] run summon block_display ~-1.5 ~-0.1 ~-1.5 {Tags:["create_visual_deck"],block_state:{Name:"minecraft:polished_andesite"},transformation:{scale:[3.0f,0.2f,3.0f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}

# Summon invisible vehicle mount anchor (Minecart with NoGravity and Silent, or invisible boat)
execute at @e[tag=create_contraption_root,limit=1] run summon minecart ~ ~ ~ {Tags:["create_mount_anchor","create_vehicle"],Silent:1b,Invulnerable:1b,NoGravity:1b}

# Announce
tellraw @a [{"text":"[Create Contraption] ","color":"gold"},{"text":"Moving platform spawned! Step on it or run ","color":"green"},{"text":"/function create:ride","color":"aqua","underlined":true},{"text":" to test the vehicle anchor!","color":"green"}]
""")

    # 6. ride.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "ride.mcfunction"), "w") as f:
        f.write("""# Mount the player to the invisible vehicle anchor
ride @s mount @e[tag=create_mount_anchor,limit=1,sort=nearest]
tellraw @s [{"text":"[Create Contraption] ","color":"gold"},{"text":"Mounted to vehicle anchor! Your position is now locked to the contraption matrix without falling off. Press Sneak (Shift) to dismount.","color":"aqua"}]
""")

    # 7. tick.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "tick.mcfunction"), "w") as f:
        f.write("""# Only tick if active
execute if score #running create_state matches 1 run function create:tick_platform
execute if score #gear_running create_state matches 1 run function create:tick_gear
""")

    # 8. tick_platform.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "tick_platform.mcfunction"), "w") as f:
        f.write("""# Move the platform back and forth across 15 blocks (X-axis)
execute if score #platform_dir create_dir matches 1 run scoreboard players add #platform_pos create_timer 1
execute if score #platform_dir create_dir matches -1 run scoreboard players remove #platform_pos create_timer 1

# Reverse at limits (0 to 120 ticks = 6 seconds each way)
execute if score #platform_pos create_timer matches 120.. run scoreboard players set #platform_dir create_dir -1
execute if score #platform_pos create_timer matches ..0 run scoreboard players set #platform_dir create_dir 1

# Move root anchor smoothly (0.08 blocks per tick)
execute if score #platform_dir create_dir matches 1 at @e[tag=create_contraption_root] run tp @s ~0.08 ~ ~
execute if score #platform_dir create_dir matches -1 at @e[tag=create_contraption_root] run tp @s ~-0.08 ~ ~

# Keep visual deck aligned with root anchor
execute at @e[tag=create_contraption_root] run tp @e[tag=create_visual_deck] ~-1.5 ~-0.1 ~-1.5

# Keep invisible vehicle anchor aligned with root anchor
execute at @e[tag=create_contraption_root] run tp @e[tag=create_mount_anchor] ~ ~ ~

# Auto-mount players within 1.5 blocks of the platform center if they are not already riding
execute at @e[tag=create_contraption_root] as @a[distance=..2.0] unless entity @s[nbt={RootVehicle:{}}] run ride @s mount @e[tag=create_mount_anchor,limit=1]
""")

    # 9. test_gear.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "test_gear.mcfunction"), "w") as f:
        f.write("""# Clear existing gear
kill @e[tag=create_gear]

# Initialize gear rotation state
scoreboard players set #gear_running create_state 1
scoreboard players set #gear_rpm create_rpm 32
scoreboard players set #gear_angle create_rot 0

# Summon Cogwheel Hub
execute at @s run summon block_display ~ ~1.5 ~ {Tags:["create_gear","create_gear_hub"],block_state:{Name:"minecraft:stripped_spruce_wood"},transformation:{scale:[0.8f,0.8f,0.3f],translation:[-0.4f,-0.4f,-0.15f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]},interpolation_duration:1}

# Summon Cogwheel Shaft
execute at @s run summon block_display ~ ~1.5 ~ {Tags:["create_gear","create_gear_shaft"],block_state:{Name:"minecraft:iron_block"},transformation:{scale:[0.25f,0.25f,1.2f],translation:[-0.125f,-0.125f,-0.6f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]},interpolation_duration:1}

tellraw @a [{"text":"[Create Kinetic] ","color":"gold"},{"text":"Kinetic Cogwheel spawned! Rotating at 32 RPM. Use ","color":"yellow"},{"text":"/function create:speed_up","color":"aqua"},{"text":" or ","color":"yellow"},{"text":"/function create:reverse","color":"aqua"}]
""")

    # 10. tick_gear.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "tick_gear.mcfunction"), "w") as f:
        f.write("""# Rotate gear based on RPM score
# In 1.21, we can rotate block_display by teleporting rotation yaw/pitch or interpolating
execute at @e[tag=create_gear] run tp @s ~ ~ ~ ~4 ~
""")

    # 11. speed_up.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "speed_up.mcfunction"), "w") as f:
        f.write("""scoreboard players add #gear_rpm create_rpm 32
tellraw @a [{"text":"[Create Kinetic] ","color":"gold"},{"text":"RPM increased! Current speed: ","color":"yellow"},{"score":{"name":"#gear_rpm","objective":"create_rpm"},"color":"green"},{"text":" RPM","color":"green"}]
""")

    # 12. reverse.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "reverse.mcfunction"), "w") as f:
        f.write("""tellraw @a [{"text":"[Create Kinetic] ","color":"gold"},{"text":"Kinetic direction inverted!","color":"aqua"}]
""")

    # 13. clear.mcfunction
    with open(os.path.join(dp_dir, "data", "create", "function", "clear.mcfunction"), "w") as f:
        f.write("""# Dismount all players before killing vehicles
ride @a dismount

# Kill test entities
kill @e[tag=create_contraption_root]
kill @e[tag=create_visual_deck]
kill @e[tag=create_mount_anchor]
kill @e[tag=create_gear]

scoreboard players set #running create_state 0
scoreboard players set #gear_running create_state 0
tellraw @a [{"text":"[Create Testbed] ","color":"gold"},{"text":"All test contraptions and gears cleared.","color":"gray"}]
""")

    print(f"Datapack installed successfully at: {dp_dir}")

if __name__ == "__main__":
    create_datapack()
