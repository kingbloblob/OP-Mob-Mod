package com.onepiecebosses.crew;

import java.util.EnumSet;
import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecebosses.world.WanderingHunterEntity;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.npc.HumanNpc;

/**
 * A pirate in one of the rival crews (see RivalCrews). The captain leads the crew across the land, a few blocks
 * at a time, and waits for stragglers; the crew follows the captain. They go after players, Marines and bounty
 * hunters, and any pirate of another rival crew. When one of them picks a fight the rest of the crew piles in.
 *
 * At a camp (CrewCamp) they stay by the treasure chest instead of roaming. If the captain falls, the toughest
 * crewmate left takes over. They are pirate-side, so the main mod's own pirates leave them be.
 */
public class RivalPirateEntity extends HumanNpc {
	/** Crewmates this close join a fight one of them starts. */
	private static final double RALLY_RANGE = 24.0;
	/** The crew keeps within this distance of the captain, and the captain waits for anyone further. */
	private static final double KEEP_UP = 7.0;
	private static final double WAIT_FOR = 12.0;

	/** The rival crew's id in crews.json ("red_tusk"). Pirates of the same crew never fight each other. */
	private String rivalId = "";
	/** This band: the captain and the crew that came with them. */
	private UUID bandId;
	private boolean captain = false;
	private UUID captainId;
	/** The chest of the camp they guard, or null for a crew on the move. */
	private BlockPos treasure;
	private boolean boasted = false;

	public RivalPirateEntity(EntityType<? extends RivalPirateEntity> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return HumanNpc.createNpcAttributes().add(Attributes.FOLLOW_RANGE, 32.0);
	}

	@Override
	public boolean isMarineSide() {
		return false;
	}

	/** Puts this pirate in a crew. Call before applyKit. captainId is null for the captain. */
	public void joinCrew(String rivalId, UUID bandId, boolean captain, UUID captainId) {
		this.rivalId = rivalId;
		this.bandId = bandId;
		this.captain = captain;
		this.captainId = captainId;
	}

	/** Makes camp: they stay within 16 blocks of the chest, never despawn, and don't roam. */
	public void guardTreasure(BlockPos chest) {
		this.treasure = chest;
		makeGuard();
		setHomeTo(chest, 12);
	}

	public String getRivalId() {
		return rivalId;
	}

	public RivalCrews.Rival getRival() {
		return RivalCrews.get(rivalId);
	}

	public UUID getBandId() {
		return bandId;
	}

	public boolean isCaptain() {
		return captain;
	}

	public UUID getCaptainId() {
		return captainId;
	}

	public BlockPos getTreasure() {
		return treasure;
	}

	public boolean sameCrew(Entity other) {
		return other instanceof RivalPirateEntity pirate && !rivalId.isEmpty() && rivalId.equals(pirate.rivalId);
	}

	/** A pirate of another rival crew: fair game. */
	public boolean isRival(LivingEntity other) {
		return other instanceof RivalPirateEntity pirate && !pirate.rivalId.isEmpty() && !rivalId.isEmpty() && !sameCrew(pirate);
	}

	/**
	 * Only their own crew are friends. Every other rival crew is an enemy, even though they're all pirates; the main
	 * mod's pirates are still left alone (HumanNpc counts every pirate as a friend).
	 */
	@Override
	public boolean considersEntityAsAlly(Entity other) {
		if (other instanceof RivalPirateEntity) {
			return sameCrew(other);
		}
		return super.considersEntityAsAlly(other);
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		// HumanNpc's "hit one and the group turns on you" calls over every rival pirate around, whatever their crew.
		// Swap it for a plain one; customServerAiStep calls over the crew only.
		this.targetSelector.removeAllGoals(goal -> goal instanceof HurtByTargetGoal);
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
		this.goalSelector.addGoal(5, new FollowCaptainGoal());
		this.goalSelector.addGoal(5, new LeadGoal());
	}

