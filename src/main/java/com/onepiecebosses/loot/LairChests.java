package com.onepiecebosses.loot;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.PushReaction;

import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecebosses.BossesMod;

/**
 * Each lair's own chest block (opbosses:&lt;lair&gt;_chest; models and names from tools/gen_chests.py), and the rule that
 * keeps a locked chest shut: vanilla stops you opening a locked chest, but not breaking it and picking up what spills,
 * so a locked chest only breaks for someone who could open it (holding the key) or in creative.
 */
public final class LairChests {
	private LairChests() {
	}

	/** Each lair (by structure name) and its boss. Their chests are "<lair>_chest". */
	public static final Map<String, String> LAIR_BOSSES = new LinkedHashMap<>();
	static {
		String[][] pairs = {{"scrapheap_reef", "saltjaw_rourke"}, {"lantern_house", "corvina_fog_widow"}, {"fort_iron_tide", "iron_tide_graves"},
				{"hollow_shrine", "hollow_ronin_tsurugi"}, {"shipbreakers_foundry", "boilerheart_gantz"}, {"abyssal_temple", "nereus_vane"},
				{"sunken_kasbah", "khamsin_sandshackle"}, {"gilded_wake", "mortimer_gale"}, {"leviathan_pens", "vasco_tidebreaker"},
				{"laboratory_null", "doctor_kreuz"},
				{"gran_tesoro", "gild_tesoro"}, {"elegia_stage", "uta_diva"}, {"end_point", "zephyr_z"},
				{"ironclad_colosseum", "douglas_bullet"}, {"merveille", "shiki_golden_lion"},
				{"gold_island", "el_drago"}, {"salamander", "gasparde"}, {"omatsuri_island", "baron_omatsuri"},
				{"karakuri_castle", "ratchet"}, {"groseade", "byrnndi_world"},
				{"clockwork_island", "bear_king"}, {"delta_island", "buena_festa"}, {"asuka_island", "saga"},
				{"crown_island", "count_butler"}};
		for (String[] pair : pairs) {
			LAIR_BOSSES.put(pair[0], pair[1]);
		}
	}
	public static final List<String> LAIRS = List.copyOf(LAIR_BOSSES.keySet());

	/**
	 * The sea bosses' flagships (sea/BossShips) and their captains. Each has a strongroom chest, "<ship>_chest",
	 * locked to the captain's key like a lair's. Kept apart from LAIR_BOSSES: a ship isn't a structure the Lair
	 * Charter can reset, it sinks or docks wherever it was beaten.
	 */
	public static final Map<String, String> SHIP_BOSSES = new LinkedHashMap<>();
	static {
		SHIP_BOSSES.put("widowmaker", "maribel_sedge");
		SHIP_BOSSES.put("tithe_cathedral", "severo_lume");
		SHIP_BOSSES.put("cinderwake", "kael_ashgrave");
	}

	/** Lair name -> its chest block. */
	public static final Map<String, Block> BLOCKS = new LinkedHashMap<>();
	public static final Map<String, Item> ITEMS = new LinkedHashMap<>();
	public static BlockEntityType<LairChestBlockEntity> ENTITY;

	public static void initialize() {
		List<String> chests = new java.util.ArrayList<>(LAIRS);
		chests.addAll(SHIP_BOSSES.keySet());
		for (String lair : chests) {
			ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, BossesMod.id(lair + "_chest"));
			// Blast-proof and immovable, so the loot can't be blown or pushed out of a lair.
			Block block = Registry.register(BuiltInRegistries.BLOCK, key, new LairChestBlock(BlockBehaviour.Properties.of()
					.strength(2.5f, 3600000.0f).sound(SoundType.WOOD).noOcclusion().pushReaction(PushReaction.IMMOVEABLE)
					.lightLevel(state -> 4).setId(key)));
			BLOCKS.put(lair, block);
			ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, BossesMod.id(lair + "_chest"));
			ITEMS.put(lair, Registry.register(BuiltInRegistries.ITEM, itemKey,
					new BlockItem(block, new Item.Properties().rarity(Rarity.RARE).useBlockDescriptionPrefix().setId(itemKey))));
		}
		ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, BossesMod.id("lair_chest"),
				FabricBlockEntityTypeBuilder.create(LairChestBlockEntity::new, BLOCKS.values().toArray(new Block[0])).build());

		PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, blockEntity) ->
				player.isCreative() || !(blockEntity instanceof BaseContainerBlockEntity container) || container.canOpen(player));
	}
}
