package com.createbridge;

import com.createbridge.blocks.CubeBlockRegistrar;
import com.createbridge.blocks.FacingBlockRegistrar;
import com.createbridge.blocks.KineticBlockRegistrar;
import com.createbridge.config.BridgeConfig;
import com.createbridge.items.ItemRegistryManager;
import com.createbridge.network.PacketInterceptorManager;
import com.createbridge.ui.CommandSanitizer;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.event.bedrock.SessionDisconnectEvent;
import org.geysermc.geyser.api.event.bedrock.SessionJoinEvent;
import org.geysermc.geyser.api.event.java.ServerDefineCommandsEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomItemsEvent;
import org.geysermc.geyser.api.event.lifecycle.GeyserPostInitializeEvent;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.session.GeyserSession;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class CreateBridgeExtension implements Extension {

    private JsonObject registryDump;
    private JsonObject geoBlocks;

    private JsonObject getRegistryDump() {
        if (registryDump != null) return registryDump;
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("create_registry_dump.json")) {
            if (is != null) {
                try (InputStreamReader reader = new InputStreamReader(is)) {
                    registryDump = JsonParser.parseReader(reader).getAsJsonObject();
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return registryDump;
    }

    private JsonObject getGeoBlocks() {
        if (geoBlocks != null) return geoBlocks;
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("geo_blocks.json")) {
            if (is != null) {
                try (InputStreamReader reader = new InputStreamReader(is)) {
                    geoBlocks = JsonParser.parseReader(reader).getAsJsonObject();
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

    @Subscribe
    public void onDefineCustomBlocks(GeyserDefineCustomBlocksEvent event) {
        System.out.println("[CreateBridge] Registering custom blocks from dynamic registry...");
        Set<String> registered = new HashSet<>();

        // 1. Kinetic 3-axis blocks
        KineticBlockRegistrar.register(event, "cogwheel", "create_cogwheel", "geometry.create.cogwheel", BridgeConfig.CUBE_COLLISION, "z", getBlockStateIds("create:cogwheel"));
        KineticBlockRegistrar.register(event, "large_cogwheel", "create_large_cogwheel", "geometry.create.large_cogwheel", BridgeConfig.CUBE_COLLISION, "y", getBlockStateIds("create:large_cogwheel"));
        KineticBlockRegistrar.register(event, "shaft", "create_shaft", "geometry.create.shaft", BridgeConfig.CUBE_COLLISION, "y", getBlockStateIds("create:shaft"));
        registered.addAll(Set.of("cogwheel", "large_cogwheel", "shaft"));

        // 2. Mined 3D geometries (facing, kinetic, static)
        JsonObject geoMap = getGeoBlocks();
        if (geoMap != null) {
            for (Map.Entry<String, JsonElement> entry : geoMap.entrySet()) {
                String name = entry.getKey();
                if (registered.contains(name)) continue;

                String geoId = entry.getValue().getAsString();
                JavaBoundingBox[] collision = "depot".equals(name) ? BridgeConfig.DEPOT_COLLISION : BridgeConfig.CUBE_COLLISION;
                List<Integer> rawIds = getBlockStateIds("create:" + name);

                if (com.createbridge.config.BlockProperties.hasFacing(name, rawIds)) {
                    FacingBlockRegistrar.register(event, name, "create_" + name, geoId, collision, rawIds);
                } else if (com.createbridge.config.BlockProperties.hasAxis(name, rawIds)) {
                    KineticBlockRegistrar.register(event, name, "create_" + name, geoId, collision, "y", rawIds);
                } else if ("fluid_pipe".equals(name) || "glass_fluid_pipe".equals(name)) {
                    com.createbridge.blocks.PipeBlockRegistrar.register(event, name, "create_" + name, collision, rawIds);
                } else {
                    CubeBlockRegistrar.registerStaticGeo(event, name, "create_" + name, geoId, collision, rawIds);
                }
                registered.add(name);
            }
        }

        // 3. Casings & Unit Cubes
        JsonObject dump = getRegistryDump();
        if (dump != null && dump.has("blockstates")) {
            JsonObject states = dump.getAsJsonObject("blockstates");
            for (Map.Entry<String, JsonElement> entry : states.entrySet()) {
                String fullId = entry.getKey();
                String name = fullId.startsWith("create:") ? fullId.substring(7) : fullId;
                if (registered.contains(name)) continue;

                List<Integer> rawIds = getBlockStateIds(fullId);
                CubeBlockRegistrar.registerUnitCube(event, name, "create_" + name, rawIds);
                registered.add(name);
            }
        }
        System.out.println("[CreateBridge] Successfully registered " + registered.size() + " custom blocks!");
    }

    @Subscribe
    public void onDefineCustomItems(GeyserDefineCustomItemsEvent event) {
        System.out.println("[CreateBridge] Registering custom items with deterministic ID sorting...");
        JsonObject dump = getRegistryDump();
        Set<String> blockSet = new HashSet<>();
        if (dump != null && dump.has("blockstates")) {
            blockSet.addAll(dump.getAsJsonObject("blockstates").keySet());
        }
        int count = ItemRegistryManager.registerAll(event, dump, blockSet);
        System.out.println("[CreateBridge] Registered " + count + " custom items!");
    }

    @Subscribe
    public void onPostInitialize(GeyserPostInitializeEvent event) {
        System.out.println("[CreateBridge] Starting BridgeSyncServer socket listener...");
        com.createbridge.network.BridgeSyncServer.start();
        System.out.println("[CreateBridge] Installing packet interceptors...");
        PacketInterceptorManager.registerAll();
        System.out.println("[CreateBridge] Packet interceptors active.");
    }

    @Subscribe
    public void onSessionJoin(SessionJoinEvent event) {
        if (event.connection() instanceof GeyserSession session) {
            PacketInterceptorManager.onPlayerSpawned(session);
        }
    }

    @Subscribe
    public void onSessionDisconnect(SessionDisconnectEvent event) {
        if (event.connection() instanceof GeyserSession session) {
            PacketInterceptorManager.cleanupSession(session);
        }
    }

    @Subscribe
    public void onServerDefineCommands(ServerDefineCommandsEvent event) {
        CommandSanitizer.sanitize(event, getRegistryDump());
    }
}
