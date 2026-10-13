package com.createbridge.companion;

import com.createbridge.companion.net.BridgeSocketClient;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.event.lifecycle.FMLLoadCompleteEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;

import java.io.File;
import java.io.FileWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@Mod("createbridge_companion")
public class CreateBridgeCompanion {

    public static final String MODID = "createbridge_companion";
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public CreateBridgeCompanion(IEventBus modEventBus) {
        System.out.println("[CreateBridge-Companion] Initializing CreateBridge Companion Mod...");
        
        // Start background high-speed socket client to Geyser bridge
        BridgeSocketClient.start();

        // Register mod bus events
        modEventBus.addListener(this::onLoadComplete);

        // Register server lifecycle events
        NeoForge.EVENT_BUS.register(this);
    }

    private void onLoadComplete(FMLLoadCompleteEvent event) {
        event.enqueueWork(() -> {
            try {
                exportAllBlockStates();
            } catch (Throwable t) {
                System.err.println("[CreateBridge-Companion] Failed to export blockstates: " + t.getMessage());
                t.printStackTrace();
            }
        });
    }

    @SubscribeEvent
    public void onServerStopping(ServerStoppingEvent event) {
        System.out.println("[CreateBridge-Companion] Server stopping; shutting down socket client");
        BridgeSocketClient.stop();
    }

    private void exportAllBlockStates() {
        System.out.println("[CreateBridge-Companion] Auditing and exporting all BlockState permutations...");
        File configDir = new File("config");
        if (!configDir.exists()) {
            configDir.mkdirs();
        }
        File targetFile = new File(configDir, "all_blockstates.json");

        JsonObject root = new JsonObject();
        JsonArray blocksArray = new JsonArray();
        AtomicInteger totalPermutations = new AtomicInteger(0);
        AtomicInteger totalBlocks = new AtomicInteger(0);

        for (Map.Entry<net.minecraft.resources.ResourceKey<Block>, Block> entry : BuiltInRegistries.BLOCK.entrySet()) {
            Block block = entry.getValue();
            ResourceLocation id = entry.getKey().location();
            totalBlocks.incrementAndGet();

            JsonObject blockObj = new JsonObject();
            blockObj.addProperty("id", id.toString());

            JsonArray statesArray = new JsonArray();
            for (BlockState state : block.getStateDefinition().getPossibleStates()) {
                totalPermutations.incrementAndGet();
                JsonObject stateObj = new JsonObject();
                JsonObject propsObj = new JsonObject();

                for (Property<?> property : state.getProperties()) {
                    Comparable<?> value = state.getValue(property);
                    propsObj.addProperty(property.getName(), value.toString());
                }
                stateObj.add("properties", propsObj);
                statesArray.add(stateObj);
            }

            blockObj.add("states", statesArray);
            blockObj.addProperty("permutation_count", statesArray.size());
            blocksArray.add(blockObj);
        }

        root.addProperty("total_blocks", totalBlocks.get());
        root.addProperty("total_permutations", totalPermutations.get());
        root.add("blocks", blocksArray);

        try (Writer writer = new FileWriter(targetFile, StandardCharsets.UTF_8)) {
            GSON.toJson(root, writer);
            System.out.println(String.format("[CreateBridge-Companion] Successfully exported %d permutations across %d blocks to %s",
                    totalPermutations.get(), totalBlocks.get(), targetFile.getAbsolutePath()));
        } catch (Throwable t) {
            System.err.println("[CreateBridge-Companion] Error writing all_blockstates.json: " + t.getMessage());
        }
    }
}
