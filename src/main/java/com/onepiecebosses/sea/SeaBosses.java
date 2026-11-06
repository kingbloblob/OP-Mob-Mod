package com.onepiecebosses.sea;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.SeaKingSpawner;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipBrain;

/**
 * Sea encounters: while you sail, a flagship (BossShips) or a Sea King mini-boss (SeaKingBossEntity) may come for you.
 * Rarer than the One Piece Mod's own sea events: a check every 30 seconds, a 2.5% chance, and at least 15 minutes
 * between encounters for each player. Never on Peaceful, and never while you're in another fight or event
 * (OnePieceBridge.isBusy).
 *
 * Which one depends on the sea (CalmBelt.Sea):
 *  - East Blue: the Widowmaker, or Gulpmaw.
 *  - Calm Belt: no wind for ships, so only Sea Kings (it's where they nest): Gulpmaw or Ironscale.
 *  - Grand Line: the Widowmaker or the Tithe Cathedral, or Ironscale.
 *  - New World: the Tithe Cathedral or the Cinderwake, or Thundercoil.
 *
 * Operators can call them: /opbosses seaboss <ship> [player], /opbosses seaking <kind> [player].
 */
public final class SeaBosses {
	private SeaBosses() {
	}

	private static final int CHECK_EVERY = 20 * 30;
	private static final float CHANCE = 0.025f;
	private static final long COOLDOWN = 20 * 60 * 15;
	private static final Map<UUID, Long> NEXT = new HashMap<>();

	public static void initialize() {
		SeaKings.initialize();
		ServerTickEvents.END_SERVER_TICK.register(SeaBosses::tick);
		registerCommands();
	}

	private static void tick(MinecraftServer server) {
		int time = server.getTickCount();
		if (time % 20 == 11) {
			BossShips.tick(server);
		}
		if (time % CHECK_EVERY != 17) {
			return;
		}
		ServerLevel level = server.overworld();
		if (level.getDifficulty() == Difficulty.PEACEFUL) {
			return;
		}
		long now = level.getGameTime();
		for (ServerPlayer player : List.copyOf(level.players())) {
			ShipEntity ship = sailing(player);
			if (ship == null || now < NEXT.getOrDefault(player.getUUID(), 0L) || OnePieceBridge.isBusy(player)
					|| level.getRandom().nextFloat() >= CHANCE || bossNear(level, player.position())) {
				continue;
			}
			CalmBelt.Sea sea = CalmBelt.seaAt(level, ship.blockPosition());
			if (sea == null) {
				continue;
			}
			if (encounter(level, player, sea) != null) {
				NEXT.put(player.getUUID(), now + COOLDOWN);
			}
		}
	}

	/** Starts an encounter for this sea. Returns what came, or null if nothing could. */
	@Nullable
	private static String encounter(ServerLevel level, ServerPlayer player, CalmBelt.Sea sea) {
		RandomSource random = level.getRandom();
		boolean ship = sea != CalmBelt.Sea.CALM_BELT && random.nextBoolean();
		if (ship) {
			String id = switch (sea) {
				case BLUE -> "widowmaker";
				case GRAND_LINE -> random.nextBoolean() ? "widowmaker" : "tithe_cathedral";
				default -> random.nextBoolean() ? "tithe_cathedral" : "cinderwake";
			};
			if (sendShip(level, player, id) != null) {
				return id;
			}
		}
		SeaKingBossEntity.Kind kind = switch (sea) {
			case BLUE -> SeaKingBossEntity.Kind.GULPMAW;
			case CALM_BELT -> random.nextBoolean() ? SeaKingBossEntity.Kind.GULPMAW : SeaKingBossEntity.Kind.IRONSCALE;
			case GRAND_LINE -> SeaKingBossEntity.Kind.IRONSCALE;
			case NEW_WORLD -> SeaKingBossEntity.Kind.THUNDERCOIL;
		};
		return sendSeaKing(level, player, kind) != null ? kind.id : null;
	}

	/** Sends a flagship after a player, with the news. */
	@Nullable
	public static ShipEntity sendShip(ServerLevel level, ServerPlayer player, String id) {
		ShipEntity ship = BossShips.send(level, player, id);
		if (ship != null) {
			String captain = OnePieceBridge.characterName(BossShips.captainOf(id));
			player.sendSystemMessage(Component.literal("Sails on the horizon: the " + ship.getName().getString() + ", " + captain
					+ "'s flagship, is coming about to hunt you!").withStyle(ChatFormatting.RED));
			player.sendSystemMessage(Component.literal("Cannon her below half her hull, then board her to face the captain.")
					.withStyle(ChatFormatting.GRAY));
		}
		return ship;
	}

