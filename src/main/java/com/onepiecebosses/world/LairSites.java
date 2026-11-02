package com.onepiecebosses.world;

import com.mojang.datafixers.util.Either;
import com.onepiecebosses.BossesMod;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.TerrainAdjustment;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;

/**
 * Keeps our lairs off mountains and out of the sea (ryan 2026-11-01: "the lairs keep spawning in mountains").
 * Vanilla only checks the biome at a structure's middle, and our lairs are 70-120 blocks across, so a desert fort could
 * run up the side of the mountain next door. This samples the ground on a 7x7 grid over the lair's real footprint and,
 * if it's too steep or too wet (or, for a sea lair, too dry), slides the whole lair to the nearest spot within
 * {@link #MAX_SHIFT} blocks that fits. If none does, the lair isn't built there and the next spot in the set gets it.
 * A spot must also keep clear of the main mod's structures (LairNeighbours).
 * Hooked around the calls to Structure.findValidGenerationPoint in Structure.generate and StructureCheck (LairSiteMixin,
 * StructureCheckSiteMixin), so /locate agrees with world generation; /place
 * structure skips it (PlaceCommandMixin).
 * -Dopbosses.siteRules=false turns it off.
 */
public final class LairSites {
	private LairSites() {}

	private static final boolean ENABLED = !"false".equals(System.getProperty("opbosses.siteRules"));
	private static final boolean DEBUG = Boolean.getBoolean("opbosses.siteDebug");

	/** Samples per side: 7 x 7 over the footprint and its margin, about one every 15 blocks on our biggest lair. */
	private static final int GRID = 7;
	/** Most a land lair's ground may rise and fall across its footprint (the highest and lowest samples are ignored). */
	public static final int MAX_SPREAD = 8;
	/** How far past the lair's edge the grid reaches, so a cliff right at its wall counts too. */
	private static final int MARGIN = 12;
	/** Most even the single highest sample may stand over the lair's floor: one tall hill at the wall is enough to say no. */
	private static final int MAX_RISE = 12;
	/** Most of the 49 samples under a land lair that may be water. */
	private static final int MAX_WET = 6;
	/** Fewest of the 49 samples under a sea lair that must be water (most of it: reef and beach lairs keep a bit of shore). */
	private static final int MIN_WET_SEA = 29;
	/**
	 * Most the dry ground under and round a sea lair may stand over the sea (the highest sample is ignored, a lone
	 * rock). A sea lair isn't fitted to the land, so a hill in its footprint was dug straight through: ryan 2026-11-02
	 * found the Scrapheap Reef cut into a hillside under a castle. Beaches and low shores still pass.
	 */
	private static final int MAX_SEA_SHORE = 5;
	private static final int STEP = 16;
	/** Furthest a lair slides to find flat ground. */
	private static final int MAX_SHIFT = 48;
	/** A chunk looks 8 chunks around for structure starts; one chunk of slack. */
	private static final int REACH = 7;

	/** True while /place structure runs on this thread: a lair placed by hand goes exactly where it's asked. */
	public static final ThreadLocal<Boolean> PLACING = ThreadLocal.withInitial(() -> false);

	public static Optional<Structure.GenerationStub> filter(Structure structure, Structure.GenerationContext ctx,
			Optional<Structure.GenerationStub> found) {
		if (!ENABLED || found.isEmpty() || PLACING.get()) return found;
		Identifier id = ctx.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(structure);
		if (id == null || !id.getNamespace().equals(BossesMod.MOD_ID)) return found;
		boolean sea = structure.terrainAdaptation() == TerrainAdjustment.NONE;

		Structure.GenerationStub stub = found.get();
		// Lay the pieces out once for the real footprint; the builder is handed on so they aren't laid out twice.
		StructurePiecesBuilder builder = stub.getPiecesBuilder();
		if (builder.isEmpty()) return found;
		BoundingBox box = builder.getBoundingBox();
		BlockPos start = stub.position();
		// A chunk only looks REACH chunks around itself for structure starts, so every part of the lair must stay within
		// that many chunks of its start chunk, or the far pieces are never built (Ironclad lost its chest that way).
		int sx = ctx.chunkPos().getMinBlockX(), sz = ctx.chunkPos().getMinBlockZ();
		int minX = sx - REACH * 16, maxX = sx + 15 + REACH * 16, minZ = sz - REACH * 16, maxZ = sz + 15 + REACH * 16;
		int shift = MAX_SHIFT;
		// Other structures near the lair (LairNeighbours), worked out only once a spot passes the ground check: it lays
		// out the main mod's builds round about, which is far slower than sampling the ground.
		List<BoundingBox> neighbours = null;

		for (int[] o : spiral(shift)) {
			BoundingBox moved = box.moved(o[0], 0, o[1]);
			if ((o[0] != 0 || o[1] != 0) && (moved.minX() < minX || moved.maxX() > maxX || moved.minZ() < minZ || moved.maxZ() > maxZ)) continue;
			Ground g = sample(ctx, box.moved(o[0], 0, o[1]));
			int seaLevel = ctx.chunkGenerator().getSeaLevel();
			boolean fits = sea ? g.wet >= MIN_WET_SEA && g.shore(seaLevel) <= MAX_SEA_SHORE
					: g.wet <= MAX_WET && g.spread() <= MAX_SPREAD && g.peak() <= MAX_RISE;
			if (DEBUG) BossesMod.LOGGER.info("lair site {} at {} {} offset {},{}: wet {} spread {} peak {} shore {} -> {}", id.getPath(),
					start.getX(), start.getZ(), o[0], o[1], g.wet, g.spread(), g.peak(), g.shore(seaLevel), fits);
			if (!fits) continue;
			if (neighbours == null) neighbours = LairNeighbours.blockers(ctx, box, MAX_SHIFT);
			if (!LairNeighbours.clear(moved, neighbours)) {
				if (DEBUG) BossesMod.LOGGER.info("lair site {} offset {},{}: too close to another structure", id.getPath(), o[0], o[1]);
				continue;
			}
			int dy = 0;
			if (!sea) {
				// Sit the lair on the ground under the footprint (a little low, so the yard cuts into the slope rather
				// than floating over it), not on whatever the single column under its start point was.
				int now = ctx.chunkGenerator().getFirstFreeHeight(start.getX(), start.getZ(), Heightmap.Types.WORLD_SURFACE_WG,
						ctx.heightAccessor(), ctx.randomState());
				dy = Math.max(-12, Math.min(12, g.low() - now));
			}
			if (o[0] != 0 || o[1] != 0 || dy != 0) {
				for (StructurePiece piece : builder.build().pieces()) piece.move(o[0], dy, o[1]);
				start = start.offset(o[0], dy, o[1]);
			}
			return Optional.of(new Structure.GenerationStub(start, Either.right(builder)));
		}
		return Optional.empty();
	}

