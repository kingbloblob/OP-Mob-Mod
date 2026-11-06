package com.onepiecebosses.gear;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;

/**
 * Full-set bonuses. Wearing all four pieces of a boss's set keeps its passive effects on you (checked once a second),
 * and a full-strength hit unleashes the boss's signature move (GearSignatures) when it's ready. Holding the set's
 * own weapon brings it back sooner. The move's readiness shows on the action bar.
 */
public final class GearSets {
	private GearSets() {
	}

	public static final int COOLDOWN_SECONDS = 30;
	public static final int WEAPON_COOLDOWN_SECONDS = 18;

	/** Player -> game time their signature is ready again. Forgotten on restart, which only means it's ready sooner. */
	private static final Map<UUID, Long> READY_AT = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				GearItems.Set set = fullSet(player);
				if (set != null) {
					applyPassives(player, set.data());
					Long readyAt = READY_AT.get(player.getUUID());
					long now = player.level().getGameTime();
					if (readyAt != null && now >= readyAt) {
						READY_AT.remove(player.getUUID());
						player.sendSystemMessage(Component.literal(set.data().move + " is ready").withStyle(ChatFormatting.GOLD), true);
					}
				}
			}
		});

		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (level.isClientSide() || !(player instanceof ServerPlayer serverPlayer) || !(target instanceof LivingEntity living)
					|| !living.isAlive() || player.isSpectator()) {
				return InteractionResult.PASS;
			}
			// Only a full-strength swing, so spam-clicking can't fish for it.
			if (player.getAttackStrengthScale(0.5f) < 0.9f) {
				return InteractionResult.PASS;
			}
			GearItems.Set set = fullSet(player);
			if (set != null) {
				tryUnleash(serverPlayer, set, living);
			}
			return InteractionResult.PASS; // The normal hit still lands.
		});
	}

	/** Unleashes the set's move on this target if it's ready. True if it went off. Also used by the in-game test. */
	public static boolean tryUnleash(ServerPlayer player, GearItems.Set set, LivingEntity target) {
		long now = player.level().getGameTime();
		Long readyAt = READY_AT.get(player.getUUID());
		if (readyAt != null && now < readyAt) {
			return false;
		}
		boolean withWeapon = player.getMainHandItem().is(set.weapon());
		READY_AT.put(player.getUUID(), now + 20L * (withWeapon ? WEAPON_COOLDOWN_SECONDS : COOLDOWN_SECONDS));
		GearSignatures.use(set.data().boss, player, target, (ServerLevel) player.level(), withWeapon);
		player.sendSystemMessage(Component.literal(set.data().move + "!").withStyle(ChatFormatting.RED, ChatFormatting.BOLD), true);
		return true;
	}

	/** Lets the move go off again straight away (the in-game test). */
	public static void resetCooldown(Player player) {
		READY_AT.remove(player.getUUID());
	}

	/** The set whose four pieces this player is wearing, or null. */
	public static GearItems.Set fullSet(Player player) {
		GearItems.Set set = GearItems.setOf(player.getItemBySlot(EquipmentSlot.HEAD).getItem());
		if (set == null) {
			return null;
		}
		Item[] armor = set.armor();
		return player.getItemBySlot(EquipmentSlot.HEAD).is(armor[0]) && player.getItemBySlot(EquipmentSlot.CHEST).is(armor[1])
				&& player.getItemBySlot(EquipmentSlot.LEGS).is(armor[2]) && player.getItemBySlot(EquipmentSlot.FEET).is(armor[3])
				? set : null;
	}

	private static void applyPassives(ServerPlayer player, GearData data) {
		for (List<Object> passive : data.passives) {
			String when = passive.size() > 2 ? String.valueOf(passive.get(2)) : "always";
			boolean now = switch (when) {
				case "water" -> player.isInWater();
				case "falling" -> !player.onGround() && player.getDeltaMovement().y < -0.3 && !player.isShiftKeyDown();
				default -> true;
			};
			if (!now) {
				continue;
			}
			String id = String.valueOf(passive.get(0));
			int amplifier = ((Number) passive.get(1)).intValue();
			// Night vision flickers in its last 10 seconds, so it's kept topped up well past that.
			int ticks = id.equals("night_vision") ? 260 : 60;
			BuiltInRegistries.MOB_EFFECT.get(Identifier.withDefaultNamespace(id)).ifPresent(effect ->
					player.addEffect(new MobEffectInstance(effect, ticks, amplifier, true, false, true)));
		}
	}
}
