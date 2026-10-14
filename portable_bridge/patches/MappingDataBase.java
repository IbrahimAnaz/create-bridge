/*
 * This file is part of ViaVersion - https://github.com/ViaVersion/ViaVersion
 * Copyright (C) 2016-2026 ViaVersion and contributors
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
package com.viaversion.viaversion.api.data;

import com.viaversion.nbt.tag.ByteArrayTag;
import com.viaversion.nbt.tag.CompoundTag;
import com.viaversion.nbt.tag.IntArrayTag;
import com.viaversion.nbt.tag.ListTag;
import com.viaversion.nbt.tag.StringTag;
import com.viaversion.nbt.tag.Tag;
import com.viaversion.viaversion.api.Via;
import com.viaversion.viaversion.api.data.MappingDataLoader.IdentifiersPair;
import com.viaversion.viaversion.api.minecraft.RegistryType;
import com.viaversion.viaversion.api.minecraft.TagData;
import com.viaversion.viaversion.libs.fastutil.ints.IntOpenHashSet;
import com.viaversion.viaversion.libs.fastutil.ints.IntSet;
import com.viaversion.viaversion.util.Key;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;
import java.util.stream.Collectors;
// no nullable

public class MappingDataBase implements MappingData {

    protected final String unmappedVersion;
    protected final String mappedVersion;
    protected FullMappings argumentTypeMappings;
    protected FullMappings entityMappings;
    protected FullMappings recipeSerializerMappings;
    protected FullMappings itemDataSerializerMappings;
    protected FullMappings slotDisplayMappings;
    protected FullMappings attributeMappings;
    protected FullMappings blockEntityMappings;
    protected ParticleMappings particleMappings;
    protected BiMappings itemMappings;
    protected BiMappings blockMappings;
    protected Mappings blockStateMappings;
    protected Mappings soundMappings;
    protected Mappings statisticsMappings;
    protected Mappings enchantmentMappings;
    protected Mappings paintingMappings;
    protected Mappings menuMappings;
    protected Map<RegistryType, List<TagData>> tags;
    /**
     * Set of block ids that have had type or property changes.
     */
    protected IntSet changedBlocks;
    protected Set<String> changedEnvironmentAttributes;

    public MappingDataBase(final String unmappedVersion, final String mappedVersion) {
        this.unmappedVersion = unmappedVersion;
        this.mappedVersion = mappedVersion;
    }

    @Override
    public void load() {
        if (Via.getManager().isDebug()) {
            getLogger().info("Loading " + unmappedVersion + " -> " + mappedVersion + " mappings...");
        }

        final CompoundTag data = readMappingsFile("mappings-" + unmappedVersion + "to" + mappedVersion + ".nbt");
        blockStateMappings = loadMappings(data, "blockstates");
        statisticsMappings = loadMappings(data, "statistics");
        menuMappings = loadMappings(data, "menus");
        enchantmentMappings = loadMappings(data, "enchantments");
        paintingMappings = loadMappings(data, "paintings");

        final CompoundTag unmappedIdentifierData = readUnmappedIdentifiersFile("identifiers-" + unmappedVersion + ".nbt");
        final CompoundTag mappedIdentifierData = readMappedIdentifiersFile("identifiers-" + mappedVersion + ".nbt");
        if (unmappedIdentifierData != null && mappedIdentifierData != null) {
            itemMappings = loadFullOrBiMappings(data, unmappedIdentifierData, mappedIdentifierData, "items");
            blockMappings = loadFullOrBiMappings(data, unmappedIdentifierData, mappedIdentifierData, "blocks");
            soundMappings = loadFullOrBiMappings(data, unmappedIdentifierData, mappedIdentifierData, "sounds");

            entityMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "entities");
            argumentTypeMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "argumenttypes");
            slotDisplayMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "slot_displays");
            recipeSerializerMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "recipe_serializers");
            itemDataSerializerMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "data_component_type");
            attributeMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "attributes");
            blockEntityMappings = loadFullMappings(data, unmappedIdentifierData, mappedIdentifierData, "blockentities");

            final IdentifiersPair particleIdentifiers = identifiersFromGlobalIds(unmappedIdentifierData, mappedIdentifierData, "particles");
            if (particleIdentifiers != null) {
                Mappings particleMappings = loadMappings(data, "particles");
                if (particleMappings == null) {
                    particleMappings = new IdentityMappings(particleIdentifiers.unmapped().size(), particleIdentifiers.mapped().size());
                }
                this.particleMappings = new ParticleMappings(particleIdentifiers, particleMappings);
            }
        } else {
            // Might not have identifiers in older versions
            itemMappings = loadBiMappings(data, "items");
            blockMappings = loadBiMappings(data, "blocks");
            soundMappings = loadMappings(data, "sounds");
        }

        final CompoundTag tagsTag = data.getCompoundTag("tags");
        if (tagsTag != null) {
            this.tags = new EnumMap<>(RegistryType.class);
            loadTags(RegistryType.ITEM, tagsTag);
            loadTags(RegistryType.BLOCK, tagsTag);
            loadTags(RegistryType.ENTITY, tagsTag);
            loadTags(RegistryType.FLUID, tagsTag);
        }

        final IntArrayTag changedBlocks = data.getIntArrayTag("changed_blocks");
        if (changedBlocks != null) {
            this.changedBlocks = new IntOpenHashSet(changedBlocks.getValue());
        }

        final ListTag<StringTag> changedEnvironmentAttributes = data.getListTag("changed_environment_attributes", StringTag.class);
        if (changedEnvironmentAttributes != null) {
            this.changedEnvironmentAttributes = changedEnvironmentAttributes.stream().map(StringTag::getValue).collect(Collectors.toSet());
        }

        loadExtras(data);
    }

    protected List<String> identifiersFromGlobalIds(final CompoundTag mappingsTag, final String key) {
        return MappingDataLoader.INSTANCE.identifiersFromGlobalIds(mappingsTag, key);
    }

    protected IdentifiersPair identifiersFromGlobalIds(final CompoundTag unmappedTag, final CompoundTag mappedTag, final String key) {
        return MappingDataLoader.INSTANCE.identifiersFromGlobalIds(unmappedTag, mappedTag, key);
    }

    protected CompoundTag readMappingsFile(final String name) {
        return MappingDataLoader.INSTANCE.loadNBT(name);
    }

    protected CompoundTag readUnmappedIdentifiersFile(final String name) {
        return MappingDataLoader.INSTANCE.loadNBT(name, true);
    }

    protected CompoundTag readMappedIdentifiersFile(final String name) {
        return MappingDataLoader.INSTANCE.loadNBT(name, true);
    }

    protected Mappings loadMappings(final CompoundTag data, final String key) {
        return MappingDataLoader.INSTANCE.loadMappings(data, key);
    }

    protected BiMappings loadFullOrBiMappings(final CompoundTag data, final CompoundTag unmappedIdentifiersTag, final CompoundTag mappedIdentifiersTag, final String key) {
        final FullMappings mappings = loadFullMappings(data, unmappedIdentifiersTag, mappedIdentifiersTag, key);
        return mappings != null ? mappings : loadBiMappings(data, key);
    }

    protected FullMappings loadFullMappings(final CompoundTag data, final CompoundTag unmappedIdentifiersTag, final CompoundTag mappedIdentifiersTag, final String key) {
        if (!unmappedIdentifiersTag.contains(key) || !mappedIdentifiersTag.contains(key)) {
            return null;
        }

        final IdentifiersPair identifiersPair = identifiersFromGlobalIds(unmappedIdentifiersTag, mappedIdentifiersTag, key);
        Mappings mappings = loadBiMappings(data, key); // Load as bi-mappings to keep the inverse cached
        if (mappings == null) {
            mappings = new IdentityMappings(identifiersPair.unmapped().size(), identifiersPair.mapped().size());
        }
        return createFullMappings(identifiersPair, mappings);
    }

    protected FullMappings createFullMappings(final IdentifiersPair identifiersPair, final Mappings mappings) {
        return FullMappingsBase.of(identifiersPair, mappings);
    }

    protected BiMappings loadBiMappings(final CompoundTag data, final String key) {
        final Mappings mappings = loadMappings(data, key);
        return mappings != null ? BiMappings.of(mappings) : null;
    }

    private void loadTags(final RegistryType type, final CompoundTag data) {
        final CompoundTag tag = data.getCompoundTag(type.identifier());
        if (tag == null) {
            return;
        }

        final List<TagData> tagsList = new ArrayList<>(tags.size());
        for (final Map.Entry<String, Tag> entry : tag.entrySet()) {
            final int[] entries;
            if (entry.getValue() instanceof final ByteArrayTag rangesTag) {
                entries = IdRanges.decodeAsList(rangesTag).toIntArray();
            } else {
                // Old format / if the values need to be sorted
                entries = ((IntArrayTag) entry.getValue()).getValue();
            }
            tagsList.add(new TagData(entry.getKey(), entries));
        }

        this.tags.put(type, tagsList);
    }

    @Override
    public int getNewBlockStateId(final int id) {
        if (id >= 100000) return id;
        if (id >= 25000) return 100000 + id;
        return checkValidity(id, blockStateMappings.getNewId(id), "blockstate");
    }

    @Override
    public int getNewBlockId(final int id) {
        if (id >= 100000) return id;
        if (id >= 25000) return 100000 + id;
        return checkValidity(id, blockMappings.getNewId(id), "block");
    }

    @Override
    public int getOldBlockId(final int id) {
        if (id >= 100000) return id - 100000;
        return blockMappings.inverse().getNewIdOrDefault(id, id);
    }

    @Override
    public int getNewItemId(final int id) {
        if (id >= 10000) return id;
        if (id >= 1000) return 10000 + id;
        return checkValidity(id, itemMappings.getNewId(id), "item");
    }

    @Override
    public int getOldItemId(final int id) {
        if (id >= 10000) return id - 10000;
        return itemMappings.inverse().getNewIdOrDefault(id, id);
    }

    @Override
    public int getNewParticleId(final int id) {
        return checkValidity(id, particleMappings.getNewId(id), "particles");
    }

    @Override
    public int getNewAttributeId(final int id) {
        return checkValidity(id, attributeMappings.getNewId(id), "attributes");
    }

    @Override
    public int getNewSoundId(final int id) {
        return checkValidity(id, soundMappings.getNewId(id), "sound");
    }

    @Override
    public int getOldSoundId(final int id) {
        return soundMappings.inverse().getNewIdOrDefault(id, 0);
    }

    @Override
    public List<TagData> getTags(final RegistryType type) {
        return tags != null ? tags.get(type) : null;
    }

    @Override
    public BiMappings getItemMappings() {
        return itemMappings;
    }

    private FullMappings wrappedFullItemMappings;

    @Override
    public FullMappings getFullItemMappings() {
        if (itemMappings instanceof FullMappings fullItemMappings) {
            if (wrappedFullItemMappings == null) {
                wrappedFullItemMappings = new FullMappings() {
                    @Override
                    public int id(String identifier) { return fullItemMappings.id(identifier); }
                    @Override
                    public int mappedId(String mappedIdentifier) { return fullItemMappings.mappedId(mappedIdentifier); }
                    @Override
                    public Key keyFromId(int id) { return fullItemMappings.keyFromId(id); }
                    @Override
                    public Key keyFromMappedKey(String mappedIdentifier) { return fullItemMappings.keyFromMappedKey(mappedIdentifier); }
                    @Override
                    public Key mappedKeyFromMappedId(int mappedId) {
                        Key k = fullItemMappings.mappedKeyFromMappedId(mappedId);
                        return k != null ? k : Key.of("minecraft", "air");
                    }
                    @Override
                    public Key mappedKeyFromKey(String identifier) { return fullItemMappings.mappedKeyFromKey(identifier); }
                    @Override
                    public boolean isIntIdIdentity() { return fullItemMappings.isIntIdIdentity(); }
                    @Override
                    public FullMappings inverse() { return fullItemMappings.inverse(); }
                    @Override
                    public int getNewId(int id) { return fullItemMappings.getNewId(id); }
                    @Override
                    public void setNewId(int id, int mappedId) { fullItemMappings.setNewId(id, mappedId); }
                    @Override
                    public int size() { return fullItemMappings.size(); }
                    @Override
                    public int mappedSize() { return fullItemMappings.mappedSize(); }
                    @Override
                    public String mappedIdentifier(int mappedId) {
                        String s = fullItemMappings.mappedIdentifier(mappedId);
                        return s != null ? s : "minecraft:air";
                    }
                };
            }
            return wrappedFullItemMappings;
        }
        return null;
    }

    @Override
    public ParticleMappings getParticleMappings() {
        return particleMappings;
    }

    @Override
    public Mappings getBlockMappings() {
        return blockMappings;
    }

    @Override
    public FullMappings getFullBlockMappings() {
        if (blockMappings instanceof FullMappings fullBlockMappings) {
            return fullBlockMappings;
        }
        return null;
    }

    @Override
    public FullMappings getBlockEntityMappings() {
        return blockEntityMappings;
    }

    @Override
    public Mappings getBlockStateMappings() {
        return blockStateMappings;
    }

    @Override
    public Mappings getSoundMappings() {
        return soundMappings;
    }

    @Override
    public FullMappings getFullSoundMappings() {
        if (soundMappings instanceof FullMappings fullSoundMappings) {
            return fullSoundMappings;
        }
        return null;
    }

    @Override
    public Mappings getStatisticsMappings() {
        return statisticsMappings;
    }

    @Override
    public Mappings getMenuMappings() {
        return menuMappings;
    }

    @Override
    public Mappings getEnchantmentMappings() {
        return enchantmentMappings;
    }

    @Override
    public FullMappings getAttributeMappings() {
        return attributeMappings;
    }

    @Override
    public FullMappings getEntityMappings() {
        return entityMappings;
    }

    @Override
    public FullMappings getArgumentTypeMappings() {
        return argumentTypeMappings;
    }

    @Override
    public FullMappings getDataComponentSerializerMappings() {
        return itemDataSerializerMappings;
    }

    @Override
    public Mappings getPaintingMappings() {
        return paintingMappings;
    }

    @Override
    public FullMappings getRecipeSerializerMappings() {
        return recipeSerializerMappings;
    }

    @Override
    public FullMappings getSlotDisplayMappings() {
        return slotDisplayMappings;
    }

    @Override
    public IntSet changedBlocks() {
        return changedBlocks;
    }

    @Override
    public Set<String> changedEnvironmentAttributes() {
        return changedEnvironmentAttributes;
    }

    protected Logger getLogger() {
        return Via.getPlatform().getLogger();
    }

    /**
     * Returns the given mapped id if valid, else 0 with a warning logged to the console.
     *
     * @param id       unmapped id
     * @param mappedId mapped id
     * @param type     mapping type (e.g. "item")
     * @return the given mapped id if valid, else 0
     */
    protected int checkValidity(final int id, final int mappedId, final String type) {
        if (mappedId == -1) {
            if ("blockstate".equals(type) || "block".equals(type)) {
                if (id >= 100000) {
                    return id;
                }
                if (id >= 25000) {
                    return 100000 + id;
                }
                return id;
            }
            if ("item".equals(type)) {
                if (id >= 10000) {
                    return id;
                }
                if (id >= 1000) {
                    return 10000 + id;
                }
                return id;
            }
            return id;
        }
        return mappedId;
    }

    protected void loadExtras(final CompoundTag data) {
    }
}
