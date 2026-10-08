import os
import json
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RP_DIR = os.path.join(BASE_DIR, "create_cogwheel_rp")
BP_DIR = os.path.join(BASE_DIR, "create_cogwheel_bp")

def add_wrench_texture():
    os.makedirs(os.path.join(RP_DIR, "textures", "items", "create"), exist_ok=True)
    
    # 32x32 crisp pixel art Create Wrench
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    brass_main = (235, 175, 45, 255)
    brass_dark = (180, 120, 25, 255)
    brass_light = (255, 215, 95, 255)
    wood_handle = (130, 90, 50, 255)
    wood_dark = (90, 60, 30, 255)
    metal_screw = (100, 110, 115, 255)

    # 1. Wooden handle along bottom-left diagonal
    for i in range(12):
        x = 5 + i
        y = 26 - i
        img.putpixel((x, y), wood_handle)
        img.putpixel((x+1, y), wood_handle)
        img.putpixel((x, y+1), wood_dark)
        img.putpixel((x+1, y-1), brass_light)

    # 2. Brass shaft
    for i in range(12, 18):
        x = 5 + i
        y = 26 - i
        img.putpixel((x, y), brass_main)
        img.putpixel((x+1, y), brass_main)
        img.putpixel((x, y+1), brass_dark)
        img.putpixel((x+1, y-1), brass_light)

    # 3. Wrench Head (Curved C-jaw around upper right)
    # Pivot center around (22, 9)
    draw.ellipse([18, 5, 28, 15], outline=brass_dark, width=3)
    draw.ellipse([19, 6, 27, 14], fill=brass_main)
    # Cutout jaw opening
    for x in range(23, 29):
        for y in range(3, 9):
            img.putpixel((x, y), (0, 0, 0, 0))

    # Center screw bolt
    img.putpixel((21, 10), metal_screw)
    img.putpixel((22, 10), metal_screw)
    img.putpixel((21, 11), metal_screw)
    img.putpixel((22, 11), metal_screw)

    wrench_path = os.path.join(RP_DIR, "textures", "items", "create", "wrench.png")
    img.save(wrench_path)
    print(f"Created wrench texture: {wrench_path}")

def add_item_texture_json():
    item_tex = {
        "resource_pack_name": "create_cogwheel_rp",
        "texture_name": "atlas.items",
        "texture_data": {
            "create_wrench": {
                "textures": "textures/items/create/wrench"
            }
        }
    }
    with open(os.path.join(RP_DIR, "textures", "item_texture.json"), "w") as f:
        json.dump(item_tex, f, indent=2)
    print("Created item_texture.json")

def add_item_bp():
    os.makedirs(os.path.join(BP_DIR, "items"), exist_ok=True)
    item_def = {
        "format_version": "1.20.10",
        "minecraft:item": {
            "description": {
                "identifier": "create:wrench",
                "menu_category": {
                    "category": "items"
                }
            },
            "components": {
                "minecraft:icon": "create_wrench",
                "minecraft:display_name": {
                    "value": "§6Create Wrench §7[Dev Tool]"
                },
                "minecraft:hand_equipped": True,
                "minecraft:max_stack_size": 1
            }
        }
    }
    with open(os.path.join(BP_DIR, "items", "wrench.json"), "w") as f:
        json.dump(item_def, f, indent=2)
    print("Created BP item: wrench.json")

def update_entities_with_wrench_interaction():
    # Update both cogwheel entities so right-clicking with create:wrench toggles the brake
    for ident in ["cogwheel", "cogwheel_v2"]:
        p = os.path.join(BP_DIR, "entities", f"{ident}.json")
        full_id = f"create:{ident}"
        ent_json = {
            "format_version": "1.20.10",
            "minecraft:entity": {
                "description": {
                    "identifier": full_id,
                    "is_spawnable": True,
                    "is_summonable": True
                },
                "component_groups": {
                    "stopped_state": {
                        "minecraft:type_family": {
                            "family": ["create", "inanimate", "stopped"]
                        }
                    },
                    "spinning_state": {
                        "minecraft:type_family": {
                            "family": ["create", "inanimate", "spinning"]
                        }
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
                        "family": ["create", "inanimate", "spinning"]
                    },
                    "minecraft:interact": {
                        "interactions": [
                            {
                                "on_interact": {
                                    "filters": {
                                        "all_of": [
                                            {
                                                "test": "is_family",
                                                "subject": "self",
                                                "value": "spinning"
                                            },
                                            {
                                                "test": "has_equipment",
                                                "subject": "other",
                                                "domain": "hand",
                                                "value": "create:wrench"
                                            }
                                        ]
                                    },
                                    "event": "event_toggle_brake"
                                },
                                "use_item": False,
                                "interact_text": "Engage Brake"
                            },
                            {
                                "on_interact": {
                                    "filters": {
                                        "all_of": [
                                            {
                                                "test": "is_family",
                                                "subject": "self",
                                                "value": "stopped"
                                            },
                                            {
                                                "test": "has_equipment",
                                                "subject": "other",
                                                "domain": "hand",
                                                "value": "create:wrench"
                                            }
                                        ]
                                    },
                                    "event": "event_release_brake"
                                },
                                "use_item": False,
                                "interact_text": "Release Brake"
                            }
                        ]
                    }
                },
                "events": {
                    "event_toggle_brake": {
                        "add": { "component_groups": ["stopped_state"] },
                        "remove": { "component_groups": ["spinning_state"] },
                        "queue_command": {
                            "command": [
                                f"tag @s add stop",
                                "tellraw @a {\"rawtext\":[{\"text\":\"§c[Create Wrench] §lBRAKE ENGAGED! §r§7Cogwheel halted.\"}]}"
                            ]
                        }
                    },
                    "event_release_brake": {
                        "add": { "component_groups": ["spinning_state"] },
                        "remove": { "component_groups": ["stopped_state"] },
                        "queue_command": {
                            "command": [
                                f"tag @s remove stop",
                                "tellraw @a {\"rawtext\":[{\"text\":\"§a[Create Wrench] §lBRAKE RELEASED! §r§7Cogwheel resumed spinning.\"}]}"
                            ]
                        }
                    }
                }
            }
        }
        with open(p, "w") as f:
            json.dump(ent_json, f, indent=2)
        print(f"Updated entity with wrench interaction: {p}")

def update_functions():
    with open(os.path.join(BP_DIR, "functions", "check.mcfunction"), "w", encoding="utf-8") as f:
        f.write('tellraw @a {"rawtext":[{"text":"§6========================================\\n§6[Create Engine] §aDev Pipeline Active!\\n§e- Test Item: §6Create Wrench (/give @s create:wrench)\\n§e- How to test: §fRight-click cogwheel with wrench to toggle brake!\\n§6========================================"}]}\\n')

    with open(os.path.join(BP_DIR, "functions", "wrench.mcfunction"), "w", encoding="utf-8") as f:
        f.write('give @s create:wrench 1\\n')
        f.write('tellraw @s {"rawtext":[{"text":"§6[Create] §aGave you 1x Create Wrench! Right-click any cogwheel to toggle the brake."}]}\\n')

if __name__ == "__main__":
    add_wrench_texture()
    add_item_texture_json()
    add_item_bp()
    update_entities_with_wrench_interaction()
    update_functions()
    print("Done! Test item and wrench interactions deployed directly through dev junctions!")
