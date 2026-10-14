package com.createbridge.blocks;

import com.createbridge.config.BlockProperties;
import com.createbridge.config.BridgeConfig;
import org.geysermc.geyser.api.block.custom.CustomBlockPermutation;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.GeometryComponent;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class PipeBlockRegistrar {

    private static final String GEO_BASE = "geometry.create.pipe_none";
    private static final List<String> ALL_SHAPES = generateAllShapes();

    private static List<String> generateAllShapes() {
        List<String> list = new ArrayList<>();
        list.add("none");
        String[] dirs = {"d", "u", "n", "s", "e", "w"};
        int n = dirs.length;
        for (int mask = 1; mask < (1 << n); mask++) {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < n; i++) {
                if ((mask & (1 << i)) != 0) {
                    if (sb.length() > 0) sb.append("_");
                    sb.append(dirs[i]);
                }
            }
            list.add(sb.toString());
        }
        return list;
    }

    public static void register(GeyserDefineCustomBlocksEvent event, String name, String texture, JavaBoundingBox[] collision, List<Integer> rawIds) {
        String identifier = "create:" + name;
        if (rawIds.isEmpty()) return;

        List<CustomBlockPermutation> perms = new ArrayList<>();
        for (String shape : ALL_SHAPES) {
            String geoId = "geometry.create.pipe_" + shape;
            perms.add(new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .geometry(GeometryComponent.builder().identifier(geoId).build())
                    .build(),
                "q.block_property('create:shape') == '" + shape + "'"
            ));
        }

        CustomBlockComponents baseComps = CustomBlockComponents.builder()
            .geometry(GeometryComponent.builder().identifier(GEO_BASE).build())
            .materialInstance("*", MaterialInstance.builder()
                .texture(texture)
                .renderMethod("alpha_test")
                .faceDimming(true)
                .ambientOcclusion(true)
                .build())
            .build();

        NonVanillaCustomBlockData data = NonVanillaCustomBlockData.builder()
            .namespace("create")
            .name(name)
            .components(baseComps)
            .stringProperty("create:shape", ALL_SHAPES)
            .permutations(perms)
            .build();
        event.register(data);

        Map<String, org.geysermc.geyser.api.block.custom.CustomBlockState> stateMap = new HashMap<>();
        for (String s : ALL_SHAPES) {
            stateMap.put(s, data.blockStateBuilder().stringProperty("create:shape", s).build());
        }

        for (int rawId : rawIds) {
            int shiftedId = BridgeConfig.OFFSET + rawId;
            String shape = determineShape(rawId);
            var targetState = stateMap.getOrDefault(shape, stateMap.get("none"));

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
    }

    private static String determineShape(int rawId) {
        StringBuilder sb = new StringBuilder();
        if (BlockProperties.isConnectionTrue(rawId, "down")) sb.append("d");
        if (BlockProperties.isConnectionTrue(rawId, "up")) {
            if (sb.length() > 0) sb.append("_");
            sb.append("u");
        }
        if (BlockProperties.isConnectionTrue(rawId, "north")) {
            if (sb.length() > 0) sb.append("_");
            sb.append("n");
        }
        if (BlockProperties.isConnectionTrue(rawId, "south")) {
            if (sb.length() > 0) sb.append("_");
            sb.append("s");
        }
        if (BlockProperties.isConnectionTrue(rawId, "east")) {
            if (sb.length() > 0) sb.append("_");
            sb.append("e");
        }
        if (BlockProperties.isConnectionTrue(rawId, "west")) {
            if (sb.length() > 0) sb.append("_");
            sb.append("w");
        }
        return sb.length() == 0 ? "none" : sb.toString();
    }

    private PipeBlockRegistrar() {}
}
