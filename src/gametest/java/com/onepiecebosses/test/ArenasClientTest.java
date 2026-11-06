package com.onepiecebosses.test;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.onepiecebosses.boss.ArenaData;
import com.onepiecebosses.boss.ArenaEvents;
import com.onepiecebosses.boss.ArenaMusic;
import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.boss.RogueBosses;
import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.character.BossStrikes;

/**
 * In-world check of every boss's arena (arenas.json): its lair theme is what the main mod's music player plays, its
 * boss bar has the lair's colour and fog, phase 3 brings the last crew wave, every hazard lands without an exception,
 * a collapsed floor opens and comes back when the boss falls. Results are "AT" lines in the log.
 *
 *     gradlew runClientGameTest -Dopbosses.tests=arenas [-Dopbosses.only=uta_diva,doctor_kreuz]
 */
public class ArenasClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("arenas-test");
	private static final double PX = 0.5, PY = 100, PZ = 0.5;
	/** The arena's floor: five blocks of stone, so a collapse has something to cave into. */
	private static final int FLOOR_TOP = 99, FLOOR_BOTTOM = 95, HALF = 14;
	private static final List<String> FAILURES = new java.util.concurrent.CopyOnWriteArrayList<>();

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("arenas")) {
			return;
		}
		try {
			run(context);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private void run(ClientGameTestContext context) throws Exception {
		try (TestSingleplayerContext sp = context.worldBuilder().create()) {
			sp.getConnection().waitForChunksRender();
			cmd(sp, "gamemode survival @a");
			cmd(sp, "time set day");
			cmd(sp, "weather clear");
			cmd(sp, "gamerule spawn_mobs false");
			cmd(sp, "gamerule advance_time false");
			context.waitTicks(10);
			context.setScreen(() -> null);
			server(sp, s -> checkData());
			for (String id : RogueData.all().keySet()) {
				if (TestFilter.picks(id)) {
					arenaTest(context, sp, id);
				}
			}
			LOG.info("AT DONE, {} failures", FAILURES.size());
		}
		if (!FAILURES.isEmpty()) {
			throw new AssertionError("One Piece Bosses arena test failures:\n" + String.join("\n", FAILURES));
		}
	}

	private static void check(boolean ok, String what) {
		if (!ok) {
			LOG.info("AT FAIL {}", what);
			FAILURES.add(what);
		}
	}

	/** Every boss has an arena, and everything an arena names exists. */
	private static void checkData() {
		for (RogueData boss : RogueData.all().values()) {
			check(ArenaData.has(boss.id), boss.id + ": no entry in arenas.json");
			ArenaData arena = ArenaData.of(boss.id);
			if (!arena.music.isEmpty()) {
				check(ArenaMusic.THEMES.containsKey(arena.music), boss.id + ": theme " + arena.music + " isn't registered");
				check(ArenasClientTest.class.getResource("/assets/opbosses/sounds/music/" + arena.music + ".ogg") != null,
						boss.id + ": music/" + arena.music + ".ogg is missing");
			}
			check(arena.bar.isEmpty() || ArenaEvents.color(arena.bar) != null, boss.id + ": unknown bar colour " + arena.bar);
			for (ArenaData.Hazard hazard : arena.hazards) {
				check(Set.of("collapse", "debris", "geyser", "cloud", "lightning", "tide", "fog").contains(hazard.type),
						boss.id + ": unknown hazard " + hazard.type);
				if (!hazard.particle.isEmpty()) {
					check(BuiltInRegistries.PARTICLE_TYPE.getValue(Identifier.parse(hazard.particle)) instanceof net.minecraft.core.particles.SimpleParticleType,
							boss.id + ": particle " + hazard.particle + " isn't a plain particle");
				}
				if (!hazard.effect.isEmpty()) {
					check(BuiltInRegistries.MOB_EFFECT.get(Identifier.parse(hazard.effect)).isPresent(), boss.id + ": effect " + hazard.effect + " is missing");
				}
				if (hazard.type.equals("debris")) {
					check(BuiltInRegistries.BLOCK.getValue(Identifier.parse(hazard.block)) != Blocks.AIR, boss.id + ": block " + hazard.block + " is missing");
				}
			}
		}
	}

	private void arenaTest(ClientGameTestContext context, TestSingleplayerContext sp, String id) throws Exception {
		ArenaData arena = ArenaData.of(id);
		// Twenty boss wins in a row on one island make the main mod send a Buster Call, whose shells blow craters in
		// the arena floor and whose Marines join the fight. Wipe the slate before each boss: no bounty, no trouble.
		cmd(sp, "worldevent bustercall stop");
		cmd(sp, "execute as @p run worldevent trouble 0");
		server(sp, s -> com.onepiecemod.bounty.Bounty.set(player(s), 0));
		server(sp, s -> {
			clearMobs(s);
			arena(s.overworld());
			ServerPlayer p = player(s);
			p.teleportTo(s.overworld(), PX, PY, PZ, Set.of(), -90f, 10f, true);
			p.clearFire();
			p.removeAllEffects();
			p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 600, 4, false, false));
			p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 20 * 600, 4, false, false));
			p.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 20 * 600, 0, false, false));
			p.setHealth(p.getMaxHealth());
			RogueBossEntity boss = RogueBosses.ROGUE_BOSS.create(s.overworld(), EntitySpawnReason.COMMAND);
			boss.setPos(PX + 8, PY, PZ);
			boss.setCharacter(id, true);
			s.overworld().addFreshEntity(boss);
			boss.setTarget(p);
		});
		context.waitTicks(60);

		// The lair theme: the main mod's music player should be playing it.
		Holder<SoundEvent> want = ArenaMusic.of(id);
		Object[] playing = new Object[1];
		context.runOnClient(client -> {
			try {
				Field current = Class.forName("com.onepiecemod.sound.client.MusicDirector").getDeclaredField("currentSong");
				current.setAccessible(true);
				playing[0] = current.get(null);
			} catch (ReflectiveOperationException e) {
				playing[0] = e;
			}
		});
		LOG.info("AT {} music playing={} want={}", id, playing[0], want == null ? "main mod's" : want.value().location());
		if (want != null) {
			check(playing[0] == want, id + ": the music player is on " + playing[0] + ", not the lair theme " + arena.music);
		}

		// Phase 2: the bar's look, and the hazards.
		int[] wave = new int[2];
		server(sp, s -> {
			RogueBossEntity boss = boss(s);
			if (boss == null) {
				check(false, id + ": the boss is gone");
				return;
			}
			ServerBossEvent bar = OnePieceBridge.bossBar(boss);
			check(bar != null, id + ": can't reach the boss bar");
			if (bar != null) {
				LOG.info("AT {} bar colour={} fog={} dark={}", id, bar.getColor(), bar.shouldCreateWorldFog(), bar.shouldDarkenScreen());
				check(ArenaEvents.color(arena.bar) == null || bar.getColor() == ArenaEvents.color(arena.bar), id + ": bar is " + bar.getColor() + ", not " + arena.bar);
				check(bar.shouldCreateWorldFog() == (arena.fogFrom == 1), id + ": phase 1 fog is " + bar.shouldCreateWorldFog());
			}
			boss.setHealth(boss.getMaxHealth() * 0.6f);
			boss.setTarget(player(s));
		});
		context.waitTicks(30);
		server(sp, s -> {
			RogueBossEntity boss = boss(s);
			if (boss == null) {
				return;
			}
			wave[0] = minions(s);
			// Hold the boss back at its spot, so a collapse isn't skipped for being right under it.
			boss.teleportTo(PX + 8, PY, PZ);
			boss.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 10, false, false));
			// Set every hazard off once, aimed at the player.
			for (ArenaData.Hazard hazard : arena.hazards) {
				try {
					boss.arena().start(s.overworld(), hazard, player(s));
				} catch (Exception e) {
					LOG.info("AT {} hazard {} threw", id, hazard.type, e);
					check(false, id + ": hazard " + hazard.type + " threw " + e);
				}
			}
		});
		context.waitTicks(30);
		context.takeScreenshot("arena_" + id + "_warning");
		context.waitTicks(25);
		context.takeScreenshot("arena_" + id + "_hazards");
		server(sp, s -> {
			RogueBossEntity boss = boss(s);
			if (boss == null) {
				check(false, id + ": the boss is gone after its hazards");
				return;
			}
			for (ArenaData.Hazard hazard : arena.hazards) {
				LOG.info("AT {} hazard {} landed {}x", id, hazard.type, boss.arena().landed(hazard.type));
				check(boss.arena().landed(hazard.type) > 0, id + ": hazard " + hazard.type + " never landed");
				if (hazard.type.equals("collapse")) {
					check(boss.arena().openHoles() > 0, id + ": the floor didn't collapse");
				}
			}
			// Phase 3: the last wave.
			boss.setHealth(boss.getMaxHealth() * 0.3f);
			boss.setTarget(player(s));
		});
		context.waitTicks(30);
		server(sp, s -> {
			RogueBossEntity boss = boss(s);
			wave[1] = minions(s);
			boolean hasCrew = !RogueData.get(id).crew.isEmpty();
			LOG.info("AT {} minions phase2={} phase3={}", id, wave[0], wave[1]);
			if (hasCrew && wave[0] < 5) {
				check(wave[1] > wave[0], id + ": no last wave at phase 3 (" + wave[0] + " -> " + wave[1] + ")");
			}
			if (boss != null) {
				ServerBossEvent bar = OnePieceBridge.bossBar(boss);
				if (bar != null) {
					check(bar.shouldCreateWorldFog() == (arena.fogFrom > 0), id + ": phase 3 fog is " + bar.shouldCreateWorldFog());
					check(bar.shouldDarkenScreen() == (arena.darkenFrom > 0), id + ": phase 3 dark sky is " + bar.shouldDarkenScreen());
				}
				floorReport(s.overworld(), id, "before the win (open holes " + boss.arena().openHoles() + ")");
				// The win: every collapsed block comes back.
				boss.hurtServer(s.overworld(), player(s).damageSources().playerAttack(player(s)), 100_000);
			}
		});
		context.waitTicks(10);
		server(sp, s -> {
			int missing = floorReport(s.overworld(), id, "after the win");
			check(missing == 0, id + ": " + missing + " floor blocks weren't put back after the win");
		});
	}

	/** Counts the arena's top two floor layers that aren't stone any more, and logs what's there instead and where. */
	private static int floorReport(ServerLevel level, String id, String when) {
		java.util.Map<String, Integer> found = new java.util.TreeMap<>();
		int missing = 0, minX = 99, maxX = -99, minZ = 99, maxZ = -99;
		for (int x = -HALF + 1; x < HALF; x++) {
			for (int z = -HALF + 1; z < HALF; z++) {
				for (int y = FLOOR_TOP - 1; y <= FLOOR_TOP; y++) {
					net.minecraft.world.level.block.state.BlockState state = level.getBlockState(new BlockPos(x, y, z));
					if (!state.is(Blocks.STONE)) {
						missing++;
						found.merge(BuiltInRegistries.BLOCK.getKey(state.getBlock()) + "@y" + y, 1, Integer::sum);
						minX = Math.min(minX, x);
						maxX = Math.max(maxX, x);
						minZ = Math.min(minZ, z);
						maxZ = Math.max(maxZ, z);
					}
				}
			}
		}
		LOG.info("AT {} {}: floor blocks missing={} {} x {}..{} z {}..{}", id, when, missing, found, minX, maxX, minZ, maxZ);
		return missing;
	}

	private static RogueBossEntity boss(MinecraftServer s) {
		List<RogueBossEntity> bosses = s.overworld().getEntitiesOfClass(RogueBossEntity.class, area(), Entity::isAlive);
		return bosses.isEmpty() ? null : bosses.get(0);
	}

	/** The boss's crew and beasts on the field. */
	private static int minions(MinecraftServer s) {
		return s.overworld().getEntitiesOfClass(Mob.class, area(), e -> e.isAlive() && e.entityTags().contains(BossStrikes.MINION_TAG)).size();
	}

	private static AABB area() {
		return new AABB(PX, PY, PZ, PX, PY, PZ).inflate(40);
	}

	private static void arena(ServerLevel level) {
		for (int x = -HALF; x <= HALF; x++) {
			for (int z = -HALF; z <= HALF; z++) {
				boolean edge = Math.abs(x) == HALF || Math.abs(z) == HALF;
				for (int y = FLOOR_BOTTOM; y <= FLOOR_TOP; y++) {
					level.setBlockAndUpdate(new BlockPos(x, y, z), Blocks.STONE.defaultBlockState());
				}
				for (int y = FLOOR_TOP + 1; y < FLOOR_TOP + 25; y++) {
					level.setBlockAndUpdate(new BlockPos(x, y, z), edge ? Blocks.BARRIER.defaultBlockState() : Blocks.AIR.defaultBlockState());
				}
			}
		}
	}

	private static void clearMobs(MinecraftServer s) {
		for (Entity e : s.overworld().getEntitiesOfClass(Entity.class, area().inflate(10), e -> !(e instanceof Player))) {
			e.discard();
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
