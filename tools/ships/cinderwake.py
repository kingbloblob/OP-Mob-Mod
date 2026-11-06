"""The Cinderwake: "Ash Corsair" Kael Ashgrave's black war galleon (New World). An ironclad that burns as it sails:
a furnace deck amidships feeds two smokestacks, her seams glow like coals, and her guns fire burning shot.
  hull     polished blackstone with iron-barred gun ports, a glowing ember seam (shroomlight and orange glass) along
           the wale, deepslate tiles under the water
  bow      an iron salamander's head as the figurehead: jaws open on a furnace glow, gold eyes, swept-back horns,
           ember spines down its neck onto the forecastle
  deck     the furnace deck: two smokestacks with fires at the top, blast furnaces, anvils and coal; braziers on the
           rails; three masts with ash-grey sails singed with ember holes, a flaming skull on the main course
  stern    an armoured stern castle with brazier turrets on the corners; Kael's forge-cabin with his strongroom chest,
           the wheel on the poop deck under a blackstone hood
+x is the bow; CZ = 0; the main deck is y 7.
"""
from seakit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 50
X1 = X0 + LEN - 1
BEAM = 13
KEEL, DECK = -3, 7
LOWER = 3
STERN_X1 = 10
CABIN_TOP = DECK + 4
MIZZEN_X, MAIN_X, FORE_X = 13, 27, 38
CUTS = (DECK + 1,)

SIDE = "minecraft:polished_blackstone"
BOTTOM = "minecraft:deepslate_tiles"
DECKW = "minecraft:dark_oak_planks"
SEAM = "minecraft:orange_stained_glass"
GLOW = "minecraft:shroomlight"
TRIM = "minecraft:polished_blackstone_bricks"
RAIL = "minecraft:polished_blackstone_wall[up=true]"
IRON_RAIL = "minecraft:iron_bars"
SAIL = WOOL["gray"]
EMBER = WOOL["orange"]
FLAME = WOOL["yellow"]
BLACK = WOOL["black"]
STACK = "minecraft:deepslate_bricks"
FIRE = "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
SIGNAL = "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]"

