package com.onepiecebosses.gear;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecebosses.BossesMod;
import com.onepiecebosses.boss.RogueData;

/**
 * The boss gear: for every set in gear.json, the boss's Remnant (dropped every time it's beaten), four armour pieces
 * and a weapon. Recipes are in data/opbosses/recipe (tools/gen_gear.py writes them): a diamond piece and three Remnants.
 * Tougher bosses make tougher gear.
 */
public final class GearItems {
	private GearItems() {
	}

	/** One boss's items. armor is helmet, chestplate, leggings, boots. */
	public record Set(GearData data, Item remnant, Item[] armor, Item weapon) {
	}

	/** Boss id -> its set. */
	public static final Map<String, Set> SETS = new LinkedHashMap<>();

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), BossesMod.id("gear"));

	private static final ArmorType[] PIECES = {ArmorType.HELMET, ArmorType.CHESTPLATE, ArmorType.LEGGINGS, ArmorType.BOOTS};
	private static final String[] PIECE_IDS = {"helmet", "chestplate", "leggings", "boots"};

	public static void initialize() {
		for (GearData data : GearData.all().values()) {
			RogueData boss = RogueData.get(data.boss);
			if (boss == null) {
				// A set made ahead for a boss another branch adds. Its recipes only load once its items exist.
				BossesMod.LOGGER.info("gear.json: no boss {} in bosses.json yet, skipping its set", data.boss);
				continue;
			}
			int tier = boss.tier();
			Rarity rarity = tier >= 4 ? Rarity.EPIC : tier >= 3 ? Rarity.RARE : Rarity.UNCOMMON;
			Item remnant = register(data.remnant(), p -> new GearItem(data, GearItem.Kind.REMNANT, p),
					new Item.Properties().rarity(rarity));

			ArmorMaterial material = material(data.set, tier);
			Item[] armor = new Item[4];
			for (int i = 0; i < 4; i++) {
				Item.Properties properties = new Item.Properties().humanoidArmor(material, PIECES[i]).rarity(rarity);
				if (tier >= 4) {
					properties.fireResistant();
				}
				armor[i] = register(data.set + "_" + PIECE_IDS[i], p -> new GearItem(data, GearItem.Kind.ARMOR, p), properties);
			}

			// The sword stats: diamond up to tier 3, netherite above, with a little more bite each tier.
			// Hammers and mauls hit harder and slower; rapiers and lasers lighter and faster.
			ToolMaterial tool = tier >= 4 ? ToolMaterial.NETHERITE : ToolMaterial.DIAMOND;
			float damage = 3.0f + 0.5f * (tier - (tier >= 4 ? 3 : 1));
			float speed = -2.4f;
			switch (data.weaponShape) {
				case "hammer", "anchor", "halberd" -> { damage += 2.0f; speed = -3.0f; }
				case "rapier", "laser", "claw", "mic" -> { damage -= 1.0f; speed = -1.9f; }
				case "katana", "scimitar" -> speed = -2.2f;
				case "harpoon", "trident", "drill" -> { damage += 1.0f; speed = -2.7f; }
				default -> { }
			}
			Item.Properties weaponProperties = new Item.Properties().sword(tool, damage, speed).rarity(rarity);
			if (tier >= 4) {
				weaponProperties.fireResistant();
			}
			Item weapon = register(data.weapon, p -> new GearItem(data, GearItem.Kind.WEAPON, p), weaponProperties);

			SETS.put(data.boss, new Set(data, remnant, armor, weapon));
		}

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(SETS.values().iterator().next().armor()[0]))
				.title(Component.literal("One Piece: Boss Gear"))
				.displayItems((params, output) -> {
					for (Set set : SETS.values()) {
						output.accept(set.remnant());
						for (Item piece : set.armor()) {
							output.accept(piece);
						}
						output.accept(set.weapon());
					}
				})
				.build());
	}

	/** Diamond's defence (3, 8, 6, 3) on every tier; durability, toughness and knockback resistance rise with it. */
	private static ArmorMaterial material(String set, int tier) {
		int durability = switch (tier) {
			case 1, 2 -> 33;
			case 3 -> 35;
			case 4 -> 37;
			default -> 40;
		};
		float toughness = switch (tier) {
			case 1, 2 -> 2.0f;
			case 3 -> 2.5f;
			case 4 -> 3.0f;
			default -> 3.5f;
		};
		float knockback = tier >= 5 ? 0.15f : tier >= 4 ? 0.1f : tier >= 3 ? 0.05f : 0.0f;
		ResourceKey<EquipmentAsset> asset = ResourceKey.create(EquipmentAssets.ROOT_ID, BossesMod.id(set));
		TagKey<Item> repair = TagKey.create(Registries.ITEM, BossesMod.id("repairs_" + set + "_armor"));
		return new ArmorMaterial(durability,
				Map.of(ArmorType.HELMET, 3, ArmorType.CHESTPLATE, 8, ArmorType.LEGGINGS, 6, ArmorType.BOOTS, 3, ArmorType.BODY, 8),
				10 + tier, tier >= 4 ? SoundEvents.ARMOR_EQUIP_NETHERITE : SoundEvents.ARMOR_EQUIP_DIAMOND, toughness, knockback, repair, asset);
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, BossesMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		return item;
	}

	/** The set whose armour or weapon this is, or null. */
	public static Set setOf(Item item) {
		if (item instanceof GearItem gear) {
			return SETS.get(gear.data().boss);
		}
		return null;
	}
}
