package com.onepiecebosses.loot;

import java.util.List;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import com.onepiecebosses.BossItems;
import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecebosses.gear.GearItems;

/**
 * What a rogue boss gives on top of the main mod's boss rewards (Berries, XP, Hard and Expert prizes, bounty):
 * its trophy on a first win, the key to its lair's chest and its gear Remnants every time, and the rest of its bounty.
 * (The main mod's paper already reports every boss's first defeat.) RogueBossEntity calls these.
 */
public final class BossRewards {
	private BossRewards() {
	}

	/**
	 * The main mod raises your bounty by its tier value for a boss it doesn't know (10M for every rogue).
	 * Each player beating this rogue for the first time gets the rest of the boss's own bountyReward.
	 */
	public static void topUpBounty(RogueBossEntity boss, List<ServerPlayer> firstTimers) {
		RogueData data = boss.rogue();
		long extra = data.bountyReward - OnePieceBridge.mainModBossReward(data.id);
		if (extra <= 0) {
			return;
		}
		for (ServerPlayer player : firstTimers) {
			OnePieceBridge.raiseBounty(player, extra, "Rumors spread that you took down " + data.name() + ".");
		}
	}

	/** The boss's trophy, the first time anyone nearby beats it at this difficulty. */
	public static void dropTrophy(RogueBossEntity boss, ServerLevel level) {
		Item trophy = BossItems.TROPHIES.get(boss.rogue().trophy);
		if (trophy != null) {
			boss.spawnAtLocation(level, new ItemStack(trophy));
		}
	}

	/**
	 * The boss's Remnants, every time it's beaten as a boss: 2 on Normal, 3 on Hard, 4 on Expert.
	 * Three of them and a diamond piece craft a piece of its gear set (see gear/GearItems).
	 */
	public static void dropRemnants(RogueBossEntity boss, ServerLevel level) {
		GearItems.Set set = GearItems.SETS.get(boss.rogue().id);
		if (set != null) {
			boss.spawnAtLocation(level, new ItemStack(set.remnant(), 2 + boss.getDifficulty()));
		}
	}

	/** The key to the boss's lair chest, every time it's beaten as a boss. */
	public static void dropKey(RogueBossEntity boss, ServerLevel level) {
		Item key = BossItems.KEYS.get(boss.rogue().id);
		if (key != null) {
			boss.spawnAtLocation(level, new ItemStack(key));
		}
	}
}
