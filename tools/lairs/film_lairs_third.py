"""The third band of film villains' lairs: Bear King (Clockwork Island Adventure), Buena Festa (Stampede), Saga (The Curse
of the Sacred Sword) and Count Butler (Chopper's Kingdom on the Island of Strange Animals).
gen_lairs.py calls add() to register them in the film_lairs structure set, like film_lairs.py and film_lairs_more.py.
Same rules as every lair here: a compound 90-100 blocks across, an approach, an arena at the heart, the boss's own
quarters with the chest, crew quarters, props everywhere, several levels and a landmark you can see from far off."""
import math
import random

from kit import AIR, LANTERN, HANG, BARREL, CAMPFIRE, PANE, log, leaves, pane, ladder, bed  # noqa: F401
from parts import stair, slab, fence, candle, carpet, wall_post, SOUL_LANTERN, SOUL_HANG, SOUL_FIRE, SMOKE, WATER  # noqa: F401
from film_lairs import GOLD_BRICK, MARINE_BRICK, facing, item, table, rumor, BERRY, ENCHANT  # noqa: F401
from film_lairs_more import clear_spawns, ROD, BARS_X, BARS_Z, PAPER_LANTERN, PAPER_HANG  # noqa: F401

COPPER = "minecraft:waxed_copper_block"
OXCOPPER = "minecraft:waxed_oxidized_copper"
CUT_COPPER = "minecraft:waxed_cut_copper"
TATAMI = "onepiece:tatami[axis=y]"


def disc_v(b, cx, cy, z, r, s, axis="z", rim=None):
    """A disc standing upright: in the x-y plane at z (axis "z"), or the z-y plane at x (axis "x")."""
    for d in range(-int(r) - 1, int(r) + 2):
        for dy in range(-int(r) - 1, int(r) + 2):
            dist = math.hypot(d, dy)
            if dist <= r + 0.3:
                blk = rim if rim and dist > r - 0.9 else s
                if axis == "z":
                    b.set(cx + d, cy + dy, z, blk)
                else:
                    b.set(z, cy + dy, cx + d, blk)


def gear_v(b, cx, cy, z, r, s, axis="z"):
    """An upright gear wheel: a ring with teeth and four spokes."""
    for a in range(0, 360, 4):
        for rr in (r - 0.5, r):
            x, y = round(cx + rr * math.cos(math.radians(a))), round(cy + rr * math.sin(math.radians(a)))
            b.set(x, y, z, s) if axis == "z" else b.set(z, y, x, s)
    for a in range(0, 360, 30):   # teeth
        x, y = round(cx + (r + 1) * math.cos(math.radians(a))), round(cy + (r + 1) * math.sin(math.radians(a)))
        b.set(x, y, z, s) if axis == "z" else b.set(z, y, x, s)
    for a in (0, 90, 180, 270):
        for rr in range(0, int(r)):
            x, y = round(cx + rr * math.cos(math.radians(a + 45))), round(cy + rr * math.sin(math.radians(a + 45)))
            b.set(x, y, z, s) if axis == "z" else b.set(z, y, x, s)


