package com.onepiecebosses.test;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import com.mojang.datafixers.util.Pair;

import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.onepiecebosses.BossItems;
import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.loot.LairChests;
import com.onepiecebosses.sea.BossShips;
import com.onepiecebosses.sea.SeaBosses;
import com.onepiecebosses.sea.SeaKingBossEntity;
import com.onepiecebosses.sea.SeaKings;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipTemplates;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.shipcombat.ShipHull;

/**
 * In-world check of the sea bosses, out on a real ocean (a normal world, seed "sea-bosses"), sailing one of the main
 * mod's small pirate ships as the player's own:
 *  - each flagship comes out after the player: its tags, its boss hull, its blocks (the strongroom chest, locked to
 *    its captain's key), a screenshot from the water; its special hits the player's ship; boarding it below half its
 *    hull (the main mod's Boarding.board) brings out the captain on deck, who drops their key when beaten;
 *  - each Sea King mini-boss: its health, a screenshot surfacing beside the ship, the ambush (the hull takes the
 *    breach), and its trophy and the bounty for beating it.
 * Results are "SEA" lines in the log; anything wrong says FAIL. Run it alone with
 * `gradlew runClientGameTest -Dopbosses.tests=sea` (add -Dopbosses.only=widowmaker,gulpmaw for just those).
 */
