package com.onepiecebosses.boss;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * A boss's arena, read from src/main/resources/opbosses/arenas.json: its lair's battle theme, its boss bar colour, and
 * the hazards its lair throws at you as the fight goes on (ArenaEvents runs them). Read on both sides: the server runs
 * the hazards, the client picks the music.
 */
public class ArenaData {
	/** A lair theme's name: assets/opbosses/sounds/music/<music>.ogg, sound event opbosses:music.lair.<music>. "" = the main mod's music. */
	public String music = "";
	/** The boss bar's colour, one of BossEvent.BossBarColor's names ("green"). "" = the main mod's colour for its tier. */
	public String bar = "";
	/** The phase the boss bar's world fog starts at, or 0 for never. */
	public int fogFrom = 0;
	/** The phase the boss bar darkens the sky at, or 0 for never. */
	public int darkenFrom = 0;
	/** Shouted when the crew's last wave arrives at phase 3. */
	public String finalWave = "";
	public List<Hazard> hazards = List.of();

	public static class Hazard {
		/** collapse, debris, geyser, cloud, lightning, tide or fog (see ArenaEvents). */
		public String type = "";
		/** The phase it starts at (2 or 3). */
		public int from = 2;
		/** Said once, when it starts. */
		public String warn = "";
		/** debris: the block that falls (its particles). */
		public String block = "minecraft:cobblestone";
		/** geyser, cloud, tide: the particle it's drawn with. */
		public String particle = "";
		/** cloud: the effect it gives whoever stands in it. */
		public String effect = "";
		/** geyser: sets you on fire too. */
		public boolean fire = false;
	}

	private static final ArenaData PLAIN = new ArenaData();
	private static final Map<String, ArenaData> ALL = new LinkedHashMap<>();

	public static Map<String, ArenaData> all() {
		if (ALL.isEmpty()) {
			try (InputStream in = ArenaData.class.getResourceAsStream("/opbosses/arenas.json")) {
				JsonObject file = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
				Gson gson = new Gson();
				for (Map.Entry<String, JsonElement> entry : file.entrySet()) {
					if (entry.getValue().isJsonObject()) {
						ALL.put(entry.getKey(), gson.fromJson(entry.getValue(), ArenaData.class));
					}
				}
			} catch (Exception e) {
				throw new RuntimeException("Could not read opbosses/arenas.json", e);
			}
		}
		return ALL;
	}

	/** The arena of the boss with this id. A boss with no entry gets a plain arena: no hazards, the main mod's music. */
	public static ArenaData of(String bossId) {
		return all().getOrDefault(bossId, PLAIN);
	}

	/** True if this boss has its own arena entry. */
	public static boolean has(String bossId) {
		return all().containsKey(bossId);
	}
}
