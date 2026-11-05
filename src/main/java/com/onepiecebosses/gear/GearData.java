package com.onepiecebosses.gear;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;

/**
 * One boss's gear set, read from src/main/resources/opbosses/gear.json: four armour pieces and a weapon,
 * crafted from the Remnants that boss drops, with a full-set bonus themed on its signature move.
 */
public class GearData {
	/** The boss in bosses.json whose Remnants make this set. */
	public String boss;
	/** Item id prefix: "scrapheap" makes scrapheap_helmet, scrapheap_chestplate and so on. Also the equipment asset. */
	public String set;
	/** "Scrapheap Salvage": the pieces are called "Scrapheap Salvage Helm" and so on (see the lang file). */
	public String setName;
	public String weapon;
	public String weaponName;
	/** The look of the weapon icon (tools/gen_gear.py). Hammers hit harder and slower, rapiers faster and lighter. */
	public String weaponShape;
	/** Mob effects the full set keeps on you: [effect id, amplifier, when] with when = always, water or falling. */
	public List<List<Object>> passives = List.of();
	/** The set's signature move (GearSignatures), with a line about it for the tooltips. */
	public String move;
	public String moveText;

	public String remnant() {
		return "remnant_" + boss;
	}

	// ---- Loading ----

	private static final Map<String, GearData> BY_BOSS = new LinkedHashMap<>();

	/** Boss id -> its set, in gear.json order. */
	public static Map<String, GearData> all() {
		if (BY_BOSS.isEmpty()) {
			try (InputStream in = GearData.class.getResourceAsStream("/opbosses/gear.json")) {
				Gson gson = new Gson();
				for (JsonElement entry : JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8))
						.getAsJsonObject().getAsJsonArray("sets")) {
					GearData data = gson.fromJson(entry, GearData.class);
					BY_BOSS.put(data.boss, data);
				}
			} catch (Exception e) {
				throw new RuntimeException("Could not read opbosses/gear.json", e);
			}
		}
		return BY_BOSS;
	}

	public static GearData forBoss(String bossId) {
		return all().get(bossId);
	}
}
