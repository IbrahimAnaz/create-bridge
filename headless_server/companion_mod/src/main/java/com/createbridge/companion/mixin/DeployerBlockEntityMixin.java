package com.createbridge.companion.mixin;

import com.createbridge.companion.net.BridgeSocketClient;
import com.simibubi.create.content.kinetics.deployer.DeployerBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value = DeployerBlockEntity.class, remap = false)
public abstract class DeployerBlockEntityMixin {

    @Shadow protected ItemStack heldItem;
    @Shadow protected int timer;

    private void createbridge$syncDeployer() {
        DeployerBlockEntity self = (DeployerBlockEntity) (Object) this;
        if (self.getLevel() == null || self.getLevel().isClientSide()) return;

        BlockPos pos = self.getBlockPos();
        ItemStack stack = this.heldItem != null ? this.heldItem : ItemStack.EMPTY;
        String itemId = "";
        int count = 0;
        if (!stack.isEmpty()) {
            ResourceLocation key = BuiltInRegistries.ITEM.getKey(stack.getItem());
            itemId = key != null ? key.toString() : "";
            count = stack.getCount();
        }
        // Normalize timer (0..1000 in Create Deployer) to 0.0..1.0 extension progress
        float progress = Math.max(0.0f, Math.min(1.0f, (1000 - Math.abs(1000 - this.timer)) / 1000.0f));
        BridgeSocketClient.sendDeployerUpdate(pos, "USE", itemId, count, progress);
    }

    @Inject(method = "tick", at = @At("RETURN"))
    private void createbridge$onTick(CallbackInfo ci) {
        createbridge$syncDeployer();
    }

    @Inject(method = "read", at = @At("RETURN"))
    private void createbridge$onRead(CompoundTag compound, HolderLookup.Provider registries, boolean clientPacket, CallbackInfo ci) {
        createbridge$syncDeployer();
    }
}
