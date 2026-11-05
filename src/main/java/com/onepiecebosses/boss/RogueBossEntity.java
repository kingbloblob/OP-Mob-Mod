package com.onepiecebosses.boss;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecebosses.compat.OnePieceBridge;
import com.onepiecebosses.loot.BossRewards;
import com.onepiecemod.character.BossStrikes;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;

/**
 * A rogue boss. It is the One Piece Mod's own boss mob with its data swapped for ours (getData), so the main mod
 * runs the fight: boss bar, phases at 66% and 33%, wind-ups, Hard and Expert rematches, Berries and bounty.
 *
 * On top of that this class adds what the main mod only does for its story bosses (whose fight data comes from
 * its own boss_fights.json): the boss's lines, its crew from crews.json, and its own phase 3 signature move.
 */
public class RogueBossEntity extends CharacterEntity {
	/** Players this far away hear the boss's lines. */
	private static final double SHOUT_RANGE = 32.0;
	/** Ticks between signature moves in phase 3 on Normal; Hard and Expert are quicker. */
	private static final int SIGNATURE_TICKS = 220;
	/** Players this close when the boss falls share the win (the main mod's boss bar range). */
	private static final double WIN_RANGE = 40.0;

	private final BossStrikes strikes = new BossStrikes();
	private final List<UUID> crew = new ArrayList<>();
	private int phaseSeen = 0; // 0 = not worked out yet (fresh spawn or just loaded)
	private boolean introDone = false;
	private int signatureCooldown = 60;
	private String sizedFor = "";

	public RogueBossEntity(EntityType<? extends RogueBossEntity> type, Level level) {
		super(type, level);
	}

	/** Our boss data, in the main mod's format. Everything in CharacterEntity reads its stats through this. */
	@Override
	public CharacterData getData() {
		return rogue().character;
	}

	/** Each rogue's hitbox fits its own body (see RogueModels), not a player's. */
	@Override
	protected EntityDimensions getDefaultDimensions(Pose pose) {
		float[] size = rogue().hitbox;
		return EntityDimensions.scalable(size[0], size[1]);
	}

