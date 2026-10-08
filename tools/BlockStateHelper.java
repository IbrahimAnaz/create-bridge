package org.geysermc.geyser.level.block.type;

import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import org.geysermc.geyser.level.block.Blocks;
import org.geysermc.geyser.registry.BlockRegistries;

public class BlockStateHelper {
    private static final Int2ObjectOpenHashMap<BlockState> MODDED_STATES = new Int2ObjectOpenHashMap<>();

    public static synchronized BlockState of(int id) {
        BlockState state = BlockRegistries.BLOCK_STATES.get(id);
        if (state != null) {
            return state;
        }
        if (id >= 25000) {
            return MODDED_STATES.computeIfAbsent(id, k -> new BlockState(Blocks.STONE, k));
        }
        return BlockRegistries.BLOCK_STATES.get(0);
    }
}
