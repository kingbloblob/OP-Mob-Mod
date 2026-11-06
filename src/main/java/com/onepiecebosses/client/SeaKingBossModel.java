package com.onepiecebosses.client;

import net.minecraft.client.animation.KeyframeAnimation;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

import com.onepiecemod.client.Keyframes;

/**
 * Animates a Sea King mini-boss's body (SeaKingModels): the segments swing in a swimming wave down to the tail, the
 * jaw hangs open and gapes wide while it hunts, Gulpmaw's lure bobs, and it lunges when it bites (the same moves as
 * the One Piece Mod's Sea King, so they feel like the same kind of animal).
 */
public class SeaKingBossModel extends EntityModel<SeaKingBossRenderer.State> {
	private final ModelPart body;
	private final ModelPart head;
	private final ModelPart jaw;
	private final ModelPart lure;
	private final ModelPart[] segments;
	private final KeyframeAnimation bite;

	public SeaKingBossModel(ModelPart root, String id) {
		super(root);
		this.body = root.getChild("body");
		this.head = body.getChild("head");
		this.jaw = head.getChild("jaw");
		this.lure = head.hasChild("lure") ? head.getChild("lure") : null;
		this.segments = new ModelPart[SeaKingModels.segments(id)];
		ModelPart parent = body;
		for (int i = 0; i < segments.length; i++) {
			segments[i] = parent.getChild("segment" + i);
			parent = segments[i];
		}
		this.bite = new Keyframes(0.6f)
				.rot("jaw", 0, 0, 0, 0).rot("jaw", 0.15f, 60, 0, 0).rot("jaw", 0.28f, -5, 0, 0).rot("jaw", 0.6f, 0, 0, 0)
				.rot("head", 0, 0, 0, 0).rot("head", 0.15f, -18, 0, 0).rot("head", 0.28f, 10, 0, 0).rot("head", 0.6f, 0, 0, 0)
				.pos("head", 0, 0, 0, 0).pos("head", 0.28f, 0, 0, -4).pos("head", 0.6f, 0, 0, 0)
				.build().bake(root);
	}

	@Override
	public void setupAnim(SeaKingBossRenderer.State state) {
		super.setupAnim(state);
		float time = state.ageInTicks;
		float effort = 0.4f + Math.min(state.walkAnimationSpeed, 1.0f) * 0.6f;
		body.xRot = state.xRot * Mth.DEG_TO_RAD;
		head.yRot = state.yRot * Mth.DEG_TO_RAD * 0.5f;
		head.xRot = Mth.sin(time * 0.08f) * 0.05f;
		jaw.xRot = (state.aggressive ? 0.6f : 0.15f) + Mth.sin(time * 0.15f) * 0.08f;
		if (lure != null) {
			lure.xRot = Mth.sin(time * 0.12f) * 0.12f;
			lure.zRot = Mth.cos(time * 0.09f) * 0.08f;
		}
		for (int i = 0; i < segments.length; i++) {
			segments[i].yRot = Mth.sin(time * 0.2f * effort - i * 0.9f) * (0.1f + i * 0.04f) * effort;
			segments[i].xRot = Mth.sin(time * 0.1f - i * 0.7f) * 0.05f;
		}
		if (state.attack >= 0) {
			bite.apply((long) (state.attack * 600.0f), 1.0f);
		}
	}
}
