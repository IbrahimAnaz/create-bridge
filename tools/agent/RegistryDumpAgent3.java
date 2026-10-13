package tools.agent;

import java.io.File;
import java.io.FileWriter;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.*;

public class RegistryDumpAgent3 {
    public static void agentmain(String args, Instrumentation inst) {
        System.out.println("[RegistryDumpAgent3] Successfully injected into target JVM!");
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
                System.err.println("[RegistryDumpAgent3] Failed to find BuiltInRegistries or Block class!");
                return;
            }

            Field blockRegField = birClass.getField("BLOCK");
            Object blockReg = blockRegField.get(null);
            Method blockGetKeyMethod = blockReg.getClass().getMethod("getKey", Object.class);

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

            Map<String, Map<String, Integer>> detailedBlockStates = new TreeMap<>();

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
                    String stateDesc = state.toString();
                    detailedBlockStates.computeIfAbsent(keyStr, k -> new LinkedHashMap<>()).put(stateDesc, stateId);
                }
            }

            File outFile = new File("C:/Users/ibrah/Downloads/crt aro/create_detailed_blockstates.json");
            StringBuilder json = new StringBuilder("{\n");
            int i = 0, n = detailedBlockStates.size();
            for (Map.Entry<String, Map<String, Integer>> entry : detailedBlockStates.entrySet()) {
                json.append("  \"").append(entry.getKey()).append("\": {\n");
                int j = 0, m = entry.getValue().size();
                for (Map.Entry<String, Integer> stateEntry : entry.getValue().entrySet()) {
                    // escape quotes if any
                    String esc = stateEntry.getKey().replace("\"", "\\\"");
                    json.append("    \"").append(esc).append("\": ").append(stateEntry.getValue());
                    if (++j < m) json.append(",");
                    json.append("\n");
                }
                json.append("  }");
                if (++i < n) json.append(",");
                json.append("\n");
            }
            json.append("}\n");

            try (FileWriter fw = new FileWriter(outFile)) {
                fw.write(json.toString());
            }

            System.out.println("[RegistryDumpAgent3] Successfully dumped detailed blockstates to " + outFile.getAbsolutePath() + "!");
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
