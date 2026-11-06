package com.onepiecebosses.test;

import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Which in-world tests run, so a change only replays what it touches. Pass them to Gradle:
 *
 *     gradlew runClientGameTest                                       (bosses, lairs, world mobs and crews, everything)
 *     gradlew runClientGameTest -Dopbosses.tests=lairs                (only the lair test)
 *     gradlew runClientGameTest -Dopbosses.tests=bosses -Dopbosses.only=uta_diva,zephyr_z
 *     gradlew runClientGameTest -Dopbosses.tests=models               (model portraits)
 *     gradlew runClientGameTest -Dopbosses.tests=mobs -Dopbosses.only=raids   (only the pirate raids)
 *     gradlew runClientGameTest -Dopbosses.tests=crews                (the rival pirate crews)
 *     gradlew runClientGameTest -Dopbosses.tests=places -Dopbosses.only=angel_beach   (screenshots of a main-mod structure)
 *     gradlew runClientGameTest -Dopbosses.tests=sea -Dopbosses.only=widowmaker,gulpmaw   (flagships and Sea King mini-bosses)
 *
 * opbosses.tests: any of bosses, lairs, mobs, crews, models, places, sea (default "bosses,lairs,mobs,crews"). opbosses.only: boss ids or lair
 * names (default: all of them); a lair is picked by its own name or its boss's id; the world mobs are "hunters" and "raids"; the rival crews are "roam", "clash" and "camp";
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
		return list("opbosses.tests", "bosses,lairs,mobs,crews").contains(test);
	}

	static boolean picks(String... ids) {
		Set<String> only = list("opbosses.only", "");
		return only.isEmpty() || Arrays.stream(ids).anyMatch(only::contains);
	}
}
