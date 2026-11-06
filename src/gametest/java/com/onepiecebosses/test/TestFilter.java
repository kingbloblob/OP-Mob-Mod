package com.onepiecebosses.test;

import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Which in-world tests run, so a change only replays what it touches. Pass them to Gradle:
 *
 *     gradlew runClientGameTest                                       (bosses, arenas, lairs, world mobs, crews and the bounty board, everything)
 *     gradlew runClientGameTest -Dopbosses.tests=lairs                (only the lair test)
 *     gradlew runClientGameTest -Dopbosses.tests=bosses -Dopbosses.only=uta_diva,zephyr_z
 *     gradlew runClientGameTest -Dopbosses.tests=arenas -Dopbosses.only=uta_diva   (lair music, boss bar, hazards, last wave)
 *     gradlew runClientGameTest -Dopbosses.tests=models               (model portraits)
 *     gradlew runClientGameTest -Dopbosses.tests=mobs -Dopbosses.only=raids   (only the pirate raids)
 *     gradlew runClientGameTest -Dopbosses.tests=crews                (the rival pirate crews)
 *     gradlew runClientGameTest -Dopbosses.tests=gear -Dopbosses.only=gild_tesoro   (boss gear: drops, set bonus, screenshots)
 *     gradlew runClientGameTest -Dopbosses.tests=places -Dopbosses.only=angel_beach   (screenshots of a main-mod structure)
 *     gradlew runClientGameTest -Dopbosses.tests=bounty               (the Marine Bounty Board)
 *     gradlew runClientGameTest -Dopbosses.tests=sea -Dopbosses.only=widowmaker,gulpmaw   (flagships and Sea King mini-bosses)
 *
 * opbosses.tests: any of bosses, arenas, lairs, mobs, crews, models, places, bounty, sea, gear (default "bosses,arenas,lairs,mobs,crews,bounty"). opbosses.only: boss ids or lair
 * names (default: all of them); a lair is picked by its own name or its boss's id, a gear set by its boss's id or set name; the world mobs are "hunters" and "raids"; the rival crews are "roam", "clash" and "camp";
 * the sea test picks a flagship by its id or its captain's, a Sea King by its id (gulpmaw, ironscale, thundercoil).
 */
final class TestFilter {
	private TestFilter() {
	}

	private static Set<String> list(String property, String fallback) {
		return Arrays.stream(System.getProperty(property, fallback).split(",")).map(String::trim).filter(s -> !s.isEmpty())
				.collect(Collectors.toSet());
	}

	static boolean runs(String test) {
		return list("opbosses.tests", "bosses,arenas,lairs,mobs,crews,bounty").contains(test);
	}

	static boolean picks(String... ids) {
		Set<String> only = list("opbosses.only", "");
		return only.isEmpty() || Arrays.stream(ids).anyMatch(only::contains);
	}
}
