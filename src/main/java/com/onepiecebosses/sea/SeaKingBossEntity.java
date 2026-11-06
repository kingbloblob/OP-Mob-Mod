package com.onepiecebosses.sea;

import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.sea.SeaKingEntity;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipHull;
import com.onepiecemod.util.Motion;

/**
 * A named Sea King mini-boss: the One Piece Mod's Sea King underneath (it swims, bites, knocks people off their boats
 * and has a boss bar), with its own body, far more health, and an ambush. It hunts a sailing player from below:
 * bubbles boil up around their ship for a few seconds (the warning), then it breaches straight up through the keel,
 * smashing the hull and throwing everyone on deck into the air. It dives and comes again every 20 seconds or so,
 * and between breaches it fights with its own tricks:
 *  - Gulpmaw, the Lantern Deep: its lure drags people towards its jaws, and anyone pulled close is swallowed and held
 *    in its mouth for a few seconds (hit it hard to make it spit you out).
 *  - Ironscale, the Keelbreaker: armour plate shrugs off most damage, except for a few seconds after each breach when
 *    it's dazed. It also rams the hull between breaches.
 *  - Thundercoil, the Storm Serpent: calls lightning down around its prey, and shocks the water (worst for anyone
 *    swimming in it).
 * It can't be tamed with bait. Beating one raises the bounty of everyone who fought it; its drops (the trophy, meat)
 * are its loot table, data/opbosses/loot_table/entities/<id>.json. SeaBosses sends them out; /opbosses seaking calls one.
 */
public class SeaKingBossEntity extends SeaKingEntity {
	public static final String TAG = "opbosses_sea_king";
	/** How far away a sailing target can be before it gives up and swims off. */
	private static final double LOSE_RANGE = 160;

	public enum Kind {
		GULPMAW("gulpmaw", 420, 16, 8, 45_000_000L),
		IRONSCALE("ironscale", 640, 20, 14, 90_000_000L),
		THUNDERCOIL("thundercoil", 520, 18, 8, 120_000_000L);

		public final String id;
		public final double health;
		public final double damage;
		public final double armor;
		public final long bounty;

		Kind(String id, double health, double damage, double armor, long bounty) {
			this.id = id;
			this.health = health;
			this.damage = damage;
			this.armor = armor;
			this.bounty = bounty;
		}

		public static Kind of(String id) {
			for (Kind kind : values()) {
				if (kind.id.equals(id)) {
					return kind;
				}
			}
			return null;
		}
	}

	private final Kind kind;
	/** The player it's hunting (kept across target changes, so it keeps coming back for them). */
	private UUID prey;
	/** Ticks until the next ambush; while warning > 0 the bubbles are up and the breach is coming. */
	private int ambushIn = 100;
	private int warning;
	private int abilityIn = 160;
	private int secondAbilityIn = 260;
	/** Ironscale is dazed (its armour doesn't help) for this many ticks after breaching. */
	private int dazed;
	/** Gulpmaw: who is in its mouth, and for how much longer. */
	private UUID swallowed;
	private int swallowTicks;
	private float swallowDamageTaken;
	private int awayTicks;

	public SeaKingBossEntity(EntityType<? extends SeaKingBossEntity> type, Level level) {
		super(type, level);
		Kind found = Kind.of(BuiltInRegistries.ENTITY_TYPE.getKey(type).getPath());
		this.kind = found != null ? found : Kind.GULPMAW;
		this.xpReward = 200;
		this.setPersistenceRequired();
		this.addTag(TAG);
	}

	public Kind kind() {
		return kind;
	}

	/** Sets the player it hunts. SeaBosses calls this when it sends one out. */
	public void hunt(ServerPlayer player) {
		this.prey = player.getUUID();
		this.setTarget(player);
		this.ambushIn = 60;
	}

	/** Starts the next ambush (bubbles, then the breach) in this many ticks. */
	public void ambushIn(int ticks) {
		this.ambushIn = ticks;
	}

