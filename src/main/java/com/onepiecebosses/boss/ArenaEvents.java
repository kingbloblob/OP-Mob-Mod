package com.onepiecebosses.boss;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecebosses.compat.OnePieceBridge;

/**
 * A rogue boss's arena: what its lair does while you fight it (from arenas.json, see ArenaData).
 *
 * - The boss bar takes the lair's colour, and its fog or darkened sky from the phase arenas.json says.
 * - From phase 2 (and more from phase 3) the lair throws hazards at the players fighting there, every few seconds,
 *   faster on Hard and Expert. Everything that hurts is marked first: a red ring on the ground, crumbling blocks or
 *   bubbling vents, about 1.5 seconds before it lands, so it can always be dodged.
 * - A collapsed floor is only ever a shallow pit (never over a cave, water or lava, never chests or anything
 *   unbreakable), and it is put back 10 seconds later, or as soon as the boss falls. Holes that were open when the
 *   world was saved come back on the next load.
 *
 * One of these lives on each RogueBossEntity, which calls tick() every server tick while it's a boss.
 */
public final class ArenaEvents {
	/** Players this close to the boss are in the fight (hazards aim at them). */
	private static final double ARENA_RANGE = 24.0;
	/** How long a hazard is marked before it lands. */
	private static final int WARN_TICKS = 30;
	/** How long a collapsed floor stays open. */
	private static final int RESTORE_TICKS = 200;
	private static final int CLOUD_TICKS = 120;
	private static final double CLOUD_RADIUS = 3.2;
	private static final double TIDE_RADIUS = 10.0;
	private static final int FOG_PULSE_TICKS = 160;
	private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS;
	private static final DustParticleOptions WARNING = new DustParticleOptions(0xFF3A2A, 1.3f);

	private final RogueBossEntity boss;
	private final List<Strike> strikes = new ArrayList<>();
	private final List<Cloud> clouds = new ArrayList<>();
	private final List<Hole> holes = new ArrayList<>();
	private final Set<String> started = new HashSet<>();
	private final Map<String, Integer> landed = new HashMap<>();
	private int cooldown = 80;
	private int fogPulse = FOG_PULSE_TICKS;
	private boolean loadedHoles = false;

	public ArenaEvents(RogueBossEntity boss) {
		this.boss = boss;
	}

	private ArenaData arena() {
		return ArenaData.of(boss.getCharacterId());
	}

	/** Every server tick while the mob is a boss. phase: 1, 2 or 3. */
	public void tick(ServerLevel level, int phase, boolean fighting) {
		if (loadedHoles) { // Holes from before the world was saved: the fight is over, put the floor back.
			loadedHoles = false;
			restore(level, true);
		}
		if (boss.tickCount % 20 == 0) {
			styleBar(phase);
		}
		restore(level, false);
		tickStrikes(level);
		tickClouds(level);
		if (!fighting || phase < 2) {
			return;
		}

		List<ArenaData.Hazard> active = new ArrayList<>();
		for (ArenaData.Hazard hazard : arena().hazards) {
			if (phase >= hazard.from) {
				if (started.add(hazard.type + hazard.from)) {
					announce(level, hazard.warn);
					cooldown = Math.min(cooldown, 40); // A new hazard shows itself soon after it's announced.
				}
				if (hazard.type.equals("fog")) {
					fogTick(level);
				} else {
					active.add(hazard);
				}
			}
		}
		if (active.isEmpty() || --cooldown > 0) {
			return;
		}
		List<ServerPlayer> players = players(level);
		if (players.isEmpty()) {
			return;
		}
		ArenaData.Hazard hazard = active.get(boss.getRandom().nextInt(active.size()));
		start(level, hazard, players.get(boss.getRandom().nextInt(players.size())));
		cooldown = (phase >= 3 ? 90 : 130) - 20 * boss.getDifficulty() + boss.getRandom().nextInt(30);
	}

