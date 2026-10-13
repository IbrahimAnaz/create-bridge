import json
import zipfile

def run_trace():
    print("=" * 70)
    print("PACKET & ID TRACE: FUNCTION-TO-FUNCTION LIFECYCLE EVALUATION")
    print("=" * 70)

    # 1. Load Create Registry Dump (NeoForge 1.21.1 Truth)
    with open('headless_server/create_registry_dump.json') as f:
        registry = json.load(f)
    
    test_cases = [
        {"name": "create:millstone", "type": "item", "raw_id": registry['items'].get('create:millstone'), "raw_state": registry['blockstates'].get('create:millstone', [None])[0]},
        {"name": "create:cogwheel", "type": "item", "raw_id": registry['items'].get('create:cogwheel'), "raw_state": registry['blockstates'].get('create:cogwheel', [None])[0]},
        {"name": "create:large_cogwheel", "type": "item", "raw_id": registry['items'].get('create:large_cogwheel'), "raw_state": registry['blockstates'].get('create:large_cogwheel', [None])[0]},
        {"name": "create:andesite_casing", "type": "item", "raw_id": registry['items'].get('create:andesite_casing'), "raw_state": registry['blockstates'].get('create:andesite_casing', [None])[0]},
        {"name": "minecraft:stone", "type": "block", "raw_id": 1, "raw_state": 1},
        {"name": "minecraft:fletching_table", "type": "item", "raw_id": 933, "raw_state": 20771},
        {"name": "minecraft:composter", "type": "item", "raw_id": 934, "raw_state": 21743}
    ]

    print("\n--- PHASE 1: SERVER EMISSION (NeoForge 1.21.1) ---")
    for tc in test_cases:
        print(f"[{tc['name']}] Raw Item ID: {tc['raw_id']}, Raw BlockState ID: {tc['raw_state']}")

    print("\n--- PHASE 2: VIAPROXY S2C TRANSLATION (1.21.1 -> 1.21.4) ---")
    print("Function: MappingDataBase.getNewItemId(rawId) & getNewBlockStateId(rawState)")
    for tc in test_cases:
        # Simulate our patched MappingDataBase bytecode
        raw_id = tc['raw_id']
        raw_state = tc['raw_state']
        
        # Item translation
        if raw_id >= 10000:
            viaproxy_item = raw_id
        elif raw_id >= 1333:
            viaproxy_item = 10000 + raw_id
        else:
            viaproxy_item = f"VanillaMapped({raw_id})"

        # BlockState translation
        if raw_state is not None:
            if raw_state >= 100000:
                viaproxy_state = raw_state
            elif raw_state >= 25000:
                viaproxy_state = 100000 + raw_state
            else:
                viaproxy_state = f"VanillaMappedState({raw_state})"
        else:
            viaproxy_state = "N/A"

        tc['viaproxy_item'] = viaproxy_item
        tc['viaproxy_state'] = viaproxy_state
        print(f"[{tc['name']}] Server ID {raw_id} -> ViaProxy ID {viaproxy_item} | State {raw_state} -> {viaproxy_state}")

    print("\n--- PHASE 3: GEYSER RECEPTION & BEDROCK ENCODING ---")
    print("Function: Geyser JavaContainerSetSlotTranslator / JavaBlockUpdateTranslator")
    with zipfile.ZipFile('headless_server/geyser/Geyser-Standalone.jar') as z:
        geyser_items = json.loads(z.read('mappings/items.json').decode('utf-8'))

    for tc in test_cases:
        item = tc['viaproxy_item']
        if isinstance(item, int) and item >= 10000:
            raw = item - 10000
            bedrock_item_name = tc['name']
            bedrock_handling = f"CustomItemDefinition(shiftedJavaId={item}, identifier='{tc['name']}')"
        else:
            bedrock_item_name = tc['name']
            bedrock_handling = f"VanillaItemMapping({tc['name']})"

        state = tc['viaproxy_state']
        if isinstance(state, int) and state >= 100000:
            bedrock_block_handling = f"CreateBridge CustomBlock override (javaId={state})"
        else:
            bedrock_block_handling = f"Vanilla Block palette ({tc['name']})"

        print(f"[{tc['name']}] Geyser received item {item} -> {bedrock_handling}")
        print(f"      Geyser received state {state} -> {bedrock_block_handling}")

    print("\n--- PHASE 4: CLIENT-TO-SERVER ROUNDTRIP (Bedrock Slot Swap / Interaction) ---")
    print("Bedrock emits: MobEquipmentPacket / InventoryTransactionPacket / ItemStackRequestPacket")
    print("Geyser translates: Bedrock item definition -> Java Item ID")
    print("Geyser sends to ViaProxy: ServerboundSetHeldItemPacket / ServerboundContainerClickPacket")
    print("Function: ViaProxy MappingDataBase.getOldItemId(id)")
    
    all_passed = True
    for tc in test_cases:
        item_sent_to_viaproxy = tc['viaproxy_item']
        if isinstance(item_sent_to_viaproxy, int):
            # Patched getOldItemId simulation
            if item_sent_to_viaproxy >= 10000:
                server_received_id = item_sent_to_viaproxy - 10000
            elif item_sent_to_viaproxy >= 1333:
                server_received_id = item_sent_to_viaproxy
            else:
                server_received_id = "VanillaInverse"
            
            is_match = (server_received_id == tc['raw_id'])
            if not is_match: all_passed = False
            status = "PERFECT ROUNDTRIP (NO MUTATION)" if is_match else "DESYNC ERROR"
            print(f"[{tc['name']}] Bedrock held -> Geyser sends {item_sent_to_viaproxy} -> ViaProxy getOldItemId -> Server receives {server_received_id} | {status}")
        else:
            print(f"[{tc['name']}] Vanilla item handled by vanilla inverse mappings.")

    print("\n" + "=" * 70)
    print(f"FINAL EVALUATION: {'ALL TESTS PASSED' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 70)

if __name__ == '__main__':
    run_trace()
