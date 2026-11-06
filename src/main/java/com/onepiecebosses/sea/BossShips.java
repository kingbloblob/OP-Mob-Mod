package com.onepiecebosses.sea;

import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.boss.RogueBosses;
import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecebosses.loot.LairChests;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipTemplates;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.shipcombat.ShipCombat;
import com.onepiecemod.shipcombat.ShipHull;
import com.onepiecemod.util.Motion;

/**
 * The sea bosses' flagships: the Widowmaker (Maribel Sedge), the Tithe Cathedral (Severo Lume) and the Cinderwake
 * (Kael Ashgrave). Their blocks are data/opbosses/ships/<id>.json + structure/ships/<id>.nbt (tools/ships/), which
 * the One Piece Mod's ShipTemplates reads like its own famous ships.
 *
 * Underneath, a flagship is one of the main mod's enemy pirate ships (ShipBrain sails it, its cannons fire, its hull
 * has a boss bar), with a much tougher hull and a special that its captain fires from the deck every 12 to 16 seconds:
 *  - Widowmaker: a harpoon line. Your ship is caught (the rigging is tangled, like chain shot) and dragged closer.
 *  - Tithe Cathedral: the tolling bell. Everyone on your deck is dimmed and slowed, and the hull cracks.
 *  - Cinderwake: an ember broadside. Your ship catches fire, like fire shot.
 * Cannon her below half her hull and board her (right-click her, the main mod's boarding): her captain is waiting on
 * deck with the crew (BoardingMixin). Beating the captain drops their key, which opens the strongroom chest aboard.
 * Sink her instead and the captain goes down with her: no key, no strongroom.
 */
public final class BossShips {
	private BossShips() {
	}

	public static final String TAG = "opbosses_boss_ship";
	/** Followed by the ship's id, e.g. opbosses_ship_widowmaker. */
	public static final String TAG_SHIP = "opbosses_ship_";
	private static final String TAG_SUNK = "opbosses_ship_sunk";
	private static final double SPECIAL_RANGE = 60;

	private static final Map<ShipEntity, Long> NEXT_SPECIAL = new WeakHashMap<>();

	/** The flagships' ids, in the order they get harder. */
	public static final List<String> IDS = List.copyOf(LairChests.SHIP_BOSSES.keySet());

	public static String captainOf(String shipId) {
		return LairChests.SHIP_BOSSES.get(shipId);
	}

	/** The flagship a boss captains, or null. */
	@Nullable
	public static String shipOf(String bossId) {
		for (Map.Entry<String, String> entry : LairChests.SHIP_BOSSES.entrySet()) {
			if (entry.getValue().equals(bossId)) {
				return entry.getKey();
			}
		}
		return null;
	}

	/** Which flagship this is, or null for any other ship. */
	@Nullable
	public static String idOf(ShipEntity ship) {
		for (String tag : ship.entityTags()) {
			if (tag.startsWith(TAG_SHIP) && !tag.equals(TAG_SUNK)) {
				return tag.substring(TAG_SHIP.length());
			}
		}
		return null;
	}

	/**
	 * Sends a flagship out after a player: it appears 70 to 100 blocks off in open sea, heading for them.
	 * Returns null if it couldn't (unknown ship, or no open deep water around).
	 */
	@Nullable
	public static ShipEntity send(ServerLevel level, ServerPlayer player, String id) {
		String captain = captainOf(id);
		ShipLayout layout = ShipTemplates.layout(level, id);
		if (captain == null || layout == null) {
			return null;
		}
		RogueData data = RogueData.get(captain);
		int tier = data != null ? data.tier() : 3;
		RandomSource random = level.getRandom();
		int reach = Math.max(9, Math.max(layout.max.getX() - layout.min.getX(), layout.max.getZ() - layout.min.getZ()) / 2 + 1);
		ShipEntity sailing = ShipEntity.aboard(player);
		float heading = sailing != null ? sailing.getYRot() : player.getYRot();

		for (int attempt = 0; attempt < 40; attempt++) {
			float yaw = heading + (random.nextFloat() - 0.5f) * 200f;
			double far = 70 + random.nextInt(31);
			int bx = Mth.floor(player.getX() - Mth.sin(yaw * Mth.DEG_TO_RAD) * far);
			int bz = Mth.floor(player.getZ() + Mth.cos(yaw * Mth.DEG_TO_RAD) * far);
			Integer surface = deepWaterSurface(level, bx, bz);
			if (surface == null || deepWaterSurface(level, bx + reach, bz) == null || deepWaterSurface(level, bx - reach, bz) == null
					|| deepWaterSurface(level, bx, bz + reach) == null || deepWaterSurface(level, bx, bz - reach) == null) {
				continue;
			}
			float toward = (float) (Mth.atan2(player.getZ() - bz, player.getX() - bx) * Mth.RAD_TO_DEG) - 90f;
			ShipEntity ship = ShipTemplates.spawn(level, id, bx, surface, bz, toward);
			if (ship == null) {
				return null;
			}
			setUp(ship, id, tier);
			return ship;
		}
		return null;
	}

