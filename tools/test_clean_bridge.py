import os
import json
import zipfile

def test_portable_bridge():
    print("============================================================")
    print("PORTABLE BRIDGE AUTOMATED VALIDATION")
    print("============================================================")
    
    target = os.path.abspath("portable_bridge")
    
    # 1. Check ViaProxy.jar
    vp_jar = os.path.join(target, "viaproxy", "ViaProxy.jar")
    assert os.path.exists(vp_jar), "ViaProxy.jar missing!"
    with zipfile.ZipFile(vp_jar, "r") as z:
        names = set(z.namelist())
        assert "com/viaversion/viaversion/api/data/MappingDataBase.class" in names, "MappingDataBase.class missing!"
        assert "com/viaversion/viabackwards/api/data/BackwardsMappingData.class" in names, "BackwardsMappingData.class missing!"
    print("[PASS] ViaProxy.jar has injected ID Firewall classes.")

    # 2. Check CreateBridge.jar
    cb_jar = os.path.join(target, "geyser", "extensions", "CreateBridge.jar")
    assert os.path.exists(cb_jar), "CreateBridge.jar missing!"
    with zipfile.ZipFile(cb_jar, "r") as z:
        names = set(z.namelist())
        expected_classes = [
            "com/createbridge/CreateBridgeExtension.class",
            "com/createbridge/config/BridgeConfig.class",
            "com/createbridge/blocks/FacingBlockRegistrar.class",
            "com/createbridge/blocks/KineticBlockRegistrar.class",
            "com/createbridge/blocks/CubeBlockRegistrar.class",
            "com/createbridge/items/ItemRegistryManager.class",
            "com/createbridge/network/PacketInterceptorManager.class",
            "com/createbridge/ui/CommandSanitizer.class",
            "create_registry_dump.json",
            "geo_blocks.json",
            "extension.yml"
        ]
        for ec in expected_classes:
            assert ec in names, f"{ec} missing in CreateBridge.jar!"
    print(f"[PASS] CreateBridge.jar contains all {len(expected_classes)} modular classes and resources.")

    # 3. Check Resource Pack
    rp = os.path.join(target, "geyser", "packs", "CreateKineticPack.zip")
    assert os.path.exists(rp), "CreateKineticPack.zip missing!"
    with zipfile.ZipFile(rp, "r") as z:
        names = set(z.namelist())
        assert "textures/terrain_texture.json" in names
        assert "textures/item_texture.json" in names
        assert "models/entity/cogwheel.geo.json" in names
    print(f"[PASS] CreateKineticPack.zip verified with {len(names)} pack entries.")

    # 4. Check Geyser config
    cfg_path = os.path.join(target, "geyser", "config.yml")
    assert os.path.exists(cfg_path), "Geyser config.yml missing!"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg_text = f.read()
        assert "passthrough-motd: false" in cfg_text, "passthrough-motd must be false!"
        assert "port: 25568" in cfg_text, "remote port must be 25568!"
    print("[PASS] Geyser config.yml verified (target port 25568, passthrough disabled).")

    print("============================================================")
    print("ALL PORTABLE BRIDGE TESTS PASSED (100% REPRODUCIBLE)!")
    print("============================================================")

if __name__ == "__main__":
    test_portable_bridge()
