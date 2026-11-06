package com.onepiecebosses.boss;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.character.BossStrikes;
import com.onepiecemod.fx.MoveFx;

/**
 * The rogue bosses' phase 3 signature moves. Each one builds on one of the main mod's signature strikes
 * (they draw their own warning circles and land a moment later, so they can be dodged) and adds its own twist.
 * A boss's "signature" in bosses.json picks one of these.
 *
 * "extra" is the boss's difficulty (0 Normal, 1 Hard, 2 Expert): more strikes, longer effects.
 */
public final class RogueSignatures {
	private RogueSignatures() {
	}

	public static void use(String signature, Mob boss, LivingEntity target, ServerLevel level, BossStrikes strikes, float damage, int extra) {
		switch (signature) {
			case "anchor_drag" -> { // Rourke hurls his anchor and hauls you in along the chain, into the line it cuts.
				pull(target, boss, 1.4);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40 + 20 * extra, 2));
				level.playSound(null, boss.blockPosition(), SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0f, 0.6f);
				strikes.signature("slash_line", boss, target, level, damage, extra);
			}
			case "widows_veil" -> { // Corvina vanishes into her fog and reappears behind you while smoke rains down.
				for (Player player : playersNear(boss, level, 14)) {
					player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 50 + 20 * extra, 0));
				}
				level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, boss.getX(), boss.getY() + 1, boss.getZ(), 60, 3, 1.5, 3, 0.01);
				boss.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 50, 0));
				Vec3 behind = target.position().subtract(target.getLookAngle().multiply(1, 0, 1).scale(2.0));
				BlockPos spot = safeSpot(level, BlockPos.containing(behind.x, target.getY(), behind.z));
				if (spot != null) { // Only onto solid ground: never off a cliff or into a wall.
					boss.teleportTo(behind.x, spot.getY(), behind.z);
				}
				strikes.signature("rain_smoke", boss, target, level, damage, extra);
			}
			case "seastone_volley" -> { // Graves's garrison fires seastone shot: it rains metal and drains fruit users.
				strikes.signature("rain_metal", boss, target, level, damage, extra);
				for (Player player : playersNear(boss, level, 12)) {
					if (OnePieceBridge.isFruitUser(player)) {
						OnePieceBridge.drainFruitPower(player, 100 + 40 * extra);
					}
				}
				level.playSound(null, boss.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5f, 1.4f);
			}
			case "hollow_cut" -> { // Tsurugi's cut flies the whole line, and the empty armor's curse withers whoever is close.
				strikes.signature("slash_line", boss, target, level, damage * 1.15f, extra);
				for (Player player : playersNear(boss, level, 5)) {
					player.addEffect(new MobEffectInstance(MobEffects.WITHER, 60 + 20 * extra, 1));
				}
				level.sendParticles(ParticleTypes.SOUL, boss.getX(), boss.getY() + 1, boss.getZ(), 30, 0.8, 1.0, 0.8, 0.02);
			}
			case "boiler_burst" -> { // Gantz vents his boiler: a scalding wave all around, then he has to cool down.
				strikes.signature("ground_wave", boss, target, level, damage, extra);
				for (Player player : playersNear(boss, level, 9)) {
					player.igniteForSeconds(4 + 2 * extra);
				}
				MoveFx.shockwave(level, boss.position(), 9, MoveFx.FIRE, MoveFx.FIRE_OUT);
				level.sendParticles(ParticleTypes.CLOUD, boss.getX(), boss.getY() + boss.getBbHeight(), boss.getZ(), 50, 1.0, 0.5, 1.0, 0.15);
				level.playSound(null, boss.blockPosition(), SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.5f, 0.5f);
				boss.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2)); // The opening: hit him while he cools.
			}
			case "tidal_judgment" -> { // Nereus opens a whirlpool that drags everything in, with freezing deep water raining down.
				strikes.signature("black_hole", boss, target, level, damage, extra);
				strikes.signature("rain_ice", boss, target, level, damage * 0.6f, extra);
				for (Player player : playersNear(boss, level, 12)) {
					player.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 100, 1));
				}
				level.sendParticles(ParticleTypes.SPLASH, boss.getX(), boss.getY() + 0.5, boss.getZ(), 120, 5, 0.5, 5, 0.3);
			}
			case "shackle_storm" -> { // Khamsin whips up a sandstorm, then yanks you in by his chains and claps the irons on.
				for (Player player : playersNear(boss, level, 12)) {
					player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30 + 10 * extra, 0));
					player.addEffect(new MobEffectInstance(MobEffects.HUNGER, 120, 2)); // The desert dries you out.
				}
				pull(target, boss, 1.2);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60 + 20 * extra, 3)); // Shackled.
				level.sendParticles(ParticleTypes.WHITE_ASH, boss.getX(), boss.getY() + 2, boss.getZ(), 200, 6, 2, 6, 0.05);
				level.playSound(null, boss.blockPosition(), SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0f, 0.5f);
				strikes.signature("rain_sand", boss, target, level, damage, extra + 1);
			}
			case "drowned_doubloon" -> { // Gale's cursed gold takes years off everyone near, and the years mend him: he can't die while it's paid.
				float taken = 0;
				for (Player player : playersNear(boss, level, 10)) {
					player.addEffect(new MobEffectInstance(MobEffects.WITHER, 60 + 20 * extra, 1));
					player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 0));
					level.sendParticles(ParticleTypes.SOUL, player.getX(), player.getY() + 1, player.getZ(), 12, 0.3, 0.6, 0.3, 0.03);
					taken += 1;
				}
				boss.heal(boss.getMaxHealth() * 0.015f * Math.min(taken, 4));
				level.sendParticles(ParticleTypes.SOUL, boss.getX(), boss.getY() + 1, boss.getZ(), 40, 1.5, 1.0, 1.5, 0.02);
				level.playSound(null, boss.blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0f, 0.5f);
				strikes.signature("rain_curse", boss, target, level, damage, extra + 1);
			}
			case "leviathan_charge" -> { // Vasco's Sea King lunges: a charge straight at you, a wall of seawater, the ground bucks.
				Vec3 at = target.position().subtract(boss.position()).multiply(1, 0, 1);
				if (at.lengthSqr() > 0.01) {
					Vec3 dash = at.normalize().scale(Math.min(2.4, at.length() * 0.35));
					boss.setDeltaMovement(dash.x, 0.35, dash.z);
					boss.needsSync = true;
				}
				Vec3 away = target.position().subtract(boss.position()).multiply(1, 0, 1).normalize().scale(1.6);
				target.setDeltaMovement(away.x, 0.7, away.z);
				target.needsSync = true;
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40 + 20 * extra, 1)); // Soaked through.
				level.sendParticles(ParticleTypes.SPLASH, target.getX(), target.getY() + 0.5, target.getZ(), 150, 2.5, 1.0, 2.5, 0.4);
				level.sendParticles(ParticleTypes.BUBBLE_POP, boss.getX(), boss.getY() + 1, boss.getZ(), 60, 2, 1, 2, 0.1);
				level.playSound(null, boss.blockPosition(), SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.5f, 0.6f);
				level.playSound(null, boss.blockPosition(), SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0f, 0.7f);
				strikes.signature("ground_wave", boss, target, level, damage, extra);
				strikes.signature("rain_ice", boss, target, level, damage * 0.6f, extra);
			}
			case "prototype_barrage" -> { // Kreuz: every prototype fires at once (laser rain), a paw-pad blast throws back anyone close, and a shield goes up.
				for (Player player : playersNear(boss, level, 6)) {
					Vec3 away = player.position().subtract(boss.position()).multiply(1, 0, 1).normalize().scale(1.8);
					player.setDeltaMovement(away.x, 1.1, away.z);
					player.needsSync = true;
				}
				boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 80 + 20 * extra, 1)); // His deflector prototype.
				MoveFx.shockwave(level, boss.position(), 6, 0xFFE8F0FF, 0xFF3A6AC8);
				level.sendParticles(ParticleTypes.ELECTRIC_SPARK, boss.getX(), boss.getY() + 1.5, boss.getZ(), 80, 1.2, 1.2, 1.2, 0.4);
				level.playSound(null, boss.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.0f, 0.5f);
				level.playSound(null, boss.blockPosition(), SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 1.0f, 1.6f);
				strikes.signature("rain_light", boss, target, level, damage, extra + 3);
			}
			// ---- The film villains ----
			case "golden_finale" -> { // Tesoro: the gold everyone touched grabs them, and molten gold rains down.
				for (Player player : playersNear(boss, level, 12)) {
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50 + 20 * extra, 4));
					player.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 80 + 20 * extra, 2));
					level.sendParticles(ParticleTypes.WAX_ON, player.getX(), player.getY() + 1, player.getZ(), 30, 0.4, 0.8, 0.4, 0.05);
				}
				MoveFx.shockwave(level, boss.position(), 12, MoveFx.GOLD, MoveFx.GOLD_OUT);
				level.playSound(null, boss.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5f, 0.6f);
				strikes.signature("rain_metal", boss, target, level, damage, extra + 2);
			}
			case "uta_world" -> { // Uta: her song pulls everyone into a dream (you nod off), then Tot Musica's light falls.
				for (Player player : playersNear(boss, level, 16)) {
					player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 120 + 20 * extra, 0));
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60 + 20 * extra, 2));
					player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 25, 0));
				}
				for (int i = 0; i < 24; i++) {
					double a = Math.PI * 2 * i / 24;
					level.sendParticles(ParticleTypes.NOTE, boss.getX() + Math.cos(a) * 6, boss.getY() + 2, boss.getZ() + Math.sin(a) * 6, 1, 0, 0, 0, i / 24.0);
				}
				level.playSound(null, boss.blockPosition(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 3.0f, 0.7f);
				level.playSound(null, boss.blockPosition(), SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 3.0f, 1.0f);
				boss.heal(boss.getMaxHealth() * 0.02f); // The dreamers' cheering keeps her going.
				strikes.signature("rain_light", boss, target, level, damage, extra + 1);
			}
			case "battle_smasher" -> { // Zephyr: a seastone haymaker that sends you flying, then the shockwave and his Smash Blaster shells.
				Vec3 away = target.position().subtract(boss.position()).multiply(1, 0, 1).normalize().scale(2.2);
				target.setDeltaMovement(away.x, 0.9, away.z);
				target.needsSync = true;
				level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, target.getX(), target.getY() + 1, target.getZ(), 1, 0, 0, 0, 0);
				level.playSound(null, boss.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0f, 0.8f);
				for (Player player : playersNear(boss, level, 12)) {
					if (OnePieceBridge.isFruitUser(player)) {
						OnePieceBridge.drainFruitPower(player, 140 + 40 * extra);
					}
				}
				strikes.signature("ground_wave", boss, target, level, damage, extra);
				strikes.signature("rain_metal", boss, target, level, damage * 0.8f, extra);
			}
			case "gasha_fortress" -> { // Bullet: fuses all the metal around into armour (hard to hurt for a while), and the scrap comes down.
				boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100 + 20 * extra, 1));
				boss.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 200, 3 + extra));
				MoveFx.shockwave(level, boss.position(), 10, 0xFFD0D0D8, 0xFF505060);
				level.sendParticles(ParticleTypes.CRIT, boss.getX(), boss.getY() + 1.5, boss.getZ(), 80, 1.5, 1.5, 1.5, 0.3);
				level.playSound(null, boss.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.HOSTILE, 2.0f, 0.5f);
				level.playSound(null, boss.blockPosition(), SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 2.0f, 0.6f);
				strikes.signature("rain_metal", boss, target, level, damage, extra + 2);
				strikes.signature("ground_wave", boss, target, level, damage, extra);
			}
			case "lion_float" -> { // Shiki: floats everyone into the sky and lets go, while he drops floating rock on them.
				for (Player player : playersNear(boss, level, 14)) {
					player.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 30 + 10 * extra, 1));
					level.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY(), player.getZ(), 15, 0.4, 0.2, 0.4, 0.05);
				}
				level.playSound(null, boss.blockPosition(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.0f, 0.6f);
				strikes.signature("rain_rock", boss, target, level, damage, extra + 2);
			}
			case "goe_goe_blast" -> { // El Drago: a roar that flies down the line and bursts, deafening (nausea) and blowing everyone back.
				strikes.signature("slash_line", boss, target, level, damage, extra);
				for (Player player : playersNear(boss, level, 10)) {
					player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100 + 20 * extra, 0));
					Vec3 away = player.position().subtract(boss.position()).multiply(1, 0, 1).normalize().scale(1.4);
					player.setDeltaMovement(away.x, 0.5, away.z);
					player.needsSync = true;
				}
				MoveFx.shockwave(level, boss.position(), 10, MoveFx.QUAKE, MoveFx.QUAKE_OUT);
				level.sendParticles(ParticleTypes.SONIC_BOOM, boss.getX(), boss.getEyeY(), boss.getZ(), 1, 0, 0, 0, 0);
				level.playSound(null, boss.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3.0f, 0.8f);
			}
			case "syrup_flood" -> { // Gasparde: a wave of candy syrup glues everyone in place, then it sets into spikes under them.
				for (Player player : playersNear(boss, level, 11)) {
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60 + 20 * extra, 5));
					player.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 80, 2));
					level.sendParticles(ParticleTypes.DRIPPING_HONEY, player.getX(), player.getY() + 1.2, player.getZ(), 25, 0.4, 0.6, 0.4, 0.02);
				}
				MoveFx.shockwave(level, boss.position(), 11, 0xFFFFE0A0, 0xFFC88020);
				level.playSound(null, boss.blockPosition(), SoundEvents.HONEY_BLOCK_SLIDE, SoundSource.HOSTILE, 3.0f, 0.5f);
				strikes.signature("ground_wave", boss, target, level, damage, extra);
				strikes.signature("rain_metal", boss, target, level, damage * 0.7f, extra); // the syrup spikes
			}
			case "lily_arrow_storm" -> { // Omatsuri: Lily Carnation drinks from everyone nearby and turns into a rain of arrows.
				float drained = 0;
				for (Player player : playersNear(boss, level, 12)) {
					player.addEffect(new MobEffectInstance(MobEffects.WITHER, 60 + 20 * extra, 0));
					level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, player.getX(), player.getY() + 1, player.getZ(), 20, 0.5, 0.8, 0.5, 0.0);
					drained += 1;
				}
				boss.heal(boss.getMaxHealth() * 0.015f * Math.min(drained, 3)); // Lily keeps her host alive.
				level.playSound(null, boss.blockPosition(), SoundEvents.ARROW_SHOOT, SoundSource.HOSTILE, 3.0f, 0.6f);
				level.playSound(null, boss.blockPosition(), SoundEvents.SPORE_BLOSSOM_PLACE, SoundSource.HOSTILE, 3.0f, 0.5f);
				strikes.signature("rain_plant", boss, target, level, damage, extra + 3);
			}
			case "super_zogame" -> { // Ratchet: his rocket claw hauls you in front of the drill, while the turtle's four shell cannons fire.
				pull(target, boss, 1.6);
				strikes.signature("slash_line", boss, target, level, damage, extra);
				strikes.signature("rain_fire", boss, target, level, damage * 0.8f, extra + 1);
				level.playSound(null, boss.blockPosition(), SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0f, 0.5f);
				level.playSound(null, boss.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5f, 1.2f);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, boss.getX(), boss.getY() + 1, boss.getZ(), 30, 1.0, 0.8, 1.0, 0.05);
			}
			case "moa_moa_hundred" -> { // World: a handful of pebbles thrown a hundred times faster and bigger. He speeds himself up too.
				boss.addEffect(new MobEffectInstance(MobEffects.SPEED, 100 + 20 * extra, 2));
				level.sendParticles(ParticleTypes.EXPLOSION, boss.getX(), boss.getY() + 1.5, boss.getZ(), 6, 1.5, 1.0, 1.5, 0.0);
				level.playSound(null, boss.blockPosition(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.5f, 0.5f);
				strikes.signature("rain_rock", boss, target, level, damage * 1.1f, extra + 4);
				strikes.signature("ground_wave", boss, target, level, damage, extra);
			}
			case "hot_boiling_special" -> { // Bear King: the Kachi Kachi Fruit hardens him like stone and his fists boil; then the King Cannon's drill shells.
				boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 80 + 20 * extra, 1));
				Vec3 away = target.position().subtract(boss.position()).multiply(1, 0, 1).normalize().scale(1.6);
				target.setDeltaMovement(away.x, 0.6, away.z);
				target.needsSync = true;
				target.igniteForSeconds(4 + 2 * extra);
				level.sendParticles(ParticleTypes.LAVA, boss.getX(), boss.getY() + 1.4, boss.getZ(), 20, 0.6, 0.6, 0.6, 0.0);
				level.playSound(null, boss.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0f, 0.6f);
				level.playSound(null, boss.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5f, 0.5f);
				strikes.signature("ground_wave", boss, target, level, damage, extra);
				strikes.signature("rain_metal", boss, target, level, damage * 0.8f, extra + 1); // the drilling shells
			}
			case "festival_finale" -> { // Festa: the Expo's grand finale, fireworks bursting over everyone (dazzled, lit up), then they rain down.
				for (Player player : playersNear(boss, level, 14)) {
					player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30 + 10 * extra, 0));
					player.addEffect(new MobEffectInstance(MobEffects.GLOWING, 120 + 20 * extra, 0));
					level.sendParticles(ParticleTypes.FIREWORK, player.getX(), player.getY() + 3, player.getZ(), 40, 1.2, 0.8, 1.2, 0.15);
				}
				for (int i = 0; i < 16; i++) {
					double a = Math.PI * 2 * i / 16;
					level.sendParticles(ParticleTypes.FIREWORK, boss.getX() + Math.cos(a) * 5, boss.getY() + 6, boss.getZ() + Math.sin(a) * 5, 12, 0.5, 0.5, 0.5, 0.2);
				}
				level.playSound(null, boss.blockPosition(), SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.HOSTILE, 3.0f, 0.8f);
				level.playSound(null, boss.blockPosition(), SoundEvents.FIREWORK_ROCKET_TWINKLE, SoundSource.HOSTILE, 3.0f, 1.0f);
				strikes.signature("rain_fire", boss, target, level, damage, extra + 3);
			}
			case "dark_fire_slash" -> { // Saga: Youkazan, a cut of the Seven Star Sword's green fire down the line, and its curse withers whoever's close.
				strikes.signature("slash_line", boss, target, level, damage * 1.1f, extra);
				for (Player player : playersNear(boss, level, 9)) {
					player.addEffect(new MobEffectInstance(MobEffects.WITHER, 60 + 20 * extra, 1));
					level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, player.getX(), player.getY() + 1, player.getZ(), 25, 0.4, 0.8, 0.4, 0.03);
				}
				MoveFx.shockwave(level, boss.position(), 9, 0xFF60E070, 0xFF206030);
				level.playSound(null, boss.blockPosition(), SoundEvents.WITHER_SHOOT, SoundSource.HOSTILE, 2.0f, 0.7f);
				strikes.signature("rain_curse", boss, target, level, damage * 0.8f, extra + 1);
			}
			case "golden_horn_frenzy" -> { // Butler: he eats the golden horns and turns into a giant golden beast with fiery horns, and charges.
				boss.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 140 + 20 * extra, 1));
				boss.addEffect(new MobEffectInstance(MobEffects.SPEED, 100 + 20 * extra, 1));
				boss.heal(boss.getMaxHealth() * 0.04f);
				level.sendParticles(ParticleTypes.FLAME, boss.getX(), boss.getY() + 2.4, boss.getZ(), 40, 0.5, 0.4, 0.5, 0.04);
				level.playSound(null, boss.blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0f, 0.7f);
				pull(target, boss, 1.5); // he hooks you on his horns
				target.igniteForSeconds(3 + extra);
				strikes.signature("slash_line", boss, target, level, damage, extra);
				strikes.signature("rain_fire", boss, target, level, damage * 0.7f, extra);
			}
			case "harpoon_volley" -> { // Maribel fires a harpoon into you and reels you in, while her whalers' harpoons rain down.
				pull(target, boss, 1.6);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50 + 20 * extra, 2));
				level.playSound(null, boss.blockPosition(), SoundEvents.FISHING_BOBBER_THROW, SoundSource.HOSTILE, 2.0f, 0.5f);
				level.playSound(null, target.blockPosition(), SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.5f, 0.6f);
				strikes.signature("rain_metal", boss, target, level, damage, extra + 2);
			}
			case "tithe_of_bells" -> { // Lume's bell tolls: everyone near pays a tenth of their life, and it mends him, then judgment light falls.
				float paid = 0;
				for (Player player : playersNear(boss, level, 14)) {
					float tithe = Math.max(1.0f, player.getHealth() * 0.1f * (1 + extra));
					player.hurtServer(level, boss.damageSources().magic(), tithe);
					player.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60 + 20 * extra, 0));
					level.sendParticles(ParticleTypes.SOUL, player.getX(), player.getY() + 1, player.getZ(), 10, 0.3, 0.6, 0.3, 0.03);
					paid += tithe;
				}
				boss.heal(paid);
				for (int i = 0; i < 3; i++) {
					level.playSound(null, boss.blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0f, 0.5f + i * 0.1f);
				}
				MoveFx.shockwave(level, boss.position(), 14, MoveFx.DARK, MoveFx.DARK_OUT);
				strikes.signature("rain_light", boss, target, level, damage, extra + 1);
			}
			case "cinder_broadside" -> { // Kael: fire shot from every gun, the deck itself bursts into flame around him.
				strikes.signature("rain_fire", boss, target, level, damage, extra + 3);
				strikes.signature("ground_wave", boss, target, level, damage * 0.8f, extra);
				for (Player player : playersNear(boss, level, 10)) {
					player.igniteForSeconds(5 + 2 * extra);
				}
				MoveFx.shockwave(level, boss.position(), 10, MoveFx.FIRE, MoveFx.FIRE_OUT);
				level.sendParticles(ParticleTypes.LAVA, boss.getX(), boss.getY() + 1, boss.getZ(), 30, 2.0, 1.0, 2.0, 0.1);
				level.playSound(null, boss.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5f, 0.6f);
			}
			default -> strikes.signature(signature, boss, target, level, damage, extra); // Any main mod signature works too.
		}
	}

	/** Pulls the target toward the boss. */
	private static void pull(LivingEntity target, Mob boss, double strength) {
		Vec3 toward = boss.position().subtract(target.position()).normalize().scale(strength);
		target.setDeltaMovement(toward.x, 0.3, toward.z);
		target.needsSync = true;
	}

	/** The spot itself, or one a block up or down, where the boss can stand: solid below, two blocks of air. Null if none. */
	private static BlockPos safeSpot(ServerLevel level, BlockPos pos) {
		for (int dy : new int[] {0, 1, -1}) {
			BlockPos p = pos.offset(0, dy, 0);
			if (level.getBlockState(p.below()).isFaceSturdy(level, p.below(), Direction.UP)
					&& level.getBlockState(p).getCollisionShape(level, p).isEmpty()
					&& level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()) {
				return p;
			}
		}
		return null;
	}

	private static List<Player> playersNear(Mob boss, ServerLevel level, double radius) {
		return level.getEntitiesOfClass(Player.class, boss.getBoundingBox().inflate(radius),
				player -> player.isAlive() && !player.isCreative() && !player.isSpectator());
	}
}
