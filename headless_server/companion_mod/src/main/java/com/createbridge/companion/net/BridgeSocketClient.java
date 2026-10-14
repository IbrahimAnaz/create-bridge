package com.createbridge.companion.net;

import net.minecraft.core.BlockPos;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.atomic.AtomicBoolean;

public final class BridgeSocketClient {

    private static final String HOST = "127.0.0.1";
    private static final int PORT = 25575;

    private static final BlockingQueue<String> OUTBOX = new LinkedBlockingQueue<>(5000);
    private static final Map<BlockPos, DepotState> ACTIVE_DEPOTS = new ConcurrentHashMap<>();
    private static final Map<BlockPos, KineticState> ACTIVE_KINETICS = new ConcurrentHashMap<>();
    private static final Map<BlockPos, DeployerState> ACTIVE_DEPLOYERS = new ConcurrentHashMap<>();
    private static final AtomicBoolean RUNNING = new AtomicBoolean(false);

    public record DepotState(String item, int count) {}
    public record KineticState(float speed, boolean overstressed) {}
    public record DeployerState(String mode, String heldItem, int heldCount, float progress) {}

    private BridgeSocketClient() {}

    public static void start() {
        if (!RUNNING.compareAndSet(false, true)) {
            return;
        }
        Thread thread = new Thread(BridgeSocketClient::runLoop, "CreateBridge-SocketClient");
        thread.setDaemon(true);
        thread.start();
        System.out.println("[CreateBridge-Companion] Background socket client started (targeting " + HOST + ":" + PORT + ")");
    }

    public static void stop() {
        RUNNING.set(false);
    }

    public static void sendDepotUpdate(BlockPos pos, String item, int count) {
        if (pos == null) return;
        if (item == null || item.isEmpty() || "minecraft:air".equals(item) || count <= 0) {
            sendDepotClear(pos);
            return;
        }
        DepotState next = new DepotState(item, count);
        DepotState prev = ACTIVE_DEPOTS.put(pos.immutable(), next);
        if (!next.equals(prev)) {
            enqueue(String.format(Locale.ROOT,
                    "{\"t\":\"depot_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"item\":\"%s\",\"count\":%d}",
                    pos.getX(), pos.getY(), pos.getZ(), escapeJson(item), count));
        }
    }

    public static void sendDepotClear(BlockPos pos) {
        if (pos == null) return;
        DepotState removed = ACTIVE_DEPOTS.remove(pos);
        if (removed != null) {
            enqueue(String.format(Locale.ROOT,
                    "{\"t\":\"depot_clear\",\"x\":%d,\"y\":%d,\"z\":%d}",
                    pos.getX(), pos.getY(), pos.getZ()));
        }
    }

    // Legacy alias so older mixin calls still compile
    public static void updateDepot(BlockPos pos, String item, int count) {
        sendDepotUpdate(pos, item, count);
    }

    public static void sendKineticUpdate(BlockPos pos, float speed, boolean overstressed) {
        if (pos == null) return;
        KineticState next = new KineticState(speed, overstressed);
        KineticState prev = ACTIVE_KINETICS.put(pos.immutable(), next);
        if (!next.equals(prev)) {
            enqueue(String.format(Locale.ROOT,
                    "{\"t\":\"kinetic_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"speed\":%.2f,\"overstressed\":%b}",
                    pos.getX(), pos.getY(), pos.getZ(), speed, overstressed));
        }
    }

    public static void sendKineticClear(BlockPos pos) {
        if (pos == null) return;
        if (ACTIVE_KINETICS.remove(pos) != null) {
            enqueue(String.format(Locale.ROOT,
                    "{\"t\":\"kinetic_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"speed\":0.0,\"overstressed\":false}",
                    pos.getX(), pos.getY(), pos.getZ()));
        }
    }

    public static void sendDeployerUpdate(BlockPos pos, String mode, String heldItem, int heldCount, float progress) {
        if (pos == null) return;
        String safeMode = mode == null ? "USE" : mode;
        String safeItem = heldItem == null ? "" : heldItem;
        float roundedProgress = Math.round(progress * 20.0f) / 20.0f; // 5% step quantization to avoid tick spam
        DeployerState next = new DeployerState(safeMode, safeItem, Math.max(0, heldCount), roundedProgress);
        DeployerState prev = ACTIVE_DEPLOYERS.put(pos.immutable(), next);
        if (!next.equals(prev)) {
            enqueue(String.format(Locale.ROOT,
                    "{\"t\":\"deployer_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"mode\":\"%s\",\"held_item\":\"%s\",\"held_count\":%d,\"progress\":%.2f}",
                    pos.getX(), pos.getY(), pos.getZ(), escapeJson(safeMode), escapeJson(safeItem), Math.max(0, heldCount), roundedProgress));
        }
    }

    private static String escapeJson(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static void enqueue(String message) {
        if (!OUTBOX.offer(message)) {
            OUTBOX.poll();
            OUTBOX.offer(message);
        }
    }

    private static void runLoop() {
        while (RUNNING.get()) {
            try (Socket socket = new Socket(HOST, PORT);
                 PrintWriter out = new PrintWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8), true);
                 BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {

                System.out.println("[CreateBridge-Companion] Connected to Geyser Bridge on port " + PORT);

                // Replay cached state on reconnect so BridgeSyncServer has full world state immediately
                for (Map.Entry<BlockPos, DepotState> e : ACTIVE_DEPOTS.entrySet()) {
                    BlockPos p = e.getKey();
                    DepotState s = e.getValue();
                    out.println(String.format(Locale.ROOT,
                            "{\"t\":\"depot_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"item\":\"%s\",\"count\":%d}",
                            p.getX(), p.getY(), p.getZ(), escapeJson(s.item()), s.count()));
                }
                for (Map.Entry<BlockPos, KineticState> e : ACTIVE_KINETICS.entrySet()) {
                    BlockPos p = e.getKey();
                    KineticState s = e.getValue();
                    out.println(String.format(Locale.ROOT,
                            "{\"t\":\"kinetic_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"speed\":%.2f,\"overstressed\":%b}",
                            p.getX(), p.getY(), p.getZ(), s.speed(), s.overstressed()));
                }

                while (RUNNING.get() && !socket.isClosed()) {
                    out.println(OUTBOX.take());
                }
            } catch (Exception e) {
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
    }
}
