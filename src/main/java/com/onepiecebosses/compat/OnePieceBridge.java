package com.onepiecebosses.compat;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.BossStrikes;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.npc.NpcKit;
import com.onepiecemod.world.SeastoneEffects;
import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.npc.NpcNames;
import com.onepiecemod.town.Town;
import com.onepiecemod.town.Towns;

/**
 * Every static call into the One Piece Mod goes through here (RogueBossEntity also extends its CharacterEntity).
 * If the main mod renames something, this is the first file to fix.
 */
public final class OnePieceBridge {
	private OnePieceBridge() {
	}

	/** Adds an NPC kit to the main mod's list, unless it already has one with that id. */
	public static void addNpcKit(NpcKit kit) {
		NpcKit.all().putIfAbsent(kit.id, kit);
	}

	/** Spawns one of the main mod's NPCs from a kit, tagged as a boss minion (boss attacks pass through it). */
	public static Mob spawnMinion(ServerLevel level, String kitId, BlockPos pos, float yaw) {
		HumanNpc npc = NpcFeature.spawn(level, kitId, pos, yaw);
		if (npc != null) {
			npc.addTag(BossStrikes.MINION_TAG);
		}
		return npc;
	}

	/** Spawns any mob (a main mod creature like "onepiece:manticore", or a vanilla one), tagged as a boss minion. */
	public static Mob spawnBeast(ServerLevel level, String entityId, BlockPos pos, float yaw) {
		Identifier id = Identifier.tryParse(entityId);
		if (id == null || !BuiltInRegistries.ENTITY_TYPE.containsKey(id)) {
			return null;
		}
		Entity entity = BuiltInRegistries.ENTITY_TYPE.getValue(id).create(level, EntitySpawnReason.MOB_SUMMONED);
		if (!(entity instanceof Mob mob)) {
			if (entity != null) {
				entity.discard();
			}
			return null;
		}
		mob.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, yaw, 0.0f);
		mob.addTag(BossStrikes.MINION_TAG);
		mob.setPersistenceRequired();
		level.addFreshEntity(mob);
		return mob;
	}

	/** The kit a main mod NPC was made from ("pirate", "fishman"...), or null for anything else. */
	public static String npcKit(LivingEntity entity) {
		return entity instanceof HumanNpc npc ? npc.getKitId() : null;
	}

	/** True for a main mod NPC (or one of ours built on it) whose kit is a pirate one: sea pirates, rogue crews, rookie raiders. */
	public static boolean isPirateNpc(LivingEntity entity) {
		if (!(entity instanceof HumanNpc npc)) {
			return false;
		}
		NpcKit kit = NpcKit.get(npc.getKitId());
		return kit != null && "pirate".equals(kit.faction);
	}

	/** True for players who ate a fruit, and for bosses who have one. */
	public static boolean isFruitUser(LivingEntity entity) {
		return SeastoneEffects.isFruitUser(entity);
	}

	/** The main mod's seastone weakness. 20 ticks = 1 second. */
	public static void drainFruitPower(LivingEntity entity, int ticks) {
		SeastoneEffects.drain(entity, ticks);
	}

	/** What the main mod already pays for beating a boss with this id the first time. */
	public static long mainModBossReward(String bossId) {
		return Bounty.bossReward(bossId);
	}

	public static void raiseBounty(ServerPlayer player, long amount, String reason) {
		Bounty.raise(player, amount, reason, false);
	}

	/** The hardest fight this player has unlocked against a boss, the same way Wanted Posters work it out. */
	public static int unlockedDifficulty(Player player, String bossId) {
		if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, bossId + ":hard")) {
			return CharacterEntity.EXPERT;
		}
		if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, bossId)) {
			return CharacterEntity.HARD;
		}
		return CharacterEntity.NORMAL;
	}

	/** A main mod (or rogue) character's display name, or a tidied id if it has none. */
	public static String characterName(String id) {
		com.onepiecebosses.boss.RogueData rogue = com.onepiecebosses.boss.RogueData.get(id);
		if (rogue != null) {
			return rogue.name();
		}
		com.onepiecemod.character.CharacterData data = com.onepiecemod.character.CharacterData.get(id);
		return data != null && data.name != null ? data.name : id.replace('_', ' ');
	}

	// ---- For the world mobs (world package) ----

	/** A player's bounty in Berries. */
	public static long bounty(Player player) {
		return Bounty.get(player);
	}

	/** The main mod's threat level for a player's bounty: 0 none, 1 from 1 Berry, 2 from 50M, 3 from 100M... */
	public static int threatLevel(Player player) {
		return Bounty.threatLevel(player);
	}

	/** A bounty written the main mod's way ("12,000,000"). */
	public static String formatBerries(long amount) {
		return Bounty.format(amount);
	}

	/** True if the main mod would let a new hunt start on this player now (not in a boss fight or raid, not lying low at home). */
	public static boolean navyCanStart(ServerPlayer player) {
		return NavyCalm.canStart(player);
	}

	/** In the middle of something big: a story event, a raid, a boss fight... */
	public static boolean isBusy(ServerPlayer player) {
		return NavyCalm.isBusy(player);
	}

	/** Adds a "busy" check, so the main mod holds back its Marine hunts and Navy raids meanwhile. */
	public static void registerBusy(java.util.function.Predicate<ServerPlayer> busy) {
		NavyCalm.register(busy);
	}

	/** A made-up pirate crew name ("Red Gull Pirates"). */
	public static String pirateCrewName(RandomSource random) {
		return NpcNames.crew(random);
	}

	public static ItemStack berries(int count) {
		return new ItemStack(CharacterFeature.BERRY, count);
	}

	/** One of the main mod's towns: where its plaza is and its name. */
	public record TownSpot(BlockPos center, String name) {}

	/** The main mod town a position is in (or within 16 blocks of), or null. */
	public static TownSpot townAt(ServerLevel level, BlockPos pos) {
		Town town = Towns.at(level, pos, 16);
		if (town == null) {
			return null;
		}
		return new TownSpot(town.plaza != null ? town.plaza : town.box.getCenter(), town.name());
	}

	/**
	 * The main mod's cheap biome check for a structure start at chunk n (no layout), so LairNeighbours only lays out
	 * the main mod's builds that can really start near a lair.
	 */
	public static boolean startBiomeFits(net.minecraft.world.level.levelgen.structure.Structure structure,
			net.minecraft.world.level.ChunkPos n, net.minecraft.world.level.levelgen.structure.Structure.GenerationContext ctx) {
		return com.onepiecemod.world.StructureSpacing.startBiomeFits(structure, n, ctx);
	}
}
