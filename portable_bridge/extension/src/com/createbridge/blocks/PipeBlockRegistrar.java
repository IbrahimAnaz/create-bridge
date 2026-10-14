package com.createbridge.blocks;

import com.createbridge.config.BlockProperties;
import com.createbridge.config.BridgeConfig;
import org.geysermc.geyser.api.block.custom.CustomBlockPermutation;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.GeometryComponent;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;
import org.geysermc.geyser.api.block.custom.component.TransformationComponent;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class PipeBlockRegistrar {

    private static final String GEO_STRAIGHT = "geometry.create.pipe_straight";
    private static final String GEO_ELBOW    = "geometry.create.pipe_elbow";
    private static final String GEO_HUB      = "geometry.create.pipe_hub";

    public static void register(GeyserDefineCustomBlocksEvent event, String name, String texture, JavaBoundingBox[] collision, List<Integer> rawIds) {
        String identifier = "create:" + name;
        if (rawIds.isEmpty()) return;

        List<String> shapes = List.of(
            "straight_y", "straight_x", "straight_z",
            "elbow_us", "elbow_un", "elbow_ue", "elbow_uw",
            "elbow_ds", "elbow_dn", "elbow_de", "elbow_dw",
            "elbow_se", "elbow_sw", "elbow_ne", "elbow_nw",
            "hub"
        );

        List<CustomBlockPermutation> perms = new ArrayList<>();
        for (String shape : shapes) {
            String geoId = "geometry.create.pipe_" + shape;
            perms.add(new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .geometry(GeometryComponent.builder().identifier(geoId).build())
                    .build(),
                "q.block_property('create:shape') == '" + shape + "'"
            ));
        }

        CustomBlockComponents baseComps = CustomBlockComponents.builder()
            .geometry(GeometryComponent.builder().identifier(GEO_HUB).build())
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
            .stringProperty("create:shape", shapes)
            .permutations(perms)
            .build();
        event.register(data);

        Map<String, org.geysermc.geyser.api.block.custom.CustomBlockState> stateMap = new HashMap<>();
        for (String s : shapes) {
            stateMap.put(s, data.blockStateBuilder().stringProperty("create:shape", s).build());
        }

        for (int rawId : rawIds) {
            int shiftedId = BridgeConfig.OFFSET + rawId;
            String shape = determineShape(rawId);
            var targetState = stateMap.getOrDefault(shape, stateMap.get("hub"));

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
        boolean down = BlockProperties.isConnectionTrue(rawId, "down");
        boolean up = BlockProperties.isConnectionTrue(rawId, "up");
        boolean north = BlockProperties.isConnectionTrue(rawId, "north");
        boolean south = BlockProperties.isConnectionTrue(rawId, "south");
        boolean east = BlockProperties.isConnectionTrue(rawId, "east");
        boolean west = BlockProperties.isConnectionTrue(rawId, "west");

        int count = (down ? 1 : 0) + (up ? 1 : 0) + (north ? 1 : 0) + (south ? 1 : 0) + (east ? 1 : 0) + (west ? 1 : 0);

        if (count == 2) {
            if (up && down) return "straight_y";
            if (east && west) return "straight_x";
            if (north && south) return "straight_z";

            if (up && south) return "elbow_us";
            if (up && north) return "elbow_un";
            if (up && east) return "elbow_ue";
            if (up && west) return "elbow_uw";

            if (down && south) return "elbow_ds";
            if (down && north) return "elbow_dn";
            if (down && east) return "elbow_de";
            if (down && west) return "elbow_dw";

            if (south && east) return "elbow_se";
            if (south && west) return "elbow_sw";
            if (north && east) return "elbow_ne";
            if (north && west) return "elbow_nw";
        }

        if (count == 1) {
            if (east || west) return "straight_x";
            if (up || down) return "straight_y";
            if (north || south) return "straight_z";
        }

        return "hub";
    }

    private PipeBlockRegistrar() {}
}
