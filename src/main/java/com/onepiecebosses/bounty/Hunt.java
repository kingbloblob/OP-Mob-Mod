package com.onepiecebosses.bounty;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * One hunt on the Marine Bounty Board. The board's hunts are made up fresh each day (BountyBoard.hunts); the one a
 * player takes is saved on them, with their progress, until they hand it in or drop it.
 *
 * @param id        "day:slot" (like "12:3"), so a hunt can't be taken twice in one day
 * @param kind      BOSS (beat a rogue boss), PIRATES (beat pirate NPCs), RAIDERS (beat rookie raiders), BEAST (beat a creature)
 * @param target    BOSS: the rogue's id; BEAST: the creature's entity id; otherwise ""
 * @param count     how many to beat
 * @param progress  how many so far
 * @param title     "Wanted: Saltjaw Rourke" or "Clear out 8 pirates"
 * @param berries   Berries paid on hand-in
 * @param rare      a rare item paid on top (an item id), or ""
 * @param rareCount how many of it
 */
public record Hunt(String id, String kind, String target, int count, int progress, String title, int berries, String rare, int rareCount) {

	public static final String BOSS = "BOSS";
	public static final String PIRATES = "PIRATES";
	public static final String RAIDERS = "RAIDERS";
	public static final String BEAST = "BEAST";

	public static final Codec<Hunt> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.STRING.fieldOf("id").forGetter(Hunt::id),
			Codec.STRING.fieldOf("kind").forGetter(Hunt::kind),
			Codec.STRING.fieldOf("target").forGetter(Hunt::target),
			Codec.INT.fieldOf("count").forGetter(Hunt::count),
			Codec.INT.fieldOf("progress").forGetter(Hunt::progress),
			Codec.STRING.fieldOf("title").forGetter(Hunt::title),
			Codec.INT.fieldOf("berries").forGetter(Hunt::berries),
			Codec.STRING.fieldOf("rare").forGetter(Hunt::rare),
			Codec.INT.fieldOf("rare_count").forGetter(Hunt::rareCount)
	).apply(instance, Hunt::new));

	public boolean done() {
		return progress >= count;
	}

	public Hunt withProgress(int value) {
		return new Hunt(id, kind, target, count, Math.min(count, value), title, berries, rare, rareCount);
	}
}
