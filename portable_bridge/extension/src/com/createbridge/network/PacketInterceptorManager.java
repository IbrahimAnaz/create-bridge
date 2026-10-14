package com.createbridge.network;

import com.createbridge.config.BridgeConfig;
import com.createbridge.ui.CommandSanitizer;
import org.cloudburstmc.math.vector.Vector2f;
import org.cloudburstmc.math.vector.Vector3f;
import org.cloudburstmc.math.vector.Vector3i;
import org.cloudburstmc.nbt.NbtMap;
import org.cloudburstmc.protocol.bedrock.data.definitions.BlockDefinition;
import org.cloudburstmc.protocol.bedrock.data.definitions.ItemDefinition;
import org.cloudburstmc.protocol.bedrock.data.entity.EntityDataMap;
import org.cloudburstmc.protocol.bedrock.data.entity.EntityDataTypes;
import org.cloudburstmc.protocol.bedrock.data.entity.EntityFlag;
import org.cloudburstmc.protocol.bedrock.data.inventory.ItemData;
import org.cloudburstmc.protocol.bedrock.packet.AddEntityPacket;
import org.cloudburstmc.protocol.bedrock.packet.AddItemEntityPacket;
import org.cloudburstmc.protocol.bedrock.packet.BlockEntityDataPacket;
import org.cloudburstmc.protocol.bedrock.packet.BlockPickRequestPacket;
import org.cloudburstmc.protocol.bedrock.packet.CommandRequestPacket;
import org.cloudburstmc.protocol.bedrock.packet.InventoryTransactionPacket;
import org.cloudburstmc.protocol.bedrock.packet.MobEquipmentPacket;
import org.cloudburstmc.protocol.bedrock.packet.PlayerHotbarPacket;
import org.cloudburstmc.protocol.bedrock.packet.RemoveEntityPacket;
import org.cloudburstmc.protocol.bedrock.packet.UpdateBlockPacket;
import org.geysermc.geyser.GeyserImpl;
import org.geysermc.geyser.entity.type.ItemFrameEntity;
import org.geysermc.geyser.inventory.GeyserItemStack;
import org.geysermc.geyser.level.block.type.BlockState;
import org.geysermc.geyser.registry.Registries;
import org.geysermc.geyser.registry.type.ItemMapping;
import org.geysermc.geyser.session.GeyserSession;
import org.geysermc.geyser.translator.protocol.PacketTranslator;
import org.geysermc.mcprotocollib.protocol.data.game.entity.player.GameMode;
import org.geysermc.mcprotocollib.protocol.data.game.item.ItemStack;
import org.geysermc.mcprotocollib.protocol.data.game.level.block.BlockEntityInfo;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundBlockEntityDataPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundBlockUpdatePacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundForgetLevelChunkPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.level.ClientboundLevelChunkWithLightPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.inventory.ServerboundPickItemFromEntityPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.inventory.ServerboundSetCreativeModeSlotPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.player.ServerboundSetCarriedItemPacket;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

public final class PacketInterceptorManager {

    private static final Map<GeyserSession, Map<Vector3i, Long>> SESSION_DEPOT_ENTITIES = new ConcurrentHashMap<>();
    private static final Map<GeyserSession, java.util.Set<Vector3i>> SESSION_DEPOT_POSITIONS = new ConcurrentHashMap<>();
    private static final Map<Vector3i, DepotStoredItem> LAST_KNOWN_DEPOTS = new ConcurrentHashMap<>();
    private static final java.util.Set<GeyserSession> CLIENT_READY_SESSIONS = ConcurrentHashMap.newKeySet();

    private record DepotStoredItem(String itemId, int count) {}

