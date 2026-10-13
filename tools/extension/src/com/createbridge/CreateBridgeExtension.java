package com.createbridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.cloudburstmc.math.vector.Vector3f;
import org.cloudburstmc.math.vector.Vector3i;
import org.cloudburstmc.nbt.NbtMap;
import org.cloudburstmc.protocol.bedrock.data.entity.EntityDataMap;
import org.cloudburstmc.protocol.bedrock.data.entity.EntityFlag;
import org.cloudburstmc.protocol.bedrock.data.inventory.ItemData;
import org.cloudburstmc.protocol.bedrock.data.definitions.ItemDefinition;
import org.cloudburstmc.protocol.bedrock.packet.AddItemEntityPacket;
import org.cloudburstmc.protocol.bedrock.packet.RemoveEntityPacket;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.block.custom.CustomBlockPermutation;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.GeometryComponent;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;
import org.geysermc.geyser.api.block.custom.component.TransformationComponent;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.event.bedrock.SessionDisconnectEvent;
import org.geysermc.geyser.api.event.java.ServerDefineCommandsEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomItemsEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserPostInitializeEvent;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.item.custom.NonVanillaCustomItemData;
import org.geysermc.geyser.api.item.custom.v2.CustomItemBedrockOptions;
import org.geysermc.geyser.api.item.custom.v2.NonVanillaCustomItemDefinition;
import org.geysermc.geyser.api.item.custom.v2.component.geyser.GeyserBlockPlacer;
import org.geysermc.geyser.api.item.custom.v2.component.geyser.GeyserItemDataComponents;
import org.geysermc.geyser.api.util.CreativeCategory;
import org.geysermc.geyser.api.util.Identifier;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import org.cloudburstmc.protocol.bedrock.data.definitions.BlockDefinition;
import org.geysermc.geyser.registry.BlockRegistries;
import org.geysermc.geyser.registry.type.BlockMappings;
import org.geysermc.geyser.registry.type.ItemMappings;
import org.geysermc.geyser.registry.type.ItemMapping;
import org.geysermc.geyser.registry.Registries;
import org.geysermc.geyser.session.GeyserSession;
import org.geysermc.geyser.translator.protocol.PacketTranslator;
import org.geysermc.mcprotocollib.protocol.data.game.level.block.BlockEntityInfo;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundBlockEntityDataPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundBlockUpdatePacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundForgetLevelChunkPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundLevelChunkWithLightPacket;

