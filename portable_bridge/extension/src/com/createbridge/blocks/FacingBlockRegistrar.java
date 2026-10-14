package com.createbridge.blocks;

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

import java.util.List;

public final class FacingBlockRegistrar {

    public static void register(GeyserDefineCustomBlocksEvent event, String name, String texture, String geoId, JavaBoundingBox[] collision, List<Integer> rawIds) {
        String identifier = "create:" + name;
        if (rawIds.isEmpty()) return;

        // Upright rotations for mined Bedrock geometries (pitch = 0 for horizontal facings)
        List<CustomBlockPermutation> perms = List.of(
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(90, 0, 0))
                    .build(),
                "q.block_property('create:facing') == 'up'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(270, 0, 0))
                    .build(),
                "q.block_property('create:facing') == 'down'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(0, 0, 0))
                    .build(),
                "q.block_property('create:facing') == 'north'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(0, 180, 0))
                    .build(),
                "q.block_property('create:facing') == 'south'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(0, 90, 0))
                    .build(),
                "q.block_property('create:facing') == 'east'"
            ),
            new CustomBlockPermutation(
                CustomBlockComponents.builder()
                    .transformation(new TransformationComponent(0, 270, 0))
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
                .ambientOcclusion(true)
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
        var stateUp    = data.blockStateBuilder().stringProperty("create:facing", "up").build();
        var stateNorth = data.blockStateBuilder().stringProperty("create:facing", "north").build();
        var stateSouth = data.blockStateBuilder().stringProperty("create:facing", "south").build();
        var stateEast  = data.blockStateBuilder().stringProperty("create:facing", "east").build();
        var stateWest  = data.blockStateBuilder().stringProperty("create:facing", "west").build();

        for (int rawId : rawIds) {
            int shiftedId = BridgeConfig.OFFSET + rawId;
            var targetState = stateNorth;

            String facing = com.createbridge.config.BlockProperties.getFacing(rawId);
            if (facing != null) {
                switch (facing) {
                    case "down" -> targetState = stateDown;
                    case "up" -> targetState = stateUp;
                    case "north" -> targetState = stateNorth;
                    case "south" -> targetState = stateSouth;
                    case "west" -> targetState = stateWest;
                    case "east" -> targetState = stateEast;
                }
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
    }

    private FacingBlockRegistrar() {}
}