    @SuppressWarnings("unchecked")
    public static void registerAll() {
        try {
            // 1. Fallback Depot Block Entity NBT
            PacketTranslator<ClientboundBlockEntityDataPacket> origBlockEntity =
                (PacketTranslator<ClientboundBlockEntityDataPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundBlockEntityDataPacket.class);
            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundBlockEntityDataPacket.class, new PacketTranslator<ClientboundBlockEntityDataPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundBlockEntityDataPacket packet) {
                    if (origBlockEntity != null) origBlockEntity.translate(session, packet);
                    processDepotNbt(session, packet.getPosition(), (NbtMap) (Object) packet.getNbt());
                }
            });

            // 2. Level Chunk Packet (with instant sync of known depots in that chunk)
            PacketTranslator<ClientboundLevelChunkWithLightPacket> origChunk =
                (PacketTranslator<ClientboundLevelChunkWithLightPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundLevelChunkWithLightPacket.class);
            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundLevelChunkWithLightPacket.class, new PacketTranslator<ClientboundLevelChunkWithLightPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundLevelChunkWithLightPacket packet) {
                    if (origChunk != null) origChunk.translate(session, packet);
                    int chunkX = packet.getX();
                    int chunkZ = packet.getZ();
                    int chunkBlockX = chunkX << 4;
                    int chunkBlockZ = chunkZ << 4;

                    BlockEntityInfo[] beList = packet.getBlockEntities();
                    if (beList != null) {
                        for (BlockEntityInfo be : beList) {
                            if (be.getNbt() != null) {
                                Vector3i pos = Vector3i.from(chunkBlockX + be.getX(), be.getY(), chunkBlockZ + be.getZ());
                                if ("create:depot".equals(be.getNbt().getString("id", ""))) {
                                    SESSION_DEPOT_POSITIONS.computeIfAbsent(session, s -> ConcurrentHashMap.newKeySet()).add(pos);
                                }
                                processDepotNbt(session, pos, (NbtMap) (Object) be.getNbt());
                            }
                        }
                    }
                }
            });

            // 3. Block Update Packet
            PacketTranslator<ClientboundBlockUpdatePacket> origBlockUpdate =
                (PacketTranslator<ClientboundBlockUpdatePacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundBlockUpdatePacket.class);
            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundBlockUpdatePacket.class, new PacketTranslator<ClientboundBlockUpdatePacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundBlockUpdatePacket packet) {
                    int shiftedId = packet.getEntry().getBlock();
                    Vector3i pos = packet.getEntry().getPosition();
                    var bb = session.getBlockMappings().getBedrockBlock(shiftedId);
                    Map<Vector3i, Long> depotMap = SESSION_DEPOT_ENTITIES.get(session);
                    java.util.Set<Vector3i> depotPositions = SESSION_DEPOT_POSITIONS.computeIfAbsent(session, s -> ConcurrentHashMap.newKeySet());
                    if (bb != null && bb.getState() != null && "create:depot".equals(bb.getState().getString("name"))) {
                        depotPositions.add(pos);
                    } else {
                        depotPositions.remove(pos);
                        if (depotMap != null && depotMap.containsKey(pos)) {
                            despawnDepotItem(session, pos);
                        }
                    }
                    if (origBlockUpdate != null) origBlockUpdate.translate(session, packet);
                }
            });

            // 4. Chunk Unload GC
            PacketTranslator<ClientboundForgetLevelChunkPacket> origForgetChunk =
                (PacketTranslator<ClientboundForgetLevelChunkPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundForgetLevelChunkPacket.class);
            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundForgetLevelChunkPacket.class, new PacketTranslator<ClientboundForgetLevelChunkPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundForgetLevelChunkPacket packet) {
                    if (origForgetChunk != null) origForgetChunk.translate(session, packet);
                    int chunkX = packet.getX();
                    int chunkZ = packet.getZ();
                    Map<Vector3i, Long> depotMap = SESSION_DEPOT_ENTITIES.get(session);
                    java.util.Set<Vector3i> depotPositions = SESSION_DEPOT_POSITIONS.get(session);
                    if (depotPositions != null) {
                        depotPositions.removeIf(pos -> (pos.getX() >> 4) == chunkX && (pos.getZ() >> 4) == chunkZ);
                    }
                    if (depotMap != null) {
                        depotMap.keySet().removeIf(pos -> {
                            if ((pos.getX() >> 4) == chunkX && (pos.getZ() >> 4) == chunkZ) {
                                despawnDepotItem(session, pos);
                                return true;
                            }
                            return false;
                        });
                    }
                }
            });

            // 5. CommandRequestPacket Hook
            PacketTranslator<CommandRequestPacket> origCmdTranslator =
                (PacketTranslator<CommandRequestPacket>) (PacketTranslator<?>) Registries.BEDROCK_PACKET_TRANSLATORS.get(CommandRequestPacket.class);
            Registries.BEDROCK_PACKET_TRANSLATORS.register(CommandRequestPacket.class, new PacketTranslator<CommandRequestPacket>() {
                @Override
                public void translate(GeyserSession session, CommandRequestPacket packet) {
                    if (packet.getCommand() != null) {
                        String sanitized = CommandSanitizer.rewriteCommand(packet.getCommand());
                        if (!sanitized.equals(packet.getCommand())) {
                            System.out.println("[CreateBridge-Cmd] Rewrote Bedrock command: '" + packet.getCommand() + "' -> '" + sanitized + "'");
                            packet.setCommand(sanitized);
                        }
                    }
                    if (origCmdTranslator != null) origCmdTranslator.translate(session, packet);
                }
            });

            // 6. Detailed Inventory Packet Interceptor & Logger
            InventoryPacketListener.register();

            // 7. BlockPickRequestPacket Hook (Java 1.21.1 Compatible Pick Block)
            PacketTranslator<BlockPickRequestPacket> origPickTranslator =
                (PacketTranslator<BlockPickRequestPacket>) (PacketTranslator<?>) Registries.BEDROCK_PACKET_TRANSLATORS.get(BlockPickRequestPacket.class);
            Registries.BEDROCK_PACKET_TRANSLATORS.register(BlockPickRequestPacket.class, new PacketTranslator<BlockPickRequestPacket>() {
                @Override
                public void translate(GeyserSession session, BlockPickRequestPacket packet) {
                    handleBlockPick(session, packet, origPickTranslator);
                }
            });

        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static void cleanupSession(GeyserSession session) {
        CLIENT_READY_SESSIONS.remove(session);
        SESSION_DEPOT_ENTITIES.remove(session);
        SESSION_DEPOT_POSITIONS.remove(session);
    }

    public static void onPlayerSpawned(GeyserSession session) {
        if (session == null || session.isClosed()) return;
        CLIENT_READY_SESSIONS.add(session);
        System.out.println("[CreateBridge-Depot] Bedrock client registered as ready! Syncing " + LAST_KNOWN_DEPOTS.size() + " active depot items...");
        for (Map.Entry<Vector3i, DepotStoredItem> entry : LAST_KNOWN_DEPOTS.entrySet()) {
            Vector3i pos = entry.getKey();
            DepotStoredItem item = entry.getValue();
            spawnOrUpdateDepotItem(session, pos, item.itemId(), item.count());
        }
    }

    // --- Authoritative Server Push Callbacks (< 0.1ms latency) ---

    public static void onServerDepotUpdate(Vector3i pos, String itemId, int count) {
        LAST_KNOWN_DEPOTS.put(pos, new DepotStoredItem(itemId, count));
        try {
            for (GeyserSession session : GeyserImpl.getInstance().onlineConnections()) {
                if (session != null && !session.isClosed()) {
                    if (session.isSpawned() || CLIENT_READY_SESSIONS.contains(session)) {
                        CLIENT_READY_SESSIONS.add(session);
                        spawnOrUpdateDepotItem(session, pos, itemId, count);
                    }
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static void onServerDepotClear(Vector3i pos) {
        LAST_KNOWN_DEPOTS.remove(pos);
        try {
            for (GeyserSession session : GeyserImpl.getInstance().onlineConnections()) {
                if (session != null && !session.isClosed()) {
                    if (session.isSpawned() || CLIENT_READY_SESSIONS.contains(session)) {
                        CLIENT_READY_SESSIONS.add(session);
                        despawnDepotItem(session, pos);
                    }
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    // --- Bedrock Client Hand Interaction Listener ---

    static void handleDepotInteraction(GeyserSession session, InventoryTransactionPacket packet) {
        if (packet.getTransactionType() != org.cloudburstmc.protocol.bedrock.data.inventory.transaction.InventoryTransactionType.ITEM_USE
                || packet.getActionType() != 0) {
            return;
        }

        Vector3i pos = packet.getBlockPosition();
        if (pos == null) return;

        java.util.Set<Vector3i> depotPositions = SESSION_DEPOT_POSITIONS.computeIfAbsent(session, s -> ConcurrentHashMap.newKeySet());
        boolean isDepot = depotPositions.contains(pos);
        if (!isDepot && depotPositions.contains(pos.down())) {
            pos = pos.down();
            isDepot = true;
        }

        if (!isDepot) {
            try {
                int blockId = session.getChunkCache().getBlockAt(pos.getX(), pos.getY(), pos.getZ());
                if (blockId == 127274 || blockId == 127275) {
                    isDepot = true;
                } else if (blockId >= BridgeConfig.OFFSET) {
                    var bb = session.getBlockMappings().getBedrockBlock(blockId);
                    if (bb != null && bb.getState() != null && "create:depot".equals(bb.getState().getString("name"))) {
                        isDepot = true;
                    }
                }
            } catch (Throwable ignored) {}
        }

        if (isDepot) {
            depotPositions.add(pos);
        } else {
            return;
        }

        ItemData heldItem = packet.getItemInHand();
        if (heldItem == null || heldItem.isNull() || heldItem.getCount() <= 0
                || heldItem.getDefinition() == null
                || "minecraft:air".equals(heldItem.getDefinition().getIdentifier())) {
            System.out.println("[CreateBridge-Depot] Empty-hand interaction at " + pos);
            return;
        }

        System.out.println("[CreateBridge-Depot] Item interaction at " + pos + " with "
                + heldItem.getDefinition().getIdentifier() + " x" + heldItem.getCount());
    }

    private static void processDepotNbt(GeyserSession session, Vector3i pos, NbtMap nbt) {
        if (nbt == null) return;
        String id = nbt.getString("id", "");
        boolean isDepot = id.equals("create:depot") || nbt.containsKey("HeldItem");
        if (!isDepot) return;

        SESSION_DEPOT_POSITIONS.computeIfAbsent(session, s -> ConcurrentHashMap.newKeySet()).add(pos);

        try {
            DepotStoredItem item = readStoredItem(nbt.get("HeldItem"));
            if (item == null) item = readFirstStoredItem(nbt.get("Incoming"));
            if (item == null) item = readFirstStoredItem(nbt.get("OutputBuffer"));

            if (item != null) {
                LAST_KNOWN_DEPOTS.put(pos, item);
                if (CLIENT_READY_SESSIONS.contains(session)) {
                    spawnOrUpdateDepotItem(session, pos, item.itemId(), item.count());
                }
            } else {
                LAST_KNOWN_DEPOTS.remove(pos);
                if (CLIENT_READY_SESSIONS.contains(session)) {
                    despawnDepotItem(session, pos);
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private static DepotStoredItem readFirstStoredItem(Object storedItems) {
        if (storedItems instanceof NbtMap container) {
            storedItems = container.get("Items");
        }
        if (storedItems instanceof Iterable<?> items) {
            for (Object item : items) {
                DepotStoredItem storedItem = readStoredItem(item);
                if (storedItem != null) return storedItem;
            }
        }
        return null;
    }

    private static DepotStoredItem readStoredItem(Object value) {
        if (!(value instanceof NbtMap storedNbt)) return null;
        Object itemValue = storedNbt.get("Item");
        NbtMap itemNbt = itemValue instanceof NbtMap nestedItem ? nestedItem : storedNbt;
        String itemId = itemNbt.getString("id", "");
        Number countValue = itemNbt.getNumber("count", itemNbt.getNumber("Count", 1));
        int count = countValue != null ? countValue.intValue() : 1;
        if (itemId.isEmpty() || "minecraft:air".equals(itemId) || count <= 0) return null;
        return new DepotStoredItem(itemId, count);
    }

    private static void spawnOrUpdateDepotItem(GeyserSession session, Vector3i pos, String itemId, int count) {
        if (session == null || !CLIENT_READY_SESSIONS.contains(session) || session.isClosed()) return;
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
                System.err.println("[CreateBridge] Cannot display depot item without a Bedrock item mapping: " + itemId);
                despawnDepotItem(session, pos);
                return;
            }

            spawnOrUpdateDepotItem(session, pos, itemData);
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    /**
     * Displays a stationary flat item resting directly on top of the depot plate.
     * Places a floor minecraft:frame (facing_direction = 1 [UP]) at pos.up() with ItemRotation = 0.0f.
     */
    private static void spawnOrUpdateDepotItem(GeyserSession session, Vector3i pos, ItemData itemData) {
        if (session == null || session.isClosed()) return;
        Vector3i framePos = pos.up();

        try {
            // 1. Build Definition for upward facing minecraft:frame (facing_direction = 1)
            NbtMap states = NbtMap.builder()
                .putInt("facing_direction", 1)
                .putByte("item_frame_map_bit", (byte) 0)
                .build();
            NbtMap blockTag = NbtMap.builder()
                .putString("name", "minecraft:frame")
                .putCompound("states", states)
                .build();
            BlockDefinition frameDef = session.getBlockMappings().getDefinition(blockTag);

            if (frameDef != null) {
                UpdateBlockPacket updateBlock = new UpdateBlockPacket();
                updateBlock.setDataLayer(0);
                updateBlock.setBlockPosition(framePos);
                updateBlock.setDefinition(frameDef);
                updateBlock.getFlags().addAll(java.util.EnumSet.of(UpdateBlockPacket.Flag.NETWORK, UpdateBlockPacket.Flag.PRIORITY));
                session.sendUpstreamPacket(updateBlock);

                // 2. Build ItemFrame Block Entity NBT with ItemRotation = 0.0f
                NbtMap itemTag = NbtMap.builder()
                    .putString("Name", itemData.getDefinition().getIdentifier())
                    .putByte("Count", (byte) itemData.getCount())
                    .putShort("Damage", (short) itemData.getDamage())
                    .build();

                NbtMap beTag = NbtMap.builder()
                    .putString("id", "ItemFrame")
                    .putInt("x", framePos.getX())
                    .putInt("y", framePos.getY())
                    .putInt("z", framePos.getZ())
                    .putByte("isMovable", (byte) 0)
                    .putCompound("Item", itemTag)
                    .putFloat("ItemRotation", 0.0f)
                    .putFloat("ItemDropChance", 0.0f)
                    .build();

                BlockEntityDataPacket bePacket = new BlockEntityDataPacket();
                bePacket.setBlockPosition(framePos);
                bePacket.setData(beTag);
                session.sendUpstreamPacket(bePacket);

                System.out.println("[CreateBridge-Depot] Displayed flat ItemFrame at " + framePos
                        + " for item " + itemData.getDefinition().getIdentifier() + " x" + itemData.getCount());
                return;
            }
        } catch (Throwable t) {
            System.err.println("[CreateBridge-Depot] Failed to place flat floor item frame: " + t.getMessage());
        }

        // Fallback: AddItemEntityPacket
        Map<Vector3i, Long> depotMap = SESSION_DEPOT_ENTITIES.computeIfAbsent(session, s -> new ConcurrentHashMap<>());
        Long oldId = depotMap.remove(pos);
        if (oldId != null) {
            RemoveEntityPacket rem = new RemoveEntityPacket();
            rem.setUniqueEntityId(oldId);
            session.sendUpstreamPacket(rem);
        }

        long entityId = session.getEntityCache().getNextEntityId().getAndIncrement();
        depotMap.put(pos, entityId);

        AddItemEntityPacket add = new AddItemEntityPacket();
        add.setUniqueEntityId(entityId);
        add.setRuntimeEntityId(entityId);
        add.setItemInHand(itemData);
        add.setPosition(Vector3f.from(
            pos.getX() + 0.5f,
            pos.getY() + 0.82f,
            pos.getZ() + 0.5f
        ));
        add.setMotion(Vector3f.ZERO);
        add.setFromFishing(false);
        EntityDataMap metadata = new EntityDataMap();
        metadata.put(EntityDataTypes.SCALE, 1.0f);
        metadata.put(EntityDataTypes.WIDTH, 0.25f);
        metadata.put(EntityDataTypes.HEIGHT, 0.25f);
        metadata.getOrCreateFlags().put(EntityFlag.HAS_GRAVITY, false);
        metadata.getOrCreateFlags().put(EntityFlag.HAS_COLLISION, false);
        add.setMetadata(metadata);
        session.sendUpstreamPacket(add);
    }

    private static void despawnDepotItem(GeyserSession session, Vector3i pos) {
        if (session == null || session.isClosed()) return;
        Vector3i framePos = pos.up();

        // 1. Clear floor item frame at pos.up() by restoring air
        try {
            BlockDefinition airDef = session.getBlockMappings().getBedrockAir();
            if (airDef != null) {
                UpdateBlockPacket updateBlock = new UpdateBlockPacket();
                updateBlock.setDataLayer(0);
                updateBlock.setBlockPosition(framePos);
                updateBlock.setDefinition(airDef);
                updateBlock.getFlags().addAll(java.util.EnumSet.of(UpdateBlockPacket.Flag.NETWORK, UpdateBlockPacket.Flag.PRIORITY));
                session.sendUpstreamPacket(updateBlock);
            }
        } catch (Throwable ignored) {}

        // 2. Also clear any fallback entity
        Map<Vector3i, Long> depotMap = SESSION_DEPOT_ENTITIES.get(session);
        if (depotMap != null) {
            Long entityId = depotMap.remove(pos);
            if (entityId != null) {
                RemoveEntityPacket rem = new RemoveEntityPacket();
                rem.setUniqueEntityId(entityId);
                session.sendUpstreamPacket(rem);
            }
        }
        System.out.println("[CreateBridge-Depot] Despawned depot item at " + pos);
    }

    // --- Block Pick Logic ---

    private static void handleBlockPick(GeyserSession session, BlockPickRequestPacket packet, PacketTranslator<BlockPickRequestPacket> fallback) {
        try {
            Vector3i pos = packet.getBlockPosition();
            int hotbarSlot = session.getPlayerInventory().getHeldItemSlot();
            if (hotbarSlot < 0 || hotbarSlot > 8) {
                hotbarSlot = packet.getHotbarSlot();
            }
            if (hotbarSlot < 0 || hotbarSlot > 8) {
                hotbarSlot = 0;
            }
            int targetJavaSlot = 36 + hotbarSlot;

            int blockStateId = session.getChunkCache().getBlockAt(pos.getX(), pos.getY(), pos.getZ());
            System.out.println("[CreateBridge-Pick] Pick Block at " + pos + " rawBlockId=" + blockStateId + " hotbarSlot=" + hotbarSlot);

            if (blockStateId == 0) {
                ItemFrameEntity itemFrame = ItemFrameEntity.getItemFrameEntity(session, pos);
                if (itemFrame != null) {
                    session.sendDownstreamGamePacket(new ServerboundPickItemFromEntityPacket(itemFrame.javaId(), packet.isAddUserData()));
                    return;
                }
                if (fallback != null) fallback.translate(session, packet);
                return;
            }

            String itemIdentifier = null;
            int javaItemId = -1;

            if (blockStateId >= BridgeConfig.OFFSET) {
                var bedrockBlock = session.getBlockMappings().getBedrockBlock(blockStateId);
                if (bedrockBlock != null && bedrockBlock.getState() != null) {
                    String blockName = bedrockBlock.getState().getString("name");
                    itemIdentifier = resolveCreateBlockToItem(blockName);
                }
            } else {
                BlockState state = BlockState.of(blockStateId);
                org.geysermc.geyser.level.block.type.Block block = state.block();
                org.geysermc.geyser.item.type.Item javaItem = block.asItem();
                if (javaItem != null && javaItem != org.geysermc.geyser.item.Items.AIR) {
                    javaItemId = javaItem.javaId();
                    itemIdentifier = javaItem.javaIdentifier();
                }
            }

            ItemMapping mapping = null;
            if (itemIdentifier != null) {
                mapping = session.getItemMappings().getMapping(itemIdentifier);
                if (mapping == null && !itemIdentifier.contains(":")) {
                    mapping = session.getItemMappings().getMapping("minecraft:" + itemIdentifier);
                }
            }
            if (mapping == null && javaItemId != -1) {
                mapping = session.getItemMappings().getMapping(javaItemId);
            }

            if (mapping == null || mapping.getJavaItem() == null) {
                System.out.println("[CreateBridge-Pick] Could not map block to item (identifier=" + itemIdentifier + ", javaId=" + javaItemId + "), falling back.");
                if (fallback != null) fallback.translate(session, packet);
                return;
            }

            int finalJavaId = mapping.getJavaItem().javaId();
            System.out.println("[CreateBridge-Pick] Resolved block to item: identifier=" + itemIdentifier + " javaId=" + finalJavaId + " bedrock=" + mapping.getBedrockIdentifier());

            // 1. Check if item already exists in the player's hotbar (slots 36-44)
            for (int i = 0; i < 9; i++) {
                GeyserItemStack existing = session.getPlayerInventory().getItem(36 + i);
                if (!existing.isEmpty() && existing.getJavaId() == finalJavaId) {
                    System.out.println("[CreateBridge-Pick] Item already in hotbar slot " + i + ", selecting it.");
                    session.sendDownstreamGamePacket(new ServerboundSetCarriedItemPacket(i));
                    session.getPlayerInventory().setHeldItemSlot(i);
                    PlayerHotbarPacket hotbarPacket = new PlayerHotbarPacket();
                    hotbarPacket.setSelectedHotbarSlot(i);
                    hotbarPacket.setContainerId(0);
                    hotbarPacket.setSelectHotbarSlot(true);
                    session.sendUpstreamPacket(hotbarPacket);
                    return;
                }
            }

            // 2. In Creative mode: set the slot directly and send ServerboundSetCreativeModeSlotPacket
            if (session.getGameMode() == GameMode.CREATIVE) {
                ItemStack javaItemStack = new ItemStack(finalJavaId, 1, null);
                GeyserItemStack geyserItemStack = GeyserItemStack.of(session, finalJavaId, 1);

                session.getPlayerInventory().setItem(targetJavaSlot, geyserItemStack, session);
                session.getPlayerInventoryHolder().translator().updateSlot(session, session.getPlayerInventory(), targetJavaSlot);

                session.sendDownstreamGamePacket(new ServerboundSetCreativeModeSlotPacket((short) targetJavaSlot, javaItemStack));

                session.sendDownstreamGamePacket(new ServerboundSetCarriedItemPacket(hotbarSlot));
                session.getPlayerInventory().setHeldItemSlot(hotbarSlot);
                PlayerHotbarPacket hotbarPacket = new PlayerHotbarPacket();
                hotbarPacket.setSelectedHotbarSlot(hotbarSlot);
                hotbarPacket.setContainerId(0);
                hotbarPacket.setSelectHotbarSlot(true);
                session.sendUpstreamPacket(hotbarPacket);
            } else {
                int foundInvSlot = -1;
                for (int slot = 9; slot < 36; slot++) {
                    GeyserItemStack existing = session.getPlayerInventory().getItem(slot);
                    if (!existing.isEmpty() && existing.getJavaId() == finalJavaId) {
                        foundInvSlot = slot;
                        break;
                    }
                }
                if (foundInvSlot != -1) {
                    GeyserItemStack invItem = session.getPlayerInventory().getItem(foundInvSlot);
                    GeyserItemStack hotbarItem = session.getPlayerInventory().getItem(targetJavaSlot);
                    session.getPlayerInventory().setItem(targetJavaSlot, invItem, session);
                    session.getPlayerInventory().setItem(foundInvSlot, hotbarItem, session);
                    session.getPlayerInventoryHolder().translator().updateSlot(session, session.getPlayerInventory(), targetJavaSlot);
                    session.getPlayerInventoryHolder().translator().updateSlot(session, session.getPlayerInventory(), foundInvSlot);

                    session.sendDownstreamGamePacket(new ServerboundSetCarriedItemPacket(hotbarSlot));
                    session.getPlayerInventory().setHeldItemSlot(hotbarSlot);
                    PlayerHotbarPacket hotbarPacket = new PlayerHotbarPacket();
                    hotbarPacket.setSelectedHotbarSlot(hotbarSlot);
                    hotbarPacket.setContainerId(0);
                    hotbarPacket.setSelectHotbarSlot(true);
                    session.sendUpstreamPacket(hotbarPacket);
                } else {
                    if (fallback != null) fallback.translate(session, packet);
                }
            }

        } catch (Throwable t) {
            System.err.println("[CreateBridge-Pick] Error handling BlockPickRequestPacket: " + t.getMessage());
            t.printStackTrace();
            if (fallback != null) fallback.translate(session, packet);
        }
    }

    private static String resolveCreateBlockToItem(String blockId) {
        if (blockId == null) return null;
        if (blockId.equals("create:lit_blaze_burner")) return "create:blaze_burner";
        if (blockId.equals("create:water_wheel_structure")) return "create:water_wheel";
        if (blockId.equals("create:small_bogey") || blockId.equals("create:large_bogey")) return "create:railway_casing";
        if (blockId.equals("create:mechanical_piston_head")) return "create:mechanical_piston";
        if (blockId.equals("create:belt")) return "create:belt_connector";
        if (blockId.equals("create:powered_shaft")) return "create:shaft";
        if (blockId.equals("create:metal_girder_encased_shaft")) return "create:metal_girder";
        if (blockId.equals("create:andesite_belt_funnel")) return "create:andesite_funnel";
        if (blockId.equals("create:brass_belt_funnel")) return "create:brass_funnel";
        if (blockId.endsWith("_nixie_tube")) return "create:nixie_tube";
        if (blockId.endsWith("_sail")) return "create:sail_frame";
        if (blockId.equals("create:fake_track")) return "create:track";
        if (blockId.equals("create:copycat_base") || blockId.equals("create:copycat_bars")) return "create:copycat_step";
        return blockId;
    }

    private PacketInterceptorManager() {}
}
