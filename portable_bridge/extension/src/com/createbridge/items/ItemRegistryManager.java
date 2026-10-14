package com.createbridge.items;

import com.createbridge.config.BridgeConfig;
import com.google.gson.JsonObject;
import org.geysermc.geyser.api.event.lifecycle.GeyserDefineCustomItemsEvent;
import org.geysermc.geyser.api.item.custom.v2.CustomItemBedrockOptions;
import org.geysermc.geyser.api.item.custom.v2.NonVanillaCustomItemDefinition;
import org.geysermc.geyser.api.item.custom.v2.component.geyser.GeyserBlockPlacer;
import org.geysermc.geyser.api.item.custom.v2.component.geyser.GeyserItemDataComponents;
import org.geysermc.geyser.api.util.CreativeCategory;
import org.geysermc.geyser.api.util.Identifier;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

public final class ItemRegistryManager {

    public record ItemEntry(String identifier, String name, int rawId, int shiftedId, boolean isBlock) {}

    public static int registerAll(GeyserDefineCustomItemsEvent event, JsonObject dump, java.util.Set<String> blockIdentifiers) {
        if (dump == null || !dump.has("items")) return 0;
        JsonObject itemsObj = dump.getAsJsonObject("items");

        List<ItemEntry> list = new ArrayList<>();
        for (Map.Entry<String, com.google.gson.JsonElement> entry : itemsObj.entrySet()) {
            String fullId = entry.getKey();
            String name = fullId.startsWith("create:") ? fullId.substring(7) : fullId;
            int rawId = entry.getValue().getAsInt();
            int shiftedId = BridgeConfig.ITEM_OFFSET + rawId;
            boolean isBlock = blockIdentifiers.contains(fullId);
            list.add(new ItemEntry(fullId, name, rawId, shiftedId, isBlock));
        }

        // STRICT SORTING BY SHIFTED ID: Guarantees deterministic 1-to-1 Bedrock runtime ID bindings!
        list.sort(Comparator.comparingInt(ItemEntry::shiftedId));

        int count = 0;
        for (ItemEntry item : list) {
            try {
                var bedrockOptions = CustomItemBedrockOptions.builder()
                    .icon("create_" + item.name())
                    .creativeCategory(CreativeCategory.ITEMS)
                    .creativeGroup("itemGroup.name.create");

                var builder = NonVanillaCustomItemDefinition.builder(Identifier.of(item.identifier()), item.shiftedId())
                    .displayName(item.name())
                    .bedrockOptions(bedrockOptions);

                if (item.isBlock()) {
                    builder.component(
                        GeyserItemDataComponents.BLOCK_PLACER,
                        GeyserBlockPlacer.of(Identifier.of(item.identifier()), true)
                    );
                }

                event.register(builder.build());
                count++;
            } catch (Throwable t) {
                System.err.println("[CreateBridge] Item skipped: " + item.identifier() + ": " + t.getMessage());
            }
        }
        return count;
    }

    private ItemRegistryManager() {}
}
