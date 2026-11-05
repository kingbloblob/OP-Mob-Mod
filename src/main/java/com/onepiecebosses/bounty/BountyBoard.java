package com.onepiecebosses.bounty;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;

import com.onepiecebosses.BossItems;
import com.onepiecebosses.BossesMod;
import com.onepiecebosses.boss.RogueBossEntity;
import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecebosses.world.RookieRaiderEntity;

/**
 * The Marine Bounty Board (opbosses:marine_bounty_board): a notice board the Marines pin their hunts to.
 *
 * Every Minecraft day the board shows five fresh hunts, the same on every board in the world: two Wanted rogue bosses
 * and three jobs against roaming mobs (pirate NPCs, the rookie crews that raid villages, or a creature that's been
 * attacking travellers). Right-click a board to read it and click [Take] on a hunt. One hunt at a time; taking a
 * rogue hunt hands you its Rumor Poster so you can call the rogue out. Once it's done, go back to any board to get
 * paid in Berries, plus a rare drop on some hunts (another rogue's Rumor Poster, diamonds, a Lair Restoration Charter).
 *
 * /bountyboard shows your hunt; /bountyboard take &lt;n&gt; (near a board) and /bountyboard drop. A hunt you took or dropped
 * can't be taken again that day.
 */
public final class BountyBoard {
	private BountyBoard() {
	}

	/** Ticks between rotations: one Minecraft day. */
	public static final long DAY = 24000L;
	public static final int SLOTS = 5;
	/** Players this close to a beaten rogue all count it (the boss bar's range). */
	private static final double BOSS_RANGE = 40.0;
	/** How close you have to be to the board you last read to take a hunt from it. */
	private static final double BOARD_RANGE = 8.0;

	public static Block BLOCK;
	public static Item ITEM;

