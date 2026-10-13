package com.createbridge.companion.net;

import net.minecraft.core.BlockPos;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
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
    private static final AtomicBoolean RUNNING = new AtomicBoolean(false);
    private static volatile PrintWriter writer = null;

    public record DepotState(String item, int count) {}
    public record KineticState(float speed, boolean overstressed) {}

    public static void start() {
        if (RUNNING.compareAndSet(false, true)) {
            Thread worker = new Thread(BridgeSocketClient::runLoop, "CreateBridge-SocketClient");
            worker.setDaemon(true);
            worker.start();
            System.out.println("[CreateBridge-Companion] Background socket client started (targeting " + HOST + ":" + PORT + ")");
        }
    }

    public static void stop() {
        RUNNING.set(false);
    }

    public static void sendDepotUpdate(BlockPos pos, String item, int count) {
        if (pos == null || item == null || item.isEmpty() || count <= 0) return;
        ACTIVE_DEPOTS.put(pos.immutable(), new DepotState(item, count));
        String msg = String.format("{\"t\":\"depot_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"item\":\"%s\",\"count\":%d}",
                pos.getX(), pos.getY(), pos.getZ(), item, count);
        OUTBOX.offer(msg);
        System.out.println("[CreateBridge-Companion] Queued depot update at " + pos + " -> " + item + " x" + count);
    }

    public static void sendDepotClear(BlockPos pos) {
        if (pos == null) return;
        ACTIVE_DEPOTS.remove(pos);
        String msg = String.format("{\"t\":\"depot_clear\",\"x\":%d,\"y\":%d,\"z\":%d}",
                pos.getX(), pos.getY(), pos.getZ());
        OUTBOX.offer(msg);
        System.out.println("[CreateBridge-Companion] Queued depot clear at " + pos);
    }

    public static void sendKineticUpdate(BlockPos pos, float speed, boolean overstressed) {
        if (pos == null) return;
        ACTIVE_KINETICS.put(pos.immutable(), new KineticState(speed, overstressed));
        String msg = String.format(java.util.Locale.ROOT, "{\"t\":\"kinetic_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"speed\":%.2f,\"overstressed\":%b}",
                pos.getX(), pos.getY(), pos.getZ(), speed, overstressed);
        OUTBOX.offer(msg);
    }

    public static void sendKineticClear(BlockPos pos) {
        if (pos == null) return;
        ACTIVE_KINETICS.remove(pos);
        String msg = String.format("{\"t\":\"kinetic_clear\",\"x\":%d,\"y\":%d,\"z\":%d}",
                pos.getX(), pos.getY(), pos.getZ());
        OUTBOX.offer(msg);
    }

    private static void runLoop() {
        while (RUNNING.get()) {
            try (Socket socket = new Socket(HOST, PORT)) {
                socket.setTcpNoDelay(true);
                System.out.println("[CreateBridge-Companion] Connected to Geyser bridge on " + HOST + ":" + PORT);

                PrintWriter out = new PrintWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8), true);
                BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                writer = out;

                // Send handshake and sync any active depots and kinetics
                out.println("{\"t\":\"companion_hello\",\"version\":\"1.0.0\"}");
                syncAll(out);

                // Start reader thread for incoming Geyser queries
                Thread readerThread = new Thread(() -> {
                    try {
                        String line;
                        while ((line = in.readLine()) != null) {
                            if (line.contains("query_depots") || line.contains("query_sync")) {
                                System.out.println("[CreateBridge-Companion] Received sync query from bridge; syncing all active state");
                                syncAll(writer);
                            }
                        }
                    } catch (Throwable ignored) {
                    } finally {
                        try { socket.close(); } catch (Throwable ignored) {}
                        OUTBOX.offer(""); // Wake up flush loop
                    }
                }, "CreateBridge-SocketReader");
                readerThread.setDaemon(true);
                readerThread.start();

                // Outbox flush loop
                while (RUNNING.get() && !socket.isClosed()) {
                    String msg = OUTBOX.take();
                    if (msg.isEmpty()) continue;
                    out.println(msg);
                    if (out.checkError()) {
                        System.err.println("[CreateBridge-Companion] Socket write error; reconnecting...");
                        break;
                    }
                }

            } catch (Throwable t) {
                writer = null;
                // Wait 1.5 seconds before retrying connection
                try {
                    Thread.sleep(1500);
                } catch (InterruptedException ignored) {
                    break;
                }
            }
        }
    }

    private static void syncAll(PrintWriter out) {
        if (out == null) return;
        for (Map.Entry<BlockPos, DepotState> entry : ACTIVE_DEPOTS.entrySet()) {
            BlockPos pos = entry.getKey();
            DepotState state = entry.getValue();
            out.println(String.format("{\"t\":\"depot_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"item\":\"%s\",\"count\":%d}",
                    pos.getX(), pos.getY(), pos.getZ(), state.item(), state.count()));
        }
        for (Map.Entry<BlockPos, KineticState> entry : ACTIVE_KINETICS.entrySet()) {
            BlockPos pos = entry.getKey();
            KineticState state = entry.getValue();
            out.println(String.format(java.util.Locale.ROOT, "{\"t\":\"kinetic_update\",\"x\":%d,\"y\":%d,\"z\":%d,\"speed\":%.2f,\"overstressed\":%b}",
                    pos.getX(), pos.getY(), pos.getZ(), state.speed(), state.overstressed()));
        }
    }
}