	@Override
	public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
		super.onSyncedDataUpdated(key);
		// Which rogue this is arrives as synced data; resize once it changes.
		String id = getCharacterId();
		if (!id.equals(sizedFor)) {
			sizedFor = id;
			refreshDimensions();
		}
	}

	public RogueData rogue() {
		RogueData data = RogueData.get(getCharacterId());
		return data != null ? data : RogueData.fallback();
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (!isBoss()) {
			return;
		}
		strikes.tick(this, level);

		LivingEntity target = getTarget();
		boolean fighting = target instanceof Player && target.isAlive();
		if (fighting && !introDone) {
			introDone = true;
			shout(level, rogue().intro);
			callCrew(level, target);
		}

		int phase = phaseFor();
		if (phaseSeen == 0) {
			phaseSeen = phase; // Just loaded: carry on quietly.
		} else if (phase > phaseSeen) {
			phaseSeen = phase;
			shout(level, phase == 2 ? rogue().phase2 : rogue().phase3);
			if (phase == 2 && fighting) {
				callCrew(level, target); // Second wave.
			}
			signatureCooldown = 40; // The first signature comes soon after phase 3 starts.
		}

		if (phaseSeen >= 3 && fighting && distanceTo(target) < 20 && --signatureCooldown <= 0) {
			signatureCooldown = SIGNATURE_TICKS - 40 * getDifficulty();
			RogueSignatures.use(rogue().signature, this, target, level, strikes,
					(float) getAttributeValue(Attributes.ATTACK_DAMAGE), getDifficulty());
		}
	}

	/** Phase 1 above 66% health, phase 2 above 33%, then phase 3 (the same as the main mod's bosses). */
	private int phaseFor() {
		float share = getHealth() / getMaxHealth();
		return share < 0.33f ? 3 : share < 0.66f ? 2 : 1;
	}

	/** Calls a few of the boss's crew around it, and its beasts if it has any. Bosses with neither (Tsurugi, Bullet) fight alone. */
	private void callCrew(ServerLevel level, LivingEntity target) {
		String kit = rogue().crew;
		List<String> beasts = rogue().beasts;
		boolean hasCrew = kit != null && !kit.isEmpty();
		if (!hasCrew && beasts.isEmpty()) {
			return;
		}
		crew.removeIf(id -> {
			Entity member = level.getEntity(id);
			return member == null || !member.isAlive();
		});
		int count = hasCrew ? Math.min(2 + getDifficulty(), 5 - crew.size()) : 0;
		int called = 0;
		for (int i = 0; i < count; i++) {
			BlockPos spot = crewSpot(level);
			if (spot != null && join(level, OnePieceBridge.spawnMinion(level, kit, spot, getRandom().nextFloat() * 360f), target)) {
				called++;
			}
		}
		// Beasts on top of the crew: one, or two on Hard and Expert.
		int beastCount = beasts.isEmpty() ? 0 : Math.min(getDifficulty() > 0 ? 2 : 1, 7 - crew.size());
		for (int i = 0; i < beastCount; i++) {
			BlockPos spot = crewSpot(level);
			String beast = beasts.get(getRandom().nextInt(beasts.size()));
			if (spot != null && join(level, OnePieceBridge.spawnBeast(level, beast, spot, getRandom().nextFloat() * 360f), target)) {
				called++;
			}
		}
		if (called > 0) {
			for (ServerPlayer player : listeners(level)) {
				player.sendSystemMessage(Component.literal(getData().name + " calls their crew!").withStyle(ChatFormatting.GOLD), true);
			}
		}
	}

	/** A freshly called crew member or beast joins the fight. False if it couldn't be spawned. */
	private boolean join(ServerLevel level, Mob member, LivingEntity target) {
		if (member == null) {
			return false;
		}
		member.setTarget(target);
		crew.add(member.getUUID());
		level.sendParticles(ParticleTypes.POOF, member.getX(), member.getY() + 1, member.getZ(), 12, 0.3, 0.6, 0.3, 0.02);
		return true;
	}

	/** A free spot with solid ground 3-6 blocks from the boss, at about its height (works inside lairs too). */
	private BlockPos crewSpot(ServerLevel level) {
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = getRandom().nextDouble() * Math.PI * 2;
			double dist = 3 + getRandom().nextDouble() * 3;
			BlockPos base = BlockPos.containing(getX() + Math.cos(angle) * dist, getY(), getZ() + Math.sin(angle) * dist);
			for (int dy : new int[] {0, 1, -1, 2, -2}) {
				BlockPos pos = base.offset(0, dy, 0);
				if (level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
						&& level.getBlockState(pos).getCollisionShape(level, pos).isEmpty() && level.getFluidState(pos).isEmpty()
						&& level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty()) {
					return pos;
				}
			}
		}
		return null;
	}

	private List<ServerPlayer> listeners(ServerLevel level) {
		return level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(SHOUT_RANGE), player -> !player.isSpectator());
	}

	private void shout(ServerLevel level, String line) {
		if (line == null || line.isEmpty()) {
			return;
		}
		Component text = Component.literal(getData().name + ": ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(line).withStyle(ChatFormatting.RED));
		for (ServerPlayer player : listeners(level)) {
			player.sendSystemMessage(text);
		}
	}

	@Override
	public void die(DamageSource source) {
		if (isBoss() && level() instanceof ServerLevel level) {
			shout(level, rogue().defeat);
			// Worked out before super.die(), which marks everyone here as having beaten this boss.
			// The killer always counts, wherever they are (the main mod pays them too, from any range).
			List<ServerPlayer> nearby = new ArrayList<>(level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(WIN_RANGE), p -> !p.isSpectator()));
			if (source.getEntity() instanceof ServerPlayer killer && !nearby.contains(killer)) {
				nearby.add(killer);
			}
			List<ServerPlayer> firstTimers = new ArrayList<>();
			for (ServerPlayer player : nearby) {
				if (OnePieceBridge.unlockedDifficulty(player, getCharacterId()) == NORMAL) {
					firstTimers.add(player);
				}
			}
			BossRewards.topUpBounty(this, firstTimers);
			// The crew scatters when the captain falls.
			for (UUID id : crew) {
				Entity member = level.getEntity(id);
				if (member != null && member.isAlive()) {
					level.sendParticles(ParticleTypes.POOF, member.getX(), member.getY() + 1, member.getZ(), 12, 0.3, 0.6, 0.3, 0.02);
					member.discard();
				}
			}
			crew.clear();
		}
		super.die(source);
	}

	@Override
	protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
		super.dropCustomDeathLoot(level, source, recentlyHit);
		if (isBoss()) {
			BossRewards.dropKey(this, level);
			BossRewards.dropRemnants(this, level);
		}
		if (isBoss() && isFirstWin()) {
			BossRewards.dropTrophy(this, level);
		}
	}

	// ---- Saving and loading ----

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putBoolean("RogueIntro", introDone);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		introDone = input.getBooleanOr("RogueIntro", false);
	}
}