# Kael's mark: a black skull wreathed in flame.
MARK_ROWS = [
    "....Y...Y....",
    "...YOY.YOY...",
    "..YOOYYYOOY..",
    "..YOKKKKKOY..",
    ".YOKKKKKKKOY.",
    ".YOKWWKWWKOY.",
    ".OOKWWKWWKOO.",
    "..OKKKWKKKO..",
    "...OKKKKKO...",
    "....KWKWK....",
    ".....OOO.....",
]
FLAG_ROWS = [
    "KKKKKKKKK",
    "KKYKKKYKK",
    "KYOWWWOYK",
    "KOWKWKWOK",
    "KKWWWWWKK",
    "KKKWKWKKK",
    "KKKKKKKKK",
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


def singed(seed, base=None):
    """Burn holes: little ember-orange spots across an ash-grey sail."""
    import random
    rnd = random.Random(seed)
    spots = [(rnd.uniform(-0.85, 0.85), rnd.uniform(-0.8, 0.8)) for _ in range(6)]

    def pattern(u, v):
        if base:
            b = base(u, v)
            if b:
                return b
        for (pu, pv) in spots:
            d = abs(u - pu) + abs(v - pv)
            if d < 0.07:
                return FLAME
            if d < 0.16:
                return EMBER
        return None
    return pattern


def build():
    s = BossShip("cinderwake", "Cinderwake", captain="kael_ashgrave", crew="Ashgrave Corsairs")

    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=SIDE, bottom=BOTTOM, deck=DECKW,
           bow_len=14, stern_len=4, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=1, fullness=0.64, flat=0.42,
           bulwark=1, bulwark_mat=TRIM, rail=RAIL, inner_decks=[(LOWER, "minecraft:dark_oak_planks")])
    inside = s._inside

    def zedge(x):
        return int(round(s.halfwidth(x, s.deck_y(x))))

    # the ember seam along the wale: orange glass with a glowing block every fourth
    for (x, y, z), b in list(s.blocks.items()):
        if b == SIDE and x in s._hull and y == s.deck_y(x) - 1:
            s.set(x, y, z, GLOW if x % 4 == 0 else SEAM)
    for y in range(KEEL + 1, DECK + 1):
        s.set(X0 - 1, y, CZ, BOTTOM if y <= 0 else SIDE)

    # ---- guns: a lower row behind iron-barred ports, and the weather deck
    s.broadside((16, 20, 24, 28, 32, 36), LOWER + 1, CZ, lambda x: s.halfwidth(x, LOWER + 1), gunport=IRON_RAIL)
    s.broadside((18, 31, 35), DECK + 1, CZ, lambda x: zedge(x))

    # ---- the hold: coal, powder and plunder
    s.open_hatch(22, DECK, 2, ladder_facing="west", down_to=KEEL + 1)
    for y in range(KEEL + 1, DECK):
        s.fill_if(23, y, 2, "minecraft:dark_oak_planks")
    s.chest(26, KEEL + 1, 0, "treasure", facing="west")
    s.chest(30, KEEL + 1, -1, "hard", facing="west")
    s.chest(30, KEEL + 1, 1, "pirate", facing="west")
    for (x, z) in ((18, -1), (19, -1), (34, 1), (34, -1)):
        s.set(x, KEEL + 1, z, "minecraft:coal_block")
    s.set(20, LOWER + 1, 0, "minecraft:tnt")
    for x in (18, 26, 34):
        s.lamp(x, DECK - 1, CZ, hanging=True)

    # ---- the furnace deck: two smokestacks, blast furnaces and anvils between them
    for (sx, h) in ((20, 13), (31, 11)):
        for x in (sx, sx + 1):
            for z in (-1, 0):
                for y in range(DECK + 1, DECK + h):
                    s.set(x, y, z, STACK)
                s.set(x, DECK + h, z, FIRE)
        for x in (sx - 1, sx + 2):                                 # iron bands round the stack
            for z in (-1, 0):
                s.set(x, DECK + h - 3, z, "minecraft:iron_bars")
        for z in (-2, 1):
            for x in (sx, sx + 1):
                s.set(x, DECK + h - 3, z, "minecraft:iron_bars")
        s.set(sx + 2, DECK + 1, -1, "minecraft:blast_furnace[facing=east,lit=true]")
        s.set(sx + 2, DECK + 1, 0, "minecraft:blast_furnace[facing=east,lit=true]")
        s.set(sx - 1, DECK + 1, -1, "minecraft:blast_furnace[facing=west,lit=true]")
        s.set(sx - 1, DECK + 1, 0, "minecraft:blast_furnace[facing=west,lit=true]")
    s.set(25, DECK + 1, 2, "minecraft:anvil[facing=east]")
    s.set(25, DECK + 1, -3, "minecraft:anvil[facing=east]")
    s.set(26, DECK + 1, 3, "minecraft:coal_block")
    s.set(26, DECK + 1, -3, "minecraft:smithing_table")
    # braziers on the rails
    for x in (15, 24, 34, 40):
        for side in (-1, 1):
            z = side * zedge(x)
            s.set(x, DECK + 2, z, FIRE)

    # ---- stern castle: armoured, brazier turrets on the corners; the forge-cabin inside
    for x in range(X0, STERN_X1 + 1):
        hw = int(round(s.halfwidth(x, s.deck_y(x))))
        dy = s.deck_y(x)
        for z in range(-hw, hw + 1):
            edge = abs(z) == hw or x in (X0, STERN_X1)
            for y in range(dy + 1, CABIN_TOP):
                s.set(x, y, z, TRIM if edge else AIR)
            s.set(x, CABIN_TOP, z, DECKW if not edge else TRIM)
        s.set(x, CABIN_TOP + 1, -hw, RAIL)
        s.set(x, CABIN_TOP + 1, hw, RAIL)
    for z in range(-int(round(s.halfwidth(X0, s.deck_y(X0)))), int(round(s.halfwidth(X0, s.deck_y(X0)))) + 1):
        s.set(X0, CABIN_TOP + 1, z, RAIL)
    for (x, side) in ((X0, -1), (X0, 1), (STERN_X1, -1), (STERN_X1, 1)):
        hw = int(round(s.halfwidth(x, s.deck_y(x))))
        z = side * hw
        s.set(x, CABIN_TOP + 1, z, TRIM)
        s.set(x, CABIN_TOP + 2, z, TRIM)
        s.set(x, CABIN_TOP + 3, z, SIGNAL)
    for z in (-3, -1, 1, 3):                                          # glowing stern windows
        s.set(X0, DECK + 2, z, pane("orange"))
        s.set(X0, DECK + 3, z, pane("orange"))
    s.set(STERN_X1, DECK + 1, 2, door("minecraft:iron_door", "east", "lower"))
    s.set(STERN_X1, DECK + 2, 2, door("minecraft:iron_door", "east", "upper"))
    s.set(STERN_X1 + 1, DECK + 1, 3, "minecraft:stone_button[face=floor,facing=east,powered=false]")
    I.furnish(s, 1, DECK + 1, -4, STERN_X1 - 1, 4, 3, "captain", "pirate", seed=41)
    s.strongroom(1, DECK + 1, 0, facing="east")
    s.set(1, DECK + 1, -1, "minecraft:blast_furnace[facing=east,lit=true]")
    s.set(1, DECK + 1, 1, "minecraft:anvil[facing=north]")
    s.set(1, DECK + 3, 0, "minecraft:netherite_block")              # his trophy: a slab of netherite on the wall
    s.lamp(5, CABIN_TOP - 1, CZ, hanging=True)
    # stairs up to the poop deck
    s.stairs_run(STERN_X1 + 4, DECK + 1, -4, 4, "minecraft:polished_blackstone_stairs", "west")
    s.set(STERN_X1, CABIN_TOP + 1, -4, AIR)
    # the helm under a blackstone hood
    s.helm(7, CABIN_TOP + 1, CZ)
    for (x, z) in ((5, -2), (5, 2), (9, -2), (9, 2)):
        for y in range(CABIN_TOP + 1, CABIN_TOP + 4):
            s.set(x, y, z, RAIL)
    s.box(5, CABIN_TOP + 4, -2, 9, CABIN_TOP + 4, 2, TRIM)
    s.set(9, CABIN_TOP + 3, CZ, "minecraft:lantern[hanging=true,waterlogged=false]")

    # ---- forecastle
    fx0 = X1 - 8
    for x in range(fx0, X1 + 1):
        dy = s.deck_y(x)
        hw = int(round(s.halfwidth(x, dy)))
        for z in range(-hw, hw + 1):
            for y in range(dy + 1, DECK + 3):
                s.set(x, y, z, TRIM if (abs(z) == hw or x == fx0) else AIR)
            s.set(x, DECK + 3, z, DECKW)
        if hw >= 1:
            s.set(x, DECK + 4, -hw, RAIL)
            s.set(x, DECK + 4, hw, RAIL)
    s.set(fx0, DECK + 1, 0, door("minecraft:iron_door", "west", "lower"))
    s.set(fx0, DECK + 2, 0, door("minecraft:iron_door", "west", "upper"))
    I.furnish(s, fx0 + 1, DECK + 1, -3, X1 - 3, 3, 1, "barracks", "pirate", seed=43)
    s.stairs_run(fx0 - 2, DECK + 1, 3, 2, "minecraft:polished_blackstone_stairs", "east")
    s.anchor(fx0 + 2, DECK + 4, -3, "north")
    s.cannon(fx0 + 5, DECK + 4, CZ, "east")                          # the bow chaser

    # ---- the figurehead: an iron salamander's head, jaws open on a furnace glow
    for y in range(KEEL + 3, DECK + 2):
        s.line((X1, y, CZ), (X1 + 1 + max(0, y) // 3, y, CZ), SIDE if y > 0 else BOTTOM)
    hx = X1 + 3
    hy = DECK + 3
    s.blob(hx, hy + 1, CZ, 2.8, 2.2, 2.3, SIDE, power=2.4, hollow=True)          # skull
    s.blob(hx + 4, hy + 1.5, CZ, 2.6, 1.0, 1.8, SIDE, power=2.8, hollow=True)    # upper jaw
    s.blob(hx + 3.5, hy - 1.2, CZ, 2.4, 0.8, 1.6, SIDE, power=2.8, hollow=True)  # lower jaw
    for x in range(hx + 2, hx + 7):                                               # the open mouth, glowing
        for z in (-1, 0, 1):
            s.set(x, hy, z, AIR)
    for x in range(hx + 1, hx + 4):
        s.set(x, hy - 1, 0, GLOW)
        s.set(x, hy, 0, "minecraft:orange_stained_glass")
    for z in (-2, 2):
        s.set(hx + 2, hy + 2, z, "minecraft:gold_block")                          # eyes
    for x in range(hx + 3, hx + 7, 2):                                            # teeth
        for z in (-1, 1):
            s.set(x, hy + 1, z, "minecraft:end_rod[facing=down]")
    for side in (-1, 1):                                                          # horns
        prev = None
        for i in range(6):
            p = (hx - 1 - i, hy + 3 + min(i, 2), side * (2 + i // 3))
            s.set(*p, TRIM)
            if prev:
                s.set(p[0], prev[1], prev[2], TRIM)
                s.set(p[0], p[1], prev[2], TRIM)
            prev = p
    for i, x in enumerate(range(hx - 2, fx0 + 2, -2)):                            # ember spines down the neck
        y = DECK + 4 if x <= X1 else hy + 2
        s.set(x, y, CZ, GLOW)

    # ---- masts and ash-grey sails
    def mast(x, y0, top):
        for y in range(y0, top + 1):
            s.set(x, y, CZ, log("dark_oak"))
    FORE_TOP, MAIN_TOP, MIZZEN_TOP = DECK + 26, DECK + 31, DECK + 22
    mast(FORE_X, DECK, FORE_TOP)
    s.square_sail(FORE_X + 1, CZ, DECK + 9, DECK + 17, 8, SAIL, belly=1, yard="dark_oak", pattern=singed(11))
    s.square_sail(FORE_X + 1, CZ, DECK + 19, DECK + 23, 5, SAIL, belly=1, yard="dark_oak", pattern=singed(12))
    mast(MAIN_X, DECK, MAIN_TOP)
    mark = bitmap_pattern(compose(19, 11, MARK_ROWS, flip=True), {"Y": FLAME, "O": EMBER, "K": BLACK, "W": WOOL["white"]})
    s.square_sail(MAIN_X + 1, CZ, DECK + 15, DECK + 25, 9, SAIL, belly=1, yard="dark_oak", pattern=singed(13, mark))
    s.square_sail(MAIN_X + 1, CZ, DECK + 27, DECK + 30, 4, SAIL, belly=1, yard="dark_oak", pattern=singed(14))
    mast(MIZZEN_X, CABIN_TOP - 3, MIZZEN_TOP)
    s.square_sail(MIZZEN_X + 1, CZ, DECK + 11, DECK + 18, 6, SAIL, belly=1, yard="dark_oak", pattern=singed(15))
    s.flag(MAIN_X, MAIN_TOP + 1, CZ, (FLAG_ROWS, {"K": BLACK, "Y": FLAME, "O": EMBER, "W": WOOL["white"]}))
    for (mx, top, ry) in ((FORE_X, DECK + 16, DECK + 2), (MAIN_X, DECK + 24, DECK + 2), (MIZZEN_X, DECK + 17, CABIN_TOP + 1)):
        for side in (-1, 1):
            s.rope((mx - 1, top, CZ), (mx - 2, ry, side * zedge(mx - 2)))
    s.rope((MAIN_X, MAIN_TOP, CZ), (FORE_X, FORE_TOP, CZ))
    s.rope((MIZZEN_X, MIZZEN_TOP, CZ), (MAIN_X, MAIN_TOP, CZ))
    s.rope((FORE_X, FORE_TOP - 2, CZ), (X1 - 1, DECK + 5, CZ))

    for p, b in list(s.blocks.items()):
        if b.endswith("_carpet"):
            s.set(p[0], p[1], p[2], AIR)
    return finish(s)
