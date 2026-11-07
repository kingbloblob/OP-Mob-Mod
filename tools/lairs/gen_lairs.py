#!/usr/bin/env python3
"""Builds each rogue's lair: the structure (.nbt), how and where it generates, and its chest loot.

    python3 tools/lairs/gen_lairs.py .
    python3 tools/lairs/gen_lairs.py . gold_island groseade      (only rebuild these lairs, leave the rest as they are)

Writes into src/main/resources/data/opbosses/: structure/, worldgen/structure, worldgen/template_pool,
worldgen/structure_set, tags/worldgen/biome/has_structure and loot_table/chests. Change a lair here and run it
again; it rewrites all of those folders. Builds with the One Piece Mod's building kit (kit.py), so they work the
same way as its lairs: the boss and its crew appear when the chunk is first made, and only then.
Coordinates: x east, y up, z south; y = 0 is the ground. A "sea" lair sets waterline, the level that sits at the sea's surface;
its blocks below y = 0 reach down toward the sea floor.
"""
import json
import math
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *   # noqa: E402,F401  (B, AIR, FENCE, LANTERN, HANG, ... and NEW_CHAR_TAG, GUARD_TAG)
from parts import *  # noqa: E402,F401  (Parts: stair roofs, halls, furniture; stair(), slab(), fence() ...)
from nbt import Byte  # noqa: E402

KIT_TAG_PREFIX = "onepiece_kit_"   # the main mod's GuardKit.KIT_TAG_PREFIX


import detail  # noqa: E402


class Lair(Parts):
    """The main mod's canvas, plus this mod's boss, crews and chests."""

    def rogue(self, x, y, z, boss_id):
        # The main mod sets up any of its boss mobs carrying this tag when the chunk loads; rogues are those mobs too.
        self.entities.append(("opbosses:rogue_boss", x, y, z,
                              {"Character": boss_id, "Boss": Byte(1), "PersistenceRequired": Byte(1), "Tags": [NEW_CHAR_TAG]}))

    def crew(self, kit, spots, y=1):
        # The main mod turns a pirate NPC with these tags into a guard from that kit (our kits are in its list).
        # A spot is (x, z) at height y, or (x, y, z).
        for spot in spots:
            x, yy, z = spot if len(spot) == 3 else (spot[0], y, spot[1])
            self.entities.append(("onepiece:sea_pirate", x, yy, z,
                                  {"PersistenceRequired": Byte(1), "Tags": [GUARD_TAG, KIT_TAG_PREFIX + kit]}))

    def beast(self, entity_id, spots, y=1):
        # A creature (Shiki's mutated beasts) that stays put: it never despawns.
        for spot in spots:
            x, yy, z = spot if len(spot) == 3 else (spot[0], y, spot[1])
            self.entities.append((entity_id, x, yy, z, {"PersistenceRequired": Byte(1)}))

    boss = None   # the lair's boss id, set before it's built

    def chest(self, x, y, z, loot, facing="south"):
        # The lair's own chest (tools/gen_chests.py), locked with vanilla's container lock: it only opens for
        # someone holding the key the boss drops.
        self.set(x, y, z, f"opbosses:{loot}_chest[facing={facing}]",
                 {"id": "opbosses:lair_chest", "LootTable": f"opbosses:chests/{loot}", "lock": {"items": f"opbosses:key_{self.boss}"}})

    def tree(self, x, y, z, h=6, kind="oak", r=2.5):
        detail.oak(self, x, y, z, h + 1, random.Random(x * 73 + z * 19), kind, r + 0.8)

    def palm(self, x, y, z, h=6):
        detail.palm(self, x, y, z, h + 2, random.Random(x * 73 + z * 19))

    def tower(self, cx, cz, r, h, wall, roof=None, y=0, windows=True, ladder_side=True, floors=None):
        super().tower(cx, cz, r, h, wall, None, y, windows, ladder_side, floors)
        if roof:
            detail.stair_cone(self, cx, cz, r, y + h + 1, *detail.cone_family(roof))

    def tower_cap(self, cx, cz, r, h, roof, y=0):
        pass   # the stair cone needs no filling under its tip

    def scatter(self, x0, z0, x1, z1, y, blocks, chance, rnd, only_on=None, replace=False):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if rnd.random() < chance and (replace or self.get(x, y, z) in (None, AIR)) and (only_on is None or self.get(x, y - 1, z) in only_on):
                    self.set(x, y, z, rnd.choice(blocks))

    def support(self, x0, z0, x1, z1, y, blocks, rnd, down_to=0):
        """Fills the empty space under every block at level y down to the ground, so nothing floats."""
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if self.get(x, y, z) in (None, AIR):
                    continue
                yy = y - 1
                while yy >= down_to and self.get(x, yy, z) in (None, AIR):
                    self.set(x, yy, z, rnd.choice(blocks))
                    yy -= 1

    def skirt(self, cx, cz, r, y0, y1, blocks, rnd, spread=0.35, sz=1.0):
        """A pile under a sea lair from y1 down to y0, widening as it goes down, so it reaches the sea floor."""
        for y in range(y1, y0 - 1, -1):
            rr = r + (y1 - y) * spread
            for x in range(int(cx - rr) - 2, int(cx + rr) + 3):
                for z in range(int(cz - rr) - 2, int(cz + rr) + 3):
                    d = math.hypot(x - cx, (z - cz) * sz) + rnd.random() * 1.6
                    if rr - 3 < d <= rr or (y == y1 and d <= rr):   # a shell: nobody sees the inside
                        self.set(x, y, z, rnd.choice(blocks))


LAIRS = []

CLEAR_TOP = 24