	/** Makes a freshly spawned ship a flagship: an enemy pirate ship with a boss's hull and tags. */
	public static void setUp(ShipEntity ship, String id, int tier) {
		ShipBrain.mark(ship, ShipBrain.Faction.PIRATE, tier);
		ship.addTag(TAG);
		ship.addTag(TAG_SHIP + id);
		ShipHull.setMax(ship, ShipHull.sizeToHull(ship.getLayout().size()) * (1 + tier * 0.15f));
		NEXT_SPECIAL.put(ship, ship.level().getGameTime() + 200);
	}

	/** Once a second: the flagships' specials, and the news when one sinks with her captain. */
	static void tick(MinecraftServer server) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			if (ship.isRemoved() || !(ship.level() instanceof ServerLevel level) || !ship.entityTags().contains(TAG)) {
				continue;
			}
			String id = idOf(ship);
			if (id == null) {
				continue;
			}
			if (ship.sinking) {
				if (ship.addTag(TAG_SUNK)) {
					sunk(level, ship, id);
				}
				continue;
			}
			long now = level.getGameTime();
			long next = NEXT_SPECIAL.computeIfAbsent(ship, s -> now + 200);
			if (now < next) {
				continue;
			}
			ShipEntity target = nearestPlayerShip(level, ship);
			if (target == null) {
				continue;
			}
			NEXT_SPECIAL.put(ship, now + 240 + level.getRandom().nextInt(80));
			special(level, ship, target, id);
		}
	}

	private static void sunk(ServerLevel level, ShipEntity ship, String id) {
		String captain = captainOf(id);
		String name = captain == null ? "The captain" : OnePieceBridge.characterName(captain);
		Component news = Component.literal(name + " goes down with the " + ship.getName().getString()
				+ ". Board her next time to face them and win the strongroom key.").withStyle(ChatFormatting.GRAY);
		for (ServerPlayer player : level.players()) {
			if (player.distanceToSqr(ship) < 128 * 128) {
				player.sendSystemMessage(news);
			}
		}
	}

	/** The closest ship with a player aboard (not creative, not spectating), within SPECIAL_RANGE. */
	@Nullable
	private static ShipEntity nearestPlayerShip(ServerLevel level, ShipEntity from) {
		ShipEntity best = null;
		double bestDistance = SPECIAL_RANGE * SPECIAL_RANGE;
		for (ShipEntity other : ShipCombat.loadedShips()) {
			if (other == from || other.isRemoved() || other.sinking || other.level() != level || ShipBrain.isAi(other)) {
				continue;
			}
			double distance = other.distanceToSqr(from);
			if (distance < bestDistance && ShipEntity.playersAboard(other).stream().anyMatch(p -> !p.isCreative() && !p.isSpectator())) {
				best = other;
				bestDistance = distance;
			}
		}
		return best;
	}

	/** Fires a flagship's special at that ship right now (the in-game test uses it). False if it isn't a flagship. */
	public static boolean fireSpecial(ShipEntity ship, ShipEntity target) {
		String id = idOf(ship);
		if (id == null || !(ship.level() instanceof ServerLevel level)) {
			return false;
		}
		special(level, ship, target, id);
		return true;
	}

	private static void special(ServerLevel level, ShipEntity ship, ShipEntity target, String id) {
		List<ServerPlayer> aboard = ShipEntity.playersAboard(target);
		Vec3 from = ship.position().add(0, ship.getLayout().waterline + 4, 0);
		Vec3 to = target.position().add(0, target.getLayout().waterline + 1, 0);
		switch (id) {
			case "widowmaker" -> {
				// A harpoon on a chain: your ship is caught and hauled in.
				line(level, from, to, ParticleTypes.CRIT);
				level.playSound(null, BlockPos.containing(to), SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0f, 0.5f);
				level.playSound(null, BlockPos.containing(from), SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 4.0f, 0.5f);
				ShipHull.chain(target, 20 * 8);
				ShipHull.damage(target, 14f, null, to, ship);
				Vec3 haul = from.subtract(to).multiply(1, 0, 1).normalize().scale(0.6);
				target.setDeltaMovement(target.getDeltaMovement().add(haul));
				Motion.sync(target);
				tell(aboard, "A harpoon bites into the hull! The Widowmaker is reeling you in.", ChatFormatting.RED);
			}
			case "tithe_cathedral" -> {
				// Its bell tolls across the water: everyone on deck pays the tithe.
				for (int i = 0; i < 3; i++) {
					level.playSound(null, BlockPos.containing(from), SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 5.0f, 0.5f + i * 0.08f);
				}
				level.sendParticles(ParticleTypes.SOUL, to.x, to.y + 1, to.z, 60, 4, 1.5, 4, 0.03);
				ShipHull.damage(target, 18f, null, to, ship);
				for (ServerPlayer player : aboard) {
					player.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1));
					player.hurtServer(level, level.damageSources().magic(), Math.max(2f, player.getHealth() * 0.15f));
				}
				tell(aboard, "The Tithe Cathedral's bell tolls. The Red Tithe is collected!", ChatFormatting.DARK_RED);
			}
			case "cinderwake" -> {
				// A broadside of burning shot.
				line(level, from, to, ParticleTypes.FLAME);
				level.playSound(null, BlockPos.containing(from), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 4.0f, 0.6f);
				level.sendParticles(ParticleTypes.LAVA, to.x, to.y + 1, to.z, 40, 3, 1, 3, 0.1);
				ShipHull.ignite(target, 20 * 10);
				ShipHull.damage(target, 20f, null, to, ship);
				tell(aboard, "The Cinderwake fires an ember broadside: you're on fire!", ChatFormatting.GOLD);
			}
			default -> {
			}
		}
	}

	private static void line(ServerLevel level, Vec3 from, Vec3 to, net.minecraft.core.particles.ParticleOptions particle) {
		Vec3 step = to.subtract(from);
		int points = (int) Math.min(80, step.length() * 1.5);
		for (int i = 0; i <= points; i++) {
			Vec3 at = from.add(step.scale(i / (double) points));
			level.sendParticles(particle, at.x, at.y, at.z, 1, 0, 0, 0, 0);
		}
	}

	private static void tell(List<ServerPlayer> players, String text, ChatFormatting colour) {
		for (ServerPlayer player : players) {
			player.sendSystemMessage(Component.literal(text).withStyle(colour), true);
		}
	}

	// ---- Boarding: the captain is waiting on deck ----

	/**
	 * Boarding docks the ship into blocks, and the main mod refuses if any block of hers would land on something solid.
	 * A flagship draws a lot of water, so kelp and coral under her keel would stop anyone ever boarding her: they're
	 * cleared to water first. Returns how many blocks are still in the way (rock, another ship), and logs what they are.
	 * BoardingMixin calls this just before Boarding.board.
	 */
	public static int clearKeel(ServerLevel level, ShipEntity ship) {
		int quarterTurns = Math.floorMod(Math.round(Mth.wrapDegrees(ship.rotationSinceBuilt(1.0f)) / 90f), 4);
		net.minecraft.world.level.block.Rotation rotation = switch (quarterTurns) {
			case 1 -> net.minecraft.world.level.block.Rotation.CLOCKWISE_90;
			case 2 -> net.minecraft.world.level.block.Rotation.CLOCKWISE_180;
			case 3 -> net.minecraft.world.level.block.Rotation.COUNTERCLOCKWISE_90;
			default -> net.minecraft.world.level.block.Rotation.NONE;
		};
		BlockPos anchor = BlockPos.containing(ship.getX(), Math.round(ship.getY()), ship.getZ());
		int blocked = 0;
		java.util.Map<String, Integer> what = new java.util.TreeMap<>();
		for (ShipLayout.ShipBlock block : ship.getLayout().blocks) {
			BlockPos target = anchor.offset(block.pos().rotate(rotation));
			net.minecraft.world.level.block.state.BlockState state = level.getBlockState(target);
			if (state.canBeReplaced()) {
				continue;
			}
			if (state.is(net.minecraft.world.level.block.Blocks.KELP) || state.is(net.minecraft.world.level.block.Blocks.KELP_PLANT)
					|| state.is(net.minecraft.tags.BlockTags.CORALS) || state.is(net.minecraft.tags.BlockTags.CORAL_BLOCKS)
					|| state.is(net.minecraft.world.level.block.Blocks.SEA_PICKLE) || state.is(net.minecraft.world.level.block.Blocks.BUBBLE_COLUMN)) {
				level.setBlock(target, net.minecraft.world.level.block.Blocks.WATER.defaultBlockState(), 2);
				continue;
			}
			blocked++;
			what.merge(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath(), 1, Integer::sum);
		}
		if (blocked > 0) {
			com.onepiecebosses.BossesMod.LOGGER.info("Flagship {} can't dock at {}: {} blocks in the way {}", ship.getName().getString(),
					anchor.toShortString(), blocked, what);
		}
		return blocked;
	}

	/**
	 * A player just boarded a flagship (the main mod docked her into blocks and put the player on deck by the wheel):
	 * her captain comes at them. BoardingMixin calls this.
	 */
	public static void captainMeets(ServerLevel level, ServerPlayer player, String shipId) {
		String captain = captainOf(shipId);
		if (captain == null) {
			return;
		}
		RogueBossEntity boss = RogueBosses.ROGUE_BOSS.create(level, EntitySpawnReason.EVENT);
		if (boss == null) {
			return;
		}
		BlockPos spot = deckSpot(level, player.blockPosition());
		boss.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, player.getYRot() + 180, 0);
		boss.setYHeadRot(boss.getYRot());
		boss.setCharacter(captain, true);
		boss.setDifficulty(OnePieceBridge.unlockedDifficulty(player, captain));
		boss.setPersistenceRequired();
		level.addFreshEntity(boss);
		boss.setTarget(player);
		level.sendParticles(ParticleTypes.POOF, boss.getX(), boss.getY() + 1, boss.getZ(), 20, 0.4, 0.8, 0.4, 0.02);
		player.sendSystemMessage(Component.literal(boss.getData().name + " steps out to meet you. Beat them for the key to the strongroom!")
				.withStyle(ChatFormatting.GOLD));
	}

	/** A free deck spot 3 to 5 blocks from the player, or right beside them. */
	private static BlockPos deckSpot(ServerLevel level, BlockPos near) {
		RandomSource random = level.getRandom();
		for (int attempt = 0; attempt < 20; attempt++) {
			BlockPos base = near.offset(random.nextInt(9) - 4, 0, random.nextInt(9) - 4);
			if (base.distManhattan(near) < 3) {
				continue;
			}
			for (int dy : new int[] {0, 1, -1, 2, -2}) {
				BlockPos pos = base.offset(0, dy, 0);
				if (level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
						&& level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()
						&& level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty()
						&& level.getFluidState(pos).isEmpty()) {
					return pos;
				}
			}
		}
		return near.east();
	}

	/** The Y just above the sea's surface if this column is open sea at least 5 blocks deep, otherwise null. */
	@Nullable
	static Integer deepWaterSurface(ServerLevel level, int x, int z) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		if (!level.getFluidState(new BlockPos(x, top - 1, z)).is(FluidTags.WATER) || top - floor < 5) {
			return null;
		}
		return top;
	}
}
