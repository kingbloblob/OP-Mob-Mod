package com.onepiecebosses.client;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.AABB;

import com.onepiecebosses.BossesMod;
import com.onepiecebosses.sea.SeaKingBossEntity;

/** Draws a Sea King mini-boss: its own body (SeaKingModels) and skin, assets/opbosses/textures/entity/sea_king/<id>.png. */
public class SeaKingBossRenderer extends MobRenderer<SeaKingBossEntity, SeaKingBossRenderer.State, SeaKingBossModel> {
	private final float size;
	private final Identifier texture;

	public static class State extends LivingEntityRenderState {
		public boolean aggressive;
		/** 0 to 1 while it bites, otherwise -1. */
		public float attack = -1;
	}

	public SeaKingBossRenderer(EntityRendererProvider.Context context, String id) {
		super(context, new SeaKingBossModel(context.bakeLayer(SeaKingModels.layer(id)), id), 4.0f);
		this.size = SeaKingModels.size(id);
		this.texture = BossesMod.id("textures/entity/sea_king/" + id + ".png");
	}

	// The tail reaches far behind the hitbox: keep drawing it when only the tail is on screen.
	@Override
	protected AABB getBoundingBoxForCulling(SeaKingBossEntity entity, float partialTick) {
		return super.getBoundingBoxForCulling(entity, partialTick).inflate(14.0);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(SeaKingBossEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.aggressive = entity.isAggressive();
		float swing = entity.getSwingAnimation(partialTick);
		state.attack = swing > 0 ? swing : -1;
	}

	@Override
	protected void scale(State state, PoseStack poseStack) {
		poseStack.scale(size, size, size);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return texture;
	}
}
