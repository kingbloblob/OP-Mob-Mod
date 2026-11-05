package com.onepiecebosses.gear;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

import com.onepiecebosses.boss.RogueData;

/** A boss's Remnant, armour piece or weapon. Its tooltip says where it comes from and what the full set does. */
public class GearItem extends Item {
	public enum Kind { REMNANT, ARMOR, WEAPON }

	private final GearData data;
	private final Kind kind;

	public GearItem(GearData data, Kind kind, Properties properties) {
		super(properties);
		this.data = data;
		this.kind = kind;
	}

	public GearData data() {
		return data;
	}

	public Kind kind() {
		return kind;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		RogueData boss = RogueData.get(data.boss);
		String bossName = boss != null ? boss.name() : data.boss;
		switch (kind) {
			case REMNANT -> {
				textConsumer.accept(Component.literal("Dropped by " + bossName + " every time they're beaten").withStyle(ChatFormatting.GRAY));
				textConsumer.accept(Component.literal("Craft with a diamond helmet, chestplate, leggings, boots or sword").withStyle(ChatFormatting.DARK_GRAY));
				textConsumer.accept(Component.literal("(three Remnants each) for the " + data.setName + " gear").withStyle(ChatFormatting.DARK_GRAY));
			}
			case ARMOR -> {
				textConsumer.accept(Component.literal(data.setName + " set (" + bossName + ")").withStyle(ChatFormatting.GOLD));
				textConsumer.accept(Component.literal("Full set: " + passiveText()).withStyle(ChatFormatting.GRAY));
				textConsumer.accept(Component.literal(data.move + ": ").withStyle(ChatFormatting.RED)
						.append(Component.literal(data.moveText).withStyle(ChatFormatting.GRAY)));
				textConsumer.accept(Component.literal("Unleashed by a full-strength hit, every " + GearSets.COOLDOWN_SECONDS
						+ "s (" + GearSets.WEAPON_COOLDOWN_SECONDS + "s holding the " + data.weaponName + ")").withStyle(ChatFormatting.DARK_GRAY));
			}
			case WEAPON -> {
				textConsumer.accept(Component.literal("Forged from " + bossName + "'s Remnants").withStyle(ChatFormatting.GRAY));
				textConsumer.accept(Component.literal("With the full " + data.setName + " set, " + data.move + " comes back every "
						+ GearSets.WEAPON_COOLDOWN_SECONDS + "s").withStyle(ChatFormatting.DARK_GRAY));
			}
		}
	}

	private String passiveText() {
		if (data.passives.isEmpty()) {
			return "nothing extra";
		}
		StringBuilder text = new StringBuilder();
		for (var passive : data.passives) {
			if (!text.isEmpty()) {
				text.append(", ");
			}
			String effect = String.valueOf(passive.get(0)).replace('_', ' ');
			int level = ((Number) passive.get(1)).intValue() + 1;
			text.append(Character.toUpperCase(effect.charAt(0))).append(effect.substring(1));
			if (level > 1) {
				text.append(' ').append(level == 2 ? "II" : "III");
			}
			String when = passive.size() > 2 ? String.valueOf(passive.get(2)) : "always";
			if (when.equals("water")) {
				text.append(" in water");
			} else if (when.equals("falling")) {
				text.append(" while falling");
			}
		}
		return text.toString();
	}
}