	/** The hunt a player has taken, with their progress. */
	public static final AttachmentType<Hunt> ACTIVE = AttachmentRegistry.create(BossesMod.id("bounty_hunt"),
			builder -> builder.persistent(Hunt.CODEC).copyOnDeath());
	/** Hunt ids ("day:slot") the player took today, so they can't take one twice. */
	public static final AttachmentType<List<String>> TAKEN = AttachmentRegistry.create(BossesMod.id("bounty_taken"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());
	/** How many hunts the player has handed in. */
	public static final AttachmentType<Integer> DONE = AttachmentRegistry.create(BossesMod.id("bounty_done"),
			builder -> builder.persistent(Codec.INT).copyOnDeath());

	/** The board each player read last. Never saved. */
	private record Seen(ResourceKey<Level> dimension, BlockPos pos) {
	}

	private static final Map<UUID, Seen> LAST_BOARD = new HashMap<>();

	/** Creatures a BEAST hunt can be after (the ones that aren't there are skipped), on top of the rogues' own beasts. */
	private static final String[] BEASTS = {"onepiece:lapahn", "onepiece:sand_scorpion", "onepiece:bananawani", "onepiece:humandrill",
			"onepiece:cerberus", "onepiece:basilisk", "onepiece:manticore"};

	/** Berries for a rogue hunt, by tier (1 to 5). The main mod's side jobs pay 10 to 90. */
	private static final int[] BOSS_PAY = {0, 45, 70, 105, 150, 220};

	public static void initialize() {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, BossesMod.id("marine_bounty_board"));
		BLOCK = Registry.register(BuiltInRegistries.BLOCK, key, new BountyBoardBlock(BlockBehaviour.Properties.of()
				.strength(2.0f, 3.0f).sound(SoundType.WOOD).noOcclusion().ignitedByLava().setId(key)));
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, BossesMod.id("marine_bounty_board"));
		ITEM = Registry.register(BuiltInRegistries.ITEM, itemKey,
				new BlockItem(BLOCK, new Item.Properties().rarity(Rarity.UNCOMMON).useBlockDescriptionPrefix().setId(itemKey)));

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity.level() instanceof ServerLevel level) {
				onDeath(level, entity, source.getEntity() instanceof ServerPlayer killer ? killer : null);
			}
		});
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> LAST_BOARD.clear());
		registerCommands();
	}

	// ---- Today's hunts ----

	/** Which day's hunts are up (the same for every board). */
	public static long day(MinecraftServer server) {
		return server.overworld().getGameTime() / DAY;
	}

	/** Today's five hunts, slots 1 to 5. */
	public static List<Hunt> hunts(MinecraftServer server) {
		return hunts(server.overworld().getSeed(), day(server));
	}

	public static List<Hunt> hunts(long seed, long day) {
		RandomSource random = RandomSource.create(seed ^ (day * 0x9E3779B97F4A7C15L) ^ 0x6F70626F756E7479L);
		List<Hunt> hunts = new ArrayList<>();
		List<RogueData> rogues = new ArrayList<>(RogueData.all().values());
		// Two different rogues: one from the lower tiers, one from anywhere, so there's always something within reach.
		List<RogueData> low = rogues.stream().filter(r -> r.tier() <= 3).toList();
		RogueData first = pick(low.isEmpty() ? rogues : low, random);
		RogueData second = first;
		for (int i = 0; i < 8 && second == first; i++) {
			second = pick(rogues, random);
		}
		for (RogueData rogue : second == first ? List.of(first) : List.of(first, second)) {
			hunts.add(bossHunt(day, hunts.size() + 1, rogue, rogues, random));
		}
		// Then the roaming mobs, each kind once, in a random order.
		List<String> kinds = new ArrayList<>(List.of(Hunt.PIRATES, Hunt.RAIDERS, Hunt.BEAST));
		for (int i = kinds.size() - 1; i > 0; i--) {
			java.util.Collections.swap(kinds, i, random.nextInt(i + 1));
		}
		for (String kind : kinds) {
			if (hunts.size() >= SLOTS) {
				break;
			}
			hunts.add(mobHunt(day, hunts.size() + 1, kind, rogues, random));
		}
		return hunts;
	}

	private static Hunt bossHunt(long day, int slot, RogueData rogue, List<RogueData> rogues, RandomSource random) {
		int tier = Math.max(1, Math.min(5, rogue.tier()));
		int berries = BOSS_PAY[tier] + random.nextInt(10);
		String rare;
		int rareCount = 1;
		if (tier >= 4) {
			rare = BossesMod.id("lair_charter").toString();
		} else {
			// A lead on someone tougher: a higher-tier rogue's Rumor Poster.
			List<RogueData> tougher = rogues.stream().filter(r -> r.tier() > tier && r.tier() <= tier + 2).toList();
			if (tougher.isEmpty()) {
				rare = "minecraft:diamond";
				rareCount = 2;
			} else {
				rare = BossesMod.id("rumor_" + pick(tougher, random).id).toString();
			}
		}
		return new Hunt(day + ":" + slot, Hunt.BOSS, rogue.id, 1, 0, "Wanted: " + rogue.name(), berries, rare, rareCount);
	}

	private static Hunt mobHunt(long day, int slot, String kind, List<RogueData> rogues, RandomSource random) {
		String id = day + ":" + slot;
		String rare = "";
		int rareCount = 0;
		// Some mob hunts carry a rare drop too.
		if (random.nextInt(5) < 2) {
			List<RogueData> leads = rogues.stream().filter(r -> r.tier() <= 2).toList();
			if (!leads.isEmpty() && random.nextBoolean()) {
				rare = BossesMod.id("rumor_" + pick(leads, random).id).toString();
				rareCount = 1;
			} else {
				rare = "minecraft:diamond";
				rareCount = 2;
			}
		}
		return switch (kind) {
			case Hunt.RAIDERS -> {
				int count = 4 + random.nextInt(4);
				yield new Hunt(id, kind, "", count, 0, "Break up a rookie raiding crew (" + count + " raiders)", 25 + count * 3, rare, rareCount);
			}
			case Hunt.BEAST -> {
				List<String> pool = beastPool(rogues);
				if (pool.isEmpty()) {
					yield mobHunt(day, slot, Hunt.PIRATES, rogues, random);
				}
				String beast = pool.get(random.nextInt(pool.size()));
				int count = 2 + random.nextInt(3);
				yield new Hunt(id, kind, beast, count, 0, "Cull " + count + " " + beastName(beast), 30 + count * 6, rare, rareCount);
			}
			default -> {
				int count = 6 + random.nextInt(7);
				yield new Hunt(id, Hunt.PIRATES, "", count, 0, "Bring down " + count + " pirates", 15 + count * 2, rare, rareCount);
			}
		};
	}

	/** Every creature a BEAST hunt can name that this game really has. */
	public static List<String> beastPool(List<RogueData> rogues) {
		LinkedHashSet<String> ids = new LinkedHashSet<>(List.of(BEASTS));
		for (RogueData rogue : rogues) {
			ids.addAll(rogue.beasts);
			ids.addAll(rogue.lairBeasts);
		}
		List<String> pool = new ArrayList<>();
		for (String id : ids) {
			Identifier parsed = Identifier.tryParse(id);
			if (parsed != null && BuiltInRegistries.ENTITY_TYPE.containsKey(parsed)) {
				pool.add(id);
			}
		}
		return pool;
	}

	/** "onepiece:sea_cat" -> "Sea Cats". */
	static String beastName(String id) {
		String path = id.contains(":") ? id.substring(id.indexOf(':') + 1) : id;
		StringBuilder name = new StringBuilder();
		for (String word : path.split("_")) {
			if (!word.isEmpty()) {
				name.append(name.isEmpty() ? "" : " ").append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
			}
		}
		return name + "s";
	}

	private static <T> T pick(List<T> list, RandomSource random) {
		return list.get(random.nextInt(list.size()));
	}

	// ---- The player's side ----

	public static Hunt active(Player player) {
		return player.getAttached(ACTIVE);
	}

	public static int handedIn(Player player) {
		return player.getAttachedOrElse(DONE, 0);
	}

	private static List<String> takenToday(ServerPlayer player) {
		String today = day(player.level().getServer()) + ":";
		return player.getAttachedOrElse(TAKEN, List.<String>of()).stream().filter(id -> id.startsWith(today)).toList();
	}

	private static void markTaken(ServerPlayer player, String id) {
		List<String> taken = new ArrayList<>(takenToday(player));
		if (!taken.contains(id)) {
			taken.add(id);
		}
		player.setAttached(TAKEN, taken);
	}

	/** Right-clicking a board: hand in a finished hunt, then read today's hunts. */
	public static void use(ServerPlayer player, BlockPos pos) {
		LAST_BOARD.put(player.getUUID(), new Seen(player.level().dimension(), pos.immutable()));
		player.level().playSound(null, pos, SoundEvents.BOOK_PAGE_TURN, SoundSource.BLOCKS, 1.0f, 1.0f);
		Hunt hunt = active(player);
		if (hunt != null && hunt.done()) {
			handIn(player, hunt);
		}
		show(player);
	}

	private static void show(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		long left = DAY - server.overworld().getGameTime() % DAY;
		player.sendSystemMessage(Component.literal("=== Marine Bounty Board ===").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD)
				.append(Component.literal("  new hunts in " + Math.max(1, left / 1200) + " min").withStyle(Style.EMPTY.withBold(false).withColor(ChatFormatting.GRAY))));
		Hunt mine = active(player);
		List<String> taken = takenToday(player);
		List<Hunt> hunts = hunts(server);
		for (int i = 0; i < hunts.size(); i++) {
			Hunt hunt = hunts.get(i);
			MutableComponent line = Component.literal((i + 1) + ". ").withStyle(ChatFormatting.DARK_AQUA)
					.append(Component.literal(hunt.title()).withStyle(Hunt.BOSS.equals(hunt.kind()) ? ChatFormatting.RED : ChatFormatting.WHITE))
					.append(Component.literal("  " + reward(hunt)).withStyle(ChatFormatting.GOLD));
			if (mine != null && mine.id().equals(hunt.id())) {
				line.append(Component.literal("  [yours]").withStyle(ChatFormatting.GREEN));
			} else if (taken.contains(hunt.id())) {
				line.append(Component.literal("  [taken]").withStyle(ChatFormatting.DARK_GRAY));
			} else if (mine == null) {
				line.append(Component.literal("  [Take]").withStyle(Style.EMPTY.withColor(ChatFormatting.GREEN).withBold(true)
						.withClickEvent(new ClickEvent.RunCommand("/bountyboard take " + (i + 1)))));
			}
			player.sendSystemMessage(line);
		}
		if (mine != null) {
			player.sendSystemMessage(status(mine).append(Component.literal("  [Drop]").withStyle(Style.EMPTY.withColor(ChatFormatting.RED)
					.withClickEvent(new ClickEvent.RunCommand("/bountyboard drop")))));
		}
	}

	private static MutableComponent status(Hunt hunt) {
		return Component.literal("Your hunt: ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(hunt.title()).withStyle(ChatFormatting.YELLOW))
				.append(Component.literal(hunt.done() ? "  done! Hand it in at a Marine Bounty Board" : "  " + hunt.progress() + "/" + hunt.count())
						.withStyle(hunt.done() ? ChatFormatting.GREEN : ChatFormatting.GRAY));
	}

	/** "70 Berries + Rumor: Iron-Tide Graves". */
	public static String reward(Hunt hunt) {
		String text = hunt.berries() + " Berries";
		ItemStack rare = rareStack(hunt);
		if (!rare.isEmpty()) {
			text += " + " + (rare.getCount() > 1 ? rare.getCount() + " " : "") + rare.getHoverName().getString();
		}
		return text;
	}

	private static ItemStack rareStack(Hunt hunt) {
		if (hunt.rare().isEmpty() || hunt.rareCount() <= 0) {
			return ItemStack.EMPTY;
		}
		Identifier id = Identifier.tryParse(hunt.rare());
		if (id == null || !BuiltInRegistries.ITEM.containsKey(id)) {
			return ItemStack.EMPTY;
		}
		return new ItemStack(BuiltInRegistries.ITEM.getValue(id), hunt.rareCount());
	}

	/** Takes hunt number slot (1 to 5) from today's board. Null if it worked, or why not. */
	public static String take(ServerPlayer player, int slot) {
		Seen seen = LAST_BOARD.get(player.getUUID());
		if (seen == null || !seen.dimension.equals(player.level().dimension())
				|| !player.level().getBlockState(seen.pos).is(BLOCK)
				|| player.distanceToSqr(seen.pos.getX() + 0.5, seen.pos.getY() + 0.5, seen.pos.getZ() + 0.5) > BOARD_RANGE * BOARD_RANGE) {
			return "Stand by a Marine Bounty Board to take a hunt.";
		}
		Hunt current = active(player);
		if (current != null) {
			return current.done() ? "Hand in your finished hunt first: right-click the board." : "You already have a hunt. Finish it, or /bountyboard drop.";
		}
		List<Hunt> hunts = hunts(player.level().getServer());
		if (slot < 1 || slot > hunts.size()) {
			return "There's no hunt " + slot + " on the board.";
		}
		Hunt hunt = hunts.get(slot - 1);
		if (takenToday(player).contains(hunt.id())) {
			return "You already took that one today. New hunts go up tomorrow.";
		}
		player.setAttached(ACTIVE, hunt);
		markTaken(player, hunt.id());
		player.sendSystemMessage(Component.literal("Hunt taken: ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(hunt.title()).withStyle(ChatFormatting.YELLOW)));
		player.sendSystemMessage(Component.literal(howTo(hunt)).withStyle(ChatFormatting.GRAY));
		if (Hunt.BOSS.equals(hunt.kind()) && BossItems.RUMORS.containsKey(hunt.target())) {
			give(player, new ItemStack(BossItems.RUMORS.get(hunt.target())));
		}
		return null;
	}

	private static String howTo(Hunt hunt) {
		return switch (hunt.kind()) {
			case Hunt.BOSS -> "The Marines sent you their Rumor Poster: use it on a block to call " + OnePieceBridge.characterName(hunt.target())
					+ " out, or find them in their lair.";
			case Hunt.RAIDERS -> "Rookie crews raid villages and towns. Defend one and beat its raiders.";
			case Hunt.BEAST -> "They've been attacking travellers out in the wild.";
			default -> "Any pirate counts: sea pirates, rogue crews, rookie raiders.";
		};
	}

	public static boolean drop(ServerPlayer player) {
		Hunt hunt = active(player);
		if (hunt == null) {
			return false;
		}
		player.removeAttached(ACTIVE);
		player.sendSystemMessage(Component.literal("You dropped: " + hunt.title()).withStyle(ChatFormatting.GRAY));
		return true;
	}

	private static void handIn(ServerPlayer player, Hunt hunt) {
		player.removeAttached(ACTIVE);
		int total = handedIn(player) + 1;
		player.setAttached(DONE, total);
		int berries = hunt.berries();
		while (berries > 0) {
			ItemStack stack = OnePieceBridge.berries(1);
			int count = Math.min(berries, stack.getMaxStackSize());
			stack.setCount(count);
			give(player, stack);
			berries -= count;
		}
		ItemStack rare = rareStack(hunt);
		MutableComponent paid = Component.literal("The Marines pay out: ").withStyle(ChatFormatting.AQUA)
				.append(Component.literal(hunt.berries() + " Berries").withStyle(ChatFormatting.GOLD));
		if (!rare.isEmpty()) {
			paid.append(Component.literal(" and " + (rare.getCount() > 1 ? rare.getCount() + " " : "") + rare.getHoverName().getString())
					.withStyle(ChatFormatting.LIGHT_PURPLE));
			give(player, rare);
		}
		player.sendSystemMessage(paid);
		player.sendSystemMessage(Component.literal("Hunts handed in: " + total).withStyle(ChatFormatting.GRAY));
		player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8f, 1.2f);
	}

	private static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack) && !stack.isEmpty()) {
			player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
		}
	}

	// ---- Progress ----

	private static void onDeath(ServerLevel level, LivingEntity entity, ServerPlayer killer) {
		if (entity instanceof RogueBossEntity boss) {
			if (!boss.isBoss()) {
				return;
			}
			// Everyone in on the fight counts it, like the main mod's boss rewards.
			List<ServerPlayer> credited = new ArrayList<>(level.getEntitiesOfClass(ServerPlayer.class,
					boss.getBoundingBox().inflate(BOSS_RANGE), p -> !p.isSpectator()));
			if (killer != null && !credited.contains(killer)) {
				credited.add(killer);
			}
			for (ServerPlayer player : credited) {
				Hunt hunt = active(player);
				if (hunt != null && Hunt.BOSS.equals(hunt.kind()) && hunt.target().equals(boss.getCharacterId())) {
					advance(player, hunt);
				}
			}
			return;
		}
		if (killer == null) {
			return;
		}
		Hunt hunt = active(killer);
		if (hunt == null || hunt.done()) {
			return;
		}
		boolean counts = switch (hunt.kind()) {
			case Hunt.RAIDERS -> entity instanceof RookieRaiderEntity;
			case Hunt.PIRATES -> OnePieceBridge.isPirateNpc(entity);
			case Hunt.BEAST -> hunt.target().equals(BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString());
			default -> false;
		};
		if (counts) {
			advance(killer, hunt);
		}
	}

	private static void advance(ServerPlayer player, Hunt hunt) {
		if (hunt.done()) {
			return;
		}
		Hunt next = hunt.withProgress(hunt.progress() + 1);
		player.setAttached(ACTIVE, next);
		if (next.done()) {
			player.sendSystemMessage(Component.literal("[Bounty] ").withStyle(ChatFormatting.AQUA)
					.append(Component.literal(next.title() + " - done! Hand it in at a Marine Bounty Board.").withStyle(ChatFormatting.GREEN)));
			player.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 0.6f, 1.0f);
		} else {
			player.sendSystemMessage(Component.literal("Bounty hunt: " + next.progress() + "/" + next.count()).withStyle(ChatFormatting.AQUA), true);
		}
	}

	// ---- /bountyboard ----

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("bountyboard")
						.executes(c -> {
							ServerPlayer player = c.getSource().getPlayerOrException();
							Hunt hunt = active(player);
							player.sendSystemMessage(hunt != null ? status(hunt)
									: Component.literal("No hunt. Right-click a Marine Bounty Board to find one.").withStyle(ChatFormatting.GRAY));
							return hunt != null ? 1 : 0;
						})
						.then(Commands.literal("take").then(Commands.argument("hunt", IntegerArgumentType.integer(1, SLOTS)).executes(c -> {
							ServerPlayer player = c.getSource().getPlayerOrException();
							String error = take(player, IntegerArgumentType.getInteger(c, "hunt"));
							if (error != null) {
								player.sendSystemMessage(Component.literal(error).withStyle(ChatFormatting.GRAY));
							}
							return error == null ? 1 : 0;
						})))
						.then(Commands.literal("drop").executes(c -> {
							ServerPlayer player = c.getSource().getPlayerOrException();
							if (!drop(player)) {
								player.sendSystemMessage(Component.literal("You don't have a hunt.").withStyle(ChatFormatting.GRAY));
								return 0;
							}
							return 1;
						}))));
	}
}
