package com.onepiecebosses.boss;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;

import com.onepiecebosses.compat.OnePieceBridge;

/**
 * A Rumor Poster: the rogue bosses' Wanted Poster. Use it on a block and the boss appears.
 * Beat them and the poster brings them back on Hard, then Expert. Sneak while using it for a Normal fight.
 */
public class RumorPosterItem extends Item {
	private final String bossId;

	public RumorPosterItem(String bossId, Properties properties) {
		super(properties);
		this.bossId = bossId;
	}

	public String bossId() {
		return bossId;
	}

	@Override
	public Component getName(ItemStack stack) {
		return Component.literal("Rumor: " + RogueData.get(bossId).name());
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		RogueData boss = RogueData.get(bossId);
		textConsumer.accept(Component.literal("Tier " + boss.tier() + " rogue").withStyle(ChatFormatting.RED));
		textConsumer.accept(Component.literal(boss.lore).withStyle(ChatFormatting.GRAY));
		textConsumer.accept(Component.literal("Use on a block to call them out. Sneak for a Normal fight.").withStyle(ChatFormatting.DARK_GRAY));
		if (com.onepiecebosses.sea.BossShips.shipOf(bossId) != null) {
			textConsumer.accept(Component.literal("Use it while sailing and their flagship comes for you instead.").withStyle(ChatFormatting.DARK_AQUA));
		}
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (context.getLevel() instanceof ServerLevel level) {
			// A flagship's captain, called while sailing: her ship comes for you (sea/BossShips) instead.
			String flagship = com.onepiecebosses.sea.BossShips.shipOf(bossId);
			if (flagship != null && context.getPlayer() instanceof net.minecraft.server.level.ServerPlayer sailor
					&& com.onepiecemod.ship.ShipEntity.aboard(sailor) != null) {
				if (com.onepiecebosses.sea.SeaBosses.sendShip(level, sailor, flagship) != null) {
					if (!sailor.isCreative()) {
						context.getItemInHand().shrink(1);
					}
				} else {
					sailor.sendOverlayMessage(Component.literal("Her sails won't show here: sail out into open, deep sea.")
							.withStyle(ChatFormatting.YELLOW));
				}
				return InteractionResult.SUCCESS;
			}
			RogueBossEntity boss = RogueBosses.ROGUE_BOSS.create(level, EntitySpawnReason.SPAWN_ITEM_USE);
			if (boss != null) {
				BlockPos pos = context.getClickedPos().relative(context.getClickedFace());
				boss.setPos(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
				Player player = context.getPlayer();
				if (player != null) {
					// Face the player who used the poster.
					boss.setYRot(player.getYRot() + 180);
					boss.setYHeadRot(boss.getYRot());
				}
				boss.setCharacter(bossId, true);
				if (player != null && !player.isShiftKeyDown()) {
					boss.setDifficulty(OnePieceBridge.unlockedDifficulty(player, bossId));
				}
				level.addFreshEntity(boss);

				if (player == null || !player.isCreative()) {
					context.getItemInHand().shrink(1);
				}
			}
		}
		return InteractionResult.SUCCESS;
	}
}
