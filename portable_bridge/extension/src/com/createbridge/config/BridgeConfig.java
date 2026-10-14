package com.createbridge.config;

import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBoundingBox;

public final class BridgeConfig {
    public static final int OFFSET = 100000;
    public static final int ITEM_OFFSET = 10000;

    public static final JavaBoundingBox[] CUBE_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    };

    public static final JavaBoundingBox[] DEPOT_COLLISION = new JavaBoundingBox[]{
        new JavaBoundingBox(0.0, 0.0, 0.0, 1.0, 0.8125, 1.0)
    };

    private BridgeConfig() {}
}
