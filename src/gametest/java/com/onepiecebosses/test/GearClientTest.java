package com.onepiecebosses.test;

import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.boss.RogueBosses;
import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.gear.GearItems;
import com.onepiecebosses.gear.GearSets;

/**
 * The boss gear sets: every boss has a set; a beaten boss drops its Remnants; wearing the full set keeps its passive
 * effects on and its signature move goes off on a mob (then waits out its cooldown); and a screenshot of each set on
 * an armour stand. Run it with -Dopbosses.tests=gear (and -Dopbosses.only=&lt;boss ids&gt; for some of them).
 * Results are "GT" lines in the log; screenshots are gear_&lt;set&gt;.png.
 */
public class GearClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("bosses-gear-test");
	private static final double PX = 0.5, PY = 100, PZ = 0.5;
	private static final List<String> FAILURES = new java.util.concurrent.CopyOnWriteArrayList<>();

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("gear")) {
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
			sp.getServer().runCommand("gamemode survival @a");
			sp.getServer().runCommand("time set noon");
			sp.getServer().runCommand("weather clear");
			sp.getServer().runCommand("gamerule spawn_mobs false");
			sp.getServer().runCommand("gamerule advance_time false");
			context.waitTicks(10);
			context.setScreen(() -> null);
			server(sp, s -> {
				arena(s.overworld());
				ServerPlayer p = player(s);
				p.teleportTo(s.overworld(), PX, PY, PZ, Set.of(), 0f, 10f, true);
				p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 1200, 4, false, false));
				p.addEffect(new MobEffectInstance(MobEffects.SATURATION, 20 * 1200, 4, false, false));
				for (String id : RogueData.all().keySet()) {
					GearItems.Set set = GearItems.SETS.get(id);
					check(set != null, id + ": no gear set");
					if (set != null) {
						for (var item : List.of(set.remnant(), set.armor()[0], set.armor()[1], set.armor()[2], set.armor()[3], set.weapon())) {
							check(BuiltInRegistries.ITEM.getKey(item).getNamespace().equals("opbosses"), id + ": " + item + " not registered");
						}
					}
				}
			});
			context.waitTicks(20);

			for (String id : GearItems.SETS.keySet()) {
				if (TestFilter.picks(id, GearItems.SETS.get(id).data().set)) {
					setTest(context, sp, id);
				}
			}
			LOG.info("GT DONE, {} failures", FAILURES.size());
		}
		if (!FAILURES.isEmpty()) {
			throw new AssertionError("One Piece Bosses gear test failures:\n" + String.join("\n", FAILURES));
		}
	}

	private void setTest(ClientGameTestContext context, TestSingleplayerContext sp, String id) throws Exception {
		GearItems.Set set = GearItems.SETS.get(id);
		String name = set.data().set;

		// A beaten boss drops its Remnants (2 on Normal).
		server(sp, s -> {
			clearMobs(s);
			ServerLevel level = s.overworld();
			RogueBossEntity boss = RogueBosses.ROGUE_BOSS.create(level, EntitySpawnReason.COMMAND);
			boss.setPos(PX + 4, PY, PZ);
			boss.setCharacter(id, true);
			boss.setNoAi(true);
			level.addFreshEntity(boss);
			ServerPlayer p = player(s);
			boss.hurtServer(level, p.damageSources().playerAttack(p), 1_000_000);
		});
		context.waitTicks(20);
		server(sp, s -> {
			int remnants = s.overworld().getEntitiesOfClass(ItemEntity.class, area(), e -> e.getItem().is(set.remnant()))
					.stream().mapToInt(e -> e.getItem().getCount()).sum();
			remnants += countInInventory(player(s), set);
			LOG.info("GT {} remnants dropped={}", id, remnants);
			check(remnants >= 2, id + ": " + remnants + " Remnants from a Normal win, want 2");
			clearMobs(s);
		});

		// Wear the set and hold the weapon: the passives come on within a second or two.
		server(sp, s -> {
			ServerPlayer p = player(s);
			p.removeAllEffects();
			p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 1200, 4, false, false));
			p.teleportTo(s.overworld(), PX, PY, PZ, Set.of(), 0f, 10f, true);
			p.setItemSlot(EquipmentSlot.HEAD, new ItemStack(set.armor()[0]));
			p.setItemSlot(EquipmentSlot.CHEST, new ItemStack(set.armor()[1]));
			p.setItemSlot(EquipmentSlot.LEGS, new ItemStack(set.armor()[2]));
			p.setItemSlot(EquipmentSlot.FEET, new ItemStack(set.armor()[3]));
			p.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(set.weapon()));
			p.setHealth(p.getMaxHealth() - 6);
		});
		context.waitTicks(45);
		server(sp, s -> {
			ServerPlayer p = player(s);
			check(GearSets.fullSet(p) == set, id + ": full set not recognised");
			for (List<Object> passive : set.data().passives) {
				String when = passive.size() > 2 ? String.valueOf(passive.get(2)) : "always";
				if (!when.equals("always")) {
					continue;
				}
				var effect = BuiltInRegistries.MOB_EFFECT.get(Identifier.withDefaultNamespace(String.valueOf(passive.get(0))));
				check(effect.isPresent(), id + ": unknown effect " + passive.get(0));
				effect.ifPresent(e -> check(p.hasEffect(e), id + ": full set but no " + passive.get(0)));
			}
			LOG.info("GT {} passives {}", id, p.getActiveEffects());
		});

		// The signature move on two zombies in front, then the cooldown.
		float[] before = new float[2];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			ServerPlayer p = player(s);
			Mob first = zombie(level, PX, PZ + 3);
			Mob second = zombie(level, PX + 1.5, PZ + 4.5);
			second.setTarget(p);
			before[0] = first.getHealth();
			before[1] = second.getHealth();
			GearSets.resetCooldown(p);
			try {
				boolean went = GearSets.tryUnleash(p, set, first);
				check(went, id + ": signature didn't go off");
				check(!GearSets.tryUnleash(p, set, first), id + ": signature went off twice with no cooldown");
			} catch (Exception e) {
				LOG.info("GT {} signature threw", id, e);
				check(false, id + ": signature threw " + e);
			}
		});
		context.waitTicks(8);
		context.takeScreenshot("gear_" + name + "_move");
		context.waitTicks(30);
		server(sp, s -> {
			List<Mob> zombies = s.overworld().getEntitiesOfClass(Mob.class, area(), e -> e.entityTags().contains("opbosses_gear_test"));
			boolean anyHurt = zombies.size() < 2 || zombies.stream().anyMatch(z -> z.getHealth() < Math.max(before[0], before[1])
					|| !z.getActiveEffects().isEmpty());
			LOG.info("GT {} after move: zombies {} health {} effects {} player health {}", id, zombies.size(),
					zombies.stream().map(LivingEntity::getHealth).toList(), zombies.stream().map(z -> z.getActiveEffects().size()).toList(),
					player(s).getHealth());
			check(anyHurt, id + ": signature hurt or affected nothing");
			clearMobs(s);
			ServerPlayer p = player(s);
			for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.MAINHAND}) {
				p.setItemSlot(slot, ItemStack.EMPTY);
			}
			p.removeAllEffects();
			p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 20 * 1200, 4, false, false));
		});

		// A portrait of the set on an armour stand, front and back.
		sp.getServer().runCommand("summon minecraft:armor_stand " + PX + " " + PY + " " + (PZ + 3)
				+ " {ShowArms:1b,NoBasePlate:1b,Rotation:[180f,0f],Tags:[\"opbosses_gear_test\"]}");
		context.waitTicks(2);
		server(sp, s -> {
			for (Entity e : s.overworld().getEntitiesOfClass(Entity.class, area(), e -> e.entityTags().contains("opbosses_gear_test"))) {
				if (e instanceof LivingEntity stand) {
					stand.setItemSlot(EquipmentSlot.HEAD, new ItemStack(set.armor()[0]));
					stand.setItemSlot(EquipmentSlot.CHEST, new ItemStack(set.armor()[1]));
					stand.setItemSlot(EquipmentSlot.LEGS, new ItemStack(set.armor()[2]));
					stand.setItemSlot(EquipmentSlot.FEET, new ItemStack(set.armor()[3]));
					stand.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(set.weapon()));
				}
			}
			ServerPlayer p = player(s);
			p.teleportTo(s.overworld(), PX + 0.6, PY, PZ, Set.of(), 0f, 15f, true);
		});
		// Clear the chat, which otherwise covers the stand's leggings and boots.
		context.runOnClient(client -> client.gui.hud.getChat().clearMessages(true));
		context.waitTicks(15);
		context.takeScreenshot("gear_" + name);
		server(sp, s -> player(s).teleportTo(s.overworld(), PX - 0.6, PY, PZ + 6, Set.of(), 180f, 15f, true));
		context.waitTicks(10);
		context.takeScreenshot("gear_" + name + "_back");
		server(sp, this::clearMobs);
	}

	private static Mob zombie(ServerLevel level, double x, double z) {
		Mob zombie = (Mob) net.minecraft.world.entity.EntityTypes.ZOMBIE.create(level, EntitySpawnReason.COMMAND);
		zombie.setPos(x, PY, z);
		zombie.setNoAi(true);
		zombie.addTag("opbosses_gear_test");
		zombie.setItemSlot(EquipmentSlot.HEAD, new ItemStack(net.minecraft.world.item.Items.LEATHER_HELMET)); // No burning at noon.
		level.addFreshEntity(zombie);
		return zombie;
	}

	private static int countInInventory(ServerPlayer p, GearItems.Set set) {
		int count = 0;
		for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
			ItemStack stack = p.getInventory().getItem(i);
			if (stack.is(set.remnant())) {
				count += stack.getCount();
			}
		}
		return count;
	}

	private static void check(boolean ok, String what) {
		if (!ok) {
			LOG.info("GT FAIL {}", what);
			FAILURES.add(what);
		}
	}

	private static AABB area() {
		return new AABB(PX, PY, PZ, PX, PY, PZ).inflate(24);
	}

	private void clearMobs(MinecraftServer s) {
		for (Entity e : s.overworld().getEntitiesOfClass(Entity.class, area(), e -> !(e instanceof Player))) {
			e.discard();
		}
		ServerPlayer p = player(s);
		p.getInventory().clearContent();
	}

	private static void arena(ServerLevel level) {
		for (int x = -10; x <= 10; x++) {
			for (int z = -10; z <= 12; z++) {
				level.setBlockAndUpdate(new BlockPos(x, 99, z), Blocks.STONE.defaultBlockState());
				boolean edge = x == -10 || x == 10 || z == -10 || z == 12;
				for (int y = 100; y < 112; y++) {
					level.setBlockAndUpdate(new BlockPos(x, y, z), edge ? Blocks.BARRIER.defaultBlockState() : Blocks.AIR.defaultBlockState());
				}
			}
		}
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void server(TestSingleplayerContext sp, Consumer<MinecraftServer> action) throws Exception {
		sp.getServer().runOnServer(action::accept);
	}
}
