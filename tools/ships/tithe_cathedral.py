"""The Tithe Cathedral: Cardinal Severo Lume's war galleon (Grand Line). The "Red Tithe" sails a church to sea and
collects a tithe from every ship it meets: a tenth of the cargo, or the ship.
  hull     crimson planks with a gold wale and black-blackstone lower strakes, gun ports in two rows
  stern    a gothic cathedral fills the after third of the ship: blackstone walls with tall red-glass lancet windows,
           buttresses, a steep slate roof with a gold ridge, a rose window and a pointed doorway on its front, two spires
           at the front corners and a bell tower at the back with a real bell. Inside: pews, a red carpet aisle, the
           altar with candles, and behind it the Tithe Vault (the Cardinal's strongroom chest)
  helm     on the pulpit, a raised deck in front of the cathedral doors
  sails    crimson, a gold coin with a black sword cross on the main course; a crimson banner with the same mark
  bow      a hooded penitent saint as the figurehead, robes flowing back, a lantern held out on a chain
+x is the bow; CZ = 0; the main deck is y 7.
"""
from seakit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 48
X1 = X0 + LEN - 1
BEAM = 13
KEEL, DECK = -3, 7
LOWER = 3
NAVE_X0, NAVE_X1 = 1, 16          # the cathedral on the after deck
NAVE_HW = 5                      # its walls stand at z = +-5
NAVE_TOP = DECK + 7              # top of the walls (y 14); the roof rises from there
PULPIT_X0, PULPIT_X1 = 17, 20    # the raised helm deck in front of the doors
PULPIT_Y = DECK + 3
MAIN_X, FORE_X = 28, 39
CUTS = (DECK + 1,)

SIDE = "minecraft:crimson_planks"
BOTTOM = "minecraft:polished_blackstone_bricks"
DECKW = "minecraft:spruce_planks"
GOLD = "minecraft:gold_block"
WALL = "minecraft:polished_blackstone_bricks"
TRIM = "minecraft:chiseled_polished_blackstone"
ROOF = "minecraft:deepslate_tiles"
ROOF_ST = "minecraft:deepslate_tile_stairs"
RAIL = fence("crimson")
SAIL = WOOL["red"]
LANCET = pane("red")
BLACK = WOOL["black"]
YELLOW = WOOL["yellow"]
CANDLE = "minecraft:white_candle[candles=3,lit=true,waterlogged=false]"

# The Red Tithe: a gold coin with a black sword cross.
COIN_ROWS = [
    "....YYYYY....",
    "..YYYYKYYYY..",
    ".YYYYYKYYYYY.",
    ".YYYYYKYYYYY.",
    "YYKKKKKKKKKYY",
    "YYYYYYKYYYYYY",
    "YYYYYYKYYYYYY",
    "YYYYYYKYYYYYY",
    ".YYYYYKYYYYY.",
    ".YYYYKKKYYYY.",
    "..YYYYKYYYY..",
    "....YYYYY....",
]
FLAG_ROWS = [
    "RRRRRRRRR",
    "RRRYYYRRR",
    "RRYYKYYRR",
    "RYKKKKKYR",
    "RRYYKYYRR",
    "RRRYKYRRR",
    "RRRRRRRRR",
]


def compose(w, h, rows, flip=False):
    out = [["."] * w for _ in range(h)]
    rw = max(len(r) for r in rows)
    left = (w - rw) // 2
    top = (h - len(rows)) // 2
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != "." and 0 <= top + j < h and 0 <= left + i < w:
                out[top + j][left + i] = ch
    return ["".join(reversed(r) if flip else r) for r in out]