	/** Sends a Sea King mini-boss after a player: it starts deep beside their ship and comes up underneath. */
	@Nullable
	public static SeaKingBossEntity sendSeaKing(ServerLevel level, ServerPlayer player, SeaKingBossEntity.Kind kind) {
		Vec3 spot = deepSpotNear(level, player);
		if (spot == null) {
			return null;
		}
		SeaKingBossEntity king = SeaKings.TYPES.get(kind).create(level, EntitySpawnReason.EVENT);
		if (king == null) {
			return null;
		}
		king.snapTo(spot.x, spot.y, spot.z, level.getRandom().nextFloat() * 360, 0);
		king.setCustomName(Component.translatable("entity.opbosses." + kind.id).withStyle(ChatFormatting.DARK_AQUA));
		level.addFreshEntity(king);
		king.hunt(player);
		level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, spot.x, level.getSeaLevel() - 1, spot.z, 40, 2, 1, 2, 0.1);
		player.sendSystemMessage(Component.literal("The sea goes dark and still... ").withStyle(ChatFormatting.DARK_AQUA)
				.append(Component.translatable("entity.opbosses." + kind.id).withStyle(ChatFormatting.RED))
				.append(Component.literal(" is hunting you from below!").withStyle(ChatFormatting.DARK_AQUA)));
		return king;
	}

	/** Deep water 14 to 36 blocks from the player (or their ship), 8 below the surface. */
	@Nullable
	private static Vec3 deepSpotNear(ServerLevel level, ServerPlayer player) {
		RandomSource random = level.getRandom();
		for (int attempt = 0; attempt < 48; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			double far = 14 + random.nextInt(23);
			int x = Mth.floor(player.getX() + Math.cos(angle) * far);
			int z = Mth.floor(player.getZ() + Math.sin(angle) * far);
			if (SeaKingSpawner.isDeepWater(level, new BlockPos(x, level.getSeaLevel() - 5, z))) {
				return new Vec3(x + 0.5, level.getSeaLevel() - 8, z + 0.5);
			}
		}
		return null;
	}

	/** The ship a player is sailing (a player's own ship, afloat), or null. Creative players don't get encounters. */
	@Nullable
	private static ShipEntity sailing(ServerPlayer player) {
		if (player.isSpectator() || player.isCreative() || player.level().dimension() != Level.OVERWORLD) {
			return null;
		}
		ShipEntity ship = ShipEntity.aboard(player);
		return ship == null || ship.sinking || ShipBrain.isAi(ship) ? null : ship;
	}

	/** True if a flagship, a Sea King mini-boss or one of the main mod's sea monsters is already out near here. */
	private static boolean bossNear(ServerLevel level, Vec3 at) {
		if (!level.getEntitiesOfClass(SeaKingBossEntity.class, new AABB(at, at).inflate(200), e -> e.isAlive()).isEmpty()) {
			return true;
		}
		if (!level.getEntitiesOfClass(ShipEntity.class, new AABB(at, at).inflate(200), s -> s.entityTags().contains(BossShips.TAG)).isEmpty()) {
			return true;
		}
		// Or one of the main mod's own sea monsters (its Sea King Lord, the Kraken...): one boss at a time.
		return !level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class, new AABB(at, at).inflate(120),
				e -> e.isAlive() && e.entityTags().contains("onepiece_sea_monster")).isEmpty();
	}

	// ---- /opbosses seaboss | seaking (operators only) ----

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("opbosses")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("seaboss")
								.then(Commands.argument("ship", StringArgumentType.word())
										.suggests((c, b) -> SharedSuggestionProvider.suggest(BossShips.IDS, b))
										.executes(c -> seaboss(c, c.getSource().getPlayerOrException()))
										.then(Commands.argument("player", EntityArgument.player())
												.executes(c -> seaboss(c, EntityArgument.getPlayer(c, "player"))))))
						.then(Commands.literal("seaking")
								.then(Commands.argument("kind", StringArgumentType.word())
										.suggests((c, b) -> SharedSuggestionProvider.suggest(
												java.util.Arrays.stream(SeaKingBossEntity.Kind.values()).map(k -> k.id), b))
										.executes(c -> seaking(c, c.getSource().getPlayerOrException()))
										.then(Commands.argument("player", EntityArgument.player())
												.executes(c -> seaking(c, EntityArgument.getPlayer(c, "player"))))))));
	}

	private static int seaboss(CommandContext<CommandSourceStack> c, ServerPlayer player) {
		String id = StringArgumentType.getString(c, "ship");
		if (!BossShips.IDS.contains(id)) {
			c.getSource().sendFailure(Component.literal("No flagship called " + id + ". Try: " + String.join(", ", BossShips.IDS)));
			return 0;
		}
		ShipEntity ship = sendShip((ServerLevel) player.level(), player, id);
		c.getSource().sendSuccess(() -> Component.literal(ship != null ? "Sent the " + ship.getName().getString() + " after " + player.getName().getString()
				: "No flagship came: she needs open sea at least 5 blocks deep, 70 to 100 blocks from the player"), false);
		return ship != null ? 1 : 0;
	}

	private static int seaking(CommandContext<CommandSourceStack> c, ServerPlayer player) {
		SeaKingBossEntity.Kind kind = SeaKingBossEntity.Kind.of(StringArgumentType.getString(c, "kind"));
		if (kind == null) {
			c.getSource().sendFailure(Component.literal("Try: gulpmaw, ironscale or thundercoil"));
			return 0;
		}
		SeaKingBossEntity king = sendSeaKing((ServerLevel) player.level(), player, kind);
		c.getSource().sendSuccess(() -> Component.literal(king != null ? "Sent " + kind.id + " after " + player.getName().getString()
				: "No Sea King came: it needs deep water (8+ blocks) 14 to 36 blocks from the player"), false);
		return king != null ? 1 : 0;
	}
}