def torii(b, x, z, h=7, span=6, axis="x"):
    """A red shrine gate across the path: two posts, a black-capped lintel with upturned ends and a tie beam."""
    RED = "minecraft:red_concrete"
    for dx in (0, span):
        px, pz = (x + dx, z) if axis == "x" else (x, z + dx)
        b.box(px, 1, pz, px, h, pz, RED)
        b.set(px, 0, pz, "minecraft:polished_blackstone")
    for d in range(-1, span + 2):
        px, pz = (x + d, z) if axis == "x" else (x, z + d)
        b.set(px, h + 1, pz, "minecraft:black_concrete")
        b.set(px, h, pz, RED) if -1 < d < span + 1 else None
        if 0 < d < span:
            b.set(px, h - 2, pz, RED)
    for d in (-2, span + 2):
        px, pz = (x + d, z) if axis == "x" else (x, z + d)
        b.set(px, h + 2, pz, "minecraft:black_concrete")
    mx, mz = (x + span // 2, z) if axis == "x" else (x, z + span // 2)
    b.set(mx, h - 1, mz, "minecraft:black_concrete")   # the name plaque


def pagoda(b, cx, cz, tiers, base_r, wall, post, fam, fill, y=0, tier_h=4):
    """A stone pagoda: each tier a little smaller, with its own upturned roof. Returns the top y."""
    for t in range(tiers):
        r = base_r - t
        x0, z0, x1, z1 = cx - r, cz - r, cx + r, cz + r
        b.hall(x0, z0, x1, z1, y, tier_h, wall, post, post, floor="minecraft:polished_andesite", win=pane("red") if t else None,
               every=r, doors=[("south", r - 1, 3, 3)] if t == 0 else [], proud=False)
        b.pagoda_roof(x0, z0, x1, z1, y + tier_h, fam, fill, ov=1)
        b.box(x0 + 1, y + tier_h, z0 + 1, x1 - 1, y + tier_h, z1 - 1, fill)
        b.set(cx, y + tier_h - 1, cz, HANG)
        y += tier_h + 1
    b.box(cx, y, cz, cx, y + 4, cz, GOLD_BRICK)   # the spire
    b.set(cx, y + 5, cz, ROD)
    return y


def tent(b, tx, tz, col, rnd, bed_col=None):
    for i in range(4):
        b.box(tx - 3 + i, 1 + i, tz - 3, tx - 3 + i, 1 + i, tz + 3, f"minecraft:{col}_wool")
        b.box(tx + 3 - i, 1 + i, tz - 3, tx + 3 - i, 1 + i, tz + 3, f"minecraft:{col}_wool")
    for i in range(1, 3):
        b.box(tx - 3 + i, 1, tz - 3, tx + 3 - i, i, tz - 3, AIR)
    bed(bed_col or col, tx - 1, 1, tz, b, "south"); b.set(tx + 1, 1, tz + 2, BARREL)


def add(lair, OCEANS, DEEP):
    """Registers the four lairs with gen_lairs's @lair decorator."""

    # ============================================================ Bear King: Clockwork Island
    @lair("clockwork_island", "Clockwork Island", "bear_king",
          ["minecraft:beach", "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow"], "land", group="film_lairs")
    def _(b):
        rnd = random.Random(31)
        W, D = 96, 96
        grass = ["minecraft:grass_block"] * 5 + ["minecraft:coarse_dirt"]
        for x in range(W + 1):
            for z in range(D + 1):
                b.set(x, -1, z, "minecraft:dirt")
                b.set(x, 0, z, "minecraft:sand" if z > D - 14 else rnd.choice(grass))
        # --- The great clock tower (the landmark): a square stone tower with a clock on every side and the city on top.
        TX0, TZ0, TX1, TZ1, TH = 41, 16, 55, 30, 44
        TCX, TCZ = (TX0 + TX1) // 2, (TZ0 + TZ1) // 2
        for y in range(0, TH + 1):
            for x in range(TX0, TX1 + 1):
                for z in range(TZ0, TZ1 + 1):
                    edge = x in (TX0, TX1) or z in (TZ0, TZ1)
                    corner = x in (TX0, TX1) and z in (TZ0, TZ1)
                    if y == 0:
                        b.set(x, y, z, "minecraft:polished_andesite")
                    elif corner:
                        b.set(x, y, z, "minecraft:polished_deepslate")
                    elif edge:
                        b.set(x, y, z, CUT_COPPER if y % 11 == 0 else rnd.choice(["minecraft:stone_bricks"] * 4 + ["minecraft:cracked_stone_bricks"]))
                    else:
                        b.set(x, y, z, AIR)
            if y % 6 == 3 and 3 < y < TH - 12:   # arrow-slit windows up the sides
                for (x, z) in ((TCX, TZ0), (TCX, TZ1), (TX0, TCZ), (TX1, TCZ)):
                    b.set(x, y, z, pane()); b.set(x, y + 1, z, pane())
        b.box(TCX - 1, 1, TZ1, TCX + 1, 4, TZ1, AIR)   # the door, facing the courtyard
        b.set(TCX, 5, TZ1 + 1, HANG)
        # the clock faces, one on each side, with copper rims and hands at ten to two
        CY = TH - 16   # below the braces that hold the city out
        for (fz, axis, out) in ((TZ0 - 1, "z", -1), (TZ1 + 1, "z", 1)):
            disc_v(b, TCX, CY, fz, 5, "minecraft:white_concrete", "z", rim=OXCOPPER)
            for i in range(1, 4):
                b.set(TCX - i, CY + (i + 1) // 2, fz + out, "minecraft:black_concrete")   # hour hand
                b.set(TCX + i, CY + i, fz + out, "minecraft:black_concrete")              # minute hand
            b.set(TCX, CY, fz + out, GOLD_BRICK)
            for (dx, dy) in ((0, 4), (4, 0), (0, -4), (-4, 0)):
                b.set(TCX + dx, CY + dy, fz + out, "minecraft:black_concrete")
        for (fx, out) in ((TX0 - 1, -1), (TX1 + 1, 1)):
            disc_v(b, TCZ, CY, fx, 5, "minecraft:white_concrete", "x", rim=OXCOPPER)
            for i in range(1, 4):
                b.set(fx + out, CY + (i + 1) // 2, TCZ - i, "minecraft:black_concrete")
                b.set(fx + out, CY + i, TCZ + i, "minecraft:black_concrete")
            b.set(fx + out, CY, TCZ, GOLD_BRICK)
            for (dz, dy) in ((0, 4), (4, 0), (0, -4), (-4, 0)):
                b.set(fx + out, CY + dy, TCZ + dz, "minecraft:black_concrete")
        # inside: a spiral stair two wide round the walls, and the clockwork turning in the middle
        ring = []
        for x in range(TX0 + 1, TX1):
            ring.append((x, TZ1 - 1, "east"))
        for z in range(TZ1 - 1, TZ0, -1):
            ring.append((TX1 - 1, z, "north"))
        for x in range(TX1 - 1, TX0, -1):
            ring.append((x, TZ0 + 1, "west"))
        for z in range(TZ0 + 1, TZ1):
            ring.append((TX0 + 1, z, "south"))
        inward = {"east": (0, -1), "north": (-1, 0), "west": (0, 1), "south": (1, 0)}
        CITY = TH   # the city's floor is the tower's top
        b.box(TX0 + 1, CITY, TZ0 + 1, TX1 - 1, CITY, TZ1 - 1, "minecraft:polished_andesite")
        i = 0
        while i < 4 * len(ring):
            x, z, f = ring[i % len(ring)]
            y = 1 + i
            if y > CITY:
                break
            nx, nz = inward[f]
            for (sx, sz) in ((x, z), (x + nx, z + nz)):
                b.set(sx, y, sz, stair("stone_brick", f) if y < CITY else "minecraft:polished_andesite")
                if y > 1 and b.get(sx, y - 1, sz) in (None, AIR):
                    b.set(sx, y - 1, sz, "minecraft:stone_bricks")
                for yy in range(y + 1, y + 4):
                    if yy <= CITY + 2 and b.get(sx, yy, sz) in (None, AIR, "minecraft:polished_andesite") and not (yy == CITY and y + 3 < CITY):
                        b.set(sx, yy, sz, AIR)
            if i % 9 == 4:   # a lamp set into the wall every so often
                b.set(x - nx, y + 2, z - nz, "minecraft:pearlescent_froglight[axis=y]")
            i += 1
        for y in range(1, CITY):   # the clockwork column: a shaft of chain with gears turning on it
            b.set(TCX, y, TCZ, "minecraft:iron_chain[axis=y,waterlogged=false]")
        for (gy, gr) in ((8, 3), (20, 3), (32, 3)):
            gear_v(b, TCX, gy, TCZ, gr, COPPER if gy != 20 else GOLD_BRICK)
        # --- The city on top: a wide plaza held out on copper braces, with houses, a fountain and the great "key".
        PX0, PZ0, PX1, PZ1 = TX0 - 9, TZ0 - 9, TX1 + 9, TZ1 + 9
        for x in range(PX0, PX1 + 1):
            for z in range(PZ0, PZ1 + 1):
                inside = TX0 < x < TX1 and TZ0 < z < TZ1
                if inside and b.get(x, CITY, z) in (None, AIR):
                    continue   # the stair's opening
                b.set(x, CITY, z, "minecraft:smooth_stone" if (x + z) % 2 else "minecraft:polished_andesite")
                if x in (PX0, PX1) or z in (PZ0, PZ1):
                    b.set(x, CITY, z, CUT_COPPER)
                    b.set(x, CITY + 1, z, wall_post("stone_brick"))
        for k in range(1, 10):   # braces from the tower walls out under the plaza's edge
            for z in range(TZ0 + 1, TZ1, 4):
                b.set(TX0 - k, CITY - 10 + k, z, COPPER); b.set(TX1 + k, CITY - 10 + k, z, COPPER)
            for x in range(TX0 + 1, TX1, 4):
                b.set(x, CITY - 10 + k, TZ0 - k, COPPER); b.set(x, CITY - 10 + k, TZ1 + k, COPPER)
        for (hx, hz, wall, roof) in ((PX0 + 1, PZ0 + 1, "minecraft:white_terracotta", "minecraft:red_terracotta"),
                                     (PX1 - 7, PZ0 + 1, "minecraft:yellow_terracotta", "minecraft:blue_terracotta"),
                                     (PX0 + 1, PZ1 - 7, "minecraft:light_blue_terracotta", "minecraft:red_terracotta"),
                                     (PX1 - 7, PZ1 - 7, "minecraft:white_terracotta", "minecraft:green_terracotta")):
            b.house(hx, hz, 7, 7, 4, wall, roof, floor="minecraft:spruce_planks", y=CITY, door="south" if hz < TCZ else "north")
            b.set(hx + 1, CITY + 1, hz + 1, BARREL); b.set(hx + 5, CITY + 1, hz + 5, facing("crate_stack", "north"))
        # the key that holds the city up, standing in the middle of the plaza
        KX, KZ = TCX, PZ0 + 4
        b.box(KX, CITY + 1, KZ, KX, CITY + 10, KZ, GOLD_BRICK)
        disc_v(b, KX, CITY + 13, KZ, 3, GOLD_BRICK, "z")
        disc_v(b, KX, CITY + 13, KZ, 1, AIR, "z")
        for (dx, dy) in ((1, 2), (1, 3), (2, 2), (1, 5), (2, 5), (2, 6)):
            b.set(KX + dx, CITY + dy, KZ, GOLD_BRICK)
        b.box(KX - 2, CITY + 1, KZ - 1, KX + 2, CITY + 1, KZ + 1, "minecraft:polished_deepslate")
        for (x, z) in ((PX0 + 10, TCZ), (PX1 - 10, TCZ), (TCX, PZ1 - 3)):
            b.lamp_post(x, CITY + 1, z, "dark_oak", 3, LANTERN)
        b.flag(PX1 - 2, CITY + 1, PZ1 - 9, h=10, colors=("minecraft:red_wool", "minecraft:black_wool"), skull=True, length=5)
        # --- Trump Castle (east): Bear King's hall, card suits on its banners, towers on its corners. The chest is here.
        CX0, CZ0, CX1, CZ1 = 64, 40, 90, 66
        b.hall(CX0, CZ0, CX1, CZ1, 0, 9, "minecraft:red_terracotta", "minecraft:polished_blackstone_bricks", "minecraft:quartz_pillar[axis=y]",
               trim=GOLD_BRICK, floor="minecraft:polished_blackstone", win=pane("red"), every=4, win_h=3,
               doors=[("west", 11, 3, 4)], proud=True)
        b.gable_roof(CX0, CZ0, CX1, CZ1, 10, "dark_oak", "minecraft:red_terracotta", axis="x")
        for (tx, tz) in ((CX0, CZ0), (CX1, CZ0), (CX0, CZ1), (CX1, CZ1)):
            b.tower(tx, tz, 3, 15, "minecraft:white_concrete", roof="minecraft:red_concrete")
            b.tower_cap(tx, tz, 3, 15, "minecraft:red_concrete")
        for x in range(CX0 + 1, CX1 - 3):   # a red carpet from the door to the throne
            for z in (52, 53, 54):
                b.set(x, 1, z, carpet("red"))
        b.box(CX1 - 4, 1, CZ0 + 8, CX1 - 1, 1, CZ1 - 8, "minecraft:polished_blackstone_bricks")   # the dais
        b.set(CX1 - 2, 2, 53, facing("throne", "west"))
        b.chest(CX1 - 2, 2, 50, "clockwork_island", "west")
        b.set(CX1 - 2, 2, 56, facing("treasure_pile", "west"))
        for (sx, c) in ((CZ0 + 3, "black"), (CZ0 + 8, "red"), (CZ1 - 8, "black"), (CZ1 - 3, "red")):   # the four suits' banners
            b.box(CX1 - 1, 4, sx, CX1 - 1, 7, sx, f"minecraft:{c}_wool")
        for x in range(CX0 + 4, CX1 - 5, 5):
            b.set(x, 8, 53, facing("chandelier", "north"))
            b.set(x, 1, CZ0 + 1, facing("weapon_rack", "south")); b.set(x + 1, 1, CZ1 - 1, facing("wine_rack", "north"))
        b.table(CX0 + 4, 1, CZ0 + 5, "dark_oak", "minecraft:green_carpet", w=6)   # the card table
        for x in range(CX0 + 4, CX0 + 10, 2):
            b.chair(x, 1, CZ0 + 4, "dark_oak", "south"); b.chair(x, 1, CZ0 + 6, "dark_oak", "north")
        b.set(CX0 + 6, 2, CZ0 + 5, facing("treasure_pile", "north"))
        b.set(CX0 + 4, 1, CZ1 - 4, facing("piano", "east"))
        b.set(CX0 + 3, 2, CZ1 - 1, facing("wall_wanted_poster", "north"))
        # --- The Trump Pirates' barracks (west).
        BX0, BZ0, BX1, BZ1 = 4, 40, 28, 60
        b.hall(BX0, BZ0, BX1, BZ1, 0, 6, "minecraft:stone_bricks", "minecraft:mossy_cobblestone", log("dark_oak"),
               floor="minecraft:spruce_planks", win=pane(), every=4, doors=[("east", 8, 3, 3)], proud=True)
        b.gable_roof(BX0, BZ0, BX1, BZ1, 7, "spruce", "minecraft:spruce_planks", axis="x")
        for x in range(BX0 + 2, BX1 - 1, 3):
            bed("red", x, 1, BZ0 + 1, b, "south"); bed("black", x, 1, BZ1 - 2, b, "north")
        b.table(BX0 + 8, 1, 50, "spruce", carpet("red"), w=8)
        for x in range(BX0 + 8, BX0 + 16, 2):
            b.chair(x, 1, 49, "spruce", "south"); b.chair(x, 1, 51, "spruce", "north")
        b.set(BX0 + 10, 2, 50, facing("beer_mugs", "north")); b.set(BX0 + 13, 2, 50, facing("treasure_pile", "north"))
        for x in (BX0 + 6, BX0 + 12, BX0 + 18):
            b.set(x, 5, 50, HANG)
        b.set(BX0 + 2, 1, 50, facing("powder_keg", "east")); b.set(BX0 + 2, 1, 52, facing("cannonball_pile", "east"))
        # --- The courtyard (the arena), south of the tower: paved like a card table, with the King Cannon.
        AX, AZ = 48, 58
        for x in range(30, 63):
            for z in range(33, 80):
                if b.get(x, 0, z) not in (None, "minecraft:sand"):
                    b.set(x, 0, z, "minecraft:polished_andesite" if ((x // 3) + (z // 3)) % 2 else "minecraft:smooth_stone")
        for (dx, dz, c) in ((-1, 0, "red"), (1, 0, "red"), (0, -1, "red"), (0, 1, "red"), (0, 0, "red")):   # a heart in the middle
            b.set(AX + dx, 0, AZ + dz, f"minecraft:{c}_concrete")
        b.set(AX - 1, 0, AZ - 1, "minecraft:red_concrete"); b.set(AX + 1, 0, AZ - 1, "minecraft:red_concrete"); b.set(AX, 0, AZ + 2, "minecraft:red_concrete")
        # the King Cannon, pointing down the courtyard: a black barrel on red wheels, a pile of drill shells beside it
        KCZ = 36
        for z in range(KCZ, KCZ + 11):
            disc_v(b, AX, 4, z, 2.4 if z < KCZ + 9 else 3, "minecraft:black_concrete", "z")
        disc_v(b, AX, 4, KCZ + 10, 1.2, AIR, "z")
        for side in (-4, 4):
            disc_v(b, KCZ + 3, 2, AX + side, 2, "minecraft:red_concrete", "x", rim="minecraft:dark_oak_planks")
        b.box(AX - 3, 1, KCZ + 1, AX + 3, 1, KCZ + 5, "minecraft:dark_oak_planks")
        for (x, z) in ((AX + 7, KCZ + 2), (AX + 8, KCZ + 4), (AX + 7, KCZ + 6)):   # drilling shells
            b.box(x, 1, z, x, 2, z, OXCOPPER); b.set(x, 3, z, ROD)
        for (x, z) in ((31, 34), (62, 34), (31, 78), (62, 78), (31, 56), (62, 56)):
            b.lamp_post(x, 1, z, "dark_oak", 4, LANTERN)
        for (gx, gz) in ((34, 44), (60, 70)):   # old gears from the tower, standing on edge
            gear_v(b, gz, 4, gx, 3, OXCOPPER, axis="x")
            b.box(gx, 0, gz - 4, gx, 0, gz + 4, "minecraft:cobblestone")
        # --- The beach and the Trump Pirates' ship, run up on the sand (south).
        sx, sz, L, SW = 8, D - 14, 30, 11
        deck = b.ship(sx, -3, sz, L, SW, hull="minecraft:red_terracotta", deck="minecraft:spruce_planks", masts=((9, 13), (18, 15)),
                      sail="minecraft:white_wool", flag=("minecraft:red_wool", "minecraft:black_wool"), cabin=(6, 4, "minecraft:dark_oak_planks"))
        b.mast_yard(sx, deck, sz, SW, ((9, 13), (18, 15)))
        cz = sz + SW // 2
        for x in range(sx + 10, sx + 24, 4):
            b.set(x, deck + 1, sz + 2, facing("cannon", "north")); b.set(x, deck + 1, sz + SW - 3, facing("cannon", "south"))
        b.support(sx, sz, sx + L + 2, sz + SW, -3, ["minecraft:sand"], rnd, down_to=-6)
        for z in range(80, D - 13):   # the path from the beach to the courtyard
            for x in range(AX - 2, AX + 3):
                b.set(x, 0, z, "minecraft:gravel" if abs(x - AX) < 2 else "minecraft:cobblestone")
        for (x, z) in ((4, 6), (14, 4), (88, 8), (92, 22), (6, 70), (92, 76), (24, 30), (74, 28), (82, 86)):
            b.tree(x, 1, z, rnd.randint(5, 7), "oak", 2.5)
        for (x, z) in ((70, 90), (80, 88), (90, 92), (60, 92)):
            b.palm(x, 1, z, rnd.randint(5, 7))
        b.scatter(0, 0, W, D, 1, ["minecraft:short_grass", "minecraft:poppy", "minecraft:dandelion", "minecraft:short_grass"], 0.06, rnd, only_on=grass)

        b.rogue(AX, 1, AZ, "bear_king")
        b.crew("trump_pirate", ((AX - 8, AZ - 6), (AX + 8, AZ - 6), (AX - 8, AZ + 8), (AX + 8, AZ + 8), (BX0 + 10, 47), (CX0 + 8, 58),
                                (TCX, CITY + 1, TCZ + 8)))
        clear_spawns(b)

    # ============================================================ Buena Festa: Delta Island, the Pirates Expo
    @lair("delta_island", "Delta Island", "buena_festa",
          ["minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:flower_forest", "minecraft:beach"], "land", group="film_lairs")
    def _(b):
        rnd = random.Random(32)
        W, D = 100, 100
        LX, LZ, LR = 50, 46, 15           # the round lake in the middle
        grass = ["minecraft:grass_block"] * 5 + ["minecraft:coarse_dirt"]
        for x in range(W + 1):
            for z in range(D + 1):
                b.set(x, -1, z, "minecraft:dirt")
                b.set(x, 0, z, rnd.choice(grass))
        # --- Three rivers split the island, running out from the lake (south-west, south-east and north).
        RIVERS = (math.radians(135), math.radians(45), math.radians(270))
        def river(x, z):
            for a in RIVERS:
                dx, dz = math.cos(a), math.sin(a)
                t = (x - LX) * dx + (z - LZ) * dz
                if t > LR - 2 and abs(-(x - LX) * dz + (z - LZ) * dx) <= 1.6:
                    return True
            return False
        for x in range(W + 1):
            for z in range(D + 1):
                d = math.hypot(x - LX, z - LZ)
                if d <= LR or river(x, z):
                    depth = 7 if d <= LR - 3 else 3
                    for y in range(-depth, 1):
                        b.set(x, y, z, WATER)
                    b.set(x, -depth - 1, z, "minecraft:sand")
                elif d <= LR + 1.5:
                    for y in range(-4, 1):
                        b.set(x, y, z, "minecraft:stone")   # the cliff rim
        # --- The audience stands (the lake's cliffs): rings of seats rising away from the water, coloured by section.
        SEATS = ["red", "yellow", "blue", "white"]
        for x in range(W + 1):
            for z in range(D + 1):
                d = math.hypot(x - LX, z - LZ)
                if LR + 2 <= d < LR + 9 and not river(x, z):
                    a = math.degrees(math.atan2(z - LZ, x - LX)) % 360
                    if 80 < a < 100:
                        continue   # the main gangway, from the south
                    row = int(d - (LR + 2))
                    for y in range(1, row + 1):
                        b.set(x, y, z, "minecraft:stone_bricks")
                    if row % 2 == 0:
                        b.set(x, row + 1, z, f"minecraft:{SEATS[int(a // 30) % 4]}_wool" if row else slab("smooth_stone"))
                    else:
                        b.set(x, row + 1, z, slab("smooth_stone"))
                elif LR + 9 <= d < LR + 10 and not river(x, z):
                    a = math.degrees(math.atan2(z - LZ, x - LX)) % 360
                    if not 80 < a < 100:
                        b.box(x, 1, z, x, 8, z, "minecraft:stone_bricks")
                        b.set(x, 9, z, wall_post("stone_brick") if int(a) % 6 else LANTERN)
        for a in range(0, 360, 30):   # bunting poles round the top of the stands
            if 80 < a < 100:
                continue
            x, z = round(LX + (LR + 9.5) * math.cos(math.radians(a))), round(LZ + (LR + 9.5) * math.sin(math.radians(a)))
            if b.get(x, 1, z) == "minecraft:stone_bricks":
                b.box(x, 10, z, x, 14, z, fence("spruce")); b.set(x, 15, z, f"minecraft:{SEATS[(a // 30) % 4]}_wool")
        # --- The stage in the middle of the lake (the arena), on its own rock, with bridges out to the stands.
        b.cyl(LX, LZ, 9, -8, 0, "minecraft:stone")
        b.disk(LX, 1, LZ, 9, "minecraft:spruce_planks")
        b.disk(LX, 1, LZ, 3, GOLD_BRICK)   # the treasure's spot, under the spotlight
        for a in range(0, 360, 20):
            x, z = round(LX + 9 * math.cos(math.radians(a))), round(LZ + 9 * math.sin(math.radians(a)))
            b.set(x, 2, z, fence("spruce") if a % 60 else LANTERN)
        for (dx, dz, f) in ((0, 1, "south"), (-1, 0, "west"), (1, 0, "east")):   # three bridges
            for k in range(9, LR + 3):
                x, z = LX + dx * k, LZ + dz * k
                for w in (-1, 0, 1):
                    bx, bz = (x + w, z) if dz else (x, z + w)
                    b.set(bx, 1, bz, "minecraft:spruce_planks")
                    for yy in range(2, 5):
                        if b.get(bx, yy, bz) not in (None, AIR) and k > LR:
                            b.set(bx, yy, bz, AIR)
                for w in (-2, 2):
                    bx, bz = (x + w, z) if dz else (x, z + w)
                    b.set(bx, 2, bz, fence("spruce"))
                if k % 4 == 0:
                    for w in (-1, 0, 1):
                        bx, bz = (x + w, z) if dz else (x, z + w)
                        b.box(bx, -6, bz, bx, 0, bz, log("spruce")) if w != 0 else None
        # the backdrop: a big festival arch behind the stage with the Expo's banners
        for dx in (-6, 6):
            b.box(LX + dx, 2, LZ - 8, LX + dx, 12, LZ - 8, "minecraft:red_concrete")
        for x in range(LX - 7, LX + 8):
            b.set(x, 13, LZ - 8, "minecraft:yellow_concrete"); b.set(x, 12, LZ - 8, "minecraft:red_concrete")
        for x in range(LX - 5, LX + 6):
            for y in range(7, 12):
                b.set(x, y, LZ - 8, f"minecraft:{SEATS[(x + y) % 4]}_wool" if (x + y) % 3 else "minecraft:white_wool")
        for dx in (-4, 0, 4):   # fireworks launchers on the stage
            b.box(LX + dx, 2, LZ - 6, LX + dx, 3, LZ - 6, "minecraft:red_concrete"); b.set(LX + dx, 4, LZ - 6, ROD)
        # --- Festa's tower (north-east): he watches the whole show from up here. His office (and the chest) is at its foot.
        FX, FZ = 86, 14
        b.tower(FX, FZ, 6, 32, "minecraft:white_concrete", roof="minecraft:red_concrete", floors=[11, 22])
        b.tower_cap(FX, FZ, 6, 32, "minecraft:red_concrete")
        for y in range(4, 30, 7):
            b.cyl(FX, FZ, 6, y, y, "minecraft:red_concrete", hollow=True)
        b.box(FX - 1, 1, FZ + 6, FX + 1, 3, FZ + 6, AIR)   # the door, toward the lake
        b.chest(FX + 3, 1, FZ - 2, "delta_island", "west")
        b.set(FX - 3, 1, FZ - 2, facing("writing_desk", "east")); b.set(FX - 2, 1, FZ - 2, facing("captains_chair", "west"))
        b.set(FX, 1, FZ - 4, facing("grand_line_wall_map", "south")); b.set(FX + 3, 1, FZ + 2, facing("globe", "west"))
        b.set(FX - 3, 1, FZ + 2, facing("drafting_table", "east")); b.set(FX + 2, 1, FZ - 4, facing("book_stack", "south"))
        b.set(FX, 10, FZ, facing("chandelier", "north"))
        b.set(FX - 2, 12, FZ + 2, facing("telescope", "south")); b.set(FX + 2, 12, FZ + 2, facing("den_den_relay", "south"))
        for x in range(FX - 3, FX + 4):   # the balcony on the top floor, looking over the lake
            b.set(x, 22, FZ + 7, "minecraft:spruce_planks"); b.set(x, 23, FZ + 8, fence("spruce"))
            b.set(x, 22, FZ + 8, "minecraft:spruce_planks")
        b.box(FX - 1, 23, FZ + 6, FX + 1, 25, FZ + 6, AIR)
        # the planning room under the tower, where Festa and Bullet drew up the Expo
        b.room(FX - 5, -7, FZ - 5, FX + 5, -1, FZ + 5, "minecraft:stone_bricks", floor="minecraft:spruce_planks")
        for y in range(-6, 1):
            b.set(FX + 4, y, FZ, ladder("west"))
        b.table(FX - 2, -6, FZ - 1, "spruce", "minecraft:white_carpet", w=4)
        b.set(FX - 1, -5, FZ - 1, facing("chart_table", "south")); b.set(FX - 4, -6, FZ - 4, facing("notice_board", "south"))
        b.set(FX, -2, FZ, HANG); b.set(FX - 4, -6, FZ + 3, facing("powder_keg", "east")); b.set(FX - 3, -6, FZ + 4, facing("powder_keg", "north"))
        # --- The harbour market along the south shore: stalls and little shops along the road in.
        for z in range(LZ + LR + 10, D + 1):
            for x in range(LX - 2, LX + 3):
                b.set(x, 0, z, "minecraft:gravel" if abs(x - LX) < 2 else "minecraft:stone_bricks")
        STALLS = ["red", "yellow", "blue", "lime", "orange", "magenta", "cyan", "white"]
        for k, z in enumerate(range(LZ + LR + 12, D - 4, 6)):
            b.stall(LX - 7, 0, z, STALLS[k % 8]); b.stall(LX + 5, 0, z, STALLS[(k + 3) % 8])
            b.set(LX - 4, 1, z + 1, LANTERN) if k % 2 else None
        for (hx, hz, wall, roof) in ((LX - 22, 82, "minecraft:white_terracotta", "minecraft:red_terracotta"),
                                     (LX + 14, 82, "minecraft:yellow_terracotta", "minecraft:blue_terracotta"),
                                     (LX - 38, 58, "minecraft:light_blue_terracotta", "minecraft:orange_terracotta"),
                                     (LX + 22, 89, "minecraft:white_terracotta", "minecraft:green_terracotta")):
            b.house(hx, hz, 8, 7, 4, wall, roof, floor="minecraft:spruce_planks", door="east" if hx < LX else "west")
            b.set(hx + 2, 1, hz + 2, facing("crate_stack", "north")); b.set(hx + 5, 1, hz + 4, BARREL)
        # the Expo's gate at the south edge
        for dx in (-5, 5):
            b.box(LX + dx, 1, D - 2, LX + dx, 11, D - 2, "minecraft:red_concrete")
        for x in range(LX - 6, LX + 7):
            b.set(x, 12, D - 2, "minecraft:yellow_concrete"); b.set(x, 11, D - 2, "minecraft:red_concrete")
            b.set(x, 13, D - 2, f"minecraft:{STALLS[x % 8]}_wool" if x % 2 else AIR)
        # --- The Festival Pirates' camp (west): tents, a mess fire and the fireworks store.
        for (tx, tz, col) in ((10, 14, "red"), (20, 8, "yellow"), (10, 28, "blue"), (22, 22, "red")):
            tent(b, tx, tz, col, rnd)
        b.set(16, 1, 18, CAMPFIRE)
        for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            b.set(16 + dx, 1, 18 + dz, slab("spruce"))
        for k, (x, z) in enumerate(((6, 40), (9, 42), (12, 40), (7, 45), (11, 46))):   # rockets as tall as a man
            b.box(x, 1, z, x, 3, z, f"minecraft:{SEATS[k % 4]}_concrete"); b.set(x, 4, z, "minecraft:red_concrete"); b.set(x, 5, z, ROD)
        b.set(14, 1, 44, facing("powder_keg", "north")); b.set(15, 1, 44, facing("powder_keg", "north")); b.set(14, 1, 45, facing("cannonball_pile", "north"))
        for (x, z) in ((4, 60), (12, 66), (88, 60), (94, 70), (30, 4), (60, 6), (94, 40), (4, 90), (94, 92)):
            b.tree(x, 1, z, rnd.randint(5, 7), "birch" if (x + z) % 2 else "oak", 2.5)
        b.scatter(0, 0, W, D, 1, ["minecraft:short_grass", "minecraft:cornflower", "minecraft:poppy", "minecraft:short_grass", "minecraft:dandelion"],
                  0.06, rnd, only_on=grass)

        b.rogue(LX, 2, LZ + 3, "buena_festa")
        b.crew("festival_pirate", ((LX - 5, 2, LZ - 3), (LX + 5, 2, LZ - 3), (LX - 5, 2, LZ + 5), (LX + 5, 2, LZ + 5), (16, 22), (LX, 90),
                                   (FX, 23, FZ + 3)))
        clear_spawns(b)

    # ============================================================ Saga: Asuka Island, the Seven Star Sword's shrine
    @lair("asuka_island", "Asuka Island", "saga",
          ["minecraft:cherry_grove", "minecraft:meadow", "minecraft:forest", "minecraft:plains", "onepiece:wano"], "land", group="film_lairs")
    def _(b):
        rnd = random.Random(33)
        W, D = 96, 96
        grass = ["minecraft:grass_block"] * 4 + ["minecraft:podzol", "minecraft:moss_block"]
        for x in range(W + 1):
            for z in range(D + 1):
                b.set(x, -1, z, "minecraft:dirt")
                b.set(x, 0, z, rnd.choice(grass))
        # --- The road in from the south, under a line of torii.
        for z in range(70, D + 1):
            for x in range(45, 52):
                b.set(x, 0, z, "minecraft:gravel" if 46 <= x <= 50 else "minecraft:stone_bricks")
        for z in range(74, D, 6):
            torii(b, 45, z, h=6 + (D - z) // 12, span=6)
            b.stone_lantern(43, 1, z + 2, "stone_brick", PAPER_LANTERN); b.stone_lantern(53, 1, z + 2, "stone_brick", PAPER_LANTERN)
        # --- The sacred courtyard (the arena), where the Altar of Ancestors stood before Saga broke it.
        AX, AZ = 48, 56
        for x in range(28, 69):
            for z in range(42, 70):
                b.set(x, 0, z, rnd.choice(["minecraft:stone_bricks", "minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:andesite"]))
        for x in range(28, 69):
            for z in (42, 69):
                b.set(x, 1, z, wall_post("stone_brick") if x % 4 else "minecraft:chiseled_stone_bricks")
        for z in range(42, 70):
            for x in (28, 68):
                if not 54 <= z <= 58:
                    b.set(x, 1, z, wall_post("stone_brick") if z % 4 else "minecraft:chiseled_stone_bricks")
        b.box(46, 1, 69, 50, 1, 69, AIR)
        b.box(46, 1, 42, 50, 1, 42, AIR)
        # the broken altar, at the courtyard's north end: a stepped dais, its pillars snapped, rubble everywhere
        ALZ = 45
        b.box(AX - 6, 1, ALZ - 2, AX + 6, 1, ALZ + 2, "minecraft:polished_andesite")
        b.box(AX - 4, 2, ALZ - 1, AX + 4, 2, ALZ + 1, "minecraft:polished_andesite")
        for (dx, h) in ((-5, 6), (-2, 2), (2, 4), (5, 1)):
            b.box(AX + dx, 2, ALZ + 2, AX + dx, 1 + h, ALZ + 2, "minecraft:stone_brick_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]" if h < 3 else "minecraft:quartz_pillar[axis=y]")
        b.set(AX, 3, ALZ, "minecraft:cracked_stone_bricks"); b.set(AX + 1, 3, ALZ, slab("stone_brick"))
        b.scatter(30, 43, 66, 68, 1, [slab("cobblestone"), "minecraft:cobblestone_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]",
                                      "minecraft:stone_button[face=floor,facing=north,powered=false]"], 0.03, rnd)
        for (x, z) in ((31, 45), (65, 45), (31, 66), (65, 66)):
            b.set(x, 1, z, SOUL_FIRE)   # the sword's green fire burning in the braziers
            b.set(x, 0, z, "minecraft:soul_soil")
        # --- The sword's shrine (north centre): a small hall on a stone platform where the Seven Star Sword was sealed.
        SX, SZ = 48, 22
        b.box(SX - 9, 0, SZ - 7, SX + 9, 2, SZ + 7, "minecraft:stone_bricks")
        b.stair_run(SX - 2, 1, SZ + 9, 2, "stone_brick", "north", "minecraft:stone_bricks", width=5)
        b.hall(SX - 6, SZ - 5, SX + 6, SZ + 5, 2, 6, "minecraft:white_terracotta", "minecraft:stripped_dark_oak_log[axis=y]", "minecraft:red_concrete",
               floor="minecraft:dark_oak_planks", win=None, every=3, doors=[("south", 5, 3, 4)], proud=False)
        b.pagoda_roof(SX - 6, SZ - 5, SX + 6, SZ + 5, 8, "dark_oak", "minecraft:dark_oak_planks", ov=2)
        b.box(SX - 1, 3, SZ - 4, SX + 1, 3, SZ - 3, "minecraft:polished_blackstone")
        b.set(SX, 4, SZ - 4, facing("katana_stand", "south"))   # where the sword rested
        for dx in (-4, -2, 2, 4):
            b.set(SX + dx, 3, SZ - 4, candle(3, "red")); b.set(SX + dx, 3, SZ + 2, facing("andon_lantern", "south"))
        b.set(SX, 3, SZ - 1, SOUL_FIRE); b.set(SX, 2, SZ - 1, "minecraft:soul_soil")
        b.set(SX, 7, SZ, SOUL_HANG)
        for z in range(SZ - 2, SZ + 5):
            b.set(SX, 3, z, carpet("red")) if z != SZ - 1 else None
        torii(b, SX - 3, SZ + 13, h=7, span=6)
        # --- The three seal towers round the shrine: stone pagodas, joined underground by a cave the seal ran through.
        TOWERS = ((24, 14), (72, 14), (48, 2 + 4))
        for (tx, tz) in TOWERS[:2]:
            pagoda(b, tx, tz, 4, 5, "minecraft:stone_bricks", "minecraft:polished_deepslate", "deepslate_tile", "minecraft:deepslate_tiles")
        TX3, TZ3 = 48, 4   # the third, behind the shrine: smaller
        b.box(TX3 - 3, 1, TZ3 - 3, TX3 + 3, 1, TZ3 + 3, "minecraft:stone_bricks")
        b.box(TX3 - 2, 2, TZ3 - 2, TX3 + 2, 10, TZ3 + 2, "minecraft:stone_bricks")
        b.box(TX3 - 1, 2, TZ3 - 1, TX3 + 1, 9, TZ3 + 1, AIR)
        b.pagoda_roof(TX3 - 2, TZ3 - 2, TX3 + 2, TZ3 + 2, 11, "deepslate_tile", "minecraft:deepslate_tiles", ov=1)
        b.box(TX3, 12, TZ3, TX3, 15, TZ3, GOLD_BRICK); b.set(TX3, 16, TZ3, ROD)
        b.box(TX3, 2, TZ3 + 2, TX3, 4, TZ3 + 2, AIR)
        # the cave that joins them, under the courtyard of the shrine
        def tunnel(x0, z0, x1, z1):
            n = int(max(abs(x1 - x0), abs(z1 - z0)))
            for k in range(n + 1):
                x = round(x0 + (x1 - x0) * k / n); z = round(z0 + (z1 - z0) * k / n)
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        b.set(x + dx, -8, z + dz, "minecraft:tuff")
                        for y in range(-7, -3):
                            b.set(x + dx, y, z + dz, AIR)
                        b.set(x + dx, -3, z + dz, "minecraft:tuff") if b.get(x + dx, -3, z + dz) in (None, AIR) else None
                for (sx_, sz_) in ((x - 2, z), (x + 2, z), (x, z - 2), (x, z + 2)):
                    for y in range(-8, -2):
                        if b.get(sx_, y, sz_) is None:
                            b.set(sx_, y, sz_, rnd.choice(["minecraft:tuff", "minecraft:stone", "minecraft:andesite"]))
                if k % 7 == 3:
                    b.set(x, -4, z, SOUL_HANG)
        for (tx, tz) in ((24, 14), (72, 14), (TX3, TZ3)):
            tunnel(tx, tz, SX, SZ)
            for y in range(-7, 1):   # a ladder down from the tower's floor into the cave
                b.set(tx, y, tz - 1, "minecraft:stone_bricks")
                b.set(tx, y, tz, ladder("south"))
        b.room(SX - 4, -9, SZ - 4, SX + 4, -2, SZ + 4, "minecraft:polished_blackstone_bricks", floor="minecraft:polished_blackstone")
        b.box(SX - 3, -8, SZ - 3, SX + 3, -3, SZ + 3, AIR)
        b.set(SX, -8, SZ, "minecraft:soul_soil"); b.set(SX, -7, SZ, SOUL_FIRE)   # the seal's heart, still burning
        for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            b.set(SX + dx, -8, SZ + dz, candle(4, "green"))
        for (tx, tz) in ((24, 14), (72, 14), (TX3, TZ3)):   # open the chamber's walls where the tunnels come in
            ang = math.atan2(tz - SZ, tx - SX)
            hx, hz = round(SX + 4 * math.cos(ang)), round(SZ + 4 * math.sin(ang))
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for y in range(-7, -4):
                        b.set(hx + dx, y, hz + dz, AIR)
        # --- Asuka Palace (west): Saga's quarters. Tatami, sake, his swords; the reliquary chest is in his room.
        PX0, PZ0, PX1, PZ1 = 4, 44, 24, 76
        b.box(PX0 - 1, 0, PZ0 - 1, PX1 + 1, 1, PZ1 + 1, "minecraft:stone_bricks")
        b.hall(PX0, PZ0, PX1, PZ1, 1, 6, "minecraft:white_terracotta", "minecraft:stripped_dark_oak_log[axis=y]", log("dark_oak"),
               floor="minecraft:dark_oak_planks", win=pane("white"), every=4, doors=[("east", 13, 3, 4)], proud=True)
        b.pagoda_roof(PX0, PZ0, PX1, PZ1, 7, "dark_oak", "minecraft:dark_oak_planks", ov=2)
        b.hall(PX0 + 5, PZ0 + 8, PX1 - 5, PZ1 - 8, 8, 4, "minecraft:white_terracotta", "minecraft:stripped_dark_oak_log[axis=y]", log("dark_oak"),
               floor="minecraft:dark_oak_planks", win=pane("white"), every=3, proud=False)
        b.pagoda_roof(PX0 + 5, PZ0 + 8, PX1 - 5, PZ1 - 8, 12, "dark_oak", "minecraft:dark_oak_planks", ov=2)
        for x in range(PX0 + 1, PX1):
            for z in range(PZ0 + 1, PZ1):
                b.set(x, 1, z, TATAMI)
        b.walls(PX0 + 1, 2, PZ0 + 12, PX1 - 1, 4, PZ0 + 12, "minecraft:birch_planks")   # a paper wall closing off his room
        b.box(PX0 + 9, 2, PZ0 + 12, PX0 + 11, 4, PZ0 + 12, AIR)
        b.chest(PX0 + 2, 2, PZ0 + 2, "asuka_island", "south")
        b.set(PX0 + 4, 2, PZ0 + 2, facing("katana_stand", "south")); b.set(PX0 + 6, 2, PZ0 + 2, facing("katana_stand", "south"))
        b.set(PX0 + 10, 2, PZ0 + 5, facing("low_table", "north")); b.set(PX0 + 11, 2, PZ0 + 5, facing("sake_set", "north"))
        b.set(PX0 + 9, 2, PZ0 + 6, facing("red_floor_cushion", "north")); b.set(PX0 + 12, 2, PZ0 + 6, facing("red_floor_cushion", "north"))
        b.set(PX1 - 2, 2, PZ0 + 2, facing("book_stack", "south")); b.set(PX1 - 2, 2, PZ0 + 9, facing("andon_lantern", "west"))
        bed("red", PX1 - 4, 2, PZ0 + 6, b, "south")
        for z in range(PZ0 + 16, PZ1 - 2, 4):   # the great hall: low tables and cushions for his men
            b.set(PX0 + 8, 2, z, facing("low_table", "north")); b.set(PX0 + 12, 2, z, facing("low_table", "north"))
            b.set(PX0 + 7, 2, z, facing("purple_floor_cushion", "east")); b.set(PX0 + 13, 2, z, facing("purple_floor_cushion", "west"))
        for z in range(PZ0 + 6, PZ1 - 3, 6):
            b.set(PX0 + 10, 6, z, PAPER_HANG)
        b.set(PX0 + 1, 2, PZ1 - 2, BARREL)
        # --- The Marine dojo (east), where Saga and Zoro's old friend trained: the swordsmen sleep and drill here.
        DX0, DZ0, DX1, DZ1 = 72, 44, 92, 74
        b.hall(DX0, DZ0, DX1, DZ1, 0, 7, "minecraft:white_concrete", MARINE_BRICK, log("spruce"), trim="minecraft:light_blue_concrete",
               floor="minecraft:spruce_planks", win=pane("light_blue"), every=4, doors=[("west", 13, 3, 3)], proud=True)
        b.gable_roof(DX0, DZ0, DX1, DZ1, 8, "dark_oak", "minecraft:dark_oak_planks", axis="z")
        for z in range(DZ0 + 2, DZ1 - 1, 3):
            bed("blue", DX1 - 2, 1, z, b, "west") if z < DZ0 + 13 else None
        for z in range(DZ0 + 16, DZ1 - 2, 3):   # training posts: straw dummies with sticks for arms
            b.set(DX0 + 6, 1, z, fence("spruce")); b.set(DX0 + 6, 2, z, "minecraft:hay_block[axis=y]"); b.set(DX0 + 6, 3, z, "minecraft:carved_pumpkin[facing=west]")
        for z in range(DZ0 + 15, DZ1 - 1, 4):
            b.set(DX1 - 1, 1, z, facing("weapon_rack", "west")); b.set(DX1 - 1, 1, z + 1, facing("katana_stand", "west"))
        b.set(DX0 + 10, 1, DZ0 + 1, facing("notice_board", "south")); b.set(DX0 + 12, 1, DZ0 + 1, facing("alarm_bell", "south"))
        for z in range(DZ0 + 4, DZ1 - 3, 6):
            b.set(DX0 + 10, 6, z, HANG)
        b.flag(DX0 - 2, 1, DZ0 + 2, h=11, colors=("minecraft:white_wool", "minecraft:light_blue_wool"), skull=False, length=4)
        # --- Cherry trees, stone lanterns and a koi pond.
        b.disk(36, 0, 84, 5, WATER); b.disk(36, -1, 84, 4, WATER); b.disk(36, -2, 84, 3, "minecraft:gravel")
        for (x, z) in ((6, 6), (16, 30), (36, 6), (60, 6), (88, 30), (90, 8), (10, 86), (24, 92), (64, 86), (80, 90), (92, 84), (30, 32), (66, 32)):
            b.tree(x, 1, z, rnd.randint(5, 7), "cherry", 3)
        for (x, z) in ((32, 38), (64, 38), (24, 40), (72, 40)):
            b.stone_lantern(x, 1, z, "stone_brick", PAPER_LANTERN)
        b.scatter(0, 0, W, D, 1, ["minecraft:pink_petals[facing=north,flower_amount=3]", "minecraft:short_grass", "minecraft:fern"], 0.07, rnd, only_on=grass)

        b.rogue(AX, 1, AZ, "saga")
        b.crew("seven_star_swordsman", ((AX - 9, AZ - 5), (AX + 9, AZ - 5), (AX - 9, AZ + 7), (AX + 9, AZ + 7), (DX0 + 8, 52), (DX0 + 10, 64),
                                        (PX0 + 10, 2, PZ0 + 22)))
        clear_spawns(b)

    # ============================================================ Count Butler: Crown Island
    @lair("crown_island", "Crown Island", "count_butler",
          ["minecraft:jungle", "minecraft:sparse_jungle", "minecraft:bamboo_jungle", "minecraft:savanna"], "land", group="film_lairs")
    def _(b):
        rnd = random.Random(34)
        W, D = 96, 96
        grass = ["minecraft:grass_block"] * 4 + ["minecraft:podzol", "minecraft:coarse_dirt", "minecraft:moss_block"]
        for x in range(W + 1):
            for z in range(D + 1):
                b.set(x, -1, z, "minecraft:dirt")
                b.set(x, 0, z, rnd.choice(grass))
        # --- The golden lion (the landmark): Crown Island's statue of its animal king, sitting on a stone plinth.
        LX, LZ = 48, 20
        b.box(LX - 8, 1, LZ - 9, LX + 8, 4, LZ + 9, "minecraft:stone_bricks")
        b.box(LX - 9, 1, LZ - 10, LX + 9, 1, LZ + 10, "minecraft:polished_andesite")
        b.box(LX - 8, 4, LZ - 9, LX + 8, 4, LZ + 9, "minecraft:chiseled_stone_bricks")
        G, MANE = GOLD_BRICK, "minecraft:honeycomb_block"
        b.sphere(LX, 10, LZ - 2, 5.5, G, ry=5)                       # haunches
        b.sphere(LX, 13, LZ + 1, 4.5, G, ry=6)                       # chest, sitting up
        for dx in (-3, 3):
            b.box(LX + dx - 1, 5, LZ + 4, LX + dx + 1, 12, LZ + 6, G)   # front legs
            b.box(LX + dx - 1, 5, LZ + 7, LX + dx + 1, 6, LZ + 7, G)    # paws
        b.sphere(LX, 20, LZ + 2, 5.5, MANE, ry=6)                    # the mane
        b.sphere(LX, 20, LZ + 5, 4, G)                               # the head, looking out over the fountain
        b.box(LX - 1, 18, LZ + 8, LX + 1, 19, LZ + 10, G)            # muzzle
        b.set(LX - 2, 21, LZ + 9, "minecraft:black_concrete"); b.set(LX + 2, 21, LZ + 9, "minecraft:black_concrete")   # eyes
        b.set(LX, 19, LZ + 11, "minecraft:black_concrete")
        for a in range(0, 360, 45):                                  # its crown
            x, z = round(LX + 3 * math.cos(math.radians(a))), round(LZ + 4 + 3 * math.sin(math.radians(a)))
            b.box(x, 24, z, x, 25 + (a // 45) % 2, z, "minecraft:gold_block")
        b.set(LX, 26, LZ + 4, "minecraft:red_concrete")
        for k in range(8):                                           # its tail curling round the plinth
            b.set(LX + 5 + k // 2, 5, LZ - 7 + k, G)
        b.set(LX + 9, 6, LZ - 2, MANE)
        # --- The crown fountain in front of it, whose jets form a crown when a new king is chosen.
        FX, FZ = 48, 40
        b.cyl(FX, FZ, 7, 0, 1, "minecraft:stone_bricks", hollow=True)
        b.disk(FX, 0, FZ, 6, WATER); b.disk(FX, -1, FZ, 6, "minecraft:prismarine_bricks")
        b.box(FX, 0, FZ, FX, 3, FZ, "minecraft:prismarine_bricks"); b.set(FX, 4, FZ, "minecraft:sea_lantern")
        for a in range(0, 360, 36):   # the jets: frozen in glass, alternately tall and short like a crown's points
            x, z = round(FX + 4 * math.cos(math.radians(a))), round(FZ + 4 * math.sin(math.radians(a)))
            h = 6 if (a // 36) % 2 == 0 else 3
            b.box(x, 0, z, x, 0, z, "minecraft:prismarine_bricks")
            b.box(x, 1, z, x, h, z, "minecraft:light_blue_stained_glass")
            b.set(x, h + 1, z, "minecraft:white_stained_glass")
        # --- The clearing (the arena) round the fountain.
        AX, AZ = 48, 52
        for x in range(26, 71):
            for z in range(31, 66):
                if math.hypot((x - FX) / 1.3, z - (FZ + 8)) < 18 and b.get(x, 0, z) not in (WATER, "minecraft:stone_bricks"):
                    b.set(x, 0, z, rnd.choice(["minecraft:coarse_dirt", "minecraft:grass_block", "minecraft:rooted_dirt", "minecraft:gravel"]))
        for (x, z) in ((32, 40), (64, 40), (32, 62), (64, 62)):
            b.lamp_post(x, 1, z, "jungle", 4, LANTERN)
        for (x, z) in ((36, 58), (60, 46), (40, 66)):   # bones of the animals he has already eaten
            b.set(x, 1, z, "minecraft:bone_block[axis=x]"); b.set(x + 1, 1, z, "minecraft:bone_block[axis=y]")
        # --- Butler's mansion and laboratory (east): two floors of purple wood, cages of specimens, the study with the chest.
        MX0, MZ0, MX1, MZ1 = 66, 60, 92, 88
        b.hall(MX0, MZ0, MX1, MZ1, 0, 6, "minecraft:purple_terracotta", "minecraft:polished_blackstone_bricks", log("dark_oak"),
               trim=GOLD_BRICK, floor="minecraft:dark_oak_planks", win=pane("purple"), every=4, doors=[("west", 6, 3, 3)], proud=True)
        b.hall(MX0, MZ0, MX1, MZ1, 6, 5, "minecraft:purple_terracotta", "minecraft:polished_blackstone_bricks", log("dark_oak"),
               trim=GOLD_BRICK, floor="minecraft:dark_oak_planks", win=pane("purple"), every=4, proud=True)
        b.hip_roof(MX0, MZ0, MX1, MZ1, 12, "dark_oak", "minecraft:dark_oak_planks", ov=1)
        b.box(MX0 + 1, 6, MZ0 + 1, MX1 - 1, 6, MZ1 - 1, "minecraft:dark_oak_planks")
        b.stair_run(MX1 - 2, 1, MZ1 - 8, 6, "dark_oak", "north", "minecraft:dark_oak_planks")
        b.box(MX1 - 2, 6, MZ1 - 12, MX1 - 2, 6, MZ1 - 9, AIR)   # the stairwell
        # ground floor: the laboratory, with specimen cages along the north wall
        for x in range(MX0 + 2, MX0 + 20, 5):
            for y in range(1, 4):
                for xx in range(x, x + 5):
                    b.set(xx, y, MZ0 + 5, BARS_X)
                for zz in range(MZ0 + 1, MZ0 + 5):
                    b.set(x, y, zz, BARS_Z); b.set(x + 4, y, zz, BARS_Z)
            b.box(x + 1, 1, MZ0 + 2, x + 3, 3, MZ0 + 4, AIR)
            b.box(x, 0, MZ0 + 1, x + 4, 0, MZ0 + 5, "minecraft:hay_block[axis=y]")
            b.box(x, 4, MZ0 + 1, x + 4, 4, MZ0 + 5, "minecraft:dark_oak_planks")
        for (x, z) in ((MX0 + 4, MZ0 + 10), (MX0 + 8, MZ0 + 10), (MX0 + 12, MZ0 + 10)):
            b.set(x, 1, z, "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
            b.set(x + 1, 1, z, "minecraft:cauldron")
            b.set(x - 1, 1, z, "onepiece:lab_panel")
        b.table(MX0 + 4, 1, MZ0 + 14, "dark_oak", "minecraft:white_carpet", w=10)
        b.set(MX0 + 10, 1, MZ0 + 16, facing("drafting_table", "north")); b.set(MX0 + 6, 1, MZ0 + 16, facing("book_stack", "north"))
        for x in range(MX0 + 3, MX1 - 3, 5):
            b.set(x, 5, MZ0 + 12, "onepiece:lab_light")
        b.shelf(MX0 + 1, 1, MZ1 - 1, h=3, axis="x", n=8)
        # upstairs: his study (the chest), a bedroom and the trophy wall of horns
        b.chest(MX0 + 2, 7, MZ0 + 2, "crown_island", "south")
        b.set(MX0 + 4, 7, MZ0 + 2, facing("writing_desk", "south")); b.set(MX0 + 4, 7, MZ0 + 3, facing("captains_chair", "north"))
        b.set(MX0 + 7, 7, MZ0 + 2, facing("piano", "south")); b.set(MX0 + 10, 7, MZ0 + 2, facing("globe", "south"))
        b.shelf(MX0 + 1, 7, MZ0 + 6, h=3, axis="z", n=6)
        for x in range(MX0 + 2, MX1 - 1, 3):   # mounted horns
            b.set(x, 9, MZ1 - 1, "minecraft:bone_block[axis=z]"); b.set(x, 10, MZ1 - 1, "minecraft:bone_block[axis=y]")
        bed("purple", MX1 - 4, 7, MZ0 + 3, b, "south")
        b.set(MX1 - 6, 7, MZ0 + 2, facing("wine_rack", "south"))
        b.set(MX0 + 12, 10, MZ0 + 12, facing("chandelier", "north"))
        for z in range(MZ0 + 4, MZ1 - 2):
            b.set(MX0 + 13, 7, z, carpet("purple"))
        b.set(MX0 + 1, 2, MZ0 + 20, facing("wall_wanted_poster", "east"))
        # --- His henchmen's camp (west): tents, a fire, weapon racks and a pen of horned beasts.
        for (tx, tz, col) in ((10, 50, "brown"), (20, 58, "green"), (10, 66, "brown"), (22, 74, "green")):
            tent(b, tx, tz, col, rnd)
        b.set(16, 1, 64, CAMPFIRE)
        for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            b.set(16 + dx, 1, 64 + dz, slab("jungle"))
        for z in (52, 56, 60):
            b.set(4, 1, z, facing("weapon_rack", "east"))
        PX0, PZ0, PX1, PZ1 = 4, 80, 30, 94
        for x in range(PX0, PX1 + 1):
            for z in (PZ0, PZ1):
                b.set(x, 1, z, fence("jungle"))
        for z in range(PZ0, PZ1 + 1):
            for x in (PX0, PX1):
                b.set(x, 1, z, fence("jungle"))
        b.set(PX1, 1, PZ0 + 6, "minecraft:jungle_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
        b.box(PX0 + 2, 1, PZ0 + 2, PX0 + 3, 1, PZ0 + 3, "minecraft:hay_block[axis=y]")
        b.set(PX1 - 3, 1, PZ1 - 3, "minecraft:water_cauldron[level=3]")
        # --- Jungle all round: big trees, bamboo and ferns, and a pond.
        b.disk(80, 0, 26, 5, WATER); b.disk(80, -1, 26, 4, WATER); b.disk(80, -2, 26, 4, "minecraft:clay")
        for (x, z) in ((6, 6), (20, 14), (8, 30), (30, 34), (70, 8), (90, 10), (92, 40), (66, 44), (6, 88), (40, 90), (58, 92), (26, 4)):
            b.tree(x, 1, z, rnd.randint(7, 10), "jungle", 3)
        for (x, z) in ((36, 80), (44, 76), (52, 82), (88, 50)):
            b.palm(x, 1, z, rnd.randint(5, 7))
        for _ in range(40):
            x, z = rnd.randint(0, W), rnd.randint(0, D)
            if b.get(x, 1, z) in (None, AIR) and b.get(x, 0, z) in grass and not (MX0 - 1 <= x <= MX1 + 1 and MZ0 - 1 <= z <= MZ1 + 1):
                for y in range(1, 1 + rnd.randint(3, 7)):
                    if b.get(x, y, z) not in (None, AIR):
                        break
                    b.set(x, y, z, "minecraft:bamboo[age=0,leaves=none,stage=0]")
        for z in range(66, D + 1):
            for x in range(AX - 1, AX + 2):
                b.set(x, 0, z, "minecraft:coarse_dirt" if x == AX else "minecraft:gravel")
        b.scatter(0, 0, W, D, 1, ["minecraft:fern", "minecraft:short_grass", "minecraft:short_grass"],
                  0.08, rnd, only_on=grass)

        b.rogue(AX, 1, AZ, "count_butler")
        b.crew("butler_henchman", ((AX - 8, AZ - 4), (AX + 8, AZ - 4), (AX - 7, AZ + 8), (AX + 7, AZ + 8), (16, 60), (MX0 + 10, 1, MZ0 + 20)))
        b.beast("onepiece:deer", ((MX0 + 4, MZ0 + 3), (MX0 + 9, MZ0 + 3)))
        b.beast("onepiece:long_horse", ((PX0 + 8, PZ0 + 7), (PX0 + 18, PZ0 + 7)))
        clear_spawns(b)


LOOT = {
    "clockwork_island": table((5, 8, [item(BERRY, 10, 16, 40), item("minecraft:clock", 6), item("minecraft:copper_ingot", 8, 4, 16),
                                      item("minecraft:gold_ingot", 8, 2, 8), item("minecraft:diamond", 4, 1, 3), item("minecraft:golden_apple", 5, 1, 2),
                                      item("minecraft:gunpowder", 6, 4, 10), item("minecraft:spyglass", 2), item("minecraft:iron_pickaxe", 2, 1, 1, ENCHANT),
                                      item("minecraft:netherite_scrap", 1)]), rumor("bear_king")),
    "delta_island": table((6, 9, [item(BERRY, 10, 24, 56), item("minecraft:firework_rocket", 10, 8, 24), item("minecraft:firework_star", 4, 2, 6),
                                  item("minecraft:gold_ingot", 6, 4, 12), item("minecraft:diamond", 5, 1, 4), item("minecraft:golden_apple", 5, 1, 3),
                                  item("minecraft:enchanted_golden_apple", 1), item("minecraft:map", 3), item("onepiece:berry_block", 2, 1, 2),
                                  item("minecraft:crossbow", 2, 1, 1, ENCHANT)]), rumor("buena_festa")),
    "asuka_island": table((6, 9, [item(BERRY, 10, 24, 56), item("minecraft:iron_sword", 3, 1, 1, ENCHANT), item("minecraft:diamond_sword", 2, 1, 1, ENCHANT),
                                  item("minecraft:emerald", 6, 2, 8), item("minecraft:diamond", 5, 1, 4), item("minecraft:cherry_sapling", 5, 1, 3),
                                  item("minecraft:golden_apple", 5, 1, 3), item("minecraft:enchanted_golden_apple", 1), item("minecraft:experience_bottle", 6, 2, 8),
                                  item("minecraft:soul_lantern", 4, 1, 4)]),
                          (1, 1, [item("minecraft:enchanted_book", 1, 1, 1, ENCHANT)]), rumor("saga")),
    "crown_island": table((5, 8, [item(BERRY, 10, 16, 40), item("minecraft:goat_horn", 3), item("minecraft:bone", 8, 4, 12), item("minecraft:lead", 5, 1, 3),
                                  item("minecraft:golden_carrot", 6, 2, 6), item("minecraft:gold_ingot", 6, 2, 8), item("minecraft:diamond", 4, 1, 3),
                                  item("minecraft:golden_apple", 5, 1, 2), item("minecraft:glass_bottle", 4, 2, 6), item("minecraft:name_tag", 3)]),
                          rumor("count_butler")),
}
