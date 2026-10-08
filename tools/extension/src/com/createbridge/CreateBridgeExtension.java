package com.createbridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.GeometryComponent;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.event.bedrock.SessionJoinEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomItemsEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserPostInitializeEvent;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.item.custom.NonVanillaCustomItemData;
import org.geysermc.geyser.network.bedrock.GameProtocol;
import org.geysermc.geyser.registry.BlockRegistries;
import org.geysermc.geyser.registry.type.BlockMappings;
import org.geysermc.geyser.registry.type.GeyserBedrockBlock;
import org.geysermc.geyser.session.GeyserSession;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public class CreateBridgeExtension implements Extension {
    private static final int OFFSET = 100000;
    private static final int ITEM_OFFSET = 10000;

    private static final JavaBoundingBox[] CUBE_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.5, 0.5, 0.5, 1.0, 1.0, 1.0)
    };

    private static final JavaBoundingBox[] DEPOT_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.5, 0.40625, 0.5, 1.0, 0.8125, 1.0)
    };

    private JsonObject registryDump;

    private JsonObject getRegistryDump() {
        if (registryDump != null) return registryDump;
        try {
            InputStream is = getClass().getClassLoader().getResourceAsStream("create_registry_dump.json");
            if (is == null) {
                File f = new File("create_registry_dump.json");
                if (f.exists()) {
                    is = new FileInputStream(f);
                } else {
                    f = new File("headless_server/create_registry_dump.json");
                    if (f.exists()) {
                        is = new FileInputStream(f);
                    }
                }
            }
            if (is != null) {
                try (InputStreamReader reader = new InputStreamReader(is)) {
                    registryDump = JsonParser.parseReader(reader).getAsJsonObject();
                    System.out.println("[CreateBridge] Loaded dynamic registry dump successfully!");
                }
            } else {
                System.err.println("[CreateBridge] ERROR: Could not find create_registry_dump.json!");
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return registryDump;
    }

    private List<Integer> getBlockStateIds(String identifier) {
        List<Integer> list = new ArrayList<>();
        JsonObject dump = getRegistryDump();
        if (dump != null && dump.has("blockstates")) {
            JsonObject states = dump.getAsJsonObject("blockstates");
            if (states.has(identifier)) {
                JsonArray arr = states.getAsJsonArray(identifier);
                for (JsonElement el : arr) {
                    list.add(el.getAsInt());
                }
            }
        }
        return list;
    }

    private int getItemId(String identifier) {
        JsonObject dump = getRegistryDump();
        if (dump != null && dump.has("items")) {
            JsonObject items = dump.getAsJsonObject("items");
            if (items.has(identifier)) {
                return items.get(identifier).getAsInt();
            }
        }
        return -1;
    }

    @Subscribe
    public void onDefineCustomItems(GeyserDefineCustomItemsEvent event) {
        System.out.println("[CreateBridge] Registering Create custom items from dynamic registry...");

        String[] blockItemNames = new String[]{
            "andesite_casing", "brass_casing", "copper_casing", "railway_casing",
            "raw_zinc_block", "zinc_block", "brass_block",
            "large_cogwheel", "cogwheel", "depot", "chute", "schematicannon"
        };

        for (String name : blockItemNames) {
            registerItemDynamic(event, name, true);
        }

        registerItemDynamic(event, "wrench", false);

        System.out.println("[CreateBridge] Successfully registered Create custom items!");
    }

    private void registerItemDynamic(GeyserDefineCustomItemsEvent event, String name, boolean isBlock) {
        String identifier = "create:" + name;
        int rawId = getItemId(identifier);
        if (rawId == -1) {
            System.err.println("[CreateBridge] Warning: No item ID found for " + identifier);
            return;
        }

        int shiftedJavaId = ITEM_OFFSET + rawId;
        try {
            var builder = NonVanillaCustomItemData.builder()
                .identifier(identifier)
                .javaId(shiftedJavaId)
                .name(name)
                .icon("create_" + name);
            if (isBlock) {
                builder.block(identifier);
            }
            event.register(builder.build());
            System.out.println("  + Item " + identifier + " (raw=" + rawId + " -> shifted=" + shiftedJavaId + ")");
        } catch (Throwable t) {
            System.out.println("[CreateBridge] Notice: item " + name + " skipped: " + t.getMessage());
        }
    }

    @Subscribe
    public void onDefineCustomBlocks(GeyserDefineCustomBlocksEvent event) {
        System.out.println("[CreateBridge] Registering Create blocks from dynamic registry...");

        // Standard unit cubes
        registerCubeBlock(event, "andesite_casing", "create_andesite_casing");
        registerCubeBlock(event, "brass_casing", "create_brass_casing");
        registerCubeBlock(event, "copper_casing", "create_copper_casing");
        registerCubeBlock(event, "railway_casing", "create_railway_casing");
        registerCubeBlock(event, "raw_zinc_block", "create_raw_zinc_block");
        registerCubeBlock(event, "zinc_block", "create_zinc_block");
        registerCubeBlock(event, "brass_block", "create_brass_block");
        registerCubeBlock(event, "chute", "create_andesite_casing");
        registerCubeBlock(event, "schematicannon", "create_copper_casing");

        // Custom model blocks
        registerGeoBlock(event, "cogwheel", "create_cogwheel", "geometry.create.cogwheel", CUBE_COLLISION);
        registerGeoBlock(event, "large_cogwheel", "create_cogwheel", "geometry.create.cogwheel", CUBE_COLLISION);
        registerGeoBlock(event, "depot", "create_depot", "geometry.create.depot", DEPOT_COLLISION);

        System.out.println("[CreateBridge] Successfully registered Create blocks with dynamic Java ID overrides!");
    }

    private void registerCubeBlock(GeyserDefineCustomBlocksEvent event, String name, String texture) {
        String identifier = "create:" + name;
        List<Integer> rawIds = getBlockStateIds(identifier);
        if (rawIds.isEmpty()) {
            System.err.println("[CreateBridge] Warning: No blockstate IDs found for " + identifier);
            return;
        }

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
                    .identifier(identifier)
                    .javaId(shiftedId)
                    .stateGroupId(shiftedId)
                    .collision(CUBE_COLLISION)
                    .build(),
                data.defaultBlockState()
            );
        }
        System.out.println("  + Cube " + identifier + " registered " + rawIds.size() + " state(s): " + rawIds);
    }

    private void registerGeoBlock(GeyserDefineCustomBlocksEvent event, String name, String texture, String geoId, JavaBoundingBox[] collision) {
        String identifier = "create:" + name;
        List<Integer> rawIds = getBlockStateIds(identifier);
        if (rawIds.isEmpty()) {
            System.err.println("[CreateBridge] Warning: No blockstate IDs found for " + identifier);
            return;
        }

        CustomBlockComponents comps = CustomBlockComponents.builder()
            .geometry(GeometryComponent.builder().identifier(geoId).build())
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
                    .identifier(identifier)
                    .javaId(shiftedId)
                    .stateGroupId(shiftedId)
                    .collision(collision)
                    .build(),
                data.defaultBlockState()
            );
        }
        System.out.println("  + Geo " + identifier + " [" + geoId + "] registered " + rawIds.size() + " state(s): " + rawIds);
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
                int[] probeNames = new int[]{29091, 29092, 29093, 27274, 27275, 26695, 26701};
                for (int rawId : probeNames) {
                    GeyserBedrockBlock bbRaw = bm.getBedrockBlock(rawId);
                    GeyserBedrockBlock bbShifted = bm.getBedrockBlock(OFFSET + rawId);
                    System.out.println("  >> Raw " + rawId + " -> " + (bbRaw != null ? bbRaw.toString() : "NULL")
                        + " | Shifted " + (OFFSET + rawId) + " -> " + (bbShifted != null ? bbShifted.toString() : "NULL")
                        + " | runtimeId=" + (bbShifted != null ? bbShifted.getRuntimeId() : -1));
                }
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
                    GeyserBedrockBlock bbAndesite = bm.getBedrockBlock(OFFSET + 29091);
                    GeyserBedrockBlock bbDepot = bm.getBedrockBlock(OFFSET + 27274);
                    System.out.println("=============================================================");
                    System.out.println("[CreateBridge LIVE SESSION PROBE] Player " + session.name());
                    System.out.println("  >> Andesite Casing (129091) Bedrock: " + bbAndesite + " | runtimeId=" + (bbAndesite != null ? bbAndesite.getRuntimeId() : -1));
                    System.out.println("  >> Depot (127274) Bedrock: " + bbDepot + " | runtimeId=" + (bbDepot != null ? bbDepot.getRuntimeId() : -1));
                    System.out.println("=============================================================");
                }
            } catch (Throwable t) {
                t.printStackTrace();
            }
        }).start();
    }
}
