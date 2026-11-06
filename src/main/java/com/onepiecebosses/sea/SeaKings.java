package com.onepiecebosses.sea;

import java.util.LinkedHashMap;
import java.util.Map;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;

import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecebosses.BossesMod;
import com.onepiecemod.sea.SeaKingEntity;

/** Registers the Sea King mini-bosses (one mob type each, so each has its own name, model and loot) and their trophies. */
public final class SeaKings {
	private SeaKings() {
	}

	public static final Map<SeaKingBossEntity.Kind, EntityType<SeaKingBossEntity>> TYPES = new LinkedHashMap<>();
	/** Kind -> its trophy (always dropped, see its loot table). */
	public static final Map<SeaKingBossEntity.Kind, Item> TROPHIES = new LinkedHashMap<>();
	private static final Map<SeaKingBossEntity.Kind, String> TROPHY_IDS = Map.of(
			SeaKingBossEntity.Kind.GULPMAW, "gulpmaw_lure",
			SeaKingBossEntity.Kind.IRONSCALE, "ironscale_plate",
			SeaKingBossEntity.Kind.THUNDERCOIL, "thundercoil_fang");

	static void initialize() {
		for (SeaKingBossEntity.Kind kind : SeaKingBossEntity.Kind.values()) {
			ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, BossesMod.id(kind.id));
			EntityType<SeaKingBossEntity> type = Registry.register(BuiltInRegistries.ENTITY_TYPE, key,
					EntityType.Builder.<SeaKingBossEntity>of(SeaKingBossEntity::new, MobCategory.MONSTER)
							.sized(4.0f, 3.2f) // Bigger than a plain Sea King (2.5 x 2.4); the model is drawn about 3x.
							.eyeHeight(2.0f)
							.clientTrackingRange(16)
							.build(key));
			TYPES.put(kind, type);
			FabricDefaultAttributeRegistry.register(type, SeaKingEntity.createAttributes()
					.add(Attributes.MAX_HEALTH, kind.health)
					.add(Attributes.ATTACK_DAMAGE, kind.damage)
					.add(Attributes.ARMOR, kind.armor)
					.add(Attributes.FOLLOW_RANGE, 64.0)
					.add(Attributes.MOVEMENT_SPEED, 1.4));

			ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, BossesMod.id(TROPHY_IDS.get(kind)));
			TROPHIES.put(kind, Registry.register(BuiltInRegistries.ITEM, itemKey,
					new Item(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).setId(itemKey))));
		}
	}
}
