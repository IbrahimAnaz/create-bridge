package com.createbridge.blocks;

import com.createbridge.config.BridgeConfig;
import org.geysermc.geyser.api.block.custom.NonVanillaCustomBlockData;
import org.geysermc.geyser.api.block.custom.component.CustomBlockComponents;
import org.geysermc.geyser.api.block.custom.component.GeometryComponent;
import org.geysermc.geyser.api.block.custom.component.MaterialInstance;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomBlocksEvent;

import java.util.List;

public final class CubeBlockRegistrar {

    public static int registerUnitCube(GeyserDefineCustomBlocksEvent event, String name, String texture, List<Integer> rawIds) {
        String identifier = "create:" + name;
        if (rawIds.isEmpty()) return 0;

        CustomBlockComponents comps = CustomBlockComponents.builder()
            .geometry(GeometryComponent.builder().identifier("geometry.full_block").build())
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
            .build();
        event.register(data);

        for (int rawId : rawIds) {
            int shiftedId = BridgeConfig.OFFSET + rawId;
            event.registerOverride(
                JavaBlockState.builder()
                    .identifier(identifier)
                    .javaId(shiftedId)
                    .stateGroupId(shiftedId)
                    .collision(BridgeConfig.CUBE_COLLISION)
                    .build(),
                data.defaultBlockState()
            );
        }
        return rawIds.size();
    }

    public static void registerStaticGeo(GeyserDefineCustomBlocksEvent event, String name, String texture, String geoId, JavaBoundingBox[] collision, List<Integer> rawIds) {
        String identifier = "create:" + name;
        if (rawIds.isEmpty()) return;

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
            .build();
        event.register(data);

        for (int rawId : rawIds) {
            int shiftedId = BridgeConfig.OFFSET + rawId;
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
    }

    private CubeBlockRegistrar() {}
}
