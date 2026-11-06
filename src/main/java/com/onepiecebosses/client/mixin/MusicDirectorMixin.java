package com.onepiecebosses.client.mixin;

import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.core.Holder;
import net.minecraft.sounds.SoundEvent;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import com.onepiecebosses.boss.ArenaMusic;
import com.onepiecebosses.boss.RogueBossEntity;

/**
 * Lair battle themes. The main mod's music player (MusicDirector) picks a boss theme while a boss is close; with a
 * rogue boss close by, it plays that boss's lair theme instead (the nearest rogue's, if there are several). Everything
 * else stays the main mod's: the fade in and out, the loop, and the victory fanfare when the boss falls.
 */
@Mixin(targets = "com.onepiecemod.sound.client.MusicDirector")
public abstract class MusicDirectorMixin {
	/** The same range the main mod uses for its boss music. */
	private static final double OPBOSSES_RANGE = 40;

	@Inject(method = "battleSong", at = @At("HEAD"), cancellable = true)
	private static void opbosses$lairTheme(Minecraft mc, CallbackInfoReturnable<Holder<SoundEvent>> cir) {
		if (mc.player == null || mc.level == null || mc.player.isSpectator()) {
			return;
		}
		List<RogueBossEntity> rogues = mc.level.getEntitiesOfClass(RogueBossEntity.class,
				mc.player.getBoundingBox().inflate(OPBOSSES_RANGE), e -> e.isBoss() && e.isAlive());
		RogueBossEntity nearest = null;
		for (RogueBossEntity rogue : rogues) {
			if (ArenaMusic.of(rogue.getCharacterId()) != null && (nearest == null || rogue.distanceToSqr(mc.player) < nearest.distanceToSqr(mc.player))) {
				nearest = rogue;
			}
		}
		if (nearest != null) {
			cir.setReturnValue(ArenaMusic.of(nearest.getCharacterId()));
		}
	}

	/**
	 * A lair theme is a battle theme too, so the victory fanfare follows it. Optional (require = 0): main mod builds
	 * from before the fanfare have no isBattleSong, and there the lair theme simply fades out like any boss theme.
	 */
	@Inject(method = "isBattleSong", at = @At("HEAD"), cancellable = true, require = 0)
	private static void opbosses$lairThemeIsBattle(Holder<SoundEvent> song, CallbackInfoReturnable<Boolean> cir) {
		if (ArenaMusic.isTheme(song)) {
			cir.setReturnValue(true);
		}
	}
}
