package com.onepiecebosses.test;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

import com.mojang.datafixers.util.Pair;

import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.commands.PlaceCommand;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.phys.AABB;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.onepiecebosses.BossItems;
import com.onepiecebosses.loot.LairChestBlockEntity;
import com.onepiecebosses.loot.LairChests;
import com.onepiecebosses.loot.LairReset;
import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.world.GuardKit;
import com.onepiecemod.world.WorldFeature;

/**
 * In-world check of every rogue lair in a default world: /locate distance from spawn, then /place in a biome the lair
 * spawns in, the boss and crew it sets up, the chest's loot and a screenshot from above. Results are "LT" lines in the
 * log; anything wrong says FAIL. Screenshots go to build/run/clientGameTest/screenshots (lair_<name>.png).
 */
public class LairsClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("lairs-test");
	private static final List<String> FAILURES = new java.util.concurrent.CopyOnWriteArrayList<>();

	private record Lair(String name, String boss, String kit, int crew, boolean sea) {}

	private static final List<Lair> LAIRS = List.of(
			new Lair("scrapheap_reef", "saltjaw_rourke", "scrapdeck_raider", 7, true),
			new Lair("lantern_house", "corvina_fog_widow", "lantern_smuggler", 7, false),
			new Lair("fort_iron_tide", "iron_tide_graves", "deserter_marine", 7, false),
			new Lair("hollow_shrine", "hollow_ronin_tsurugi", "", 0, false),
			new Lair("shipbreakers_foundry", "boilerheart_gantz", "boiler_stoker", 7, false),
			new Lair("abyssal_temple", "nereus_vane", "abyssal_cultist", 7, true),
			new Lair("sunken_kasbah", "khamsin_sandshackle", "sandshackle_raider", 7, false),
			new Lair("gilded_wake", "mortimer_gale", "cursed_deckhand", 7, true),
			new Lair("leviathan_pens", "vasco_tidebreaker", "sea_king_wrangler", 7, true),
			new Lair("laboratory_null", "doctor_kreuz", "pacifista_prototype", 7, false),
			new Lair("gran_tesoro", "gild_tesoro", "gran_tesoro_guard", 7, true),
			new Lair("elegia_stage", "uta_diva", "entranced_fan", 6, false),
			new Lair("end_point", "zephyr_z", "neo_marine", 7, false),
			new Lair("ironclad_colosseum", "douglas_bullet", "", 0, false),
			new Lair("merveille", "shiki_golden_lion", "golden_lion_pirate", 7, false),
			new Lair("gold_island", "el_drago", "el_drago_pirate", 7, false),
			new Lair("salamander", "gasparde", "gasparde_pirate", 7, true),
			new Lair("omatsuri_island", "baron_omatsuri", "red_arrows_pirate", 7, false),
			new Lair("karakuri_castle", "ratchet", "karakuri_soldier", 6, true),
			new Lair("groseade", "byrnndi_world", "world_pirate", 6, false),
			new Lair("clockwork_island", "bear_king", "trump_pirate", 7, false),
			new Lair("delta_island", "buena_festa", "festival_pirate", 7, false),
			new Lair("asuka_island", "saga", "seven_star_swordsman", 7, false),
			new Lair("crown_island", "count_butler", "butler_henchman", 6, false));

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("lairs")) {
			return;
		}
		try {
			run(context);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private void run(ClientGameTestContext context) throws Exception {
		List<Lair> picked = LAIRS.stream().filter(l -> TestFilter.picks(l.name, l.boss)).toList();
		try (TestSingleplayerContext sp = context.worldBuilder().adjustSettings(LairsClientTest::defaultWorld).create()) {
			sp.getConnection().waitForChunksRender();
			cmd(sp, "race set @p human");
			cmd(sp, "gamemode spectator @a");
			cmd(sp, "time set noon");
			cmd(sp, "weather clear");
			context.waitTicks(10);
			context.setScreen(() -> null);
			context.runOnClient(client -> {
				try {
					Field visible = Class.forName("com.onepiecemod.questtree.client.QuestTreePanel").getDeclaredField("visible");
					visible.setAccessible(true);
					visible.set(null, false);
				} catch (ReflectiveOperationException e) {
					LOG.info("LT could not hide quest panel: {}", e.toString());
				}
				try {
					Field hidden = client.gui.hud.getClass().getDeclaredField("isHidden");
					hidden.setAccessible(true);
					hidden.set(client.gui.hud, true);
				} catch (ReflectiveOperationException e) {
					LOG.info("LT could not hide the HUD: {}", e.toString());
				}
			});

			server(sp, LairsClientTest::checkPalettes);
			Map<String, BlockPos> located = new LinkedHashMap<>();
			server(sp, s -> {
				for (Lair lair : picked) {
					BlockPos p = locate(s, lair);
					if (p != null) {
						located.put(lair.name, p);
					}
				}
			});
			// The lairs the world made itself: everything is checked here, and these are the screenshots.
			for (Lair lair : picked) {
				if (located.containsKey(lair.name)) {
					naturalTest(context, sp, lair, located.get(lair.name));
					resetTest(context, sp, lair, located.get(lair.name));
				}
			}
			// /place structure, somewhere else in a biome each spawns in. The chunks there are already decorated (trees,
			// no terrain smoothing), so this only checks that the lair places and sets itself up, not how it looks.
			List<BlockPos> used = new ArrayList<>(located.values());
			for (int i = 0; i < picked.size(); i++) {
				placeTest(context, sp, picked.get(i), i, used);
			}
			if (TestFilter.picks("buggy_big_top", "buggy")) {
				mainModResetTest(context, sp, "buggy_big_top", "buggy");
			}
			LOG.info("LT DONE, {} failures", FAILURES.size());
		}
		if (!FAILURES.isEmpty()) {
			throw new AssertionError("One Piece Bosses lair test failures:\n" + String.join("\n", FAILURES));
		}
	}

	/** Every block id in each lair's .nbt palette is a real block: a bad id would silently place as air. */
	private static void checkPalettes(MinecraftServer s) {
		for (Lair lair : LAIRS) {
			String path = "data/opbosses/structure/" + lair.name + ".nbt";
			try (var in = LairsClientTest.class.getClassLoader().getResourceAsStream(path)) {
				if (in == null) {
					check(false, lair.name + ": no " + path);
					continue;
				}
				var nbt = net.minecraft.nbt.NbtIo.readCompressed(in, net.minecraft.nbt.NbtAccounter.unlimitedHeap());
				var palette = nbt.getListOrEmpty("palette");
				int bad = 0;
				for (int i = 0; i < palette.size(); i++) {
					var entry = palette.getCompoundOrEmpty(i);
					String id = entry.getStringOr("Name", entry.getStringOr("id", ""));
					Identifier key = Identifier.tryParse(id);
					if (key == null || !BuiltInRegistries.BLOCK.containsKey(key)) {
						bad++;
						check(false, lair.name + ": unknown block " + id + " in the structure");
					}
				}
				LOG.info("LT {} palette {} block states, {} unknown, {} blocks", lair.name, palette.size(), bad, nbt.getListOrEmpty("blocks").size());
			} catch (java.io.IOException e) {
				check(false, lair.name + ": can't read " + path + ": " + e);
			}
		}
	}

	/** A normal world (the test default is superflat with no structures), so /locate means something. */
	private static void defaultWorld(WorldCreationUiState creator) {
		creator.setWorldType(new WorldCreationUiState.WorldTypeEntry(
				creator.getSettings().worldgenLoadContext().lookupOrThrow(Registries.WORLD_PRESET).getOrThrow(WorldPresets.NORMAL)));
		creator.setGenerateStructures(true);
		creator.setAllowCommands(true);
		creator.setSeed("rogue-lairs");
	}

	private static void check(boolean ok, String what) {
		if (!ok) {
			LOG.info("LT FAIL {}", what);
			FAILURES.add(what);
		}
	}

	private static Holder.Reference<Structure> structure(MinecraftServer s, String name) {
		return s.registryAccess().lookupOrThrow(Registries.STRUCTURE)
				.getOrThrow(ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath("opbosses", name)));
	}

	/** What /locate structure does, from the world's centre. */
	private static BlockPos locate(MinecraftServer s, Lair lair) {
		ServerLevel level = s.overworld();
		BlockPos from = new BlockPos(0, 64, 0);
		long start = System.currentTimeMillis();
		Pair<BlockPos, Holder<Structure>> found = level.getChunkSource().getGenerator()
				.findNearestMapStructure(level, HolderSet.direct(structure(s, lair.name)), from, 100, false);
		long ms = System.currentTimeMillis() - start;
		if (found == null) {
			check(false, lair.name + ": /locate found none within 100 regions");
			return null;
		}
		BlockPos p = found.getFirst();
		LOG.info("LT LOCATE {} at {} {} distance {} ({} ms)", lair.name, p.getX(), p.getZ(),
				(int) Math.sqrt(p.distSqr(new BlockPos(0, p.getY(), 0))), ms);
		return p;
	}

	/**
	 * The middle of the lair /locate found. /locate gives its start chunk, but the ground check (LairSites) may have slid
	 * the lair up to 48 blocks from there, so the test goes to the lair's own bounds instead.
	 */
	private static BlockPos centre(MinecraftServer s, Lair lair, BlockPos pos) {
		var start = s.overworld().getChunk(pos).getStartForStructure(structure(s, lair.name).value());
		if (start == null || !start.isValid()) return pos;
		var bb = start.getBoundingBox();
		return new BlockPos((bb.minX() + bb.maxX()) / 2, pos.getY(), (bb.minZ() + bb.maxZ()) / 2);
	}

	private void naturalTest(ClientGameTestContext context, TestSingleplayerContext sp, Lair lair, BlockPos pos) throws Exception {
		BlockPos[] mid = new BlockPos[1];
		server(sp, s -> mid[0] = centre(s, lair, pos));
		server(sp, s -> player(s).teleportTo(s.overworld(), mid[0].getX() + 0.5, 160, mid[0].getZ() + 0.5, Set.of(), 0f, 60f, true));
		context.waitTicks(60);
		sp.getConnection().waitForChunksRender();
		context.waitTicks(20);
		List<double[]> cameras = new ArrayList<>();
		server(sp, s -> inspect(s, lair, pos, "natural", cameras));
		String[] shots = {"", "_ground", "_inside", "_north"};
		for (int i = 0; i < cameras.size(); i++) {
			double[] c = cameras.get(i);
			server(sp, s -> player(s).teleportTo(s.overworld(), c[0], c[1], c[2], Set.of(), (float) c[3], (float) c[4], true));
			context.waitTicks(30);
			sp.getConnection().waitForChunksRender();
			context.runOnClient(client -> client.gui.hud.getChat().clearMessages(true));
			context.waitTicks(20);
			context.takeScreenshot("lair_" + lair.name + shots[i]);
		}
	}

	/**
	 * The Lair Restoration Charter: with the boss beaten, the chest emptied and a hole knocked in the lair, using it
	 * rebuilds the lair, brings the boss back and puts a fresh locked chest in place. It refuses while the boss lives.
	 */
	private void resetTest(ClientGameTestContext context, TestSingleplayerContext sp, Lair lair, BlockPos pos) throws Exception {
		String name = lair.name + " (reset)";
		BlockPos[] chestAt = new BlockPos[1];
		BlockPos[] hole = new BlockPos[1];
		net.minecraft.world.level.block.state.BlockState[] holeWas = new net.minecraft.world.level.block.state.BlockState[1];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			BlockPos mid = centre(s, lair, pos);
			for (int cx = (mid.getX() >> 4) - 5; cx <= (mid.getX() >> 4) + 5 && chestAt[0] == null; cx++) {
				for (int cz = (mid.getZ() >> 4) - 5; cz <= (mid.getZ() >> 4) + 5 && chestAt[0] == null; cz++) {
					for (BlockPos bp : level.getChunk(cx, cz).getBlockEntitiesPos()) {
						if (level.getBlockEntity(bp) instanceof LairChestBlockEntity && level.getBlockState(bp).is(LairChests.BLOCKS.get(lair.name))) {
							chestAt[0] = bp.immutable();
						}
					}
				}
			}
			if (chestAt[0] == null) {
				check(false, name + ": no lair chest to reset around");
				return;
			}
			p.teleportTo(level, chestAt[0].getX() + 0.5, chestAt[0].getY() + 1, chestAt[0].getZ() + 0.5, Set.of(), 0f, 0f, true);
			var refused = LairReset.reset(level, p);
			LOG.info("LT {} with the boss alive: {}", name, refused);
			check(refused == LairReset.Result.BOSS_STILL_HERE, name + ": rebuilt with the boss still alive (" + refused + ")");

			// Beat the boss, loot the chest and knock a block out of the floor under it.
			for (RogueBossEntity b : level.getEntitiesOfClass(RogueBossEntity.class, new AABB(chestAt[0]).inflate(150), e -> e.getCharacterId().equals(lair.boss))) {
				b.discard();
			}
			LairChestBlockEntity chest = (LairChestBlockEntity) level.getBlockEntity(chestAt[0]);
			chest.unpackLootTable(p);
			chest.clearContent();
			hole[0] = chestAt[0].below();
			holeWas[0] = level.getBlockState(hole[0]);
			level.setBlockAndUpdate(hole[0], net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());

			var done = LairReset.reset(level, p);
			LOG.info("LT {} after the win: {}", name, done);
			check(done == LairReset.Result.DONE, name + ": the charter didn't rebuild the lair (" + done + ")");
		});
		context.waitTicks(40);
		server(sp, s -> {
			if (chestAt[0] == null) {
				return;
			}
			ServerLevel level = s.overworld();
			boolean bossBack = !level.getEntitiesOfClass(RogueBossEntity.class, new AABB(chestAt[0]).inflate(150),
					e -> e.isAlive() && e.getCharacterId().equals(lair.boss)).isEmpty();
			boolean chestBack = level.getBlockEntity(chestAt[0]) instanceof LairChestBlockEntity c && c.getLootTable() != null;
			boolean floorBack = level.getBlockState(hole[0]).equals(holeWas[0]);
			LOG.info("LT {} rebuilt: boss back={} fresh chest={} floor back={} ({})", name, bossBack, chestBack, floorBack, level.getBlockState(hole[0]));
			check(bossBack, name + ": " + lair.boss + " didn't come back");
			check(chestBack, name + ": the chest wasn't refilled");
			check(floorBack, name + ": the broken block wasn't rebuilt");
		});
	}

	/**
	 * The charter on one of the main mod's boss structures, as the world made it (/place only builds a main-mod
	 * structure's start tile, so its boss, saved in another tile, never appears). Then the same as resetTest without the
	 * chest: refused while the boss lives; with the boss beaten and a block broken, the boss, the block and the same
	 * number of crew come back.
	 */
	private void mainModResetTest(ClientGameTestContext context, TestSingleplayerContext sp, String structure, String boss) throws Exception {
		String name = structure + " (main mod reset)";
		BlockPos[] located = new BlockPos[1];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			Holder<Structure> st = level.registryAccess().lookupOrThrow(Registries.STRUCTURE)
					.getOrThrow(net.minecraft.resources.ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath("onepiece", structure)));
			Pair<BlockPos, Holder<Structure>> found = level.getChunkSource().getGenerator()
					.findNearestMapStructure(level, HolderSet.direct(st), new BlockPos(0, 64, 0), 100, false);
			located[0] = found == null ? null : found.getFirst();
			LOG.info("LT {} located at {}", name, located[0]);
		});
		if (located[0] == null) {
			check(false, name + ": /locate found none");
			return;
		}
		int x = located[0].getX(), z = located[0].getZ();
		server(sp, s -> player(s).teleportTo(s.overworld(), x + 0.5, 200, z + 0.5, Set.of(), 0f, 60f, true));
		context.waitTicks(40);
		// The tiles spread about 100 blocks either side of the start; 15x15 chunks stays under forceload's 256.
		cmd(sp, "forceload add " + (x - 112) + " " + (z - 112) + " " + (x + 112) + " " + (z + 112));
		context.waitTicks(200);
		BlockPos[] hole = new BlockPos[1];
		net.minecraft.world.level.block.state.BlockState[] holeWas = new net.minecraft.world.level.block.state.BlockState[1];
		int[] crewBefore = new int[1];
		AABB search = new AABB(x, -64, z, x, 320, z).inflate(160, 0, 160);
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			var found = level.getEntitiesOfClass(com.onepiecemod.character.CharacterEntity.class, search, e -> e.isAlive() && e.getCharacterId().equals(boss));
			LOG.info("LT {} placed: {} {} found", name, found.size(), boss);
			if (found.isEmpty()) {
				check(false, name + ": no " + boss + " after /place");
				return;
			}
			var b = found.get(0);
			BlockPos at = b.blockPosition();
			p.teleportTo(level, at.getX() + 0.5, at.getY(), at.getZ() + 0.5, Set.of(), 0f, 0f, true);
			crewBefore[0] = crew(level, search);
			var refused = LairReset.reset(level, p);
			LOG.info("LT {} with the boss alive: {} (crew {})", name, refused, crewBefore[0]);
			check(refused == LairReset.Result.BOSS_STILL_HERE, name + ": rebuilt with " + boss + " still alive (" + refused + ")");

			b.discard();
			hole[0] = at.below();
			holeWas[0] = level.getBlockState(hole[0]);
			level.setBlockAndUpdate(hole[0], net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());
			var done = LairReset.reset(level, p);
			LOG.info("LT {} after the win: {}", name, done);
			check(done == LairReset.Result.DONE, name + ": the charter didn't rebuild it (" + done + ")");
		});
		context.waitTicks(40);
		server(sp, s -> {
			if (hole[0] == null) {
				return;
			}
			ServerLevel level = s.overworld();
			int bosses = level.getEntitiesOfClass(com.onepiecemod.character.CharacterEntity.class, search, e -> e.isAlive() && e.getCharacterId().equals(boss)).size();
			int crewAfter = crew(level, search);
			boolean floorBack = level.getBlockState(hole[0]).equals(holeWas[0]);
			LOG.info("LT {} rebuilt: {} x{} crew {} -> {} floor back={}", name, boss, bosses, crewBefore[0], crewAfter, floorBack);
			check(bosses == 1, name + ": " + bosses + " " + boss + " after the rebuild, want 1");
			check(crewAfter == crewBefore[0], name + ": crew went from " + crewBefore[0] + " to " + crewAfter);
			check(floorBack, name + ": the broken block wasn't rebuilt");
		});
		cmd(sp, "forceload remove all");
	}

	/** The main mod's kept pirates and Marines (a structure's crew) in an area. */
	private static int crew(ServerLevel level, AABB area) {
		return level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class, area, e -> e.isAlive() && e.isPersistenceRequired()
				&& !(e instanceof com.onepiecemod.character.CharacterEntity)
				&& net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getNamespace().equals("onepiece")).size();
	}

	/** A camera at (x, y, z) looking at (tx, ty, tz), as {x, y, z, yaw, pitch}. */
	private static double[] look(double x, double y, double z, double tx, double ty, double tz) {
		double yaw = Math.toDegrees(Math.atan2(-(tx - x), tz - z));
		double pitch = Math.toDegrees(Math.atan2(y - ty, Math.hypot(tx - x, tz - z)));
		return new double[] {x, y, z, yaw, pitch};
	}

	private void placeTest(ClientGameTestContext context, TestSingleplayerContext sp, Lair lair, int i, List<BlockPos> used) throws Exception {
		BlockPos[] target = new BlockPos[1];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			TagKey<Biome> tag = TagKey.create(Registries.BIOME, Identifier.fromNamespaceAndPath("opbosses", "has_structure/" + lair.name));
			// Start each search somewhere else, and skip spots within 200 blocks of another lair.
			for (int tries = 0; tries < 8 && target[0] == null; tries++) {
				BlockPos from = new BlockPos(-600 * i - 300 * tries, level.getSeaLevel(), 400 * tries - 1500);
				Pair<BlockPos, Holder<Biome>> biome = level.findClosestBiome3d(h -> h.is(tag), from, 4000, 32, 64);
				if (biome == null) {
					continue;
				}
				BlockPos p = biome.getFirst();
				if (used.stream().noneMatch(u -> u.distSqr(p) < 200 * 200)) {
					target[0] = p;
					LOG.info("LT {} placing in {} at {} {}", lair.name, biome.getSecond().getRegisteredName(), p.getX(), p.getZ());
				}
			}
		});
		if (target[0] == null) {
			check(false, lair.name + ": no biome it spawns in within 4000 blocks");
			return;
		}
		BlockPos pos = target[0];
		used.add(pos);
		// /place needs the chunks loaded, so go there first.
		server(sp, s -> player(s).teleportTo(s.overworld(), pos.getX() + 0.5, 160, pos.getZ() + 0.5, Set.of(), 0f, 60f, true));
		context.waitTicks(40);
		sp.getConnection().waitForChunksRender();
		boolean[] placed = new boolean[1];
		// The film lairs are up to 120 blocks across, wider than the view distance: load all of it for /place.
		int cx = pos.getX() >> 4, cz = pos.getZ() >> 4, r = 9;
		server(sp, s -> {
			for (int x = cx - r; x <= cx + r; x++) {
				for (int z = cz - r; z <= cz + r; z++) {
					s.overworld().setChunkForced(x, z, true);
				}
			}
		});
		context.waitTicks(40);
		server(sp, s -> {
			try {
				PlaceCommand.placeStructure(s.createCommandSourceStack().withSuppressedOutput(), structure(s, lair.name), pos);
				placed[0] = true;
				LOG.info("LT {} placed ok", lair.name);
			} catch (Exception e) {
				check(false, lair.name + ": /place structure failed: " + e.getMessage());
			}
		});
		if (placed[0]) {
			context.waitTicks(40);
			server(sp, s -> inspect(s, lair, pos, "placed", null));
		}
		server(sp, s -> {
			for (int x = cx - r; x <= cx + r; x++) {
				for (int z = cz - r; z <= cz + r; z++) {
					s.overworld().setChunkForced(x, z, false);
				}
			}
		});
	}

	/** No structure of the main mod's (nor a village or outpost) overlaps the lair or comes within 16 blocks of it (LairNeighbours). */
	private static void neighbours(ServerLevel level, String name, net.minecraft.world.level.levelgen.structure.BoundingBox bb) {
		var near = bb.inflatedBy(16);
		var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
		Set<String> seen = new java.util.HashSet<>();
		for (int cx = near.minX() >> 4; cx <= near.maxX() >> 4; cx++) {
			for (int cz = near.minZ() >> 4; cz <= near.maxZ() >> 4; cz++) {
				for (var start : level.structureManager().startsForStructure(cx, cz, st -> {
					Identifier id = registry.getKey(st);
					return id != null && (id.getNamespace().equals("onepiece") || id.getPath().startsWith("village_") || id.getPath().equals("pillager_outpost"));
				})) {
					String other = String.valueOf(registry.getKey(start.getStructure()));
					var obb = start.getBoundingBox();
					if (!seen.add(other + obb)) continue;
					LOG.info("LT {} neighbour {} at {} {} .. {} {}", name, other, obb.minX(), obb.minZ(), obb.maxX(), obb.maxZ());
					check(!obb.intersects(near), name + ": overlaps " + other + " (" + obb + ")");
				}
			}
		}
	}

	/**
	 * Checks the boss, crew and chest of the lair near pos. A natural lair (camera != null) is also checked for anyone
	 * stuck in a block and for its height above the sea, and the camera is set to look down at it.
	 */
	private static void inspect(MinecraftServer s, Lair lair, BlockPos pos, String how, List<double[]> camera) {
		ServerLevel level = s.overworld();
		String name = lair.name + " (" + how + ")";
		// The lair's own bounds: the /locate spot is just its start chunk, and the compounds are up to 100 blocks across.
		var start = level.getChunk(pos).getStartForStructure(structure(s, lair.name).value());
		var bb = start != null && start.isValid() ? start.getBoundingBox() : new net.minecraft.world.level.levelgen.structure.BoundingBox(pos).inflatedBy(72);
		LOG.info("LT {} bounds {} {} {} .. {} {} {} ({} x {} x {}) start found={}", name, bb.minX(), bb.minY(), bb.minZ(), bb.maxX(), bb.maxY(),
				bb.maxZ(), bb.getXSpan(), bb.getYSpan(), bb.getZSpan(), start != null && start.isValid());
		AABB area = AABB.of(bb).inflate(16);
		RogueBossEntity boss = level.getEntitiesOfClass(RogueBossEntity.class, area, e -> e.isAlive() && e.getCharacterId().equals(lair.boss)).stream()
				.min(Comparator.comparingDouble(e -> e.distanceToSqr(pos.getX(), e.getY(), pos.getZ()))).orElse(null);
		if (boss == null) {
			for (RogueBossEntity e : level.getEntitiesOfClass(RogueBossEntity.class, area.inflate(200), e -> true)) {
				LOG.info("LT {} other boss {} alive={} at {}", name, e.getCharacterId(), e.isAlive(), e.blockPosition());
			}
			check(false, name + ": no " + lair.boss + " nearby");
			return;
		}
		boolean setUp = !boss.entityTags().contains(WorldFeature.NEW_CHARACTER_TAG);
		int sea = level.getSeaLevel();
		String inBlock = blockedBy(level, boss);
		LOG.info("LT {} boss id={} name='{}' boss={} setUp={} health={}/{} at {} (sea level {}, {} above it) stuckIn={}", name,
				boss.getCharacterId(), boss.getData() == null ? "?" : boss.getData().name, boss.isBoss(), setUp, boss.getHealth(),
				boss.getMaxHealth(), boss.blockPosition(), sea, boss.getBlockY() - sea, inBlock);
		check(setUp && boss.isBoss(), name + ": the boss wasn't set up (setUp=" + setUp + ", boss=" + boss.isBoss() + ")");
		if (camera != null) {
			neighbours(level, name, bb);
			check(inBlock == null, name + ": the boss is stuck in " + inBlock);
			if (lair.sea) {
				check(boss.getBlockY() > sea && boss.getBlockY() < sea + 6, name + ": the arena is " + (boss.getBlockY() - sea) + " blocks above the sea");
			}
		}

		// Tall enough for Merveille, whose palace guards are on the floating island 36 blocks over the arena.
		List<HumanNpc> crew = level.getEntitiesOfClass(HumanNpc.class, boss.getBoundingBox().inflate(48, 44, 48), Entity::isAlive);
		int kitted = 0;
		for (HumanNpc npc : crew) {
			boolean leftover = npc.entityTags().stream().anyMatch(t -> t.equals(GuardKit.GUARD_TAG) || t.startsWith(GuardKit.KIT_TAG_PREFIX));
			String stuck = blockedBy(level, npc);
			LOG.info("LT {} crew {} kit={} name='{}' hand={} tagsLeft={} at {} stuckIn={}", name, BuiltInRegistries.ENTITY_TYPE.getKey(npc.getType()),
					npc.getKitId(), npc.getName().getString(), npc.getMainHandItem(), leftover, npc.blockPosition(), stuck);
			if (npc.getKitId().equals(lair.kit) && !leftover) {
				kitted++;
				if (camera != null) {
					check(stuck == null, name + ": crew " + npc.getName().getString() + " is stuck in " + stuck);
				}
			}
		}
		check(kitted == lair.crew, name + ": " + kitted + " crew with kit " + lair.kit + ", want " + lair.crew);

		// Only this mod's chests: a lair may sit on top of a dungeon or next to a shipwreck.
		int chests = 0;
		BlockPos chestAt = null;
		for (int cx = (boss.getBlockX() >> 4) - 3; cx <= (boss.getBlockX() >> 4) + 3; cx++) {
			for (int cz = (boss.getBlockZ() >> 4) - 3; cz <= (boss.getBlockZ() >> 4) + 3; cz++) {
				for (BlockPos bp : level.getChunk(cx, cz).getBlockEntitiesPos()) {
					BlockEntity be = level.getBlockEntity(bp);
					if (!(be instanceof LairChestBlockEntity chest) || chest.getLootTable() == null
							|| !chest.getLootTable().identifier().getNamespace().equals("opbosses")) {
						continue;
					}
					String table = chest.getLootTable().identifier().toString();
					check(table.equals("opbosses:chests/" + lair.name), name + ": chest at " + bp + " has loot table " + table);
					check(level.getBlockState(bp).is(LairChests.BLOCKS.get(lair.name)),
							name + ": the chest at " + bp + " is " + level.getBlockState(bp) + ", not the lair's own chest");
					chest.unpackLootTable(player(s));
					List<String> items = new ArrayList<>();
					boolean poster = false;
					for (int slot = 0; slot < chest.getContainerSize(); slot++) {
						ItemStack stack = chest.getItem(slot);
						if (!stack.isEmpty()) {
							items.add(stack.getCount() + " " + stack.getItem());
							poster |= stack.is(BossItems.RUMORS.get(lair.boss));
						}
					}
					chests++;
					chestAt = bp.immutable();
					LOG.info("LT {} chest {} at {} ({} above the boss) items={}", name, table, bp, bp.getY() - boss.getBlockY(), items);
					check(!items.isEmpty(), name + ": the chest is empty");
					check(poster, name + ": no rumor poster for " + lair.boss + " in the chest");
					// Locked to the boss's key: shut without it, open with it in hand. Spectators open every lock, so check in survival.
					ServerPlayer p = player(s);
					p.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
					ItemStack held = p.getMainHandItem().copy();
					p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
					boolean openWithout = chest.canOpen(p);
					p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(BossItems.KEYS.get(lair.boss)));
					boolean openWithKey = chest.canOpen(p);
					p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(BossItems.KEYS.get(lair.name.equals("merveille") ? "uta_diva" : "shiki_golden_lion")));
					boolean openWithOther = chest.canOpen(p);
					p.setItemInHand(InteractionHand.MAIN_HAND, held);
					p.setGameMode(net.minecraft.world.level.GameType.SPECTATOR);
					LOG.info("LT {} lock: opens without key={} with key={} with another boss's key={}", name, openWithout, openWithKey, openWithOther);
					check(!openWithout, name + ": the chest opens without a key");
					check(openWithKey, name + ": the chest doesn't open with " + lair.boss + "'s key");
					check(!openWithOther, name + ": the chest opens with another boss's key");
				}
			}
		}
		check(chests == 1, name + ": " + chests + " loot chests");

		if (camera != null) {
			double cx = (bb.minX() + bb.maxX() + 1) / 2.0, cz = (bb.minZ() + bb.maxZ() + 1) / 2.0;
			double span = Math.max(bb.getXSpan(), bb.getZSpan());
			double ty = boss.getY();
			// 1. overview: high up from the south-east, far enough out for the whole compound.
			double d = span * 0.6;
			camera.add(look(cx + d * 0.55, ty + d * 0.8, cz + d * 0.55, cx, ty, cz));
			// 2. ground level, 14 blocks from the boss on the first side with a clear view of the arena.
			double[] ground = null;
			for (int a = 0; a < 16 && ground == null; a++) {
				double ang = Math.toRadians(a * 22.5), gx = boss.getX() + Math.sin(ang) * 14, gz = boss.getZ() + Math.cos(ang) * 14, gy = boss.getY() + 1.5;
				BlockPos gp = BlockPos.containing(gx, gy, gz);
				if (!level.getBlockState(gp).getCollisionShape(level, gp).isEmpty() || !level.getBlockState(gp.above()).getCollisionShape(level, gp.above()).isEmpty()) {
					continue;
				}
				var eye = new net.minecraft.world.phys.Vec3(gx, gy + 1.62, gz);
				var hit = level.clip(new net.minecraft.world.level.ClipContext(eye, boss.getEyePosition(), net.minecraft.world.level.ClipContext.Block.VISUAL,
						net.minecraft.world.level.ClipContext.Fluid.NONE, net.minecraft.world.phys.shapes.CollisionContext.empty()));
				if (hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS) {
					ground = look(gx, gy, gz, boss.getX(), boss.getY(), boss.getZ());
				}
			}
			camera.add(ground != null ? ground : look(boss.getX() + 4, boss.getY() + 2.5, boss.getZ() + 14, boss.getX(), boss.getY() + 1.5, boss.getZ()));
			// 3. inside the boss's quarters: the side of the chest with the most room, backed off up to 6 blocks, looking at it.
			if (chestAt != null) {
				BlockPos best = null;
				int bestRoom = -1;
				for (var dir : net.minecraft.core.Direction.Plane.HORIZONTAL) {
					BlockPos at = chestAt.relative(dir);
					if (!passable(level, at)) {
						continue;
					}
					int room = 0;
					while (room < 6 && passable(level, at.relative(dir))) {
						at = at.relative(dir);
						room++;
					}
					if (room > bestRoom) {
						bestRoom = room;
						best = at;
					}
				}
				if (best != null) {
					int light = level.getBrightness(net.minecraft.world.level.LightLayer.BLOCK, chestAt.above());
					int sky = level.getBrightness(net.minecraft.world.level.LightLayer.SKY, chestAt.above());
					LOG.info("LT {} quarters: block light {} sky light {} at the chest, camera {} blocks back", name, light, sky, bestRoom + 1);
					camera.add(look(best.getX() + 0.5, best.getY() + 0.1, best.getZ() + 0.5, chestAt.getX() + 0.5, chestAt.getY() - 1.4, chestAt.getZ() + 0.5));
				}
			}
			// 4. overview from the north-west, the other side.
			camera.add(look(cx - d * 0.55, ty + d * 0.6, cz - d * 0.55, cx, ty, cz));
			boss.setNoAi(true);
			for (HumanNpc npc : crew) {
				npc.setNoAi(true);
			}
		}
	}

	/** A spot a player could stand in: low or no block at the feet, nothing at the head. */
	private static boolean passable(ServerLevel level, BlockPos p) {
		var feet = level.getBlockState(p).getCollisionShape(level, p);
		return (feet.isEmpty() || feet.max(net.minecraft.core.Direction.Axis.Y) <= 0.5) && level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty();
	}

	/** The first solid block inside the entity's box, or null if it's standing free. */
	private static String blockedBy(ServerLevel level, Entity e) {
		AABB box = e.getBoundingBox().deflate(0.05);
		for (BlockPos p : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ), BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
			var state = level.getBlockState(p);
			if (!state.getCollisionShape(level, p).isEmpty() && state.getCollisionShape(level, p).bounds().move(p).intersects(box)) {
				return state.getBlock() + " at " + p.immutable();
			}
		}
		return null;
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