	@Override
	protected void addTargetGoals() {
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, RivalPirateEntity.class, 10, true, false,
				(target, level) -> isRival(target)));
		this.targetSelector.addGoal(4, new NearestAttackableTargetGoal<>(this, MarineEntity.class, true));
		this.targetSelector.addGoal(4, new NearestAttackableTargetGoal<>(this, WanderingHunterEntity.class, true));
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		LivingEntity target = getTarget();
		if (target == null || !target.isAlive() || tickCount % 10 != 0) {
			return;
		}
		// The whole crew piles in.
		for (RivalPirateEntity mate : crewmates(RALLY_RANGE)) {
			if (mate.getTarget() == null && !mate.isAlliedTo(target)) {
				mate.setTarget(target);
			}
		}
		if (captain && !boasted && target instanceof ServerPlayer player && distanceTo(player) < 16) {
			boasted = true;
			RivalCrews.Rival rival = getRival();
			if (rival != null && !rival.boast.isEmpty()) {
				player.sendSystemMessage(Component.literal(getName().getString() + ": ").withStyle(ChatFormatting.GOLD)
						.append(Component.literal(rival.boast).withStyle(ChatFormatting.YELLOW)));
			}
		}
	}

	/** Others of this band within range. */
	public List<RivalPirateEntity> crewmates(double range) {
		return level().getEntitiesOfClass(RivalPirateEntity.class, getBoundingBox().inflate(range, 8, range),
				p -> p != this && p.isAlive() && bandId != null && bandId.equals(p.bandId));
	}

	private RivalPirateEntity findCaptain() {
		if (captainId == null || !(level() instanceof ServerLevel level)) {
			return null;
		}
		Entity e = level.getEntity(captainId);
		return e instanceof RivalPirateEntity pirate && pirate.isAlive() ? pirate : null;
	}

	/** The captain is beaten: a bounty for whoever did it, and the toughest crewmate left takes over. */
	@Override
	public void die(DamageSource source) {
		if (captain && !this.dead && level() instanceof ServerLevel level) {
			RivalCrews.Rival rival = getRival();
			String crewName = rival != null ? rival.name : getCrew();
			if (source.getEntity() instanceof ServerPlayer player) {
				long reward = getBountyReward() > 0 ? getBountyReward() : 5_000_000L;
				OnePieceBridge.raiseBounty(player, reward, "You beat " + getName().getString() + " of the " + crewName + ".");
			}
			RivalPirateEntity heir = null;
			List<RivalPirateEntity> mates = crewmates(48);
			for (RivalPirateEntity mate : mates) {
				if (heir == null || mate.getMaxHealth() > heir.getMaxHealth()) {
					heir = mate;
				}
			}
			if (heir != null) {
				heir.captain = true;
				heir.captainId = null;
				String name = heir.getName().getString();
				heir.setCustomName(Component.literal("Acting Captain " + name));
				for (RivalPirateEntity mate : mates) {
					if (mate != heir) {
						mate.captainId = heir.getUUID();
					}
				}
				Component news = Component.literal(getName().getString() + " has fallen! " + name + " takes command of the "
						+ crewName + ".").withStyle(ChatFormatting.GOLD);
				for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(48))) {
					player.sendSystemMessage(news);
				}
			}
		}
		super.die(source);
	}

	/** With nobody to fight, a crewmate stays close to the captain. */
	private class FollowCaptainGoal extends Goal {
		private RivalPirateEntity leader;
		private int repath;

		FollowCaptainGoal() {
			setFlags(EnumSet.of(Goal.Flag.MOVE));
		}

		@Override
		public boolean canUse() {
			if (captain || getTarget() != null || tickCount % 10 != 0) {
				return false;
			}
			leader = findCaptain();
			return leader != null && distanceToSqr(leader) > KEEP_UP * KEEP_UP;
		}

		@Override
		public boolean canContinueToUse() {
			return leader != null && leader.isAlive() && getTarget() == null && distanceToSqr(leader) > 3 * 3;
		}

		@Override
		public void start() {
			repath = 0;
		}

		@Override
		public void tick() {
			getLookControl().setLookAt(leader, 10f, getMaxHeadXRot());
			if (--repath <= 0) {
				repath = 10;
				getNavigation().moveTo(leader, distanceToSqr(leader) > 16 * 16 ? 1.25 : 1.05);
			}
		}

		@Override
		public void stop() {
			leader = null;
			getNavigation().stop();
		}
	}

	/** The captain walks the crew from place to place, a short leg at a time, and waits for anyone falling behind. */
	private class LeadGoal extends Goal {
		private Vec3 goal;
		private int rest = 60;
		private int timeout;

		LeadGoal() {
			setFlags(EnumSet.of(Goal.Flag.MOVE));
		}

		@Override
		public boolean canUse() {
			if (!captain || treasure != null || getTarget() != null) {
				return false;
			}
			if (rest > 0) {
				rest--;
				return false;
			}
			for (RivalPirateEntity mate : crewmates(32)) {
				if (mate.getTarget() == null && mate.distanceToSqr(RivalPirateEntity.this) > WAIT_FOR * WAIT_FOR) {
					return false;
				}
			}
			goal = DefaultRandomPos.getPos(RivalPirateEntity.this, 24, 6);
			return goal != null;
		}

		@Override
		public boolean canContinueToUse() {
			return goal != null && getTarget() == null && timeout > 0 && !getNavigation().isDone();
		}

		@Override
		public void start() {
			timeout = 20 * 20;
			getNavigation().moveTo(goal.x, goal.y, goal.z, 0.8);
		}

		@Override
		public void tick() {
			timeout--;
		}

		@Override
		public void stop() {
			goal = null;
			rest = 100 + getRandom().nextInt(140);
			getNavigation().stop();
		}
	}

	/** Roaming crews despawn like any monster once everyone is far away; a camp's crew stays (makeGuard). */
	@Override
	public boolean removeWhenFarAway(double distance) {
		return treasure == null && super.removeWhenFarAway(distance);
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("RivalCrew", rivalId);
		output.putBoolean("RivalCaptain", captain);
		output.putBoolean("RivalBoasted", boasted);
		if (bandId != null) {
			output.putString("RivalBand", bandId.toString());
		}
		if (captainId != null) {
			output.putString("RivalCaptainId", captainId.toString());
		}
		if (treasure != null) {
			output.putLong("RivalTreasure", treasure.asLong());
		}
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		rivalId = input.getStringOr("RivalCrew", "");
		captain = input.getBooleanOr("RivalCaptain", false);
		boasted = input.getBooleanOr("RivalBoasted", false);
		bandId = uuid(input.getStringOr("RivalBand", ""));
		captainId = uuid(input.getStringOr("RivalCaptainId", ""));
		long packed = input.getLongOr("RivalTreasure", Long.MIN_VALUE);
		treasure = packed == Long.MIN_VALUE ? null : BlockPos.of(packed);
	}

	private static UUID uuid(String text) {
		try {
			return text.isEmpty() ? null : UUID.fromString(text);
		} catch (IllegalArgumentException e) {
			return null;
		}
	}

	/** For the test: everyone within range of a spot, by band. */
	public static List<RivalPirateEntity> around(ServerLevel level, BlockPos pos, double range) {
		return level.getEntitiesOfClass(RivalPirateEntity.class, new AABB(pos).inflate(range), RivalPirateEntity::isAlive);
	}
}
