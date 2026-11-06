package com.onepiecebosses.test;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.phys.AABB;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.onepiecebosses.BossItems;
import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.boss.RogueBosses;
import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.bounty.BountyBoard;
import com.onepiecebosses.bounty.BountyBoardBlock;
import com.onepiecebosses.bounty.Hunt;
import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;

/**
 * In-world check of the Marine Bounty Board on the flat test world: today's five hunts (two rogues, three roaming
 * mob jobs, changing each day), right-clicking a placed board, taking a pirate hunt and counting kills, handing it in
 * for Berries, the once-a-day rule, the range rule, and a rogue hunt from Rumor Poster to payout with its rare drop.
 * Results are "BB" lines in the log; anything wrong says FAIL. Run it alone with
 * `gradlew runClientGameTest -Dopbosses.tests=bounty`.
 */
public class BountyClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("bounty-board-test");
	private static final List<String> FAILURES = new java.util.concurrent.CopyOnWriteArrayList<>();
	private static final BlockPos HOME = new BlockPos(0, -60, 0);
	/** The board, 3 blocks north of the player, facing them. */
	private static final BlockPos BOARD = HOME.offset(0, 0, -3);

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("bounty")) {
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
			cmd(sp, "race set @p human");
			cmd(sp, "gamerule spawn_mobs false");
			cmd(sp, "gamerule advance_time false");
			context.waitTicks(10);
			context.setScreen(() -> null);
			context.runOnClient(client -> {
				try {
					Field visible = Class.forName("com.onepiecemod.questtree.client.QuestTreePanel").getDeclaredField("visible");
					visible.setAccessible(true);
					visible.set(null, false);
				} catch (ReflectiveOperationException e) {
					LOG.info("BB could not hide quest panel: {}", e.toString());
				}
			});
			server(sp, s -> {
				ServerPlayer p = player(s);
				p.teleportTo(s.overworld(), HOME.getX() + 0.5, HOME.getY(), HOME.getZ() + 0.5, Set.of(), 180f, 10f, true);
				p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 1200, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 20 * 1200, 4, false, false));
				s.overworld().setBlockAndUpdate(BOARD, BountyBoard.BLOCK.defaultBlockState().setValue(BountyBoardBlock.FACING, Direction.SOUTH));
				rotationTest(s);
			});
			context.waitTicks(20);

			// Right-click the board like a player would: it reads out today's hunts.
			context.getInput().lookAt(BOARD);
			context.waitTicks(3);
			context.getInput().pressKey(o -> o.keyUse);
			context.waitTicks(10);
			context.takeScreenshot("bounty_board");

			pirateHuntTest(context, sp);
			bossHuntTest(context, sp);
			LOG.info("BB DONE, {} failures", FAILURES.size());
		}
		if (!FAILURES.isEmpty()) {
			throw new AssertionError("One Piece Bosses bounty board test failures:\n" + String.join("\n", FAILURES));
		}
	}

	/** Five hunts, two of them rogues, the same all day and different tomorrow; every reward and target is real. */
	private static void rotationTest(MinecraftServer s) {
		List<Hunt> today = BountyBoard.hunts(s);
		long seed = s.overworld().getSeed();
		long day = BountyBoard.day(s);
		for (Hunt h : today) {
			LOG.info("BB HUNT {} {} {} x{} -> {}", h.id(), h.kind(), h.target(), h.count(), BountyBoard.reward(h));
		}
		check(today.size() == BountyBoard.SLOTS, today.size() + " hunts on the board");
		check(today.stream().filter(h -> Hunt.BOSS.equals(h.kind())).count() == 2, "not two rogue hunts");
		check(today.stream().map(Hunt::kind).distinct().count() == 4, "the mob hunts aren't one of each kind");
		check(today.equals(BountyBoard.hunts(seed, day)), "the board changed within a day");
		check(!today.equals(BountyBoard.hunts(seed, day + 1)), "tomorrow's board is the same as today's");
		check(!BountyBoard.beastPool(List.copyOf(RogueData.all().values())).isEmpty(), "no creatures for beast hunts");
		// A month of boards: every rogue, creature and rare item they name exists.
		for (long d = day; d < day + 30; d++) {
			for (Hunt h : BountyBoard.hunts(seed, d)) {
				if (Hunt.BOSS.equals(h.kind())) {
					check(RogueData.get(h.target()) != null, h.id() + " names a missing rogue " + h.target());
				}
				if (Hunt.BEAST.equals(h.kind())) {
					check(BuiltInRegistries.ENTITY_TYPE.containsKey(Identifier.parse(h.target())), h.id() + " names a missing creature " + h.target());
				}
				if (!h.rare().isEmpty()) {
					check(BuiltInRegistries.ITEM.containsKey(Identifier.parse(h.rare())), h.id() + " pays a missing item " + h.rare());
				}
				check(h.berries() > 0, h.id() + " pays no Berries");
			}
		}
	}

	/** Take the pirate hunt, beat the pirates, hand it in for Berries; it can't be taken twice; out of range says so. */
	private static void pirateHuntTest(ClientGameTestContext context, TestSingleplayerContext sp) throws Exception {
		server(sp, s -> {
			ServerPlayer p = player(s);
			int slot = slotOf(s, Hunt.PIRATES);
			check(BountyBoard.take(p, slot) == null, "couldn't take the pirate hunt after reading the board");
			check(BountyBoard.take(p, slot) != null, "took a second hunt while one was running");
			Hunt hunt = BountyBoard.active(p);
			check(hunt != null && Hunt.PIRATES.equals(hunt.kind()), "the pirate hunt isn't the player's");
			if (hunt == null) {
				return;
			}
			ServerLevel level = s.overworld();
			// A cow doesn't count, a pirate does.
			Entity cow = net.minecraft.world.entity.EntityTypes.COW.create(level, EntitySpawnReason.COMMAND);
			if (cow instanceof net.minecraft.world.entity.LivingEntity living) {
				living.snapTo(HOME.getX() + 3.5, HOME.getY(), HOME.getZ() + 0.5, 0f, 0f);
				level.addFreshEntity(living);
				living.hurtServer(level, p.damageSources().playerAttack(p), 100_000);
			}
			check(BountyBoard.active(p).progress() == 0, "a cow counted as a pirate");
			int killed = 0;
			for (int i = 0; i < hunt.count() + 2; i++) {
				HumanNpc npc = NpcFeature.spawn(level, "pirate", HOME.offset(3, 0, 0), 0f);
				if (npc != null) {
					npc.hurtServer(level, p.damageSources().playerAttack(p), 100_000);
					killed++;
				}
			}
			Hunt after = BountyBoard.active(p);
			LOG.info("BB PIRATES killed {} for {}: progress {}/{}", killed, hunt.title(), after.progress(), after.count());
			check(after.done(), "beating " + killed + " pirates didn't finish " + hunt.title());
			check(after.progress() == after.count(), "progress went past the count");
		});
		context.waitTicks(10);
		server(sp, s -> {
			ServerPlayer p = player(s);
			Hunt hunt = BountyBoard.active(p);
			Item berry = OnePieceBridge.berries(1).getItem();
			int before = p.getInventory().countItem(berry);
			BountyBoard.use(p, BOARD);
			int after = p.getInventory().countItem(berry);
			LOG.info("BB PAY berries {} -> {} (want +{}), handed in {}", before, after, hunt == null ? -1 : hunt.berries(), BountyBoard.handedIn(p));
			check(BountyBoard.active(p) == null, "the hunt is still running after handing it in");
			check(hunt != null && after - before == hunt.berries(), "paid " + (after - before) + " Berries");
			check(BountyBoard.handedIn(p) == 1, "hand-ins counted " + BountyBoard.handedIn(p));
			check(BountyBoard.take(p, slotOf(s, Hunt.PIRATES)) != null, "took the same hunt twice in a day");
			// Walk off: no taking hunts from across the island.
			p.teleportTo(s.overworld(), HOME.getX() + 20.5, HOME.getY(), HOME.getZ() + 0.5, Set.of(), 0f, 10f, true);
			check(BountyBoard.take(p, slotOf(s, Hunt.RAIDERS)) != null, "took a hunt 20 blocks from the board");
			p.teleportTo(s.overworld(), HOME.getX() + 0.5, HOME.getY(), HOME.getZ() + 0.5, Set.of(), 180f, 10f, true);
		});
	}

	/** Take the first rogue hunt: its Rumor Poster arrives, beating the rogue finishes it, the payout has its rare drop. */
	private static void bossHuntTest(ClientGameTestContext context, TestSingleplayerContext sp) throws Exception {
		String[] bossId = new String[1];
		server(sp, s -> {
			ServerPlayer p = player(s);
			BountyBoard.use(p, BOARD);
			int slot = slotOf(s, Hunt.BOSS);
			Hunt hunt = BountyBoard.hunts(s).get(slot - 1);
			bossId[0] = hunt.target();
			check(BountyBoard.take(p, slot) == null, "couldn't take the rogue hunt");
			check(p.getInventory().countItem(BossItems.RUMORS.get(hunt.target())) == 1, "no Rumor Poster for " + hunt.target());
			RogueBossEntity boss = RogueBosses.ROGUE_BOSS.create(s.overworld(), EntitySpawnReason.COMMAND);
			boss.snapTo(HOME.getX() + 6.5, HOME.getY(), HOME.getZ() + 0.5, 90f, 0f);
			boss.setCharacter(hunt.target(), true);
			s.overworld().addFreshEntity(boss);
		});
		context.waitTicks(20);
		server(sp, s -> {
			ServerPlayer p = player(s);
			List<RogueBossEntity> bosses = s.overworld().getEntitiesOfClass(RogueBossEntity.class, area(), Entity::isAlive);
			check(!bosses.isEmpty(), "the rogue didn't spawn");
			for (RogueBossEntity boss : bosses) {
				boss.hurtServer(s.overworld(), p.damageSources().playerAttack(p), 100_000);
			}
			Hunt hunt = BountyBoard.active(p);
			LOG.info("BB BOSS {} beaten, hunt {}", bossId[0], hunt == null ? "none" : hunt.progress() + "/" + hunt.count());
			check(hunt != null && hunt.done(), "beating " + bossId[0] + " didn't finish the rogue hunt");
		});
		context.waitTicks(20);
		server(sp, s -> {
			ServerPlayer p = player(s);
			Hunt hunt = BountyBoard.active(p);
			if (hunt == null) {
				return;
			}
			Item rare = BuiltInRegistries.ITEM.getValue(Identifier.parse(hunt.rare()));
			int before = p.getInventory().countItem(rare);
			BountyBoard.use(p, BOARD);
			int after = p.getInventory().countItem(rare);
			LOG.info("BB BOSS PAY {} {} -> {} (want +{}), handed in {}", hunt.rare(), before, after, hunt.rareCount(), BountyBoard.handedIn(p));
			check(after - before == hunt.rareCount(), "the rare drop " + hunt.rare() + " wasn't paid");
			check(BountyBoard.handedIn(p) == 2, "hand-ins counted " + BountyBoard.handedIn(p));
		});
		context.waitTicks(10);
		context.takeScreenshot("bounty_board_payout");
		server(sp, s -> clearMobs(s));
	}

	// ---- Helpers ----

	private static int slotOf(MinecraftServer s, String kind) {
		List<Hunt> hunts = BountyBoard.hunts(s);
		for (int i = 0; i < hunts.size(); i++) {
			if (kind.equals(hunts.get(i).kind())) {
				return i + 1;
			}
		}
		check(false, "no " + kind + " hunt on the board");
		return 1;
	}

	private static AABB area() {
		return new AABB(HOME).inflate(64, 24, 64);
	}

	private static void clearMobs(MinecraftServer s) {
		for (Entity e : s.overworld().getEntitiesOfClass(Entity.class, area(), e -> !(e instanceof Player))) {
			e.discard();
		}
	}

	private static void check(boolean ok, String what) {
		if (!ok) {
			LOG.info("BB FAIL {}", what);
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
