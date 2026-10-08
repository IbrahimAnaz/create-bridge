package tools.agent;

import java.io.File;
import java.io.FileWriter;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.*;

public class RegistryDumpAgent {
    public static void agentmain(String args, Instrumentation inst) {
        System.out.println("[RegistryDumpAgent] Successfully injected into target JVM!");
        try {
            Class<?> birClass = null;
            Class<?> blockClass = null;
            for (Class<?> clazz : inst.getAllLoadedClasses()) {
                if (clazz.getName().equals("net.minecraft.core.registries.BuiltInRegistries")) {
                    birClass = clazz;
                } else if (clazz.getName().equals("net.minecraft.world.level.block.Block")) {
                    blockClass = clazz;
                }
            }

            if (birClass == null || blockClass == null) {
                System.err.println("[RegistryDumpAgent] Failed to find BuiltInRegistries or Block class!");
                return;
            }

            // 1. Get BuiltInRegistries.BLOCK and BuiltInRegistries.ITEM
            Field blockRegField = birClass.getField("BLOCK");
            Object blockReg = blockRegField.get(null);

            Field itemRegField = birClass.getField("ITEM");
            Object itemReg = itemRegField.get(null);

            Method blockGetKeyMethod = blockReg.getClass().getMethod("getKey", Object.class);
            Method itemGetKeyMethod = itemReg.getClass().getMethod("getKey", Object.class);
            Method itemGetIdMethod = itemReg.getClass().getMethod("getId", Object.class);

            // 2. Get Block.BLOCK_STATE_REGISTRY
            Field bsrField = null;
            for (Field f : blockClass.getFields()) {
                if (f.getName().equals("BLOCK_STATE_REGISTRY")) {
                    bsrField = f;
                    break;
                }
            }
            if (bsrField == null) {
                for (Field f : blockClass.getDeclaredFields()) {
                    if (f.getType().getName().contains("IdMapper")) {
                        f.setAccessible(true);
                        bsrField = f;
                        break;
                    }
                }
            }

            Object blockStateRegistry = bsrField.get(null);
            Method getIdMethod = blockStateRegistry.getClass().getMethod("getId", Object.class);
            Method getBlockMethod = null;

            Map<String, List<Integer>> createBlockStates = new TreeMap<>();
            Map<String, Integer> createItems = new TreeMap<>();

            // Iterate over block states
            Iterable<?> states = (Iterable<?>) blockStateRegistry;
            for (Object state : states) {
                if (getBlockMethod == null) {
                    getBlockMethod = state.getClass().getMethod("getBlock");
                }
                Object block = getBlockMethod.invoke(state);
                Object key = blockGetKeyMethod.invoke(blockReg, block);
                String keyStr = key.toString();
                if (keyStr.startsWith("create:")) {
                    int stateId = (int) getIdMethod.invoke(blockStateRegistry, state);
                    createBlockStates.computeIfAbsent(keyStr, k -> new ArrayList<>()).add(stateId);
                }
            }

            // Iterate over items
            Iterable<?> items = (Iterable<?>) itemReg;
            for (Object item : items) {
                Object key = itemGetKeyMethod.invoke(itemReg, item);
                String keyStr = key.toString();
                if (keyStr.startsWith("create:")) {
                    int itemId = (int) itemGetIdMethod.invoke(itemReg, item);
                    createItems.put(keyStr, itemId);
                }
            }

            // Write JSON
            File outFile = new File("C:/Users/ibrah/Downloads/crt aro/tools/create_registry_dump.json");
            StringBuilder json = new StringBuilder("{\n");
            json.append("  \"items\": {\n");
            int i = 0, n = createItems.size();
            for (Map.Entry<String, Integer> e : createItems.entrySet()) {
                json.append("    \"").append(e.getKey()).append("\": ").append(e.getValue());
                if (++i < n) json.append(",");
                json.append("\n");
            }
            json.append("  },\n");

            json.append("  \"blockstates\": {\n");
            i = 0; n = createBlockStates.size();
            for (Map.Entry<String, List<Integer>> e : createBlockStates.entrySet()) {
                json.append("    \"").append(e.getKey()).append("\": ").append(e.getValue().toString());
                if (++i < n) json.append(",");
                json.append("\n");
            }
            json.append("  }\n");
            json.append("}\n");

            try (FileWriter fw = new FileWriter(outFile)) {
                fw.write(json.toString());
            }

            System.out.println("[RegistryDumpAgent] Successfully dumped " + createItems.size() + " Create items and "
                + createBlockStates.size() + " Create blocks to " + outFile.getAbsolutePath() + "!");

        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
