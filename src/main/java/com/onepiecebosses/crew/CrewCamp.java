package com.onepiecebosses.crew;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;

import com.onepiecebosses.BossItems;
import com.onepiecebosses.compat.OnePieceBridge;

/**
 * A rival crew's camp, built where they've stopped: a campfire with log seats, a tent in the crew's colour with the
 * treasure chest and bedrolls inside, their flag on a pole, a stack of barrels and crates of plunder, a weapon rack
 * and lantern posts. About 13 by 13 blocks.
 *
 * The chest holds what they've plundered: Berries, gold, emeralds, sometimes a diamond, a golden apple, or a Rumor
 * Poster for one of the rogue bosses. It's a plain chest; the crew standing over it is the lock.
 */
public final class CrewCamp {
	private CrewCamp() {
	}

	/** Footprint around the campfire: x -6..6, z -5..7. */
	private static final int X0 = -6, X1 = 6, Z0 = -5, Z1 = 7;

	/**
	 * Builds a camp with its campfire at ground (the air block above the ground). Returns the chest, or null if the
	 * ground isn't flat and dry enough (every column within one block of the campfire's height, no water).
	 */
	public static BlockPos build(ServerLevel level, BlockPos ground, RivalCrews.Rival rival, RandomSource random) {
		int y = ground.getY();
		for (int dx = X0; dx <= X1; dx++) {
			for (int dz = Z0; dz <= Z1; dz++) {
				int x = ground.getX() + dx, z = ground.getZ() + dz;
				if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
					return null;
				}
				int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
				BlockPos below = new BlockPos(x, top - 1, z);
				if (Math.abs(top - y) > 1 || !level.getFluidState(below).isEmpty() || !level.getFluidState(below.above()).isEmpty()) {
					return null;
				}
			}
		}
		DyeColor dye = DyeColor.byName(rival.color, DyeColor.BLACK);
		Block wool = Blocks.WOOL.pick(dye);
		Block carpet = Blocks.CARPET.pick(dye);
		Block banner = Blocks.BANNER.pick(dye);

