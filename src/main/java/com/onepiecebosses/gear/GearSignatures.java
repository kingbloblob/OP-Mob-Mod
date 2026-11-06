package com.onepiecebosses.gear;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import com.onepiecebosses.boss.RogueData;
import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecemod.fx.MoveFx;

/**
 * The gear sets' signature moves: a player-sized take on each boss's phase 3 move (boss/RogueSignatures).
 * They only touch foes: monsters, anything hunting you, and whatever you struck. Never other players or your pets.
 *
 * Damage grows with the boss's tier (6 for a tier 1 set up to 14 for tier 5), and a quarter more with the set's weapon.
 */
public final class GearSignatures {
	private GearSignatures() {
	}

	public static void use(String boss, ServerPlayer player, LivingEntity target, ServerLevel level, boolean withWeapon) {
		RogueData data = RogueData.get(boss);
		int tier = data != null ? data.tier() : 1;
		float damage = (4 + 2 * tier) * (withWeapon ? 1.25f : 1.0f);
		List<LivingEntity> hurt = new ArrayList<>();

		switch (boss) {
			case "saltjaw_rourke" -> { // Anchor Drag: haul the foe to you along the chain, slow it, and cut down the line.
				pull(target, player, 1.2);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
				for (LivingEntity foe : line(player, target, level, 8)) {
					hit(player, foe, damage, level, hurt);
				}
				level.playSound(null, player.blockPosition(), SoundEvents.CHAIN_BREAK, SoundSource.PLAYERS, 1.5f, 0.6f);
				sweep(level, player, 8, ParticleTypes.SWEEP_ATTACK);
			}
			case "corvina_fog_widow" -> { // Widow's Veil: fog blinds foes near you, you vanish and step out behind your target.
				for (LivingEntity foe : foes(player, target, level, 8)) {
					foe.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 80, 0));
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
					if (foe instanceof Mob mob && mob.getTarget() == player) {
						mob.setTarget(null); // Lost you in the fog.
					}
				}
				level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, player.getX(), player.getY() + 1, player.getZ(), 60, 2.5, 1.2, 2.5, 0.01);
				player.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 80, 0));
				player.addEffect(new MobEffectInstance(MobEffects.SPEED, 80, 1));
				Vec3 behind = target.position().subtract(target.getLookAngle().multiply(1, 0, 1).scale(1.5));
				BlockPos spot = safeSpot(level, BlockPos.containing(behind.x, target.getY(), behind.z));
				if (spot != null) {
					player.teleportTo(behind.x, spot.getY(), behind.z);
				}
				hit(player, target, damage, level, hurt);
				level.playSound(null, player.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 1.5f, 0.8f);
			}
			case "iron_tide_graves" -> { // Seastone Volley: shot rains around you, weighs foes down and drains fruit users.
				for (LivingEntity foe : foes(player, target, level, 7)) {
					hit(player, foe, damage, level, hurt);
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
					if (OnePieceBridge.isFruitUser(foe)) {
						OnePieceBridge.drainFruitPower(foe, 100);
					}
					level.sendParticles(ParticleTypes.EXPLOSION, foe.getX(), foe.getY() + 0.5, foe.getZ(), 1, 0, 0, 0, 0);
				}
				level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.2f, 1.4f);
			}
			case "hollow_ronin_tsurugi" -> { // Hollow Cut: a flying cut down the line, and the curse withers what it passes.
				for (LivingEntity foe : line(player, target, level, 12)) {
					hit(player, foe, damage * 1.15f, level, hurt);
					foe.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1));
				}
				sweep(level, player, 12, ParticleTypes.SOUL);
				level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.5f, 0.5f);
			}
			case "boilerheart_gantz" -> { // Boiler Burst: scalding steam all around, burning foes and blowing them back.
				for (LivingEntity foe : foes(player, target, level, 6)) {
					hit(player, foe, damage, level, hurt);
					foe.igniteForSeconds(5);
					push(foe, player, 1.0, 0.4);
				}
				player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 100, 0));
				MoveFx.shockwave(level, player.position(), 6, MoveFx.FIRE, MoveFx.FIRE_OUT);
				level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1.5, player.getZ(), 40, 1.0, 0.5, 1.0, 0.15);
				level.playSound(null, player.blockPosition(), SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 2.0f, 0.5f);
			}
			case "nereus_vane" -> { // Tidal Judgment: a whirlpool drags the foes around you into your target, and the deep weighs on them.
				for (LivingEntity foe : foes(player, target, level, 10)) {
					if (foe != target) {
						pull(foe, target, 1.1);
					}
					hit(player, foe, damage * 0.8f, level, hurt);
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
					foe.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 100, 1));
				}
				level.sendParticles(ParticleTypes.SPLASH, target.getX(), target.getY() + 0.5, target.getZ(), 120, 3, 0.5, 3, 0.3);
				level.sendParticles(ParticleTypes.BUBBLE_POP, target.getX(), target.getY() + 1, target.getZ(), 40, 1.5, 1, 1.5, 0.1);
				level.playSound(null, player.blockPosition(), SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.PLAYERS, 0.8f, 1.2f);
			}
			case "khamsin_sandshackle" -> { // Sandshackle Storm: sand blinds the foes around you, and the one you struck is chained.
				for (LivingEntity foe : foes(player, target, level, 8)) {
					foe.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0));
					hit(player, foe, damage * 0.6f, level, hurt);
				}
				pull(target, player, 1.0);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 3)); // Shackled.
				hit(player, target, damage * 0.6f, level, hurt);
				level.sendParticles(ParticleTypes.WHITE_ASH, player.getX(), player.getY() + 2, player.getZ(), 160, 5, 2, 5, 0.05);
				MoveFx.shockwave(level, player.position(), 8, MoveFx.SAND, MoveFx.SAND_OUT);
				level.playSound(null, player.blockPosition(), SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.5f, 0.5f);
			}
			case "mortimer_gale" -> { // The Doubloon's Curse: cursed gold withers the foes around you, and their years mend you.
				int taken = 0;
				for (LivingEntity foe : foes(player, target, level, 8)) {
					foe.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
					foe.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 0));
					hit(player, foe, damage * 0.5f, level, hurt);
					level.sendParticles(ParticleTypes.SOUL, foe.getX(), foe.getY() + 1, foe.getZ(), 10, 0.3, 0.6, 0.3, 0.03);
					taken++;
				}
				player.heal(2.0f * Math.min(taken, 4));
				level.playSound(null, player.blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 1.5f, 0.5f);
			}
			case "vasco_tidebreaker" -> { // Leviathan Charge: surge forward and throw the foes in your path up in a wall of seawater.
				Vec3 at = target.position().subtract(player.position()).multiply(1, 0, 1);
				if (at.lengthSqr() > 0.01) {
					Vec3 dash = at.normalize().scale(Math.min(1.6, at.length() * 0.4));
					player.setDeltaMovement(dash.x, 0.25, dash.z);
					player.needsSync = true;
					// A player's own game moves them, so the dash has to be sent to it.
					player.connection.send(new ClientboundSetEntityMotionPacket(player));
				}
				for (LivingEntity foe : line(player, target, level, 8)) {
					hit(player, foe, damage, level, hurt);
					push(foe, player, 1.0, 0.8);
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
				}
				level.sendParticles(ParticleTypes.SPLASH, target.getX(), target.getY() + 0.5, target.getZ(), 150, 2, 1, 2, 0.4);
				level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_SPLASH, SoundSource.PLAYERS, 2.0f, 0.7f);
			}
			case "doctor_kreuz" -> { // Prototype Barrage: a paw-pad blast throws foes back, lasers strike them, a shield covers you.
				for (LivingEntity foe : foes(player, target, level, 7)) {
					hit(player, foe, damage, level, hurt);
					push(foe, player, 1.6, 0.8);
					level.sendParticles(ParticleTypes.ELECTRIC_SPARK, foe.getX(), foe.getY() + 1, foe.getZ(), 20, 0.3, 0.6, 0.3, 0.2);
				}
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100, 1));
				MoveFx.shockwave(level, player.position(), 7, 0xFFE8F0FF, 0xFF3A6AC8);
				level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.5f, 0.6f);
			}
			case "gild_tesoro" -> { // Golden Finale: gold grabs every foe around you and molten gold strikes them.
				for (LivingEntity foe : foes(player, target, level, 9)) {
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 4));
					foe.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 1));
					hit(player, foe, damage * 0.8f, level, hurt);
					level.sendParticles(ParticleTypes.WAX_ON, foe.getX(), foe.getY() + 1, foe.getZ(), 25, 0.4, 0.8, 0.4, 0.05);
				}
				MoveFx.shockwave(level, player.position(), 9, MoveFx.GOLD, MoveFx.GOLD_OUT);
				level.playSound(null, player.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 1.2f, 0.7f);
			}
			case "uta_diva" -> { // Uta World: your song lulls every foe around you, notes fall on them and you are healed.
				for (LivingEntity foe : foes(player, target, level, 12)) {
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 2));
					foe.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
					foe.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
					hit(player, foe, damage * 0.7f, level, hurt);
				}
				for (int i = 0; i < 24; i++) {
					double a = Math.PI * 2 * i / 24;
					level.sendParticles(ParticleTypes.NOTE, player.getX() + Math.cos(a) * 5, player.getY() + 2, player.getZ() + Math.sin(a) * 5, 1, 0, 0, 0, i / 24.0);
				}
				player.heal(6.0f);
				level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 2.0f, 0.9f);
				level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.PLAYERS, 2.0f, 1.2f);
			}
			case "zephyr_z" -> { // Battle Smasher: a seastone haymaker blasts your target away and drains fruit users near it.
				hit(player, target, damage * 1.5f, level, hurt);
				push(target, player, 2.4, 0.9);
				for (LivingEntity foe : foes(player, target, level, 8)) {
					if (OnePieceBridge.isFruitUser(foe)) {
						OnePieceBridge.drainFruitPower(foe, 140);
					}
				}
				level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, target.getX(), target.getY() + 1, target.getZ(), 1, 0, 0, 0, 0);
				level.playSound(null, target.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.5f, 0.8f);
			}
			case "douglas_bullet" -> { // Gashapon Fortress: scrap fuses onto you as armour while it slams into the foes around you.
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 120, 1));
				player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 200, 2));
				for (LivingEntity foe : foes(player, target, level, 7)) {
					hit(player, foe, damage, level, hurt);
					level.sendParticles(ParticleTypes.CRIT, foe.getX(), foe.getY() + 1, foe.getZ(), 15, 0.4, 0.6, 0.4, 0.3);
				}
				MoveFx.shockwave(level, player.position(), 7, 0xFFD0D0D8, 0xFF505060);
				level.playSound(null, player.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.PLAYERS, 1.5f, 0.5f);
			}
			case "shiki_golden_lion" -> { // Lion Float: the foes around you float into the sky, then you let go.
				for (LivingEntity foe : foes(player, target, level, 10)) {
					foe.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 40, 2));
					hit(player, foe, damage * 0.6f, level, hurt);
					level.sendParticles(ParticleTypes.END_ROD, foe.getX(), foe.getY(), foe.getZ(), 12, 0.4, 0.2, 0.4, 0.05);
				}
				level.playSound(null, player.blockPosition(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 1.5f, 0.6f);
			}
			case "el_drago" -> { // Goe Goe Blast: a roar flies down the line, hurting, dazing and blowing back every foe it hits.
				for (LivingEntity foe : line(player, target, level, 14)) {
					hit(player, foe, damage, level, hurt);
					foe.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
					push(foe, player, 1.4, 0.5);
				}
				Vec3 eye = player.getEyePosition().add(player.getLookAngle().scale(2));
				level.sendParticles(ParticleTypes.SONIC_BOOM, eye.x, eye.y, eye.z, 1, 0, 0, 0, 0);
				level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 1.5f, 1.0f);
			}
			case "gasparde" -> { // Syrup Flood: syrup glues every foe around you in place, then sets into spikes.
				for (LivingEntity foe : foes(player, target, level, 8)) {
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 5));
					foe.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 100, 2));
					hit(player, foe, damage * 0.8f, level, hurt);
					level.sendParticles(ParticleTypes.DRIPPING_HONEY, foe.getX(), foe.getY() + 1.2, foe.getZ(), 20, 0.4, 0.6, 0.4, 0.02);
				}
				MoveFx.shockwave(level, player.position(), 8, 0xFFFFE0A0, 0xFFC88020);
				level.playSound(null, player.blockPosition(), SoundEvents.HONEY_BLOCK_SLIDE, SoundSource.PLAYERS, 2.0f, 0.5f);
			}
			case "baron_omatsuri" -> { // Lily Arrow Storm: Lily drinks from the foes around you and their life flows into you.
				int drained = 0;
				for (LivingEntity foe : foes(player, target, level, 9)) {
					foe.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1));
					hit(player, foe, damage * 0.7f, level, hurt);
					level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, foe.getX(), foe.getY() + 1, foe.getZ(), 15, 0.5, 0.8, 0.5, 0.0);
					drained++;
				}
				player.heal(2.5f * Math.min(drained, 4));
				level.playSound(null, player.blockPosition(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS, 2.0f, 0.6f);
			}
			case "ratchet" -> { // Super Zogame-kun: a rocket claw hauls your target in, then shell cannons burst around it.
				pull(target, player, 1.4);
				for (LivingEntity foe : foes(player, target, level, 6)) {
					if (foe.distanceTo(target) <= 4 || foe == target) {
						hit(player, foe, damage, level, hurt);
						foe.igniteForSeconds(3);
					}
				}
				level.sendParticles(ParticleTypes.EXPLOSION, target.getX(), target.getY() + 1, target.getZ(), 4, 1.5, 0.5, 1.5, 0);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, target.getX(), target.getY() + 1, target.getZ(), 25, 1.0, 0.8, 1.0, 0.05);
				level.playSound(null, player.blockPosition(), SoundEvents.PISTON_EXTEND, SoundSource.PLAYERS, 1.5f, 0.5f);
				level.playSound(null, target.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.2f, 1.2f);
			}
			case "byrnndi_world" -> { // Moa Moa Hundred: you move a hundred times faster and boulders burst around your target.
				player.addEffect(new MobEffectInstance(MobEffects.SPEED, 100, 2));
				for (LivingEntity foe : foes(player, target, level, 8)) {
					if (foe.distanceTo(target) <= 5 || foe == target) {
						hit(player, foe, damage * 1.1f, level, hurt);
						push(foe, target, 0.6, 0.5);
					}
				}
				level.sendParticles(ParticleTypes.EXPLOSION, target.getX(), target.getY() + 1, target.getZ(), 5, 1.5, 1.0, 1.5, 0.0);
				MoveFx.shockwave(level, target.position(), 5, MoveFx.QUAKE, MoveFx.QUAKE_OUT);
				level.playSound(null, player.blockPosition(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 2.0f, 0.5f);
			}
			// ---- Sets for bosses other branches add (ignored until the boss is in bosses.json) ----
			case "bear_king" -> { // Hot Boiling Special: burning fists for the struck foe and those around it, and stone-hard skin.
				for (LivingEntity foe : foes(player, target, level, 6)) {
					if (foe.distanceTo(target) <= 4 || foe == target) {
						hit(player, foe, foe == target ? damage * 1.2f : damage * 0.7f, level, hurt);
						foe.igniteForSeconds(4);
						push(foe, player, 1.2, 0.5);
					}
				}
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100, 1));
				MoveFx.shockwave(level, target.position(), 4, MoveFx.MAGMA, MoveFx.MAGMA_OUT);
				level.playSound(null, player.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.PLAYERS, 1.5f, 0.6f);
			}
			case "buena_festa" -> { // Festival Finale: fireworks burst over every foe around you.
				for (LivingEntity foe : foes(player, target, level, 9)) {
					hit(player, foe, damage * 0.8f, level, hurt);
					foe.igniteForSeconds(3);
					foe.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
					level.sendParticles(ParticleTypes.FIREWORK, foe.getX(), foe.getY() + 2, foe.getZ(), 30, 0.6, 0.6, 0.6, 0.15);
				}
				level.playSound(null, player.blockPosition(), SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.PLAYERS, 2.0f, 1.0f);
			}
			case "saga" -> { // Dark Fire Slash: a cut of green fire down the line, burning and withering.
				for (LivingEntity foe : line(player, target, level, 12)) {
					hit(player, foe, damage * 1.15f, level, hurt);
					foe.igniteForSeconds(4);
					foe.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 1));
				}
				sweep(level, player, 12, ParticleTypes.SOUL_FIRE_FLAME);
				level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.5f, 0.6f);
			}
			case "count_butler" -> { // Golden Horn Frenzy: the violin hypnotises the foes around you, then a horned charge.
				for (LivingEntity foe : foes(player, target, level, 10)) {
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
					foe.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 1));
					if (foe instanceof Mob mob && mob.getTarget() == player && foe != target) {
						mob.setTarget(null); // Lulled by the violin.
					}
					level.sendParticles(ParticleTypes.NOTE, foe.getX(), foe.getY() + 2.2, foe.getZ(), 3, 0.3, 0.2, 0.3, 0.5);
				}
				hit(player, target, damage * 1.3f, level, hurt);
				target.igniteForSeconds(3);
				push(target, player, 1.6, 0.6);
				level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_HARP.value(), SoundSource.PLAYERS, 2.0f, 0.8f);
				level.playSound(null, player.blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.PLAYERS, 1.0f, 1.2f);
			}
			case "maribel_sedge" -> { // Harpoon Volley: harpoons reel every foe around you in, slowed.
				for (LivingEntity foe : foes(player, target, level, 10)) {
					pull(foe, player, 1.1);
					hit(player, foe, damage * 0.8f, level, hurt);
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
					level.sendParticles(ParticleTypes.CRIT, foe.getX(), foe.getY() + 1, foe.getZ(), 10, 0.3, 0.5, 0.3, 0.2);
				}
				level.playSound(null, player.blockPosition(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS, 1.5f, 0.8f);
				level.playSound(null, player.blockPosition(), SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.2f, 0.7f);
			}
			case "severo_lume" -> { // Tithe of Bells: the toll stuns the foes around you and their tithe heals you.
				int tithed = 0;
				for (LivingEntity foe : foes(player, target, level, 9)) {
					foe.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 3));
					foe.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 80, 1));
					foe.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
					hit(player, foe, damage * 0.7f, level, hurt);
					tithed++;
				}
				player.heal(2.0f * Math.min(tithed, 5));
				MoveFx.shockwave(level, player.position(), 9, MoveFx.GOLD, 0xFFA01818);
				level.playSound(null, player.blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 2.5f, 0.6f);
			}
			case "kael_ashgrave" -> { // Cinder Broadside: burning shot sets every foe around you alight and blasts them back.
				for (LivingEntity foe : foes(player, target, level, 8)) {
					hit(player, foe, damage, level, hurt);
					foe.igniteForSeconds(6);
					push(foe, player, 1.3, 0.6);
					level.sendParticles(ParticleTypes.EXPLOSION, foe.getX(), foe.getY() + 0.8, foe.getZ(), 1, 0, 0, 0, 0);
				}
				player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 120, 0));
				MoveFx.shockwave(level, player.position(), 8, MoveFx.FIRE, MoveFx.FIRE_OUT);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, player.getX(), player.getY() + 1, player.getZ(), 40, 2, 1, 2, 0.05);
				level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.5f, 0.9f);
			}
			default -> hit(player, target, damage, level, hurt);
		}

		// Let the swing that set this off land in full, and whatever else hits them next.
		for (LivingEntity foe : hurt) {
			foe.setInvulnerableTime(0);
		}
	}

	private static void hit(ServerPlayer player, LivingEntity foe, float damage, ServerLevel level, List<LivingEntity> hurt) {
		foe.setInvulnerableTime(0);
		foe.hurtServer(level, player.damageSources().playerAttack(player), damage);
		hurt.add(foe);
	}

	/** Foes within this radius of the player: monsters, mobs hunting the player, and the struck target. Never other players, pets or armour stands. */
	static List<LivingEntity> foes(ServerPlayer player, LivingEntity target, ServerLevel level, double radius) {
		List<LivingEntity> found = level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
				e -> e != player && e.isAlive() && isFoe(player, target, e) && e.distanceTo(player) <= radius);
		if (target.isAlive() && !found.contains(target)) {
			found.add(target);
		}
		return found;
	}

	/** Foes along a line from the player toward the target, this long and about two blocks wide. */
	static List<LivingEntity> line(ServerPlayer player, LivingEntity target, ServerLevel level, double length) {
		Vec3 start = player.position();
		Vec3 dir = target.position().subtract(start).multiply(1, 0, 1);
		dir = dir.lengthSqr() < 0.01 ? player.getLookAngle().multiply(1, 0, 1).normalize() : dir.normalize();
		Vec3 along = dir;
		List<LivingEntity> found = new ArrayList<>();
		for (LivingEntity e : foes(player, target, level, length + 1)) {
			Vec3 rel = e.position().subtract(start);
			double t = rel.x * along.x + rel.z * along.z;
			double side = Math.abs(rel.x * along.z - rel.z * along.x);
			if ((t >= 0 && t <= length && side <= 1.5 + e.getBbWidth() / 2) || e == target) {
				found.add(e);
			}
		}
		return found;
	}

	private static boolean isFoe(ServerPlayer player, LivingEntity target, LivingEntity e) {
		if (e == target) {
			return true;
		}
		if (e instanceof Player) {
			return false;
		}
		// Monsters and anything hunting you. Pets, villagers and armour stands are neither.
		return e instanceof Enemy || (e instanceof Mob mob && mob.getTarget() == player);
	}

	private static void pull(LivingEntity foe, LivingEntity toward, double strength) {
		Vec3 dir = toward.position().subtract(foe.position());
		if (dir.lengthSqr() < 1.0) {
			return;
		}
		Vec3 v = dir.normalize().scale(strength);
		foe.setDeltaMovement(v.x, 0.3, v.z);
		foe.needsSync = true;
	}

	private static void push(LivingEntity foe, LivingEntity from, double strength, double up) {
		Vec3 dir = foe.position().subtract(from.position()).multiply(1, 0, 1);
		Vec3 v = dir.lengthSqr() < 0.01 ? Vec3.ZERO : dir.normalize().scale(strength);
		foe.setDeltaMovement(v.x, up, v.z);
		foe.needsSync = true;
	}

	/** A trail of particles down the line the player faces. */
	private static void sweep(ServerLevel level, ServerPlayer player, double length, net.minecraft.core.particles.SimpleParticleType particle) {
		Vec3 dir = player.getLookAngle().multiply(1, 0, 1).normalize();
		for (double d = 1; d <= length; d += 1) {
			level.sendParticles(particle, player.getX() + dir.x * d, player.getY() + 1, player.getZ() + dir.z * d, 2, 0.2, 0.2, 0.2, 0.0);
		}
	}

	/** The spot itself, or one a block up or down, with solid ground below and two blocks of air. Null if none. */
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
}
