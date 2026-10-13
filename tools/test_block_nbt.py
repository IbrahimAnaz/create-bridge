import subprocess
import os

java_code = """
import org.geysermc.geyser.level.block.GeyserCustomBlockComponents;
import org.geysermc.geyser.level.block.GeyserNonVanillaCustomBlockData;
import org.geysermc.geyser.level.block.GeyserGeometryComponent;
import org.geysermc.geyser.level.block.GeyserMaterialInstance;
import org.geysermc.geyser.registry.populator.CustomBlockRegistryPopulator;
import org.geysermc.geyser.api.block.custom.CustomBlockData;
import org.cloudburstmc.protocol.bedrock.data.BlockPropertyData;
import java.lang.reflect.Method;

public class TestBlockNbt {
    public static void main(String[] args) throws Exception {
        var geo = new GeyserGeometryComponent.Builder().identifier("geometry.create.andesite_casing").build();
        var mat = new GeyserMaterialInstance.Builder().texture("create_andesite_casing").build();
        var comps = new GeyserCustomBlockComponents.Builder()
            .geometry(geo)
            .materialInstance("*", mat)
            .build();
        var data = new GeyserNonVanillaCustomBlockData.Builder()
            .namespace("create")
            .name("andesite_casing")
            .components(comps)
            .build();
            
        System.out.println("Data identifier: " + data.identifier());
        Method m = CustomBlockRegistryPopulator.class.getDeclaredMethod("generateBlockPropertyData", CustomBlockData.class);
        m.setAccessible(true);
        BlockPropertyData bpd = (BlockPropertyData) m.invoke(null, data);
        System.out.println("BPD name: " + bpd.getName());
    }
}
"""

with open("TestBlockNbt.java", "w") as f:
    f.write(java_code)

subprocess.run(["javac", "-cp", "portable_bridge/geyser/Geyser-Standalone.jar", "TestBlockNbt.java"], check=True)
res = subprocess.run(["java", "-cp", ".;portable_bridge/geyser/Geyser-Standalone.jar", "TestBlockNbt"], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("ERR:", res.stderr)

if os.path.exists("TestBlockNbt.java"):
    os.remove("TestBlockNbt.java")
if os.path.exists("TestBlockNbt.class"):
    os.remove("TestBlockNbt.class")