	/** True while it's dazed after a breach (Ironscale's armour is down). */
	public boolean dazed() {
		return dazed > 0;
	}

	/** The Sea King's boss bar (the main mod's, private) with this one's own name, in red. */
	private void nameBar() {
		try {
			if (BAR == null) {
				BAR = SeaKingEntity.class.getDeclaredField("bossBar");
				BAR.setAccessible(true);
			}
			net.minecraft.server.level.ServerBossEvent bar = (net.minecraft.server.level.ServerBossEvent) BAR.get(this);
			if (!getName().equals(bar.getName())) {
				bar.setName(getName());
				bar.setColor(net.minecraft.world.BossEvent.BossBarColor.RED);
			}
		} catch (ReflectiveOperationException | ClassCastException e) {
			BAR_BROKEN = true;
		}
	}

	@Override
	public void setCustomName(Component name) {
		super.setCustomName(name);
		if (!this.level().isClientSide() && !BAR_BROKEN) {
			nameBar();
		}
	}

	private static java.lang.reflect.Field BAR;
	private static boolean BAR_BROKEN;

	// ---------- No taming, no riding ----------

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (player.getItemInHand(hand).is(com.onepiecemod.sea.SeaItems.SEA_KING_BAIT) && !this.level().isClientSide()) {
			player.sendOverlayMessage(Component.literal(getName().getString() + " ignores the bait. This one can't be tamed!")
					.withStyle(ChatFormatting.RED));
		}
		return InteractionResult.PASS;
	}

	@Override
	public LivingEntity getControllingPassenger() {
		return null;
	}

	@Override
	public void checkDespawn() {
		// Never the natural way (it's persistent); it swims off when its prey is long gone (see customServerAiStep).
	}

	// ---------- The fight ----------

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (tickCount % 20 == 0 && !BAR_BROKEN) {
			nameBar();
		}
		ServerPlayer player = prey == null ? null : level.getServer().getPlayerList().getPlayer(prey);
		if (player == null || !player.isAlive() || player.isSpectator() || player.level() != level || player.distanceTo(this) > LOSE_RANGE) {
			if (getTarget() instanceof ServerPlayer other && other.isAlive()) {
				prey = other.getUUID(); // Whoever it's fighting now.
			} else if (++awayTicks > 20 * 60) {
				swimOff(level);
			}
			return;
		}
		awayTicks = 0;
		if (getTarget() == null) {
			setTarget(player);
		}
		if (dazed > 0) {
			dazed--;
			if (dazed % 10 == 0) {
				level.sendParticles(ParticleTypes.CRIT, getX(), getY() + getBbHeight() + 1, getZ(), 6, 0.8, 0.3, 0.8, 0.1);
			}
		}
		tickSwallow(level);

		ShipEntity ship = ShipEntity.aboard(player);
		if (warning > 0) {
			tickWarning(level, ship);
		} else if (--ambushIn <= 0 && ship != null && !ship.sinking) {
			warning = 70;
			for (ServerPlayer aboard : ShipEntity.playersAboard(ship)) {
				aboard.sendSystemMessage(Component.literal("Something huge is circling under the ship... the water is boiling!")
						.withStyle(ChatFormatting.DARK_AQUA), true);
			}
			level.playSound(null, ship.getX(), level.getSeaLevel(), ship.getZ(), com.onepiecemod.sound.WorldSounds.SEA_KING_AMBIENT,
					SoundSource.HOSTILE, 5.0f, 0.4f);
		}

		if (--abilityIn <= 0 && distanceTo(player) < 40) {
			abilityIn = 160 + getRandom().nextInt(60);
			ability(level, player, ship);
		}
		if (--secondAbilityIn <= 0 && distanceTo(player) < 40) {
			secondAbilityIn = 240 + getRandom().nextInt(80);
			secondAbility(level, player, ship);
		}
	}

	/** Bubbles boil up all around the ship, then it breaches under the keel. */
	private void tickWarning(ServerLevel level, ShipEntity ship) {
		warning--;
		if (ship == null || ship.sinking) {
			warning = 0;
			ambushIn = 100;
			return;
		}
		double sea = level.getSeaLevel();
		// Stay down out of sight, right under the ship, while the bubbles give it away.
		this.setPos(ship.getX(), sea - 9, ship.getZ());
		this.setDeltaMovement(Vec3.ZERO);
		if (warning % 4 == 0) {
			for (int i = 0; i < 4; i++) {
				double a = getRandom().nextDouble() * Math.PI * 2;
				double r = 3 + getRandom().nextDouble() * 8;
				level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, ship.getX() + Math.cos(a) * r, sea - 1, ship.getZ() + Math.sin(a) * r,
						12, 0.6, 0.6, 0.6, 0.15);
				level.sendParticles(ParticleTypes.SPLASH, ship.getX() + Math.cos(a) * r, sea + 0.5, ship.getZ() + Math.sin(a) * r,
						10, 0.6, 0.2, 0.6, 0.1);
			}
		}
		if (warning == 0) {
			breach(level, ship);
		}
	}

	/** Straight up through the keel. */
	private void breach(ServerLevel level, ShipEntity ship) {
		double sea = level.getSeaLevel();
		Vec3 under = new Vec3(ship.getX(), sea - 3, ship.getZ());
		this.setPos(under.x, under.y, under.z);
		this.setDeltaMovement(0, 1.4, 0);
		this.needsSync = true;
		float hull = kind == Kind.IRONSCALE ? 70f : 45f;
		ShipHull.damage(ship, hull, null, under.add(0, 2, 0), null);
		level.sendParticles(ParticleTypes.SPLASH, under.x, sea + 1, under.z, 220, 3.5, 3.0, 3.5, 0.5);
		level.sendParticles(ParticleTypes.CLOUD, under.x, sea + 2, under.z, 40, 2.5, 1.5, 2.5, 0.1);
		level.playSound(null, under.x, sea, under.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0f, 0.5f);
		level.playSound(null, under.x, sea, under.z, com.onepiecemod.sound.WorldSounds.SEA_KING_AMBIENT, SoundSource.HOSTILE, 6.0f, 0.5f);
		for (ServerPlayer aboard : ShipEntity.playersAboard(ship)) {
			aboard.stopRiding();
			aboard.hurtServer(level, damageSources().mobAttack(this), (float) kind.damage * 0.5f);
			aboard.setDeltaMovement(aboard.getDeltaMovement().add((getRandom().nextDouble() - 0.5) * 0.8, 1.1, (getRandom().nextDouble() - 0.5) * 0.8));
			Motion.sync(aboard);
			aboard.sendSystemMessage(Component.literal(getName().getString() + " bursts up through the hull!").withStyle(ChatFormatting.RED));
		}
		if (kind == Kind.IRONSCALE) {
			dazed = 100;
			for (ServerPlayer near : playersNear(level, 40)) {
				near.sendSystemMessage(Component.literal("Ironscale is dazed from the impact: hit it now, before its plates close!")
						.withStyle(ChatFormatting.GOLD), true);
			}
		}
		ambushIn = 380 + getRandom().nextInt(140);
	}

	private void ability(ServerLevel level, ServerPlayer player, ShipEntity ship) {
		switch (kind) {
			case GULPMAW -> lure(level);
			case IRONSCALE -> ram(level, ship);
			case THUNDERCOIL -> lightning(level, player);
		}
	}

	private void secondAbility(ServerLevel level, ServerPlayer player, ShipEntity ship) {
		switch (kind) {
			case GULPMAW -> {
				// It snaps up whoever is nearest its mouth.
				for (ServerPlayer near : playersNear(level, 6)) {
					swallow(level, near);
					break;
				}
			}
			case IRONSCALE -> {
				// Its tail club sweeps the water around it.
				for (ServerPlayer near : playersNear(level, 9)) {
					near.hurtServer(level, damageSources().mobAttack(this), (float) kind.damage * 0.7f);
					Vec3 away = near.position().subtract(position()).normalize();
					near.setDeltaMovement(away.x * 1.6, 0.6, away.z * 1.6);
					Motion.sync(near);
				}
				level.playSound(null, blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0f, 0.5f);
				level.sendParticles(ParticleTypes.SPLASH, getX(), level.getSeaLevel() + 1, getZ(), 120, 5, 1, 5, 0.3);
			}
			case THUNDERCOIL -> shock(level);
		}
	}

	/** Gulpmaw's lure glows, and everyone who sees it is dragged towards the jaws. */
	private void lure(ServerLevel level) {
		Vec3 mouth = mouth();
		level.sendParticles(ParticleTypes.GLOW, mouth.x, mouth.y + 1, mouth.z, 60, 1.2, 1.2, 1.2, 0.05);
		level.playSound(null, BlockPos.containing(mouth), SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 3.0f, 1.6f);
		for (ServerPlayer near : playersNear(level, 22)) {
			Vec3 pull = mouth.subtract(near.position()).normalize().scale(1.3);
			near.stopRiding();
			near.setDeltaMovement(pull.x, Math.max(0.35, pull.y), pull.z);
			Motion.sync(near);
			near.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0));
			near.sendSystemMessage(Component.literal("A cold light in the deep... you can't look away!").withStyle(ChatFormatting.AQUA), true);
		}
		secondAbilityIn = Math.min(secondAbilityIn, 30); // The jaws follow the lure.
	}

	private void swallow(ServerLevel level, ServerPlayer player) {
		if (swallowed != null) {
			return;
		}
		swallowed = player.getUUID();
		swallowTicks = 80;
		swallowDamageTaken = 0;
		player.stopRiding();
		player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 90, 0));
		level.playSound(null, blockPosition(), SoundEvents.GENERIC_EAT.value(), SoundSource.HOSTILE, 3.0f, 0.4f);
		player.sendSystemMessage(Component.literal("Gulpmaw swallowed you! Hit it hard to make it spit you out!").withStyle(ChatFormatting.RED));
	}

	private void tickSwallow(ServerLevel level) {
		if (swallowed == null) {
			return;
		}
		ServerPlayer player = level.getServer().getPlayerList().getPlayer(swallowed);
		if (player == null || !player.isAlive() || --swallowTicks <= 0 || swallowDamageTaken >= 40) {
			swallowed = null;
			if (player != null && player.isAlive()) {
				Vec3 look = getLookAngle();
				player.setDeltaMovement(look.x * 1.2, 0.8, look.z * 1.2);
				Motion.sync(player);
				level.sendParticles(ParticleTypes.SPLASH, player.getX(), player.getY(), player.getZ(), 40, 0.5, 0.5, 0.5, 0.2);
				player.sendSystemMessage(Component.literal("Gulpmaw spits you out!").withStyle(ChatFormatting.GOLD), true);
			}
			return;
		}
		Vec3 mouth = mouth();
		player.teleportTo(mouth.x, mouth.y, mouth.z);
		player.setDeltaMovement(Vec3.ZERO);
		player.setAirSupply(player.getMaxAirSupply()); // Held, not drowned.
		if (swallowTicks % 20 == 0) {
			player.hurtServer(level, damageSources().mobAttack(this), 4.0f);
		}
	}

	/** Ironscale rams the side of the ship. */
	private void ram(ServerLevel level, ShipEntity ship) {
		if (ship == null || ship.sinking) {
			return;
		}
		Vec3 to = ship.position().subtract(position());
		Vec3 dash = new Vec3(to.x, 0, to.z).normalize().scale(1.8);
		this.setDeltaMovement(dash.x, 0.2, dash.z);
		this.needsSync = true;
		ShipHull.damage(ship, 22f, null, ship.position().add(-dash.x * 2, 1, -dash.z * 2), null);
		level.playSound(null, ship.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0f, 0.4f);
		for (ServerPlayer aboard : ShipEntity.playersAboard(ship)) {
			aboard.sendSystemMessage(Component.literal("Ironscale rams the hull!").withStyle(ChatFormatting.RED), true);
			aboard.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 80, 0));
		}
	}

	/** Thundercoil calls lightning down around its prey. */
	private void lightning(ServerLevel level, ServerPlayer player) {
		int bolts = 3 + getRandom().nextInt(3);
		for (int i = 0; i < bolts; i++) {
			Vec3 at = player.position().add((getRandom().nextDouble() - 0.5) * 10, 0, (getRandom().nextDouble() - 0.5) * 10);
			if (i == 0) {
				at = player.position(); // One always lands right on them.
			}
			LightningBolt bolt = net.minecraft.world.entity.EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
			if (bolt != null) {
				bolt.setVisualOnly(true); // No fires on deck; the damage is ours.
				bolt.snapTo(at.x, at.y, at.z);
				level.addFreshEntity(bolt);
			}
			for (ServerPlayer near : level.getEntitiesOfClass(ServerPlayer.class, new net.minecraft.world.phys.AABB(at, at).inflate(3), p -> !p.isSpectator())) {
				near.hurtServer(level, damageSources().lightningBolt(), (float) kind.damage * 0.6f);
			}
		}
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + getBbHeight(), getZ(), 80, 2, 2, 2, 0.4);
	}

	/** Thundercoil shocks the water: worst for anyone swimming in it, but it reaches the deck too. */
	private void shock(ServerLevel level) {
		level.playSound(null, blockPosition(), SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 3.0f, 1.4f);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), level.getSeaLevel() + 0.5, getZ(), 200, 12, 0.3, 12, 0.3);
		for (ServerPlayer near : playersNear(level, 18)) {
			boolean wet = near.isInWater();
			near.hurtServer(level, damageSources().lightningBolt(), (float) kind.damage * (wet ? 0.9f : 0.35f));
			near.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, wet ? 80 : 40, wet ? 3 : 1));
		}
	}

	private Vec3 mouth() {
		Vec3 look = Vec3.directionFromRotation(0, getYRot());
		return position().add(look.x * 2.5, getBbHeight() * 0.6, look.z * 2.5);
	}

	private List<ServerPlayer> playersNear(ServerLevel level, double range) {
		return level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(range), p -> !p.isSpectator() && p.isAlive());
	}

	private void swimOff(ServerLevel level) {
		level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, getX(), getY(), getZ(), 40, 2, 1, 2, 0.1);
		discard();
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (kind == Kind.IRONSCALE && dazed <= 0 && !source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			amount *= 0.35f; // Its plates turn most of it.
			if (getRandom().nextInt(3) == 0) {
				level.playSound(null, blockPosition(), SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.0f, 1.6f);
			}
		}
		boolean hurt = super.hurtServer(level, source, amount);
		if (hurt && swallowed != null) {
			swallowDamageTaken += amount;
		}
		return hurt;
	}

	@Override
	public void die(DamageSource source) {
		if (level() instanceof ServerLevel level && !isRemoved()) {
			Component name = getName();
			for (ServerPlayer player : playersNear(level, 64)) {
				OnePieceBridge.raiseBounty(player, kind.bounty, "beating " + name.getString());
				player.sendSystemMessage(Component.literal(name.getString() + " sinks into the deep. The whole sea will hear of this!")
						.withStyle(ChatFormatting.GOLD));
			}
			if (source.getEntity() instanceof ServerPlayer killer && killer.distanceTo(this) > 64) {
				OnePieceBridge.raiseBounty(killer, kind.bounty, "beating " + name.getString());
			}
		}
		super.die(source);
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("Prey", prey == null ? "" : prey.toString());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		String id = input.getStringOr("Prey", "");
		prey = id.isEmpty() ? null : UUID.fromString(id);
	}
}
