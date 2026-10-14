package com.createbridge.network;

import org.cloudburstmc.protocol.bedrock.data.inventory.ItemData;
import org.cloudburstmc.protocol.bedrock.data.inventory.itemstack.request.ItemStackRequest;
import org.cloudburstmc.protocol.bedrock.data.inventory.itemstack.request.action.ItemStackRequestAction;
import org.cloudburstmc.protocol.bedrock.data.inventory.transaction.InventoryActionData;
import org.cloudburstmc.protocol.bedrock.packet.InventoryTransactionPacket;
import org.cloudburstmc.protocol.bedrock.packet.ItemStackRequestPacket;
import org.cloudburstmc.protocol.bedrock.packet.PlayerHotbarPacket;
import org.geysermc.geyser.registry.Registries;
import org.geysermc.geyser.session.GeyserSession;
import org.geysermc.geyser.translator.protocol.PacketTranslator;
import org.geysermc.mcprotocollib.protocol.data.game.item.ItemStack;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.inventory.ClientboundContainerSetContentPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.inventory.ClientboundContainerSetSlotPacket;

import java.io.FileWriter;
import java.io.PrintWriter;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

public final class InventoryPacketListener {

    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HH:mm:ss.SSS");
    private static PrintWriter LOG_WRITER = null;

    static {
        try {
            FileWriter fw = new FileWriter("logs/inventory_debug.log", true);
            LOG_WRITER = new PrintWriter(fw, true);
            log("=================== INVENTORY LISTENER INITIALIZED ===================");
        } catch (Throwable t) {
            System.err.println("[CreateBridge] Failed to open inventory_debug.log: " + t.getMessage());
        }
    }

    private static synchronized void log(String line) {
        String msg = "[" + LocalTime.now().format(TIME_FMT) + "] " + line;
        System.out.println("[CreateBridge-Inv] " + line);
        if (LOG_WRITER != null) {
            LOG_WRITER.println(msg);
        }
    }

    @SuppressWarnings("unchecked")
    public static void register() {
        try {
            // 1. ClientboundContainerSetSlotPacket (Java -> Geyser)
            PacketTranslator<ClientboundContainerSetSlotPacket> origSetSlot =
                (PacketTranslator<ClientboundContainerSetSlotPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundContainerSetSlotPacket.class);
            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundContainerSetSlotPacket.class, new PacketTranslator<ClientboundContainerSetSlotPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundContainerSetSlotPacket packet) {
                    try {
                        ItemStack item = packet.getItem();
                        String itemInfo = (item == null) ? "EMPTY" : ("id=" + item.getId() + " count=" + item.getAmount());
                        log("[JAVA->GEYSER SET_SLOT] containerId=" + packet.getContainerId()
                                + " slot=" + packet.getSlot()
                                + " stateId=" + packet.getStateId()
                                + " item=[" + itemInfo + "]");
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                    if (origSetSlot != null) origSetSlot.translate(session, packet);
                }
            });

            // 2. ClientboundContainerSetContentPacket (Java -> Geyser)
            PacketTranslator<ClientboundContainerSetContentPacket> origSetContent =
                (PacketTranslator<ClientboundContainerSetContentPacket>) (PacketTranslator<?>) Registries.JAVA_PACKET_TRANSLATORS.get(ClientboundContainerSetContentPacket.class);
            Registries.JAVA_PACKET_TRANSLATORS.register(ClientboundContainerSetContentPacket.class, new PacketTranslator<ClientboundContainerSetContentPacket>() {
                @Override
                public void translate(GeyserSession session, ClientboundContainerSetContentPacket packet) {
                    try {
                        ItemStack[] items = packet.getItems();
                        int count = (items == null) ? 0 : items.length;
                        StringBuilder sb = new StringBuilder();
                        sb.append("[JAVA->GEYSER SET_CONTENT] containerId=").append(packet.getContainerId())
                          .append(" totalSlots=").append(count)
                          .append(" stateId=").append(packet.getStateId())
                          .append(" non-empty=[");
                        if (items != null) {
                            int nonNullCount = 0;
                            for (int i = 0; i < items.length; i++) {
                                ItemStack it = items[i];
                                if (it != null && it.getAmount() > 0) {
                                    if (nonNullCount++ > 0) sb.append(", ");
                                    sb.append("slot ").append(i).append(": id=").append(it.getId()).append("x").append(it.getAmount());
                                }
                            }
                        }
                        sb.append("]");
                        log(sb.toString());
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                    if (origSetContent != null) origSetContent.translate(session, packet);
                }
            });

            // 3. PlayerHotbarPacket (Bedrock -> Geyser)
            PacketTranslator<PlayerHotbarPacket> origHotbar =
                (PacketTranslator<PlayerHotbarPacket>) (PacketTranslator<?>) Registries.BEDROCK_PACKET_TRANSLATORS.get(PlayerHotbarPacket.class);
            Registries.BEDROCK_PACKET_TRANSLATORS.register(PlayerHotbarPacket.class, new PacketTranslator<PlayerHotbarPacket>() {
                @Override
                public void translate(GeyserSession session, PlayerHotbarPacket packet) {
                    try {
                        log("[BEDROCK->GEYSER HOTBAR] selectedSlot=" + packet.getSelectedHotbarSlot()
                                + " containerId=" + packet.getContainerId()
                                + " isSelect=" + packet.isSelectHotbarSlot());
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                    if (origHotbar != null) origHotbar.translate(session, packet);
                }
            });

            // 4. InventoryTransactionPacket (Bedrock -> Geyser)
            PacketTranslator<InventoryTransactionPacket> origTx =
                (PacketTranslator<InventoryTransactionPacket>) (PacketTranslator<?>) Registries.BEDROCK_PACKET_TRANSLATORS.get(InventoryTransactionPacket.class);
            Registries.BEDROCK_PACKET_TRANSLATORS.register(InventoryTransactionPacket.class, new PacketTranslator<InventoryTransactionPacket>() {
                @Override
                public void translate(GeyserSession session, InventoryTransactionPacket packet) {
                    try {
                        ItemData inHand = packet.getItemInHand();
                        String handInfo = (inHand == null || inHand.getDefinition() == null) ? "EMPTY"
                                : (inHand.getDefinition().getIdentifier() + " x" + inHand.getCount());
                        StringBuilder actionsSb = new StringBuilder();
                        if (packet.getActions() != null) {
                            for (InventoryActionData act : packet.getActions()) {
                                String fromId = (act.getFromItem() != null && act.getFromItem().getDefinition() != null) ? act.getFromItem().getDefinition().getIdentifier() : "air";
                                String toId = (act.getToItem() != null && act.getToItem().getDefinition() != null) ? act.getToItem().getDefinition().getIdentifier() : "air";
                                actionsSb.append(" [src=").append(act.getSource()).append(" slot=").append(act.getSlot())
                                         .append(" from=").append(fromId)
                                         .append(" to=").append(toId).append("]");
                            }
                        }
                        log("[BEDROCK->GEYSER TRANSACTION] type=" + packet.getTransactionType()
                                + " actionType=" + packet.getActionType()
                                + " hotbarSlot=" + packet.getHotbarSlot()
                                + " inHand=[" + handInfo + "]"
                                + " blockPos=" + packet.getBlockPosition()
                                + " actions=" + actionsSb);
                    } catch (Throwable t) {
                        t.printStackTrace();
                    }
                    PacketInterceptorManager.handleDepotInteraction(session, packet);
                    if (origTx != null) origTx.translate(session, packet);
                }
            });

            System.out.println("[CreateBridge] InventoryPacketListener registered successfully!");
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private InventoryPacketListener() {}
}