	/** The boss bar's lair colour, and its fog and dark sky from their phases. */
	private void styleBar(int phase) {
		ServerBossEvent bar = OnePieceBridge.bossBar(boss);
		if (bar == null) {
			return;
		}
		ArenaData arena = arena();
		BossEvent.BossBarColor color = color(arena.bar);
		if (color != null && bar.getColor() != color) {
			bar.setColor(color);
		}
		bar.setCreateWorldFog(arena.fogFrom > 0 && phase >= arena.fogFrom);
		bar.setDarkenScreen(arena.darkenFrom > 0 && phase >= arena.darkenFrom);
	}

	public static BossEvent.BossBarColor color(String name) {
		if (name == null || name.isEmpty()) {
			return null;
		}
		try {
			return BossEvent.BossBarColor.valueOf(name.toUpperCase(java.util.Locale.ROOT));
		} catch (IllegalArgumentException e) {
			return null;
		}
	}

	// ---- Starting hazards ----

	/** Starts one hazard aimed at a player. Public so the in-world test can set each one off. */
	public void start(ServerLevel level, ArenaData.Hazard hazard, ServerPlayer target) {
		Vec3 at = target.position();
		int extra = boss.getDifficulty();
		switch (hazard.type) {
			case "collapse" -> strikes.add(new Strike(hazard, ground(level, at), WARN_TICKS + 10)); // Under them even mid-jump.
			case "debris", "lightning" -> {
				strikes.add(new Strike(hazard, at, WARN_TICKS));
				for (int i = 0; i < extra + 1; i++) { // More around them, so standing still isn't the only answer.
					strikes.add(new Strike(hazard, near(level, at, 3, 6), WARN_TICKS + 6 * (i + 1)));
				}
			}
			case "geyser" -> {
				strikes.add(new Strike(hazard, at, WARN_TICKS));
				for (int i = 0; i < extra; i++) {
					strikes.add(new Strike(hazard, near(level, at, 2, 5), WARN_TICKS + 8 * (i + 1)));
				}
			}
			case "cloud" -> {
				clouds.add(new Cloud(hazard, at, CLOUD_TICKS + 40 * extra));
				level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.0f, 0.5f);
			}
			case "tide" -> {
				strikes.add(new Strike(hazard, boss.position(), WARN_TICKS));
				level.playSound(null, boss.blockPosition(), SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.0f, 0.6f);
			}
			case "fog" -> fogPulse = 0;
			default -> {
			}
		}
	}

	/** The floor under a spot (a player may be mid-jump or knocked into the air): up to 6 blocks down, else the spot itself. */
	private static Vec3 ground(ServerLevel level, Vec3 at) {
		BlockPos pos = BlockPos.containing(at);
		for (int dy = 0; dy <= 6; dy++) {
			BlockPos below = pos.below(dy + 1);
			if (level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)) {
				return new Vec3(at.x, below.getY() + 1, at.z);
			}
		}
		return at;
	}

	/** A spot on the ground a few blocks from `at`, or `at` itself if there's no floor there. */
	private Vec3 near(ServerLevel level, Vec3 at, double min, double max) {
		for (int attempt = 0; attempt < 8; attempt++) {
			double angle = boss.getRandom().nextDouble() * Math.PI * 2;
			double dist = min + boss.getRandom().nextDouble() * (max - min);
			BlockPos base = BlockPos.containing(at.x + Math.cos(angle) * dist, at.y, at.z + Math.sin(angle) * dist);
			for (int dy : new int[] {0, 1, -1, 2, -2}) {
				BlockPos pos = base.offset(0, dy, 0);
				if (level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
						&& level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) {
					return new Vec3(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
				}
			}
		}
		return at;
	}

	private void announce(ServerLevel level, String line) {
		if (line == null || line.isEmpty()) {
			return;
		}
		Component text = Component.literal(line).withStyle(ChatFormatting.DARK_AQUA, ChatFormatting.ITALIC);
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, boss.getBoundingBox().inflate(32), p -> !p.isSpectator())) {
			player.sendSystemMessage(text);
		}
	}

	// ---- Marked hazards: they warn, then land ----

	private static final class Strike {
		final ArenaData.Hazard hazard;
		final Vec3 at;
		int ticks;

		Strike(ArenaData.Hazard hazard, Vec3 at, int ticks) {
			this.hazard = hazard;
			this.at = at;
			this.ticks = ticks;
		}
	}

	private void tickStrikes(ServerLevel level) {
		List<Strike> due = new ArrayList<>();
		for (Iterator<Strike> it = strikes.iterator(); it.hasNext();) {
			Strike strike = it.next();
			if (--strike.ticks <= 0) {
				it.remove();
				due.add(strike);
			} else if (strike.ticks <= WARN_TICKS && strike.ticks % 4 == 0) {
				warn(level, strike);
			}
		}
		for (Strike strike : due) {
			land(level, strike);
			landed.merge(strike.hazard.type, 1, Integer::sum);
		}
	}

	private void warn(ServerLevel level, Strike strike) {
		Vec3 at = strike.at;
		switch (strike.hazard.type) {
			case "collapse" -> {
				BlockPos floor = BlockPos.containing(at.x, at.y - 0.5, at.z);
				BlockState state = level.getBlockState(floor);
				if (!state.isAir()) {
					level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), at.x, floor.getY() + 1.05, at.z, 14,
							1.2, 0.05, 1.2, 0.05);
					if (strike.ticks % 12 == 0) {
						level.playSound(null, floor, state.getSoundType().getBreakSound(), SoundSource.BLOCKS, 1.0f, 0.6f);
					}
				}
			}
			case "debris" -> {
				ring(level, at, 2.0, WARNING);
				level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, block(strike.hazard)), at.x, at.y + 7, at.z, 6,
						0.8, 0.5, 0.8, 0.0);
			}
			case "geyser" -> {
				ring(level, at, 1.3, WARNING);
				level.sendParticles(ParticleTypes.SMOKE, at.x, at.y + 0.1, at.z, 6, 0.3, 0.05, 0.3, 0.02);
				if (strike.ticks % 12 == 0) {
					level.playSound(null, at.x, at.y, at.z, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 1.0f, 0.8f);
				}
			}
			case "lightning" -> {
				ring(level, at, 2.0, WARNING);
				level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + 0.3, at.z, 8, 0.6, 0.3, 0.6, 0.05);
			}
			case "tide" -> {
				double grow = TIDE_RADIUS * (1 - strike.ticks / (double) WARN_TICKS);
				ring(level, at, Math.max(1.5, grow), WARNING);
				level.sendParticles(particle(strike.hazard, ParticleTypes.SPLASH), at.x, at.y + 0.5, at.z, 10, 1.0, 0.3, 1.0, 0.1);
			}
			default -> {
			}
		}
	}

	private void land(ServerLevel level, Strike strike) {
		Vec3 at = strike.at;
		ArenaData.Hazard hazard = strike.hazard;
		float damage = (float) boss.getAttributeValue(Attributes.ATTACK_DAMAGE);
		switch (hazard.type) {
			case "collapse" -> collapse(level, at);
			case "debris" -> {
				BlockState look = block(hazard);
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, look), at.x, at.y + 0.6, at.z, 50, 0.9, 0.5, 0.9, 0.15);
				level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.4, 0.2, 0.4, 0.0);
				level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.2f, 0.8f);
				for (ServerPlayer player : hit(level, at, 2.2, 3.0)) {
					player.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.6f);
				}
			}
			case "geyser" -> {
				ParticleOptions look = particle(hazard, ParticleTypes.CLOUD);
				for (double y = 0; y < 6; y += 0.5) {
					level.sendParticles(look, at.x, at.y + y, at.z, 5, 0.25, 0.15, 0.25, 0.03);
				}
				level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5f, 0.6f);
				for (ServerPlayer player : hit(level, at, 1.6, 2.5)) {
					player.setDeltaMovement(player.getDeltaMovement().x, 1.0, player.getDeltaMovement().z);
					OnePieceBridge.syncMotion(player);
					player.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.5f);
					if (hazard.fire) {
						player.igniteForSeconds(4);
					}
				}
			}
			case "lightning" -> {
				LightningBolt bolt = new LightningBolt(EntityTypes.LIGHTNING_BOLT, level);
				bolt.setPos(at);
				bolt.setVisualOnly(true); // Nothing catches fire: the lair stays as it is.
				level.addFreshEntity(bolt);
				level.playSound(null, at.x, at.y, at.z, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 1.5f, 1.1f);
				for (ServerPlayer player : hit(level, at, 2.5, 3.0)) {
					player.hurtServer(level, level.damageSources().lightningBolt(), damage * 0.7f);
				}
			}
			case "tide" -> {
				ParticleOptions look = particle(hazard, ParticleTypes.SPLASH);
				for (double r = 1.5; r <= TIDE_RADIUS; r += 1.5) {
					ring(level, at, r, look);
				}
				level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0f, 0.5f);
				for (ServerPlayer player : hit(level, at, TIDE_RADIUS, 4.0)) {
					Vec3 away = player.position().subtract(at).multiply(1, 0, 1);
					away = away.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : away.normalize();
					player.setDeltaMovement(away.x * 1.3, 0.45, away.z * 1.3);
					OnePieceBridge.syncMotion(player);
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
					player.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.4f);
				}
			}
			default -> {
			}
		}
	}

	/** Players standing within `radius` (sideways) and `height` (up or down) of a spot. */
	private List<ServerPlayer> hit(ServerLevel level, Vec3 at, double radius, double height) {
		return level.getEntitiesOfClass(ServerPlayer.class, new AABB(at, at).inflate(radius, height, radius),
				p -> p.isAlive() && !p.isSpectator() && !p.isCreative()
						&& (p.getX() - at.x) * (p.getX() - at.x) + (p.getZ() - at.z) * (p.getZ() - at.z) <= radius * radius);
	}

	private List<ServerPlayer> players(ServerLevel level) {
		return level.getEntitiesOfClass(ServerPlayer.class, boss.getBoundingBox().inflate(ARENA_RANGE),
				p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
	}

	private static void ring(ServerLevel level, Vec3 at, double radius, ParticleOptions particle) {
		int points = Math.max(10, (int) (radius * 7));
		for (int i = 0; i < points; i++) {
			double angle = Math.PI * 2 * i / points;
			level.sendParticles(particle, at.x + Math.cos(angle) * radius, at.y + 0.15, at.z + Math.sin(angle) * radius, 1, 0, 0, 0, 0);
		}
	}

	// ---- Collapsing floors ----

	private static final class Hole {
		final BlockPos pos;
		final BlockState state;
		int ticks;

		Hole(BlockPos pos, BlockState state, int ticks) {
			this.pos = pos;
			this.state = state;
			this.ticks = ticks;
		}
	}

	/** Opens a shallow pit in the floor at a spot: 3x3, or wider on Hard and Expert. */
	private void collapse(ServerLevel level, Vec3 at) {
		BlockPos center = BlockPos.containing(at.x, at.y - 0.5, at.z);
		int radius = boss.getDifficulty() > 0 ? 2 : 1;
		int opened = 0;
		for (int dx = -radius; dx <= radius; dx++) {
			for (int dz = -radius; dz <= radius; dz++) {
				if (radius == 2 && Math.abs(dx) == 2 && Math.abs(dz) == 2) {
					continue; // Round the corners.
				}
				BlockPos top = center.offset(dx, 0, dz);
				// Never right under the boss: it would only fall in its own pit.
				double bx = boss.getX() - (top.getX() + 0.5), bz = boss.getZ() - (top.getZ() + 0.5);
				if (bx * bx + bz * bz < 6.25) {
					continue;
				}
				opened += openColumn(level, top);
			}
		}
		if (opened > 0) {
			BlockState look = level.getBlockState(center.below(2));
			level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y, at.z, 1, 0, 0, 0, 0);
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, look.isAir() ? Blocks.STONE.defaultBlockState() : look),
					at.x, at.y - 0.5, at.z, 40, 1.2, 0.4, 1.2, 0.1);
			level.playSound(null, center, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.BLOCKS, 0.8f, 0.5f);
		}
	}

	/** Takes out the top two blocks of a floor column, if that's safe. Returns how many blocks were removed. */
	private int openColumn(ServerLevel level, BlockPos top) {
		BlockPos second = top.below();
		if (!removable(level, top)) {
			return 0;
		}
		boolean both = removable(level, second);
		// The pit needs a floor of its own close below: no drops into caves, the sea or the void.
		BlockPos bottom = both ? second.below() : second;
		boolean floor = false;
		for (int dy = 0; dy < 3; dy++) {
			BlockPos pos = bottom.below(dy);
			BlockState state = level.getBlockState(pos);
			if (!state.getFluidState().isEmpty()) {
				return 0; // Never open onto water or lava.
			}
			if (state.isFaceSturdy(level, pos, Direction.UP)) {
				floor = true;
				break;
			}
		}
		if (!floor) {
			return 0;
		}
		int removed = 0;
		for (BlockPos pos : both ? List.of(top, second) : List.of(top)) {
			holes.add(new Hole(pos.immutable(), level.getBlockState(pos), RESTORE_TICKS));
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), QUIET);
			removed++;
		}
		return removed;
	}

	private static boolean removable(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		return !state.isAir() && state.getFluidState().isEmpty() && !state.hasBlockEntity()
				&& state.getDestroySpeed(level, pos) >= 0 && state.isCollisionShapeFullBlock(level, pos)
				&& level.getBlockState(pos.above()).getFluidState().isEmpty();
	}

	/**
	 * Puts collapsed floor back once its time is up (all of it if `all`). Lowest blocks first, and anything standing in
	 * the pit is lifted out onto the restored floor, so nobody ends up inside a block.
	 */
	private void restore(ServerLevel level, boolean all) {
		if (holes.isEmpty()) {
			return;
		}
		List<Hole> due = new ArrayList<>();
		for (Iterator<Hole> it = holes.iterator(); it.hasNext();) {
			Hole hole = it.next();
			if ((all || --hole.ticks <= 0) && level.isLoaded(hole.pos)) {
				it.remove();
				due.add(hole);
			}
		}
		due.sort(Comparator.comparingInt(hole -> hole.pos.getY()));
		for (Hole hole : due) {
			BlockState now = level.getBlockState(hole.pos);
			if (!now.isAir() && !now.canBeReplaced()) {
				continue; // Someone built there meanwhile: leave it.
			}
			level.setBlock(hole.pos, hole.state, QUIET);
			for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, new AABB(hole.pos))) {
				entity.teleportTo(entity.getX(), hole.pos.getY() + 1.0, entity.getZ());
			}
		}
	}

	// ---- Clouds and fog ----

	private static final class Cloud {
		final ArenaData.Hazard hazard;
		final Vec3 at;
		int ticks;

		Cloud(ArenaData.Hazard hazard, Vec3 at, int ticks) {
			this.hazard = hazard;
			this.at = at;
			this.ticks = ticks;
		}
	}

	private void tickClouds(ServerLevel level) {
		for (Iterator<Cloud> it = clouds.iterator(); it.hasNext();) {
			Cloud cloud = it.next();
			if (--cloud.ticks <= 0) {
				it.remove();
				continue;
			}
			if (cloud.ticks % 4 == 0) {
				level.sendParticles(particle(cloud.hazard, ParticleTypes.CAMPFIRE_COSY_SMOKE), cloud.at.x, cloud.at.y + 0.8, cloud.at.z,
						10, CLOUD_RADIUS * 0.6, 0.5, CLOUD_RADIUS * 0.6, 0.005);
			}
			if (cloud.ticks % 20 == 0) {
				Holder<MobEffect> effect = effect(cloud.hazard);
				for (ServerPlayer player : hit(level, cloud.at, CLOUD_RADIUS, 2.5)) {
					if (effect != null) {
						player.addEffect(new MobEffectInstance(effect, effect.is(MobEffects.NAUSEA) ? 140 : 80, 0));
					}
				}
				landed.merge("cloud", 1, Integer::sum);
			}
		}
	}

	/** Darkness washes over everyone in the fog now and then. */
	private void fogTick(ServerLevel level) {
		if (--fogPulse > 0) {
			return;
		}
		fogPulse = FOG_PULSE_TICKS - 30 * boss.getDifficulty();
		for (ServerPlayer player : players(level)) {
			player.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0));
		}
		level.playSound(null, boss.blockPosition(), SoundEvents.AMBIENT_CAVE.value(), SoundSource.HOSTILE, 1.0f, 0.7f);
		landed.merge("fog", 1, Integer::sum);
	}

	// ---- The end of the fight ----

	/** The boss fell or was removed: the floor comes back and the hazards stop. */
	public void end(ServerLevel level) {
		strikes.clear();
		clouds.clear();
		restore(level, true);
		holes.clear();
	}

	// ---- Looking things up from arenas.json ----

	private static BlockState block(ArenaData.Hazard hazard) {
		Identifier id = Identifier.tryParse(hazard.block);
		Block block = id != null ? BuiltInRegistries.BLOCK.getValue(id) : Blocks.AIR;
		return block == null || block == Blocks.AIR ? Blocks.COBBLESTONE.defaultBlockState() : block.defaultBlockState();
	}

	private static ParticleOptions particle(ArenaData.Hazard hazard, ParticleOptions fallback) {
		Identifier id = Identifier.tryParse(hazard.particle);
		if (id != null && BuiltInRegistries.PARTICLE_TYPE.getValue(id) instanceof SimpleParticleType simple) {
			return simple;
		}
		return fallback;
	}

	private static Holder<MobEffect> effect(ArenaData.Hazard hazard) {
		Identifier id = Identifier.tryParse(hazard.effect);
		return id == null ? null : BuiltInRegistries.MOB_EFFECT.get(id).<Holder<MobEffect>>map(ref -> ref).orElse(null);
	}

	// ---- For the in-world test ----

	/** How many times each kind of hazard has landed (cloud and fog count each time they touch you). */
	public int landed(String type) {
		return landed.getOrDefault(type, 0);
	}

	/** How many collapsed blocks are waiting to be put back. */
	public int openHoles() {
		return holes.size();
	}

	// ---- Saving and loading: only open holes, so a reload never leaves the floor missing ----

	public String saveHoles() {
		StringBuilder out = new StringBuilder();
		for (Hole hole : holes) {
			if (!out.isEmpty()) {
				out.append(';');
			}
			out.append(hole.pos.getX()).append(',').append(hole.pos.getY()).append(',').append(hole.pos.getZ()).append(',')
					.append(Block.getId(hole.state));
		}
		return out.toString();
	}

	public void loadHoles(String saved) {
		holes.clear();
		if (saved == null || saved.isEmpty()) {
			return;
		}
		for (String entry : saved.split(";")) {
			String[] parts = entry.split(",");
			if (parts.length != 4) {
				continue;
			}
			try {
				BlockPos pos = new BlockPos(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]));
				holes.add(new Hole(pos, Block.stateById(Integer.parseInt(parts[3])), 0));
			} catch (NumberFormatException e) {
				// A damaged entry: skip it.
			}
		}
		loadedHoles = !holes.isEmpty();
	}
}
