package com.onepiecebosses.world.mixin;

import com.onepiecebosses.world.LairNeighbours;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Hands each dimension's structure state to LairNeighbours, which needs it to find the other structures near a lair. */
@Mixin(ChunkGeneratorStructureState.class)
public abstract class StructureStateMixin {
	@Shadow @Final private BiomeSource biomeSource;

	@Inject(method = "<init>", at = @At("TAIL"))
	private void opbosses$register(CallbackInfo ci) {
		LairNeighbours.register((ChunkGeneratorStructureState) (Object) this, biomeSource);
	}
}
