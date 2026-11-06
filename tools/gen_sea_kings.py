#!/usr/bin/env python3
"""Builds the Sea King mini-bosses' bodies: the 3D model (Java) and the skin painted to fit it.

    python3 tools/gen_sea_kings.py .

Writes src/main/java/com/onepiecebosses/client/SeaKingModels.java and
src/main/resources/assets/opbosses/textures/entity/sea_king/<id>.png. Change a shape or a colour here and run it
again; don't edit the generated files by hand.

Every one is built like the One Piece Mod's Sea King: a "body" root, a "head" with a hinged "jaw", and a chain of
"segment<N>" parts down to the tail, each hanging off the one before so a small wiggle on each adds up to a
swimming wave (client/SeaKingBossModel animates them). Optional parts: "lure" (Gulpmaw's light, on the head).
Model space is Minecraft's: 16 px = 1 block, y down, the front is -z. Sizes are whole pixels so the skin maps 1:1.
"""
import os
import random
import sys

from PIL import Image


def B(x, y, z, w, h, d, colour, pattern=None, **extra):
    return dict(x=x, y=y, z=z, w=w, h=h, d=d, colour=colour, pattern=pattern, **extra)


def serpent(sizes, length, colour, pattern, belly, back=None, side=None, tail=None):
    """Segment boxes: sizes = [(width, height)], each `length` long; back(i, w, h) / side(i, w, h) / tail(w, h) add
    boxes (fins, plates, spines) to segment i."""
    segs = []
    for i, (w, h) in enumerate(sizes):
        boxes = [B(-w // 2, -h // 2, 0, w, h, length, colour, pattern, belly=belly)]
        if back:
            boxes += back(i, w, h)
        if side:
            boxes += side(i, w, h)
        if tail and i == len(sizes) - 1:
            boxes += tail(w, h)
        segs.append(boxes)
    return segs


# ---------------- the Sea Kings ----------------
KINGS = {}

# Gulpmaw, the Lantern Deep: an anglerfish's head on an eel's body. The head is mostly mouth, a ring of needle teeth
# around a jaw that hangs open, little dead eyes, and a glowing lure dangling on a rod in front of it all.
# Black-teal skin with glowing cyan spots down the flanks.
KINGS["gulpmaw"] = dict(
    size=3.0, length=12,
    head=[
        B(-7, -8, -14, 14, 10, 14, '#1d343c', 'spots', belly='#2e4c52'),     # the great skull
        B(-6, -10, -12, 12, 2, 10, '#16282e', 'ridges'),                     # brow
        B(-8, -4, -6, 1, 6, 5, '#16282e', 'fin'),                            # gill flaps
        B(7, -4, -6, 1, 6, 5, '#16282e', 'fin'),
        B(-6, 2, -14, 1, 4, 1, '#ece8d4', 'tooth'),                          # needle teeth hanging from the upper jaw
        B(-3, 2, -14, 1, 5, 1, '#ece8d4', 'tooth'),
        B(0, 2, -14, 1, 4, 1, '#ece8d4', 'tooth'),
        B(3, 2, -14, 1, 5, 1, '#ece8d4', 'tooth'),
        B(5, 2, -14, 1, 4, 1, '#ece8d4', 'tooth'),
        B(-7, 2, -10, 1, 3, 1, '#ece8d4', 'tooth'),
        B(6, 2, -10, 1, 3, 1, '#ece8d4', 'tooth'),
        B(-5, -6, -14.5, 2, 2, 1, '#d8e8a0', 'eye'),                         # small dead eyes
        B(3, -6, -14.5, 2, 2, 1, '#d8e8a0', 'eye'),
    ],
    jaw=dict(pivot=(0, 2, 0), boxes=[
        B(-7, 0, -15, 14, 4, 14, '#24404a', 'spots', belly='#3a5a60'),       # the hanging lower jaw
        B(-6, -3, -15, 1, 3, 1, '#ece8d4', 'tooth'),
        B(-3, -4, -15, 1, 4, 1, '#ece8d4', 'tooth'),
        B(1, -3, -15, 1, 3, 1, '#ece8d4', 'tooth'),
        B(4, -4, -15, 1, 4, 1, '#ece8d4', 'tooth'),
        B(6, -3, -12, 1, 3, 1, '#ece8d4', 'tooth'),
        B(-7, -3, -12, 1, 3, 1, '#ece8d4', 'tooth'),
    ]),
    lure=dict(pivot=(0, -9, -8), boxes=[
        B(-0.5, -9, -0.5, 1, 9, 1, '#2a3a40', 'rod'),                        # the rod up off the brow
        B(-0.5, -10, -9, 1, 1, 9, '#2a3a40', 'rod'),                         # out over the mouth
        B(-0.5, -9, -9, 1, 8, 1, '#2a3a40', 'rod'),                          # dangling
        B(-2, -1, -10.5, 4, 4, 4, '#a8ffd8', 'glow'),                        # the light
    ]),
    segments=serpent([(12, 10), (10, 9), (9, 8), (7, 6), (5, 4)], 12, '#1d343c', 'spots', '#2e4c52',
                     back=lambda i, w, h: [B(-0.5, -h // 2 - 3, 2, 1, 3, 8, '#16282e', 'fin')],
                     side=lambda i, w, h: ([B(w // 2, 1, 2, 6, 1, 6, '#16282e', 'fin'), B(-w // 2 - 6, 1, 2, 6, 1, 6, '#16282e', 'fin')]
                                           if i == 0 else []),
                     tail=lambda w, h: [B(-0.5, -7, 8, 1, 14, 8, '#16282e', 'fin')]),
)

# Ironscale, the Keelbreaker: a hammerhead serpent in armour. The hammer is a battering ram of plate with an eye at
# each end, the back is a row of overlapping iron-grey scutes with barnacles and rust, and the tail ends in a
# spiked club. It rams ships from below.
KINGS["ironscale"] = dict(
    size=3.4, length=11,
    head=[
        B(-5, -5, -12, 10, 8, 12, '#56606a', 'plates', belly='#7a7c78'),     # skull
        B(-13, -4, -15, 26, 5, 5, '#4a525a', 'plates'),                      # the hammer
        B(-14, -3, -14, 1, 2, 2, '#f0c040', 'eye'),                          # eyes on its ends
        B(13, -3, -14, 1, 2, 2, '#f0c040', 'eye'),
        B(-4, -8, -11, 8, 3, 10, '#3e464e', 'barnacles'),                    # armour ridge
        B(-3, -11, -9, 6, 3, 4, '#3e464e', 'plates'),                        # ram horn
    ],
    jaw=dict(pivot=(0, 3, -2), boxes=[
        B(-4.5, 0, -10, 9, 3, 10, '#6a6e6c', 'plates', belly='#8a8a84'),
        B(-4, -1, -10, 8, 1, 1, '#ece8d4', 'tooth'),
    ]),
    segments=serpent([(12, 10), (11, 9), (10, 8), (9, 7), (7, 6), (5, 5)], 11, '#56606a', 'plates', '#7a7c78',
                     back=lambda i, w, h: [B(-w // 2 - 1, -h // 2 - 2, 1, w + 2, 2, 9, '#3e464e', 'barnacles'),
                                           B(-0.5, -h // 2 - 5, 3, 1, 3, 2, '#c8c4b0', 'tooth'),
                                           B(-0.5, -h // 2 - 4, 7, 1, 2, 2, '#c8c4b0', 'tooth')],
                     side=lambda i, w, h: ([B(w // 2, 2, 2, 7, 2, 7, '#3e464e', 'plates'), B(-w // 2 - 7, 2, 2, 7, 2, 7, '#3e464e', 'plates')]
                                           if i in (0, 3) else []),
                     tail=lambda w, h: [B(-4, -4, 9, 8, 8, 7, '#3e464e', 'barnacles'),           # the club
                                        B(-0.5, -7, 11, 1, 3, 2, '#c8c4b0', 'tooth'),
                                        B(4, -1, 11, 3, 1, 2, '#c8c4b0', 'tooth'),
                                        B(-7, -1, 11, 3, 1, 2, '#c8c4b0', 'tooth')]),
)

# Thundercoil, the Storm Serpent: a long, thin storm eel. A narrow snout with drooping whisker barbels, a jagged
# crest of glowing yellow fins down its whole back like a lightning bolt, deep-blue skin striped with yellow.
KINGS["thundercoil"] = dict(
    size=3.2, length=10,
    head=[
        B(-4, -4, -14, 8, 7, 14, '#203070', 'bolts', belly='#3a5aa0'),
        B(-0.5, -10, -12, 1, 6, 10, '#fff070', 'glow'),                     # lightning crest
        B(-4, -1, -15, 1, 8, 1, '#c8d8ff', 'rod'),                          # whiskers
        B(3, -1, -15, 1, 8, 1, '#c8d8ff', 'rod'),
        B(-4.5, -3, -11, 1, 2, 2, '#fff070', 'eye'),
        B(3.5, -3, -11, 1, 2, 2, '#fff070', 'eye'),
    ],
    jaw=dict(pivot=(0, 3, -1), boxes=[
        B(-3.5, 0, -13, 7, 3, 12, '#2a3a80', 'bolts', belly='#4a6ab0'),
        B(-3, -1, -13, 6, 1, 1, '#ece8d4', 'tooth'),
    ]),
    segments=serpent([(8, 7), (8, 7), (7, 6), (7, 6), (6, 5), (5, 4), (4, 3)], 10, '#203070', 'bolts', '#3a5aa0',
                     back=lambda i, w, h: [B(-0.5, -h // 2 - 7 + i // 2, 1, 1, 7 - i // 2, 8, '#fff070', 'glow')],
                     side=lambda i, w, h: ([B(w // 2, 0, 2, 5, 1, 5, '#3a5aa0', 'fin'), B(-w // 2 - 5, 0, 2, 5, 1, 5, '#3a5aa0', 'fin')]
                                           if i in (0, 4) else []),
                     tail=lambda w, h: [B(-0.5, -6, 7, 1, 12, 9, '#fff070', 'glow')]),
)

# ---------------- painting ----------------


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def dims(b):
    return int(round(b['w'])), int(round(b['h'])), int(round(b['d']))


def paint(img, u, v, b, rnd):
    w, h, d = dims(b)
    base = rgb(b['colour'])
    belly = rgb(b['belly']) if b.get('belly') else None
    faces = {  # name: (x0, y0, width, height, light)
        'top': (u + d, v, w, d, 1.12), 'bottom': (u + d + w, v, w, d, 0.8),
        'right': (u, v + d, d, h, 0.92), 'front': (u + d, v + d, w, h, 1.0),
        'left': (u + d + w, v + d, d, h, 0.92), 'back': (u + 2 * d + w, v + d, w, h, 0.86),
    }
    px = img.load()
    pat = b['pattern']
    for face, (x0, y0, fw, fh, light) in faces.items():
        for y in range(fh):
            for x in range(fw):
                c = shade(base, light * (0.92 + 0.12 * rnd.random()))
                if belly and (face == 'bottom' or (face in ('left', 'right', 'front', 'back') and y >= fh - max(1, fh // 3))):
                    c = shade(belly, light * (0.95 + 0.08 * rnd.random()))
                if pat == 'spots' and face != 'bottom' and rnd.random() < 0.05:
                    c = (120, 255, 220)
                elif pat == 'ridges' and x % 3 == 0:
                    c = shade(c, 0.75)
                elif pat == 'fin' and (x + y) % 3 == 0:
                    c = shade(c, 1.25)
                elif pat == 'tooth':
                    c = shade(base, 0.9 + 0.15 * (y / max(1, fh)))
                elif pat == 'eye':
                    c = base if (x + y) % 2 == 0 else shade(base, 0.7)
                elif pat == 'glow':
                    c = shade(base, 0.9 + 0.2 * rnd.random())
                elif pat == 'rod':
                    c = shade(base, 0.85 + 0.2 * rnd.random())
                elif pat == 'plates':
                    if y % 4 == 0 or x % 5 == 0:
                        c = shade(c, 0.7)
                    elif rnd.random() < 0.04:
                        c = (150, 80, 40)                            # rust
                elif pat == 'barnacles':
                    if rnd.random() < 0.12:
                        c = (220, 214, 196)
                    elif y % 3 == 0:
                        c = shade(c, 0.75)
                elif pat == 'bolts' and face != 'bottom':
                    if (x + 2 * y) % 9 in (0, 1) and (x // 3) % 2 == 0:
                        c = (250, 230, 90)
                px[x0 + x, y0 + y] = c + (255,)


def pack(boxes, size):
    """Shelf-packs each box's UV rectangle (2(w+d) by d+h). Returns [(u, v)] or None if they don't fit."""
    order = sorted(range(len(boxes)), key=lambda i: -(dims(boxes[i])[2] + dims(boxes[i])[1]))
    spots = [None] * len(boxes)
    x = y = row = 0
    for i in order:
        w, h, d = dims(boxes[i])
        bw, bh = 2 * (w + d), d + h
        if x + bw > size:
            x, y, row = 0, y + row, 0
        if y + bh > size or bw > size:
            return None
        spots[i] = (x, y)
        x += bw
        row = max(row, bh)
    return spots


def f(v):
    return ('%gF' % v)


def java(layouts):
    out = ['package com.onepiecebosses.client;', '',
           'import net.minecraft.client.model.geom.ModelLayerLocation;',
           'import net.minecraft.client.model.geom.PartPose;',
           'import net.minecraft.client.model.geom.builders.CubeListBuilder;',
           'import net.minecraft.client.model.geom.builders.LayerDefinition;',
           'import net.minecraft.client.model.geom.builders.MeshDefinition;',
           'import net.minecraft.client.model.geom.builders.PartDefinition;', '',
           'import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;', '',
           'import com.onepiecebosses.BossesMod;', '',
           '/**',
           ' * The Sea King mini-bosses\' bodies: a head with a hinged jaw (and Gulpmaw\'s lure), then a chain of segments to',
           ' * the tail, like the One Piece Mod\'s Sea King. SeaKingBossModel animates them; skins are',
           ' * assets/opbosses/textures/entity/sea_king/<id>.png and match these boxes.',
           ' * GENERATED by tools/gen_sea_kings.py, which also paints the skins: change the shapes there and run it again.',
           ' */',
           'public final class SeaKingModels {',
           '\tprivate SeaKingModels() {', '\t}', '']
    out.append('\t/** How much bigger than the model each one is drawn. */')
    out.append('\tpublic static float size(String id) {')
    out.append('\t\treturn switch (id) {')
    for k, spec in KINGS.items():
        out.append('\t\t\tcase "%s" -> %s;' % (k, f(spec['size'])))
    out.append('\t\t\tdefault -> 3F;')
    out.append('\t\t};')
    out.append('\t}')
    out.append('')
    out.append('\t/** How many body segments each one has (segment0 behind the head, the last one at the tail). */')
    out.append('\tpublic static int segments(String id) {')
    out.append('\t\treturn switch (id) {')
    for k, spec in KINGS.items():
        out.append('\t\t\tcase "%s" -> %d;' % (k, len(spec['segments'])))
    out.append('\t\t\tdefault -> 0;')
    out.append('\t\t};')
    out.append('\t}')
    out.append('')
    out.append('\tpublic static ModelLayerLocation layer(String id) {')
    out.append('\t\treturn new ModelLayerLocation(BossesMod.id("sea_king_" + id), "main");')
    out.append('\t}')
    out.append('')
    out.append('\t/** Registers one model layer per Sea King. BossesClient calls this. */')
    out.append('\tpublic static void register() {')
    for k in KINGS:
        out.append('\t\tModelLayerRegistry.registerModelLayer(layer("%s"), SeaKingModels::%s);' % (k, k))
    out.append('\t}')
    for k, spec in KINGS.items():
        boxes, spots, size = layouts[k]
        it = iter(zip(boxes, spots))

        def cubes(n):
            parts = []
            for _ in range(n):
                b, (u, v) = next(it)
                w, h, d = dims(b)
                parts.append('.texOffs(%d, %d).addBox(%s, %s, %s, %d, %d, %d)' % (u, v, f(b['x']), f(b['y']), f(b['z']), w, h, d))
            return 'CubeListBuilder.create()' + ''.join('\n\t\t\t\t\t' + p for p in parts)
        out.append('')
        out.append('\tprivate static LayerDefinition %s() {' % k)
        out.append('\t\tMeshDefinition mesh = new MeshDefinition();')
        out.append('\t\tPartDefinition body = mesh.getRoot().addOrReplaceChild("body", CubeListBuilder.create(), PartPose.offset(0F, 16F, 8F));')
        out.append('\t\tPartDefinition head = body.addOrReplaceChild("head", %s,\n\t\t\t\tPartPose.ZERO);' % cubes(len(spec['head'])))
        jp = spec['jaw']['pivot']
        out.append('\t\thead.addOrReplaceChild("jaw", %s,\n\t\t\t\tPartPose.offset(%s, %s, %s));' % (cubes(len(spec['jaw']['boxes'])), f(jp[0]), f(jp[1]), f(jp[2])))
        if 'lure' in spec:
            lp = spec['lure']['pivot']
            out.append('\t\thead.addOrReplaceChild("lure", %s,\n\t\t\t\tPartPose.offset(%s, %s, %s));' % (cubes(len(spec['lure']['boxes'])), f(lp[0]), f(lp[1]), f(lp[2])))
        out.append('\t\tPartDefinition parent = body;')
        for i, seg in enumerate(spec['segments']):
            off = 0 if i == 0 else spec['length']
            out.append('\t\tparent = parent.addOrReplaceChild("segment%d", %s,\n\t\t\t\tPartPose.offset(0F, 0F, %s));' % (i, cubes(len(seg)), f(off)))
        out.append('\t\treturn LayerDefinition.create(mesh, %d, %d);' % (size, size))
        out.append('\t}')
    out.append('}')
    return '\n'.join(out) + '\n'


def main(root):
    res = os.path.join(root, 'src/main/resources/assets/opbosses/textures/entity/sea_king')
    os.makedirs(res, exist_ok=True)
    layouts = {}
    for k, spec in KINGS.items():
        boxes = list(spec['head']) + list(spec['jaw']['boxes']) + list(spec.get('lure', {}).get('boxes', []))
        for seg in spec['segments']:
            boxes += seg
        for size in (128, 256):
            spots = pack(boxes, size)
            if spots:
                break
        else:
            sys.exit('%s: the boxes do not fit in a 256x256 skin' % k)
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        rnd = random.Random(k)
        for b, (u, v) in zip(boxes, spots):
            paint(img, u, v, b, rnd)
        img.save(os.path.join(res, k + '.png'))
        layouts[k] = (boxes, spots, size)
    with open(os.path.join(root, 'src/main/java/com/onepiecebosses/client/SeaKingModels.java'), 'w') as fh:
        fh.write(java(layouts))
    print('Built %d Sea King models' % len(KINGS))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
