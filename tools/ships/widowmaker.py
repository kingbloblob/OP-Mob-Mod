"""The Widowmaker: "Harpoon Queen" Maribel Sedge's whaling barque, a Sea King hunter (East Blue and Grand Line).

A long, weathered three-master that hunts Sea Kings for their scales and meat, and wears its kills.
  hull     dark spruce with the old whalers' painted band: a bone-white stripe with black painted gun ports
           (real cannons sit behind every other one), dark oak under the water
  bow      a Sea King's skull lashed over the stem as a figurehead: open jaws full of white fangs, black eye sockets,
           two horns sweeping back, a harpoon gun on the forecastle between its horns
  deck     the ribcage of a Sea King arches over the waist (bone ribs from rail to rail on a bone spine), the brick
           try-works amidships (two cauldrons over the fires, a chimney), racks of harpoons, coiled line, two
           whaleboats hanging on davits on each side
  stern    a two-storey stern castle: Maribel's cabin with a wall of trophies and her strongroom chest, the poop
           deck above with the wheel; stern windows and lanterns
  sails    grey, patched, a red harpoon through a Sea King skull on the main course; a black flag with the same mark
  hold     barrels of rendered oil, salted meat, the crew's loot

+x is the bow; CZ = 0; the main deck is y 6.
"""
from seakit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 48
X1 = X0 + LEN - 1
BEAM = 13
KEEL, DECK = -3, 6
LOWER = 2                       # floor of the lower deck inside the hull
STERN_X1 = 9                    # stern castle x 0..9
CABIN_TOP = DECK + 4            # its roof = the poop deck (y 10)
MIZZEN_X, MAIN_X, FORE_X = 11, 23, 36
CUTS = (DECK + 1,)

SIDE = "minecraft:spruce_planks"
BOTTOM = "minecraft:dark_oak_planks"
DECKW = "minecraft:oak_planks"
BAND = "minecraft:bone_block[axis=x]"
PORT = CONCRETE["black"]
BONE = "minecraft:bone_block[axis=y]"
BONE_X = "minecraft:bone_block[axis=x]"
BONE_Z = "minecraft:bone_block[axis=z]"
RAIL = fence("spruce")
SAIL = WOOL["light_gray"]
PATCH = WOOL["gray"]
RED = WOOL["red"]
WHITE = WOOL["white"]
BLACK = WOOL["black"]
BARREL = "minecraft:barrel[facing=up,open=false]"
FANG = "minecraft:end_rod[facing=down]"
FANG_UP = "minecraft:end_rod[facing=up]"
HARPOON = "minecraft:lightning_rod[facing=east,powered=false,waterlogged=false]"

# The Sedge Whaling Company's mark: a Sea King skull pierced by a red harpoon.
MARK_ROWS = [
    "..............RR",
    ".............RR.",
    "....WWWWWW..RR..",
    "...WWWWWWWWRR...",
    "..WWKKWWKKRRW...",
    "..WWKKWWKRRWW...",
    "..WWWWWWRRWWW...",
    "...WWWWRRWWW....",
    "...WKWKRRWKW....",
    "....W.RR.W......",
    ".....RR.........",
    "....RR..........",
    "...R.R..........",
    "..R..R..........",
]
MARK = (MARK_ROWS, {"W": WHITE, "K": BLACK, "R": RED})
FLAG_ROWS = [
    "BBBBBBBBBB",
    "BBWWWWBBRB",
    "BWKWWKWRBB",
    "BWWWWWRWBB",
    "BBWKWRKBBB",
    "BBBBRBBBBB",
    "BBBRBBBBBB",
    "BBBBBBBBBB",
]


def compose(w, h, rows, flip=False):
    """The mark centred on a plain w x h sail bitmap ('.' = sail colour), so it isn't stretched."""
    out = [["."] * w for _ in range(h)]
    rw = max(len(r) for r in rows)
    left = (w - rw) // 2
    top = (h - len(rows)) // 2
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != "." and 0 <= top + j < h and 0 <= left + i < w:
                out[top + j][left + i] = ch
    return ["".join(reversed(r) if flip else r) for r in out]


def patched(seed):
    """A sail pattern with a few darker patches sewn on (old canvas)."""
    import random
    rnd = random.Random(seed)
    spots = [(rnd.uniform(-0.8, 0.8), rnd.uniform(-0.7, 0.7)) for _ in range(4)]

    def pattern(u, v):
        for (pu, pv) in spots:
            if abs(u - pu) < 0.13 and abs(v - pv) < 0.15:
                return PATCH
        return None
    return pattern


