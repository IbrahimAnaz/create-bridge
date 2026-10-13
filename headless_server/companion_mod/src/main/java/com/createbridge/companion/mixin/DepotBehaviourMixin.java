package com.createbridge.companion.mixin;

import com.createbridge.companion.net.BridgeSocketClient;
import com.simibubi.create.content.kinetics.belt.transport.TransportedItemStack;
import com.simibubi.create.content.logistics.depot.DepotBehaviour;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value = DepotBehaviour.class, remap = false)
public abstract class DepotBehaviourMixin {

    private BlockPos createbridge$getPos() {
        return ((DepotBehaviour) (Object) this).getPos();
    }

    @Inject(method = "setHeldItem", at = @At("RETURN"))
    private void createbridge$onSetHeldItem(TransportedItemStack heldItem, CallbackInfo ci) {
        BlockPos pos = createbridge$getPos();
        if (heldItem != null && heldItem.stack != null && !heldItem.stack.isEmpty()) {
            ResourceLocation key = BuiltInRegistries.ITEM.getKey(heldItem.stack.getItem());
            BridgeSocketClient.sendDepotUpdate(pos, key.toString(), heldItem.stack.getCount());
        } else {
            BridgeSocketClient.sendDepotClear(pos);
        }
    }

    @Inject(method = "setCenteredHeldItem", at = @At("RETURN"))
    private void createbridge$onSetCenteredHeldItem(TransportedItemStack heldItem, CallbackInfo ci) {
        BlockPos pos = createbridge$getPos();
        if (heldItem != null && heldItem.stack != null && !heldItem.stack.isEmpty()) {
            ResourceLocation key = BuiltInRegistries.ITEM.getKey(heldItem.stack.getItem());
            BridgeSocketClient.sendDepotUpdate(pos, key.toString(), heldItem.stack.getCount());
        } else {
            BridgeSocketClient.sendDepotClear(pos);
        }
    }

    @Inject(method = "removeHeldItem", at = @At("HEAD"))
    private void createbridge$onRemoveHeldItem(CallbackInfo ci) {
        BridgeSocketClient.sendDepotClear(createbridge$getPos());
    }

    @Inject(method = "destroy", at = @At("HEAD"))
    private void createbridge$onDestroy(CallbackInfo ci) {
        BridgeSocketClient.sendDepotClear(createbridge$getPos());
    }

    @Inject(method = "unload", at = @At("HEAD"))
    private void createbridge$onUnload(CallbackInfo ci) {
        BridgeSocketClient.sendDepotClear(createbridge$getPos());
    }

    @Inject(method = "read", at = @At("RETURN"))
    private void createbridge$onRead(CompoundTag compound, HolderLookup.Provider registries, boolean clientPacket, CallbackInfo ci) {
        DepotBehaviour self = (DepotBehaviour) (Object) this;
        if (self.getHeldItemStack() != null && !self.getHeldItemStack().isEmpty()) {
            ResourceLocation key = BuiltInRegistries.ITEM.getKey(self.getHeldItemStack().getItem());
            BridgeSocketClient.sendDepotUpdate(createbridge$getPos(), key.toString(), self.getHeldItemStack().getCount());
        }
    }
}
