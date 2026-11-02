package com.onepiecebosses.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import com.mojang.datafixers.util.Pair;

import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

/**
 * Looks at one of the One Piece Mod's own structures as a world makes it, for a fix to a main-mod build that shows up
 * next to the lairs (ryan 2026-11-02: Angel Beach's cloud sea was see-through glass). Runs only when asked:
 *
 *     gradlew runClientGameTest -Dopbosses.tests=places -Dopbosses.only=angel_beach
 *
 * For each id it /locates onepiece:<id>, logs its bounds and how many of its blocks are see-through (glass, panes,
 * ice), and takes screenshots from above, from the side and from underneath (places_<id>*.png). "PT" lines in the log.
 */
public class PlacesClientTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("places-test");

	@Override
	public void runTest(ClientGameTestContext context) {
		if (!TestFilter.runs("places")) {
			return;
		}
		List<String> ids = new ArrayList<>(List.of(System.getProperty("opbosses.only", "angel_beach").split(",")));
		ids.replaceAll(String::trim);
		try (TestSingleplayerContext sp = context.worldBuilder().adjustSettings(PlacesClientTest::defaultWorld).create()) {
			sp.getConnection().waitForChunksRender();
			cmd(sp, "gamemode spectator @a");
			cmd(sp, "time set noon");
			cmd(sp, "weather clear");
			context.waitTicks(10);
			context.setScreen(() -> null);
			for (String id : ids) {
				if (!id.isEmpty()) look(context, sp, id);
			}
			LOG.info("PT DONE");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private void look(ClientGameTestContext context, TestSingleplayerContext sp, String id) throws Exception {
		BlockPos[] found = new BlockPos[1];
		server(sp, s -> {
			var key = ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath("onepiece", id));
			var holder = s.registryAccess().lookupOrThrow(Registries.STRUCTURE).get(key);
			if (holder.isEmpty()) {
				LOG.info("PT FAIL no structure onepiece:{}", id);
				return;
			}
			ServerLevel level = s.overworld();
			Pair<BlockPos, Holder<Structure>> p = level.getChunkSource().getGenerator()
					.findNearestMapStructure(level, HolderSet.direct(holder.get()), new BlockPos(0, 64, 0), 100, false);
			if (p == null) {
				LOG.info("PT FAIL /locate found no {}", id);
				return;
			}
			found[0] = p.getFirst();
			LOG.info("PT LOCATE {} at {} {}", id, found[0].getX(), found[0].getZ());
		});
		if (found[0] == null) return;
		// Go there first so the chunks generate, then read the structure's real bounds.
		server(sp, s -> player(s).teleportTo(s.overworld(), found[0].getX() + 8.5, 230, found[0].getZ() + 8.5, Set.of(), 0f, 90f, true));
		context.waitTicks(100);
		sp.getConnection().waitForChunksRender();
		BoundingBox[] box = new BoundingBox[1];
		server(sp, s -> {
			ServerLevel level = s.overworld();
			var holder = s.registryAccess().lookupOrThrow(Registries.STRUCTURE)
					.getOrThrow(ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath("onepiece", id)));
			var start = level.getChunk(found[0]).getStartForStructure(holder.value());
			box[0] = start != null && start.isValid() ? start.getBoundingBox() : new BoundingBox(found[0]).inflatedBy(70);
			BoundingBox b = box[0];
			LOG.info("PT {} bounds {} {} {} .. {} {} {}", id, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ());
			// count see-through blocks and the opaque cloud, over every 2nd column
			int glass = 0, seaCloud = 0, cloud = 0;
			for (int x = b.minX(); x <= b.maxX(); x += 2) {
				for (int z = b.minZ(); z <= b.maxZ(); z += 2) {
					for (int y = b.minY(); y <= b.maxY(); y++) {
						BlockState st = level.getBlockState(new BlockPos(x, y, z));
						String n = BuiltInRegistries.BLOCK.getKey(st.getBlock()).toString();
						if (n.endsWith("stained_glass") || n.equals("minecraft:glass")) glass++;
						else if (n.equals("onepiece:sea_cloud")) seaCloud++;
						else if (n.equals("onepiece:island_cloud")) cloud++;
					}
				}
			}
			LOG.info("PT {} blocks (every 2nd column): glass {} sea_cloud {} island_cloud {}", id, glass, seaCloud, cloud);
		});
		BoundingBox b = box[0];
		double cx = (b.minX() + b.maxX()) / 2.0, cz = (b.minZ() + b.maxZ()) / 2.0;
		int top = b.maxY(), bottom = b.minY();
		double[][] cams = {
				{cx, top + 40, b.maxZ() + 45, 180f, 35f},          // above, from the south
				{b.minX() - 30, bottom + 18, cz, -90f, 8f},         // the side, at the sea's level
				{cx + 20, bottom + 18, b.maxZ() - 6, 200f, 30f},    // standing on the sea, looking over it
				{cx, bottom - 30, b.maxZ() + 30, 180f, -30f}};      // underneath
		String[] names = {"", "_side", "_sea", "_under"};
		for (int i = 0; i < cams.length; i++) {
			double[] c = cams[i];
			server(sp, s -> player(s).teleportTo(s.overworld(), c[0], c[1], c[2], Set.of(), (float) c[3], (float) c[4], true));
			context.waitTicks(40);
			sp.getConnection().waitForChunksRender();
			context.waitTicks(20);
			context.takeScreenshot("places_" + id + names[i]);
		}
	}

	private static void defaultWorld(WorldCreationUiState creator) {
		creator.setWorldType(new WorldCreationUiState.WorldTypeEntry(
				creator.getSettings().worldgenLoadContext().lookupOrThrow(Registries.WORLD_PRESET).getOrThrow(WorldPresets.NORMAL)));
		creator.setGenerateStructures(true);
		creator.setAllowCommands(true);
		creator.setSeed("rogue-lairs");
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void cmd(TestSingleplayerContext sp, String command) {
		sp.getServer().runCommand(command);
	}

	private static void server(TestSingleplayerContext sp, Consumer<MinecraftServer> action) throws Exception {
		sp.getServer().runOnServer(action::accept);
	}
}