		// Level the ground: fill dips, clear bumps and plants, a trodden dirt floor around the fire.
		for (int dx = X0; dx <= X1; dx++) {
			for (int dz = Z0; dz <= Z1; dz++) {
				BlockPos floor = ground.offset(dx, -1, dz);
				if (level.getBlockState(floor).getCollisionShape(level, floor).isEmpty()) {
					set(level, floor, Blocks.DIRT);
				}
				for (int up = 0; up <= 4; up++) {
					set(level, ground.offset(dx, up, dz), Blocks.AIR);
				}
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d <= 3.2 && random.nextInt(5) != 0) {
					set(level, floor, random.nextInt(3) == 0 ? Blocks.COARSE_DIRT : Blocks.DIRT_PATH);
				} else if (d <= 4.5 && random.nextInt(3) == 0) {
					set(level, floor, Blocks.COARSE_DIRT);
				}
			}
		}

		// The fire, its stone ring, log seats and a cooking pot.
		set(level, ground, Blocks.CAMPFIRE);
		for (int[] o : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
			set(level, ground.offset(o[0], -1, o[1]), Blocks.COBBLESTONE);
		}
		set(level, ground.offset(2, 0, -1), Blocks.STRIPPED_SPRUCE_LOG);
		set(level, ground.offset(-2, 0, -1), Blocks.STRIPPED_SPRUCE_LOG);
		set(level, ground.offset(-1, 0, -2), Blocks.STRIPPED_OAK_LOG);
		set(level, ground.offset(1, 0, -2), Blocks.SPRUCE_STAIRS);
		set(level, ground.offset(2, 0, 1), Blocks.CAULDRON);

		// The tent: an A-frame of the crew's colour running east-west, open at both ends.
		BlockPos tent = ground.offset(0, 0, 4);
		for (int dx = -3; dx <= 3; dx++) {
			set(level, tent.offset(dx, 0, -2), wool);
			set(level, tent.offset(dx, 1, -1), wool);
			set(level, tent.offset(dx, 2, 0), wool);
			set(level, tent.offset(dx, 1, 1), wool);
			set(level, tent.offset(dx, 0, 2), wool);
			set(level, tent.offset(dx, -1, -1), Blocks.SPRUCE_PLANKS);
			set(level, tent.offset(dx, -1, 0), Blocks.SPRUCE_PLANKS);
			set(level, tent.offset(dx, -1, 1), Blocks.SPRUCE_PLANKS);
		}
		// Poles at the ends, holding up the ridge.
		set(level, tent.offset(-4, 0, 0), Blocks.SPRUCE_FENCE);
		set(level, tent.offset(-4, 1, 0), Blocks.SPRUCE_FENCE);
		set(level, tent.offset(-4, 2, 0), Blocks.SPRUCE_FENCE);
		set(level, tent.offset(4, 0, 0), Blocks.SPRUCE_FENCE);
		set(level, tent.offset(4, 1, 0), Blocks.SPRUCE_FENCE);
		set(level, tent.offset(4, 2, 0), Blocks.SPRUCE_FENCE);
		// Bedrolls and a lantern inside.
		set(level, tent.offset(-2, 0, -1), carpet);
		set(level, tent.offset(-2, 0, 1), carpet);
		set(level, tent.offset(2, 0, -1), carpet);
		set(level, tent.offset(2, 0, 1), carpet);
		set(level, tent.offset(-1, 1, 0), Blocks.LANTERN.defaultBlockState().setValue(net.minecraft.world.level.block.LanternBlock.HANGING, true));
		// The treasure, under the ridge (a chest won't open with wool right on top of it).
		BlockPos chest = tent;
		level.setBlock(chest, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.NORTH), Block.UPDATE_ALL);
		fill(level, chest, random);
		set(level, tent.offset(1, 0, 1), Blocks.BARREL);

		// The flag on a tall pole.
		BlockPos pole = ground.offset(-5, 0, -3);
		for (int up = 0; up < 5; up++) {
			set(level, pole.above(up), Blocks.SPRUCE_FENCE);
		}
		set(level, pole.above(5), banner);
		set(level, pole.below(), Blocks.COBBLESTONE);

		// Plunder: barrels, crates and a hay bale.
		set(level, ground.offset(5, 0, -4), Blocks.BARREL);
		set(level, ground.offset(5, 1, -4), Blocks.BARREL);
		set(level, ground.offset(4, 0, -4), Blocks.BARREL);
		set(level, ground.offset(5, 0, -3), Blocks.SPRUCE_PLANKS);
		set(level, ground.offset(4, 0, -3), Blocks.HAY_BLOCK);
		set(level, ground.offset(3, 0, -4), Blocks.COMPOSTER);
		set(level, ground.offset(5, 0, -2), Blocks.BARREL);
		set(level, ground.offset(5, 1, -3), Blocks.OAK_TRAPDOOR);

		// A weapon rack: an anvil and a grindstone by the fire.
		set(level, ground.offset(-4, 0, -1), Blocks.GRINDSTONE);
		set(level, ground.offset(-4, 0, 0), Blocks.ANVIL);
		set(level, ground.offset(-4, 0, 1), Blocks.SMITHING_TABLE);

		// Lantern posts at the front corners.
		for (int side : new int[] {-1, 1}) {
			BlockPos post = ground.offset(side * 6, 0, -5);
			set(level, post, Blocks.SPRUCE_FENCE);
			set(level, post.above(), Blocks.SPRUCE_FENCE);
			set(level, post.above(2), Blocks.LANTERN);
		}
		return chest;
	}

	private static void set(ServerLevel level, BlockPos pos, Block block) {
		set(level, pos, block.defaultBlockState());
	}

	private static void set(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state, Block.UPDATE_ALL);
	}

	/** The crew's plunder, spread around the chest. */
	static void fill(ServerLevel level, BlockPos pos, RandomSource random) {
		if (!(level.getBlockEntity(pos) instanceof ChestBlockEntity chest)) {
			return;
		}
		List<ItemStack> loot = new ArrayList<>();
		loot.add(OnePieceBridge.berries(20 + random.nextInt(41)));
		loot.add(new ItemStack(Items.GOLD_INGOT, 2 + random.nextInt(5)));
		loot.add(new ItemStack(Items.EMERALD, 1 + random.nextInt(4)));
		loot.add(new ItemStack(Items.GOLD_NUGGET, 4 + random.nextInt(12)));
		if (random.nextFloat() < 0.6f) {
			loot.add(new ItemStack(Items.GUNPOWDER, 2 + random.nextInt(5)));
		}
		if (random.nextFloat() < 0.5f) {
			loot.add(new ItemStack(Items.COOKED_BEEF, 3 + random.nextInt(5)));
		}
		if (random.nextFloat() < 0.3f) {
			loot.add(new ItemStack(Items.GOLDEN_APPLE));
		}
		if (random.nextFloat() < 0.15f) {
			loot.add(new ItemStack(Items.DIAMOND, 1 + random.nextInt(2)));
		}
		if (random.nextFloat() < 0.35f && !BossItems.RUMORS.isEmpty()) {
			List<Item> rumors = new ArrayList<>(BossItems.RUMORS.values());
			loot.add(new ItemStack(rumors.get(random.nextInt(rumors.size()))));
		}
		List<Integer> slots = new ArrayList<>();
		for (int i = 0; i < chest.getContainerSize(); i++) {
			slots.add(i);
		}
		for (ItemStack stack : loot) {
			if (stack.isEmpty() || slots.isEmpty()) {
				continue;
			}
			chest.setItem(slots.remove(random.nextInt(slots.size())), stack);
		}
	}
}
