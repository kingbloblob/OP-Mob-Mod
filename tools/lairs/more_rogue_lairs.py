"""The second band of rogues' lairs: Khamsin's Sunken Kasbah, Gale's Gilded Wake, Vasco's Leviathan Pens and Kreuz's
Laboratory Null. gen_lairs.py calls add() to register them in the rogue_lairs set (each lair only spawns in its own
biomes, so they share the set's spots with the first six without crowding them out much).
Same rules as the other lairs: a compound 70-90 blocks across, an approach, an arena at the heart, the boss's own
quarters with the chest, crew quarters, props everywhere, several levels and a landmark you can see from far off."""
import math
import random

from kit import AIR, FENCE, LANTERN, HANG, BARREL, CHAIN, PANE, CAMPFIRE, log, leaves, pane, ladder, bed  # noqa: F401
from parts import (stair, slab, trap, wall_post, fence, candle, carpet, CHAIN_X, CHAIN_Z, SOUL_HANG, SOUL_LANTERN,  # noqa: F401
                   SMOKE, SOUL_FIRE, WATER)

AB = "onepiece:alabasta_sandstone_bricks"
ABF = "onepiece:alabasta_sandstone_brick"
AB_WALL = "onepiece:alabasta_sandstone_brick_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]"
TILE = "onepiece:alabasta_tiles"
GOLD_BRICK = "onepiece:shandora_gold_bricks"     # gold to look at, not a free stack of gold blocks
LAB = "onepiece:lab_panel"
LABF = "onepiece:lab_panel"
LAB_LIGHT = "onepiece:lab_light"
BONE = "minecraft:bone_block[axis=y]"
BARS = "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]"
BUBBLE_HANG = "onepiece:bubble_lamp[hanging=true]"
import detail
CAMPFIRE_LIT = "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"


def facing(name, f):
    return f"onepiece:{name}[facing={f}]"


def banner(color, f):
    return f"minecraft:{color}_wall_banner[facing={f}]"