import org.cloudburstmc.protocol.bedrock.data.command.CommandEnumConstraint;
import org.cloudburstmc.protocol.bedrock.data.command.CommandEnumData;
import org.cloudburstmc.protocol.bedrock.data.command.CommandOverloadData;
import org.cloudburstmc.protocol.bedrock.data.command.CommandParam;
import org.cloudburstmc.protocol.bedrock.data.command.CommandParamData;
import org.cloudburstmc.protocol.bedrock.packet.ItemStackRequestPacket;
import org.cloudburstmc.protocol.bedrock.data.inventory.itemstack.request.ItemStackRequest;
import org.cloudburstmc.protocol.bedrock.data.inventory.itemstack.request.action.ItemStackRequestAction;
import org.cloudburstmc.protocol.bedrock.data.inventory.itemstack.request.action.ItemStackRequestActionType;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class CreateBridgeExtension implements Extension {

    public static final int OFFSET = 100000;
    public static final int ITEM_OFFSET = 10000;

    private static final JavaBoundingBox[] CUBE_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    };

    private static final JavaBoundingBox[] DEPOT_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.0, 0.0, 0.0, 1.0, 0.8125, 1.0)
    };

    private boolean isCustomBlock(String identifier) {
        JsonObject dump = getRegistryDump();
        if (dump != null && dump.has("blockstates")) {
            return dump.getAsJsonObject("blockstates").has(identifier);
        }
        return false;
    }

    private JsonObject registryDump;
    private final Map<GeyserSession, Map<Vector3i, Long>> sessionDepotEntities = new ConcurrentHashMap<>();

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

    private JsonObject geoBlocks;

    private JsonObject getGeoBlocks() {
        if (geoBlocks != null) return geoBlocks;
        try {
            InputStream is = getClass().getClassLoader().getResourceAsStream("geo_blocks.json");
            if (is == null) {
                File f = new File("tools/extension/resources/geo_blocks.json");
                if (f.exists()) {
                    is = new FileInputStream(f);
                }
            }
            if (is != null) {
                try (InputStreamReader reader = new InputStreamReader(is)) {
                    geoBlocks = JsonParser.parseReader(reader).getAsJsonObject();
                    System.out.println("[CreateBridge] Loaded " + geoBlocks.size() + " custom 3D geometries from geo_blocks.json!");
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return geoBlocks;
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

        JsonObject dump = getRegistryDump();
        if (dump != null && dump.has("items")) {
            JsonObject items = dump.getAsJsonObject("items");
            for (Map.Entry<String, JsonElement> entry : items.entrySet()) {
                String fullId = entry.getKey();
                String name = fullId.startsWith("create:") ? fullId.substring(7) : fullId;
                registerItemDynamic(event, name);
            }
        }

        System.out.println("[CreateBridge] Successfully registered Create custom items!");
    }

    private void registerItemDynamic(GeyserDefineCustomItemsEvent event, String name) {
        String identifier = "create:" + name;
        int rawId = getItemId(identifier);
        if (rawId == -1) {
            System.err.println("[CreateBridge] Warning: No item ID found for " + identifier);
            return;
        }

        int shiftedJavaId = ITEM_OFFSET + rawId;
        try {
            var bedrockOptions = CustomItemBedrockOptions.builder()
                .icon("create_" + name)
                .creativeCategory(CreativeCategory.ITEMS)
                .creativeGroup("itemGroup.name.create");

            var builder = NonVanillaCustomItemDefinition.builder(Identifier.of(identifier), shiftedJavaId)
                .displayName(name)
                .bedrockOptions(bedrockOptions);

            if (isCustomBlock(identifier)) {
                builder.component(
                    GeyserItemDataComponents.BLOCK_PLACER,
                    GeyserBlockPlacer.of(Identifier.of(identifier), true)
                );
            }

            event.register(builder.build());
            System.out.println("  + Item " + identifier + " (raw=" + rawId + " -> shifted=" + shiftedJavaId + (isCustomBlock(identifier) ? " [3D Block]" : "") + ")");
        } catch (Throwable t) {
            System.out.println("[CreateBridge] Notice: item " + name + " skipped: " + t.getMessage());
        }
    }

    @Subscribe
    public void onDefineCustomBlocks(GeyserDefineCustomBlocksEvent event) {
        System.out.println("[CreateBridge] Registering Create blocks from dynamic registry...");

        java.util.Set<String> kineticBlocks = java.util.Set.of(
            "cogwheel", "large_cogwheel", "shaft"
        );

        // 1. Kinetic 3-axis blocks (with custom axis permutations)
        registerKineticBlock(event, "cogwheel", "create_cogwheel", "geometry.create.cogwheel", CUBE_COLLISION, "z");
        registerKineticBlock(event, "large_cogwheel", "create_large_cogwheel", "geometry.create.large_cogwheel", CUBE_COLLISION, "y");
        registerKineticBlock(event, "shaft", "create_shaft", "geometry.create.shaft", CUBE_COLLISION, "y");

        // 2. Dynamic 3D Geometry blocks (mined from Create JAR via model_miner.py)
        JsonObject geoMap = getGeoBlocks();
        java.util.Set<String> registeredGeo = new java.util.HashSet<>(kineticBlocks);
        int geoCount = kineticBlocks.size();

        if (geoMap != null) {
            for (Map.Entry<String, JsonElement> entry : geoMap.entrySet()) {
                String name = entry.getKey();
                if (registeredGeo.contains(name)) {
                    continue;
                }
                String geoId = entry.getValue().getAsString();
                JavaBoundingBox[] collision = "depot".equals(name) ? DEPOT_COLLISION : CUBE_COLLISION;
                if (name.endsWith("valve_handle") || name.equals("hand_crank") || name.equals("creative_motor")
                        || name.equals("encased_fan") || name.equals("mechanical_drill") || name.equals("mechanical_saw")
                        || name.equals("deployer") || name.equals("mechanical_harvester") || name.equals("mechanical_plough")) {
                    registerFacingBlock(event, name, "create_" + name, geoId, collision);
                } else if (name.equals("gearbox") || name.equals("clutch") || name.equals("gearshift") || name.equals("water_wheel")) {
                    registerKineticBlock(event, name, "create_" + name, geoId, collision, "y");
                } else {
                    registerGeoBlock(event, name, "create_" + name, geoId, collision);
                }
                registeredGeo.add(name);
                geoCount++;
            }
        }

        // 3. Dynamic registration for all other blocks (standard unit cubes)
        JsonObject dump = getRegistryDump();
        int cubeCount = 0;
        int stateCount = 0;
        if (dump != null && dump.has("blockstates")) {
            JsonObject states = dump.getAsJsonObject("blockstates");
            for (Map.Entry<String, JsonElement> entry : states.entrySet()) {
                String fullId = entry.getKey();
                String name = fullId.startsWith("create:") ? fullId.substring(7) : fullId;
                if (registeredGeo.contains(name)) {
                    continue;
                }
                int statesRegistered = registerCubeBlock(event, name, "create_" + name);
                if (statesRegistered > 0) {
                    cubeCount++;
                    stateCount += statesRegistered;
                }
            }
        }

        System.out.println("[CreateBridge] Successfully registered " + (geoCount + cubeCount) + " Create blocks (" + geoCount + " 3D geo models, " + stateCount + " cube states) with dynamic Java ID overrides!");
    }

    private int registerCubeBlock(GeyserDefineCustomBlocksEvent event, String name, String texture) {
        String identifier = "create:" + name;
        List<Integer> rawIds = getBlockStateIds(identifier);
        if (rawIds.isEmpty()) {
            return 0;
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
        return rawIds.size();
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
            .materialInstance("*", MaterialInstance.builder()
                .texture(texture)
                .renderMethod("alpha_test")
                .faceDimming(true)
                .ambientOcclusion(false)
                .build())
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

    private void registerFacingBlock(GeyserDefineCustomBlocksEvent event, String name, String texture, String geoId, JavaBoundingBox[] collision) {
        String identifier = "create:" + name;
        List<Integer> rawIds = getBlockStateIds(identifier);
        if (rawIds.isEmpty()) {
            System.err.println("[CreateBridge] Warning: No blockstate IDs found for " + identifier);
            return;
        }

        List<CustomBlockPermutation> perms = List.of(
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(0, 0, 0))
                    .build(),
                "q.block_property('create:facing') == 'up'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(180, 0, 0))
                    .build(),
                "q.block_property('create:facing') == 'down'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(90, 0, 0))
                    .build(),
                "q.block_property('create:facing') == 'north'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(90, 180, 0))
                    .build(),
                "q.block_property('create:facing') == 'south'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(90, 90, 0))
                    .build(),
                "q.block_property('create:facing') == 'east'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(90, 270, 0))
                    .build(),
                "q.block_property('create:facing') == 'west'"
            )
        );

        CustomBlockComponents comps = CustomBlockComponents.builder()
            .geometry(GeometryComponent.builder().identifier(geoId).build())
            .materialInstance("*", MaterialInstance.builder()
                .texture(texture)
                .renderMethod("alpha_test")
                .faceDimming(true)
                .ambientOcclusion(false)
                .build())
            .build();

        NonVanillaCustomBlockData data = NonVanillaCustomBlockData.builder()
            .namespace("create")
            .name(name)
            .components(comps)
            .stringProperty("create:facing", List.of("down", "up", "north", "south", "west", "east"))
            .permutations(perms)
            .build();
        event.register(data);

        var stateDown  = data.blockStateBuilder().stringProperty("create:facing", "down").build();
        var stateEast  = data.blockStateBuilder().stringProperty("create:facing", "east").build();
        var stateNorth = data.blockStateBuilder().stringProperty("create:facing", "north").build();
        var stateSouth = data.blockStateBuilder().stringProperty("create:facing", "south").build();
        var stateUp    = data.blockStateBuilder().stringProperty("create:facing", "up").build();
        var stateWest  = data.blockStateBuilder().stringProperty("create:facing", "west").build();

        for (int rawId : rawIds) {
            int shiftedId = OFFSET + rawId;
            int idx = rawIds.indexOf(rawId);
            var targetState = stateUp;
            if (rawIds.size() >= 12) {
                if (idx == 0 || idx == 1) targetState = stateDown;
                else if (idx == 2 || idx == 3) targetState = stateEast;
                else if (idx == 4 || idx == 5) targetState = stateNorth;
                else if (idx == 6 || idx == 7) targetState = stateSouth;
                else if (idx == 8 || idx == 9) targetState = stateUp;
                else if (idx == 10 || idx == 11) targetState = stateWest;
            } else if (rawIds.size() == 6) {
                if (idx == 0) targetState = stateDown;
                else if (idx == 1) targetState = stateEast;
                else if (idx == 2) targetState = stateNorth;
                else if (idx == 3) targetState = stateSouth;
                else if (idx == 4) targetState = stateUp;
                else if (idx == 5) targetState = stateWest;
            }

            event.registerOverride(
                JavaBlockState.builder()
                    .identifier(identifier)
                    .javaId(shiftedId)
                    .stateGroupId(shiftedId)
                    .collision(collision)
                    .build(),
                targetState
            );
        }
        System.out.println("  + Facing " + identifier + " [" + geoId + "] registered 6-way permutations for " + rawIds.size() + " state(s)");
    }

    private void registerKineticBlock(GeyserDefineCustomBlocksEvent event, String name, String texture, String geoId, JavaBoundingBox[] collision, String baseAxis) {
        String identifier = "create:" + name;
        List<Integer> rawIds = getBlockStateIds(identifier);
        if (rawIds.isEmpty()) {
            System.err.println("[CreateBridge] Warning: No blockstate IDs found for " + identifier);
            return;
        }

        List<CustomBlockPermutation> perms;
        if ("z".equalsIgnoreCase(baseAxis)) {
            // Base geometry is aligned along the Z axis (like models/entity/cogwheel.geo.json)
            // x: rotate yaw by 90 to align with X axis
            // y: rotate pitch by 90 to align with Y axis
            // z: default (0, 0, 0)
            perms = List.of(
                new CustomBlockPermutation(
                    CustomBlockComponents.builder()
                        .transformation(new TransformationComponent(0, 90, 0))
                        .build(),
                    "q.block_property('create:axis') == 'x'"
                ),
                new CustomBlockPermutation(
                    CustomBlockComponents.builder()
                        .transformation(new TransformationComponent(90, 0, 0))
                        .build(),
                    "q.block_property('create:axis') == 'y'"
                ),
                new CustomBlockPermutation(
                    CustomBlockComponents.builder()
                        .transformation(new TransformationComponent(0, 0, 0))
                        .build(),
                    "q.block_property('create:axis') == 'z'"
                )
            );
        } else {
            // Base geometry is aligned along the Y axis (like shaft.geo.json and large_cogwheel.geo.json)
            perms = List.of(
                new CustomBlockPermutation(
                    CustomBlockComponents.builder()
                        .transformation(new TransformationComponent(0, 0, 90))
                        .build(),
                    "q.block_property('create:axis') == 'x'"
                ),
                new CustomBlockPermutation(
                    CustomBlockComponents.builder()
                        .transformation(new TransformationComponent(0, 0, 0))
                        .build(),
                    "q.block_property('create:axis') == 'y'"
                ),
                new CustomBlockPermutation(
                    CustomBlockComponents.builder()
                        .transformation(new TransformationComponent(90, 0, 0))
                        .build(),
                    "q.block_property('create:axis') == 'z'"
                )
            );
        }

        CustomBlockComponents comps = CustomBlockComponents.builder()
            .geometry(GeometryComponent.builder().identifier(geoId).build())
            .materialInstance("*", MaterialInstance.builder()
                .texture(texture)
                .renderMethod("alpha_test")
                .faceDimming(true)
                .ambientOcclusion(false)
                .build())
            .build();

        NonVanillaCustomBlockData data = NonVanillaCustomBlockData.builder()
            .namespace("create")
            .name(name)
            .components(comps)
            .stringProperty("create:axis", List.of("x", "y", "z"))
            .permutations(perms)
            .build();
        event.register(data);

        var stateX = data.blockStateBuilder().stringProperty("create:axis", "x").build();
        var stateY = data.blockStateBuilder().stringProperty("create:axis", "y").build();
        var stateZ = data.blockStateBuilder().stringProperty("create:axis", "z").build();

        for (int rawId : rawIds) {
            int shiftedId = OFFSET + rawId;
            int idx = rawIds.indexOf(rawId);
            var targetState = stateY;
            if (idx == 0 || idx == 1) {
                targetState = stateX;
            } else if (idx == 2 || idx == 3) {
                targetState = stateY;
            } else if (idx == 4 || idx == 5) {
                targetState = stateZ;
            }

            event.registerOverride(
                JavaBlockState.builder()
                    .identifier(identifier)
                    .javaId(shiftedId)
                    .stateGroupId(shiftedId)
                    .collision(collision)
                    .build(),
                targetState
            );
        }
        System.out.println("  + Kinetic " + identifier + " [" + geoId + ", base=" + baseAxis + "] registered 3-axis permutations for " + rawIds.size() + " state(s): " + rawIds);
    }

    @Subscribe
    @SuppressWarnings("unchecked")
    public void onPostInitialize(GeyserPostInitializeEvent event) {
        System.out.println("=============================================================");
        System.out.println("[CreateBridge] Installing Packet Translators for Create Mod...");
        System.out.println("[CreateBridge ITEM REGISTRY CHECK]");
        System.out.println("  JAVA_ITEM_IDENTIFIERS total: " + Registries.JAVA_ITEM_IDENTIFIERS.get().size());
        System.out.println("  Contains create:cogwheel? " + Registries.JAVA_ITEM_IDENTIFIERS.get().containsKey("create:cogwheel"));
        System.out.println("  Contains create:speedometer? " + Registries.JAVA_ITEM_IDENTIFIERS.get().containsKey("create:speedometer"));
        System.out.println("  Contains create:wrench? " + Registries.JAVA_ITEM_IDENTIFIERS.get().containsKey("create:wrench"));
        System.out.println("=============================================================");

        try {
            // 1. Hook Block Entity Data Translator
            PacketTranslator<ClientboundBlockEntityDataPacket> origBlockEntity =
                (PacketTranslator<ClientboundBlockEntityDataPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundBlockEntityDataPacket.class);

            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundBlockEntityDataPacket.class, new PacketTranslator<ClientboundBlockEntityDataPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundBlockEntityDataPacket packet) {
                    if (origBlockEntity != null) {
                        origBlockEntity.translate(session, packet);
                    }
                    try {
                        processDepotNbt(session, packet.getPosition(), packet.getNbt());
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                }
            });
            System.out.println("[CreateBridge] Successfully hooked ClientboundBlockEntityDataPacket translator!");

            // 2. Hook Level Chunk Translator
            PacketTranslator<ClientboundLevelChunkWithLightPacket> origChunk =
                (PacketTranslator<ClientboundLevelChunkWithLightPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundLevelChunkWithLightPacket.class);

            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundLevelChunkWithLightPacket.class, new PacketTranslator<ClientboundLevelChunkWithLightPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundLevelChunkWithLightPacket packet) {
                    if (origChunk != null) {
                        origChunk.translate(session, packet);
                    }
                    try {
                        int chunkBlockX = packet.getX() << 4;
                        int chunkBlockZ = packet.getZ() << 4;
                        BlockEntityInfo[] beList = packet.getBlockEntities();
                        if (beList != null) {
                            for (BlockEntityInfo be : beList) {
                                if (be.getNbt() != null) {
                                    Vector3i pos = Vector3i.from(chunkBlockX + be.getX(), be.getY(), chunkBlockZ + be.getZ());
                                    processDepotNbt(session, pos, be.getNbt());
                                }
                            }
                        }
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                }
            });
            System.out.println("[CreateBridge] Successfully hooked ClientboundLevelChunkWithLightPacket translator!");

            // 3. Hook Block Update Translator (handles depot break / replace)
            PacketTranslator<ClientboundBlockUpdatePacket> origBlockUpdate =
                (PacketTranslator<ClientboundBlockUpdatePacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundBlockUpdatePacket.class);

            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundBlockUpdatePacket.class, new PacketTranslator<ClientboundBlockUpdatePacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundBlockUpdatePacket packet) {
                    if (origBlockUpdate != null) {
                        origBlockUpdate.translate(session, packet);
                    }
                    try {
                        Vector3i pos = packet.getEntry().getPosition();
                        Map<Vector3i, Long> depotMap = sessionDepotEntities.get(session);
                        if (depotMap != null && depotMap.containsKey(pos)) {
                            int shiftedId = packet.getEntry().getBlock();
                            int rawId = shiftedId - OFFSET;
                            if (rawId != 27274 && rawId != 27275) {
                                despawnDepotItem(session, pos);
                            }
                        }
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                }
            });
            System.out.println("[CreateBridge] Successfully hooked ClientboundBlockUpdatePacket translator!");

            // 4. Hook Forget Level Chunk Translator (handles chunk unload)
            PacketTranslator<ClientboundForgetLevelChunkPacket> origForgetChunk =
                (PacketTranslator<ClientboundForgetLevelChunkPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundForgetLevelChunkPacket.class);

            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundForgetLevelChunkPacket.class, new PacketTranslator<ClientboundForgetLevelChunkPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundForgetLevelChunkPacket packet) {
                    if (origForgetChunk != null) {
                        origForgetChunk.translate(session, packet);
                    }
                    try {
                        int chunkX = packet.getX();
                        int chunkZ = packet.getZ();
                        Map<Vector3i, Long> depotMap = sessionDepotEntities.get(session);
                        if (depotMap != null) {
                            depotMap.keySet().removeIf(pos -> {
                                if ((pos.getX() >> 4) == chunkX && (pos.getZ() >> 4) == chunkZ) {
                                    despawnDepotItem(session, pos);
                                    return true;
                                }
                                return false;
                            });
                        }
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                }
            });
            System.out.println("[CreateBridge] Successfully hooked ClientboundForgetLevelChunkPacket translator!");

            // 5. Hook Bedrock ItemStackRequestPacket Translator to prevent creative action rejections
            PacketTranslator<ItemStackRequestPacket> origRequestTranslator =
                (PacketTranslator<ItemStackRequestPacket>) (PacketTranslator<?>) Registries.BEDROCK_PACKET_TRANSLATORS.get(ItemStackRequestPacket.class);

            Registries.BEDROCK_PACKET_TRANSLATORS.register(ItemStackRequestPacket.class, new PacketTranslator<ItemStackRequestPacket>() {
                @Override
                public void translate(GeyserSession session, ItemStackRequestPacket packet) {
                    if (packet.getRequests() == null || packet.getRequests().isEmpty()) {
                        if (origRequestTranslator != null) {
                            origRequestTranslator.translate(session, packet);
                        }
                        return;
                    }

                    List<ItemStackRequest> creativeRequests = new ArrayList<>();
                    List<ItemStackRequest> normalRequests = new ArrayList<>();

                    for (ItemStackRequest req : packet.getRequests()) {
                        boolean hasCreative = false;
                        if (req.getActions() != null) {
                            for (ItemStackRequestAction action : req.getActions()) {
                                if (action != null && action.getType() == ItemStackRequestActionType.CRAFT_CREATIVE) {
                                    hasCreative = true;
                                    break;
                                }
                            }
                        }
                        if (hasCreative) {
                            creativeRequests.add(req);
                        } else {
                            normalRequests.add(req);
                        }
                    }

                    if (!creativeRequests.isEmpty()) {
                        session.getPlayerInventoryHolder().translateRequests(creativeRequests);
                    }
                    if (!normalRequests.isEmpty()) {
                        if (session.getInventoryHolder() != null) {
                            session.getInventoryHolder().translateRequests(normalRequests);
                        } else {
                            session.getPlayerInventoryHolder().translateRequests(normalRequests);
                        }
                    }
                }
            });
            System.out.println("[CreateBridge] Successfully hooked ItemStackRequestPacket translator!");

        } catch (Throwable t) {
            t.printStackTrace();
        }
        System.out.println("=============================================================");
    }

    @Subscribe
    public void onSessionDisconnect(SessionDisconnectEvent event) {
        if (event.connection() instanceof GeyserSession session) {
            sessionDepotEntities.remove(session);
            System.out.println("[CreateBridge] Cleaned up depot session tracking for " + session.name());
        }
    }

    @Subscribe
    public void onServerDefineCommands(ServerDefineCommandsEvent event) {
        System.out.println("=============================================================");
        System.out.println("[CreateBridge] ServerDefineCommandsEvent fired with " + event.commands().size() + " commands! Sanitizing for Bedrock palette...");

        int removedCount = 0;
        int fixedOverloadCount = 0;

        Set<String> blockedNames = Set.of("c", "catnip", "ponder", "neoforge");

        java.util.Iterator<? extends ServerDefineCommandsEvent.CommandInfo> it = event.commands().iterator();
        while (it.hasNext()) {
            ServerDefineCommandsEvent.CommandInfo cmd = it.next();
            String name = cmd.name().toLowerCase(java.util.Locale.ROOT);

            // 1. Remove namespaced or blocked commands that break Bedrock command UI
            // Bedrock edition does NOT allow colons in command names and chokes on complex mod Brigadier trees
            if (name.contains(":") || blockedNames.contains(name) || !name.matches("^[a-z0-9_]+$")) {
                it.remove();
                removedCount++;
                continue;
            }

            // 2. Sanitize and enhance overloads
            CommandOverloadData[] overloads = getParamData(cmd);
            if (overloads != null) {
                for (CommandOverloadData overload : overloads) {
                    CommandParamData[] params = overload.getOverloads();
                    if (params == null) continue;

                    boolean seenOptional = false;
                    for (int i = 0; i < params.length; i++) {
                        CommandParamData p = params[i];
                        if (p == null) continue;

                        // Clean parameter name
                        if (p.getName() != null && !p.getName().matches("^[a-zA-Z0-9_]+$")) {
                            p.setName(p.getName().replaceAll("[^a-zA-Z0-9_]", "_"));
                        }

                        // Fix Bedrock rule: required parameter CANNOT follow optional parameter
                        if (p.isOptional()) {
                            seenOptional = true;
                        } else if (seenOptional) {
                            p.setOptional(true);
                            fixedOverloadCount++;
                        }

                        // Enhance give command with all Create items & short aliases
                        if (name.equals("give") && p.getEnumData() != null) {
                            enhanceItemEnum(p);
                        }

                        // Enhance setblock / fill commands with all Create block identifiers
                        if ((name.equals("setblock") || name.equals("fill")) && p.getEnumData() != null) {
                            enhanceBlockEnum(p);
                        }

                        // Ensure ALL large or item/block enums across all commands are soft enums
                        CommandEnumData ed = p.getEnumData();
                        if (ed != null && !ed.isSoft() && (ed.getValues().size() > 50 || ed.getName().toLowerCase(java.util.Locale.ROOT).contains("item") || ed.getName().toLowerCase(java.util.Locale.ROOT).contains("block"))) {
                            p.setEnumData(new CommandEnumData(ed.getName(), ed.getValues(), true));
                        }
                    }
                }
            }
        }

        System.out.println("[CreateBridge] Sanitization complete: " + event.commands().size() + " commands active (" + removedCount + " removed, " + fixedOverloadCount + " overloads corrected)!");
        System.out.println("=============================================================");
    }

    private CommandOverloadData[] getParamData(ServerDefineCommandsEvent.CommandInfo cmd) {
        try {
            Method m = cmd.getClass().getMethod("paramData");
            m.setAccessible(true);
            return (CommandOverloadData[]) m.invoke(cmd);
        } catch (Throwable t1) {
            try {
                java.lang.reflect.Field f = cmd.getClass().getDeclaredField("paramData");
                f.setAccessible(true);
                return (CommandOverloadData[]) f.get(cmd);
            } catch (Throwable t2) {
                return null;
            }
        }
    }

    private void enhanceItemEnum(CommandParamData p) {
        try {
            CommandEnumData oldEnum = p.getEnumData();
            if (oldEnum == null || oldEnum.getValues() == null) return;
            LinkedHashMap<String, Set<CommandEnumConstraint>> newMap = new LinkedHashMap<>(oldEnum.getValues());

            JsonObject dump = getRegistryDump();
            if (dump != null && dump.has("items")) {
                JsonObject items = dump.getAsJsonObject("items");
                for (String fullId : items.keySet()) {
                    newMap.put(fullId, Collections.emptySet());
                    if (fullId.startsWith("create:")) {
                        String shortId = fullId.substring(7);
                        if (!newMap.containsKey(shortId)) {
                            newMap.put(shortId, Collections.emptySet());
                        }
                    }
                }
            }
            p.setEnumData(new CommandEnumData(oldEnum.getName(), newMap, true));
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private void enhanceBlockEnum(CommandParamData p) {
        try {
            CommandEnumData oldEnum = p.getEnumData();
            if (oldEnum == null || oldEnum.getValues() == null) return;
            LinkedHashMap<String, Set<CommandEnumConstraint>> newMap = new LinkedHashMap<>(oldEnum.getValues());

            JsonObject dump = getRegistryDump();
            if (dump != null && dump.has("blockstates")) {
                JsonObject states = dump.getAsJsonObject("blockstates");
                for (String fullId : states.keySet()) {
                    newMap.put(fullId, Collections.emptySet());
                    if (fullId.startsWith("create:")) {
                        String shortId = fullId.substring(7);
                        if (!newMap.containsKey(shortId)) {
                            newMap.put(shortId, Collections.emptySet());
                        }
                    }
                }
            }
            p.setEnumData(new CommandEnumData(oldEnum.getName(), newMap, true));
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private void processDepotNbt(GeyserSession session, Vector3i pos, NbtMap nbt) {
        if (nbt == null) return;
        String id = nbt.getString("id", "");
        boolean isDepot = id.equals("create:depot") || nbt.containsKey("HeldItem");
        if (!isDepot) return;

        try {
            String itemId = null;
            int count = 0;

            if (nbt.containsKey("HeldItem")) {
                Object heldObj = nbt.get("HeldItem");
                if (heldObj instanceof NbtMap heldNbt) {
                    if (heldNbt.containsKey("Item") && heldNbt.get("Item") instanceof NbtMap itemNbt) {
                        itemId = itemNbt.getString("id", "");
                        Number countNum = itemNbt.getNumber("count", itemNbt.getNumber("Count", 1));
                        count = countNum != null ? countNum.intValue() : 1;
                    } else if (heldNbt.containsKey("id")) {
                        itemId = heldNbt.getString("id", "");
                        Number countNum = heldNbt.getNumber("count", heldNbt.getNumber("Count", 1));
                        count = countNum != null ? countNum.intValue() : 1;
                    }
                }
            }

            if (itemId != null && !itemId.isEmpty() && !itemId.equals("minecraft:air") && count > 0) {
                spawnOrUpdateDepotItem(session, pos, itemId, count);
            } else {
                despawnDepotItem(session, pos);
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private void spawnOrUpdateDepotItem(GeyserSession session, Vector3i pos, String itemId, int count) {
        try {
            ItemData itemData = null;
            ItemMapping mapping = session.getItemMappings().getMapping(itemId);
            if (mapping == null && !itemId.contains(":")) {
                mapping = session.getItemMappings().getMapping("minecraft:" + itemId);
            }
            if (mapping != null && mapping.getBedrockDefinition() != null) {
                itemData = ItemData.builder()
                    .definition(mapping.getBedrockDefinition())
                    .count(count)
                    .damage(mapping.getBedrockData())
                    .build();
            } else {
                ItemDefinition def = session.getItemMappings().getDefinition(itemId);
                if (def != null) {
                    itemData = ItemData.builder()
                        .definition(def)
                        .count(count)
                        .damage(0)
                        .build();
                }
            }

            if (itemData == null) {
                System.err.println("[CreateBridge DEPOT] Unable to resolve item definition for " + itemId);
                return;
            }

            Map<Vector3i, Long> depotMap = sessionDepotEntities.computeIfAbsent(session, s -> new ConcurrentHashMap<>());
            long entityId = depotMap.computeIfAbsent(pos, k -> session.getEntityCache().nextEntityId());

            // Always despawn previous entity ID to force Bedrock to recreate / update cleanly
            RemoveEntityPacket rem = new RemoveEntityPacket();
            rem.setUniqueEntityId(entityId);
            session.sendUpstreamPacket(rem);

            // Spawn AddItemEntityPacket resting directly on the depot plate (y + 0.82f)
            AddItemEntityPacket add = new AddItemEntityPacket();
            add.setUniqueEntityId(entityId);
            add.setRuntimeEntityId(entityId);
            add.setItemInHand(itemData);
            add.setPosition(Vector3f.from(pos.getX() + 0.5f, pos.getY() + 0.82f, pos.getZ() + 0.5f));
            add.setMotion(Vector3f.ZERO);

            EntityDataMap meta = new EntityDataMap();
            meta.getOrCreateFlags().put(EntityFlag.HAS_GRAVITY, false);
            add.setMetadata(meta);

            session.sendUpstreamPacket(add);
            System.out.println("[CreateBridge DEPOT] Successfully displayed " + itemId + " x" + count + " at " + pos + " (entityId=" + entityId + ")");
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private void despawnDepotItem(GeyserSession session, Vector3i pos) {
        Map<Vector3i, Long> depotMap = sessionDepotEntities.get(session);
        if (depotMap != null) {
            Long entityId = depotMap.remove(pos);
            if (entityId != null) {
                RemoveEntityPacket rem = new RemoveEntityPacket();
                rem.setUniqueEntityId(entityId);
                session.sendUpstreamPacket(rem);
                System.out.println("[CreateBridge DEPOT] Cleared item display at " + pos + " (entityId=" + entityId + ")");
            }
        }
    }
}