def build():
    s = BossShip("widowmaker", "The Widowmaker", captain="maribel_sedge", crew="Sedge Whaling Company")

    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=SIDE, bottom=BOTTOM, deck=DECKW,
           bow_len=14, stern_len=5, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=1, fullness=0.62, flat=0.4,
           bulwark=1, bulwark_mat=SIDE, rail=RAIL, inner_decks=[(LOWER, "minecraft:spruce_planks")])
    inside = s._inside

    def zedge(x):
        return s.halfwidth(x, s.deck_y(x))

    # ---- the painted band: bone-white courses under the deck edge, black painted ports along it
    for (x, y, z), b in list(s.blocks.items()):
        if b != SIDE or x not in s._hull:
            continue
        dy = s.deck_y(x)
        if y in (dy - 1, dy - 2):
            s.set(x, y, z, PORT if (y == dy - 2 + 1 and x % 3 == 0 and 4 < x < X1 - 6) else BAND)
    # rudder
    for y in range(KEEL + 1, DECK + 1):
        s.set(X0 - 1, y, CZ, BOTTOM if y <= 0 else SIDE)

    # ---- guns behind the painted ports, on the main deck
    gun_xs = (15, 21, 27, 33)
    s.broadside(gun_xs, DECK + 1, CZ, lambda x: zedge(x))

    # ---- the hold and the lower deck: oil barrels, salted meat, loot
    s.open_hatch(19, DECK, -1, ladder_facing="east", down_to=KEEL + 1)
    for y in range(KEEL + 1, DECK):
        s.fill_if(18, y, -1, "minecraft:spruce_planks")
    for x in range(10, 40, 3):
        for z in (-3, 3):
            if inside(x, LOWER + 1, z) and s.get(x, LOWER + 1, z) in (None, AIR):
                s.set(x, LOWER + 1, z, BARREL)
                if x % 4 == 0 and inside(x, LOWER + 2, z):
                    s.set(x, LOWER + 2, z, BARREL)
    for x in range(12, 36, 5):
        for z in (-2, 2):
            if inside(x, KEEL + 1, z) and s.get(x, KEEL + 1, z) in (None, AIR):
                s.set(x, KEEL + 1, z, BARREL)
    s.chest(24, KEEL + 1, 0, "pirate", facing="west")
    s.chest(30, KEEL + 1, 0, "treasure", facing="west")
    s.chest(16, LOWER + 1, 0, "medium", facing="east")
    s.set(26, LOWER + 1, 1, "minecraft:hay_block")          # salted meat in straw
    s.set(26, LOWER + 1, -1, "minecraft:hay_block")
    for x in (14, 24, 34):
        s.lamp(x, DECK - 1, CZ, hanging=True)
        s.lamp(x, LOWER - 1, CZ, hanging=True)

    # ---- stern castle: Maribel's cabin, the poop deck on top
    for x in range(X0, STERN_X1 + 1):
        hw = int(round(s.halfwidth(x, s.deck_y(x))))
        dy = s.deck_y(x)
        for z in range(-hw, hw + 1):
            edge = abs(z) == hw or x == X0 or x == STERN_X1
            for y in range(dy + 1, CABIN_TOP):
                s.set(x, y, z, SIDE if edge else AIR)
            s.set(x, CABIN_TOP, z, DECKW if not edge else SIDE)
        s.set(x, CABIN_TOP + 1, -hw, RAIL)
        s.set(x, CABIN_TOP + 1, hw, RAIL)
    for z in range(-5, 6):
        s.set(X0, CABIN_TOP + 1, z, RAIL)
    # stern windows (two rows of panes in the transom) and the cabin door onto the main deck
    for z in (-3, -1, 1, 3):
        s.set(X0, DECK + 2, z, pane("light_blue"))
        s.set(X0, DECK + 3, z, pane("light_blue"))
    for x in (2, 5, 8):
        for side in (-1, 1):
            s.porthole(x, DECK + 2, side * int(round(s.halfwidth(x, s.deck_y(x)))), "north" if side < 0 else "south")
    s.set(STERN_X1, DECK + 1, 2, door("minecraft:spruce_door", "east", "lower"))
    s.set(STERN_X1, DECK + 2, 2, door("minecraft:spruce_door", "east", "upper"))
    I.furnish(s, 1, DECK + 1, -4, STERN_X1 - 1, 4, 3, "captain", "pirate", seed=21)
    # the trophy wall: Sea King fangs and a skull plaque on the back wall, her strongroom chest under it
    for z in (-4, 4):
        s.set(1, DECK + 3, z, "minecraft:skeleton_skull[rotation=4]")
    for z in range(-2, 3):
        s.set(1, DECK + 3, z, BONE_Z)
    s.set(1, DECK + 2, -2, FANG)
    s.set(1, DECK + 2, 2, FANG)
    s.strongroom(1, DECK + 1, 0, facing="east")
    s.set(1, DECK + 1, -1, "minecraft:gold_block")
    s.set(1, DECK + 1, 1, "minecraft:gold_block")
    s.lamp(5, CABIN_TOP - 1, CZ, hanging=True)
    # stairs from the waist up to the poop deck (port side, along the cabin front)
    s.stairs_run(STERN_X1 + 4, DECK + 1, -4, 4, "minecraft:spruce_stairs", "west")
    s.set(STERN_X1, CABIN_TOP + 1, -4, AIR)
    # the poop deck: wheel, compass binnacle, lanterns, a harpoon rack
    s.helm(6, CABIN_TOP + 1, CZ)
    s.set(8, CABIN_TOP + 1, CZ, "minecraft:lectern[facing=west,has_book=false,powered=false]")
    for x in (X0, STERN_X1):
        hw = int(round(s.halfwidth(x, s.deck_y(x))))
        for side in (-1, 1):
            s.lamp(x, CABIN_TOP + 2, side * hw)
    for z in (-3, -2, 2, 3):
        s.set(1, CABIN_TOP + 1, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ---- the try-works amidships: a brick furnace with two cauldrons over the fires and a chimney
    tx0, tx1 = 28, 32
    for x in range(tx0, tx1 + 1):
        for z in range(-2, 3):
            s.set(x, DECK + 1, z, "minecraft:bricks")
            if x in (tx0, tx1) or abs(z) == 2:
                s.set(x, DECK + 2, z, "minecraft:bricks")
    s.set(29, DECK + 2, -1, "minecraft:water_cauldron[level=3]")
    s.set(29, DECK + 2, 1, "minecraft:water_cauldron[level=3]")
    s.set(31, DECK + 2, -1, "minecraft:water_cauldron[level=3]")
    s.set(31, DECK + 2, 1, "minecraft:water_cauldron[level=3]")
    s.set(30, DECK + 2, 0, "minecraft:bricks")
    for z in (-1, 1):
        s.set(tx1, DECK + 1, z, "minecraft:furnace[facing=east,lit=true]")
    for y in range(DECK + 3, DECK + 7):
        s.set(tx0, y, 0, "minecraft:bricks")
    s.set(tx0, DECK + 7, 0, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")

    # ---- the Sea King's ribcage over the waist: bone ribs from rail to rail on a bone spine
    RIB_TOP = DECK + 9
    rib_xs = (13, 16, 19, 26)
    for rx in rib_xs:
        hw = zedge(rx)
        def rib_y(z):
            t = abs(z) / max(1, hw)
            return int(round(RIB_TOP - (RIB_TOP - DECK - 2) * t ** 2.2))
        for z in range(-hw, hw + 1):
            y = rib_y(z)
            inner = rib_y(z - 1 if z > 0 else z + 1) if z != 0 else y
            s.set(rx, y, z, BONE_Z if abs(z) < hw - 1 else BONE)
            for yy in range(y + 1, inner + 1):                  # no gaps where the curve steps down
                s.set(rx, yy, z, BONE)
            if abs(z) >= hw - 1:
                for yy in range(DECK + 2, y):
                    s.set(rx, yy, z, BONE)
        # the tips curl in a little at the rail, like a real rib
        s.set(rx, DECK + 2, hw, BONE)
        s.set(rx, DECK + 2, -hw, BONE)
    for x in range(rib_xs[0], rib_xs[-1] + 1):
        if x not in (MAIN_X,):
            s.set(x, RIB_TOP + 1, CZ, BONE_X)
    s.set(rib_xs[0] - 1, RIB_TOP + 1, CZ, "minecraft:bone_block[axis=x]")
    s.set(rib_xs[-1] + 1, RIB_TOP, CZ, "minecraft:bone_block[axis=x]")

    # ---- whaleboats hanging on davits, two a side
    for bx in (14, 22):
        for side in (-1, 1):
            hw = zedge(bx + 2)
            bz = side * (hw + 2)
            by = DECK + 2
            for x in range(bx, bx + 6):
                end = x in (bx, bx + 5)
                for dz in (-1, 0, 1):
                    if end and dz != 0:
                        continue
                    s.set(x, by, bz + dz, "minecraft:oak_planks")
                    if not end and dz != 0:
                        s.set(x, by + 1, bz + dz, "minecraft:oak_slab[type=bottom,waterlogged=false]")
            s.set(bx + 2, by + 1, bz, "minecraft:oak_slab[type=bottom,waterlogged=false]")
            # davits: posts on the rail, arms out over the boat, lines down
            for dx in (1, 4):
                x = bx + dx
                hwx = zedge(x)
                for y in range(DECK + 2, DECK + 5):
                    s.set(x, y, side * hwx, RAIL)
                for z in range(hwx, hw + 3):
                    s.set(x, DECK + 5, side * z, "minecraft:spruce_planks")
                s.set(x, DECK + 4, bz, "minecraft:chain[axis=y]")
                s.set(x, DECK + 3, bz, "minecraft:chain[axis=y]")

    # ---- deck gear: harpoon racks, coiled line, lanterns
    for x in (24, 25):
        for side in (-1, 1):
            hw = zedge(x)
            s.set(x, DECK + 1, side * (hw - 1), "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    for (x, z) in ((20, -3), (34, 3), (12, 3)):
        s.set(x, DECK + 1, z, "onepiece:rope_coil[facing=north]")
    for x in (12, 20, 27, 34, 40):
        for side in (-1, 1):
            s.lamp(x, DECK + 2, side * zedge(x))
    s.set(35, DECK + 1, -3, BARREL)
    s.set(35, DECK + 1, -2, BARREL)

    # ---- forecastle: a raised deck at the bow with the harpoon gun
    fx0 = 39
    for x in range(fx0, X1 + 1):
        dy = s.deck_y(x)
        hw = int(round(s.halfwidth(x, dy)))
        for z in range(-hw, hw + 1):
            for y in range(dy + 1, DECK + 3):
                edge = abs(z) == hw or x == fx0
                s.set(x, y, z, SIDE if edge else AIR)
            s.set(x, DECK + 3, z, DECKW)
        if hw >= 1:
            s.set(x, DECK + 4, -hw, RAIL)
            s.set(x, DECK + 4, hw, RAIL)
    for z in range(-3, 4):
        if z not in (-1, 0, 1):
            s.set(fx0, DECK + 4, z, RAIL)
    s.set(fx0, DECK + 1, 0, door("minecraft:spruce_door", "west", "lower"))
    s.set(fx0, DECK + 2, 0, door("minecraft:spruce_door", "west", "upper"))
    I.furnish(s, fx0 + 1, DECK + 1, -3, X1 - 3, 3, 1, "barracks", "pirate", seed=7)
    s.stairs_run(fx0 - 3, DECK + 1, 3, 2, "minecraft:spruce_stairs", "east")
    s.set(fx0 - 1, DECK + 3, 3, "minecraft:spruce_planks")
    s.set(fx0 - 1, DECK + 2, 3, "minecraft:spruce_planks")
    # the harpoon gun: a cannon on a swivel, a barbed harpoon loaded in its mouth, line coiled beside it
    s.cannon(X1 - 4, DECK + 4, CZ, "east")
    s.set(X1 - 3, DECK + 4, CZ, HARPOON)
    s.set(X1 - 4, DECK + 4, 1, "onepiece:rope_coil[facing=east]")
    s.anchor(X1 - 5, DECK + 4, -2, "north")
    s.lamp(fx0 + 1, DECK + 4, -3)
    s.lamp(fx0 + 1, DECK + 4, 3)

    # ---- the figurehead: a Sea King skull lashed over the stem
    sx = X1 + 1
    sy = DECK + 1
    for y in range(KEEL + 3, sy + 1):                      # the stem rakes forward under the skull
        s.line((X1, y, CZ), (X1 + 1 + max(0, y) // 3, y, CZ), SIDE if y > 0 else BOTTOM)
    s.blob(sx + 3, sy + 4, CZ, 3.5, 2.6, 3.0, BONE, power=2.4, hollow=True)                # the cranium
    s.blob(sx + 7, sy + 3.5, CZ, 3.0, 1.2, 2.2, BONE, power=2.6, hollow=True)  # upper jaw (snout)
    s.blob(sx + 6, sy + 0.5, CZ, 3.0, 0.9, 2.0, BONE, power=2.6, hollow=True)  # lower jaw, hanging open
    for x in range(sx + 4, sx + 10):                                          # the open mouth between them
        for z in (-1, 0, 1):
            s.set(x, sy + 2, z, AIR)
    for x in range(sx + 5, sx + 9, 2):                                        # fangs, down from the snout, up from the jaw
        for z in (-2, 2):
            s.set(x, sy + 2, z, FANG)
        s.set(x - 1, sy + 1, 0, FANG_UP)
    for z in (-2, 2):                                                         # deep black eye sockets
        s.set(sx + 5, sy + 5, z, CONCRETE["black"])
        s.set(sx + 5, sy + 5, z + (1 if z > 0 else -1), CONCRETE["black"])
    for side in (-1, 1):                                                      # horns sweeping back over the bow
        prev = None
        for i in range(7):
            p = (sx + 3 - i, sy + 7 + min(i, 3) - max(0, i - 4), side * (2 + i // 2))
            s.set(*p, BONE)
            if prev:                                                          # keep the horn joined face to face
                s.set(p[0], prev[1], prev[2], BONE)
                s.set(p[0], p[1], prev[2], BONE)
            prev = p
    s.set(sx + 3, sy + 1, CZ, "minecraft:chain[axis=y]")                      # lashings
    s.set(sx + 1, sy + 4, CZ, BONE_X)

    # ---- masts, sails, rigging, the flag
    def mast(x, y0, top):
        for y in range(y0, top + 1):
            s.set(x, y, CZ, log("spruce"))
    FORE_TOP, MAIN_TOP, MIZZEN_TOP = DECK + 27, DECK + 31, DECK + 22
    mast(FORE_X, DECK, FORE_TOP)
    s.square_sail(FORE_X + 1, CZ, DECK + 9, DECK + 17, 8, SAIL, belly=1, yard="spruce", pattern=patched(3))
    s.square_sail(FORE_X + 1, CZ, DECK + 20, DECK + 24, 5, SAIL, belly=1, yard="spruce", pattern=patched(4))
    mast(MAIN_X, DECK, MAIN_TOP)
    s.square_sail(MAIN_X + 1, CZ, DECK + 12, DECK + 21, 10, SAIL, belly=1, yard="spruce",
                  bitmap=(compose(21, 10, MARK_ROWS, flip=True), {"W": WHITE, "K": BLACK, "R": RED}))
    s.square_sail(MAIN_X + 1, CZ, DECK + 24, DECK + 28, 6, SAIL, belly=1, yard="spruce", pattern=patched(5))
    s.crows_nest(MAIN_X, DECK + 29, CZ, 1.5, "spruce")
    mast(MIZZEN_X, CABIN_TOP - 3, MIZZEN_TOP)
    s.square_sail(MIZZEN_X + 1, CZ, DECK + 11, DECK + 18, 6, SAIL, belly=1, yard="spruce", pattern=patched(6))
    s.flag(MAIN_X, MAIN_TOP + 1, CZ, (FLAG_ROWS, {"W": WHITE, "K": BLACK, "R": RED, "B": BLACK}))
    for (mx, top, ry) in ((FORE_X, DECK + 16, DECK + 2), (MAIN_X, DECK + 20, DECK + 2), (MIZZEN_X, DECK + 17, CABIN_TOP + 1)):
        for side in (-1, 1):
            s.rope((mx - 1, top, CZ), (mx - 2, ry, side * (zedge(mx - 2) - 0)))
    s.rope((MAIN_X, MAIN_TOP, CZ), (FORE_X, FORE_TOP, CZ))
    s.rope((MIZZEN_X, MIZZEN_TOP, CZ), (MAIN_X, MAIN_TOP, CZ))
    s.rope((FORE_X, FORE_TOP - 2, CZ), (X1 - 1, DECK + 5, CZ))                # the forestay down to the bow
    s.tri_sail(CZ, (FORE_X + 2, DECK + 6), (FORE_X + 2, DECK + 22), (X1 - 2, DECK + 6), SAIL)
    for p, b in list(s.blocks.items()):                      # rugs cost blocks the budget needs
        if b.endswith("_carpet"):
            s.set(p[0], p[1], p[2], AIR)
    return finish(s)