def build():
    s = BossShip("tithe_cathedral", "The Tithe Cathedral", captain="severo_lume", crew="Red Tithe Order")

    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=SIDE, bottom=BOTTOM, deck=DECKW,
           bow_len=15, stern_len=4, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=0, fullness=0.66, flat=0.45,
           bulwark=1, bulwark_mat=SIDE, rail=RAIL, wale=GOLD, inner_decks=[(LOWER, "minecraft:dark_oak_planks")])
    inside = s._inside

    def zedge(x):
        return s.halfwidth(x, s.deck_y(x))

    # black lower strakes above the waterline, and the rudder
    for (x, y, z), b in list(s.blocks.items()):
        if b == SIDE and y in (1, 2):
            s.set(x, y, z, BOTTOM)
    for y in range(KEEL + 1, DECK + 1):
        s.set(X0 - 1, y, CZ, BOTTOM if y <= 2 else SIDE)

    # ---- guns: a lower row through gold-rimmed ports and the weather deck
    s.broadside((22, 26, 30, 34), LOWER + 1, CZ, lambda x: s.halfwidth(x, LOWER + 1), gunport=CONCRETE["black"])
    s.broadside((24, 32, 36), DECK + 1, CZ, lambda x: zedge(x))

    # ---- the hold and gun deck: the tithes they've collected
    s.open_hatch(24, DECK, -2, ladder_facing="east", down_to=KEEL + 1)
    for y in range(KEEL + 1, DECK):
        s.fill_if(23, y, -2, "minecraft:dark_oak_planks")
    s.chest(28, KEEL + 1, 0, "treasure", facing="west")
    s.chest(32, KEEL + 1, -1, "pirate", facing="west")
    s.chest(32, KEEL + 1, 1, "hard", facing="west")
    for (x, z) in ((26, 2), (35, -2), (36, 2)):
        s.set(x, KEEL + 1, z, "minecraft:barrel[facing=up,open=false]")
    s.set(30, KEEL + 1, 2, GOLD)
    s.set(30, KEEL + 1, -2, "minecraft:raw_gold_block")
    for x in (22, 31, 40):
        s.lamp(x, DECK - 1, CZ, hanging=True)

    # ---- the cathedral
    ROOF_PEAK = NAVE_TOP + NAVE_HW + 1
    for x in range(NAVE_X0, NAVE_X1 + 1):
        for z in range(-NAVE_HW, NAVE_HW + 1):
            edge = abs(z) == NAVE_HW or x in (NAVE_X0, NAVE_X1)
            for y in range(DECK + 1, NAVE_TOP + 1):
                s.set(x, y, z, WALL if edge else AIR)
        # the steep roof: stairs stepping up to a gold ridge, hollow under it
        for k in range(NAVE_HW + 2):
            y = NAVE_TOP + 1 + k
            for side in (-1, 1):
                z = side * (NAVE_HW + 1 - k)
                if k <= NAVE_HW:
                    s.set(x, y, z, stairs(ROOF_ST, "north" if side > 0 else "south"))
        s.set(x, ROOF_PEAK, CZ, GOLD)
    for x in (NAVE_X0, NAVE_X1):                                   # gable ends filled up to the roof
        for k in range(NAVE_HW + 1):
            for z in range(-(NAVE_HW - k), NAVE_HW - k + 1):
                s.set(x, NAVE_TOP + 1 + k, z, WALL)
    # buttresses against the side walls, lancet windows between them
    for x in range(NAVE_X0 + 2, NAVE_X1 - 1, 3):
        for side in (-1, 1):
            for y in range(DECK + 1, NAVE_TOP - 1):
                s.set(x, y, side * (NAVE_HW + 1), TRIM)
            s.set(x, NAVE_TOP - 1, side * (NAVE_HW + 1), stairs("minecraft:polished_blackstone_brick_stairs", "north" if side > 0 else "south"))
    for x in range(NAVE_X0 + 1, NAVE_X1, 3):
        for dx in (0, 1):
            if NAVE_X0 < x + dx < NAVE_X1 and (x + dx - NAVE_X0) % 3 != 1:
                for side in (-1, 1):
                    for y in range(DECK + 3, NAVE_TOP - 1):
                        s.set(x + dx, y, side * NAVE_HW, LANCET)
    # the front (facing the bow): a pointed doorway, the rose window above, two spires
    fx = NAVE_X1
    for y in range(DECK + 1, DECK + 4):
        for z in (-1, 0, 1):
            s.set(fx, y, z, AIR)
    s.set(fx, DECK + 4, 0, AIR)
    s.set(fx, DECK + 4, -1, stairs("minecraft:polished_blackstone_brick_stairs", "north", half="top"))
    s.set(fx, DECK + 4, 1, stairs("minecraft:polished_blackstone_brick_stairs", "south", half="top"))
    rose_y = NAVE_TOP + 1
    glass = {0: "minecraft:yellow_stained_glass", 1: "minecraft:red_stained_glass", 2: "minecraft:purple_stained_glass",
             3: "minecraft:red_stained_glass"}
    for dz in range(-3, 4):
        for dy in range(-3, 4):
            r = (dz * dz + dy * dy) ** 0.5
            if r <= 3.3:
                s.set(fx, rose_y + dy, dz, GOLD if r > 2.7 else glass[int(r)] if r < 3 else GOLD)
    s.set(fx, rose_y, 0, GOLD)
    for side in (-1, 1):                                           # the spires on the front corners
        z = side * NAVE_HW
        for y in range(NAVE_TOP + 1, NAVE_TOP + 6):
            s.set(fx, y, z, WALL)
        s.set(fx, NAVE_TOP + 6, z, TRIM)
        s.set(fx, NAVE_TOP + 7, z, "minecraft:polished_blackstone_wall[up=true]")
        s.set(fx, NAVE_TOP + 8, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        s.set(fx + 1, NAVE_TOP + 5, z, stairs("minecraft:polished_blackstone_brick_stairs", "west"))
    # the bell tower at the back: square, open belfry with a bell, a spire and gold tip
    bx0, bx1 = NAVE_X0, NAVE_X0 + 4
    for x in range(bx0, bx1 + 1):
        for z in range(-2, 3):
            edge = x in (bx0, bx1) or abs(z) == 2
            for y in range(NAVE_TOP + 1, ROOF_PEAK + 5):
                s.set(x, y, z, WALL if edge else AIR)
            s.set(x, ROOF_PEAK + 5, z, WALL)
    for y in range(ROOF_PEAK + 2, ROOF_PEAK + 5):                    # open arches of the belfry
        for x in range(bx0 + 1, bx1):
            s.set(x, y, -2, AIR)
            s.set(x, y, 2, AIR)
        for z in (-1, 0, 1):
            s.set(bx0, y, z, AIR)
            s.set(bx1, y, z, AIR)
    s.set(bx0 + 2, ROOF_PEAK + 4, 0, "minecraft:bell[attachment=ceiling,facing=east,powered=false]")
    for k in range(4):                                             # the spire
        r = 2 - k // 2 if k < 3 else 0
        for x in range(bx0 + 2 - r, bx0 + 3 + r):
            for z in range(-r, r + 1):
                s.set(x, ROOF_PEAK + 6 + k, z, ROOF)
    s.set(bx0 + 2, ROOF_PEAK + 10, 0, GOLD)
    s.set(bx0 + 2, ROOF_PEAK + 11, 0, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the nave inside: pews either side of a red aisle, the altar, the Tithe Vault behind it
    for x in range(NAVE_X0 + 6, NAVE_X1 - 1, 2):
        for z in range(-4, 5):
            if abs(z) >= 2:
                s.set(x, DECK + 1, z, stairs("minecraft:dark_oak_stairs", "east"))
    for x in range(NAVE_X0 + 5, NAVE_X1):
        s.set(x, DECK + 1, 0, "minecraft:red_carpet")
    for z in range(-2, 3):
        s.set(NAVE_X0 + 3, DECK + 1, z, "minecraft:quartz_block")
        s.set(NAVE_X0 + 3, DECK + 2, z, CANDLE if abs(z) == 2 else "minecraft:air")
    s.set(NAVE_X0 + 3, DECK + 2, 0, "minecraft:gold_block")
    s.set(NAVE_X0 + 3, DECK + 3, 0, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    s.strongroom(NAVE_X0 + 1, DECK + 1, 0, facing="east")
    s.set(NAVE_X0 + 1, DECK + 1, -1, GOLD)
    s.set(NAVE_X0 + 1, DECK + 1, 1, GOLD)
    for x in (NAVE_X0 + 4, NAVE_X0 + 9, NAVE_X0 + 13):
        for y in range(NAVE_TOP + 2, ROOF_PEAK):
            s.set(x, y, 0, "minecraft:chain[axis=y]")
        s.lamp(x, NAVE_TOP + 1, 0, hanging=True)
    for x in range(NAVE_X0 + 2, NAVE_X1, 4):
        for side in (-1, 1):
            s.set(x, DECK + 1, side * 4, CANDLE)

    # ---- the pulpit: a raised deck before the doors with the Ship's Wheel, stairs down to the waist
    for x in range(PULPIT_X0, PULPIT_X1 + 1):
        hw = int(round(zedge(x)))
        for z in range(-hw, hw + 1):
            if abs(z) <= 1 and x == PULPIT_X0:
                continue                                           # the way in to the doors
            for y in range(DECK + 1, PULPIT_Y):
                s.set(x, y, z, SIDE if (abs(z) == hw or x == PULPIT_X1) else AIR)
            s.set(x, PULPIT_Y, z, DECKW)
        s.set(x, PULPIT_Y + 1, -hw, RAIL)
        s.set(x, PULPIT_Y + 1, hw, RAIL)
    for z in range(-1, 2):                                         # the doors open under the pulpit's front
        for y in range(DECK + 1, PULPIT_Y):
            s.set(PULPIT_X0, y, z, AIR)
    for z in range(-int(round(zedge(PULPIT_X1))), int(round(zedge(PULPIT_X1))) + 1):
        if abs(z) > 2:
            s.set(PULPIT_X1, PULPIT_Y + 1, z, RAIL)
    for z in (-1, 0, 1):                                           # the passage under the pulpit to the doors
        for y in range(DECK + 1, PULPIT_Y):
            for x in range(PULPIT_X0, PULPIT_X1 + 1):
                s.set(x, y, z, AIR)
    s.helm(PULPIT_X1 - 1, PULPIT_Y + 1, CZ)
    s.stairs_run(PULPIT_X1 + 3, DECK + 1, 4, 3, "minecraft:crimson_stairs", "west")
    s.stairs_run(PULPIT_X1 + 3, DECK + 1, -4, 3, "minecraft:crimson_stairs", "west")
    for side in (-1, 1):
        s.set(PULPIT_X1, PULPIT_Y + 1, side * 4, AIR)
        s.lamp(PULPIT_X1, PULPIT_Y + 2, side * int(round(zedge(PULPIT_X1))))
        s.set(PULPIT_X0, PULPIT_Y + 1, side * 3, "minecraft:polished_blackstone_wall[up=true]")
        s.set(PULPIT_X0, PULPIT_Y + 2, side * 3, CANDLE)

    # ---- the waist and forecastle: braziers of incense, lanterns, a pillory for the tithe-dodgers
    for x in (24, 34, 44):
        for side in (-1, 1):
            s.lamp(x, DECK + 2, side * int(round(zedge(x))))
    for (x, z) in ((27, 3), (37, -3)):
        s.set(x, DECK + 1, z, "minecraft:polished_blackstone_wall[up=true]")
        s.set(x, DECK + 2, z, "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    fx0 = X1 - 8
    for x in range(fx0, X1 + 1):
        dy = s.deck_y(x)
        hw = int(round(s.halfwidth(x, dy)))
        for z in range(-hw, hw + 1):
            for y in range(dy + 1, DECK + 3):
                s.set(x, y, z, SIDE if (abs(z) == hw or x == fx0) else AIR)
            s.set(x, DECK + 3, z, DECKW)
        if hw >= 1:
            s.set(x, DECK + 4, -hw, RAIL)
            s.set(x, DECK + 4, hw, RAIL)
    s.set(fx0, DECK + 1, 0, door("minecraft:crimson_door", "west", "lower"))
    s.set(fx0, DECK + 2, 0, door("minecraft:crimson_door", "west", "upper"))
    I.furnish(s, fx0 + 1, DECK + 1, -3, X1 - 3, 3, 1, "storage", "pirate", seed=31)
    s.stairs_run(fx0 - 2, DECK + 1, 3, 2, "minecraft:crimson_stairs", "east")
    s.anchor(fx0 + 2, DECK + 4, -3, "north")
    s.set(fx0 + 3, DECK + 4, 2, "onepiece:rope_coil[facing=east]")

    # ---- the figurehead: a hooded penitent saint, lantern held out on a chain
    stem = X1 + 1
    for y in range(KEEL + 3, DECK + 2):
        s.line((X1, y, CZ), (X1 + 1 + max(0, y) // 3, y, CZ), SIDE if y > 2 else BOTTOM)
    hx = X1 + 3
    s.blob(hx, DECK + 3, CZ, 1.6, 3.2, 1.6, WOOL["black"], power=2.2)              # robes
    s.blob(hx - 1, DECK + 2, CZ, 2.2, 1.4, 1.3, WOOL["black"], power=2.0)          # robes flowing back
    s.blob(hx + 0.4, DECK + 7, CZ, 1.4, 1.5, 1.4, WOOL["black"], power=2.4)        # the hood
    s.set(hx + 1, DECK + 7, CZ, CONCRETE["light_gray"])                            # the face, in shadow
    s.set(hx + 2, DECK + 7, CZ, CONCRETE["black"])
    s.set(hx + 1, DECK + 6, CZ, CONCRETE["light_gray"])
    for z in (-1, 1):                                                              # hands folded at the chest
        s.set(hx + 2, DECK + 5, z, CONCRETE["light_gray"])
    s.set(hx + 2, DECK + 5, 0, "minecraft:gold_block")                             # a gold censer between them
    s.set(hx + 3, DECK + 5, 0, "minecraft:chain[axis=x]")
    s.set(hx + 4, DECK + 5, 0, "minecraft:chain[axis=x]")
    s.set(hx + 4, DECK + 4, 0, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    for y in range(DECK + 2, DECK + 6):                                            # gold trim down the robe
        s.set(hx + 1, y, CZ, "minecraft:yellow_wool" if y == DECK + 2 else WOOL["red"])

    # ---- masts and sails
    def mast(x, y0, top):
        for y in range(y0, top + 1):
            s.set(x, y, CZ, log("dark_oak"))
    MAIN_TOP, FORE_TOP = DECK + 32, DECK + 27
    mast(MAIN_X, DECK, MAIN_TOP)
    s.square_sail(MAIN_X + 1, CZ, DECK + 10, DECK + 21, 9, SAIL, belly=1, yard="dark_oak",
                  bitmap=(compose(19, 12, COIN_ROWS, flip=True), {"Y": YELLOW, "K": BLACK}))
    s.square_sail(MAIN_X + 1, CZ, DECK + 23, DECK + 27, 5, SAIL, belly=1, yard="dark_oak")
    s.flag(MAIN_X, MAIN_TOP + 1, CZ, (FLAG_ROWS, {"R": WOOL["red"], "Y": YELLOW, "K": BLACK}))
    mast(FORE_X, DECK, FORE_TOP)
    s.square_sail(FORE_X + 1, CZ, DECK + 10, DECK + 18, 8, SAIL, belly=1, yard="dark_oak")
    s.square_sail(FORE_X + 1, CZ, DECK + 20, DECK + 23, 4, SAIL, belly=1, yard="dark_oak")
    for (mx, top) in ((MAIN_X, DECK + 20), (FORE_X, DECK + 17)):
        for side in (-1, 1):
            s.rope((mx - 1, top, CZ), (mx - 2, DECK + 2, side * int(round(zedge(mx - 2)))))
    s.rope((MAIN_X, MAIN_TOP, CZ), (FORE_X, FORE_TOP, CZ))
    s.rope((FORE_X, FORE_TOP - 2, CZ), (X1 - 1, DECK + 5, CZ))
    s.rope((MAIN_X, MAIN_TOP - 3, CZ), (bx0 + 2, ROOF_PEAK + 10, CZ))
    s.tri_sail(CZ, (FORE_X + 2, DECK + 6), (FORE_X + 2, DECK + 21), (X1 - 2, DECK + 6), SAIL)

    for p, b in list(s.blocks.items()):
        if b.endswith("_carpet") and b != "minecraft:red_carpet":
            s.set(p[0], p[1], p[2], AIR)
    return finish(s)