public class SeaClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("sea-test");
	private static final List<String> FAILURES = new java.util.concurrent.CopyOnWriteArrayList<>();

	private BlockPos sea;
	private static final List<BlockPos> USED = new java.util.ArrayList<>();
	private ShipEntity own;

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("sea")) {
			return;
		}
		try {
			run(context);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private void run(ClientGameTestContext context) throws Exception {
		try (TestSingleplayerContext sp = context.worldBuilder().adjustSettings(SeaClientTest::oceanWorld).create()) {
			sp.getConnection().waitForChunksRender();
			cmd(sp, "race set @p human");
			cmd(sp, "gamemode survival @a");
			cmd(sp, "time set noon");
			cmd(sp, "weather clear");
			cmd(sp, "gamerule advance_time false");
			cmd(sp, "gamerule spawn_mobs false");
			cmd(sp, "difficulty normal");
			context.waitTicks(10);
			context.setScreen(() -> null);
			context.runOnClient(client -> {
				try {
					Field visible = Class.forName("com.onepiecemod.questtree.client.QuestTreePanel").getDeclaredField("visible");
					visible.setAccessible(true);
					visible.set(null, false);
				} catch (ReflectiveOperationException e) {
					LOG.info("SEA could not hide quest panel: {}", e.toString());
				}
			});
			server(sp, s -> {
				ServerLevel level = s.overworld();
				Pair<BlockPos, Holder<Biome>> ocean = level.findClosestBiome3d(h -> h.is(BiomeTags.IS_DEEP_OCEAN), new BlockPos(0, level.getSeaLevel(), 0),
						1200, 32, 64);
				check(ocean != null, "no deep ocean within 1200 blocks of spawn");
				sea = ocean != null ? new BlockPos(ocean.getFirst().getX(), level.getSeaLevel(), ocean.getFirst().getZ()) : BlockPos.ZERO;
				LOG.info("SEA ocean at {}", sea.toShortString());
				ServerPlayer p = player(s);
				p.teleportTo(level, sea.getX() + 0.5, sea.getY() + 20, sea.getZ() + 0.5, Set.of(), 0f, 30f, true);
				p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 3600, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.SATURATION, 20 * 3600, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 20 * 3600, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 20 * 3600, 0, false, false));
			});
			context.waitTicks(60);
			sp.getConnection().waitForChunksRender();
			if (sea.equals(BlockPos.ZERO)) {
				return;
			}

			int i = 0;
			for (String id : BossShips.IDS) {
				if (TestFilter.picks(id, BossShips.captainOf(id))) {
					flagshipTest(context, sp, id, i);
				}
				i++;
			}
			for (SeaKingBossEntity.Kind kind : SeaKingBossEntity.Kind.values()) {
				if (TestFilter.picks(kind.id)) {
					seaKingTest(context, sp, kind, i);
				}
				i++;
			}
			LOG.info("SEA DONE, {} failures", FAILURES.size());
		}
		if (!FAILURES.isEmpty()) {
			throw new AssertionError("One Piece Bosses sea test failures:\n" + String.join("\n", FAILURES));
		}
	}

	/** A normal world, so there's a real ocean to sail. */
	private static void oceanWorld(WorldCreationUiState creator) {
		creator.setWorldType(new WorldCreationUiState.WorldTypeEntry(
				creator.getSettings().worldgenLoadContext().lookupOrThrow(Registries.WORLD_PRESET).getOrThrow(WorldPresets.NORMAL)));
		creator.setGenerateStructures(false);
		creator.setAllowCommands(true);
		creator.setSeed("sea-bosses");
	}

	// ---- Flagships ----

	private void flagshipTest(ClientGameTestContext context, TestSingleplayerContext sp, String id, int index) throws Exception {
		String captain = BossShips.captainOf(id);
		ShipEntity[] flagship = new ShipEntity[1];
		Vec3[] camera = new Vec3[1];
		sail(context, sp, index);
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			ShipTemplates.Spec spec = ShipTemplates.spec(s, id);
			check(spec != null, id + ": no ship spec (data/opbosses/ships/" + id + ".json)");
			check(spec == null || "boss".equals(spec.faction), id + ": its faction isn't \"boss\" (it would turn up as a random pirate)");
			ShipLayout layout = ShipTemplates.layout(level, id);
			check(layout != null, id + ": its structure didn't load");
			if (layout != null) {
				long helms = layout.blocks.stream().filter(b -> b.state().getBlock().getDescriptionId().contains("ships_wheel")).count();
				List<ShipLayout.ShipBlock> chests = layout.blocks.stream().filter(b -> b.state().is(LairChests.BLOCKS.get(id))).toList();
				String lock = chests.isEmpty() ? "" : chests.get(0).nbt().map(Object::toString).orElse("");
				LOG.info("SEA {} {} blocks, {} helm(s), {} strongroom chest(s), lock {}", id, layout.size(), helms, chests.size(), lock);
				check(layout.size() > 3000, id + ": only " + layout.size() + " blocks");
				check(chests.size() == 1, id + ": " + chests.size() + " strongroom chests (want 1)");
				check(lock.contains("key_" + captain), id + ": the strongroom isn't locked to key_" + captain + " (" + lock + ")");
				check(lock.contains("opbosses:chests/" + id), id + ": the strongroom has no loot table");
			}
			ShipEntity ship = SeaBosses.sendShip(level, p, id);
			check(ship != null, id + ": didn't come out on open sea");
			if (ship == null) {
				return;
			}
			flagship[0] = ship;
			// Bring her in close for the camera and the special.
			Vec3 at = own.position().add(0, 0, 45);
			ship.snapTo(at.x, ship.getY(), at.z, 90f, 0f);
			check(ShipBrain.isAi(ship) && ShipBrain.factionOf(ship) == ShipBrain.Faction.PIRATE, id + ": isn't an enemy pirate ship");
			check(id.equals(BossShips.idOf(ship)) && ship.entityTags().contains(BossShips.TAG), id + ": is missing its tags " + ship.entityTags());
			float max = ShipHull.max(ship);
			LOG.info("SEA {} named '{}', hull {}, tier {}", id, ship.getName().getString(), max, ShipBrain.tierOf(ship));
			check(max > 700, id + ": hull " + max + " is no tougher than a big pirate ship's");
			camera[0] = at.add(-44, 18, -34);
			look(p, camera[0], at.add(0, 6, 0));
		});
		if (flagship[0] == null) {
			return;
		}
		context.waitTicks(40);
		sp.getConnection().waitForChunksRender();
		clearChat(context);
		context.takeScreenshot("sea_" + id);
		server(sp, s -> {
			ServerPlayer p = player(s);
			look(p, flagship[0].position().add(18, 12, -26), flagship[0].position().add(0, 6, 0));
		});
		context.waitTicks(30);
		clearChat(context);
		context.takeScreenshot("sea_" + id + "_bow");

		// Her special hits the player's ship.
		server(sp, s -> {
			ServerPlayer p = player(s);
			p.startRiding(own);
			float before = ShipHull.get(own);
			check(BossShips.fireSpecial(flagship[0], own), id + ": fireSpecial says she isn't a flagship");
			float after = ShipHull.get(own);
			LOG.info("SEA {} special: own hull {} -> {}, burning {}, darkness {}", id, before, after, ShipHull.burning(own), p.hasEffect(MobEffects.DARKNESS));
			check(after < before, id + ": her special didn't hurt the player's hull");
			if (id.equals("cinderwake")) {
				check(ShipHull.burning(own), id + ": the ember broadside didn't set the ship on fire");
			}
			if (id.equals("tithe_cathedral")) {
				check(p.hasEffect(MobEffects.DARKNESS), id + ": the bell didn't dim the deck");
			}
			ShipHull.setMax(own, ShipHull.max(own));
		});

		// Board her below half her hull: the captain is waiting on deck.
		BlockPos[] deck = new BlockPos[1];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			ShipEntity ship = flagship[0];
			ship.setAttached(ShipHull.HULL, ShipHull.max(ship) * 0.3f);
			p.stopRiding();
			own.snapTo(own.getX(), own.getY(), own.getZ() - 60, own.getYRot(), 0f); // Clear of where she docks.
			InteractionResult result = board(p, ship);
			LOG.info("SEA {} boarding: {}, player at {}", id, result, p.blockPosition().toShortString());
			check(result == InteractionResult.SUCCESS, id + ": boarding her at 30% hull didn't work (" + result + ")");
			deck[0] = p.blockPosition();
			List<RogueBossEntity> bosses = level.getEntitiesOfClass(RogueBossEntity.class, p.getBoundingBox().inflate(16),
					b -> b.getCharacterId().equals(captain));
			check(bosses.size() == 1, id + ": " + bosses.size() + " " + captain + " on deck after boarding (want 1)");
			if (!bosses.isEmpty()) {
				RogueBossEntity boss = bosses.get(0);
				LOG.info("SEA {} captain {} at {} ({} blocks away), target {}", id, captain, boss.blockPosition().toShortString(),
						String.format("%.1f", boss.distanceTo(p)), boss.getTarget() == null ? "none" : boss.getTarget().getName().getString());
				check(boss.getTarget() == p, id + ": the captain isn't after the boarder");
				check(level.getBlockState(boss.blockPosition().below()).isSolid(), id + ": the captain isn't standing on the deck");
				look(p, boss.position().add(-4, 3, -4), boss.position().add(0, 1.4, 0));
			}
			BlockPos chest = findBlock(level, p.blockPosition(), 40, LairChests.BLOCKS.get(id));
			check(chest != null, id + ": no strongroom chest in the docked ship");
		});
		context.waitTicks(30);
		clearChat(context);
		context.takeScreenshot("sea_" + id + "_captain");
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			for (RogueBossEntity boss : level.getEntitiesOfClass(RogueBossEntity.class, p.getBoundingBox().inflate(24), b -> b.getCharacterId().equals(captain))) {
				boss.hurtServer(level, p.damageSources().playerAttack(p), 1_000_000f);
			}
		});
		context.waitTicks(20);
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			boolean key = !level.getEntitiesOfClass(ItemEntity.class, p.getBoundingBox().inflate(24),
					e -> e.getItem().is(BossItems.KEYS.get(captain))).isEmpty() || p.getInventory().contains(new net.minecraft.world.item.ItemStack(BossItems.KEYS.get(captain)));
			LOG.info("SEA {} captain beaten, key dropped {}", id, key);
			check(key, id + ": the captain didn't drop key_" + captain);
			clearMobs(s, p.position(), 60);
		});
	}

	// ---- Sea Kings ----

	private void seaKingTest(ClientGameTestContext context, TestSingleplayerContext sp, SeaKingBossEntity.Kind kind, int index) throws Exception {
		SeaKingBossEntity[] king = new SeaKingBossEntity[1];
		sail(context, sp, index);
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			SeaKingBossEntity k = SeaBosses.sendSeaKing(level, p, kind);
			check(k != null, kind.id + ": didn't come out of the deep");
			if (k == null) {
				return;
			}
			king[0] = k;
			LOG.info("SEA {} health {}, name '{}'", kind.id, k.getMaxHealth(), k.getName().getString());
			check(Math.abs(k.getMaxHealth() - kind.health) < 1, kind.id + ": health " + k.getMaxHealth() + ", want " + kind.health);
			check(k.getType() == SeaKings.TYPES.get(kind), kind.id + ": the wrong mob type");
			// Surfaced beside the ship for its portrait.
			// Well clear of the player's ship, seen side-on from the far side so the ship isn't in the way.
			Vec3 at = own.position().add(0, 0, 40);
			k.setNoAi(true);
			k.snapTo(at.x, level.getSeaLevel() - 1.2, at.z, 90f, 0f);
			look(p, at.add(-4, 5, 13), at.add(-3, 1, 0));
		});
		if (king[0] == null) {
			return;
		}
		context.waitTicks(40);
		clearChat(context);
		context.takeScreenshot("sea_" + kind.id);

		// The ambush: bubbles, then it breaches under the keel.
		float[] hull = new float[1];
		server(sp, s -> {
			ServerPlayer p = player(s);
			// At the helm (riding the ship counts as aboard at once); the breach screenshot is from the deck.
			p.getAbilities().flying = false;
			p.onUpdateAbilities();
			check(p.startRiding(own), kind.id + ": couldn't take the helm of the player's ship");
			hull[0] = ShipHull.get(own);
			king[0].setNoAi(false);
			king[0].hunt(p);
			king[0].ambushIn(5);
			LOG.info("SEA {} ambush set, aboard {}", kind.id, ShipEntity.aboard(p) == own);
		});
		context.waitTicks(78); // 5 + 70 ticks of warning, then the breach
		// Out of the splash, to see it rear up beside the ship.
		server(sp, s -> look(player(s), own.position().add(-16, 8, 14), king[0].position().add(0, 4, 0)));
		context.waitTicks(5);
		clearChat(context);
		context.takeScreenshot("sea_" + kind.id + "_breach");
		context.waitTicks(20);
		server(sp, s -> {
			float after = ShipHull.get(own);
			LOG.info("SEA {} ambush: own hull {} -> {}, king at {} ({} from the ship), dazed {}", kind.id, hull[0], after,
					king[0].blockPosition().toShortString(), String.format("%.1f", king[0].distanceTo(own)), king[0].dazed());
			check(after < hull[0], kind.id + ": the breach didn't hurt the hull");
			if (kind == SeaKingBossEntity.Kind.IRONSCALE) {
				check(king[0].dazed(), kind.id + ": isn't dazed after breaching");
			}
			ShipHull.setMax(own, ShipHull.max(own));
		});

		// Beaten: its trophy, and a bigger bounty.
		long[] bounty = new long[1];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			bounty[0] = Bounty.get(p);
			king[0].hurtServer(level, p.damageSources().playerAttack(p), 1_000_000f);
		});
		context.waitTicks(30);
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			Vec3 where = king[0].position();
			boolean trophy = !level.getEntitiesOfClass(ItemEntity.class, new AABB(where, where).inflate(20),
					e -> e.getItem().is(SeaKings.TROPHIES.get(kind))).isEmpty();
			long after = Bounty.get(p);
			LOG.info("SEA {} beaten: dead {}, trophy {}, bounty {} -> {}", kind.id, !king[0].isAlive(), trophy, bounty[0], after);
			check(!king[0].isAlive(), kind.id + ": survived a million damage");
			check(trophy, kind.id + ": no trophy dropped");
			check(after > bounty[0], kind.id + ": beating it didn't raise the bounty");
			clearMobs(s, p.position(), 60);
		});
	}

	// ---- Helpers ----

	/** Puts the player at the helm of a small pirate ship of the main mod's, their own, somewhere fresh on the ocean. */
	private void sail(ClientGameTestContext context, TestSingleplayerContext sp, int index) throws Exception {
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			if (own != null && !own.isRemoved()) {
				p.stopRiding();
				own.discard();
			}
			// Somewhere fresh each time, far from the others (a boarded flagship is docked into blocks where she was), with
			// deep water all around (a Sea King needs 8 blocks of it).
			BlockPos spot = null;
			for (int tries = 0; tries < 12 && spot == null; tries++) {
				BlockPos from = sea.offset(320 * (tries % 4) - 480, 0, -400 * index - 300 * (tries / 4));
				Pair<BlockPos, Holder<Biome>> ocean = level.findClosestBiome3d(h -> h.is(BiomeTags.IS_DEEP_OCEAN), from, 600, 16, 64);
				if (ocean == null) {
					continue;
				}
				BlockPos c = new BlockPos(ocean.getFirst().getX(), sea.getY(), ocean.getFirst().getZ());
				if (USED.stream().anyMatch(u -> u.distSqr(c) < 220 * 220)) {
					continue;
				}
				level.getChunk(c); // Loads it, so the water check below is real.
				spot = c;
			}
			if (spot == null) {
				spot = sea.offset(0, 0, -400 * index);
			}
			USED.add(spot);
			p.teleportTo(level, spot.getX() + 0.5, spot.getY() + 10, spot.getZ() + 0.5, Set.of(), 0f, 20f, true);
		});
		context.waitTicks(40);
		sp.getConnection().waitForChunksRender();
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			ShipTemplates.Spec small = ShipTemplates.specs(s).values().stream().filter(spec -> "pirate".equals(spec.faction))
					.min(Comparator.comparingInt(spec -> spec.blocks)).orElse(null);
			check(small != null, "the main mod has no pirate ships to sail");
			if (small == null) {
				return;
			}
			BlockPos spot = p.blockPosition();
			own = ShipTemplates.spawn(level, small.id, spot.getX(), level.getSeaLevel(), spot.getZ(), 0f);
			check(own != null, "couldn't launch the player's ship " + small.id);
			if (own != null) {
				int deep = 0;
				for (int a = 0; a < 8; a++) {
					double r = Math.toRadians(a * 45);
					if (com.onepiecemod.sea.SeaKingSpawner.isDeepWater(level, spot.offset((int) (Math.cos(r) * 24), -5, (int) (Math.sin(r) * 24)))) {
						deep++;
					}
				}
				LOG.info("SEA deep water in {} of 8 directions around {}", deep, spot.toShortString());
				p.startRiding(own);
				LOG.info("SEA sailing '{}' at {}, aboard {}", own.getName().getString(), own.blockPosition().toShortString(), ShipEntity.aboard(p) == own);
			}
		});
		context.waitTicks(20);
	}

	private static InteractionResult board(ServerPlayer player, ShipEntity ship) {
		try {
			Method board = Class.forName("com.onepiecemod.shipcombat.Boarding").getDeclaredMethod("board", ServerPlayer.class, ShipEntity.class);
			board.setAccessible(true);
			return (InteractionResult) board.invoke(null, player, ship);
		} catch (ReflectiveOperationException e) {
			check(false, "couldn't call Boarding.board: " + e);
			return InteractionResult.FAIL;
		}
	}

	private static BlockPos findBlock(ServerLevel level, BlockPos near, int range, net.minecraft.world.level.block.Block block) {
		for (BlockPos pos : BlockPos.betweenClosed(near.offset(-range, -12, -range), near.offset(range, 16, range))) {
			if (level.getBlockState(pos).is(block)) {
				return pos.immutable();
			}
		}
		return null;
	}

	/** Stands the player at `from` looking at `at` (the screenshots' camera). */
	private static void look(ServerPlayer p, Vec3 from, Vec3 at) {
		p.stopRiding();
		double yaw = Math.toDegrees(Math.atan2(-(at.x - from.x), at.z - from.z));
		double pitch = Math.toDegrees(Math.atan2(from.y - at.y, Math.hypot(at.x - from.x, at.z - from.z)));
		p.teleportTo((ServerLevel) p.level(), from.x, from.y, from.z, Set.of(), (float) yaw, (float) pitch, true);
		p.getAbilities().flying = true;
		p.getAbilities().mayfly = true;
		p.onUpdateAbilities();
	}

	private static void clearChat(ClientGameTestContext context) {
		context.runOnClient(client -> client.gui.hud.getChat().clearMessages(true));
	}

	private void clearMobs(MinecraftServer s, Vec3 at, double range) {
		for (Entity e : s.overworld().getEntitiesOfClass(Entity.class, new AABB(at, at).inflate(range),
				e -> !(e instanceof Player) && e != own)) {
			e.discard();
		}
	}

	private static void check(boolean ok, String what) {
		if (!ok) {
			LOG.info("SEA FAIL {}", what);
			FAILURES.add(what);
		}
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void cmd(TestSingleplayerContext sp, String command) {
		sp.getServer().runCommand(command);
	}

	private static void server(TestSingleplayerContext sp, Consumer<MinecraftServer> action) throws Exception {
		sp.getServer().runOnServer(action::accept);
	}
}
