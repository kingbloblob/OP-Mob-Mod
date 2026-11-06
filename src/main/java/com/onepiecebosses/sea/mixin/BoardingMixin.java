package com.onepiecebosses.sea.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;

import com.onepiecebosses.sea.BossShips;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.Boarding;

/**
 * Boarding a flagship (BossShips) brings out her captain. The main mod's Boarding.board docks the ship into blocks
 * (the ship entity is gone afterwards), so which flagship it was is noted first and the captain comes once the
 * boarding has worked.
 */
@Mixin(Boarding.class)
public abstract class BoardingMixin {
	@Unique
	private static final ThreadLocal<String> opbosses$flagship = new ThreadLocal<>();

	@Inject(method = "board", at = @At("HEAD"))
	private static void opbosses$noteFlagship(ServerPlayer player, ShipEntity ship, CallbackInfoReturnable<InteractionResult> cir) {
		boolean flagship = ship.entityTags().contains(BossShips.TAG);
		opbosses$flagship.set(flagship ? BossShips.idOf(ship) : null);
		if (flagship && !ship.sinking && ship.level() instanceof ServerLevel level) {
			BossShips.clearKeel(level, ship);
		}
	}

	@Inject(method = "board", at = @At("RETURN"))
	private static void opbosses$captainMeets(ServerPlayer player, ShipEntity ship, CallbackInfoReturnable<InteractionResult> cir) {
		String id = opbosses$flagship.get();
		opbosses$flagship.remove();
		if (id != null && cir.getReturnValue() == InteractionResult.SUCCESS && player.level() instanceof ServerLevel level) {
			BossShips.captainMeets(level, player, id);
		}
	}
}
