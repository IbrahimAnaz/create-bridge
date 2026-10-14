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

public final class KineticBlockRegistrar {

    public static void register(GeyserDefineCustomBlocksEvent event, String name, String texture, String geoId, JavaBoundingBox[] collision, String baseAxis, List<Integer> rawIds) {
        String identifier = "create:" + name;
        if (rawIds.isEmpty()) return;

        List<CustomBlockPermutation> perms;
        if ("z".equals(baseAxis)) {
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
                .ambientOcclusion(true)
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
            int shiftedId = BridgeConfig.OFFSET + rawId;
            var targetState = stateY;

            String axis = com.createbridge.config.BlockProperties.getAxis(rawId);
            if (axis != null) {
                switch (axis) {
                    case "x" -> targetState = stateX;
                    case "y" -> targetState = stateY;
                    case "z" -> targetState = stateZ;
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

    private KineticBlockRegistrar() {}
}
