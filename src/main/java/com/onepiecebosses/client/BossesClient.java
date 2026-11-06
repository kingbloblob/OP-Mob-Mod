package com.onepiecebosses.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import net.fabricmc.api.ClientModInitializer;

import com.onepiecebosses.boss.RogueBosses;
import com.onepiecebosses.crew.RivalCrews;
import com.onepiecebosses.sea.SeaKings;
import com.onepiecebosses.world.WorldMobs;
import com.onepiecemod.npc.client.NpcRenderer;

/** The client-only start of One Piece Bosses. */
public class BossesClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		RogueModels.register();
		SeaKingModels.register();
		EntityRenderers.register(RogueBosses.ROGUE_BOSS, RogueBossRenderer::new);
		// The world mobs are the main mod's pirate NPCs underneath, so they wear its NPC skins.
		EntityRenderers.register(WorldMobs.WANDERING_HUNTER, NpcRenderer::new);
		EntityRenderers.register(WorldMobs.ROOKIE_RAIDER, NpcRenderer::new);
		EntityRenderers.register(RivalCrews.RIVAL_PIRATE, NpcRenderer::new);
		// The Sea King mini-bosses, each with its own body and skin.
		SeaKings.TYPES.forEach((kind, type) -> EntityRenderers.register(type, context -> new SeaKingBossRenderer(context, kind.id)));
	}
}
