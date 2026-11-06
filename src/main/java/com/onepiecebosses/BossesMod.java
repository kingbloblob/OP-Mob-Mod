package com.onepiecebosses;

import net.minecraft.resources.Identifier;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.api.ModInitializer;

import com.onepiecebosses.boss.ArenaMusic;
import com.onepiecebosses.boss.RogueBosses;
import com.onepiecebosses.bounty.BountyBoard;
import com.onepiecebosses.crew.CrewKits;
import com.onepiecebosses.crew.RivalCrews;
import com.onepiecebosses.gear.GearItems;
import com.onepiecebosses.gear.GearSets;
import com.onepiecebosses.loot.LairChests;
import com.onepiecebosses.loot.RumorDrops;
import com.onepiecebosses.sea.SeaBosses;
import com.onepiecebosses.world.WorldMobs;

/**
 * The starting point of One Piece Bosses. Minecraft calls onInitialize() once while the game is loading,
 * after the One Piece Mod (fabric.mod.json makes this mod depend on it).
 *
 * The bosses here are original rogues, plus the films' villains (who aren't in the main mod's story). Underneath they are the One Piece Mod's own
 * boss mobs (see boss/RogueBossEntity), so they get its health bar, phases, wind-ups, Hard and Expert rematches
 * and bounty. Their data is in src/main/resources/opbosses/bosses.json and crews.json.
 */
public class BossesMod implements ModInitializer {
	public static final String MOD_ID = "opbosses";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		CrewKits.initialize(); // Before the bosses, so their crews exist when a saved boss loads.
		RogueBosses.initialize();
		ArenaMusic.initialize(); // The lairs' battle themes (arenas.json).
		LairChests.initialize();
		BountyBoard.initialize(); // The Marine Bounty Board and its daily hunts.
		BossItems.initialize();
		GearItems.initialize(); // Each boss's Remnant, armour set and weapon.
		GearSets.initialize();
		RumorDrops.initialize();
		WorldMobs.initialize(); // Wandering bounty hunters and rookie pirate raids.
		RivalCrews.initialize(); // Roaming rival pirate crews and their treasure camps.
		SeaBosses.initialize(); // Flagships and Sea King mini-bosses that hunt sailing players.
		LOGGER.info("One Piece Bosses: {} rogue bosses loaded", com.onepiecebosses.boss.RogueData.all().size());
	}

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}
}