	private record Ground(List<Integer> dry, int wet) {
		/** Rise and fall of the dry ground, ignoring the highest and lowest sample (a lone rock, a gully). */
		int spread() {
			return dry.size() < 5 ? 0 : dry.get(dry.size() - 2) - dry.get(1);
		}

		/** How far the highest sample stands over the floor the lair will sit on. */
		int peak() {
			return dry.isEmpty() ? 0 : dry.get(dry.size() - 1) - low();
		}

		/** How far the dry ground stands over the sea, ignoring the single highest sample. */
		int shore(int seaLevel) {
			return dry.size() < 2 ? 0 : dry.get(dry.size() - 2) - seaLevel;
		}

		/** The lower third of the dry ground. */
		int low() {
			return dry.isEmpty() ? 0 : dry.get(dry.size() * 3 / 10);
		}
	}

	private static Ground sample(Structure.GenerationContext ctx, BoundingBox box) {
		int sea = ctx.chunkGenerator().getSeaLevel();
		int x0 = box.minX() - MARGIN, x1 = box.maxX() + MARGIN, z0 = box.minZ() - MARGIN, z1 = box.maxZ() + MARGIN;
		List<Integer> dry = new ArrayList<>();
		int wet = 0;
		for (int i = 0; i < GRID; i++) {
			for (int j = 0; j < GRID; j++) {
				int x = x0 + (x1 - x0) * i / (GRID - 1), z = z0 + (z1 - z0) * j / (GRID - 1);
				int h = height(ctx, x, z);
				if (h >= sea) dry.add(h);
				else wet++;
			}
		}
		Collections.sort(dry);
		return new Ground(dry, wet);
	}

	/** Ground heights already worked out, per world: neighbouring candidates sample the same ground over and over, and
	 * sampling the noise is the slow part. Points snap to a 4-block grid, far finer than the sample grid. */
	private static final Map<RandomState, ConcurrentHashMap<Long, Integer>> HEIGHTS = Collections.synchronizedMap(new WeakHashMap<>());

	private static int height(Structure.GenerationContext ctx, int x, int z) {
		ConcurrentHashMap<Long, Integer> cache = HEIGHTS.computeIfAbsent(ctx.randomState(), r -> new ConcurrentHashMap<>());
		if (cache.size() > 200_000) cache.clear();
		int sx = (x & ~3) + 2, sz = (z & ~3) + 2;
		long key = ((long) sx << 32) ^ (sz & 0xFFFFFFFFL);
		Integer h = cache.get(key);
		if (h == null) {
			h = ctx.chunkGenerator().getFirstFreeHeight(sx, sz, Heightmap.Types.OCEAN_FLOOR_WG, ctx.heightAccessor(), ctx.randomState());
			cache.put(key, h);
		}
		return h;
	}

	/** Offsets to try, the original spot first, then rings out to `max` blocks. */
	private static List<int[]> spiral(int max) {
		List<int[]> out = new ArrayList<>();
		out.add(new int[] {0, 0});
		for (int r = STEP; r <= max; r += STEP) {
			for (int dx = -r; dx <= r; dx += STEP) {
				for (int dz = -r; dz <= r; dz += STEP) {
					if (Math.max(Math.abs(dx), Math.abs(dz)) == r) out.add(new int[] {dx, dz});
				}
			}
		}
		return out;
	}
}
