package com.createbridge.config;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

public final class BlockProperties {
    private static final Map<Integer, String> FACING_MAP = new HashMap<>();
    private static final Map<Integer, String> AXIS_MAP = new HashMap<>();
    private static final Map<Integer, Map<String, String>> ALL_PROPERTIES = new HashMap<>();
    private static boolean loaded = false;

    public static synchronized void load() {
        if (loaded) return;
        loaded = true;
        try (InputStream is = BlockProperties.class.getClassLoader().getResourceAsStream("blockstate_properties.json")) {
            if (is != null) {
                try (InputStreamReader reader = new InputStreamReader(is)) {
                    JsonObject obj = JsonParser.parseReader(reader).getAsJsonObject();
                    for (Map.Entry<String, JsonElement> entry : obj.entrySet()) {
                        int rawId = Integer.parseInt(entry.getKey());
                        JsonObject prop = entry.getValue().getAsJsonObject();
                        Map<String, String> pMap = new HashMap<>(4);
                        for (Map.Entry<String, JsonElement> pEntry : prop.entrySet()) {
                            pMap.put(pEntry.getKey(), pEntry.getValue().getAsString());
                        }
                        ALL_PROPERTIES.put(rawId, pMap);
                        if (prop.has("facing")) {
                            FACING_MAP.put(rawId, prop.get("facing").getAsString());
                        }
                        if (prop.has("axis")) {
                            AXIS_MAP.put(rawId, prop.get("axis").getAsString());
                        }
                    }
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static String getProperty(int rawId, String key) {
        if (!loaded) load();
        Map<String, String> m = ALL_PROPERTIES.get(rawId);
        return m != null ? m.get(key) : null;
    }

    public static String getFacing(int rawId) {
        if (!loaded) load();
        return FACING_MAP.get(rawId);
    }

    public static String getAxis(int rawId) {
        if (!loaded) load();
        return AXIS_MAP.get(rawId);
    }

    public static boolean isConnectionTrue(int rawId, String dir) {
        return "true".equals(getProperty(rawId, dir));
    }

    public static boolean hasFacing(String name, Iterable<Integer> rawIds) {
        if (!loaded) load();
        for (int id : rawIds) {
            if (FACING_MAP.containsKey(id)) return true;
        }
        return false;
    }

    public static boolean hasAxis(String name, Iterable<Integer> rawIds) {
        if (!loaded) load();
        for (int id : rawIds) {
            if (AXIS_MAP.containsKey(id)) return true;
        }
        return false;
    }

    public static boolean has6WayConnections(String name, Iterable<Integer> rawIds) {
        if (!loaded) load();
        for (int id : rawIds) {
            Map<String, String> m = ALL_PROPERTIES.get(id);
            if (m != null && (m.containsKey("north") || m.containsKey("south") || m.containsKey("east") || m.containsKey("west") || m.containsKey("up") || m.containsKey("down"))) {
                return true;
            }
        }
        return false;
    }

    private BlockProperties() {}
}
