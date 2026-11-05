package com.onepiecebosses.test;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.phys.AABB;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.onepiecebosses.crew.RivalCrews;
import com.onepiecebosses.crew.RivalPirateEntity;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.npc.NpcKit;
import com.onepiecemod.npc.NpcSkins;

/**
 * In-world check of the rival pirate crews on the flat test world: every crew's kits load; a crew on the move sticks
 * with its captain and goes for a player; two crews fight each other and never their own; a treasure camp is built
 * with loot in its chest and a crew guarding it; beating the captain raises your bounty and a crewmate takes over.
 * Results are "RC" lines in the log; anything wrong says FAIL. Run it alone with
 * `gradlew runClientGameTest -Dopbosses.tests=crews` (opbosses.only: roam, clash, camp).
 */
public class RivalCrewsClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("rival-crews-test");
	private static final List<String> FAILURES = new java.util.concurrent.CopyOnWriteArrayList<>();
	private static final BlockPos HOME = new BlockPos(0, -60, 0);

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("crews")) {
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
			cmd(sp, "difficulty normal");
			context.waitTicks(10);
			context.setScreen(() -> null);
			context.runOnClient(client -> {
				try {
					Field visible = Class.forName("com.onepiecemod.questtree.client.QuestTreePanel").getDeclaredField("visible");
					visible.setAccessible(true);
					visible.set(null, false);
				} catch (ReflectiveOperationException e) {
					LOG.info("RC could not hide quest panel: {}", e.toString());
				}
			});
			server(sp, s -> {
				ServerPlayer p = player(s);
				home(s);
				p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 1200, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.SATURATION, 20 * 1200, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 20 * 1200, 4, false, false));
				checkKits();
			});
			context.waitTicks(20);

			if (TestFilter.picks("roam")) {
				roamTest(context, sp);
			}
			if (TestFilter.picks("clash")) {
				clashTest(context, sp);
			}
			if (TestFilter.picks("camp")) {
				campTest(context, sp);
			}
			LOG.info("RC DONE, {} failures", FAILURES.size());
		}
		if (!FAILURES.isEmpty()) {
			throw new AssertionError("One Piece Bosses rival crew test failures:\n" + String.join("\n", FAILURES));
		}
	}

	private static void checkKits() {
		check(RivalCrews.all().size() >= 6, "only " + RivalCrews.all().size() + " rival crews loaded");
		for (RivalCrews.Rival rival : RivalCrews.all().values()) {
			check(rival.crew != null && !rival.crew.isEmpty(), rival.id + " has no crew kits");
			for (String id : rival.crew == null ? List.of(rival.captain) : concat(rival.captain, rival.crew)) {
				NpcKit kit = NpcKit.get(id);
				check(kit != null, rival.id + ": kit " + id + " is missing");
				if (kit != null) {
					for (String skin : kit.skins) {
						check(NpcSkins.COUNT.containsKey(skin), "kit " + id + " uses missing skin group " + skin);
					}
				}
			}
		}
	}

	/** A crew on the move: one captain, the crew sticks with them, and they go for the player. */
	private static void roamTest(ClientGameTestContext context, TestSingleplayerContext sp) throws Exception {
		server(sp, s -> {
			clearMobs(s);
			mode(s, GameType.CREATIVE); // Left alone while they settle in.
			List<RivalPirateEntity> band = RivalCrews.spawnBand(level(s), RivalCrews.get("red_tusk"), HOME.offset(20, 0, 0), level(s).getRandom(), false);
			LOG.info("RC ROAM {}", band.stream().map(p -> p.getName().getString()).toList());
			check(band.size() >= 3, "only " + band.size() + " in the band");
			check(band.stream().filter(RivalPirateEntity::isCaptain).count() == 1, "the band doesn't have exactly one captain");
			check(band.stream().allMatch(p -> "Red Tusk Pirates".equals(p.getCrew())), "not everyone sails with the Red Tusk Pirates");
		});
		context.waitTicks(400);
		context.takeScreenshot("rival_crews_roam");
		server(sp, s -> {
			List<RivalPirateEntity> band = pirates(s);
			RivalPirateEntity captain = band.stream().filter(RivalPirateEntity::isCaptain).findFirst().orElse(null);
			check(captain != null, "the captain is gone");
			if (captain != null) {
				double farthest = band.stream().mapToDouble(p -> p.distanceTo(captain)).max().orElse(0);
				LOG.info("RC ROAM captain moved to {}, farthest crewmate {}", captain.blockPosition().toShortString(), String.format("%.1f", farthest));
				check(farthest < 14, "a crewmate wandered off from the captain (" + farthest + ")");
			}
			mode(s, GameType.SURVIVAL);
			ServerPlayer p = player(s);
			if (captain != null) {
				p.teleportTo(level(s), captain.getX() + 8, captain.getY(), captain.getZ(), Set.of(), 0f, 10f, true);
			}
		});
		context.waitTicks(80);
		server(sp, s -> {
			ServerPlayer p = player(s);
			long onPlayer = pirates(s).stream().filter(r -> r.getTarget() == p).count();
			LOG.info("RC ROAM {} pirates after the player", onPlayer);
			check(onPlayer >= 2, "the crew didn't go for the player together (" + onPlayer + ")");
			clearMobs(s);
			home(s);
		});
	}

	/** Two crews meet: they fight each other, never their own crew. The player is in creative, out of it. */
	private static void clashTest(ClientGameTestContext context, TestSingleplayerContext sp) throws Exception {
		server(sp, s -> {
			clearMobs(s);
			mode(s, GameType.CREATIVE);
			RivalCrews.spawnBand(level(s), RivalCrews.get("thornback"), HOME.offset(14, 0, 0), level(s).getRandom(), false);
			RivalCrews.spawnBand(level(s), RivalCrews.get("gilded_gull"), HOME.offset(-6, 0, 0), level(s).getRandom(), false);
		});
		boolean ownCrew = false;
		for (int i = 0; i < 6; i++) {
			context.waitTicks(40);
			boolean[] bad = {false};
			server(sp, s -> {
				for (RivalPirateEntity p : pirates(s)) {
					if (p.getTarget() instanceof RivalPirateEntity other && p.sameCrew(other)) {
						bad[0] = true;
					}
				}
			});
			ownCrew |= bad[0];
		}
		context.takeScreenshot("rival_crews_clash");
		boolean turned = ownCrew;
		server(sp, s -> {
			List<RivalPirateEntity> all = pirates(s);
			long fighting = all.stream().filter(p -> p.getTarget() instanceof RivalPirateEntity other && p.isRival(other)).count();
			long hurt = all.stream().filter(p -> p.getHealth() < p.getMaxHealth()).count();
			long thorn = all.stream().filter(p -> "thornback".equals(p.getRivalId())).count();
			long gull = all.stream().filter(p -> "gilded_gull".equals(p.getRivalId())).count();
			LOG.info("RC CLASH {} fighting a rival, {} hurt, {} Thornbacks and {} Gulls left", fighting, hurt, thorn, gull);
			check(fighting > 0 || hurt > 0 || thorn == 0 || gull == 0, "the two crews didn't fight");
			check(!turned, "a pirate went after their own crew");
			clearMobs(s);
			mode(s, GameType.SURVIVAL);
		});
	}

	/** A camp: built, loot in the chest, guarded. Beating the captain raises the bounty and a crewmate takes over. */
	private static void campTest(ClientGameTestContext context, TestSingleplayerContext sp) throws Exception {
		BlockPos[] chestAt = {null};
		server(sp, s -> {
			clearMobs(s);
			mode(s, GameType.CREATIVE);
			chestAt[0] = RivalCrews.camp(player(s), "ashen_wake");
			LOG.info("RC CAMP chest at {}", chestAt[0]);
			check(chestAt[0] != null, "no camp was built on flat ground");
			if (chestAt[0] != null) {
				check(level(s).getBlockState(chestAt[0]).is(Blocks.CHEST), "no chest at the camp");
				int stacks = 0;
				if (level(s).getBlockEntity(chestAt[0]) instanceof ChestBlockEntity chest) {
					for (int i = 0; i < chest.getContainerSize(); i++) {
						stacks += chest.getItem(i).isEmpty() ? 0 : 1;
					}
				}
				LOG.info("RC CAMP {} stacks of loot", stacks);
				check(stacks >= 4, "the treasure chest has only " + stacks + " stacks");
				ServerPlayer p = player(s);
				p.teleportTo(level(s), chestAt[0].getX() + 0.5, chestAt[0].getY() + 6, chestAt[0].getZ() - 14.5, Set.of(), 0f, 25f, true);
			}
		});
		context.waitTicks(200);
		context.takeScreenshot("rival_crews_camp");
		server(sp, s -> {
			if (chestAt[0] == null) {
				return;
			}
			List<RivalPirateEntity> crew = pirates(s);
			long guarding = crew.stream().filter(p -> chestAt[0].equals(p.getTreasure()) && p.isGuard()).count();
			double farthest = crew.stream().mapToDouble(p -> Math.sqrt(p.blockPosition().distSqr(chestAt[0]))).max().orElse(99);
			LOG.info("RC CAMP {} guards, farthest {} from the chest", guarding, String.format("%.1f", farthest));
			check(guarding >= 3 && guarding == crew.size(), "not everyone is guarding the camp (" + guarding + "/" + crew.size() + ")");
			check(farthest < 20, "a guard wandered off from the camp (" + farthest + ")");

			mode(s, GameType.SURVIVAL);
			ServerPlayer p = player(s);
			Bounty.set(p, 0);
			RivalPirateEntity captain = crew.stream().filter(RivalPirateEntity::isCaptain).findFirst().orElse(null);
			check(captain != null, "the camp has no captain");
			if (captain != null) {
				UUID old = captain.getUUID();
				captain.hurtServer(level(s), p.damageSources().playerAttack(p), 100_000);
				long bounty = Bounty.get(p);
				List<RivalPirateEntity> left = pirates(s);
				RivalPirateEntity heir = left.stream().filter(RivalPirateEntity::isCaptain).findFirst().orElse(null);
				LOG.info("RC CAMP bounty after the captain {}, new captain {}", bounty, heir == null ? "none" : heir.getName().getString());
				check(bounty > 0, "beating the captain didn't raise the bounty");
				check(heir != null && !heir.getUUID().equals(old), "nobody took over the crew");
				check(heir == null || left.stream().filter(m -> m != heir).allMatch(m -> heir.getUUID().equals(m.getCaptainId())),
						"the crew doesn't follow the new captain");
			}
			Bounty.set(p, 0);
			clearMobs(s);
			home(s);
		});
	}

	// ---- Helpers ----

	private static List<String> concat(String first, List<String> rest) {
		List<String> all = new java.util.ArrayList<>(rest);
		all.add(0, first);
		return all;
	}

	private static List<RivalPirateEntity> pirates(MinecraftServer s) {
		return s.overworld().getEntitiesOfClass(RivalPirateEntity.class, area(), LivingEntity::isAlive);
	}

	private static AABB area() {
		return new AABB(HOME).inflate(100, 30, 100);
	}

	private static void clearMobs(MinecraftServer s) {
		for (Entity e : s.overworld().getEntitiesOfClass(Entity.class, area().inflate(40), e -> !(e instanceof Player))) {
			e.discard();
		}
	}

	private static void home(MinecraftServer s) {
		player(s).teleportTo(s.overworld(), HOME.getX() + 0.5, HOME.getY(), HOME.getZ() + 0.5, Set.of(), 0f, 10f, true);
	}

	/** Inside server(): runCommand would wait on the server thread we're already on. */
	private static void mode(MinecraftServer s, GameType type) {
		player(s).setGameMode(type);
	}

	private static ServerLevel level(MinecraftServer s) {
		return s.overworld();
	}

	private static void check(boolean ok, String what) {
		if (!ok) {
			LOG.info("RC FAIL {}", what);
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
