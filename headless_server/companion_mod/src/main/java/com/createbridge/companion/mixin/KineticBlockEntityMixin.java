package com.createbridge.companion.mixin;

import com.createbridge.companion.net.BridgeSocketClient;
import com.simibubi.create.content.kinetics.base.KineticBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value = KineticBlockEntity.class, remap = false)
public abstract class KineticBlockEntityMixin {

    @Inject(method = "setSpeed", at = @At("RETURN"))
    private void createbridge$onSetSpeed(float speed, CallbackInfo ci) {
        KineticBlockEntity self = (KineticBlockEntity) (Object) this;
        BlockPos pos = self.getBlockPos();
        if (pos != null) {
            BridgeSocketClient.sendKineticUpdate(pos, speed, self.isOverStressed());
        }
    }

    @Inject(method = "clearKineticInformation", at = @At("RETURN"))
    private void createbridge$onClearKineticInfo(CallbackInfo ci) {
        KineticBlockEntity self = (KineticBlockEntity) (Object) this;
        BlockPos pos = self.getBlockPos();
        if (pos != null) {
            BridgeSocketClient.sendKineticUpdate(pos, 0.0f, false);
        }
    }

    @Inject(method = "removeSource", at = @At("RETURN"))
    private void createbridge$onRemoveSource(CallbackInfo ci) {
        KineticBlockEntity self = (KineticBlockEntity) (Object) this;
        BlockPos pos = self.getBlockPos();
        if (pos != null) {
            BridgeSocketClient.sendKineticUpdate(pos, self.getSpeed(), self.isOverStressed());
        }
    }

    @Inject(method = "remove", at = @At("HEAD"))
    private void createbridge$onRemove(CallbackInfo ci) {
        KineticBlockEntity self = (KineticBlockEntity) (Object) this;
        BlockPos pos = self.getBlockPos();
        if (pos != null) {
            BridgeSocketClient.sendKineticClear(pos);
        }
    }

    @Inject(method = "read", at = @At("RETURN"))
    private void createbridge$onRead(CompoundTag compound, HolderLookup.Provider registries, boolean clientPacket, CallbackInfo ci) {
        KineticBlockEntity self = (KineticBlockEntity) (Object) this;
        BlockPos pos = self.getBlockPos();
        if (pos != null) {
            BridgeSocketClient.sendKineticUpdate(pos, self.getSpeed(), self.isOverStressed());
        }
    }
}
