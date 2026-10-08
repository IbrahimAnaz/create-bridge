package tools;

import org.geysermc.geyser.registry.BlockRegistries;
import org.geysermc.geyser.registry.populator.BlockRegistryPopulator;
import org.geysermc.geyser.registry.type.BlockMappings;
import org.geysermc.geyser.registry.type.GeyserBedrockBlock;
import org.geysermc.geyser.network.bedrock.GameProtocol;

public class ProbePalette {
    public static void main(String[] args) {
        org.geysermc.geyser.registry.Registries.populate();
        int version = GameProtocol.DEFAULT_BEDROCK_PROTOCOL;
        BlockMappings bm = BlockRegistries.BLOCKS.forVersion(version);
        System.out.println("Default Bedrock protocol: " + version + " -> BlockMappings: " + (bm != null));
        if (bm != null) {
            int[] testIds = new int[]{32328, 32330, 32342, 27275, 417, 1874, 1878};
            for (int id : testIds) {
                GeyserBedrockBlock bb = bm.getBedrockBlock(id);
                System.out.println("ID " + id + " -> " + (bb != null ? bb.toString() : "null"));
            }
        }
    }
}
