import os
import json
import shutil

BASE_DIR = r"c:\Users\ibrah\Downloads\crt aro"
RP_DIR = os.path.join(BASE_DIR, "create_cogwheel_rp")
BP_DIR = os.path.join(BASE_DIR, "create_cogwheel_bp")

ROAMING_BP = r"C:\Users\ibrah\AppData\Roaming\Minecraft Bedrock\Users\Shared\games\com.mojang\behavior_packs\CreateCros"
ROAMING_RP = r"C:\Users\ibrah\AppData\Roaming\Minecraft Bedrock\Users\Shared\games\com.mojang\resource_packs\CreateCros"

# 1. Update cogwheel.animation.json to use query.variant
anim_content = {
    "format_version": "1.8.0",
    "animations": {
        "animation.create.cogwheel.spin": {
            "loop": True,
            "bones": {
                "cog": {
                    "rotation": [
                        0,
                        0,
                        "query.variant * query.life_time * 192.0"
                    ]
                },
                "shaft": {
                    "rotation": [
                        0,
                        0,
                        "query.variant * query.life_time * 192.0"
                    ]
                }
            }
        }
    }
}
with open(os.path.join(RP_DIR, "animations", "cogwheel.animation.json"), "w") as f:
    json.dump(anim_content, f, indent=2)

# 2. Update entities with variant component groups
def build_entity(ident):
    return {
        "format_version": "1.20.10",
        "minecraft:entity": {
            "description": {
                "identifier": ident,
                "is_spawnable": True,
                "is_summonable": True
            },
            "component_groups": {
                "stopped_state": {
                    "minecraft:variant": { "value": 0 }
                },
                "spinning_state": {
                    "minecraft:variant": { "value": 1 }
                },
                "turbo_state": {
                    "minecraft:variant": { "value": 4 }
                }
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
                },
                "minecraft:variant": {
                    "value": 1
                },
                "minecraft:interact": {
                    "interactions": [
                        {
                            "on_interact": {
                                "filters": {
                                    "all_of": [
                                        { "test": "has_equipment", "subject": "other", "domain": "hand", "value": "create:wrench" }
                                    ]
                                },
                                "event": "event_toggle_brake"
                            },
                            "use_item": False,
                            "interact_text": "Toggle Brake"
                        }
                    ]
                }
            },
            "events": {
                "event_speed_stop": {
                    "remove": { "component_groups": ["spinning_state", "turbo_state"] },
                    "add": { "component_groups": ["stopped_state"] }
                },
                "event_speed_32": {
                    "remove": { "component_groups": ["stopped_state", "turbo_state"] },
                    "add": { "component_groups": ["spinning_state"] }
                },
                "event_speed_128": {
                    "remove": { "component_groups": ["stopped_state", "spinning_state"] },
                    "add": { "component_groups": ["turbo_state"] }
                },
                "event_toggle_brake": {
                    "sequence": [
                        {
                            "filters": {
                                "test": "has_component",
                                "subject": "self",
                                "operator": "!=",
                                "value": "minecraft:variant"
                            },
                            "add": { "component_groups": ["stopped_state"] }
                        },
                        {
                            "add": { "component_groups": ["stopped_state"] }
                        }
                    ]
                }
            }
        }
    }

for ident in ["create:cogwheel", "create:cogwheel_v2"]:
    filename = "cogwheel_v2.json" if "v2" in ident else "cogwheel.json"
    with open(os.path.join(BP_DIR, "entities", filename), "w") as f:
        json.dump(build_entity(ident), f, indent=2)

# 3. Update functions with proper newlines and event triggers
with open(os.path.join(BP_DIR, "functions", "stop.mcfunction"), "w", encoding="utf-8") as f:
    f.write("event entity @e[type=create:cogwheel] event_speed_stop\n")
    f.write("event entity @e[type=create:cogwheel_v2] event_speed_stop\n")
    f.write('tellraw @a {"rawtext":[{"text":"§c[Create Engine] §lBRAKE ENGAGED! §r§7Cogwheel frozen at 0 RPM."}]}\n')

with open(os.path.join(BP_DIR, "functions", "spin.mcfunction"), "w", encoding="utf-8") as f:
    f.write("event entity @e[type=create:cogwheel] event_speed_32\n")
    f.write("event entity @e[type=create:cogwheel_v2] event_speed_32\n")
    f.write('tellraw @a {"rawtext":[{"text":"§a[Create Engine] §lBRAKE RELEASED! §r§7Rotating at 32 RPM."}]}\n')

with open(os.path.join(BP_DIR, "functions", "fast.mcfunction"), "w", encoding="utf-8") as f:
    f.write("event entity @e[type=create:cogwheel] event_speed_128\n")
    f.write("event entity @e[type=create:cogwheel_v2] event_speed_128\n")
    f.write('tellraw @a {"rawtext":[{"text":"§e[Create Engine] §lTURBO MODE! §r§7Rotating at 128 RPM."}]}\n')

with open(os.path.join(BP_DIR, "functions", "wrench.mcfunction"), "w", encoding="utf-8") as f:
    f.write("give @s create:wrench 1\n")
    f.write('tellraw @s {"rawtext":[{"text":"§6[Create] §aGave you 1x Create Wrench! Right-click any cogwheel to toggle the brake."}]}\n')

with open(os.path.join(BP_DIR, "functions", "check.mcfunction"), "w", encoding="utf-8") as f:
    f.write('tellraw @a {"rawtext":[{"text":"§6========================================\\n§6[Create Engine] §aVariant Sync Engine Active!\\n§e- /function spin (32 RPM)\\n§e- /function fast (128 RPM Turbo)\\n§e- /function stop (0 RPM Brake)\\n§6========================================"}]}\n')

# 4. Copy directly to Roaming CreateCros
shutil.copytree(BP_DIR, ROAMING_BP, dirs_exist_ok=True)
shutil.copytree(RP_DIR, ROAMING_RP, dirs_exist_ok=True)
print("Applied variant sync fix to all directories successfully!")
