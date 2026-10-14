package com.createbridge.ui;

import com.google.gson.JsonObject;
import org.cloudburstmc.protocol.bedrock.data.command.CommandEnumConstraint;
import org.cloudburstmc.protocol.bedrock.data.command.CommandEnumData;
import org.cloudburstmc.protocol.bedrock.data.command.CommandOverloadData;
import org.cloudburstmc.protocol.bedrock.data.command.CommandParamData;
import org.geysermc.geyser.api.event.java.ServerDefineCommandsEvent;

import java.lang.reflect.Method;
import java.util.*;

public final class CommandSanitizer {

    private static final Set<String> BLOCKED_NAMES = Set.of("c", "catnip", "ponder", "neoforge");

    public static void sanitize(ServerDefineCommandsEvent event, JsonObject dump) {
        Iterator<? extends ServerDefineCommandsEvent.CommandInfo> it = event.commands().iterator();
        while (it.hasNext()) {
            ServerDefineCommandsEvent.CommandInfo cmd = it.next();
            String name = cmd.name().toLowerCase(java.util.Locale.ROOT);

            // 1. Remove namespaced or blocked commands that crash Bedrock's command parser
            if (name.contains(":") || BLOCKED_NAMES.contains(name) || !name.matches("^[a-z0-9_]+$")) {
                it.remove();
                continue;
            }

            // 2. Sanitize and enhance overloads
            CommandOverloadData[] overloads = getParamData(cmd);
            if (overloads == null) continue;

            for (CommandOverloadData overload : overloads) {
                CommandParamData[] params = overload.getOverloads();
                if (params == null) continue;

                boolean seenOptional = false;
                for (CommandParamData p : params) {
                    if (p == null) continue;

                    // Clean parameter name
                    if (p.getName() != null && !p.getName().matches("^[a-zA-Z0-9_]+$")) {
                        p.setName(p.getName().replaceAll("[^a-zA-Z0-9_]", "_"));
                    }

                    // Fix Bedrock rule: required parameter CANNOT follow optional parameter
                    if (p.isOptional()) {
                        seenOptional = true;
                    } else if (seenOptional) {
                        p.setOptional(true);
                    }

                    // Enhance give command with all Create items & short aliases
                    if (name.equals("give") && p.getEnumData() != null) {
                        enhanceItemEnum(p, dump);
                    }

                    // Enhance setblock / fill commands with all Create block identifiers
                    if ((name.equals("setblock") || name.equals("fill")) && p.getEnumData() != null) {
                        enhanceBlockEnum(p, dump);
                    }
                }
            }
        }
    }

    private static CommandOverloadData[] getParamData(ServerDefineCommandsEvent.CommandInfo cmd) {
        try {
            Method m = cmd.getClass().getMethod("paramData");
            m.setAccessible(true);
            return (CommandOverloadData[]) m.invoke(cmd);
        } catch (Throwable t1) {
            try {
                java.lang.reflect.Field f = cmd.getClass().getDeclaredField("paramData");
                f.setAccessible(true);
                return (CommandOverloadData[]) f.get(cmd);
            } catch (Throwable t2) {
                return null;
            }
        }
    }

    private static final Set<String> CREATE_SHORT_IDS = new java.util.concurrent.ConcurrentHashMap<String, Boolean>().keySet(true);

    public static String rewriteCommand(String cmd) {
        if (cmd == null || cmd.isEmpty()) return cmd;
        String prefix = cmd.startsWith("/") ? "/" : "";
        String trimmed = cmd.startsWith("/") ? cmd.substring(1) : cmd;
        String[] parts = trimmed.split(" ");
        if (parts.length < 2) return cmd;

        String action = parts[0].toLowerCase(Locale.ROOT);
        boolean isGive = action.equals("give");
        boolean isBlock = action.equals("setblock") || action.equals("fill");
        boolean modified = false;
        if (isGive) {
            for (int i = 1; i < parts.length; i++) {
                if (parts[i].equals("belt") || parts[i].equals("create:belt") || parts[i].equals("create_belt")) {
                    parts[i] = "create:belt_connector";
                    modified = true;
                }
            }
        }
        for (int i = 1; i < parts.length; i++) {
            String token = parts[i];
            if (token.startsWith("create_")) {
                String sub = token.substring(7);
                if (CREATE_SHORT_IDS.contains(sub)) {
                    parts[i] = "create:" + sub;
                    modified = true;
                }
            } else if ((isGive || isBlock) && CREATE_SHORT_IDS.contains(token)) {
                // Avoid rewriting selectors like @a, @s, or coordinates
                if (!token.startsWith("@") && !token.startsWith("~") && !token.startsWith("^")) {
                    parts[i] = "create:" + token;
                    modified = true;
                }
            }
        }
        if (!modified) return cmd;
        return prefix + String.join(" ", parts);
    }

    private static void enhanceItemEnum(CommandParamData p, JsonObject dump) {
        try {
            CommandEnumData oldEnum = p.getEnumData();
            if (oldEnum == null || oldEnum.getValues() == null) return;
            LinkedHashMap<String, Set<CommandEnumConstraint>> newMap = new LinkedHashMap<>(oldEnum.getValues());
            // Bedrock parser fails if enum tokens contain colons
            newMap.keySet().removeIf(k -> k.contains(":"));

            if (dump != null && dump.has("items")) {
                JsonObject items = dump.getAsJsonObject("items");
                for (String fullId : items.keySet()) {
                    if (fullId.startsWith("create:")) {
                        String shortId = fullId.substring(7);
                        CREATE_SHORT_IDS.add(shortId);
                        newMap.put(shortId, Collections.emptySet());
                    }
                }
                CREATE_SHORT_IDS.add("belt");
                newMap.put("belt", Collections.emptySet());
            }
            p.setEnumData(new CommandEnumData(oldEnum.getName(), newMap, false));
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private static void enhanceBlockEnum(CommandParamData p, JsonObject dump) {
        try {
            CommandEnumData oldEnum = p.getEnumData();
            if (oldEnum == null || oldEnum.getValues() == null) return;
            LinkedHashMap<String, Set<CommandEnumConstraint>> newMap = new LinkedHashMap<>(oldEnum.getValues());
            // Bedrock parser fails if enum tokens contain colons
            newMap.keySet().removeIf(k -> k.contains(":"));

            if (dump != null && dump.has("blockstates")) {
                JsonObject states = dump.getAsJsonObject("blockstates");
                for (String fullId : states.keySet()) {
                    if (fullId.startsWith("create:")) {
                        String shortId = fullId.substring(7);
                        CREATE_SHORT_IDS.add(shortId);
                        newMap.put(shortId, Collections.emptySet());
                    }
                }
            }
            p.setEnumData(new CommandEnumData(oldEnum.getName(), newMap, false));
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private CommandSanitizer() {}
}
