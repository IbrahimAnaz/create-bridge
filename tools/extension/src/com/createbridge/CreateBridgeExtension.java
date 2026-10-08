package com.createbridge;

import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomItemsEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserPostInitializeEvent;
import org.geysermc.geyser.api.event.bedrock.SessionJoinEvent;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;
import org.geysermc.geyser.api.item.custom.NonVanillaCustomItemData;
import org.geysermc.geyser.registry.BlockRegistries;
import org.geysermc.geyser.registry.type.BlockMappings;
import org.geysermc.geyser.registry.type.GeyserBedrockBlock;
import org.geysermc.geyser.network.bedrock.GameProtocol;
import org.geysermc.geyser.session.GeyserSession;

public class CreateBridgeExtension implements Extension {
    private static final int OFFSET = 100000;
    private static final JavaBoundingBox[] CUBE_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.5, 0.5, 0.5, 1.0, 1.0, 1.0)
    };

    @Subscribe
    public void onDefineCustomItems(GeyserDefineCustomItemsEvent event) {
        System.out.println("[CreateBridge] Registering Create custom items with exact Java IDs...");

        registerItem(event, "andesite_casing", 1430, true);
        registerItem(event, "brass_casing", 1431, true);
        registerItem(event, "copper_casing", 1432, true);
        registerItem(event, "railway_casing", 1441, true);
        registerItem(event, "raw_zinc_block", 1675, true);
        registerItem(event, "zinc_block", 1676, true);
        registerItem(event, "brass_block", 1680, true);
        registerItem(event, "large_cogwheel", 1337, true);
        registerItem(event, "cogwheel", 1336, true);
        registerItem(event, "depot", 1365, true);
        registerItem(event, "chute", 1367, true);
        registerItem(event, "schematicannon", 1333, true);
        registerItem(event, "wrench", 1586, false);

        System.out.println("[CreateBridge] Successfully registered Create custom items!");
    }

    private void registerItem(GeyserDefineCustomItemsEvent event, String name, int javaId, boolean isBlock) {
        var builder = NonVanillaCustomItemData.builder()
            .identifier("create:" + name)
            .name(name)
            .javaId(javaId)
            .icon("create_" + name);
        if (isBlock) {
            builder.block("create:" + name);
        }
        event.register(builder.build());
    }

    @Subscribe
    public void onDefineCustomBlocks(GeyserDefineCustomBlocksEvent event) {
        System.out.println("[CreateBridge] Registering Create blocks in Geyser with +100000 offset and collision...");

        registerCube(event, "andesite_casing", "create_andesite_casing", new int[]{32328, 32329});
        registerCube(event, "brass_casing", "create_brass_casing", new int[]{32330, 32331});
        registerCube(event, "copper_casing", "create_copper_casing", new int[]{32332, 32333});
        registerCube(event, "railway_casing", "create_railway_casing", new int[]{32336, 32337});
        registerCube(event, "raw_zinc_block", "create_raw_zinc_block", new int[]{32338});
        registerCube(event, "zinc_block", "create_zinc_block", new int[]{32339});
        registerCube(event, "brass_block", "create_brass_block", new int[]{32342});
        registerCube(event, "large_cogwheel", "create_cogwheel", new int[]{27275, 27289});
        registerCube(event, "depot", "create_brass_casing", new int[]{47909});
        registerCube(event, "chute", "create_andesite_casing", new int[]{46215});
        registerCube(event, "schematicannon", "create_copper_casing", new int[]{51297});

        System.out.println("[CreateBridge] Successfully registered Create blocks with Java ID overrides!");
    }


    private void registerCube(GeyserDefineCustomBlocksEvent event, String name, String texture, int[] rawIds) {
        CustomBlockComponents comps = CustomBlockComponents.builder()
            .unitCube(true)
            .materialInstance("*", MaterialInstance.builder().texture(texture).build())
            .build();
        NonVanillaCustomBlockData data = NonVanillaCustomBlockData.builder()
            .namespace("create")
            .name(name)
            .components(comps)
            .build();
        event.register(data);

        for (int rawId : rawIds) {
            int shiftedId = OFFSET + rawId;
            event.registerOverride(
                JavaBlockState.builder()
                    .identifier("create:" + name)
                    .javaId(shiftedId)
                    .stateGroupId(shiftedId)
                    .collision(CUBE_COLLISION)
                    .build(),
                data.defaultBlockState()
            );
        }
    }

    @Subscribe
    public void onPostInitialize(GeyserPostInitializeEvent event) {
        System.out.println("=============================================================");
        System.out.println("[CreateBridge DIAGNOSTIC] POST-INITIALIZE CHECK START");
        System.out.println("=============================================================");
        try {
            var overrides = BlockRegistries.NON_VANILLA_BLOCK_STATE_OVERRIDES.get();
            System.out.println("[DIAGNOSTIC] Total Non-Vanilla Overrides in Registry: " + (overrides != null ? overrides.size() : "null"));

            int v = GameProtocol.DEFAULT_BEDROCK_PROTOCOL;
            BlockMappings bm = BlockRegistries.BLOCKS.forVersion(v);
            if (bm != null) {
                System.out.println("[DIAGNOSTIC] Testing BlockMappings for Bedrock Default Protocol v" + v + ":");
                int[] testIds = new int[]{132328, 132329, 127275, 127289, 147909, 146215, 151297};
                for (int testId : testIds) {
                    GeyserBedrockBlock bb = bm.getBedrockBlock(testId);
                    boolean isAir = (bb == bm.getBedrockAir());
                    System.out.println("  >> Java ID " + testId + " -> Bedrock: " + (bb != null ? bb.toString() : "NULL")
                        + " | runtimeId=" + (bb != null ? bb.getRuntimeId() : -1)
                        + " | isAir=" + isAir);
                }
            } else {
                System.out.println("[DIAGNOSTIC] Warning: BlockMappings was null for protocol " + v);
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        System.out.println("=============================================================");
    }

    @Subscribe
    public void onSessionJoin(SessionJoinEvent event) {
        System.out.println("[CreateBridge DIAGNOSTIC] Bedrock player joined: " + event.connection().name());
        new Thread(() -> {
            try {
                Thread.sleep(2000);
                if (event.connection() instanceof GeyserSession session) {
                    BlockMappings bm = session.getBlockMappings();
                    GeyserBedrockBlock bb = bm.getBedrockBlock(132328);
                    boolean isAir = (bb == bm.getBedrockAir());
                    System.out.println("=============================================================");
                    System.out.println("[CreateBridge LIVE SESSION PROBE] Player " + session.name());
                    System.out.println("  >> Andesite Casing (132328) Bedrock Block: " + bb);
                    System.out.println("  >> runtimeId: " + (bb != null ? bb.getRuntimeId() : -1));
                    System.out.println("  >> isAir: " + isAir);
                    System.out.println("=============================================================");
                }
            } catch (Throwable t) {
                t.printStackTrace();
            }
        }).start();
    }
}
