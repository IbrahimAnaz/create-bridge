package org.geysermc.geyser.util;

import org.cloudburstmc.math.vector.Vector3i;
import org.cloudburstmc.protocol.bedrock.data.definitions.BlockDefinition;
import org.cloudburstmc.protocol.bedrock.packet.UpdateBlockPacket;
import org.geysermc.geyser.level.block.type.BlockState;
import org.geysermc.geyser.session.GeyserSession;

public class BlockUpdateHelper {
    public static void update(GeyserSession session, int blockState, Vector3i position) {
        if (blockState >= 25000) {
            BlockDefinition bedrockBlock = session.getBlockMappings().getBedrockBlock(blockState);
            UpdateBlockPacket packet = new UpdateBlockPacket();
            packet.setDataLayer(0);
            packet.setBlockPosition(position);
            packet.setDefinition(bedrockBlock);
            packet.getFlags().add(UpdateBlockPacket.Flag.NEIGHBORS);
            packet.getFlags().add(UpdateBlockPacket.Flag.NETWORK);
            session.sendUpstreamPacket(packet);
        } else {
            ChunkUtils.updateBlockClientSide(session, BlockState.of(blockState), position);
        }
    }
}
