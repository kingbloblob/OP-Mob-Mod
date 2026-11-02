package com.onepiecebosses.world;

import com.onepiecebosses.BossesMod;
import com.onepiecebosses.compat.OnePieceBridge;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.Holder;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.LegacyRandomSource;
import net.minecraft.world.level.levelgen.WorldgenRandom;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.placement.ConcentricRingsStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacement;

/**
 * Keeps our lairs clear of the One Piece Mod's own structures (ryan 2026-11-02: a lair was dug into the hill right
 * under a castle). Vanilla only keeps structures of one set apart, and the main mod's spacing only knows its own sets,
 * so nothing stopped a lair landing on top of a town or a castle. Here a lair looks at the main mod's structure starts
 * around it (and vanilla villages and outposts), works out what each one really generates there (biome, the main
 * mod's own ground check and slide, so the same answer whichever chunk generates first), and LairSites only takes a
 * spot that keeps {@link #GAP} blocks from all of them. The main mod's builds don't look at lairs, so lairs always give way.
 * -Dopbosses.structureGap=0 turns it off.
 */
public final class LairNeighbours {
	private LairNeighbours() {}

	/** Blocks of open ground a lair keeps from another structure's footprint. */
	public static final int GAP = Integer.getInteger("opbosses.structureGap", 32);
	/** How far another structure's footprint can reach from its start chunk: half the main mod's widest build plus its slide. */
	private static final int NEIGHBOUR_REACH = 128 + 112;
	/** The main mod's sets that never meet a lair: underground caves, the sea-floor trench, the Nether and the End. */
	private static final Set<String> SKIP = Set.of("underground_locations", "deep_trench_locations", "nether_locations", "end_locations");
	/** Vanilla sets with buildings on the surface worth keeping clear of. */
	private static final Set<String> VANILLA = Set.of("villages", "pillager_outposts");
	private static final boolean DEBUG = Boolean.getBoolean("opbosses.siteDebug");

	private static final Map<BiomeSource, World> WORLDS = Collections.synchronizedMap(new WeakHashMap<>());

	/** Called when a dimension's structure state is made (StructureStateMixin). */
	public static void register(ChunkGeneratorStructureState state, BiomeSource biomeSource) {
		WORLDS.put(biomeSource, new World(state));
	}

	private record SetInfo(Holder<StructureSet> set, String name) {}

	private static final class World {
		final ChunkGeneratorStructureState state;
		private volatile List<SetInfo> sets;
		final ConcurrentHashMap<String, Optional<BoundingBox>> generated = new ConcurrentHashMap<>();

		World(ChunkGeneratorStructureState state) {
			this.state = state;
		}

		List<SetInfo> sets() {
			List<SetInfo> s = sets;
			if (s != null) return s;
			List<SetInfo> list = new ArrayList<>();
			for (Holder<StructureSet> holder : state.possibleStructureSets()) {
				Optional<ResourceKey<StructureSet>> key = holder.unwrapKey();
				if (key.isEmpty()) continue;
				Identifier id = key.get().identifier();
				boolean keep = id.getNamespace().equals("onepiece") ? !SKIP.contains(id.getPath())
						: id.getNamespace().equals("minecraft") && VANILLA.contains(id.getPath());
				if (keep) list.add(new SetInfo(holder, id.toString()));
			}
			sets = list;
			return list;
		}
	}

	/**
	 * Footprints of other structures that really generate close enough to matter for a lair at `box` that may still
	 * slide up to `slack` blocks. Never null.
	 */
	public static List<BoundingBox> blockers(Structure.GenerationContext ctx, BoundingBox box, int slack) {
		if (GAP <= 0) return List.of();
		World w = WORLDS.get(ctx.biomeSource());
		if (w == null) return List.of();
		long t0 = DEBUG ? System.nanoTime() : 0;
		int cx = (box.minX() + box.maxX()) / 2, cz = (box.minZ() + box.maxZ()) / 2;
		int reach = Math.max(box.getXSpan(), box.getZSpan()) / 2 + slack + GAP + NEIGHBOUR_REACH;
		List<BoundingBox> out = new ArrayList<>();
		for (SetInfo info : w.sets()) {
			for (ChunkPos n : candidates(w, info, cx, cz, reach)) {
				Optional<BoundingBox> nb = generated(w, info, n, ctx);
				if (nb.isPresent() && gap(box, nb.get()) < GAP + slack * 1.5) {
					if (DEBUG) BossesMod.LOGGER.info("lair neighbours: {} near {} at {}", info.name, ctx.chunkPos(), nb.get());
					out.add(nb.get());
				}
			}
		}
		if (DEBUG) BossesMod.LOGGER.info("lair neighbours at {}: {} in {} ms", ctx.chunkPos(), out.size(), (System.nanoTime() - t0) / 1_000_000);
		return out;
	}

	/** True when the footprint keeps GAP blocks from every blocker. */
	public static boolean clear(BoundingBox box, List<BoundingBox> blockers) {
		for (BoundingBox b : blockers) if (gap(box, b) < GAP) return false;
		return true;
	}

