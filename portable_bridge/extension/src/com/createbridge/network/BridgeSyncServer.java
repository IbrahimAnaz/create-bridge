package com.createbridge.network;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.cloudburstmc.math.vector.Vector3i;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

public final class BridgeSyncServer {

    private static final int PORT = 25575;
    private static final AtomicBoolean RUNNING = new AtomicBoolean(false);
    private static final Set<PrintWriter> CLIENT_WRITERS = ConcurrentHashMap.newKeySet();

    public static void start() {
        if (RUNNING.compareAndSet(false, true)) {
            Thread serverThread = new Thread(BridgeSyncServer::runServer, "CreateBridge-SyncServer");
            serverThread.setDaemon(true);
            serverThread.start();
            System.out.println("[CreateBridge-Sync] Multi-client socket server started on port " + PORT);
        }
    }

    public static void stop() {
        RUNNING.set(false);
    }

    public static void requestSync() {
        String msg = "{\"t\":\"query_depots\"}";
        for (PrintWriter out : CLIENT_WRITERS) {
            try {
                out.println(msg);
            } catch (Throwable ignored) {}
        }
        System.out.println("[CreateBridge-Sync] Requested depot sync from " + CLIENT_WRITERS.size() + " companion client(s)");
    }

    private static void runServer() {
        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            while (RUNNING.get()) {
                try {
                    Socket socket = serverSocket.accept();
                    socket.setTcpNoDelay(true);
                    Thread t = new Thread(() -> handleConnection(socket), "CreateBridge-SyncConnection");
                    t.setDaemon(true);
                    t.start();
                } catch (Throwable t) {
                    if (!RUNNING.get()) break;
                    System.err.println("[CreateBridge-Sync] Server error: " + t.getMessage());
                }
            }
        } catch (Throwable t) {
            System.err.println("[CreateBridge-Sync] Failed to bind ServerSocket on port " + PORT + ": " + t.getMessage());
        }
    }

    private static void handleConnection(Socket socket) {
        System.out.println("[CreateBridge-Sync] Accepted connection from: " + socket.getRemoteSocketAddress());
        PrintWriter out = null;
        try {
            out = new PrintWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8), true);
            CLIENT_WRITERS.add(out);
            BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));

            String line;
            while ((line = in.readLine()) != null) {
                try {
                    handleMessage(line, out);
                } catch (Throwable t) {
                    System.err.println("[CreateBridge-Sync] Error handling message: " + line + " -> " + t.getMessage());
                }
            }
        } catch (Throwable t) {
            // Connection closed
        } finally {
            if (out != null) {
                CLIENT_WRITERS.remove(out);
            }
            try {
                socket.close();
            } catch (Throwable ignored) {}
            System.out.println("[CreateBridge-Sync] Connection closed: " + socket.getRemoteSocketAddress());
        }
    }

    private static void handleMessage(String line, PrintWriter clientOut) {
        if (line == null || line.isBlank()) return;
        JsonObject obj = JsonParser.parseString(line).getAsJsonObject();
        String type = obj.has("t") ? obj.get("t").getAsString() : "";

        if ("depot_update".equals(type)) {
            int x = obj.get("x").getAsInt();
            int y = obj.get("y").getAsInt();
            int z = obj.get("z").getAsInt();
            String item = obj.get("item").getAsString();
            int count = obj.has("count") ? obj.get("count").getAsInt() : 1;
            Vector3i pos = Vector3i.from(x, y, z);
            System.out.println("[CreateBridge-Sync] Received authoritative depot_update: " + pos + " -> " + item + " x" + count);
            PacketInterceptorManager.onServerDepotUpdate(pos, item, count);

        } else if ("depot_clear".equals(type)) {
            int x = obj.get("x").getAsInt();
            int y = obj.get("y").getAsInt();
            int z = obj.get("z").getAsInt();
            Vector3i pos = Vector3i.from(x, y, z);
            System.out.println("[CreateBridge-Sync] Received authoritative depot_clear: " + pos);
            PacketInterceptorManager.onServerDepotClear(pos);

        } else if ("companion_hello".equals(type)) {
            System.out.println("[CreateBridge-Sync] NeoForge companion online (v" + (obj.has("version") ? obj.get("version").getAsString() : "unknown") + ")");

        } else if ("ping".equals(type)) {
            if (clientOut != null) {
                clientOut.println("{\"t\":\"pong\",\"timestamp\":" + System.currentTimeMillis() + "}");
            }
        }
    }
}
