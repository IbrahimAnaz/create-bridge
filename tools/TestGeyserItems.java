import org.geysermc.geyser.item.type.Item;
import org.geysermc.geyser.registry.Registries;
import org.geysermc.geyser.registry.type.ItemMapping;
import org.geysermc.geyser.registry.type.ItemMappings;

import java.lang.reflect.Method;
import java.util.List;

public class TestGeyserItems {
    public static void main(String[] args) throws Exception {
        System.out.println("Checking Geyser's ItemMappings...");
        // Let's inspect Registries.JAVA_ITEMS
        List<Item> javaItems = Registries.JAVA_ITEMS.get();
        System.out.println("JAVA_ITEMS size: " + (javaItems != null ? javaItems.size() : "null"));
    }
}
