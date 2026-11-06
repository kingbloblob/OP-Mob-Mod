package com.onepiecebosses.world;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.shipcombat.SeaPirateEntity;

/**
 * A wandering bounty hunter: a small-time headhunter who lives off rookie bounties. They go after any player
 * with a bounty under 100M (bigger names are the main mod's Devil Fruit hunters' business, and too dangerous for
 * these), and after pirate NPCs and raiders for the Berries. Players without a bounty are left alone unless they
 * start something. They're on the law's side, so they never fight Marines.
 *
 * Beating one raises your bounty a little (getBountyReward, from the kit's "bounty" in world_mobs.json).
 */
public class WanderingHunterEntity extends HumanNpc {
	/** Bounties from this size up are out of their league. */
	public static final long BIG_GAME = 100_000_000L;
	private static final double SHOUT_RANGE = 24.0;

	/** Set once they've called out the player they're fighting, so they only do it once. */
	private boolean calledOut = false;

	public WanderingHunterEntity(EntityType<? extends WanderingHunterEntity> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return HumanNpc.createNpcAttributes().add(Attributes.FOLLOW_RANGE, 40.0);
	}

	@Override
	public boolean isMarineSide() {
		return true;
	}

	/** A player worth chasing: wanted, but for less than BIG_GAME. */
	public static boolean isPrey(LivingEntity entity) {
		if (!(entity instanceof Player player) || player.isCreative() || player.isSpectator()) {
			return false;
		}
		long bounty = OnePieceBridge.bounty(player);
		return bounty > 0 && bounty < BIG_GAME;
	}

	@Override
	protected void addTargetGoals() {
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
				(target, level) -> isPrey(target)));
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, SeaPirateEntity.class, true));
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, RookieRaiderEntity.class, true));
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, com.onepiecebosses.crew.RivalPirateEntity.class, true));
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (!calledOut && getTarget() instanceof ServerPlayer player && isPrey(player) && distanceTo(player) < SHOUT_RANGE) {
			calledOut = true;
			String name = getCustomName() != null ? getCustomName().getString() : "A bounty hunter";
			player.sendSystemMessage(Component.literal(name + ": ").withStyle(ChatFormatting.DARK_PURPLE)
					.append(Component.literal(line(OnePieceBridge.formatBerries(OnePieceBridge.bounty(player)))).withStyle(ChatFormatting.LIGHT_PURPLE)));
		}
	}

	private String line(String bounty) {
		return switch (getRandom().nextInt(4)) {
			case 0 -> "A " + bounty + " head. Small, but it pays for supper.";
			case 1 -> "You're worth " + bounty + " to the Marines. Come quietly!";
			case 2 -> "I've had my eye on that " + bounty + " poster for a week.";
			default -> bounty + "! Nothing personal, rookie.";
		};
	}

	@Override
	public void die(DamageSource source) {
		if (level() instanceof ServerLevel && source.getEntity() instanceof ServerPlayer player && !this.dead) {
			long reward = getBountyReward() > 0 ? getBountyReward() : 1_000_000L;
			String name = getCustomName() != null ? getCustomName().getString() : "a bounty hunter";
			OnePieceBridge.raiseBounty(player, reward, "You beat the bounty hunter " + name + ".");
		}
		super.die(source);
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putBoolean("CalledOut", calledOut);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		calledOut = input.getBooleanOr("CalledOut", false);
	}
}
