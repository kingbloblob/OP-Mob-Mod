package com.onepiecebosses.boss;

import java.util.LinkedHashMap;
import java.util.Map;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvent;

import com.onepiecebosses.BossesMod;

/**
 * The lairs' battle themes: one sound event per theme named in arenas.json (opbosses:music.lair.<name>, the files are
 * assets/opbosses/sounds/music/<name>.ogg). The main mod's music player (its MusicDirector) plays them in place of its
 * own boss theme while you're near a rogue boss, see client/mixin/MusicDirectorMixin.
 */
public final class ArenaMusic {
	private ArenaMusic() {
	}

	/** Theme name -> its sound event. */
	public static final Map<String, Holder<SoundEvent>> THEMES = new LinkedHashMap<>();

	public static void initialize() {
		for (ArenaData arena : ArenaData.all().values()) {
			if (!arena.music.isEmpty() && !THEMES.containsKey(arena.music)) {
				Identifier id = BossesMod.id("music.lair." + arena.music);
				THEMES.put(arena.music, Registry.registerForHolder(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id)));
			}
		}
	}

	/** The battle theme of the boss with this id, or null for the main mod's own. */
	public static Holder<SoundEvent> of(String bossId) {
		return THEMES.get(ArenaData.of(bossId).music);
	}

	public static boolean isTheme(Holder<SoundEvent> song) {
		return song != null && THEMES.containsValue(song);
	}
}