	private static double gap(BoundingBox a, BoundingBox b) {
		int dx = Math.max(0, Math.max(a.minX() - b.maxX(), b.minX() - a.maxX()));
		int dz = Math.max(0, Math.max(a.minZ() - b.maxZ(), b.minZ() - a.maxZ()));
		return Math.sqrt((double) dx * dx + (double) dz * dz);
	}

	/** The set's start chunks within `reach` blocks (square) of cx, cz that pass its placement (spread, rings, exclusion). */
	private static List<ChunkPos> candidates(World w, SetInfo info, int cx, int cz, int reach) {
		List<ChunkPos> out = new ArrayList<>();
		StructurePlacement placement = info.set.value().placement();
		if (placement instanceof RandomSpreadStructurePlacement spread) {
			int spacing = spread.spacing();
			int c0x = Math.floorDiv(cx - reach, 16), c1x = Math.floorDiv(cx + reach, 16);
			int c0z = Math.floorDiv(cz - reach, 16), c1z = Math.floorDiv(cz + reach, 16);
			for (int gx = Math.floorDiv(c0x, spacing); gx <= Math.floorDiv(c1x, spacing); gx++) {
				for (int gz = Math.floorDiv(c0z, spacing); gz <= Math.floorDiv(c1z, spacing); gz++) {
					ChunkPos p = spread.getPotentialStructureChunk(w.state.getLevelSeed(), gx * spacing, gz * spacing);
					if (p.x() < c0x || p.x() > c1x || p.z() < c0z || p.z() > c1z) continue;
					if (spread.isStructureChunk(w.state, p.x(), p.z())) out.add(p);
				}
			}
		} else if (placement instanceof ConcentricRingsStructurePlacement rings) {
			for (ChunkPos p : w.state.getRingPositionsFor(rings)) {
				if (Math.abs(p.x() * 16 + 8 - cx) <= reach && Math.abs(p.z() * 16 + 8 - cz) <= reach) out.add(p);
			}
		}
		return out;
	}

	/** The footprint the set really generates at chunk n, picked the way ChunkGenerator.createStructures does, if any. */
	private static Optional<BoundingBox> generated(World w, SetInfo info, ChunkPos n, Structure.GenerationContext ctx) {
		String key = info.name + "@" + n.x() + "," + n.z();
		Optional<BoundingBox> done = w.generated.get(key);
		if (done != null) return done;
		Optional<BoundingBox> result = Optional.empty();
		for (StructureSet.StructureSelectionEntry e : drawOrder(w, info, n)) {
			result = tryOne(e.structure().value(), n, ctx);
			if (result.isPresent()) break;
		}
		if (w.generated.size() > 100_000) w.generated.clear();
		w.generated.put(key, result);
		return result;
	}

	/** The order createStructures tries a set's structures in at chunk n (a weighted draw without putting back). */
	private static List<StructureSet.StructureSelectionEntry> drawOrder(World w, SetInfo info, ChunkPos n) {
		List<StructureSet.StructureSelectionEntry> list = new ArrayList<>(info.set.value().structures());
		if (list.size() == 1) return list;
		List<StructureSet.StructureSelectionEntry> out = new ArrayList<>();
		WorldgenRandom random = new WorldgenRandom(new LegacyRandomSource(0L));
		random.setLargeFeatureSeed(w.state.getLevelSeed(), n.x(), n.z());
		int total = 0;
		for (StructureSet.StructureSelectionEntry e : list) total += e.weight();
		while (!list.isEmpty()) {
			int pick = random.nextInt(total), k = 0;
			for (StructureSet.StructureSelectionEntry e : list) {
				pick -= e.weight();
				if (pick < 0) break;
				k++;
			}
			StructureSet.StructureSelectionEntry e = list.remove(k);
			total -= e.weight();
			out.add(e);
		}
		return out;
	}

	private static Optional<BoundingBox> tryOne(Structure structure, ChunkPos n, Structure.GenerationContext ctx) {
		// Cheap first: the main mod works out the start piece's biome without laying the structure out, and most picks
		// fail there. Only the ones that pass are laid out in full (with the main mod's own ground check and slide).
		boolean fits;
		try {
			fits = OnePieceBridge.startBiomeFits(structure, n, ctx);
		} catch (LinkageError e) {
			fits = true;
		}
		if (!fits) return Optional.empty();
		Structure.GenerationContext there = new Structure.GenerationContext(ctx.registryAccess(), ctx.chunkGenerator(),
				ctx.biomeSource(), ctx.climateSampler(), ctx.randomState(), ctx.structureTemplateManager(), ctx.seed(), n,
				ctx.heightAccessor(), structure.biomes()::contains);
		Optional<Structure.GenerationStub> stub = structure.findValidGenerationPoint(there);
		if (stub.isEmpty()) return Optional.empty();
		StructurePiecesBuilder builder = stub.get().getPiecesBuilder();
		return builder.isEmpty() ? Optional.empty() : Optional.of(builder.getBoundingBox());
	}
}
