package com.onepiecebosses.crew;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

import com.google.gson.Gson;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.npc.NpcKit;

/**
 * The rogue bosses' crews (src/main/resources/opbosses/crews.json). They are the One Piece Mod's pirate NPCs,
 * so they fight with its styles and wear its skins; this only adds their kits to its kit list.
 * /npc spawn <kit> works on them too. The "rivals" list is the roaming rival crews (RivalCrews).
 */
public final class CrewKits {
	private CrewKits() {
	}

	private static class FileData {
		List<NpcKit> kits = List.of();
		List<RivalCrews.Rival> rivals = List.of();
	}

	public static void initialize() {
		try (InputStream in = CrewKits.class.getResourceAsStream("/opbosses/crews.json")) {
			FileData data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), FileData.class);
			for (NpcKit kit : data.kits) {
				OnePieceBridge.addNpcKit(kit);
			}
			RivalCrews.load(data.rivals);
		} catch (Exception e) {
			throw new RuntimeException("Could not read opbosses/crews.json", e);
		}
	}
}
