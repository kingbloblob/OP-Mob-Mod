package com.onepiecebosses.crew;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecebosses.BossesMod;
import com.onepiecebosses.compat.OnePieceBridge;

/**
 * Rival pirate crews: small original crews (the "rivals" in src/main/resources/opbosses/crews.json) who roam the
 * land behind their captain. They fight players, Marines and bounty hunters, and any other rival crew they run into,
 * so now and then you'll come across two crews already brawling. Some have made camp around a treasure chest
 * (CrewCamp) and stand guard over it.
 *
 * Every 30 seconds each player out in the Overworld (survival or adventure, not Peaceful, on dry land) rolls for a
 * crew turning up 40 to 60 blocks away: about one every 20 minutes, and never while another crew is close by.
 * Beating a captain raises your bounty (the captain kit's "bounty"), and the first mate takes over the crew.
 *
 * Operators can call them with /opbosses crew [id], /opbosses crew camp [id] and /opbosses crew clash.
 */
public final class RivalCrews {
	private RivalCrews() {
	}

	private static final int CHECK_EVERY = 20 * 30;
	/** Chance per check of a crew turning up: about every 20 minutes. */
	private static final float CHANCE = 0.025f;
	/** Of those, how many are camped around treasure, and how many run into a second crew. */
	private static final float CAMP_CHANCE = 0.3f;
	private static final float CLASH_CHANCE = 0.25f;
	/** No new crew while a rival pirate is this close to the player. */
	private static final double CROWD_RANGE = 112.0;

	public static final String TAG = "opbosses_rival";

	private static final ResourceKey<EntityType<?>> KEY = ResourceKey.create(Registries.ENTITY_TYPE, BossesMod.id("rival_pirate"));
	public static final EntityType<RivalPirateEntity> RIVAL_PIRATE = Registry.register(BuiltInRegistries.ENTITY_TYPE, KEY,
			EntityType.Builder.<RivalPirateEntity>of(RivalPirateEntity::new, MobCategory.MONSTER)
					.sized(0.6f, 1.95f)
					.clientTrackingRange(10)
					.build(KEY));

	/** One rival crew from crews.json. */
	public static class Rival {
		public String id;
		public String name;
		public String captain;
		public List<String> crew = List.of();
		public int min = 2;
		public int max = 4;
		/** A dye colour ("red", "light_blue"...) for their flag and tent. */
		public String color = "black";
		public String boast = "";
	}

	private static final Map<String, Rival> ALL = new LinkedHashMap<>();

	/** Called by CrewKits once the kits are in, with the "rivals" list from crews.json. */
	static void load(List<Rival> rivals) {
		ALL.clear();
		for (Rival rival : rivals) {
			ALL.put(rival.id, rival);
		}
	}

	public static Map<String, Rival> all() {
		return ALL;
	}

	public static Rival get(String id) {
		return ALL.get(id);
	}