def gilded_ship(b, rnd, X0, Z0, L, CZ, dy, HULL, DECK, FX0):
    """A galleon's fittings: a gilded stern with a row of lit windows, gunports, deck gratings, a capstan, and rope on the rails."""
    for z in range(CZ - 7, CZ + 8):                                 # the stern: a gold-framed gallery of windows
        for y in range(dy - 2, dy + 6):
            x = X0 + 1
            if b.get(x, y, z) in (None, AIR):
                continue
            if y in (dy - 2, dy + 5) or z % 3 == 0:
                b.set(x - 1, y, z, GOLD_BRICK)
            elif y in (dy, dy + 1, dy + 2, dy + 3):
                b.set(x - 1, y, z, "minecraft:cyan_stained_glass")
    for x in range(X0 + 18, FX0 - 2, 5):                            # gunports down both sides, a dark square with a muzzle in it
        for side in (-1, 1):
            zs = [z for z in range(CZ - 12, CZ + 13) if b.get(x, dy - 1, z) not in (None, AIR)]
            if zs:
                z = min(zs) if side < 0 else max(zs)
                b.set(x, dy - 1, z, "minecraft:black_concrete")
                b.set(x, dy - 1, z + side, "minecraft:polished_blackstone_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
    for (x0, x1) in ((X0 + 24, X0 + 28), (X0 + 36, X0 + 40)):       # gratings over the hold
        for x in range(x0, x1 + 1):
            for z in range(CZ - 1, CZ + 2):
                b.set(x, dy, z, "minecraft:dark_oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for x in range(X0 + 40, X0 + 46):   # a shut hatch over the hold's stair, so the crew don't wander down it
        if b.get(x, dy, CZ) in (None, AIR):
            b.set(x, dy, CZ, "minecraft:dark_oak_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]")
    b.set(X0 + 34, dy + 1, CZ - 3, facing("capstan", "north"))
    b.set(X0 + 22, dy + 1, CZ + 3, facing("rope_coil", "north")); b.set(X0 + 43, dy + 1, CZ - 3, facing("rope_coil", "north"))


def gilded_island(b, rnd, RX, RZ, RRX, RRZ, CVX, CVZ, rock):
    """The reef as a place: sea stacks streaked with gold, a broken watchtower on the crest, the wrecked crew's graves,
    a salvage camp and jetty on the beach, a whale's bones, palms, and a stair cut up from the sand."""
    def ground(x, z):
        for y in range(20, -2, -1):
            if b.get(x, y, z) not in (None, AIR):
                return y
        return 0

    # sea stacks: tall, leaning, ragged columns off the reef's far side
    for (sx, sz, r, h) in ((RX + 30, RZ + 2, 4.5, 24), (RX + 25, RZ + 12, 3.2, 15), (RX - 31, RZ - 3, 3.6, 18), (RX + 8, RZ + 21, 3.4, 13)):
        for y in range(-14, h + 1):
            t = max(0.0, y) / h
            rr = r * (1 - t * 0.62) + (detail.noise(y * 3, sx, 40) - 0.5) * 1.6
            lean = t * t * 3
            for dx in range(-7, 8):
                for dz in range(-7, 8):
                    if math.hypot(dx, dz) <= rr:
                        n = detail.noise((sx + dx) * 2, y * 4, 41)
                        s = "minecraft:raw_gold_block" if 0.46 < n < 0.5 else rnd.choice(rock[:4])
                        b.set(sx + dx + round(lean), y, sz + dz, s)
        b.set(sx + round(3), h + 1, sz, "minecraft:moss_block"); b.set(sx + round(3), h + 2, sz, "minecraft:dead_bush")
    # palms and scrub, on the grass
    for (x, z) in ((RX - 18, RZ - 5), (RX - 12, RZ + 8), (RX + 17, RZ + 7), (RX + 12, RZ - 9), (RX - 6, RZ + 11), (RX + 20, RZ - 2)):
        detail.palm(b, x, ground(x, z) + 1, z, rnd.randint(8, 11), rnd)
    for (x, z) in ((RX - 15, RZ + 3), (RX + 15, RZ + 2), (RX - 2, RZ + 12), (RX + 7, RZ - 11)):
        detail.bush(b, x, ground(x, z) + 1, z, rnd, "jungle", 2)
    # the watchtower on the crest: a round stone tower, its top fallen in, a green light still burning
    TX, TZ = RX - 12, RZ - 2
    ty = ground(TX, TZ)
    b.cyl(TX, TZ, 4, ty - 2, ty + 4, "minecraft:stone_bricks")
    b.cyl(TX, TZ, 3, ty, ty + 16, "minecraft:stone_bricks", hollow=True)
    b.disk(TX, ty + 8, TZ, 2, "minecraft:spruce_planks")
    detail.weather(b, TX - 4, ty, TZ - 4, TX + 4, ty + 16, TZ + 4, "minecraft:stone_bricks")
    detail.ring_course(b, TX, TZ, 3, ty + 8, "stone_brick")
    for a in range(0, 360, 20):                                     # the ruined top: broken away on the seaward side
        x, z = round(TX + 3 * math.cos(math.radians(a))), round(TZ + 3 * math.sin(math.radians(a)))
        for y in range(ty + 12 + (a // 40) % 4, ty + 17):
            b.set(x, y, z, AIR)
    b.box(TX, ty + 1, TZ + 3, TX, ty + 2, TZ + 3, AIR)
    for y in range(ty + 1, ty + 9):
        b.set(TX - 2, y, TZ, "minecraft:ladder[facing=east,waterlogged=false]")
    b.set(TX, ty + 9, TZ, SOUL_FIRE); b.set(TX, ty + 8, TZ, "minecraft:soul_soil")
    # the graves of the crew that came ashore: fence crosses and skulls on the slope
    for i, (x, z) in enumerate(((RX + 13, RZ - 5), (RX + 15, RZ - 7), (RX + 17, RZ - 5), (RX + 15, RZ - 3), (RX + 19, RZ - 7), (RX + 11, RZ - 7))):
        g = ground(x, z)
        b.box(x, g + 1, z, x, g + 2, z, fence("dark_oak"))
        b.set(x, g + 2, z + 1, fence("dark_oak")); b.set(x, g + 2, z - 1, fence("dark_oak"))
        if i % 2:
            b.set(x + 1, g + 1, z, "minecraft:skeleton_skull[powered=false,rotation=4]")
    # the salvage camp on the beach: an awning, crates of what they raised, a fire
    CX, CZ2 = RX - 6, RZ + RRZ - 5
    cy = ground(CX, CZ2)
    for (dx, dz) in ((-4, -3), (4, -3), (-4, 3), (4, 3)):
        b.box(CX + dx, cy + 1, CZ2 + dz, CX + dx, cy + 4, CZ2 + dz, log("spruce"))
    for dx in range(-5, 6):
        for dz in range(-4, 5):
            b.set(CX + dx, cy + 5 - abs(dz) // 2, CZ2 + dz, "minecraft:gray_wool" if (dx + 20) % 4 < 2 else "minecraft:black_wool")
    b.set(CX + 1, cy + 1, CZ2, CAMPFIRE_LIT)
    for (x, z) in ((CX - 3, CZ2 - 2), (CX - 3, CZ2 + 2), (CX + 3, CZ2 + 2)):
        b.set(x, cy + 1, z, BARREL)
    b.set(CX + 3, cy + 1, CZ2 - 2, facing("crate_stack", "north")); b.set(CX - 1, cy + 1, CZ2 + 2, facing("treasure_pile", "north"))
    # a jetty out from the beach
    JX = RX + 4
    jz = RZ + RRZ - 6
    for k in range(0, 16):
        for dx in (-1, 0, 1):
            b.set(JX + dx, 1, jz + k, "minecraft:spruce_planks")
        if k % 4 == 0:
            for dx in (-2, 2):
                b.box(JX + dx, -8, jz + k, JX + dx, 3, jz + k, log("spruce"))
            b.set(JX + 2, 4, jz + k, SOUL_LANTERN)
    # a whale's bones on the sand
    b.bones(RX - 24, 1, RZ + 7, 16, axis="x", height=7)


def add(lair, OCEANS, DEEP):
    """Registers the four lairs with gen_lairs's @lair decorator."""

    # ============================================================ Khamsin: the Sunken Kasbah
    @lair("sunken_kasbah", "The Sunken Kasbah", "khamsin_sandshackle",
          ["minecraft:desert", "minecraft:badlands", "minecraft:savanna",
           "onepiece:alabasta"], "land")
    def _(b):
        rnd = random.Random(21)
        W, D = 84, 86
        CX = W // 2
        X0, Z0, X1, Z1 = 7, 9, W - 7, D - 9          # the curtain wall
        H = 9
        sand = ["minecraft:sand"] * 6 + ["minecraft:sandstone", "minecraft:smooth_sandstone"]

        # --- The ground: sand over a sandstone bed (so the dig pit has walls), dunes heaped against the north and west.
        for x in range(0, W + 1):
            for z in range(0, D + 1):
                for y in range(-3, 0):
                    b.set(x, y, z, "minecraft:sandstone")
                b.set(x, 0, z, rnd.choice(sand))
        for x in range(0, W + 1):
            for z in range(0, D + 1):
                out = x < X0 or x > X1 or z < Z0 or z > Z1
                if not out:
                    continue
                dw = min(abs(x - X0) if x < X0 else 99, abs(z - Z0) if z < Z0 else 99)   # distance to the north/west walls
                h = int(5.5 - dw * 0.8 + rnd.random() * 1.4) if dw < 99 else 0
                if x > X1 or z > Z1:
                    h = min(h, 1 if rnd.random() < 0.3 else 0)
                for y in range(1, max(0, h) + 1):
                    b.set(x, y, z, "minecraft:sand" if y < h else rnd.choice(["minecraft:sand", "minecraft:sand", "minecraft:sandstone_slab[type=bottom,waterlogged=false]"]))

        # --- The curtain wall: two thick, a red base course, a carved band, merlons on top and arrow slits.
        def wall_block(x, y, z):
            if y <= 2:
                return "minecraft:cut_red_sandstone"
            if y == 7:
                return "minecraft:chiseled_sandstone" if (x + z) % 4 == 0 else "minecraft:smooth_red_sandstone"
            return AB if rnd.random() < 0.85 else "minecraft:sandstone"
        ring = set()
        for x in range(X0, X1 + 1):
            for z in (Z0, Z0 + 1, Z1 - 1, Z1):
                ring.add((x, z))
        for z in range(Z0, Z1 + 1):
            for x in (X0, X0 + 1, X1 - 1, X1):
                ring.add((x, z))
        for (x, z) in ring:
            for y in range(-1, H + 1):
                b.set(x, y, z, wall_block(x, y, z))
            outer = x in (X0, X1) or z in (Z0, Z1)
            if outer and (x + z) % 2 == 0:
                b.set(x, H + 1, z, AB); b.set(x, H + 2, z, slab(ABF))
            if outer and (x + z) % 7 == 0:
                b.box(x, 4, z, x, 5, z, AIR)     # arrow slits
        # The south gate: a pointed arch under a gatehouse with two square towers, the portcullis raised.
        GX = CX
        for (x0, x1) in ((GX - 8, GX - 4), (GX + 4, GX + 8)):
            b.box(x0, -1, Z1 - 3, x1, 13, Z1 + 2, AB)
            b.box(x0 + 1, 1, Z1 - 2, x1 - 1, 12, Z1 + 1, AIR)
            b.box(x0, 0, Z1 - 3, x1, 2, Z1 + 2, "minecraft:cut_red_sandstone")
            b.box(x0 + 1, 0, Z1 - 2, x1 - 1, 0, Z1 + 1, TILE)
            for x in range(x0, x1 + 1, 2):
                for z in (Z1 - 3, Z1 + 2):
                    b.set(x, 14, z, AB); b.set(x, 15, z, slab(ABF))
            for z in range(Z1 - 3, Z1 + 3, 2):
                b.set(x0, 14, z, AB); b.set(x1, 14, z, AB)
            b.box(x0 + 1, 13, Z1 - 2, x1 - 1, 13, Z1 + 1, TILE)
            b.set((x0 + x1) // 2, 9, Z1 + 2, AIR); b.set((x0 + x1) // 2, 10, Z1 + 2, AIR)   # window
            b.set((x0 + x1) // 2, 8, Z1 + 3, banner("red", "south"))
        b.box(GX - 3, 1, Z1 - 1, GX + 3, 6, Z1, AIR)
        b.box(GX - 3, 7, Z1 - 3, GX + 3, 11, Z1 + 2, AB)          # the room over the gate
        b.box(GX - 2, 8, Z1 - 2, GX + 2, 10, Z1 + 1, AIR)
        for x in range(GX - 3, GX + 4, 2):
            b.set(x, 12, Z1 + 2, AB); b.set(x, 12, Z1 - 3, AB)
        b.box(GX - 3, 0, Z1 - 1, GX + 3, 0, Z1, TILE)
        b.set(GX - 3, 6, Z1 + 1, stair(ABF, "east", "top")); b.set(GX + 3, 6, Z1 + 1, stair(ABF, "west", "top"))
        b.set(GX - 2, 7, Z1 + 1, stair(ABF, "east", "top")); b.set(GX + 2, 7, Z1 + 1, stair(ABF, "west", "top"))
        for x in range(GX - 2, GX + 3):
            b.set(x, 6, Z1 + 1, BARS)                               # the portcullis, raised
        b.set(GX, 8, Z1 + 3, "minecraft:chiseled_sandstone")
        b.set(GX, 9, Z1 + 3, GOLD_BRICK)
        # Four corner towers: round, a ring of battlements and a dome with a gold finial.
        for (cx, cz) in ((X0 + 1, Z0 + 1), (X1 - 1, Z0 + 1), (X0 + 1, Z1 - 1), (X1 - 1, Z1 - 1)):
            b.tower(cx, cz, 4, 14, AB, y=0, windows=True, ladder_side=False, floors=[H])
            b.cyl(cx, cz, 4, 0, 2, "minecraft:cut_red_sandstone", hollow=True)
            b.sphere(cx, 15, cz, 3.5, "minecraft:smooth_sandstone", upper=True, ry=4)
            b.box(cx, 19, cz, cx, 20, cz, GOLD_BRICK)
            b.set(cx, 21, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
            b.set(cx, H + 1, cz, LANTERN)

        # --- The courtyard: sand, with a smooth stone road from the gate to the ring and on to the palace.
        for z in range(Z0 + 2, Z1 - 1):
            for x in range(CX - 2, CX + 3):
                if z > 64 or z < 40:
                    b.set(x, 0, z, "minecraft:smooth_sandstone" if abs(x - CX) < 2 else "minecraft:cut_sandstone")

        # --- The Chain Ring (the arena): a tiled floor ringed by columns, chains and shackles hanging from every one.
        AX, AZ, R = CX, 52, 10
        b.disk(AX, 0, AZ, R + 1, "minecraft:cut_red_sandstone")
        b.disk(AX, 0, AZ, R, TILE)
        for r in (4, 8):
            for i in range(0, 360, 4):
                a = math.radians(i)
                b.set(round(AX + r * math.cos(a)), 0, round(AZ + r * math.sin(a)), "minecraft:smooth_red_sandstone")
        b.disk(AX, 0, AZ, 1.5, "minecraft:chiseled_red_sandstone")
        for i in range(0, 360, 30):
            a = math.radians(i)
            x, z = round(AX + (R + 2) * math.cos(a)), round(AZ + (R + 2) * math.sin(a))
            if i in (90, 270):
                continue   # the road runs through here
            b.set(x, 1, z, "minecraft:chiseled_sandstone")
            b.box(x, 2, z, x, 5, z, "minecraft:cut_sandstone")
            b.set(x, 6, z, "minecraft:chiseled_sandstone")
            b.set(x, 7, z, slab("smooth_sandstone"))
            ix, iz = round(AX + (R + 1) * math.cos(a)), round(AZ + (R + 1) * math.sin(a))
            b.set(ix, 6, iz, AB)
            b.hanging(ix, 5, iz, 3, BARS)                            # a shackle on a chain
        for i in (45, 135, 225, 315):                                # braziers
            a = math.radians(i)
            x, z = round(AX + 6 * math.cos(a)), round(AZ + 6 * math.sin(a))
            b.set(x, 1, z, "minecraft:cut_red_sandstone"); b.set(x, 2, z, CAMPFIRE)

        # --- The dig pit (east): stepped down into the buried city he's after, with scaffolds, ladders and a crane.
        PX, PZ, PR = 66, 46, 8
        for depth in range(0, 9):
            r = PR - depth * 0.45
            for x in range(PX - PR - 1, PX + PR + 2):
                for z in range(PZ - PR - 1, PZ + PR + 2):
                    d = math.hypot(x - PX, z - PZ)
                    if d <= r:
                        for y in range(-depth, 1):
                            b.set(x, y, z, AIR)
                        b.set(x, -depth - 1, z, "minecraft:sandstone")
                        if d > r - 1.2:
                            b.set(x, -depth, z, rnd.choice(["minecraft:sand", "minecraft:sandstone", "minecraft:smooth_sandstone"]))
        for x in range(PX - PR - 2, PX + PR + 3):
            for z in range(PZ - PR - 2, PZ + PR + 3):
                for y in range(-12, -3):
                    if b.get(x, y, z) is None:
                        b.set(x, y, z, "minecraft:sandstone")
        PB = -9                                                        # the pit floor (you stand at PB + 1)
        for (x, z, h) in ((PX - 3, PZ - 2, 5), (PX + 2, PZ - 3, 3), (PX + 3, PZ + 2, 6), (PX - 2, PZ + 3, 2)):   # the buried city's columns
            b.box(x, PB + 1, z, x, PB + h, z, GOLD_BRICK if h > 4 else TILE)
            b.set(x, PB + h + 1, z, "minecraft:chiseled_sandstone" if h > 2 else stair(ABF, "north"))
        for x in range(PX - 3, PX + 4):
            b.set(x, PB, PZ, TILE)                                     # a strip of old floor
        for y in range(PB + 2, 1):                                     # a ladder down the north side on a timber frame
            b.set(PX, y, PZ - PR - 1, "minecraft:spruce_planks")
            b.set(PX, y, PZ - PR, ladder("south"))
        b.set(PX, 1, PZ - PR - 1, fence("spruce")); b.set(PX - 1, 1, PZ - PR - 1, fence("spruce")); b.set(PX + 1, 1, PZ - PR - 1, fence("spruce"))
        for (x, z) in ((PX - 5, PZ + 5), (PX + 5, PZ - 5)):           # timber shoring frames down the steps
            y = 0
            while b.get(x, y, z) == AIR:
                y -= 1
            b.box(x, y + 1, z, x, 2, z, log("spruce"))
            b.set(x + 1, 2, z, "minecraft:spruce_planks"); b.set(x - 1, 2, z, "minecraft:spruce_planks")
            b.set(x, 3, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
        # the crane: a timber mast on the north rim, a jib out over the pit and a basket on a chain
        CRX, CRZ = PX, PZ - PR - 3
        b.box(CRX, 1, CRZ, CRX, 12, CRZ, log("spruce"))
        for z in range(CRZ - 2, CRZ + 10):
            b.set(CRX, 12, z, log("spruce", "z"))
        b.set(CRX, 11, CRZ - 2, "minecraft:cobblestone"); b.set(CRX, 10, CRZ - 2, "minecraft:cobblestone")   # counterweight
        for y in range(PB + 4, 12):
            b.set(CRX, y, CRZ + 9, CHAIN)
        b.set(CRX, PB + 3, CRZ + 9, BARREL)
        b.box(CRX - 1, 1, CRZ - 1, CRX + 1, 1, CRZ + 1, "minecraft:spruce_planks")
        b.set(CRX, 1, CRZ, log("spruce"))
        for (x, z) in ((PX - 7, PZ - 7), (PX + 7, PZ + 7), (PX - 8, PZ + 5)):   # spoil heaps and tools
            b.set(x, 1, z, "minecraft:sand")
            b.set(x, 2, z, "minecraft:sandstone_slab[type=bottom,waterlogged=false]")
        b.crates(PX - 8, 1, PZ - 2, rnd, n=3, spread=1)
        b.set(PX + 7, 1, PZ - 4, "minecraft:decorated_pot[cracked=false,facing=south,waterlogged=false]")
        b.set(PX + 6, 1, PZ + 4, "minecraft:decorated_pot[cracked=true,facing=west,waterlogged=false]")

        # --- The cages (south-east): iron cages in rows, every door broken open and the shackles hanging empty.
        for i, (x, z) in enumerate((x, z) for z in (62, 69) for x in (56, 61, 66, 71)):
            b.box(x, 1, z, x + 3, 4, z + 3, BARS)
            b.box(x + 1, 1, z + 1, x + 2, 3, z + 2, AIR)
            b.box(x, 4, z, x + 3, 4, z + 3, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
            b.box(x + 1, 1, z, x + 2, 2, z, AIR)                       # the door, open
            b.set(x + 1, 3, z + 2, CHAIN); b.set(x + 1, 2, z + 2, BARS) if i % 2 else None
            b.set(x + 2, 1, z + 2, "minecraft:hay_block[axis=y]" if i % 3 == 0 else "minecraft:brown_carpet")
        for x in range(55, 76):
            b.set(x, 0, 66, "minecraft:cut_sandstone"); b.set(x, 0, 67, "minecraft:cut_sandstone")

        # --- The caravan camp (west): striped tents, wagons, barrels, a campfire.
        def tent(x, z, color, length=6):
            b.box(x, 0, z, x + 4, 0, z + length - 1, "minecraft:smooth_sandstone")
            for i in range(3):
                for zz in range(z, z + length):
                    wool = f"minecraft:{color}_wool" if zz % 2 else "minecraft:white_wool"
                    b.set(x + i, 1 + i, zz, wool); b.set(x + 4 - i, 1 + i, zz, wool)
            for zz in range(z, z + length):
                b.set(x + 2, 4, zz, f"minecraft:{color}_wool")
            for zz in (z, z + length - 1):
                b.set(x + 2, 5, zz, fence("dark_oak"))
            b.set(x + 2, 1, z + 2, "minecraft:red_carpet"); b.set(x + 2, 1, z + 3, "minecraft:red_carpet")
            b.set(x + 1, 1, z + length - 2, BARREL)
        tent(12, 36, "red"); tent(19, 36, "orange"); tent(12, 46, "orange"); tent(19, 46, "red"); tent(12, 56, "brown"); tent(19, 56, "red")
        b.set(17, 1, 53, CAMPFIRE)
        for (x, z) in ((16, 52), (18, 52), (16, 54), (18, 54)):
            b.set(x, 1, z, stair("spruce", "north" if z < 49 else "south"))
        def wagon(x, z):
            b.box(x, 2, z, x + 2, 2, z + 4, "minecraft:spruce_planks")
            for zz in (z, z + 4):
                b.set(x - 1, 1, zz, "minecraft:dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
                b.set(x + 3, 1, zz, "minecraft:dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
                b.set(x + 1, 1, zz, log("spruce", "x"))
            b.set(x + 1, 2, z - 1, fence("spruce")); b.set(x + 1, 2, z - 2, fence("spruce"))
            b.set(x, 3, z + 1, "minecraft:hay_block[axis=z]"); b.set(x + 2, 3, z + 2, BARREL); b.set(x + 1, 3, z + 3, "minecraft:hay_block[axis=x]")
        wagon(12, 65); wagon(19, 67); wagon(26, 64)
        b.crates(25, 1, 48, rnd, n=4, spread=2)

        # --- The oasis (north-west corner of the yard): a pool with palms and reeds.
        OX, OZ = 18, 22
        for x in range(OX - 7, OX + 8):
            for z in range(OZ - 6, OZ + 7):
                d = math.hypot((x - OX) / 7, (z - OZ) / 5.5)
                if d <= 1:
                    b.set(x, 0, z, WATER); b.set(x, -1, z, WATER); b.set(x, -2, z, "minecraft:clay")
                    if rnd.random() < 0.08:
                        b.set(x, 1, z, "minecraft:lily_pad")
                elif d <= 1.25:
                    b.set(x, 0, z, "minecraft:grass_block")
                    if rnd.random() < 0.25:
                        b.set(x, 1, z, rnd.choice(["minecraft:short_grass", "onepiece:sand_rose", "minecraft:fern"]))
        for (x, z, h) in ((OX - 8, OZ - 3, 7), (OX + 7, OZ + 4, 8), (OX - 2, OZ + 7, 6), (OX + 4, OZ - 6, 7)):
            b.set(x, 0, z, "minecraft:grass_block")
            b.palm(x, 1, z, h)

        # --- Khamsin's palace (north): two storeys of sandstone with a gold band, a great dome on top, and his throne.
        PX0, PZ0, PX1, PZ1 = CX - 16, Z0 + 4, CX + 16, Z0 + 22
        b.box(PX0 - 2, 0, PZ0 - 1, PX1 + 2, 0, PZ1 + 3, "minecraft:cut_red_sandstone")
        b.stair_run(CX - 4, 0, PZ1 + 4, 1, "smooth_sandstone", "north", "minecraft:smooth_sandstone", width=9)
        b.hall(PX0, PZ0, PX1, PZ1, 0, 8, AB, "minecraft:cut_red_sandstone", "minecraft:smooth_sandstone", trim=GOLD_BRICK, floor=TILE,
               win=BARS, every=4, doors=[("south", 14, 5, 6)], win_h=3)
        for x in (CX - 3, CX + 3):                                     # the doorway's pointed arch
            b.set(x, 6, PZ1, stair(ABF, "east" if x < CX else "west", "top"))
        b.set(CX - 2, 7, PZ1, stair(ABF, "east", "top")); b.set(CX + 2, 7, PZ1, stair(ABF, "west", "top"))
        for x in range(CX - 1, CX + 2):
            b.set(x, 7, PZ1, AIR)
        b.set(CX, 8, PZ1 + 1, "minecraft:chiseled_sandstone")
        for x in (CX - 5, CX + 5):
            b.set(x, 5, PZ1 + 1, banner("red", "south"))
        UX0, UZ0, UX1, UZ1 = PX0 + 4, PZ0 + 3, PX1 - 4, PZ1 - 3
        b.hall(UX0, UZ0, UX1, UZ1, 8, 6, AB, AB, "minecraft:smooth_sandstone", trim=GOLD_BRICK, floor=TILE, win=BARS, every=4, proud=False)
        for x in range(PX0, PX1 + 1):                                  # a crenellated roof terrace on the ground floor
            for z in (PZ0, PZ1):
                if x % 2 == 0:
                    b.set(x, 9, z, AB)
        for z in range(PZ0, PZ1 + 1):
            for x in (PX0, PX1):
                if z % 2 == 0:
                    b.set(x, 9, z, AB)
        for x in range(UX0, UX1 + 1):
            for z in (UZ0, UZ1):
                if x % 2 == 1:
                    b.set(x, 15, z, AB)
        DY = 15
        b.sphere(CX, DY, (PZ0 + PZ1) // 2, 7, "minecraft:yellow_terracotta", hollow=True, upper=True, ry=9)
        for i in range(0, 360, 5):
            a = math.radians(i)
            b.set(round(CX + 7 * math.cos(a)), DY, round((PZ0 + PZ1) // 2 + 7 * math.sin(a)), GOLD_BRICK)
        b.box(CX, DY + 9, (PZ0 + PZ1) // 2, CX, DY + 11, (PZ0 + PZ1) // 2, GOLD_BRICK)
        b.set(CX, DY + 12, (PZ0 + PZ1) // 2, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        # inside: the throne room, red runner, pillars, braziers, treasure, and the chest behind the throne
        TZ = PZ0 + 3
        b.box(CX - 4, 1, PZ0 + 1, CX + 4, 1, TZ + 1, TILE)
        for x in range(CX - 4, CX + 5):
            b.set(x, 1, TZ + 2, stair(ABF, "north"))
        b.set(CX, 2, TZ, facing("throne", "south"))
        b.chest(CX, 2, PZ0 + 1, "sunken_kasbah", "south")
        for x in (CX - 3, CX + 3):
            b.set(x, 2, TZ, facing("treasure_pile", "south"))
            b.set(x, 2, PZ0 + 1, "minecraft:cut_red_sandstone"); b.set(x, 3, PZ0 + 1, CAMPFIRE)
        for z in range(TZ + 3, PZ1):
            b.set(CX, 1, z, "minecraft:red_carpet"); b.set(CX - 1, 1, z, "minecraft:red_carpet"); b.set(CX + 1, 1, z, "minecraft:red_carpet")
        for z in range(PZ0 + 6, PZ1 - 1, 4):
            for x in (CX - 7, CX + 7):
                b.box(x, 1, z, x, 7, z, "minecraft:cut_sandstone")
                b.set(x, 1, z, "minecraft:chiseled_sandstone"); b.set(x, 7, z, "minecraft:chiseled_sandstone")
            b.hang_from(CX - 4, 6, z, HANG); b.hang_from(CX + 4, 6, z, HANG)
        for x in range(PX0 + 2, CX - 8, 3):
            b.set(x, 1, PZ0 + 1, BARREL); b.set(x + 1, 1, PZ0 + 1, facing("treasure_pile", "south"))
        for x in range(CX + 9, PX1 - 1, 3):
            b.set(x, 1, PZ0 + 1, "minecraft:decorated_pot[cracked=false,facing=south,waterlogged=false]")
        # his chamber upstairs: a stair along the west wall, a bed under a canopy, rugs, a map table, a weapon rack
        b.stair_run(PX0 + 2, 1, PZ1 - 2, 7, "smooth_sandstone", "north", "minecraft:smooth_sandstone")
        b.box(PX0 + 2, 8, PZ1 - 9, PX0 + 2, 8, PZ1 - 6, AIR)
        b.box(UX0 + 1, 8, UZ0 + 1, UX0 + 1, 8, UZ1 - 1, TILE)
        b.box(PX0 + 1, 8, PZ1 - 9, PX0 + 3, 8, PZ1 - 6, AIR)
        b.box(PX0 + 1, 7, PZ1 - 10, PX0 + 3, 7, PZ1 - 10, "minecraft:smooth_sandstone")
        bed("red", UX1 - 3, 9, UZ0 + 1, b, "south")
        for (x, z) in ((UX1 - 4, UZ0 + 1), (UX1 - 2, UZ0 + 1), (UX1 - 4, UZ0 + 3), (UX1 - 2, UZ0 + 3)):
            b.box(x, 9, z, x, 11, z, fence("dark_oak"))
        b.box(UX1 - 4, 12, UZ0 + 1, UX1 - 2, 12, UZ0 + 3, "minecraft:red_wool")
        for x in range(UX0 + 3, UX1 - 5):
            for z in range(UZ0 + 3, UZ1 - 1):
                b.set(x, 9, z, "minecraft:orange_carpet" if (x + z) % 3 else "minecraft:red_carpet")
        b.set(UX0 + 3, 9, UZ0 + 1, "minecraft:cartography_table"); b.set(UX0 + 4, 9, UZ0 + 1, "minecraft:lectern[facing=south,has_book=false,powered=false]")
        for x in range(UX0 + 6, UX0 + 10):
            b.set(x, 10, UZ0 + 1, "minecraft:lightning_rod[facing=south,powered=false,waterlogged=false]")   # his scimitars on the wall
        b.set(CX, 13, (UZ0 + UZ1) // 2, HANG)

        # --- The minaret (the landmark): 34 high, east of the palace, with a balcony and its own little dome.
        MX, MZ = PX1 + 9, Z0 + 10
        b.tower(MX, MZ, 3, 28, AB, y=0, windows=True, ladder_side=True)
        b.cyl(MX, MZ, 3, 0, 2, "minecraft:cut_red_sandstone", hollow=True)
        b.set(MX, 1, MZ + 3, AIR); b.set(MX, 2, MZ + 3, AIR)
        for y in (10, 20):
            b.cyl(MX, MZ, 3, y, y, "minecraft:chiseled_sandstone", hollow=True)
        b.disk(MX, 24, MZ, 5, AB)                                      # the balcony
        for i in range(0, 360, 20):
            a = math.radians(i)
            b.set(round(MX + 5 * math.cos(a)), 25, round(MZ + 5 * math.sin(a)), AB_WALL)
        b.sphere(MX, 30, MZ, 3, "minecraft:yellow_terracotta", upper=True, ry=4)
        b.box(MX, 34, MZ, MX, 35, MZ, GOLD_BRICK)
        b.set(MX, 36, MZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            b.set(MX + dx, 27, MZ + dz, HANG) if b.get(MX + dx, 28, MZ + dz) else None

        # --- Outside: the road south past palms and dead bushes, cacti, bones in the dunes.
        for z in range(Z1 + 3, D + 1):
            for x in range(CX - 2, CX + 3):
                b.set(x, 0, z, "minecraft:smooth_sandstone" if abs(x - CX) < 2 else "minecraft:cut_sandstone")
                for y in range(1, 4):
                    b.set(x, y, z, AIR) if b.get(x, y, z) == "minecraft:sand" else None
        for (x, z) in ((CX - 5, Z1 + 6), (CX + 5, Z1 + 6)):
            b.box(x, 1, z, x, 6, z, "minecraft:cut_sandstone"); b.set(x, 7, z, CAMPFIRE)
        for _ in range(60):
            x, z = rnd.randint(0, W), rnd.randint(0, D)
            if (x < X0 - 1 or x > X1 + 1 or z < Z0 - 1 or z > Z1 + 1) and abs(x - CX) > 4:
                y = 1
                while b.get(x, y, z) not in (None, AIR):
                    y += 1
                if b.get(x, y - 1, z) == "minecraft:sand":
                    if rnd.random() < 0.4:
                        b.box(x, y, z, x, y + rnd.randint(1, 3), z, "minecraft:cactus[age=0]")
                    else:
                        b.set(x, y, z, rnd.choice(["minecraft:dead_bush", "minecraft:dead_bush", "onepiece:sand_rose", BONE]))

        b.rogue(AX, 1, AZ, "khamsin_sandshackle")
        b.crew("sandshackle_raider", ((AX - 8, AZ - 7), (AX + 8, AZ - 7), (AX - 8, AZ + 7), (AX + 8, AZ + 7), (CX, Z1 - 5), (17, 51), (64, 60)))
        b.beast("onepiece:sand_scorpion", ((PX - 1, PZ + 1), (PX + 1, PZ - 1)), y=PB + 1)

    # ============================================================ Captain Gale: the Gilded Wake
    @lair("gilded_wake", "The Gilded Wake", "mortimer_gale", OCEANS + DEEP + ["#minecraft:is_beach", "onepiece:thriller_bark"], "sea")
    def _(b):
        rnd = random.Random(22)
        X0, Y0, Z0, L, WD = 10, -7, 8, 68, 19          # the galleon: stern at x = X0, bow at X0 + L
        CZ = Z0 + WD // 2
        HULL, DECK = "minecraft:dark_oak_planks", "minecraft:spruce_planks"
        MASTS = ((14, 26), (32, 33), (50, 27))
        rot = ["minecraft:dead_tube_coral_block", "minecraft:dead_brain_coral_block", "minecraft:mossy_cobblestone", "minecraft:stripped_dark_oak_wood[axis=y]"]
        rock = ["minecraft:tuff", "minecraft:tuff", "minecraft:cobbled_deepslate", "minecraft:mossy_cobblestone", "minecraft:andesite", "minecraft:gravel"]

        # --- The reef she ran aground on (south): a rocky mound with a beach, the Hoard Cave inside it.
        RX, RZ, RRX, RRZ = 50, 46, 28, 15
        for x in range(RX - RRX - 2, RX + RRX + 3):
            for z in range(RZ - RRZ - 2, RZ + RRZ + 3):
                d = math.hypot((x - RX) / RRX, (z - RZ) / RRZ) + (detail.noise(x * 1.4, z * 1.4, 9) - 0.5) * 0.5
                if d <= 1:
                    top = int(1 + 13 * (1 - d) ** 1.25 + detail.noise(x * 2.5, z * 2.5, 10) * 3) - 1
                    for y in range(-4, top + 1):
                        b.set(x, y, z, rnd.choice(rock))
                    b.set(x, top, z, "minecraft:sand" if top <= 1 else rnd.choice(["minecraft:gravel", "minecraft:coarse_dirt"]) if top <= 3
                          else rnd.choice(["minecraft:grass_block", "minecraft:grass_block", "minecraft:moss_block", "minecraft:coarse_dirt"]) if detail.noise(x * 2, z * 2, 12) > 0.42 else rnd.choice(rock))
        b.skirt(RX, RZ, RRX - 1, -16, -5, rock, rnd, spread=0.25, sz=RRX / RRZ)
        # the Hoard Cave: a hollow in the mound, its mouth facing the ship
        CVX, CVZ = RX + 2, RZ + 1
        for x in range(CVX - 10, CVX + 11):
            for z in range(CVZ - 9, CVZ + 8):
                for y in range(1, 7):
                    if math.hypot((x - CVX) / 9, (y - 1) / 5.2, (z - CVZ) / 6.5) <= 1:
                        b.set(x, y, z, AIR)
        for x in range(CVX - 3, CVX + 4):
            for z in range(RZ - RRZ - 2, CVZ - 4):
                for y in range(1, 5 - abs(x - CVX) // 2):
                    b.set(x, y, z, AIR)
        for x in range(CVX - 9, CVX + 10):
            for z in range(CVZ - 7, CVZ + 7):
                if b.get(x, 1, z) == AIR:
                    b.set(x, 0, z, rnd.choice(["minecraft:sand", "minecraft:gravel", "minecraft:tuff"]))
        for (x, z, r) in ((CVX - 5, CVZ + 3, 2.2), (CVX + 4, CVZ + 4, 1.8), (CVX + 6, CVZ - 1, 1.5)):   # heaps of cursed gold
            b.sphere(x, 1, z, r, GOLD_BRICK, upper=True, ry=r * 0.8)
            b.set(x, round(1 + r * 0.8) + 1, z, facing("treasure_pile", "north"))
        for (x, z, f) in ((CVX - 2, CVZ + 5, "north"), (CVX + 1, CVZ + 5, "north"), (CVX - 7, CVZ, "east"), (CVX + 8, CVZ + 1, "west")):
            b.set(x, 1, z, facing("treasure_pile", f))
        for (x, z) in ((CVX - 3, CVZ - 2), (CVX + 3, CVZ - 3)):        # the ones who came for it
            b.set(x, 1, z, BONE); b.set(x + 1, 1, z, "minecraft:bone_block[axis=x]"); b.set(x, 2, z, "minecraft:skeleton_skull[powered=false,rotation=4]")
        for (x, z) in ((CVX - 6, CVZ - 4), (CVX + 6, CVZ + 5), (CVX, CVZ + 6)):
            b.set(x, 1, z, SOUL_FIRE)
        for _ in range(14):
            x, z, y = rnd.randint(CVX - 8, CVX + 8), rnd.randint(CVZ - 6, CVZ + 6), rnd.randint(3, 6)
            if b.get(x, y, z) == AIR and b.get(x, y + 1, z) not in (None, AIR):
                b.set(x, y, z, "minecraft:cobweb" if rnd.random() < 0.6 else SOUL_HANG)
        # the beach: a beached longboat, broken barrels, bones, driftwood
        BX, BZ = RX - 20, RZ + 4
        for x in range(BX, BX + 7):
            half = 1 if x in (BX, BX + 6) else 2
            for z in range(BZ - half, BZ + half + 1):
                b.set(x, 1, z, HULL if abs(z - BZ) == half or x in (BX, BX + 6) else AIR)
            b.set(x, 0, BZ, HULL)
        b.set(BX + 3, 1, BZ, "minecraft:spruce_slab[type=top,waterlogged=false]")
        b.set(BX + 2, 2, BZ + 2, fence("spruce")); b.set(BX + 4, 2, BZ - 2, fence("spruce"))   # oarlocks
        for (x, z) in ((RX + 18, RZ - 6), (RX + 22, RZ + 2), (RX - 14, RZ - 8), (RX + 10, RZ + 11)):
            y = 1
            while b.get(x, y, z) not in (None, AIR):
                y += 1
            b.set(x, y, z, rnd.choice([BARREL, BONE, log("dark_oak", "x"), "minecraft:dead_bush"]))

        # --- The Gilded Wake: a black galleon with gold trim, three masts of rotted sails and a stern castle.
        dy = b.ship(X0, Y0, Z0, L, WD, hull=HULL, deck=DECK, masts=MASTS, sail="minecraft:light_gray_wool",
                    flag=("minecraft:black_wool", "minecraft:white_wool"), depth=8)
        b.mast_yard(X0, dy, Z0, WD, MASTS)
        def half(x, y):
            zs = [z for z in range(Z0 - 1, Z0 + WD + 1) if b.get(x, y, z) in (HULL, DECK)]
            return (CZ - min(zs)) if zs else 0
        for x in range(X0, X0 + L):                                   # gilded: a gold rail and a gold band below it
            h = half(x, dy)
            for z in (CZ - h, CZ + h):
                if x % 3:
                    b.set(x, dy, z, GOLD_BRICK)
            hb = half(x, dy - 3)
            for z in (CZ - hb, CZ + hb):
                if hb:
                    b.set(x, dy - 3, z, GOLD_BRICK)
            for y in range(Y0, dy - 4):                               # rot and barnacles below the waterline
                hl = half(x, y)
                for z in (CZ - hl, CZ + hl):
                    if hl and rnd.random() < 0.18:
                        b.set(x, y, z, rnd.choice(rot))
        detail.tatter(b, "minecraft:light_gray_wool", rnd, ["minecraft:gray_wool"])   # old, torn cloth
        for (mx, mh) in MASTS:                                         # crow's nests with green fire
            ny = dy + mh - 5
            b.disk(X0 + mx, ny, CZ, 2, DECK)
            for i in range(0, 360, 30):
                a = math.radians(i)
                b.set(round(X0 + mx + 2 * math.cos(a)), ny + 1, round(CZ + 2 * math.sin(a)), fence("dark_oak"))
            b.set(X0 + mx, ny, CZ, log("spruce"))
            b.set(X0 + mx + 1, ny + 1, CZ, SOUL_LANTERN)
        # the hold: carved out under the deck, with cursed cargo, cages and the crew that never left
        HX0, HX1 = X0 + 18, X0 + 48
        for x in range(HX0, HX1 + 1):
            for z in range(CZ - 5, CZ + 6):
                for y in range(dy - 4, dy):
                    b.set(x, y, z, AIR)
            for z in range(CZ - 5, CZ + 6):
                b.set(x, dy - 5, z, DECK)
        for x in range(HX0, HX1 + 1, 4):
            b.box(x, dy - 4, CZ - 5, x, dy - 1, CZ - 5, log("dark_oak")); b.box(x, dy - 4, CZ + 5, x, dy - 1, CZ + 5, log("dark_oak"))
            b.set(x + 2, dy - 1, CZ, SOUL_HANG)
        b.stair_run(X0 + 45, dy - 4, CZ, 5, "dark_oak", "west", HULL)   # up to a hatch in the deck
        for i in range(5):
            for yy in (dy - 4 + i + 1, dy - 4 + i + 2):
                if yy <= dy:
                    b.set(X0 + 45 - i, yy, CZ, AIR)
        for i in (0, 1):
            b.set(X0 + 41 + i, dy, CZ - 1, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        for x in range(HX0 + 1, X0 + 38, 3):
            b.set(x, dy - 4, CZ - 4, BARREL); b.set(x + 1, dy - 4, CZ - 4, facing("treasure_pile", "south"))
            b.set(x, dy - 3, CZ - 4, BARREL) if x % 2 else None
            b.set(x, dy - 4, CZ + 4, "minecraft:cobweb" if x % 2 else facing("treasure_pile", "north"))
        for (x, z) in ((HX0 + 2, CZ - 1), (HX0 + 6, CZ + 1)):         # brig cages
            b.box(x, dy - 4, z, x + 2, dy - 2, z + 2, BARS)
            b.box(x + 1, dy - 4, z + 1, x + 1, dy - 3, z + 1, AIR)
            b.set(x + 1, dy - 4, z + 1, BONE)
        b.box(X0 + 30, dy - 4, CZ - 2, X0 + 34, dy - 4, CZ + 2, "minecraft:yellow_carpet")
        b.sphere(X0 + 32, dy - 4, CZ, 1.8, GOLD_BRICK, upper=True, ry=1.4)
        # the stern castle: the captain's quarters below, a poop deck with the wheel above
        SX0, SX1 = X0 + 1, X0 + 13
        b.hall(SX0, CZ - 6, SX1, CZ + 6, dy, 5, HULL, HULL, log("dark_oak"), trim=GOLD_BRICK, floor=DECK, win=pane("cyan"), every=3,
               doors=[("east", 5, 3, 3)], proud=False)
        b.stair_run(X0 + 18, dy + 1, CZ + 5, 5, "dark_oak", "west", HULL)
        for x in range(SX0, SX1 + 1):
            for z in (CZ - 6, CZ + 6):
                b.set(x, dy + 6, z, fence("dark_oak"))
        for z in range(CZ - 6, CZ + 7):
            b.set(SX0, dy + 6, z, fence("dark_oak"))
        b.set(SX1 - 1, dy + 6, CZ, facing("ships_wheel", "east"))
        for (x, z) in ((SX0, CZ - 6), (SX0, CZ + 6)):
            b.box(x, dy + 6, z, x, dy + 8, z, fence("dark_oak")); b.set(x, dy + 9, z, SOUL_LANTERN)   # stern lanterns
        b.hall(SX0 + 1, CZ - 3, SX0 + 6, CZ + 3, dy + 5, 3, HULL, HULL, log("dark_oak"), trim=GOLD_BRICK, floor=DECK, win=pane("cyan"), every=3,
               doors=[("east", 2, 1, 2)], proud=False)
        b.gable_roof(SX0 + 1, CZ - 3, SX0 + 6, CZ + 3, dy + 9, "dark_oak", HULL, axis="x")
        b.set(SX0 + 3, dy + 6, CZ, "minecraft:cartography_table"); b.set(SX0 + 3, dy + 6, CZ + 1, "minecraft:lectern[facing=east,has_book=false,powered=false]")
        # the captain's cabin: his chest on a bed of gold, a table laid for a dinner nobody ate, a skeleton in his chair
        I = dy + 1
        b.box(SX0 + 1, dy, CZ - 5, SX1 - 1, dy, CZ + 5, "minecraft:dark_oak_planks")
        for x in range(SX0 + 1, SX1):
            for z in range(CZ - 5, CZ + 6):
                b.set(x, I, z, "minecraft:yellow_carpet" if (x < SX0 + 5 and abs(z - CZ) < 4) else ("minecraft:red_carpet" if abs(z - CZ) < 2 else None) or AIR)
        b.chest(SX0 + 2, I, CZ, "gilded_wake", "east")
        for (x, z) in ((SX0 + 2, CZ - 2), (SX0 + 2, CZ + 2), (SX0 + 3, CZ - 3), (SX0 + 3, CZ + 3)):
            b.set(x, I, z, facing("treasure_pile", "east"))
        b.table(SX0 + 7, I, CZ - 3, "dark_oak", "minecraft:white_carpet", w=3, axis="z")
        b.set(SX0 + 7, I + 2, CZ - 2, candle(3, "white"))
        b.set(SX0 + 6, I, CZ - 2, stair("dark_oak", "west")); b.set(SX0 + 6, I + 1, CZ - 2, "minecraft:skeleton_skull[powered=false,rotation=4]")
        b.set(SX0 + 8, I, CZ - 3, stair("dark_oak", "east"))
        for z in (CZ - 5, CZ + 5):
            b.shelf(SX0 + 5, I, z, h=2, axis="x", n=3)
        for (x, z) in ((SX0 + 1, CZ - 5), (SX0 + 1, CZ + 5), (SX1 - 1, CZ + 5)):
            b.set(x, I + 2, z, "minecraft:cobweb")
        b.set(SX0 + 4, dy + 4, CZ, SOUL_HANG); b.set(SX0 + 9, dy + 4, CZ, SOUL_HANG)
        # the forecastle: a raised deck at the bow, stairs up from the waist, a bowsprit and a gold skull figurehead
        FX0, FX1 = X0 + L - 18, X0 + L - 3
        for x in range(FX0, FX1 + 1):
            h = half(x, dy)
            for z in range(CZ - h, CZ + h + 1):
                b.box(x, dy + 1, z, x, dy + 2, z, HULL if abs(z - CZ) == h or x == FX0 else AIR)
                b.set(x, dy + 3, z, DECK if abs(z - CZ) < h else GOLD_BRICK)
                if abs(z - CZ) == h:
                    b.set(x, dy + 4, z, fence("dark_oak"))
        b.set(FX0, dy + 1, CZ, AIR); b.set(FX0, dy + 2, CZ, AIR)          # a door under the forecastle
        b.stair_run(FX0 - 3, dy + 1, CZ - 4, 3, "dark_oak", "east", HULL, width=1)
        b.stair_run(FX0 - 3, dy + 1, CZ + 4, 3, "dark_oak", "east", HULL, width=1)
        for i in range(10):
            b.set(X0 + L - 2 + i, dy + 3 + i // 3, CZ, fence("dark_oak"))
        b.sphere(X0 + L, dy - 1, CZ, 1.6, GOLD_BRICK)
        b.set(X0 + L + 1, dy - 1, CZ, "minecraft:black_concrete")
        b.set(X0 + L - 6, dy + 4, CZ + half(X0 + L - 6, dy) + 1, facing("anchor", "south"))
        b.set(FX0 + 6, dy + 4, CZ, facing("cannon", "east"))
        b.set(FX0 + 3, dy + 4, CZ - 2, SOUL_LANTERN); b.set(FX0 + 3, dy + 4, CZ + 2, SOUL_LANTERN)
        # the waist: cannons along both rails, coils of rope, barrels, cobwebs in the rigging
        for x in range(X0 + 20, FX0 - 4, 5):
            if abs(x - (X0 + 32)) < 2:
                continue
            h = half(x, dy)
            b.set(x, dy + 1, CZ - h + 1, facing("cannon", "north")); b.set(x, dy + 1, CZ + h - 1, facing("cannon", "south"))
        for (x, z) in ((X0 + 17, CZ - 6), (X0 + 36, CZ + 6), (X0 + 47, CZ - 6), (X0 + 24, CZ + 6)):
            b.set(x, dy + 1, z, BARREL)
        for (mx, mh) in MASTS:
            b.set(X0 + mx - 1, dy + 1, CZ, "minecraft:hay_block[axis=y]") if mx != 32 else None
        for x in range(X0 + 16, FX0 - 1, 6):
            b.set(x, dy + 1, CZ + half(x, dy) - 2, SOUL_LANTERN) if (x - X0) % 12 == 4 else None
        # the gangplank down to the reef
        GX = X0 + 36
        gz0 = CZ + half(GX, dy)
        z = gz0
        while z < RZ - RRZ + 6 and z < 60:
            for dx in (0, 1):
                b.set(GX + dx, dy, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
            z += 1
            if b.get(GX, dy, z) not in (None, AIR) and z > gz0 + 2:
                break
        b.set(GX - 1, dy + 1, gz0 + 2, fence("spruce")); b.set(GX + 2, dy + 1, gz0 + 2, fence("spruce"))

        # --- The landmark: the Wake's sister ship, sunk alongside her, its last mast and rag of a sail out of the water.
        WX, WZ = X0 + 20, Z0 - 20
        wdy = b.ship(WX, -17, WZ, 34, 11, hull=HULL, deck=DECK, masts=((14, 31),), sail="minecraft:black_wool", flag=None, depth=5)
        b.mast_yard(WX, wdy, WZ, 11, ((14, 31),))
        for p in [p for p, s in b.blocks.items() if s == "minecraft:black_wool" and p[2] < Z0 - 2]:
            if p[1] < 0 or detail.noise(p[0] * 2 + p[2] * 3, p[1] * 2, 33) > 0.62:
                b.set(*p, AIR)
        for y in range(-11, 15):
            if rnd.random() < 0.15:
                b.set(WX + 14, y, WZ + 6, "minecraft:cobweb") if y > 0 else None
        b.set(WX + 14, wdy + 31, WZ + 5, SOUL_LANTERN)

        for comp in b.floating_parts(ground=-16):                      # bits of cave roof left hanging by the carving
            if len(comp) < 8:
                for p in comp:
                    b.set(*p, AIR)

        gilded_island(b, rnd, RX, RZ, RRX, RRZ, CVX, CVZ, rock)
        gilded_ship(b, rnd, X0, Z0, L, CZ, dy, HULL, DECK, FX0)

        b.waterline = dy - 2   # the sea's top layer: the deck stands 2 above it
        b.rogue(X0 + 26, dy + 1, CZ, "mortimer_gale")
        b.crew("cursed_deckhand", ((X0 + 22, CZ - 4), (X0 + 22, CZ + 4), (X0 + 38, CZ - 4), (X0 + 38, CZ + 4), (X0 + 47, CZ + 1)), y=dy + 1)
        b.crew("cursed_deckhand", ((FX0 + 8, dy + 4, CZ), (CVX, 1, CVZ)))

    # ============================================================ Vasco: the Leviathan Pens
    @lair("leviathan_pens", "The Leviathan Pens", "vasco_tidebreaker", OCEANS + ["#minecraft:is_beach", "onepiece:fishman_reef"], "sea")
    def _(b):
        rnd = random.Random(23)
        WL = 2                       # the sea's top layer
        F = WL + 2                   # the island's top
        CX, CZ = 44, 44
        rock = ["minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:gravel", "minecraft:mossy_cobblestone"]
        grass = ["minecraft:grass_block"] * 5 + ["minecraft:coarse_dirt", "minecraft:moss_block"]
        PEN = ["minecraft:stone_bricks"] * 4 + ["minecraft:mossy_stone_bricks"] * 2 + ["minecraft:cracked_stone_bricks"]

        # --- The island: a rocky islet with grassy top, a gravel track round it.
        for x in range(CX - 27, CX + 28):
            for z in range(CZ - 25, CZ + 26):
                d = math.hypot((x - CX) / 25, (z - CZ) / 23) + rnd.random() * 0.06
                if d <= 1:
                    for y in range(WL - 3, F):
                        b.set(x, y, z, rnd.choice(rock) if d > 0.92 or y < F - 2 else "minecraft:dirt")
                    b.set(x, F, z, rnd.choice(grass) if d < 0.93 else rnd.choice(rock))
        b.skirt(CX, CZ, 24, -16, WL - 4, rock, rnd, spread=0.25, sz=25 / 23)
        for i in range(0, 360, 2):
            a = math.radians(i)
            for r in (17, 18):
                x, z = round(CX + r * math.cos(a)), round(CZ + r * 0.92 * math.sin(a))
                b.set(x, F, z, "minecraft:gravel" if r == 17 else "minecraft:coarse_dirt")

        # --- The Breaking Ring (the arena): a sand ring fenced with logs, a grandstand on the west side.
        AX, AZ, R = CX, CZ + 4, 10
        b.disk(AX, F, AZ, R + 1, "minecraft:stripped_spruce_log[axis=y]")
        b.disk(AX, F, AZ, R, "minecraft:sand")
        for y in range(F - 2, F):
            b.disk(AX, y, AZ, R, "minecraft:sandstone")
        for i in range(0, 360, 3):
            a = math.radians(i)
            x, z = round(AX + (R + 1) * math.cos(a)), round(AZ + (R + 1) * math.sin(a))
            if 80 <= i <= 100 or 260 <= i <= 280:
                continue   # gates
            b.box(x, F + 1, z, x, F + 2, z, "minecraft:stripped_spruce_log[axis=y]")
            b.set(x, F + 3, z, fence("spruce"))
        for i in range(0, 360, 30):
            a = math.radians(i)
            x, z = round(AX + (R + 1) * math.cos(a)), round(AZ + (R + 1) * math.sin(a))
            if not (80 <= i <= 100 or 260 <= i <= 280):
                b.set(x, F + 4, z, LANTERN)
        for (r, step) in ((13, 1), (14, 2), (15, 3), (16, 4)):           # the grandstand, four tiers
            for i in range(140, 221, 2):
                a = math.radians(i)
                x, z = round(AX + r * math.cos(a)), round(AZ + r * math.sin(a))
                for y in range(F + 1, F + step):
                    b.set(x, y, z, "minecraft:spruce_planks")
                b.set(x, F + step, z, stair("spruce", "west"))
        for i in (140, 220):
            a = math.radians(i)
            for r in range(13, 17):
                x, z = round(AX + r * math.cos(a)), round(AZ + r * math.sin(a))
                b.box(x, F + 1, z, x, F + 6, z, log("spruce"))
        for i in range(140, 221, 4):
            a = math.radians(i)
            x, z = round(AX + 17 * math.cos(a)), round(AZ + 17 * math.sin(a))
            b.box(x, F + 1, z, x, F + 6, z, "minecraft:spruce_planks")
            b.set(x, F + 7, z, f"minecraft:{'red' if i % 8 else 'white'}_wool")           # a striped awning over the stand
            for r in (16, 15, 14):
                xx, zz = round(AX + r * math.cos(a)), round(AZ + r * math.sin(a))
                b.set(xx, F + 7, zz, f"minecraft:{'red' if i % 8 else 'white'}_wool")

        # --- The pens: four stone pens built out into the sea, open water inside, a sea monster in each.
        pens = [(CX + 26, CZ - 13), (CX + 26, CZ + 3), (CX - 13, CZ + 24), (CX + 3, CZ + 24)]
        for (px, pz) in pens:
            for x in range(px, px + 15):
                for z in range(pz, pz + 15):
                    if x in (px, px + 14) or z in (pz, pz + 14):
                        for y in range(-16, F + 1):
                            b.set(x, y, z, rnd.choice(PEN))
                        b.set(x, F + 1, z, slab("stone_brick") if (x + z) % 2 else fence("spruce"))
            sea_side = "east" if px > CX else "south"
            for i in range(5, 10):                                    # the sea gate: iron bars from below the water to the top
                x, z = (px + 14, pz + i) if sea_side == "east" else (px + i, pz + 14)
                for y in range(WL - 6, F + 1):
                    b.set(x, y, z, BARS)
            for (cx, cz) in ((px, pz), (px + 14, pz), (px, pz + 14), (px + 14, pz + 14)):
                b.lamp_post(cx, F + 1, cz, "spruce", 3)
            fx, fz = (px + 1, pz + 6) if sea_side == "east" else (px + 6, pz + 1)   # a feeding platform
            for dx in range(3):
                for dz in range(3):
                    b.set(fx + dx, F, fz + dz, "minecraft:spruce_planks")
                    b.box(fx + dx, -6, fz + dz, fx + dx, F - 1, fz + dz, log("spruce")) if (dx, dz) in ((0, 0), (2, 2), (0, 2), (2, 0)) else None
            b.set(fx + 1, F + 1, fz + 1, facing("fish_crate", "north")); b.set(fx, F + 1, fz, BARREL)
            b.set(fx + 2, F + 1, fz + 2, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")   # a harpoon stood up
        b.beast("onepiece:sea_cat", ((pens[0][0] + 7, WL - 4, pens[0][1] + 7), (pens[1][0] + 7, WL - 4, pens[1][1] + 7)))
        b.beast("onepiece:megalo", ((pens[2][0] + 7, WL - 4, pens[2][1] + 7), (pens[3][0] + 7, WL - 4, pens[3][1] + 7)))
        for (x0, z0, x1, z1) in ((CX + 22, CZ - 8, CX + 26, CZ + 10), (CX - 8, CZ + 20, CX + 10, CZ + 24)):   # walkways to the pens
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    if b.get(x, F, z) in (None, AIR) or b.get(x, F, z) in grass + rock:
                        b.set(x, F, z, "minecraft:spruce_planks")
                        if b.get(x, F - 1, z) in (None, AIR):
                            b.box(x, -8, z, x, F - 1, z, log("spruce")) if (x + z) % 4 == 0 else b.set(x, F - 1, z, "minecraft:spruce_planks")

        # --- The landmark: the skeleton of a Sea King that wouldn't be broken, its ribs arching over Vasco's lodge.
        SZ = CZ - 18                                                  # the skeleton runs along x here
        SY = F + 22
        for x in range(CX - 22, CX + 21):
            b.set(x, SY + round(1.5 * math.sin((x - CX) / 7.0)), SZ, "minecraft:bone_block[axis=x]")
        for x in range(CX - 18, CX + 18, 3):
            top = SY + round(1.5 * math.sin((x - CX) / 7.0))
            rr = 13 - abs(x - CX) * 0.18
            for t in range(0, 181, 3):
                a = math.radians(t)
                z = round(SZ + rr * math.cos(a)); y = round(F + 8 + (top - F - 8) * math.sin(a))
                b.set(x, y, z, BONE)
            for zz in (round(SZ - rr), round(SZ + rr)):              # rib ends planted in the ground
                b.box(x, F - 1, zz, x, F + 8, zz, BONE)
        # the skull at the east end, jaws open, fangs down
        KX, KY = CX + 27, F + 16
        b.sphere(KX, KY, SZ, 6, BONE, hollow=True, ry=4.5)
        b.box(CX + 21, SY - 2, SZ, CX + 22, SY, SZ, BONE)
        for (dz, dy) in ((-3, 1), (3, 1)):                             # eye sockets with green fire
            b.box(KX + 4, KY + dy, SZ + dz - 1, KX + 6, KY + dy + 1, SZ + dz, AIR)
            b.set(KX + 3, KY + dy, SZ + dz, SOUL_FIRE)
        b.box(KX + 2, KY - 5, SZ - 3, KX + 11, KY - 4, SZ + 3, BONE)   # the lower jaw, out over the ground
        b.box(KX + 3, KY - 4, SZ - 2, KX + 11, KY - 4, SZ + 2, AIR)
        for x in range(KX + 3, KX + 11, 2):
            for z in (SZ - 3, SZ + 3):
                b.set(x, KY - 3, z, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
                b.set(x, KY - 6, z, BONE)
        b.box(KX + 4, KY, SZ - 4, KX + 11, KY, SZ + 4, BONE)            # the upper jaw, out past the skull
        for x in range(KX + 5, KX + 12, 2):
            for z in (SZ - 4, SZ + 4):
                b.set(x, KY - 1, z, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
        for x in range(KX + 2, KX + 12, 3):                            # the jaw rests on bone props
            b.box(x, F + 1, SZ - 3, x, KY - 6, SZ - 3, BONE); b.box(x, F + 1, SZ + 3, x, KY - 6, SZ + 3, BONE)
        for i in range(12):                                            # the tail, down to the water at the west end
            x = CX - 22 - i
            y = SY - i * 2
            if y < F:
                break
            b.box(x, y - 1, SZ, x, y, SZ, "minecraft:bone_block[axis=x]")
        b.box(CX - 34, F - 1, SZ, CX - 34, F + 1, SZ, BONE)

        # --- Vasco's lodge (inside the ribs): log hall, his saddle on a rack, harpoons, trophies of the ones that got away.
        LX0, LZ0, LX1, LZ1 = CX - 12, SZ - 6, CX + 12, SZ + 6
        b.hall(LX0, LZ0, LX1, LZ1, F, 6, "minecraft:spruce_planks", "minecraft:cobblestone", log("spruce"), trim="minecraft:stripped_spruce_log[axis=x]",
               floor="minecraft:spruce_planks", win=pane("light_blue"), every=4, doors=[("south", 11, 3, 4)])
        b.gable_roof(LX0, LZ0, LX1, LZ1, F + 6, "dark_prismarine", "minecraft:dark_prismarine", axis="x", eave=True)
        I = F + 1
        b.chest(CX, I, LZ0 + 1, "leviathan_pens", "south")
        for x in (CX - 2, CX + 2):
            b.set(x, I, LZ0 + 1, facing("fish_crate", "south")); b.set(x, I + 1, LZ0 + 1, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        b.box(CX - 1, I + 3, LZ0 + 1, CX + 1, I + 3, LZ0 + 1, BONE)    # a jawbone over the chest
        bed("blue", LX0 + 2, I, LZ0 + 1, b, "south")
        b.set(LX0 + 4, I, LZ0 + 1, BARREL); b.set(LX0 + 5, I, LZ0 + 1, "minecraft:cartography_table")
        b.table(LX0 + 3, I, LZ0 + 6, "spruce", "minecraft:blue_carpet", w=3)
        b.set(LX0 + 2, I, LZ0 + 6, stair("spruce", "east")); b.set(LX0 + 6, I, LZ0 + 6, stair("spruce", "west"))
        for x in range(CX + 4, LX1 - 1, 2):                            # harpoon rack and tack
            b.set(x, I, LZ0 + 1, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
            b.set(x, I + 1, LZ0 + 1, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        b.set(LX1 - 2, I, LZ1 - 2, "minecraft:hay_block[axis=y]"); b.set(LX1 - 2, I + 1, LZ1 - 2, "minecraft:brown_carpet")
        b.set(LX1 - 3, I, LZ1 - 2, "minecraft:iron_chain[axis=x,waterlogged=false]")
        for x in range(LX0 + 2, LX1 - 1, 4):
            b.set(x, F + 5, (LZ0 + LZ1) // 2, BUBBLE_HANG)
        for x in range(LX0 + 1, LX1):
            b.set(x, I, LZ1 - 1, "minecraft:blue_carpet") if abs(x - CX) < 2 else None
        b.stair_run(CX - 1, F, LZ1 + 1, 1, "spruce", "north", "minecraft:spruce_planks", width=3)

        # --- The bunkhouse (east) and the tack shed (west), the dock with a whaleboat (north-west), drying racks.
        b.hall(CX + 12, CZ - 2, CX + 20, CZ + 10, F, 4, "minecraft:spruce_planks", "minecraft:cobblestone", log("spruce"), floor="minecraft:spruce_planks",
               win=pane("light_blue"), every=4, doors=[("west", 5, 1, 3)])
        b.gable_roof(CX + 12, CZ - 2, CX + 20, CZ + 10, F + 4, "spruce", "minecraft:spruce_planks", axis="z")
        for z in (CZ, CZ + 3, CZ + 6):
            b.set(CX + 19, F + 1, z, "minecraft:cyan_bed[facing=east,occupied=false,part=head]")
            b.set(CX + 18, F + 1, z, "minecraft:cyan_bed[facing=east,occupied=false,part=foot]")
        b.set(CX + 14, F + 1, CZ + 8, BARREL); b.set(CX + 13, F + 1, CZ + 8, "minecraft:crafting_table")
        b.set(CX + 16, F + 3, CZ + 4, HANG)
        b.hall(CX - 22, CZ + 2, CX - 14, CZ + 10, F, 4, "minecraft:stripped_spruce_log[axis=y]", "minecraft:cobblestone", log("spruce"),
               floor="minecraft:coarse_dirt", win=None, every=3, doors=[("east", 3, 3, 3)])
        b.gable_roof(CX - 22, CZ + 2, CX - 14, CZ + 10, F + 4, "spruce", "minecraft:spruce_planks", axis="z")
        for (x, z) in ((CX - 20, CZ + 4), (CX - 20, CZ + 6), (CX - 18, CZ + 8), (CX - 16, CZ + 4)):
            b.set(x, F + 1, z, rnd.choice(["minecraft:hay_block[axis=y]", facing("fish_crate", "east"), BARREL]))
        for z in range(CZ - 12, CZ - 1, 3):                            # drying racks of fish (kelp) on the west shore
            b.box(CX - 20, F + 1, z, CX - 20, F + 2, z, fence("spruce")); b.box(CX - 16, F + 1, z, CX - 16, F + 2, z, fence("spruce"))
            for x in range(CX - 20, CX - 15):
                b.set(x, F + 3, z, "minecraft:dried_kelp_block")
        DZ = CZ - 2
        for x in range(CX - 44, CX - 23):                              # the dock
            for dz in (-1, 0, 1):
                b.set(x, F - 1, DZ + dz, "minecraft:spruce_planks")
            if x % 4 == 0:
                b.box(x, -10, DZ - 2, x, F, DZ - 2, log("spruce")); b.box(x, -10, DZ + 2, x, F, DZ + 2, log("spruce"))
                b.set(x, F + 1, DZ - 2, LANTERN if x % 8 == 0 else fence("spruce"))
        b.set(CX - 44, F, DZ, facing("cannon", "west"))
        b.ship(CX - 42, -2, DZ + 3, 18, 7, hull="minecraft:spruce_planks", deck="minecraft:spruce_planks", masts=((8, 11),),
               sail="minecraft:white_wool", flag=("minecraft:blue_wool", "minecraft:white_wool"), depth=4)
        b.mast_yard(CX - 42, 2, DZ + 3, 7, ((8, 11),))
        b.set(CX - 27, F, DZ + 6, facing("anchor", "east"))
        for (x, z) in ((CX - 6, CZ - 30), (CX + 8, CZ - 30), (CX - 24, CZ + 16), (CX + 18, CZ + 18), (CX - 4, CZ + 20)):
            if b.get(x, F, z) in grass + rock:
                b.lamp_post(x, F + 1, z, "spruce", 3)
        b.scatter(CX - 25, CZ - 23, CX + 25, CZ + 23, F + 1, ["minecraft:short_grass", "minecraft:fern", BONE], 0.05, rnd, only_on=grass)

        b.waterline = WL
        b.rogue(AX, F + 1, AZ, "vasco_tidebreaker")
        b.crew("sea_king_wrangler", ((AX - 6, AZ - 6), (AX + 6, AZ - 6), (AX + 6, AZ + 6), (CX + 24, CZ), (CX, CZ + 22), (CX - 30, DZ), (CX + 6, LZ1 + 3)), y=F + 1)

    # ============================================================ Dr. Kreuz: Laboratory Null
    @lair("laboratory_null", "Laboratory Null", "doctor_kreuz",
          ["minecraft:snowy_plains", "minecraft:ice_spikes", "onepiece:punk_hazard_frozen"], "land")
    def _(b):
        rnd = random.Random(24)
        W, D = 96, 82
        CX = 44
        ground = ["minecraft:gravel", "minecraft:stone", "minecraft:snow_block", "minecraft:snow_block", "minecraft:andesite"]
        PAD = ["minecraft:polished_andesite"] * 4 + ["minecraft:smooth_stone"]
        STEEL = "minecraft:light_gray_concrete"
        DARK = "minecraft:polished_deepslate"
        COPPER = "minecraft:waxed_cut_copper"
        def stripes(x, z):
            return "minecraft:yellow_concrete" if ((x + z) // 2) % 2 else "minecraft:black_concrete"

        # --- The ground and the compound pad.
        for x in range(0, W + 1):
            for z in range(0, D + 1):
                for y in range(-2, 0):
                    b.set(x, y, z, "minecraft:stone")
                b.set(x, 0, z, rnd.choice(ground))
        for x in range(6, W - 5):
            for z in range(6, D - 5):
                b.set(x, 0, z, rnd.choice(PAD))
        # cable runs set in the ground from the generator hall to the lab and the gantry
        for x in range(14, 72):
            b.set(x, 0, 37, "minecraft:black_concrete")
        for z in range(31, 44):
            b.set(16, 0, z, "minecraft:black_concrete")
        for z in range(31, 38):
            b.set(71, 0, z, "minecraft:black_concrete")

        # --- The fence: iron bars between steel posts, corner watchtowers with searchlights, a striped barrier at the gate.
        FX0, FZ0, FX1, FZ1 = 4, 4, W - 4, D - 4
        for x in range(FX0, FX1 + 1):
            for z in (FZ0, FZ1):
                if FZ1 == z and abs(x - CX) <= 3:
                    continue
                b.box(x, 1, z, x, 3, z, BARS if x % 5 else wall_post("polished_deepslate"))
                if x % 5 == 0:
                    b.set(x, 4, z, wall_post("polished_deepslate"))
        for z in range(FZ0, FZ1 + 1):
            for x in (FX0, FX1):
                b.box(x, 1, z, x, 3, z, BARS if z % 5 else wall_post("polished_deepslate"))
                if z % 5 == 0:
                    b.set(x, 4, z, wall_post("polished_deepslate"))
        for (cx, cz) in ((FX0, FZ0), (FX1, FZ0), (FX0, FZ1), (FX1, FZ1)):
            for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                b.box(cx + dx, 1, cz + dz, cx + dx, 10, cz + dz, wall_post("polished_deepslate"))
            b.box(cx - 2, 11, cz - 2, cx + 2, 11, cz + 2, LAB)
            for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
                b.box(cx + dx, 12, cz + dz, cx + dx, 13, cz + dz, wall_post("polished_deepslate"))
            b.box(cx - 2, 14, cz - 2, cx + 2, 14, cz + 2, slab("polished_deepslate"))
            b.set(cx, 12, cz, "minecraft:sea_lantern")
        for x in range(CX - 3, CX + 4):                                # the barrier arm and the booth
            b.set(x, 3, FZ1, stripes(x, 0))
        b.box(CX + 4, 1, FZ1, CX + 4, 3, FZ1, STEEL)
        b.room(CX - 9, 0, FZ1 - 4, CX - 5, 4, FZ1 - 1, LAB, floor="minecraft:smooth_stone")
        b.box(CX - 8, 2, FZ1 - 4, CX - 6, 3, FZ1 - 4, pane("light_blue")); b.box(CX - 5, 1, FZ1 - 3, CX - 5, 2, FZ1 - 3, AIR)
        b.set(CX - 7, 4, FZ1 - 2, LAB_LIGHT)
        b.set(CX - 8, 1, FZ1 - 2, facing("den_den_relay", "east"))
        for z in range(FZ1, D + 1):                                    # the road in
            for x in range(CX - 2, CX + 3):
                b.set(x, 0, z, "minecraft:smooth_stone" if abs(x - CX) < 2 else "minecraft:polished_andesite")

        # --- The Proving Ground (the arena): a striped test floor, blast walls, targets and the wreck of a failed prototype.
        AX0, AZ0, AX1, AZ1 = CX - 15, 42, CX + 15, 64
        AZ = (AZ0 + AZ1) // 2
        for x in range(AX0, AX1 + 1):
            for z in range(AZ0, AZ1 + 1):
                edge = x in (AX0, AX1) or z in (AZ0, AZ1)
                b.set(x, 0, z, stripes(x, z) if edge else ("minecraft:smooth_stone" if (x // 5 + z // 5) % 2 else "minecraft:polished_andesite"))
        for _ in range(9):                                             # scorch marks
            sx, sz, r = rnd.randint(AX0 + 3, AX1 - 3), rnd.randint(AZ0 + 3, AZ1 - 3), rnd.uniform(1.2, 2.4)
            for x in range(int(sx - r), int(sx + r) + 1):
                for z in range(int(sz - r), int(sz + r) + 1):
                    if math.hypot(x - sx, z - sz) <= r and rnd.random() < 0.8:
                        b.set(x, 0, z, rnd.choice(["minecraft:blackstone", "minecraft:coal_block", "minecraft:polished_blackstone"]))
        for (x, z, ax) in ((AX0 - 2, AZ0 - 2, 1), (AX1 + 2, AZ0 - 2, -1), (AX0 - 2, AZ1 + 2, 1), (AX1 + 2, AZ1 + 2, -1)):   # L-shaped blast walls
            dz = 1 if z < AZ else -1
            for i in range(7):
                b.box(x + ax * i, 1, z, x + ax * i, 4, z, "minecraft:gray_concrete")
                b.box(x, 1, z + dz * i, x, 4, z + dz * i, "minecraft:gray_concrete")
            b.set(x, 5, z, "minecraft:sea_lantern")
        for z in range(AZ0 + 3, AZ1 - 2, 4):                           # targets along the east side
            b.set(AX1 + 2, 1, z, "minecraft:hay_block[axis=y]"); b.set(AX1 + 2, 2, z, "minecraft:target[power=0]")
        # the failed prototype, face down at the west end, one arm torn off
        for x in range(AX0 + 2, AX0 + 6):
            for z in range(AZ - 3, AZ + 4):
                b.set(x, 1, z, "minecraft:gray_concrete" if (x + z) % 3 else "minecraft:black_concrete")
        b.box(AX0 + 3, 2, AZ - 2, AX0 + 5, 2, AZ + 2, "minecraft:black_concrete")
        b.box(AX0 + 6, 1, AZ - 1, AX0 + 8, 3, AZ + 1, "minecraft:gray_concrete")          # its head
        b.set(AX0 + 7, 4, AZ - 1, "minecraft:black_concrete"); b.set(AX0 + 7, 4, AZ + 1, "minecraft:black_concrete")   # ears of its cap
        b.box(AX0 + 2, 1, AZ + 5, AX0 + 5, 1, AZ + 6, "minecraft:gray_concrete")          # the other arm
        b.set(AX0 + 2, 1, AZ + 7, "minecraft:pink_concrete")
        b.set(AX0 + 4, 3, AZ, SMOKE)                                   # still smoking

        # --- The main lab (north): a long steel-panelled hall, a glass dome over the specimen atrium.
        LX0, LZ0, LX1, LZ1 = 8, 8, 62, 31
        LH = 9
        b.hall(LX0, LZ0, LX1, LZ1, 0, LH, LAB, DARK, STEEL, trim="minecraft:waxed_oxidized_cut_copper", floor="minecraft:white_concrete",
               win=pane("light_blue"), every=4, doors=[("south", CX - LX0 - 2, 5, 5)], win_h=4, ceiling=LAB)
        for x in range(LX0 + 1, LX1):
            for z in range(LZ0 + 1, LZ1):
                if x % 6 == 0 or z % 6 == 0:
                    b.set(x, 0, z, "minecraft:light_gray_concrete")
                if x % 6 == 3 and z % 6 == 3:
                    b.set(x, LH, z, LAB_LIGHT)
        DCX, DCZ, DR = 32, (LZ0 + LZ1) // 2, 9
        b.box(DCX - DR + 1, LH, DCZ - DR + 1, DCX + DR - 1, LH, DCZ + DR - 1, AIR)
        for x in range(DCX - DR, DCX + DR + 1):
            for z in range(DCZ - DR, DCZ + DR + 1):
                if math.hypot(x - DCX, z - DCZ) > DR - 0.5 and b.get(x, LH, z) == AIR:
                    b.set(x, LH, z, LAB)
        b.sphere(DCX, LH, DCZ, DR + 0.5, "minecraft:light_blue_stained_glass", hollow=True, upper=True, ry=8)
        for i in range(0, 360, 45):                                    # the dome's ribs
            a = math.radians(i)
            for t in range(0, 91, 3):
                tt = math.radians(t)
                r = (DR + 0.5) * math.cos(tt)
                b.set(round(DCX + r * math.cos(a)), LH + round(8 * math.sin(tt)), round(DCZ + r * math.sin(a)), STEEL)
        b.set(DCX, LH + 9, DCZ, LAB); b.set(DCX, LH + 10, DCZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        # the specimen tanks under the dome
        for (tx, tz, r) in ((DCX, DCZ, 2.4), (DCX - 6, DCZ - 4, 1.4), (DCX + 6, DCZ - 4, 1.4), (DCX - 6, DCZ + 4, 1.4), (DCX + 6, DCZ + 4, 1.4)):
            b.cyl(tx, tz, r + 0.6, 1, 1, "minecraft:polished_deepslate")
            b.disk(tx, 1, tz, r - 0.4, "minecraft:sea_lantern")
            b.cyl(tx, tz, r, 2, 6, "minecraft:light_blue_stained_glass", hollow=True)
            b.cyl(tx, tz, r - 0.9, 2, 6, WATER)
            b.cyl(tx, tz, r + 0.6, 7, 7, slab("polished_deepslate"))
            b.set(round(tx), 3, round(tz), "minecraft:tube_coral_block" if r < 2 else "minecraft:brain_coral_block")
        # the workshop (west wing): benches, counters, computer banks
        for x in range(LX0 + 2, 22):
            b.set(x, 1, LZ0 + 1, "minecraft:smooth_stone_slab[type=double,waterlogged=false]")
            b.set(x, 2, LZ0 + 1, rnd.choice(["minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
                                             "minecraft:redstone_torch[lit=true]", "minecraft:flower_pot", facing("den_den_relay", "south"), AIR]))
        for (x, blk) in ((LX0 + 2, "minecraft:smithing_table"), (LX0 + 4, "minecraft:anvil[facing=north]"), (LX0 + 6, "minecraft:grindstone[face=floor,facing=north]"),
                         (LX0 + 8, "minecraft:stonecutter[facing=north]"), (LX0 + 10, "minecraft:crafting_table"), (LX0 + 12, "minecraft:cauldron")):
            b.set(x, 1, LZ1 - 2, blk)
        for z in range(LZ0 + 4, LZ1 - 3):                              # banks of machines along the west wall
            b.box(LX0 + 1, 1, z, LX0 + 1, 3, z, rnd.choice(["minecraft:observer[facing=east,powered=false]", "minecraft:dispenser[facing=east,triggered=false]",
                                                          "minecraft:crafter[crafting=false,orientation=east_up,triggered=false]"]))
            b.set(LX0 + 1, 4, z, "minecraft:waxed_copper_bulb[lit=true,powered=false]" if z % 3 == 0 else LAB)
        # Kreuz's office (east wing), walled off: his chest, a desk, a wall of notes and a Pacifista head on the shelf
        OX0 = 48
        b.box(OX0, 1, LZ0 + 1, OX0, LH - 1, LZ1 - 1, LAB)
        b.box(OX0, 1, DCZ - 1, OX0, 3, DCZ + 1, AIR)
        b.chest(LX1 - 2, 1, DCZ, "laboratory_null", "west")
        for z in (DCZ - 2, DCZ + 2):
            b.set(LX1 - 1, 1, z, "minecraft:bookshelf"); b.set(LX1 - 1, 2, z, "minecraft:bookshelf")
        b.box(LX1 - 1, 1, LZ0 + 2, LX1 - 1, 4, LZ0 + 6, "minecraft:bookshelf")
        b.box(LX1 - 1, 1, LZ1 - 6, LX1 - 1, 4, LZ1 - 2, "minecraft:bookshelf")
        for x in range(OX0 + 3, OX0 + 8):                              # his desk
            b.set(x, 1, LZ0 + 3, "minecraft:smooth_quartz_stairs[facing=north,half=top,shape=straight,waterlogged=false]")
        b.set(OX0 + 5, 2, LZ0 + 3, "minecraft:lectern[facing=south,has_book=false,powered=false]")
        b.set(OX0 + 5, 1, LZ0 + 5, stair("quartz", "north"))
        b.box(OX0 + 2, 2, LZ0 + 1, OX0 + 9, 5, LZ0 + 1, "minecraft:black_concrete")   # the blackboard
        for _ in range(16):
            b.set(rnd.randint(OX0 + 2, OX0 + 9), rnd.randint(2, 5), LZ0 + 1, "minecraft:white_concrete")
        b.box(OX0 + 3, 1, LZ1 - 3, OX0 + 5, 3, LZ1 - 1, "minecraft:gray_concrete")       # a spare Pacifista head
        b.set(OX0 + 4, 2, LZ1 - 4, "minecraft:redstone_block")
        b.set(OX0 + 3, 4, LZ1 - 2, "minecraft:black_concrete"); b.set(OX0 + 5, 4, LZ1 - 2, "minecraft:black_concrete")
        bed("white", OX0 + 9, 1, LZ1 - 3, b, "south")
        for (x, z) in ((OX0 + 8, DCZ - 1), (OX0 + 8, DCZ + 1)):
            b.set(x, 1, z, "minecraft:glass"); b.set(x, 2, z, "minecraft:pink_stained_glass")   # brains in jars
        # the antenna on the roof
        AXr, AZr = 18, LZ0 + 6
        b.box(AXr, LH + 1, AZr, AXr, LH + 16, AZr, BARS)
        b.set(AXr, LH + 17, AZr, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        for y in (LH + 6, LH + 11):
            b.box(AXr - 2, y, AZr, AXr + 2, y, AZr, "minecraft:iron_chain[axis=x,waterlogged=false]")
        for x in range(AXr - 3, AXr + 4):
            for y in range(LH + 2, LH + 9):
                if math.hypot(x - AXr, y - (LH + 5)) <= 3.2:
                    b.set(x, y, AZr + 1, "minecraft:white_concrete")
        b.set(AXr, LH + 5, AZr + 2, "minecraft:redstone_block")

        # --- The landmark: the assembly gantry, holding an unfinished Pacifista 34 blocks tall.
        GX0, GZ0, GX1, GZ1 = 64, 10, 86, 34
        PCX, PCZ = 75, 22
        for (x, z) in ((GX0, GZ0), (GX1, GZ0), (GX0, GZ1), (GX1, GZ1)):
            b.box(x, 1, z, x + 1, 38, z + 1, DARK)
        for y in (14, 26, 38):
            for x in range(GX0, GX1 + 2):
                for z in (GZ0, GZ1 + 1):
                    b.set(x, y, z, DARK if y == 38 else "minecraft:smooth_stone_slab[type=top,waterlogged=false]")
            for z in range(GZ0, GZ1 + 2):
                for x in (GX0, GX1 + 1):
                    b.set(x, y, z, DARK if y == 38 else "minecraft:smooth_stone_slab[type=top,waterlogged=false]")
        for x in range(GX0, GX1 + 2):                                  # the crane beam across the top
            b.set(x, 38, PCZ, DARK)
        for (x, z) in ((GX0, GZ0), (GX1 + 1, GZ0), (GX0, GZ1 + 1), (GX1 + 1, GZ1 + 1)):
            b.set(x, 39, z, "minecraft:sea_lantern"); b.set(x, 40, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        BODY, SUIT = "minecraft:gray_concrete", "minecraft:black_concrete"
        for lx in (PCX - 5, PCX + 2):                                  # legs
            b.box(lx, 1, PCZ - 1, lx + 3, 3, PCZ + 3, "minecraft:light_gray_concrete")
            b.box(lx, 4, PCZ - 1, lx + 3, 14, PCZ + 2, SUIT)
        b.box(PCX - 7, 15, PCZ - 3, PCX + 7, 28, PCZ + 4, BODY)       # torso, its plating half on
        for x in range(PCX - 7, PCX + 8):
            for y in range(15, 29):
                if (x + y) % 5 and y > 17:
                    b.set(x, y, PCZ - 3, SUIT)
        b.box(PCX - 3, 19, PCZ - 3, PCX + 3, 25, PCZ - 3, AIR)          # chest panel open on the core
        b.box(PCX - 2, 20, PCZ - 2, PCX + 2, 24, PCZ - 2, "minecraft:light_blue_stained_glass")
        b.box(PCX - 1, 21, PCZ - 1, PCX + 1, 23, PCZ - 1, "minecraft:sea_lantern")
        for y in range(20, 25):
            b.set(PCX - 3, y, PCZ - 4, "minecraft:iron_chain[axis=y,waterlogged=false]") if y % 2 else None
        b.box(PCX - 11, 13, PCZ - 1, PCX - 8, 27, PCZ + 2, SUIT)       # its left arm, hanging
        b.box(PCX - 11, 10, PCZ - 1, PCX - 8, 12, PCZ + 2, BODY)
        b.box(PCX - 11, 10, PCZ - 2, PCX - 8, 12, PCZ - 2, "minecraft:pink_concrete")   # the paw pad
        b.box(PCX - 3, 29, PCZ - 2, PCX + 3, 35, PCZ + 3, BODY)       # the head
        b.box(PCX - 3, 35, PCZ - 2, PCX + 3, 36, PCZ + 3, SUIT)       # its cap
        for x in (PCX - 3, PCX + 2):
            b.box(x, 37, PCZ - 1, x + 1, 37, PCZ + 1, SUIT)             # the bear ears
        b.set(PCX - 2, 32, PCZ - 3, "minecraft:redstone_block"); b.set(PCX + 2, 32, PCZ - 3, "minecraft:redstone_block")
        b.box(PCX - 1, 30, PCZ - 3, PCX + 1, 30, PCZ - 3, SUIT)
        b.box(PCX - 1, 36, PCZ, PCX + 1, 37, PCZ, "minecraft:iron_chain[axis=y,waterlogged=false]")
        # the right arm isn't on yet: it hangs from the crane on a chain
        for y in range(27, 38):
            b.set(PCX + 10, y, PCZ, "minecraft:iron_chain[axis=y,waterlogged=false]")
        b.box(PCX + 9, 13, PCZ - 1, PCX + 12, 26, PCZ + 2, BODY)
        b.box(PCX + 9, 13, PCZ - 2, PCX + 12, 15, PCZ - 2, "minecraft:pink_concrete")
        b.box(PCX + 9, 22, PCZ - 1, PCX + 12, 26, PCZ + 2, SUIT)
        for y in (14, 26):                                             # catwalk arms reaching in to the body
            for x in range(GX0 + 2, PCX - 7):
                b.set(x, y, PCZ + 1, "minecraft:smooth_stone_slab[type=top,waterlogged=false]")
            for x in range(PCX + 8, GX1 + 1):
                b.set(x, y, PCZ + 3, "minecraft:smooth_stone_slab[type=top,waterlogged=false]")
        for y in range(1, 38):                                         # a ladder up one leg of the gantry
            b.set(GX0 - 1, y, GZ1, ladder("west"))

        # --- The generator hall (south-west): copper walls, a reactor column, tesla coils outside.
        GHX0, GHZ0, GHX1, GHZ1 = 8, 40, 26, 58
        b.hall(GHX0, GHZ0, GHX1, GHZ1, 0, 7, COPPER, DARK, "minecraft:waxed_copper_block", trim="minecraft:waxed_oxidized_cut_copper",
               floor="minecraft:smooth_stone", win=pane("orange"), every=3, doors=[("north", 8, 3, 4), ("east", 8, 3, 4)])
        b.hip_roof(GHX0, GHZ0, GHX1, GHZ1, 8, "waxed_cut_copper", COPPER, ov=1)
        RXc, RZc = (GHX0 + GHX1) // 2, (GHZ0 + GHZ1) // 2
        b.cyl(RXc, RZc, 2.5, 1, 6, "minecraft:light_blue_stained_glass", hollow=True)
        b.cyl(RXc, RZc, 1.5, 1, 6, "minecraft:sea_lantern")
        b.cyl(RXc, RZc, 3.2, 1, 1, "minecraft:waxed_copper_block", hollow=True)
        b.cyl(RXc, RZc, 3.2, 6, 6, "minecraft:waxed_copper_block", hollow=True)
        for (x, z) in ((GHX0 + 2, GHZ0 + 2), (GHX1 - 2, GHZ0 + 2), (GHX0 + 2, GHZ1 - 2), (GHX1 - 2, GHZ1 - 2)):
            b.box(x, 1, z, x, 3, z, "minecraft:waxed_copper_block"); b.set(x, 4, z, "minecraft:waxed_copper_bulb[lit=true,powered=false]")
        for (x, z) in ((GHX0 + 3, GHZ1 + 6), (GHX1 - 2, GHZ1 + 9), (GHX0 + 9, GHZ1 + 12)):   # tesla coils
            b.box(x, 1, z, x, 2, z, DARK)
            b.box(x, 3, z, x, 8, z, "minecraft:waxed_cut_copper")
            b.set(x, 9, z, "minecraft:waxed_copper_bulb[lit=true,powered=false]")
            b.set(x, 10, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                b.set(x + dx, 6, z + dz, "minecraft:waxed_cut_copper_slab[type=top,waterlogged=false]")

        # --- The prototype bays (south-east): tall charging alcoves, each with a light pad and cables.
        BX0, BZ0 = 64, 44
        for i in range(5):
            x0 = BX0 + i * 4
            b.box(x0, 0, BZ0, x0 + 4, 8, BZ0 + 6, LAB)
            b.box(x0 + 1, 1, BZ0, x0 + 3, 7, BZ0 + 5, AIR)
            b.box(x0 + 1, 0, BZ0 + 1, x0 + 3, 0, BZ0 + 5, LAB_LIGHT)
            b.box(x0 + 1, 8, BZ0, x0 + 3, 8, BZ0, stripes(x0, 0))
            b.set(x0 + 2, 6, BZ0 + 5, "minecraft:iron_chain[axis=y,waterlogged=false]"); b.set(x0 + 2, 5, BZ0 + 5, "minecraft:iron_chain[axis=y,waterlogged=false]")
        b.box(BX0, 9, BZ0, BX0 + 20, 9, BZ0 + 6, slab("polished_deepslate"))
        for x in range(BX0, BX0 + 21, 4):
            b.set(x, 10, BZ0, "minecraft:sea_lantern")
        b.crates(BX0 + 2, 1, BZ0 + 10, rnd, n=5, spread=3)

        b.scatter(0, 0, W, D, 1, ["minecraft:snow[layers=1]", "minecraft:snow[layers=2]"], 0.12, rnd,
                  only_on=["minecraft:snow_block", "minecraft:gravel", "minecraft:stone", "minecraft:andesite", "minecraft:polished_andesite", "minecraft:smooth_stone"])

        for x in range(CX - 3, CX + 4):   # no drift where Kreuz stands: a 2-layer drift counts as standing in a block
            for z in range(AZ - 3, AZ + 4):
                if (b.get(x, 1, z) or "").startswith("minecraft:snow["):
                    b.set(x, 1, z, AIR)
        b.rogue(CX, 1, AZ, "doctor_kreuz")
        b.crew("pacifista_prototype", ((AX0 + 9, AZ0 + 4), (AX1 - 5, AZ0 + 4), (AX1 - 5, AZ1 - 4), (AX0 + 9, AZ1 - 4), (CX, AZ0 - 4), (BX0 + 6, BZ0 + 10), (CX + 10, FZ1 - 6)))


# ============================================================ loot

def item(name, weight, lo=1, hi=1, extra=None):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    mods = []
    if hi > 1 or lo > 1:
        mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    if extra:
        mods.append(extra)
    if mods:
        e["modifier"] = mods
    return e


def table(*pools):
    return {"type": "minecraft:chest", "pools": [{"rolls": {"type": "minecraft:uniform", "min": lo, "max": hi}, "entries": es} for lo, hi, es in pools]}


BERRY = "onepiece:berry"
ENCHANT = {"type": "minecraft:enchant_randomly"}


def rumor(boss):
    return (1, 1, [item(f"opbosses:rumor_{boss}", 1)])


LOOT = {
    "sunken_kasbah": table((4, 8, [item(BERRY, 10, 8, 20), item("minecraft:gold_ingot", 8, 2, 6), item("minecraft:iron_chain", 6, 2, 6),
                                   item("minecraft:emerald", 5, 1, 4), item("minecraft:brush", 3), item("minecraft:saddle", 3),
                                   item("minecraft:arms_up_pottery_sherd", 2), item("minecraft:prize_pottery_sherd", 2),
                                   item("minecraft:golden_apple", 2), item("minecraft:map", 2)]), rumor("khamsin_sandshackle")),
    "gilded_wake": table((5, 8, [item(BERRY, 10, 12, 32), item("minecraft:gold_ingot", 10, 3, 10), item("minecraft:gold_nugget", 8, 8, 24),
                                 item("minecraft:emerald", 5, 2, 5), item("minecraft:diamond", 4, 1, 3), item("minecraft:heart_of_the_sea", 1),
                                 item("minecraft:spyglass", 3), item("minecraft:compass", 3), item("minecraft:soul_lantern", 4, 1, 3),
                                 item("minecraft:golden_sword", 2, 1, 1, ENCHANT), item("minecraft:golden_apple", 4, 1, 2)]),
                         (1, 1, [item("minecraft:enchanted_book", 1, 1, 1, ENCHANT)]), rumor("mortimer_gale")),
    "leviathan_pens": table((6, 10, [item(BERRY, 10, 24, 56), item("minecraft:trident", 3, 1, 1, ENCHANT), item("minecraft:nautilus_shell", 6, 1, 4),
                                     item("minecraft:prismarine_shard", 8, 4, 12), item("minecraft:saddle", 4), item("minecraft:lead", 6, 1, 3),
                                     item("minecraft:diamond", 6, 2, 5), item("minecraft:netherite_scrap", 3, 1, 2), item("minecraft:heart_of_the_sea", 2),
                                     item("minecraft:enchanted_golden_apple", 1), item("minecraft:golden_apple", 5, 1, 3)]), rumor("vasco_tidebreaker")),
    "laboratory_null": table((6, 10, [item(BERRY, 10, 32, 64), item("onepiece:seastone_ingot", 6, 1, 4), item("minecraft:redstone", 8, 8, 24),
                                      item("minecraft:copper_ingot", 8, 6, 16), item("minecraft:diamond", 6, 2, 6), item("minecraft:netherite_scrap", 4, 1, 2),
                                      item("minecraft:netherite_ingot", 2), item("minecraft:crossbow", 3, 1, 1, ENCHANT), item("minecraft:totem_of_undying", 2),
                                      item("minecraft:enchanted_golden_apple", 2), item("minecraft:experience_bottle", 6, 4, 12)]),
                             (2, 2, [item("minecraft:enchanted_book", 1, 1, 1, ENCHANT)]), rumor("doctor_kreuz")),
}