def clear_ground(b):
    """Saves air in every empty spot over a land lair's ground (y 1 up to CLEAR_TOP, over its whole footprint), so the
    land under it can't poke up through the yard: a dune burying a crewman, a hill swallowing a chimney, a mountain
    face against the wall. LairSites (Java) already keeps lairs on fairly flat ground; this cuts away the rest."""
    xs = [p[0] for p in b.blocks]; zs = [p[2] for p in b.blocks]; ys = [p[1] for p in b.blocks]
    top = min(max(ys), CLEAR_TOP)
    # Near the faded edge a hill is cut back in a slope, 2 blocks up for each block in, not straight down.
    natural = getattr(b, "natural", set())
    reach = {c: 0 for c in natural}
    ring = list(natural)
    for d in range(1, top // 2 + 1):
        nxt = []
        for (x, z) in ring:
            for c in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if c not in reach:
                    reach[c] = d
                    nxt.append(c)
        ring = nxt
    for x in range(min(xs), max(xs) + 1):
        for z in range(min(zs), max(zs) + 1):
            if (x, z) in natural:   # past the lair's faded edge: the land stays as it is
                continue
            for y in range(1, min(top, reach.get((x, z), top) * 2) + 1):
                if b.get(x, y, z) is None:
                    b.set(x, y, z, AIR)


def soften_ground(b):
    """Every land lair: drifted ground, flowers in clumps, and an edge that fades into the land instead of a square."""
    xs = [p[0] for p in b.blocks]; zs = [p[2] for p in b.blocks]
    W, D = max(xs), max(zs)
    rnd = random.Random(W * 31 + D)
    detail.ground_patches(b, W, D, rnd)
    detail.flower_drifts(b, W, D, rnd)
    if not hasattr(b, "natural"):
        detail.fade_edges(b, W, D, seed=7)
    b.adaptation = "beard_thin"   # beard_box banks the land up square all round the lair


def lair(name, title, boss, biomes, place, group="rogue_lairs"):
    def deco(fn):
        LAIRS.append(dict(name=name, title=title, boss=boss, biomes=biomes, place=place, build=fn, group=group))
        return fn
    return deco


WALL = "minecraft:{}_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]"
STAIRS = "minecraft:{}_stairs[facing={},half=bottom,shape=straight,waterlogged=false]"
SLAB = "minecraft:{}_slab[type=bottom,waterlogged=false]"
COBWEB = "minecraft:cobweb"
OCEANS = ["minecraft:ocean", "minecraft:lukewarm_ocean", "minecraft:warm_ocean", "minecraft:cold_ocean", "onepiece:east_blue"]
DEEP = ["minecraft:deep_ocean", "minecraft:deep_lukewarm_ocean", "minecraft:deep_cold_ocean", "onepiece:fishman_reef"]


# Each lair is a compound, not one building (ryan: "bigger, almost like a lair, more detail"): about 60 blocks across,
# an approach, the boss's arena at the heart of it, the boss's own quarters with the chest, crew quarters, props
# everywhere, three or more levels, and one landmark you can see from far off.

# ============================================================ Saltjaw Rourke: the Scrapheap Reef
@lair("scrapheap_reef", "The Scrapheap Reef", "saltjaw_rourke", ["#minecraft:is_beach"] + OCEANS, "sea")
def _(b):
    rnd = random.Random(1)
    scrap = ["minecraft:iron_block", "minecraft:oxidized_copper", "minecraft:weathered_cut_copper", "minecraft:dark_oak_planks",
             "minecraft:stripped_spruce_log[axis=x]", "minecraft:exposed_copper", "minecraft:spruce_planks", "minecraft:rooted_dirt",
             "minecraft:mossy_cobblestone", "minecraft:coarse_dirt"]
    top = ["minecraft:coarse_dirt", "minecraft:gravel", "minecraft:rooted_dirt", "minecraft:spruce_planks", "minecraft:oxidized_copper",
           "minecraft:packed_mud", "minecraft:coarse_dirt"]
    rubble = ["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:oxidized_copper", "minecraft:dark_oak_planks", "minecraft:iron_block"]
    CX, CZ = 32, 30
    # The island: a heap of scrap 60 x 52, 2 blocks above the sea, going down to the sea floor underneath.
    for y in range(0, 5):
        r = 28 - y * 0.9
        for x in range(CX - 30, CX + 31):
            for z in range(CZ - 28, CZ + 29):
                d = math.hypot(x - CX, (z - CZ) * 1.12) + rnd.random() * 1.8
                if d <= r:
                    b.set(x, y, z, rnd.choice(top if y == 4 else scrap))
    b.skirt(CX, CZ, 28, -14, -1, rubble, rnd, sz=1.12)
    # Plank paths across the heap.
    for x in range(CX - 22, CX + 23):
        for dz in (-1, 0, 1):
            if b.get(x, 4, CZ + 9 + dz):
                b.set(x, 4, CZ + 9 + dz, "minecraft:spruce_planks" if rnd.random() < 0.8 else "minecraft:dark_oak_planks")
    for z in range(CZ - 4, CZ + 30):
        for dx in (-1, 0, 1):
            if b.get(CX + dx, 4, z):
                b.set(CX + dx, 4, z, "minecraft:spruce_planks" if rnd.random() < 0.8 else "minecraft:dark_oak_planks")

    # --- The Wreck Pit (the arena): sunk one block, walled with stacked hull planks and iron, chains overhead.
    PX, PZ = CX, CZ + 9
    b.cyl(PX, PZ, 10, 4, 7, AIR)
    for x in range(PX - 10, PX + 11):
        for z in range(PZ - 10, PZ + 11):
            d = math.hypot(x - PX, z - PZ)
            if d <= 10.3:
                b.set(x, 3, z, "minecraft:stripped_dark_oak_wood[axis=y]" if (x + z) % 2 else "minecraft:spruce_planks")
    b.disk(PX, 3, PZ, 2.4, "minecraft:polished_blackstone")
    b.set(PX, 3, PZ, "minecraft:iron_block")
    for i in range(0, 360, 6):
        a = math.radians(i)
        x, z = round(PX + 11 * math.cos(a)), round(PZ + 11 * math.sin(a))
        if 80 <= i <= 100 or 260 <= i <= 280:   # gaps north and south
            continue
        b.box(x, 3, z, x, 5, z, rnd.choice(["minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:iron_block", "minecraft:oxidized_copper"]))
        if rnd.random() < 0.4:
            b.set(x, 6, z, rnd.choice(["minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]", fence("spruce")]))
    for (x, z) in ((PX, PZ - 11), (PX, PZ + 11), (PX - 1, PZ - 11), (PX + 1, PZ - 11), (PX - 1, PZ + 11), (PX + 1, PZ + 11)):
        b.set(x, 3, z, "minecraft:spruce_planks"); b.box(x, 4, z, x, 6, z, AIR)
    # Masts stuck upright around the pit with lanterns on chains strung between them.
    masts = [(PX - 9, PZ - 9), (PX + 9, PZ - 9), (PX - 9, PZ + 9), (PX + 9, PZ + 9)]
    for (x, z) in masts:
        b.box(x, 4, z, x, 14, z, log("spruce"))
        b.set(x, 15, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
        b.box(x - 1, 12, z, x + 1, 12, z, log("spruce", "x"))
    for (ax, az), (bx, bz) in ((masts[0], masts[1]), (masts[2], masts[3])):
        for x in range(ax + 1, bx):
            b.set(x, 13, az, CHAIN_X)
        b.hanging(PX - 4, 12, az, 2); b.hanging(PX + 4, 12, az, 2)
    for (ax, az), (bx, bz) in ((masts[0], masts[2]), (masts[1], masts[3])):
        for z in range(az + 1, bz):
            b.set(ax, 13, z, CHAIN_Z)
        b.hanging(ax, 12, PZ, 2)

    # --- Rourke's Hull (his quarters): a galleon dragged ashore and turned upside down into a hall.
    HX0, HX1, HZ = CX - 18, CX + 18, CZ - 14   # runs along x, centred on z = HZ
    for x in range(HX0, HX1 + 1):
        f = (x - HX0) / (HX1 - HX0)
        taper = 1.0 - max(0.0, (f - 0.8) / 0.2) ** 1.4 * 0.75
        hw = 7.5 * taper; hh = 11 * taper
        for z in range(HZ - 9, HZ + 10):
            dz = (z - HZ) / hw if hw else 9
            if abs(dz) > 1:
                continue
            roof = 4 + hh * math.sqrt(max(0.0, 1 - dz * dz))
            for y in range(4, int(roof) + 1):
                inner = 4 + (hh - 1.3) * math.sqrt(max(0.0, 1 - (abs(z - HZ) / max(hw - 1.3, 0.5)) ** 2)) if abs(z - HZ) < hw - 1.3 else 0
                if y > inner or x in (HX0, HX1):
                    plank = "minecraft:dark_oak_planks" if (y + x // 3) % 5 else "minecraft:spruce_planks"
                    if x % 5 == 0:
                        plank = "minecraft:stripped_spruce_log[axis=y]"   # ribs show through the planking
                    b.set(x, y, z, plank)
                else:
                    b.set(x, y, z, AIR)
            b.set(x, 4, z, "minecraft:spruce_planks")
        b.set(x, int(4 + hh) + 1, HZ, "minecraft:stripped_dark_oak_log[axis=x]")   # the keel, now the ridge
    b.box(HX1 + 1, 6, HZ, HX1 + 6, 6, HZ, "minecraft:stripped_dark_oak_log[axis=x]")   # bowsprit sticking out
    b.set(HX1 + 6, 7, HZ, fence("dark_oak"))
    # A gun-port row along the south side, a big door onto the pit, lanterns on the door frame.
    for x in range(HX0 + 3, HX1 - 2, 4):
        b.box(x, 7, HZ + 6, x, 7, HZ + 7, AIR); b.set(x, 7, HZ + 7, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.box(CX - 2, 5, HZ + 5, CX + 2, 9, HZ + 9, AIR)
    b.box(CX - 3, 5, HZ + 7, CX - 3, 9, HZ + 7, log("spruce")); b.box(CX + 3, 5, HZ + 7, CX + 3, 9, HZ + 7, log("spruce"))
    b.box(CX - 3, 10, HZ + 7, CX + 3, 10, HZ + 7, log("spruce", "x"))
    b.set(CX - 3, 9, HZ + 8, HANG); b.set(CX + 3, 9, HZ + 8, HANG)
    for x in range(HX0 + 2, HX1 - 1, 4):
        b.set(x, 13, HZ, CHAIN); b.set(x, 12, HZ, HANG)
    # Inside: his trophy hall (long table, barrels of grog), a map table and his cabin at the bow end.
    b.table(CX - 10, 5, HZ, "spruce", "minecraft:brown_carpet", w=14)
    for x in range(CX - 10, CX + 4, 2):
        b.chair(x, 5, HZ - 1, "spruce", "south"); b.chair(x, 5, HZ + 1, "spruce", "north")
    b.set(CX - 12, 5, HZ, stair("spruce", "east"))   # the captain's seat at the head
    for x in range(HX0 + 2, HX0 + 8):
        b.set(x, 5, HZ - 5, BARREL); b.set(x, 6, HZ - 5, BARREL) if x % 2 else None
    b.set(HX0 + 3, 5, HZ + 4, "minecraft:cartography_table"); b.set(HX0 + 4, 5, HZ + 4, "minecraft:lectern[facing=north,has_book=false,powered=false]")
    b.bones(HX0 + 9, 5, HZ - 5, 8, "x", 3)
    # the cabin: a plank wall across the bow end with a door
    cab = HX1 - 8
    for z in range(HZ - 7, HZ + 8):
        for y in range(5, 15):
            if b.get(cab, y, z) == AIR:
                b.set(cab, y, z, "minecraft:spruce_planks")
    b.box(cab, 5, HZ, cab, 6, HZ, AIR)
    bed("brown", cab + 3, 5, HZ - 3, b, "east")
    b.chest(cab + 5, 5, HZ + 1, "scrapheap_reef", "west")
    b.set(cab + 2, 5, HZ + 3, "minecraft:anvil[facing=north]")
    b.table(cab + 3, 5, HZ + 2, "dark_oak", "minecraft:spruce_pressure_plate[powered=false]")
    b.hang_from(cab + 4, 8, HZ)
    b.set(cab + 1, 5, HZ - 4, BARREL); b.set(cab + 1, 5, HZ + 4, "minecraft:blast_furnace[facing=east,lit=false]")

    # --- The salvage crane (the landmark): a lattice tower 28 high with an anchor swinging from its jib.
    TX, TZ = CX + 22, CZ + 2
    for (x, z) in ((TX - 1, TZ - 1), (TX + 1, TZ - 1), (TX - 1, TZ + 1), (TX + 1, TZ + 1)):
        b.box(x, 4, z, x, 28, z, log("spruce"))
        b.support(x, z, x, z, 4, [log("spruce")], rnd, down_to=-14)
    for y in range(6, 28, 4):
        b.box(TX - 1, y, TZ, TX + 1, y, TZ, log("spruce", "x")); b.box(TX, y, TZ - 1, TX, y, TZ + 1, log("spruce", "z"))
    for y in range(5, 28):
        b.set(TX, y, TZ, ladder("north")) if b.get(TX, y, TZ) in (None, AIR) else None
    b.box(TX - 2, 28, TZ - 2, TX + 2, 28, TZ + 2, "minecraft:spruce_planks")
    b.walls(TX - 2, 29, TZ - 2, TX + 2, 29, TZ + 2, fence("spruce"))
    b.box(TX - 16, 29, TZ, TX + 3, 29, TZ, log("spruce", "x"))
    b.box(TX + 3, 27, TZ, TX + 4, 30, TZ, "minecraft:iron_block")   # counterweight
    b.set(TX, 30, TZ, log("spruce")); b.set(TX, 31, TZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    AX = TX - 15
    for y in range(17, 29):
        b.set(AX, y, TZ, CHAIN)
    b.box(AX, 12, TZ, AX, 16, TZ, "minecraft:iron_block")
    b.box(AX - 3, 11, TZ, AX + 3, 11, TZ, "minecraft:iron_block")
    b.set(AX - 3, 12, TZ, "minecraft:iron_block"); b.set(AX + 3, 12, TZ, "minecraft:iron_block")
    b.box(AX - 1, 16, TZ, AX + 1, 16, TZ, "minecraft:iron_block")
    b.set(AX, 17, TZ, "minecraft:iron_block")

    # --- The raiders' shacks: two stilt shacks of copper sheet and planks on the west shore, joined by a rope bridge.
    for (sx, sz) in ((CX - 27, CZ - 6), (CX - 27, CZ + 8)):
        for (x, z) in ((sx, sz), (sx + 8, sz), (sx, sz + 7), (sx + 8, sz + 7)):
            b.box(x, -6, z, x, 7, z, log("spruce"))
        b.hall(sx, sz, sx + 8, sz + 7, 7, 4, "minecraft:weathered_cut_copper", "minecraft:dark_oak_planks", log("spruce"),
               trim=None, floor="minecraft:spruce_planks", win=pane("brown"), every=4, doors=[("east", 3, 1, 2)], proud=False)
        b.gable_roof(sx, sz, sx + 8, sz + 7, 11, "spruce", "minecraft:spruce_planks", axis="x")
        bed("red", sx + 1, 8, sz + 1, b, "south"); bed("red", sx + 3, 8, sz + 1, b, "south")
        b.set(sx + 6, 8, sz + 1, BARREL); b.set(sx + 7, 8, sz + 1, "minecraft:crafting_table")
        b.table(sx + 2, 8, sz + 5, "spruce", "minecraft:red_carpet", w=2)
        b.set(sx + 4, 11, sz + 4, HANG)
        b.box(sx + 9, 7, sz + 3, sx + 10, 7, sz + 3, "minecraft:spruce_planks")
        for y in range(4, 7):
            b.set(sx + 10, y, sz + 4, ladder("south")) if False else None
        b.stair_run(sx + 10, 5, sz + 5, 3, "spruce", "north", "minecraft:spruce_planks") if False else None
        # a ladder up the east stilt
        for y in range(5, 8):
            b.set(sx + 9, y, sz + 2, ladder("east")) if False else None
        b.box(sx + 9, 4, sz + 4, sx + 9, 6, sz + 4, log("spruce"))
        for y in range(5, 8):
            b.set(sx + 10, y, sz + 4, ladder("east"))
    for z in range(CZ + 2, CZ + 8):
        b.set(CX - 23, 7, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
        b.set(CX - 24, 8, z, fence("spruce")) if z % 2 else None
        b.set(CX - 22, 8, z, fence("spruce")) if z % 2 else None

    # --- Scrap piles, salvage and junk all over the island.
    for (x, z) in ((CX - 14, CZ + 21), (CX + 14, CZ + 22), (CX - 22, CZ + 20), (CX + 20, CZ - 12), (CX - 12, CZ - 2), (CX + 12, CZ - 2), (CX + 24, CZ + 14)):
        b.sphere(x, 5, z, rnd.uniform(1.8, 3), rnd.choice(scrap), ry=rnd.uniform(1.5, 2.6), upper=True)
        b.scatter(x - 3, z - 3, x + 3, z + 3, 5, scrap, 0.35, rnd)
        b.support(x - 4, z - 4, x + 4, z + 4, 5, rubble, rnd, down_to=-14)
    props = ["minecraft:anvil[facing=north]", "minecraft:chipped_anvil[facing=east]", "minecraft:damaged_anvil[facing=south]", BARREL,
             "minecraft:cauldron", "minecraft:grindstone[face=floor,facing=north]", "minecraft:composter[level=0]", BARREL, "minecraft:chain[axis=x,waterlogged=false]".replace("minecraft:chain", "minecraft:iron_chain")]
    b.scatter(CX - 26, CZ - 24, CX + 26, CZ + 26, 5, props, 0.035, rnd, only_on=top)
    b.scatter(CX - 26, CZ - 24, CX + 26, CZ + 26, 5, ["minecraft:dead_bush", "minecraft:short_grass"], 0.04, rnd, only_on=["minecraft:coarse_dirt", "minecraft:rooted_dirt"])
    for (x, z) in ((CX - 3, CZ + 25), (CX + 3, CZ + 25), (CX - 18, CZ + 9), (CX + 18, CZ + 9), (CX - 6, CZ - 4), (CX + 6, CZ - 4)):
        b.lamp_post(x, 5, z, "spruce", 3)
        b.support(x, z, x, z, 5, [log("spruce")], rnd, down_to=-14)

    # --- The landing: a pier out to sea on the south side with a captured sloop tied up to it.
    for z in range(CZ + 24, CZ + 40):
        for dx in (-1, 0, 1):
            b.set(CX + dx, 3, z, "minecraft:spruce_planks")
        if z % 4 == 0:
            b.box(CX - 2, -10, z, CX - 2, 4, z, log("spruce")); b.box(CX + 2, -10, z, CX + 2, 4, z, log("spruce"))
            b.set(CX - 2, 5, z, LANTERN if z % 8 == 0 else "minecraft:spruce_slab[type=bottom,waterlogged=false]")
            b.set(CX + 2, 5, z, LANTERN if z % 8 == 0 else "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    b.ship(CX + 4, -2, CZ + 30, 20, 9, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks", masts=((7, 14),),
           sail="minecraft:gray_wool", flag=("minecraft:brown_wool", "minecraft:white_wool"), depth=4)
    b.mast_yard(CX + 4, 2, CZ + 30, 9, ((7, 14),))
    b.waterline = 2   # y = 2 is the sea's top layer: the island's top (y = 4) stands 2 above it; set after ship(), which sets it too
    b.flag(CX - 8, 5, CZ - 6, h=12, colors=("minecraft:brown_wool", "minecraft:white_wool"))

    b.rogue(PX, 4, PZ, "saltjaw_rourke")
    b.crew("scrapdeck_raider", ((PX - 6, PZ - 6), (PX + 6, PZ - 6), (PX, PZ + 7)), y=4)
    b.crew("scrapdeck_raider", ((CX - 23, 8, CZ - 2), (CX - 23, 8, CZ + 12), (TX - 3, 5, TZ + 3), (CX, 4, CZ + 30)))


# ============================================================ Corvina: the Lantern House
@lair("lantern_house", "The Widow's Lantern House", "corvina_fog_widow",
      ["minecraft:swamp", "minecraft:mangrove_swamp", "onepiece:thriller_bark"], "land")
def _(b):
    rnd = random.Random(2)
    W, D = 60, 64
    FL = 3   # the boardwalks and floors stand on stilts 3 above the bog
    deck = ["minecraft:dark_oak_planks"] * 6 + ["minecraft:spruce_planks", "minecraft:mangrove_planks"]
    # The bog: mud, puddles and roots under everything.
    for x in range(0, W + 1):
        for z in range(0, D + 1):
            r = rnd.random()
            b.set(x, 0, z, WATER if r < 0.12 else "minecraft:mud" if r < 0.7 else "minecraft:muddy_mangrove_roots" if r < 0.85 else "minecraft:moss_block")
            b.set(x, -1, z, "minecraft:mud")
    def boardwalk(x0, z0, x1, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                b.set(x, FL, z, rnd.choice(deck))
                if (x - x0) % 4 == 0 and (z - z0) % 4 == 0:
                    b.box(x, 1, z, x, FL - 1, z, log("mangrove"))
    def rail_posts(xs, zs, lamp_every=3):
        for i, (x, z) in enumerate(zip(xs, zs)):
            b.set(x, FL + 1, z, fence("dark_oak"))
            if i % lamp_every == 0:
                b.set(x, FL + 2, z, fence("dark_oak")); b.set(x, FL + 3, z, rnd.choice([LANTERN, SOUL_LANTERN]))

    # --- The approach: a long pier from the south edge through a lantern gate.
    boardwalk(28, 46, 32, D)
    rail_posts([27] * 19, list(range(46, D + 1)), 3); rail_posts([33] * 19, list(range(46, D + 1)), 3)
    for x in (26, 34):
        b.box(x, FL + 1, D - 2, x, FL + 8, D - 2, log("dark_oak"))
    b.box(25, FL + 9, D - 2, 35, FL + 9, D - 2, log("dark_oak", "x"))
    b.gable_roof(25, D - 2, 35, D - 2, FL + 10, "dark_oak", "minecraft:dark_oak_planks", ov=1)
    for x in (27, 30, 33):
        b.hanging(x, FL + 8, D - 2, 2, SOUL_HANG if x == 30 else HANG)

    # --- The Lantern Court (the arena): a round deck on stilts ringed by tall posts with lanterns hung on chains.
    AX, AZ, R = 30, 36, 11
    for x in range(AX - R, AX + R + 1):
        for z in range(AZ - R, AZ + R + 1):
            d = math.hypot(x - AX, z - AZ)
            if d <= R + 0.3:
                ring = int(d) % 4 == 0
                b.set(x, FL, z, "minecraft:spruce_planks" if ring else "minecraft:dark_oak_planks")
                if (x % 3 == 0 and z % 3 == 0):
                    b.box(x, 1, z, x, FL - 1, z, log("mangrove"))
    b.disk(AX, FL, AZ, 2, "minecraft:polished_blackstone_bricks"); b.set(AX, FL, AZ, "minecraft:crying_obsidian")
    for i in range(0, 360, 30):
        a = math.radians(i)
        x, z = round(AX + (R + 1) * math.cos(a)), round(AZ + (R + 1) * math.sin(a))
        b.box(x, 1, z, x, FL, z, log("mangrove"))
        b.box(x, FL + 1, z, x, FL + 8, z, log("dark_oak"))
        arm = ("west" if x > AX else "east") if abs(x - AX) >= abs(z - AZ) else ("north" if z > AZ else "south")
        b.lamp_post(x, FL + 1, z, "dark_oak", 8, SOUL_LANTERN if (i // 30) % 2 else LANTERN, arm=arm)
        if not (240 <= i <= 300) and not (60 <= i <= 120):   # railings, open to the north (manor) and south (pier)
            for j in range(0, 30, 6):
                aa = math.radians(i + j)
                b.set(round(AX + (R + 0.6) * math.cos(aa)), FL + 1, round(AZ + (R + 0.6) * math.sin(aa)), fence("dark_oak"))

    # --- The manor (her quarters): three storeys of black wood and deepslate, and a bell tower (the landmark).
    MX0, MZ0, MX1, MZ1 = 12, 2, 48, 18
    boardwalk(MX0 - 2, MZ0 - 1, MX1 + 2, MZ1 + 4)
    for (y, h, wall) in ((FL, 5, "minecraft:deepslate_bricks"), (FL + 5, 5, "minecraft:dark_oak_planks"), (FL + 10, 4, "minecraft:dark_oak_planks")):
        b.hall(MX0, MZ0, MX1, MZ1, y, h, wall, "minecraft:polished_deepslate" if y == FL else wall, log("dark_oak"),
               trim="minecraft:polished_blackstone_bricks", floor="minecraft:dark_oak_planks", win=pane("purple"), every=4,
               doors=[("south", 17, 3, 3)] if y == FL else [], proud=True)
        b.box(MX0 + 1, y + h, MZ0 + 1, MX1 - 1, y + h, MZ1 - 1, "minecraft:dark_oak_planks")
    top = b.gable_roof(MX0, MZ0, MX1, MZ1, FL + 14, "deepslate_tile", "minecraft:deepslate_tiles", ov=1, axis="x", eave=True)
    for x in (MX0 + 6, MX1 - 6):   # chimneys
        b.box(x, FL + 15, MZ0 + 3, x + 1, top + 3, MZ0 + 4, "minecraft:deepslate_bricks"); b.set(x, top + 4, MZ0 + 3, SMOKE)
    # a porch over the front door
    b.box(MX0 + 15, FL + 1, MZ1 + 1, MX0 + 15, FL + 4, MZ1 + 3, log("dark_oak")); b.box(MX0 + 21, FL + 1, MZ1 + 1, MX0 + 21, FL + 4, MZ1 + 3, log("dark_oak"))
    b.box(MX0 + 15, FL + 1, MZ1 + 2, MX0 + 15, FL + 3, MZ1 + 2, AIR); b.box(MX0 + 21, FL + 1, MZ1 + 2, MX0 + 21, FL + 3, MZ1 + 2, AIR)
    b.gable_roof(MX0 + 15, MZ1 + 1, MX0 + 21, MZ1 + 3, FL + 4, "deepslate_tile", "minecraft:deepslate_tiles", ov=1, axis="z")
    b.set(MX0 + 16, FL + 4, MZ1 + 3, HANG); b.set(MX0 + 20, FL + 4, MZ1 + 3, HANG)
    # bell tower in the middle of the roof
    BX = (MX0 + MX1) // 2
    b.hall(BX - 3, MZ0 + 5, BX + 3, MZ0 + 11, FL + 14, 12, "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks",
           log("dark_oak"), trim="minecraft:deepslate_tiles", win=None, proud=False)
    for (x, z) in ((BX, MZ0 + 5), (BX, MZ0 + 11), (BX - 3, MZ0 + 8), (BX + 3, MZ0 + 8)):
        b.box(x, FL + 22, z, x, FL + 24, z, AIR)
    b.box(BX, FL + 25, MZ0 + 8, BX, FL + 26, MZ0 + 8, CHAIN); b.set(BX, FL + 24, MZ0 + 8, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    b.hip_roof(BX - 3, MZ0 + 5, BX + 3, MZ0 + 11, FL + 26, "deepslate_tile", "minecraft:deepslate_tiles", ov=1)
    b.set(BX, FL + 31, MZ0 + 8, SOUL_LANTERN)
    for (x, z) in ((BX - 4, MZ0 + 4), (BX + 4, MZ0 + 4), (BX - 4, MZ0 + 12), (BX + 4, MZ0 + 12)):
        b.set(x, FL + 26, z, SOUL_HANG)
    # inside, ground floor: the hall with a long table and a stair up
    G = FL + 1
    b.table(BX - 8, G, MZ0 + 8, "dark_oak", "minecraft:purple_carpet", w=10)
    for x in range(BX - 8, BX + 2, 2):
        b.chair(x, G, MZ0 + 7, "dark_oak", "south"); b.chair(x, G, MZ0 + 9, "dark_oak", "north")
    for x in range(MX0 + 1, MX0 + 8):
        b.shelf(x, G, MZ0 + 1, 3) if x % 3 else b.set(x, G, MZ0 + 1, BARREL)
    b.stair_run(MX1 - 3, G, MZ1 - 1, 5, "dark_oak", "north", "minecraft:dark_oak_planks", width=2)
    b.box(MX1 - 3, FL + 5, MZ1 - 6, MX1 - 2, FL + 5, MZ1 - 2, AIR)
    for x in range(MX0 + 3, MX1 - 2, 6):
        b.set(x, FL + 4, MZ0 + 8, HANG)
    b.set(MX0 + 2, G, MZ1 - 2, "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    b.set(MX0 + 3, G, MZ1 - 2, "minecraft:cauldron")
    # first floor: Corvina's parlour, with her chest, books and a rug
    P = FL + 6
    for x in range(BX - 6, BX + 7):
        for z in range(MZ0 + 4, MZ0 + 13):
            b.set(x, P - 1, z, "minecraft:purple_wool" if (x + z) % 2 else "minecraft:black_wool") if False else None
            b.set(x, P, z, carpet("purple") if abs(x - BX) < 5 and 5 < z - MZ0 < 12 else AIR)
    for x in range(MX0 + 1, MX0 + 10):
        b.shelf(x, P, MZ0 + 1, 3)
    b.chest(BX, P, MZ0 + 2, "lantern_house", "south")
    b.set(BX - 1, P, MZ0 + 2, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    b.set(BX + 1, P, MZ0 + 2, candle(4, "purple"))
    b.chair(BX - 2, P, MZ0 + 9, "dark_oak", "east"); b.chair(BX + 2, P, MZ0 + 9, "dark_oak", "west")
    b.table(BX, P, MZ0 + 9, "dark_oak", candle(3, "black"))
    for x in range(MX0 + 3, MX1 - 2, 6):
        b.set(x, P + 3, MZ0 + 8, HANG)
    bed("black", MX1 - 6, P, MZ0 + 2, b, "south"); b.set(MX1 - 7, P, MZ0 + 2, candle(2))
    b.box(MX1 - 3, P - 1, MZ1 - 6, MX1 - 2, P - 1, MZ1 - 2, AIR)   # stairwell from below
    # cobwebs in the corners and up under the roof
    for y in range(G, FL + 14):
        b.scatter(MX0 + 1, MZ0 + 1, MX1 - 1, MZ1 - 1, y, [COBWEB], 0.006, rnd)

    # --- The smugglers' warehouses on the west and the boat dock on the east, joined to the court by boardwalks.
    boardwalk(4, 22, 18, 56)
    for (wz) in (24, 42):
        b.hall(5, wz, 15, wz + 11, FL, 5, "minecraft:spruce_planks", "minecraft:dark_oak_planks", log("dark_oak"), trim=None,
               floor="minecraft:spruce_planks", win=pane("black"), doors=[("east", 5, 2, 3)])
        b.gable_roof(5, wz, 15, wz + 11, FL + 5, "dark_oak", "minecraft:dark_oak_planks", axis="z", eave=True)
        for z in range(wz + 1, wz + 11):
            for x in (6, 7):
                b.crates(x, FL + 1, z, rnd, n=1, spread=0)
            if z % 3 == 0:
                b.set(13, FL + 1, z, "minecraft:barrel[facing=up,open=false]"); b.set(14, FL + 1, z, "minecraft:spruce_planks")
                b.set(14, FL + 2, z, LANTERN)
        b.table(10, FL + 1, wz + 3, "spruce", "minecraft:white_carpet", w=2, axis="z")
        b.set(10, FL + 4, wz + 6, HANG)
    boardwalk(18, 34, AX - R, 38)
    boardwalk(AX + R, 34, 46, 38)
    # the dock: a channel of open water and a smuggling boat
    for x in range(46, W + 1):
        for z in range(26, 52):
            b.set(x, 0, z, WATER); b.set(x, -1, z, WATER); b.set(x, -2, z, "minecraft:mud")
    boardwalk(46, 24, 50, 52)
    b.ship(51, -2, 30, 14, 7, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks", masts=((6, 9),), sail="minecraft:black_wool",
           flag=("minecraft:purple_wool", "minecraft:black_wool"), depth=3)
    b.mast_yard(51, 1, 30, 7, ((6, 9),))
    b.waterline = 0
    for z in range(24, 53, 4):
        b.lamp_post(50, FL + 1, z, "dark_oak", 2)
    b.crates(47, FL + 1, 44, rnd, n=6, spread=2)
    # dead trees hung with lanterns, mangrove roots, lily pads
    for (x, z) in ((6, 6), (54, 8), (3, 60), (22, 50), (40, 52), (56, 58), (20, 4)):
        b.tree(x, 1, z, 7, "dark_oak", 2.2)
        b.set(x + 1, 6, z, fence("dark_oak")); b.set(x + 1, 5, z, HANG)
    b.scatter(0, 0, W, D, 1, ["minecraft:lily_pad"], 0.25, rnd, only_on=[WATER])
    b.scatter(0, 0, W, D, 1, ["minecraft:mangrove_roots[waterlogged=false]", "minecraft:short_grass", "minecraft:brown_mushroom"], 0.05, rnd,
              only_on=["minecraft:mud", "minecraft:moss_block"])

    b.rogue(AX, FL + 1, AZ, "corvina_fog_widow")
    b.crew("lantern_smuggler", ((AX - 6, AZ - 5), (AX + 6, AZ - 5), (AX - 6, AZ + 6), (AX + 6, AZ + 6), (10, 30), (10, 48), (48, 40)), y=FL + 1)


# ============================================================ Graves: Fort Iron Tide
@lair("fort_iron_tide", "Fort Iron Tide", "iron_tide_graves",
      ["#minecraft:is_beach", "minecraft:plains", "minecraft:savanna", "onepiece:east_blue", "onepiece:jaya"], "land")
def _(b):
    rnd = random.Random(3)
    N = 62
    STONE = ["minecraft:stone_bricks"] * 6 + ["minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks"]
    pave = ["minecraft:polished_andesite"] * 4 + ["minecraft:andesite", "minecraft:cobblestone", "minecraft:stone"]
    # Ground: a paved yard inside, a gravel glacis outside.
    for x in range(-2, N + 3):
        for z in range(-6, N + 3):
            b.set(x, 0, z, rnd.choice(pave) if 3 <= x <= N - 3 and 3 <= z <= N - 3 else rnd.choice(["minecraft:gravel", "minecraft:coarse_dirt", "minecraft:grass_block"]))
            b.set(x, -1, z, "minecraft:cobblestone")
    def curtain(x0, z0, x1, z1):
        """A curtain wall 3 thick and 9 high: base course, buttresses outside, a string course, a walkway and merlons."""
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(1, 10):
                    b.set(x, y, z, rnd.choice(STONE))
                b.set(x, 1, z, "minecraft:cobblestone"); b.set(x, 5, z, "minecraft:polished_andesite")
                b.set(x, 10, z, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    curtain(0, 0, N, 2); curtain(0, N - 2, N, N); curtain(0, 0, 2, N); curtain(N - 2, 0, N, N)
    for i in range(0, N + 1, 2):   # merlons on the outer edge
        for (x, z) in ((i, 0), (i, N), (0, i), (N, i)):
            b.set(x, 10, z, "minecraft:stone_bricks"); b.set(x, 11, z, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    for i in range(6, N - 5, 6):   # buttresses
        for (x, z, dx, dz) in ((i, -1, 0, -1), (i, N + 1, 0, 1), (-1, i, -1, 0), (N + 1, i, 1, 0)):
            b.box(x, 1, z, x, 6, z, "minecraft:stone_bricks"); b.set(x, 7, z, stair("stone_brick", {(0, -1): "south", (0, 1): "north", (-1, 0): "east", (1, 0): "west"}[(dx, dz)]))
            b.set(x + dx, 1, z + dz, "minecraft:cobblestone"); b.set(x + dx, 2, z + dz, stair("stone_brick", {(0, -1): "south", (0, 1): "north", (-1, 0): "east", (1, 0): "west"}[(dx, dz)]))
    # Stairs up to the walls inside the yard.
    b.stair_run(8, 1, 3, 9, "stone_brick", "east", "minecraft:stone_bricks", width=2)
    b.stair_run(N - 8, 1, N - 4, 9, "stone_brick", "west", "minecraft:stone_bricks", width=2)
    # Navy-white bastions at the corners with blue roofs and cannons; peeling paint.
    for (cx, cz) in ((1, 1), (N - 1, 1), (1, N - 1), (N - 1, N - 1)):
        b.tower(cx, cz, 5, 14, "minecraft:white_concrete", "minecraft:blue_concrete", windows=True, ladder_side=False, floors=[5, 10])
        b.tower_cap(cx, cz, 5, 14, "minecraft:blue_concrete")
        b.walls(cx - 5, 1, cz - 5, cx + 5, 2, cz + 5, "minecraft:air") if False else None
        b.cyl(cx, cz, 5.4, 1, 2, "minecraft:stone_bricks", hollow=True)
        b.cyl(cx, cz, 5.4, 8, 8, "minecraft:blue_concrete", hollow=True)
        for k in range(6):
            a = rnd.uniform(0, 2 * math.pi); yy = rnd.randint(3, 13)
            px, pz = round(cx + 5 * math.cos(a)), round(cz + 5 * math.sin(a))
            if b.get(px, yy, pz) == "minecraft:white_concrete":
                b.set(px, yy, pz, rnd.choice(["minecraft:smooth_stone", "minecraft:light_gray_concrete", "minecraft:cracked_stone_bricks"]))
        for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            b.set(cx + dx, 15, cz + dz, "minecraft:dispenser[facing=" + ("east" if dx > 0 else "west" if dx < 0 else "south" if dz > 0 else "north") + ",triggered=false]")
        # doorways from the wall-walk into the bastion
        for (dx, dz) in ((4, 0), (-4, 0), (0, 4), (0, -4), (5, 0), (-5, 0), (0, 5), (0, -5)):
            if 0 < cx + dx < N and 0 < cz + dz < N:
                b.box(cx + dx, 11, cz + dz, cx + dx, 12, cz + dz, AIR)
    # Cannons along the wall-walk.
    for i in range(10, N - 9, 6):
        for (x, z, f) in ((i, 1, "north"), (i, N - 1, "south"), (1, i, "west"), (N - 1, i, "east")):
            b.set(x, 11, z, f"minecraft:dispenser[facing={f},triggered=false]")
            if f in ("north", "south"):
                b.set(x - 1, 11, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]"); b.set(x + 1, 11, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
            else:
                b.set(x, 11, z - 1, "minecraft:spruce_slab[type=bottom,waterlogged=false]"); b.set(x, 11, z + 1, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    # --- The gatehouse (south): twin towers, a portcullis half up, Navy white and blue over the arch.
    GX = N // 2
    b.hall(GX - 6, N - 4, GX + 6, N + 3, 0, 12, "minecraft:white_concrete", "minecraft:stone_bricks", "minecraft:polished_andesite",
           trim="minecraft:blue_concrete", win=pane("light_blue"), every=3, proud=True)
    b.box(GX - 2, 1, N - 4, GX + 2, 6, N + 3, AIR)
    for x in range(GX - 2, GX + 3):
        b.set(x, 7, N + 3, stair("stone_brick", "south", "top")); b.set(x, 7, N - 4, stair("stone_brick", "north", "top"))
        b.box(x, 5, N, x, 6, N, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
        b.box(x, 7, N, x, 11, N, "minecraft:stone_bricks")   # the wall over the gate the portcullis hangs from
    for (tx) in (GX - 7, GX + 7):
        b.tower(tx, N + 2, 3, 16, "minecraft:white_concrete", "minecraft:blue_concrete", ladder_side=False)
        b.tower_cap(tx, N + 2, 3, 16, "minecraft:blue_concrete")
        b.cyl(tx, N + 2, 3.4, 1, 2, "minecraft:stone_bricks", hollow=True)
    b.hip_roof(GX - 6, N - 4, GX + 6, N + 3, 12, "stone_brick", "minecraft:blue_concrete", ov=1)
    b.set(GX - 3, 6, N + 4, LANTERN); b.set(GX + 3, 6, N + 4, LANTERN)
    for x in range(GX - 3, GX + 4):   # the road in
        for z in range(N + 4, N + 9):
            b.set(x, 0, z, "minecraft:gravel" if abs(x - GX) == 3 else "minecraft:stone_bricks")
    # --- The parade ground (the arena): a painted Navy target, ringed with posts, a training yard on one side.
    AX, AZ = GX, 30
    b.disk(AX, 0, AZ, 12, "minecraft:smooth_stone")
    b.disk(AX, 0, AZ, 10.5, "minecraft:white_concrete")
    b.disk(AX, 0, AZ, 9.5, "minecraft:smooth_stone")
    b.disk(AX, 0, AZ, 5.5, "minecraft:blue_concrete")
    b.disk(AX, 0, AZ, 4.5, "minecraft:smooth_stone")
    b.disk(AX, 0, AZ, 1.5, "minecraft:white_concrete")
    for i in range(0, 360, 30):
        a = math.radians(i)
        x, z = round(AX + 13 * math.cos(a)), round(AZ + 13 * math.sin(a))
        b.set(x, 1, z, wall_post("stone_brick")); b.set(x, 2, z, wall_post("stone_brick")); b.set(x, 3, z, LANTERN)
    # training dummies and weapon racks
    for z in range(16, 24, 3):
        b.set(10, 1, z, fence("spruce")); b.set(10, 2, z, "minecraft:hay_block[axis=y]"); b.set(10, 3, z, "minecraft:carved_pumpkin[facing=east]")
    for z in range(16, 26, 2):
        b.set(5, 1, z, "minecraft:grindstone[face=floor,facing=east]" if z % 4 else "minecraft:smithing_table")
    for x in range(14, 20, 2):
        b.set(x, 1, 40, "minecraft:target[power=0]"); b.set(x, 2, 40, "minecraft:target[power=0]")
    # --- The barracks (west) and the powder store (east).
    b.hall(4, 28, 14, 52, 0, 5, "minecraft:white_concrete", "minecraft:stone_bricks", "minecraft:polished_andesite",
           trim="minecraft:blue_concrete", floor="minecraft:spruce_planks", win=pane("light_blue"), doors=[("east", 11, 2, 3)])
    b.gable_roof(4, 28, 14, 52, 5, "stone_brick", "minecraft:white_concrete", axis="z", eave=True)
    for z in range(30, 51, 3):
        if abs(z - 40) > 1:
            bed("blue", 5, 1, z, b, "east"); b.set(7, 1, z + 1, "minecraft:barrel[facing=up,open=false]")
            bed("blue", 12, 1, z, b, "west")
    for z in range(31, 52, 6):
        b.set(9, 5, z, HANG)
    b.table(9, 1, 38, "spruce", "minecraft:blue_carpet", w=4, axis="z")
    b.hall(N - 14, 8, N - 4, 22, 0, 5, "minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:polished_andesite",
           trim="minecraft:stone_bricks", floor="minecraft:spruce_planks", win="minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]",
           doors=[("west", 6, 2, 3)])
    b.gable_roof(N - 14, 8, N - 4, 22, 5, "cobblestone", "minecraft:cobblestone", axis="z")
    for z in range(9, 22):
        for x in (N - 13, N - 5):
            b.set(x, 1, z, BARREL); b.set(x, 2, z, BARREL) if z % 2 else None
    b.set(N - 9, 5, 15, HANG)
    # --- The keep (Graves's headquarters, north): three floors, a mess hall, his office with the chest, and the cells.
    KX0, KZ0, KX1, KZ1 = 18, 4, 44, 18
    for (y, h) in ((0, 5), (5, 5), (10, 5)):
        b.hall(KX0, KZ0, KX1, KZ1, y, h, "minecraft:white_concrete", "minecraft:stone_bricks" if y == 0 else "minecraft:white_concrete",
               "minecraft:polished_andesite", trim="minecraft:blue_concrete", floor="minecraft:spruce_planks", win=pane("light_blue"),
               doors=[("south", 11, 4, 4)] if y == 0 else [], every=4)
        b.box(KX0 + 1, y + h, KZ0 + 1, KX1 - 1, y + h, KZ1 - 1, "minecraft:spruce_planks")
    b.hip_roof(KX0, KZ0, KX1, KZ1, 15, "stone_brick", "minecraft:blue_concrete", ov=1)
    b.box(KX0 + 9, 16, KZ0 + 4, KX1 - 9, 20, KZ1 - 4, "minecraft:white_concrete")   # the lookout on top
    b.hip_roof(KX0 + 9, KZ0 + 4, KX1 - 9, KZ1 - 4, 20, "stone_brick", "minecraft:blue_concrete", ov=1)
    for x in range(KX0 + 10, KX1 - 9, 2):
        b.set(x, 18, KZ1 - 4, pane("light_blue"))
    # steps and a balcony over the door
    b.box(KX0 + 10, 0, KZ1 + 1, KX0 + 16, 0, KZ1 + 2, "minecraft:polished_andesite")
    for x in range(KX0 + 10, KX0 + 17):
        b.set(x, 5, KZ1 + 1, "minecraft:white_concrete"); b.set(x, 6, KZ1 + 1, wall_post("stone_brick")) if x % 2 == 0 else None
        b.set(x, 4, KZ1 + 1, stair("stone_brick", "north", "top"))
    b.box(KX0 + 12, 6, KZ1, KX0 + 14, 7, KZ1, AIR)
    # inside, ground floor: the mess hall
    for z in (KZ0 + 4, KZ0 + 10):
        b.table(KX0 + 4, 1, z, "spruce", "minecraft:white_carpet", w=10)
        for x in range(KX0 + 4, KX0 + 14, 2):
            b.chair(x, 1, z - 1, "spruce", "south"); b.chair(x, 1, z + 1, "spruce", "north")
    b.set(KX1 - 2, 1, KZ0 + 2, "minecraft:smoker[facing=west,lit=true]"); b.set(KX1 - 2, 1, KZ0 + 3, "minecraft:furnace[facing=west,lit=false]")
    b.set(KX1 - 2, 1, KZ0 + 4, BARREL); b.set(KX1 - 2, 1, KZ0 + 5, "minecraft:cauldron")
    b.stair_run(KX1 - 4, 1, KZ1 - 2, 4, "spruce", "north", "minecraft:spruce_planks", width=2); b.box(KX1 - 4, 5, KZ1 - 6, KX1 - 3, 5, KZ1 - 3, AIR)
    for x in range(KX0 + 3, KX1, 6):
        b.set(x, 4, KZ0 + 7, HANG)
    # first floor: the commandant's office
    O = 6
    b.box(KX0 + 8, O, KZ0 + 2, KX0 + 18, O, KZ0 + 10, carpet("blue"))
    b.table(KX0 + 11, O, KZ0 + 4, "dark_oak", "minecraft:dark_oak_pressure_plate[powered=false]", w=5)
    b.chair(KX0 + 13, O, KZ0 + 3, "dark_oak", "south")
    b.chest(KX0 + 13, O, KZ0 + 1, "fort_iron_tide", "south")
    for x in range(KX0 + 1, KX0 + 8):
        b.shelf(x, O, KZ0 + 1, 3)
    b.set(KX0 + 16, O, KZ0 + 1, "minecraft:cartography_table"); b.set(KX0 + 17, O, KZ0 + 1, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    b.set(KX0 + 10, O, KZ0 + 1, "minecraft:white_banner[rotation=0]") if False else None
    # the armoury beside it
    for x in range(KX0 + 22, KX1):
        b.set(x, O, KZ0 + 1, rnd.choice(["minecraft:smithing_table", "minecraft:anvil[facing=east]", BARREL, "minecraft:grindstone[face=floor,facing=north]"]))
    for x in range(KX0 + 3, KX1, 6):
        b.set(x, O + 3, KZ0 + 7, HANG)
    b.stair_run(KX1 - 4, O, KZ0 + 2, 4, "spruce", "south", "minecraft:spruce_planks", width=2); b.box(KX1 - 4, O + 4, KZ0 + 2, KX1 - 3, O + 4, KZ0 + 5, AIR)
    # second floor: the cells
    C = 11
    for x in range(KX0 + 2, KX1 - 6, 4):
        b.box(x, C, KZ0 + 1, x, C + 3, KZ0 + 5, "minecraft:stone_bricks")
        b.box(x + 1, C, KZ0 + 5, x + 3, C + 3, KZ0 + 5, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
        b.set(x + 2, C, KZ0 + 2, "minecraft:white_carpet"); b.set(x + 1, C, KZ0 + 1, "minecraft:cauldron") if x % 8 == 2 else None
    for x in range(KX0 + 3, KX1, 6):
        b.set(x, C + 3, KZ0 + 10, HANG)
    # --- His flag (the landmark): a 26-high pole before the keep, the Navy flag torn and his own mark sewn over it.
    FX, FZ = GX, 21
    b.box(FX - 1, 1, FZ - 1, FX + 1, 1, FZ + 1, "minecraft:polished_andesite")
    b.box(FX, 2, FZ, FX, 27, FZ, fence("dark_oak"))
    b.box(FX + 1, 21, FZ, FX + 8, 26, FZ, "minecraft:white_wool")
    for (x, y) in ((FX + 3, 23), (FX + 4, 24), (FX + 5, 23), (FX + 4, 22), (FX + 3, 25), (FX + 5, 25)):
        b.set(x, y, FZ, "minecraft:black_wool")
    for (x, y) in ((FX + 8, 21), (FX + 8, 22), (FX + 7, 21), (FX + 8, 26), (FX + 6, 21)):
        b.set(x, y, FZ, AIR)   # torn edge
    b.box(FX + 1, 26, FZ, FX + 8, 26, FZ, "minecraft:blue_wool")
    b.set(FX, 28, FZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # yard clutter: cannonball stacks, crates, a water trough
    for (x, z) in ((20, 46), (40, 46), (48, 30), (48, 40)):
        b.set(x, 1, z, "minecraft:coal_block"); b.set(x + 1, 1, z, "minecraft:coal_block"); b.set(x, 2, z, "minecraft:blackstone")
    b.crates(48, 1, 44, rnd, n=6); b.crates(18, 1, 54, rnd, n=5)
    for x in range(40, 46):
        b.set(x, 1, 54, "minecraft:water_cauldron[level=3]" if x % 2 else "minecraft:cauldron")

    b.rogue(AX, 1, AZ, "iron_tide_graves")
    b.crew("deserter_marine", ((AX - 7, AZ - 6), (AX + 7, AZ - 6), (AX - 7, AZ + 6), (AX + 7, AZ + 6), (GX, N - 6), (10, 40), (KX0 + 6, KZ1 + 3)))


# ============================================================ Tsurugi: the Hollow Shrine
@lair("hollow_shrine", "The Hollow Shrine", "hollow_ronin_tsurugi",
      ["minecraft:cherry_grove", "minecraft:meadow", "minecraft:taiga", "onepiece:wano"], "land")
def _(b):
    rnd = random.Random(4)
    W, D = 58, 74
    CXs = W // 2
    STONE = ["minecraft:stone_bricks"] * 5 + ["minecraft:mossy_stone_bricks"] * 2 + ["minecraft:cracked_stone_bricks"]
    grass = ["minecraft:moss_block", "minecraft:grass_block", "minecraft:grass_block", "minecraft:podzol"]
    # Three terraces climbing to the north: the approach (y 0), the ring (y 3) and the shrine (y 6).
    def terrace(z0, z1, y):
        for x in range(0, W + 1):
            for z in range(z0, z1 + 1):
                for yy in range(-1, y):
                    b.set(x, yy, z, "minecraft:dirt")
                b.set(x, y, z, rnd.choice(grass))
    terrace(50, D, 0); terrace(26, 49, 3); terrace(0, 25, 6)
    for (z, y) in ((49, 3), (25, 6)):   # retaining walls with a capstone
        for x in range(0, W + 1):
            for yy in range(y - 3 if y == 6 else 0, y + 1):
                b.set(x, yy, z, rnd.choice(STONE))
            b.set(x, y + 1, z, slab("stone_brick"))
    for x in range(CXs - 3, CXs + 4):   # wide stairs up the middle
        b.box(x, 1, 50, x, 3, 52, AIR); b.box(x, 4, 26, x, 6, 28, AIR)
    b.stair_run(CXs - 3, 1, 52, 3, "stone_brick", "north", "minecraft:stone_bricks", width=7)
    b.stair_run(CXs - 3, 4, 28, 3, "stone_brick", "north", "minecraft:stone_bricks", width=7)
    # The path up, gravel with stone edging.
    for z in range(0, D + 1):
        y = 0 if z > 52 else 3 if z > 28 else 6
        for x in range(CXs - 2, CXs + 3):
            if b.get(x, y, z) in grass:
                b.set(x, y, z, "minecraft:gravel" if abs(x - CXs) < 2 else "minecraft:polished_andesite")
    # --- Three torii on the approach, each larger than the last.
    def torii(z, y, half, h):
        for x in (CXs - half, CXs + half):
            b.box(x, y + 1, z, x, y + h, z, "minecraft:red_concrete")
            b.set(x, y + 1, z, "minecraft:black_concrete")
        b.box(CXs - half - 2, y + h + 1, z, CXs + half + 2, y + h + 1, z, "minecraft:black_concrete")
        b.set(CXs - half - 2, y + h + 2, z, slab("blackstone")); b.set(CXs + half + 2, y + h + 2, z, slab("blackstone"))
        b.box(CXs - half - 1, y + h - 1, z, CXs + half + 1, y + h - 1, z, "minecraft:red_concrete")
        b.set(CXs, y + h, z, "minecraft:black_concrete")
    torii(D - 2, 0, 4, 7); torii(58, 0, 5, 8); torii(30, 3, 6, 10)
    for z in range(54, D, 5):
        b.stone_lantern(CXs - 5, 1, z, "stone_brick"); b.stone_lantern(CXs + 5, 1, z, "stone_brick")
    # --- The dueling ring (the arena): a raised stone stage with a sand floor, swords of the beaten all around it.
    AX, AZ, R = CXs, 38, 9
    b.cyl(AX, AZ, R + 1, 3, 4, "minecraft:stone_bricks")
    b.disk(AX, 4, AZ, R + 1, "minecraft:polished_andesite")
    b.disk(AX, 4, AZ, R, "minecraft:smooth_sandstone")
    b.disk(AX, 4, AZ, 1.2, "minecraft:chiseled_stone_bricks")
    for i in range(0, 360, 45):
        a = math.radians(i)
        b.set(round(AX + (R - 3) * math.cos(a)), 4, round(AZ + (R - 3) * math.sin(a)), "minecraft:chiseled_sandstone")
    for i in range(0, 360, 6):   # a rope of straw around the ring (kept low)
        a = math.radians(i)
        x, z = round(AX + (R + 1) * math.cos(a)), round(AZ + (R + 1) * math.sin(a))
        if b.get(x, 5, z) is None and not (80 < i < 100 or 260 < i < 280):
            b.set(x, 5, z, "minecraft:hay_block[axis=y]" if i % 30 == 0 else "minecraft:white_carpet")
    for i in range(15, 360, 30):
        a = math.radians(i)
        b.stone_lantern(round(AX + (R + 3) * math.cos(a)), 4, round(AZ + (R + 3) * math.sin(a)), "stone_brick")
    swords = 0
    for _ in range(400):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(R + 4, R + 13)
        x, z = round(AX + r * math.cos(a)), round(AZ + r * math.sin(a))
        if 1 < x < W - 1 and 30 < z < 48 and b.get(x, 4, z) is None and b.get(x, 3, z) in grass and abs(x - CXs) > 3:
            b.set(x, 4, z, rnd.choice(["minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]"] * 3 + [wall_post("cobblestone"), "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]"]))
            swords += 1
            if swords >= 46:
                break
    # --- The shrine hall (his quarters, north): a raised hall with white walls, dark frames and a double roof.
    SX0, SZ0, SX1, SZ1 = CXs - 13, 5, CXs + 13, 19
    b.box(SX0 - 2, 6, SZ0 - 2, SX1 + 2, 7, SZ1 + 2, "minecraft:stone_bricks")
    b.box(SX0 - 2, 7, SZ0 - 2, SX1 + 2, 7, SZ1 + 2, "minecraft:polished_andesite")
    b.stair_run(CXs - 3, 7, SZ1 + 3, 1, "stone_brick", "north", "minecraft:stone_bricks", width=7)
    b.hall(SX0, SZ0, SX1, SZ1, 7, 6, "minecraft:calcite", "minecraft:dark_oak_planks", log("dark_oak"), trim="minecraft:dark_oak_planks",
           floor="minecraft:bamboo_mosaic", win=trap("spruce", "south", "bottom", True) if False else "minecraft:spruce_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]",
           every=3, doors=[("south", 11, 5, 4)], win_h=2)
    for x in range(SX0, SX1 + 1):   # a veranda all round
        for z in (SZ0 - 2, SZ1 + 2):
            b.set(x, 7, z, "minecraft:spruce_planks")
            if x % 3 == 0:
                b.box(x, 8, z, x, 12, z, log("dark_oak"))
    b.pagoda_roof(SX0 - 1, SZ0 - 2, SX1 + 1, SZ1 + 2, 13, "deepslate_tile", "minecraft:deepslate_tiles", ov=2)
    b.box(SX0 + 6, 16, SZ0 + 3, SX1 - 6, 19, SZ1 - 3, "minecraft:calcite")
    for x in range(SX0 + 6, SX1 - 5, 3):
        b.box(x, 16, SZ0 + 3, x, 19, SZ0 + 3, log("dark_oak")); b.box(x, 16, SZ1 - 3, x, 19, SZ1 - 3, log("dark_oak"))
    b.pagoda_roof(SX0 + 6, SZ0 + 3, SX1 - 6, SZ1 - 3, 19, "deepslate_tile", "minecraft:deepslate_tiles", ov=2)
    for x in (SX0 - 1, SX1 + 1):
        b.hang_from(x, 11, SZ1 + 2, SOUL_HANG)
    # inside: the altar where he keeps his blade's sheath, candles, soul fires and the chest
    I = 8
    b.box(CXs - 4, I, SZ0 + 1, CXs + 4, I, SZ0 + 3, "minecraft:dark_oak_planks")
    for x in range(CXs - 4, CXs + 5):
        b.set(x, I, SZ0 + 4, stair("dark_oak", "north"))
    b.chest(CXs, I + 1, SZ0 + 1, "hollow_shrine", "south")
    b.set(CXs - 2, I + 1, SZ0 + 2, SOUL_FIRE); b.set(CXs + 2, I + 1, SZ0 + 2, SOUL_FIRE)
    for x in (CXs - 4, CXs - 3, CXs + 3, CXs + 4):
        b.set(x, I + 1, SZ0 + 2, candle(rnd.randint(1, 4)))
    b.set(CXs, I + 1, SZ0 + 2, "minecraft:lightning_rod[facing=east,powered=false,waterlogged=false]")
    for x in range(SX0 + 2, SX1 - 1, 3):
        for z in (SZ0 + 7, SZ0 + 11):
            b.set(x, I, z, "minecraft:white_carpet") if (x + z) % 2 else None
        b.set(x, I + 4, SZ0 + 9, SOUL_HANG)
    for z in range(SZ0 + 6, SZ1):   # sitting cushions along the sides
        b.set(SX0 + 1, I, z, "minecraft:red_carpet"); b.set(SX1 - 1, I, z, "minecraft:red_carpet")
    # --- The pagoda (the landmark): five tiers, 34 high, east of the hall.
    PX, PZ = W - 9, 12
    y = 6
    for t, half in enumerate((5, 4, 4, 3, 2)):
        h = 5 if t == 0 else 4
        b.hall(PX - half, PZ - half, PX + half, PZ + half, y, h, "minecraft:calcite" if t % 2 == 0 else "minecraft:red_terracotta",
               "minecraft:dark_oak_planks", log("dark_oak"), win="minecraft:spruce_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]",
               every=2 if half < 4 else 3, doors=[("west", half, 1, 3)] if t == 0 else [], proud=False)
        b.pagoda_roof(PX - half, PZ - half, PX + half, PZ + half, y + h, "deepslate_tile", "minecraft:deepslate_tiles", ov=2)
        y += h + 2
    for yy in range(y - 2, y + 6):
        b.set(PX, yy, PZ, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]" if yy % 2 else CHAIN)
    b.set(PX, y + 6, PZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    b.set(PX - 7, 7, PZ, "minecraft:bell[attachment=floor,facing=west,powered=false]")
    # --- The koi pond and its bridge (west of the ring), a ruined dormitory (north-west), the belfry by the stairs.
    for x in range(3, 16):
        for z in range(31, 47):
            if math.hypot((x - 9) / 6.5, (z - 39) / 8) <= 1:
                b.set(x, 3, z, WATER); b.set(x, 2, z, WATER); b.set(x, 1, z, "minecraft:clay")
                if rnd.random() < 0.15:
                    b.set(x, 4, z, "minecraft:lily_pad")
    for x in range(2, 17):
        b.set(x, 4, 39, "minecraft:spruce_planks" if 3 < x < 15 else stair("spruce", "east" if x < 9 else "west"))
        if x in (5, 13):
            b.set(x, 5, 38, fence("dark_oak")); b.set(x, 5, 40, fence("dark_oak")); b.set(x, 6, 38, "minecraft:red_concrete"); b.set(x, 6, 40, "minecraft:red_concrete")
    for (x, z) in ((3, 37), (15, 41), (4, 45)):
        b.set(x, 4, z, "minecraft:mossy_cobblestone"); b.set(x, 5, z, "minecraft:mossy_cobblestone_slab[type=bottom,waterlogged=false]")
    b.hall(2, 4, 13, 18, 6, 4, "minecraft:calcite", "minecraft:dark_oak_planks", log("dark_oak"), floor="minecraft:bamboo_mosaic",
           win="minecraft:spruce_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]", every=3, doors=[("east", 6, 2, 3)])
    b.gable_roof(2, 4, 13, 18, 10, "deepslate_tile", "minecraft:deepslate_tiles", axis="z")
    b.box(4, 11, 9, 12, 14, 13, AIR)   # its roof fell in
    b.box(4, 7, 10, 7, 7, 12, "minecraft:deepslate_tiles"); b.set(5, 8, 11, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]")
    for z in (6, 14):
        b.set(4, 7, z, "minecraft:white_carpet"); b.set(5, 7, z, "minecraft:white_carpet")
    b.set(11, 7, 6, BARREL); b.set(11, 7, 7, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    b.set(7, 10, 16, SOUL_HANG)
    # cherry trees, big ones, and petals underfoot
    for (x, z, h) in ((4, 58, 8), (W - 4, 60, 9), (6, 70, 7), (W - 6, 70, 8), (W - 5, 34, 9), (W - 8, 44, 7), (20, 2, 8), (W - 20, 2, 7), (3, 27, 6)):
        yb = 1 if z > 49 else 4 if z > 25 else 7
        b.tree(x, yb, z, h, "cherry", 3.4)
    b.scatter(0, 0, W, D, 1, ["minecraft:pink_petals[facing=north,flower_amount=4]", "minecraft:short_grass", "minecraft:fern"], 0.08, rnd, only_on=grass)
    b.scatter(0, 0, W, D, 4, ["minecraft:pink_petals[facing=east,flower_amount=3]", "minecraft:short_grass"], 0.06, rnd, only_on=grass)
    b.scatter(0, 0, W, D, 7, ["minecraft:pink_petals[facing=south,flower_amount=2]", "minecraft:short_grass"], 0.06, rnd, only_on=grass)

    b.rogue(AX, 5, AZ, "hollow_ronin_tsurugi")


# ============================================================ Gantz: the Shipbreakers' Foundry
@lair("shipbreakers_foundry", "The Shipbreakers' Foundry", "boilerheart_gantz",
      ["minecraft:badlands", "minecraft:desert", "onepiece:onigashima", "onepiece:punk_hazard_burning"], "land")
def _(b):
    rnd = random.Random(5)
    W, D = 64, 58
    ground = ["minecraft:blackstone", "minecraft:polished_blackstone", "minecraft:gravel", "minecraft:cracked_polished_blackstone_bricks",
              "minecraft:basalt[axis=y]", "minecraft:coal_block", "minecraft:blackstone"]
    for x in range(0, W + 1):
        for z in range(0, D + 1):
            b.set(x, 0, z, rnd.choice(ground)); b.set(x, -1, z, "minecraft:blackstone")
    COPPER = "waxed_weathered_cut_copper"
    # --- The foundry hall (north): brick and iron, a copper roof, three smokestacks 34 high (the landmark).
    FX0, FZ0, FX1, FZ1 = 3, 2, 60, 22
    b.hall(FX0, FZ0, FX1, FZ1, 0, 11, "minecraft:bricks", "minecraft:polished_blackstone_bricks", "minecraft:iron_block",
           trim="minecraft:polished_blackstone_bricks", floor="minecraft:polished_blackstone", win=pane("orange"), every=5, win_h=4,
           doors=[("south", 8, 5, 7), ("south", 25, 6, 8), ("south", 44, 5, 7)])
    b.gable_roof(FX0, FZ0, FX1, FZ1, 11, COPPER, f"minecraft:{COPPER}", ov=1, axis="x", eave=True)
    for x in range(FX0 + 5, FX1 - 4, 10):   # a clerestory of skylights along the ridge
        b.set(x, 21, (FZ0 + FZ1) // 2, "minecraft:orange_stained_glass")
    STACKS = (14, 32, 50)
    for sx in STACKS:
        sz = FZ0 + 5
        b.cyl(sx, sz, 2.2, 1, 34, "minecraft:bricks", hollow=True)
        for y in (14, 20, 26, 32):
            b.cyl(sx, sz, 2.6, y, y, "minecraft:iron_block", hollow=True)
        b.set(sx, 33, sz, SMOKE); b.set(sx, 32, sz, "minecraft:blackstone")
        b.box(sx - 1, 1, sz - 1, sx + 1, 3, sz + 1, "minecraft:blast_furnace[facing=south,lit=true]")
        b.set(sx, 2, sz + 2, "minecraft:lava_cauldron")
    # inside: forges, anvils, lava troughs, chains, a catwalk and Gantz's office up on it
    for x in range(FX0 + 4, FX1 - 3, 6):
        b.set(x, 1, FZ0 + 12, "minecraft:anvil[facing=east]"); b.set(x + 1, 1, FZ0 + 12, "minecraft:grindstone[face=floor,facing=north]") if x % 12 == 7 else None
        b.set(x + 2, 1, FZ0 + 12, "minecraft:smithing_table") if x % 12 == 1 else None
        b.hanging(x + 3, 10, FZ0 + 10, rnd.randint(2, 5), "minecraft:iron_block" if x % 12 else HANG)
    for x in range(FX0 + 2, FX1 - 1):
        if x % 7 not in (0, 1):
            b.set(x, 0, FZ1 - 3, "minecraft:magma_block")
    for x in range(FX0 + 1, FX1):
        for z in (FZ0 + 1, FZ0 + 2):
            b.set(x, 7, z, "minecraft:polished_blackstone_brick_slab[type=top,waterlogged=false]")
        b.set(x, 8, FZ0 + 3, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for y in range(1, 8):
        b.set(FX0 + 1, y, FZ0 + 3, ladder("south"))
    b.box(FX1 - 12, 8, FZ0 + 1, FX1 - 1, 11, FZ0 + 6, "minecraft:bricks"); b.box(FX1 - 11, 8, FZ0 + 2, FX1 - 2, 10, FZ0 + 5, AIR)
    b.box(FX1 - 11, 7, FZ0 + 2, FX1 - 2, 7, FZ0 + 5, "minecraft:spruce_planks")
    b.box(FX1 - 12, 8, FZ0 + 3, FX1 - 12, 9, FZ0 + 3, AIR)
    b.chest(FX1 - 3, 8, FZ0 + 2, "shipbreakers_foundry", "south")
    b.table(FX1 - 7, 8, FZ0 + 3, "spruce", "minecraft:spruce_pressure_plate[powered=false]", w=3)
    b.chair(FX1 - 6, 8, FZ0 + 4, "spruce", "north")
    b.set(FX1 - 10, 8, FZ0 + 2, BARREL); b.set(FX1 - 9, 8, FZ0 + 2, "minecraft:cartography_table"); b.set(FX1 - 2, 8, FZ0 + 5, "minecraft:blast_furnace[facing=west,lit=true]")
    b.set(FX1 - 6, 10, FZ0 + 4, HANG)
    for x in range(FX0 + 4, FX1, 8):
        b.set(x, 10, FZ0 + 16, HANG)
    # rails from the dock to the forges, with a coal heap at the end
    for z in range(FZ1 - 1, 34):
        b.set(26, 1, z, "minecraft:rail[shape=north_south,waterlogged=false]")
    b.sphere(20, 1, 27, 3, "minecraft:coal_block", ry=2, upper=True); b.scatter(16, 23, 24, 31, 1, ["minecraft:coal_ore", "minecraft:coal_block"], 0.3, rnd)
    # --- The drydock (south-west): a sunken pit with a warship being torn down to its ribs, under a gantry crane.
    DX0, DZ0, DX1, DZ1 = 3, 33, 40, 56
    for x in range(DX0, DX1 + 1):
        for z in range(DZ0, DZ1 + 1):
            edge = x in (DX0, DX1) or z in (DZ0, DZ1)
            for y in range(-4, 1):
                b.set(x, y, z, "minecraft:stone_bricks" if edge or y == -4 else AIR)
            if edge:
                b.set(x, 1, z, "minecraft:polished_blackstone_brick_slab[type=bottom,waterlogged=false]")
    b.box(DX0 + 1, -4, DZ0 + 1, DX1 - 1, -4, DZ1 - 1, "minecraft:polished_blackstone")
    b.box(DX1 - 1, -3, DZ0 + 8, DX1 - 1, -3, DZ0 + 10, AIR)
    for i in range(4):
        b.box(DX1 + 1 - 0, 0 - i, DZ0 + 8, DX1, 0 - i, DZ0 + 10, AIR) if False else None
    b.stair_run(DX1 - 4, -3, DZ0 + 8, 4, "stone_brick", "east", "minecraft:stone_bricks", width=3)
    b.box(DX1, -0, DZ0 + 8, DX1, 0, DZ0 + 10, "minecraft:stone_bricks")
    b.box(DX1, 1, DZ0 + 8, DX1, 1, DZ0 + 10, AIR)
    keel_z = (DZ0 + DZ1) // 2
    b.box(DX0 + 3, -3, keel_z, DX1 - 3, -3, keel_z, log("spruce", "x"))
    for x in range(DX0 + 3, DX1 - 2, 3):
        f = (x - DX0) / (DX1 - DX0)
        half = 8 if f < 0.7 else int(8 - (f - 0.7) * 22)
        for k in range(-half, half + 1):
            yy = -3 + int(round((abs(k) / max(half, 1)) ** 2 * 8))
            yin = -3 + int(round((max(abs(k) - 1, 0) / max(half, 1)) ** 2 * 8))   # the step in toward the keel: fill it so the rib is whole
            for y3 in range(min(yin + 1, yy), yy + 1):
                b.set(x, y3, keel_z + k, log("dark_oak"))
            if abs(k) == half:
                b.box(x, yy, keel_z + k, x, 5, keel_z + k, log("dark_oak"))
        b.set(x, -2, keel_z - 1, "minecraft:spruce_planks"); b.set(x, -2, keel_z + 1, "minecraft:spruce_planks")
    for x in range(DX0 + 3, DX0 + 14):   # the stern still has its planking
        for k in range(-8, 9):
            yy = -3 + int(round((abs(k) / 8) ** 2 * 8))
            yin = -3 + int(round((max(abs(k) - 1, 0) / 8) ** 2 * 8))
            for y2 in range(min(yin + 1, yy), 6 if abs(k) == 8 else yy + 1):
                b.set(x, y2, keel_z + k, "minecraft:dark_oak_planks" if (x + y2) % 4 else "minecraft:spruce_planks")
    b.box(DX0 + 3, 5, keel_z - 8, DX0 + 13, 5, keel_z + 8, "minecraft:spruce_planks")
    b.box(DX0 + 5, 6, keel_z - 6, DX0 + 10, 9, keel_z + 6, "minecraft:dark_oak_planks"); b.box(DX0 + 6, 6, keel_z - 5, DX0 + 9, 8, keel_z + 5, AIR)
    b.box(DX0 + 10, 6, keel_z - 1, DX0 + 10, 7, keel_z + 1, AIR)
    for z in range(keel_z - 5, keel_z + 6, 3):
        b.set(DX0 + 6, 6, z, "minecraft:red_bed[facing=east,occupied=false,part=foot]"); b.set(DX0 + 7, 6, z, "minecraft:red_bed[facing=east,occupied=false,part=head]")
    b.set(DX0 + 9, 8, keel_z, HANG)
    for (gx) in (DX0 + 6, DX1 - 6):   # gantry
        for gz in (DZ0 - 1, DZ1 + 1):
            b.box(gx, 1, gz, gx, 18, gz, "minecraft:iron_block")
            b.set(gx, 1, gz, "minecraft:polished_blackstone_bricks")
        b.box(gx, 18, DZ0 - 1, gx, 18, DZ1 + 1, "minecraft:iron_block")
    b.box(DX0 + 6, 19, keel_z, DX1 - 6, 19, keel_z, "minecraft:iron_block")
    for y in range(9, 19):
        b.set(DX1 - 14, y, keel_z, CHAIN)
    b.set(DX1 - 14, 8, keel_z, "minecraft:anvil[facing=north]")
    # --- The casting floor (the arena, south-east): iron plate, a ring channel of magma, crucibles of lava around it.
    AX, AZ, R = 52, 41, 10
    for x in range(AX - R - 2, AX + R + 3):
        for z in range(AZ - R - 2, AZ + R + 3):
            d = math.hypot(x - AX, z - AZ)
            if d <= R + 2.3:
                b.set(x, 0, z, "minecraft:magma_block" if R - 0.6 < d <= R + 0.6 else "minecraft:iron_block" if (x + z) % 4 == 0 else "minecraft:polished_blackstone_bricks"
                      if d < R else "minecraft:polished_blackstone")
    b.disk(AX, 0, AZ, 2.5, "minecraft:chiseled_polished_blackstone")
    for i in range(0, 360, 45):
        a = math.radians(i)
        x, z = round(AX + (R + 2) * math.cos(a)), round(AZ + (R + 2) * math.sin(a))
        if 0 < x < W and 0 < z < D:
            b.set(x, 1, z, "minecraft:lava_cauldron"); b.set(x, 2, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
            b.box(x, 3, z, x, 8, z, CHAIN); b.set(x, 9, z, "minecraft:iron_block") if False else None
    for (px, pz) in ((AX - R - 2, AZ - R - 2), (AX + R + 1, AZ - R - 2), (AX - R - 2, AZ + R + 1), (AX + R + 1, AZ + R + 1)):
        if 0 <= px <= W and 0 <= pz <= D:
            b.box(px, 1, pz, px, 9, pz, "minecraft:iron_block")
            b.set(px, 10, pz, "minecraft:blast_furnace[facing=north,lit=true]") if False else b.set(px, 10, pz, SMOKE)
    # the great crucible on the arena's edge
    b.cyl(AX + 7, AZ + 11, 2, 1, 4, "minecraft:iron_block", hollow=True)
    b.disk(AX + 7, 1, AZ + 11, 1, "minecraft:magma_block")
    b.box(AX + 7, 4, AZ + 11, AX + 7, 4, AZ + 11, "minecraft:lava_cauldron")
    # --- The stokers' bunkhouse between the dock and the hall.
    b.hall(42, 25, 56, 31, 0, 4, "minecraft:bricks", "minecraft:polished_blackstone_bricks", "minecraft:iron_block", floor="minecraft:spruce_planks",
           win=pane("orange"), doors=[("west", 3, 1, 3)], every=4, proud=False)
    b.gable_roof(42, 25, 56, 31, 4, COPPER, f"minecraft:{COPPER}", axis="x")
    for x in range(44, 56, 2):
        bed("gray", x, 1, 26, b, "south")
    b.set(55, 1, 30, BARREL); b.set(54, 1, 30, "minecraft:crafting_table"); b.set(49, 4, 28, HANG)
    # scrap stacks, coal and iron everywhere
    for (x, z) in ((60, 26), (44, 54), (2, 26), (60, 55)):
        b.sphere(x, 1, z, 2.3, "minecraft:iron_block", ry=1.6, upper=True); b.scatter(x - 3, z - 3, x + 3, z + 3, 1, ["minecraft:chain[axis=x,waterlogged=false]".replace("minecraft:chain", "minecraft:iron_chain"), "minecraft:anvil[facing=north]", BARREL], 0.25, rnd)
    for (x, z) in ((8, 26), (34, 28), (41, 50)):
        b.lamp_post(x, 1, z, "dark_oak", 4, LANTERN, arm="east")

    b.rogue(AX, 1, AZ, "boilerheart_gantz")
    b.crew("boiler_stoker", ((AX - 6, AZ - 5), (AX + 6, AZ - 5), (AX - 6, AZ + 5), (30, 18), (14, 16), (48, 28)))
    b.crew("boiler_stoker", ((22, 40),), y=-3)


# ============================================================ Nereus: the Abyssal Temple
@lair("abyssal_temple", "The Abyssal Temple", "nereus_vane", OCEANS + DEEP, "sea")
def _(b):
    rnd = random.Random(6)
    C = 32
    WL = 6                    # the sea's top layer; the temple floor (y = 8) stands 2 above it
    F = WL + 2
    PB, DP, P = "minecraft:prismarine_bricks", "minecraft:dark_prismarine", "minecraft:prismarine"
    corals = ["minecraft:tube_coral_block", "minecraft:brain_coral_block", "minecraft:fire_coral_block", "minecraft:horn_coral_block", "minecraft:bubble_coral_block"]
    def column(x, z, y_top, s=PB, w=2):
        b.box(x, -16, z, x + w - 1, y_top, z + w - 1, s)
    # --- The arena: a round platform on a drum rising out of the sea, with a star of prismarine set in it.
    R = 14
    b.skirt(C, C, R, -16, F - 1, [DP, PB, P, DP], rnd, spread=0.2)
    b.disk(C, F, C, R + 1, PB)
    b.disk(C, F, C, R, DP)
    for i in range(0, 360, 45):
        for r in range(2, R):
            a = math.radians(i)
            b.set(round(C + r * math.cos(a)), F, round(C + r * math.sin(a)), P)
    for r in (5, 10):
        for i in range(0, 360, 3):
            a = math.radians(i)
            b.set(round(C + r * math.cos(a)), F, round(C + r * math.sin(a)), "minecraft:sea_lantern" if i % 30 == 0 else PB)
    b.disk(C, F, C, 1.5, "minecraft:sea_lantern")
    for i in range(0, 360, 4):   # a low parapet with gaps for the causeway and sanctum
        a = math.radians(i)
        x, z = round(C + (R + 1) * math.cos(a)), round(C + (R + 1) * math.sin(a))
        if not (80 <= i <= 100 or 260 <= i <= 280 or 350 <= i or i <= 10 or 170 <= i <= 190):
            b.set(x, F + 1, z, "minecraft:prismarine_brick_slab[type=bottom,waterlogged=false]")
    # --- The colonnade (the landmark): twelve tall columns standing in the sea round the arena, joined by a ring at the top.
    RO = 24
    for i in range(0, 360, 30):
        a = math.radians(i)
        x, z = round(C + RO * math.cos(a)), round(C + RO * math.sin(a))
        column(x, z, 22)
        b.box(x - 1, 23, z - 1, x + 2, 23, z + 2, DP)
        b.set(x, 24, z, "minecraft:sea_lantern"); b.set(x + 1, 24, z + 1, "minecraft:sea_lantern")
        b.box(x, F + 4, z, x + 1, F + 4, z + 1, DP)
        for y in range(-16, WL - 1):
            if rnd.random() < 0.25:
                b.set(x + rnd.choice((-1, 2)), y, z + rnd.randint(0, 1), rnd.choice(corals))
    for i in range(0, 360):
        a = math.radians(i)
        b.set(round(C + 0.5 + RO * math.cos(a)), 23, round(C + 0.5 + RO * math.sin(a)), "minecraft:prismarine_brick_slab[type=bottom,waterlogged=false]") \
            if b.get(round(C + 0.5 + RO * math.cos(a)), 23, round(C + 0.5 + RO * math.sin(a))) is None else None
    # --- The causeway in from the south: a walk on columns, with lantern posts.
    for z in range(C + R, C + RO + 8):
        for x in range(C - 2, C + 3):
            b.set(x, F, z, PB if abs(x - C) == 2 else DP)
        if z % 4 == 0:
            column(C - 2, z, F - 1, PB, 1); column(C + 2, z, F - 1, PB, 1)
            b.set(C - 2, F + 1, z, wall_post("prismarine")); b.set(C - 2, F + 2, z, "minecraft:sea_lantern")
            b.set(C + 2, F + 1, z, wall_post("prismarine")); b.set(C + 2, F + 2, z, "minecraft:sea_lantern")
    b.box(C - 2, F + 1, C + RO + 6, C - 2, F + 7, C + RO + 6, PB); b.box(C + 2, F + 1, C + RO + 6, C + 2, F + 7, C + RO + 6, PB)
    b.box(C - 3, F + 8, C + RO + 6, C + 3, F + 8, C + RO + 6, DP); b.set(C, F + 9, C + RO + 6, "minecraft:sea_lantern")
    # --- The sanctum (his quarters, north): a domed hall on a drum, pews for the faithful, an altar with the conduit.
    SZ = C - R - 7
    b.skirt(C, SZ, 9, -16, F - 1, [DP, PB, P], rnd, spread=0.15)
    b.disk(C, F, SZ, 9, PB)
    b.cyl(C, SZ, 8, F + 1, F + 7, PB, hollow=True)
    b.disk(C, F, SZ, 7, DP)
    for i in range(0, 360, 30):
        a = math.radians(i)
        x, z = round(C + 8.6 * math.cos(a)), round(SZ + 8.6 * math.sin(a))
        b.box(x, F + 1, z, x, F + 7, z, DP)
        b.set(round(C + 8 * math.cos(a)), F + 4, round(SZ + 8 * math.sin(a)), "minecraft:light_blue_stained_glass")
    b.sphere(C, F + 8, SZ, 8, P, hollow=True, upper=True, ry=7)
    b.cyl(C, SZ, 1.3, F + 14, F + 16, AIR)   # oculus
    b.cyl(C, SZ, 2.3, F + 14, F + 14, DP, hollow=True)
    b.box(C - 2, F + 1, SZ + 6, C + 2, F + 5, SZ + 9, AIR)
    b.box(C - 3, F + 6, SZ + 8, C + 3, F + 6, SZ + 8, DP)
    b.box(C - 1, F, SZ + 8, C + 1, F, SZ + 16, DP)
    for z in range(SZ + 1, SZ + 6, 2):   # pews
        for x in list(range(C - 6, C - 1)) + list(range(C + 2, C + 7)):
            if math.hypot(x - C, z - SZ) < 7.2:
                b.set(x, F + 1, z, stair("prismarine", "south"))
    b.box(C - 2, F + 1, SZ - 6, C + 2, F + 1, SZ - 4, DP)
    b.set(C, F + 2, SZ - 5, "minecraft:conduit[waterlogged=false]")
    b.chest(C - 2, F + 2, SZ - 5, "abyssal_temple", "south")
    b.set(C + 2, F + 2, SZ - 5, candle(4, "cyan")); b.set(C - 1, F + 2, SZ - 4, candle(2, "light_blue"))
    for i in range(0, 360, 60):
        a = math.radians(i)
        b.hang_from(round(C + 5 * math.cos(a)), F + 9, round(SZ + 5 * math.sin(a)), "minecraft:sea_lantern")
    # --- The cultists' cells, east and west: small halls on the platform's flanks.
    for (hx0, hx1) in ((C - R - 9, C - R + 1), (C + R - 1, C + R + 9)):
        b.skirt((hx0 + hx1) / 2, C, 6, -16, F - 1, [DP, PB], rnd, spread=0.15)
        b.hall(hx0, C - 5, hx1, C + 5, F, 5, PB, DP, DP, trim=P, floor=DP, win=pane("cyan"), every=4,
               doors=[("east" if hx0 < C else "west", 4, 3, 3)], proud=False)
        b.hip_roof(hx0, C - 5, hx1, C + 5, F + 5, "prismarine_brick", P, ov=1, cap="minecraft:sea_lantern")
        for z in range(C - 4, C + 5, 2):
            bed("cyan", hx0 + 1 if hx0 < C else hx1 - 2, F + 1, z, b, "east" if hx0 < C else "west")
        b.set((hx0 + hx1) // 2, F + 4, C, "minecraft:sea_lantern")
        b.set((hx0 + hx1) // 2, F + 1, C + 4, BARREL); b.set((hx0 + hx1) // 2 + 1, F + 1, C + 4, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=false]")
    # Coral and pickles all over the drum, below the water only (above it, coral dies grey).
    for _ in range(260):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(R - 1, R + 6); y = rnd.randint(-12, WL - 1)
        x, z = round(C + r * math.cos(a)), round(C + r * math.sin(a))
        if b.get(x, y, z) is None and any(b.get(x + dx, y + dy, z + dz) not in (None, AIR) for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            b.set(x, y, z, rnd.choice(corals))
    b.waterline = WL

    b.rogue(C, F + 1, C, "nereus_vane")
    b.crew("abyssal_cultist", ((C - 7, C - 6), (C + 7, C - 6), (C - 7, C + 7), (C + 7, C + 7), (C, SZ + 2), (C - R - 4, C), (C + R + 4, C)), y=F + 1)


# ============================================================ the second band of rogues (more_rogue_lairs.py)
import more_rogue_lairs  # noqa: E402
more_rogue_lairs.add(lair, OCEANS, DEEP)


# ============================================================ the film villains (film_lairs.py)
import film_lairs  # noqa: E402
film_lairs.add(lair, OCEANS, DEEP)
import film_lairs_more  # noqa: E402
film_lairs_more.add(lair, OCEANS, DEEP)
import film_lairs_third  # noqa: E402
film_lairs_third.add(lair, OCEANS, DEEP)


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
    # The boss's own Rumor Poster, so you can call them out again for a rematch.
    return (1, 1, [item(f"opbosses:rumor_{boss}", 1)])


LOOT = {
    "scrapheap_reef": table((4, 7, [item(BERRY, 10, 4, 14), item("minecraft:iron_ingot", 10, 2, 6), item("minecraft:copper_ingot", 10, 4, 12),
                                    item("minecraft:iron_chain", 6, 1, 4), item("minecraft:gunpowder", 5, 1, 4), item("minecraft:golden_apple", 1),
                                    item("minecraft:compass", 2), item("minecraft:iron_axe", 3)]), rumor("saltjaw_rourke")),
    "lantern_house": table((4, 7, [item(BERRY, 10, 8, 20), item("minecraft:lantern", 8, 2, 6), item("minecraft:emerald", 6, 1, 4),
                                   item("minecraft:gold_ingot", 6, 1, 4), item("minecraft:potion", 4, 1, 2, {"type": "minecraft:set_potion", "id": "minecraft:invisibility"}),
                                   item("minecraft:ender_pearl", 3, 1, 2), item("minecraft:golden_apple", 2), item("minecraft:map", 3)]), rumor("corvina_fog_widow")),
    "fort_iron_tide": table((5, 8, [item(BERRY, 10, 10, 30), item("onepiece:seastone_ingot", 6, 1, 3), item("onepiece:seastone_cuffs", 3, 1, 1),
                                    item("minecraft:diamond", 5, 1, 3), item("minecraft:iron_ingot", 8, 2, 6), item("minecraft:gunpowder", 8, 2, 6),
                                    item("minecraft:golden_apple", 4, 1, 2), item("minecraft:diamond_sword", 2, 1, 1, ENCHANT)]), rumor("iron_tide_graves")),
    "hollow_shrine": table((5, 8, [item(BERRY, 10, 10, 30), item("minecraft:diamond_sword", 4, 1, 1, ENCHANT), item("minecraft:netherite_scrap", 3, 1, 1),
                                   item("minecraft:diamond", 5, 1, 3), item("minecraft:experience_bottle", 8, 2, 8), item("minecraft:cherry_sapling", 6, 1, 3),
                                   item("minecraft:golden_apple", 4, 1, 2)]), (1, 1, [item("minecraft:enchanted_book", 1, 1, 1, ENCHANT)]), rumor("hollow_ronin_tsurugi")),
    "shipbreakers_foundry": table((6, 10, [item(BERRY, 10, 24, 60), item("minecraft:iron_block", 6, 1, 3), item("minecraft:netherite_scrap", 4, 1, 2),
                                           item("minecraft:diamond", 6, 2, 5), item("minecraft:coal_block", 8, 2, 6), item("minecraft:netherite_ingot", 1),
                                           item("minecraft:enchanted_golden_apple", 1), item("minecraft:golden_apple", 5, 1, 3)]), rumor("boilerheart_gantz")),
    "abyssal_temple": table((6, 10, [item(BERRY, 10, 32, 64), item("minecraft:heart_of_the_sea", 3), item("minecraft:nautilus_shell", 6, 1, 4),
                                     item("minecraft:trident", 2, 1, 1, ENCHANT), item("minecraft:diamond", 6, 2, 6), item("minecraft:netherite_ingot", 2),
                                     item("minecraft:enchanted_golden_apple", 2), item("minecraft:totem_of_undying", 2), item("minecraft:prismarine_crystals", 6, 2, 8)]),
                            (2, 2, [item("minecraft:enchanted_book", 1, 1, 1, ENCHANT)]), rumor("nereus_vane")),
}

# One rogue lair per this many chunks on average (the main mod's hard lairs are 40 / 14).
SPACING, SEPARATION, SALT = 44, 16, 1408172101
# The film villains' lairs are their own set, so adding them didn't make the rogue lairs any rarer. With 14 of them the
# spacing is a little tighter, so each one stays about as common as when there were ten (40 / 15).
GROUPS = {"rogue_lairs": (SPACING, SEPARATION, SALT), "film_lairs": (35, 13, 1408172177)}
LOOT.update(more_rogue_lairs.LOOT)
LOOT.update(film_lairs.LOOT)
LOOT.update(film_lairs_more.LOOT)
LOOT.update(film_lairs_third.LOOT)
# ...and never right next to one: a film lair stays at least 10 chunks from any rogue lair.
EXCLUDE = {"film_lairs": {"exclusion_zone": {"other_set": "opbosses:rogue_lairs", "chunk_count": 10}}}


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def main(root, only=()):
    D = os.path.join(root, 'src/main/resources/data/opbosses')
    unknown = set(only) - {l['name'] for l in LAIRS}
    if unknown:
        sys.exit('No such lair: ' + ', '.join(sorted(unknown)))
    if not only:   # a full run starts clean, so a lair taken out leaves nothing behind
        for p in ('structure', 'worldgen/template_pool', 'worldgen/structure', 'worldgen/structure_set', 'tags/worldgen/biome/has_structure', 'loot_table/chests'):
            shutil.rmtree(f'{D}/{p}', ignore_errors=True)
    bosses = {b['id'] for b in json.load(open(os.path.join(root, 'src/main/resources/opbosses/bosses.json')))['bosses']}
    kits = {k['id'] for k in json.load(open(os.path.join(root, 'src/main/resources/opbosses/crews.json')))['kits']}
    rows = []
    for l in LAIRS:
        if only and l['name'] not in only:
            continue
        b = Lair()
        b.boss = l['boss']
        l['build'](b)
        for (eid, *_r, data) in b.entities:
            if eid == "opbosses:rogue_boss":
                assert data["Character"] in bosses, (l['name'], data["Character"])
            elif "Tags" in data:
                kit = [t for t in data["Tags"] if t.startswith(KIT_TAG_PREFIX)][0][len(KIT_TAG_PREFIX):]
                assert kit in kits, (l['name'], kit)
        name = l['name']
        if l['place'] == "land":
            soften_ground(b)
            clear_ground(b)
        size, my = b.save(f'{D}/structure/{name}.nbt')
        st = {"type": "minecraft:jigsaw", "biomes": f"#opbosses:has_structure/{name}", "step": "surface_structures",
              "spawn_overrides": {"monster": {"bounding_box": "piece", "spawns": []}, "ambient": {"bounding_box": "piece", "spawns": []}},
              "terrain_adaptation": getattr(b, "adaptation", "beard_box"), "start_pool": f"opbosses:{name}", "size": 1, "max_distance_from_center": 80, "use_expansion_hack": False}
        # The jigsaw puts a piece's lowest level 1 below surface + start_height (a single element's ground level delta is 1),
        # so start_height 0 puts y = 0 on the top block of the ground, or of the sea for a sea lair's waterline.
        if l['place'] == "land":
            st["project_start_to_heightmap"] = "WORLD_SURFACE_WG"; st["start_height"] = {"absolute": my}
        else:   # "sea": the waterline level sits at the sea's surface
            st["project_start_to_heightmap"] = "WORLD_SURFACE_WG"; st["start_height"] = {"absolute": -b.waterline + my}; st["terrain_adaptation"] = "none"
        write(f'{D}/worldgen/structure/{name}.json', st)
        write(f'{D}/worldgen/template_pool/{name}.json', {"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
            "element_type": "minecraft:single_pool_element", "location": f"opbosses:{name}", "processors": {"processors": []}, "projection": "rigid"}}]})
        write(f'{D}/tags/worldgen/biome/has_structure/{name}.json', {"replace": False, "values": [
            v if v.startswith('#') or v.startswith('minecraft:') else {"id": v, "required": False} for v in l['biomes']]})
        write(f'{D}/loot_table/chests/{name}.json', LOOT[name])
        rows.append((name, l['title'], l['boss'], size, len(b.entities) - 1))
    for group, (spacing, separation, salt) in GROUPS.items():
        write(f'{D}/worldgen/structure_set/{group}.json', {
            "structures": [{"structure": f"opbosses:{l['name']}", "weight": 1} for l in LAIRS if l['group'] == group],
            "placement": dict({"type": "minecraft:random_spread", "spacing": spacing, "separation": separation, "salt": salt},
                              **EXCLUDE.get(group, {}))})
    for r in rows:
        print('%-22s %-28s boss %-22s size %-14s crew %d' % (r[0], r[1], r[2], r[3], r[4]))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.', sys.argv[2:])