	public static void initialize() {
		FabricDefaultAttributeRegistry.register(RIVAL_PIRATE, RivalPirateEntity.createAttributes());
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (canMeet(player) && player.getRandom().nextFloat() < CHANCE && nearby((ServerLevel) player.level(), player.blockPosition()) == 0) {
					encounter(player);
				}
			}
		});
		registerCommands();
	}

	private static boolean canMeet(ServerPlayer player) {
		return player.level().dimension() == Level.OVERWORLD && !player.isCreative() && !player.isSpectator()
				&& player.level().getDifficulty() != Difficulty.PEACEFUL && player.isAlive()
				&& !player.isInWater() && player.getVehicle() == null && !OnePieceBridge.isBusy(player);
	}

	/** Rival pirates around a spot. */
	public static int nearby(ServerLevel level, BlockPos pos) {
		return level.getEntitiesOfClass(RivalPirateEntity.class, new AABB(pos).inflate(CROWD_RANGE), RivalPirateEntity::isAlive).size();
	}

	/** The natural roll came up: a camp, a clash, or one crew on the move. */
	private static void encounter(ServerPlayer player) {
		RandomSource random = player.getRandom();
		float roll = random.nextFloat();
		if (roll < CAMP_CHANCE && camp(player, null) != null) {
			return;
		}
		if (roll < CAMP_CHANCE + CLASH_CHANCE && clash(player) > 0) {
			return;
		}
		roam(player, null);
	}

	private static Rival pick(RandomSource random, String except) {
		List<Rival> choices = new ArrayList<>();
		for (Rival rival : ALL.values()) {
			if (!rival.id.equals(except)) {
				choices.add(rival);
			}
		}
		return choices.isEmpty() ? null : choices.get(random.nextInt(choices.size()));
	}

	/** One crew on the move 40-60 blocks from the player. rivalId null = any. Returns the captain, or null. */
	public static RivalPirateEntity roam(ServerPlayer player, String rivalId) {
		ServerLevel level = (ServerLevel) player.level();
		RandomSource random = player.getRandom();
		Rival rival = rivalId != null ? get(rivalId) : pick(random, null);
		BlockPos spot = dryGround(level, player.blockPosition(), 40, 60, random);
		if (rival == null || spot == null) {
			return null;
		}
		List<RivalPirateEntity> band = spawnBand(level, rival, spot, random, false);
		if (band.isEmpty()) {
			return null;
		}
		player.sendSystemMessage(Component.literal("You spot the flag of the " + rival.name + " not far off.").withStyle(ChatFormatting.GOLD));
		return band.get(0);
	}

	/** Two rival crews meeting about 20 blocks apart, near the player. Returns how many pirates came. */
	public static int clash(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		RandomSource random = player.getRandom();
		Rival first = pick(random, null);
		Rival second = first == null ? null : pick(random, first.id);
		BlockPos a = dryGround(level, player.blockPosition(), 36, 52, random);
		BlockPos b = a == null ? null : dryGround(level, a, 16, 22, random);
		if (first == null || second == null || b == null) {
			return 0;
		}
		List<RivalPirateEntity> one = spawnBand(level, first, a, random, false);
		List<RivalPirateEntity> two = spawnBand(level, second, b, random, false);
		if (one.isEmpty() || two.isEmpty()) {
			one.forEach(RivalPirateEntity::discard);
			two.forEach(RivalPirateEntity::discard);
			return 0;
		}
		// The captains have spotted each other: each crew marches on the other.
		one.get(0).setTarget(two.get(0));
		two.get(0).setTarget(one.get(0));
		player.sendSystemMessage(Component.literal("Shouts and steel nearby: the " + first.name + " and the " + second.name
				+ " are settling a score!").withStyle(ChatFormatting.GOLD));
		return one.size() + two.size();
	}

	/** A crew camped around a treasure chest, 30-48 blocks from the player. Returns the camp's chest, or null. */
	public static BlockPos camp(ServerPlayer player, String rivalId) {
		ServerLevel level = (ServerLevel) player.level();
		RandomSource random = player.getRandom();
		Rival rival = rivalId != null ? get(rivalId) : pick(random, null);
		if (rival == null) {
			return null;
		}
		for (int attempt = 0; attempt < 6; attempt++) {
			BlockPos spot = dryGround(level, player.blockPosition(), 30, 48, random);
			if (spot == null || OnePieceBridge.townAt(level, spot) != null) {
				continue;
			}
			BlockPos chest = CrewCamp.build(level, spot, rival, random);
			if (chest == null) {
				continue;
			}
			List<RivalPirateEntity> band = spawnBand(level, rival, spot.offset(0, 0, -3), random, true);
			for (RivalPirateEntity pirate : band) {
				pirate.guardTreasure(chest);
			}
			player.sendSystemMessage(Component.literal("Smoke rises from a camp nearby. The " + rival.name + " are guarding something.")
					.withStyle(ChatFormatting.GOLD));
			return chest;
		}
		return null;
	}

	/** A captain and their crew at a spot. The captain is first in the list. */
	public static List<RivalPirateEntity> spawnBand(ServerLevel level, Rival rival, BlockPos spot, RandomSource random, boolean camped) {
		List<RivalPirateEntity> band = new ArrayList<>();
		UUID bandId = UUID.randomUUID();
		int count = 1 + rival.min + random.nextInt(Math.max(1, rival.max - rival.min + 1));
		RivalPirateEntity captain = null;
		for (int i = 0; i < count; i++) {
			BlockPos pos = i == 0 ? spot : dryGround(level, spot, 1, 3, random);
			RivalPirateEntity pirate = RIVAL_PIRATE.create(level, EntitySpawnReason.EVENT);
			if (pirate == null) {
				continue;
			}
			BlockPos at = pos != null ? pos : spot;
			pirate.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, random.nextFloat() * 360f, 0f);
			boolean isCaptain = captain == null;
			String kit = isCaptain ? rival.captain : rival.crew.get(random.nextInt(rival.crew.size()));
			pirate.joinCrew(rival.id, bandId, isCaptain, isCaptain ? null : captain.getUUID());
			pirate.applyKit(kit, random);
			pirate.addTag(TAG);
			level.addFreshEntity(pirate);
			if (isCaptain) {
				captain = pirate;
			}
			band.add(pirate);
		}
		return band;
	}

	/** Dry, open ground minDist to maxDist from origin, within 12 blocks of its height, in a loaded chunk. */
	static BlockPos dryGround(ServerLevel level, BlockPos origin, int minDist, int maxDist, RandomSource random) {
		for (int attempt = 0; attempt < 24; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = minDist + random.nextInt(Math.max(1, maxDist - minDist + 1));
			int x = Mth.floor(origin.getX() + Math.cos(angle) * distance);
			int z = Mth.floor(origin.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (!level.getFluidState(pos.below()).isEmpty() || !level.getBlockState(pos.below()).isSolid()
					|| Math.abs(pos.getY() - origin.getY()) >= 12
					|| !level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()
					|| !level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty()) {
				continue;
			}
			return pos;
		}
		return null;
	}

	// ---- /opbosses crew (operators only) ----

	private static void registerCommands() {
		// Brigadier merges this into the /opbosses command WorldMobs registers.
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("opbosses")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("crew")
								.executes(c -> roamCommand(c, null))
								.then(Commands.literal("clash")
										.executes(RivalCrews::clashCommand))
								.then(Commands.literal("camp")
										.executes(c -> campCommand(c, null))
										.then(Commands.argument("crew", StringArgumentType.word())
												.suggests((c, b) -> SharedSuggestionProvider.suggest(ALL.keySet(), b))
												.executes(c -> campCommand(c, StringArgumentType.getString(c, "crew")))))
								.then(Commands.argument("crew", StringArgumentType.word())
										.suggests((c, b) -> SharedSuggestionProvider.suggest(ALL.keySet(), b))
										.executes(c -> roamCommand(c, StringArgumentType.getString(c, "crew")))))));
	}

	private static boolean unknown(CommandContext<CommandSourceStack> c, String id) {
		if (id != null && get(id) == null) {
			c.getSource().sendFailure(Component.literal("No rival crew " + id + ". Crews: " + String.join(", ", ALL.keySet())));
			return true;
		}
		return false;
	}

	private static int roamCommand(CommandContext<CommandSourceStack> c, String id) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		if (unknown(c, id)) {
			return 0;
		}
		RivalPirateEntity captain = roam(c.getSource().getPlayerOrException(), id);
		c.getSource().sendSuccess(() -> Component.literal(captain != null ? captain.getName().getString() + " and their crew are nearby"
				: "No dry ground nearby"), false);
		return captain != null ? 1 : 0;
	}

	private static int clashCommand(CommandContext<CommandSourceStack> c) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		int sent = clash(c.getSource().getPlayerOrException());
		c.getSource().sendSuccess(() -> Component.literal(sent > 0 ? "Two crews are fighting nearby (" + sent + " pirates)" : "No dry ground nearby"), false);
		return sent;
	}

	private static int campCommand(CommandContext<CommandSourceStack> c, String id) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		if (unknown(c, id)) {
			return 0;
		}
		BlockPos chest = camp(c.getSource().getPlayerOrException(), id);
		c.getSource().sendSuccess(() -> Component.literal(chest != null ? "A crew made camp at " + chest.toShortString()
				: "No flat, open ground nearby for a camp"), false);
		return chest != null ? 1 : 0;
	}
}
