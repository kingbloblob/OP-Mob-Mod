"""Finer building parts for the lairs, so a lair reads as built rather than boxed (ryan: "a little simple and blocky"):
real stair roofs on timber townhouses, round towers with stair cones, piers and string courses that give a wall depth,
trees and rocks with an uneven outline, and ground that fades into the land round it instead of ending in a square.
Everything here works on a Lair canvas `b`. Coordinates as in kit.py: x east, y up, z south."""
import math

from kit import AIR, LANTERN, HANG, BARREL, log, leaves, pane
from parts import stair, slab, wall_post, carpet, fence, trap, OPP

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
FLOWERS = ["minecraft:poppy", "minecraft:dandelion", "minecraft:oxeye_daisy", "minecraft:cornflower", "minecraft:azure_bluet"]


def wall_run(m, axis):
    """A low wall that joins its neighbours along `axis`: a balustrade, not a row of posts."""
    ew, ns = ("low", "none") if axis == "x" else ("none", "low")
    return f"minecraft:{m}_wall[east={ew},north={ns},south={ns},west={ew},up=false,waterlogged=false]"


def mix(b, x0, y0, z0, x1, y1, z1, was, blocks, rnd, chance=0.3):
    """Breaks up a large surface: swaps some `was` blocks for related ones, in small patches rather than single speckles."""
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if b.get(x, y, z) == was and rnd.random() < chance:
                    b.set(x, y, z, rnd.choice(blocks))


def noise(x, z, seed=0):
    """Smooth value noise from 0 to 1, about 8 blocks to a bump."""
    def corner(i, j):
        n = (i * 374761393 + j * 668265263 + seed * 2147483647) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return (n & 0xFFFF) / 65535.0
    fx, fz = x / 8.0, z / 8.0
    i, j = math.floor(fx), math.floor(fz)
    u, v = fx - i, fz - j
    u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
    top = corner(i, j) * (1 - u) + corner(i + 1, j) * u
    bottom = corner(i, j + 1) * (1 - u) + corner(i + 1, j + 1) * u
    return top * (1 - v) + bottom * v


def fade_edges(b, W, D, seed=1, band=9, corner=16):
    """Cuts the square off a land lair: past an uneven, round-cornered line the lair's own ground is taken away and left
    to the land, and b.natural tells clear_ground to leave those columns alone (it would cut a hill off square there)."""
    natural = set()
    for x in range(W + 1):
        for z in range(D + 1):
            ex, ez = min(x, W - x), min(z, D - z)
            edge = min(ex, ez)
            if ex < corner and ez < corner:   # rounded corners
                edge = corner - math.hypot(corner - ex, corner - ez)
            if edge >= band * noise(x, z, seed):
                continue
            if (b.get(x, 0, z) or "").split("[")[0] not in SOFT_GROUND:
                continue   # water, paving and so on stay
            if any(s != AIR and s.split("[")[0] not in GROUND_COVER for p, s in _column(b, x, z)):
                continue   # something stands here: keep what it stands on
            for y in range(-2, 4):
                if (x, y, z) in b.blocks and (y <= 0 or b.blocks[(x, y, z)].split("[")[0] in GROUND_COVER):
                    del b.blocks[(x, y, z)]
            natural.add((x, z))
    b.natural = natural


SOFT_GROUND = {"minecraft:grass_block", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:moss_block", "minecraft:sand", "minecraft:rooted_dirt"}
GROUND_COVER = {"minecraft:short_grass", "minecraft:tall_grass", "minecraft:fern", "minecraft:poppy", "minecraft:dandelion",
                "minecraft:oxeye_daisy", "minecraft:cornflower", "minecraft:azure_bluet", "minecraft:sweet_berry_bush"}


def _column(b, x, z):
    return [((x, y, z), b.blocks[(x, y, z)]) for y in range(1, 30) if (x, y, z) in b.blocks]


def ground_patches(b, W, D, rnd, seed=3, keep=()):
    """Ground with some life in it: grass with drifts of moss, coarse dirt and podzol where the noise says, not speckle."""
    for x in range(W + 1):
        for z in range(D + 1):
            if b.get(x, 0, z) not in ("minecraft:grass_block", "minecraft:coarse_dirt"):
                continue
            n = noise(x * 1.6, z * 1.6, seed)
            s = "minecraft:grass_block"
            if n > 0.8:
                s = "minecraft:podzol"
            elif n > 0.72:
                s = "minecraft:coarse_dirt"
            elif n < 0.16:
                s = "minecraft:moss_block"
            b.set(x, 0, z, s)


def flower_drifts(b, W, D, rnd, seed=5, density=0.5):
    """Flowers and long grass in drifts: thick in places, none in others."""
    for x in range(W + 1):
        for z in range(D + 1):
            if b.get(x, 0, z) not in ("minecraft:grass_block", "minecraft:moss_block") or b.get(x, 1, z) not in (None, AIR):
                continue
            n = noise(x * 1.3 + 40, z * 1.3, seed)
            if n > 0.66 and rnd.random() < density:
                b.set(x, 1, z, FLOWERS[int(noise(x, z, seed + 1) * 5) % 5])
            elif n > 0.38 and rnd.random() < density * 0.35:
                b.set(x, 1, z, "minecraft:short_grass")


def oak(b, x, y, z, h, rnd, kind="oak", spread=3.2):
    """A tree with a shape: a trunk that flares at the foot, branches going out, and uneven clumps of leaves on them."""
    wood, leaf = log(kind), leaves(kind)
    for yy in range(y, y + h):
        b.set(x, yy, z, wood)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):   # root flare
        if rnd.random() < 0.7:
            b.set(x + dx, y, z + dz, log(kind, "x" if dx else "z"))
    tips = [(x, y + h, z)]
    for i in range(rnd.randint(3, 4)):
        a = rnd.random() * math.tau
        by = y + h - 3 + i % 3
        n = rnd.randint(2, 3)
        px, pz = x, z
        for k in range(1, n + 1):
            px, pz = x + round(math.cos(a) * k), z + round(math.sin(a) * k)
            b.set(px, by + k // 2, pz, log(kind, "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"))
        tips.append((px, by + n // 2, pz))
    for (tx, ty, tz) in tips:
        r = spread * (0.75 + rnd.random() * 0.4)
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                for dy in range(-2, 4):
                    d = math.hypot(dx, dz) ** 2 / (r * r) + (dy * 1.3 / r) ** 2
                    if d <= 1 and not (d > 0.72 and rnd.random() < 0.5) and b.get(tx + dx, ty + dy, tz + dz) in (None, AIR):
                        b.set(tx + dx, ty + dy, tz + dz, leaf)


def palm(b, x, y, z, h, rnd):
    """A leaning palm: the trunk curves one way, and long fronds droop off the crown on all sides."""
    a = rnd.random() * math.tau
    lx, lz = math.cos(a), math.sin(a)
    px, pz = x, z
    for i in range(h):
        lean = (i / h) ** 2 * 3
        px, pz = x + round(lx * lean), z + round(lz * lean)
        b.set(px, y + i, pz, log("jungle"))
        if i and (b.get(px, y + i - 1, pz) in (None, AIR)):
            b.set(px, y + i - 1, pz, log("jungle"))
    top = y + h
    leaf = leaves("jungle")
    b.set(px, top, pz, leaf)
    for k in range(12):
        fa = k * math.tau / 12 + rnd.random() * 0.2
        n = rnd.randint(4, 6)
        for i in range(1, n + 1):
            fx, fz = px + round(math.cos(fa) * i), pz + round(math.sin(fa) * i)
            fy = top + (1 if i <= 2 else 0) - max(0, i - 3)
            b.set(fx, fy, fz, leaf)
            if i in (2, 3):   # a frond is broad near the crown
                b.set(fx + round(-math.sin(fa)), fy, fz + round(math.cos(fa)), leaf)
    for (dx, dz) in ((1, 0), (0, 1)):
        b.set(px + dx, top - 1, pz + dz, "minecraft:cocoa[age=2,facing=%s]" % ("west" if dx else "north"))


def bush(b, x, y, z, rnd, kind="oak", r=1.6):
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in range(0, 2):
                if math.hypot(dx, dz) + dy * 0.9 <= r + rnd.random() * 0.6 and b.get(x + dx, y + dy, z + dz) in (None, AIR):
                    b.set(x + dx, y + dy, z + dz, leaves(kind))


def rock(b, x, y, z, r, rnd, blocks=("minecraft:stone", "minecraft:andesite", "minecraft:mossy_cobblestone", "minecraft:cobblestone")):
    """A boulder: a lumpy, flattened mound with slabs round its foot."""
    ri = int(r) + 2
    for dx in range(-ri, ri + 1):
        for dz in range(-ri, ri + 1):
            top = r * 0.9 - math.hypot(dx, dz * 1.2) * 0.8 + rnd.random() * 0.9
            for dy in range(0, int(top) + 1):
                if top > 0:
                    b.set(x + dx, y + dy, z + dz, rnd.choice(blocks))
            if -0.8 < top <= 0 and b.get(x + dx, y, z + dz) in (None, AIR) and rnd.random() < 0.5:
                b.set(x + dx, y, z + dz, slab("cobblestone"))


def stair_cone(b, cx, cz, r, y, fam, fill, finial=None, steep=2):
    """A round tower's roof: a real cone of stairs that flares out over the wall, `steep` levels for each block it narrows."""
    R0 = r + 1.6
    levels = int(R0 * steep) + 1
    for i in range(levels):
        R = R0 * (1 - i / levels) ** 1.15
        inner = R - 1.05
        ri = int(R) + 1
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz)
                if d > R + 0.15:
                    continue
                if d >= inner:
                    if abs(dx) >= abs(dz):
                        f = "west" if dx > 0 else "east"
                    else:
                        f = "north" if dz > 0 else "south"
                    b.set(cx + dx, y + i, cz + dz, stair(fam, f) if d else fill)
                elif i and d >= inner - 1:
                    b.set(cx + dx, y + i, cz + dz, fill)
    top = y + levels
    b.set(cx, top - 1, cz, fill)
    if finial:
        b.set(cx, top, cz, finial)
        b.set(cx, top + 1, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    return top


def pier(b, x, z, side, y0, y1, s, cap=None, width=1):
    """A pier standing 1 proud of a wall on `side`, topped with a stair so it dies back into the wall."""
    dx, dz = DIRS[side]
    for w in range(-(width // 2), width // 2 + 1):
        px, pz = x + dx + (w if dz else 0), z + dz + (w if dx else 0)
        b.box(px, y0, pz, px, y1, pz, s)
        if cap:
            b.set(px, y1 + 1, pz, stair(cap, OPP[side]))


def corbels(b, x0, z0, x1, z1, y, fam):
    """A row of upside-down stairs under an overhang, all round a rectangle: the jetty's or the parapet's shadow line."""
    for x in range(x0, x1 + 1):
        b.set(x, y, z0, stair(fam, "south", "top")); b.set(x, y, z1, stair(fam, "north", "top"))
    for z in range(z0 + 1, z1):
        b.set(x0, y, z, stair(fam, "east", "top")); b.set(x1, y, z, stair(fam, "west", "top"))


def string_course(b, x0, z0, x1, z1, y, fam, skip=lambda x, z: False):
    """A moulding round the outside of a rectangle: upside-down stairs 1 proud of the wall, broken by `skip`."""
    for x in range(x0, x1 + 1):
        if not skip(x, z0 - 1) and b.get(x, y, z0 - 1) in (None, AIR):
            b.set(x, y, z0 - 1, stair(fam, "south", "top"))
        if not skip(x, z1 + 1) and b.get(x, y, z1 + 1) in (None, AIR):
            b.set(x, y, z1 + 1, stair(fam, "north", "top"))
    for z in range(z0, z1 + 1):
        if not skip(x0 - 1, z) and b.get(x0 - 1, y, z) in (None, AIR):
            b.set(x0 - 1, y, z, stair(fam, "east", "top"))
        if not skip(x1 + 1, z) and b.get(x1 + 1, y, z) in (None, AIR):
            b.set(x1 + 1, y, z, stair(fam, "west", "top"))


def shutters(b, x, y, z, side, h=2, wood="spruce"):
    """Open shutters either side of a window in a wall facing `side`, and a window box of flowers under it."""
    dx, dz = DIRS[side]
    sx, sz = (1, 0) if dz else (0, 1)
    for yy in range(y, y + h):
        for k, f in ((-1, side), (1, side)):
            b.set(x + dx + sx * k, yy, z + dz + sz * k, trap(wood, _hinge(side, k), "bottom", True))
    b.set(x + dx, y - 1, z + dz, trap(wood, OPP[side], "top", False))
    b.set(x + dx, y, z + dz, "minecraft:flowering_azalea" if (x + z) % 2 else "minecraft:azalea")
    b.set(x + dx, y - 1, z + dz, "minecraft:moss_block")
    for k in (-1, 1):
        pass


def _hinge(side, k):
    """An open trapdoor lying flat against the wall beside the window."""
    if side in ("north", "south"):
        return "east" if k < 0 else "west"
    return "south" if k < 0 else "north"


def dormer(b, x, y, z, side, fam, wall, post):
    """A small gabled window coming out of a roof slope that faces `side`."""
    dx, dz = DIRS[side]
    sx, sz = (1, 0) if dz else (0, 1)
    for k in (-1, 1):
        b.box(x + sx * k, y, z + sz * k, x + sx * k, y + 1, z + sz * k, post)
    b.box(x, y, z, x, y + 1, z, pane())
    for i in (1, 2):   # the cheeks back into the roof
        for k in (-1, 0, 1):
            b.box(x - dx * i + sx * k, y, z - dz * i + sz * k, x - dx * i + sx * k, y + 1, z - dz * i + sz * k, wall)
    fa, fb = (("east", "west") if dz else ("south", "north"))
    for i in (0, -1, -2):
        b.set(x + dx * i - sx * 2, y + 2, z + dz * i - sz * 2, stair(fam, fa))
        b.set(x + dx * i + sx * 2, y + 2, z + dz * i + sz * 2, stair(fam, fb))
        b.set(x + dx * i - sx, y + 3, z + dz * i - sz, stair(fam, fa))
        b.set(x + dx * i + sx, y + 3, z + dz * i + sz, stair(fam, fb))
        b.set(x + dx * i, y + 3, z + dz * i, wall)
        b.set(x + dx * i, y + 4, z + dz * i, slab(fam))
        b.box(x + dx * i - sx, y + 2, z + dz * i - sz, x + dx * i + sx, y + 2, z + dz * i + sz, wall)


def chimney(b, x, y, z, h, rnd, brick="minecraft:bricks", smoke=True):
    b.box(x, y, z, x, y + h - 1, z, brick)
    b.set(x, y + h, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]" if smoke else slab("brick"))
    for (dx, dz, f) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
        b.set(x + dx, y + h - 1, z + dz, stair("brick", f, "top"))


def townhouse(b, x0, z0, w, d, y, rnd, plaster="minecraft:white_terracotta", timber="dark_oak", fam="waxed_cut_copper", fill=None, door="south",
              base="minecraft:stone_bricks", storeys=2, shutter="spruce"):
    """A two-storey timber-framed house: stone ground floor, an upper floor jettied out on corbels, a steep stair roof
    with a dormer and a chimney, shutters, a window box, a lit, stepped doorway, and furniture inside."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    post = log(timber)
    beam_x, beam_z = log(timber, "x"), log(timber, "z")
    h1, h2 = 4, 4
    b.room(x0, y, z0, x1, y + h1, z1, base, floor="minecraft:spruce_planks")
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        b.box(x, y + 1, z, x, y + h1, z, post)
    ux0, uz0, ux1, uz1 = x0 - 1, z0 - 1, x1 + 1, z1 + 1
    uy = y + h1
    corbels(b, ux0, uz0, ux1, uz1, uy - 1 + 0, timber)
    b.room(ux0, uy, uz0, ux1, uy + h2, uz1, plaster, floor="minecraft:spruce_planks")
    # the frame: sill and head beams, corner posts, studs and braces in the plaster
    for yy in (uy, uy + h2):
        for x in range(ux0, ux1 + 1):
            b.set(x, yy, uz0, beam_x); b.set(x, yy, uz1, beam_x)
        for z in range(uz0, uz1 + 1):
            b.set(ux0, yy, z, beam_z); b.set(ux1, yy, z, beam_z)
    for (x, z) in ((ux0, uz0), (ux1, uz0), (ux0, uz1), (ux1, uz1)):
        b.box(x, uy, z, x, uy + h2, z, post)
    midx, midz = (ux0 + ux1) // 2, (uz0 + uz1) // 2
    for x in (ux0 + 2, ux1 - 2):
        for z in (uz0, uz1):
            b.box(x, uy + 1, z, x, uy + h2 - 1, z, post)
    for z in (uz0 + 2, uz1 - 2):
        for x in (ux0, ux1):
            b.box(x, uy + 1, z, x, uy + h2 - 1, z, post)
    # upstairs windows with shutters on the two long faces
    for (x, z, s) in ((midx, uz0, "north"), (midx, uz1, "south"), (ux0, midz, "west"), (ux1, midz, "east")):
        b.box(x, uy + 2, z, x, uy + 3, z, pane())
        dx, dz = DIRS[s]
        b.set(x + dx, uy + 1, z + dz, trap(shutter, OPP[s], "top"))
    # roof
    axis = "x" if w >= d else "z"
    ridge = b.gable_roof(ux0, uz0, ux1, uz1, uy + h2 + 1, fam, fill or plaster, axis=axis, eave=True)
    # ground floor door, lintel, step and lamp
    dx, dz = DIRS[door]
    mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
    fx, fz = {"south": (mx, z1), "north": (mx, z0), "east": (x1, mz), "west": (x0, mz)}[door]
    sx, sz = (1, 0) if dz else (0, 1)
    b.box(fx, y + 1, fz, fx, y + 2, fz, AIR)
    b.set(fx, y + 1, fz, f"minecraft:{timber}_door[facing={OPP[door]},half=lower,hinge=left,open=false,powered=false]")
    b.set(fx, y + 2, fz, f"minecraft:{timber}_door[facing={OPP[door]},half=upper,hinge=left,open=false,powered=false]")
    for k in (-1, 1):
        b.box(fx + sx * k, y + 1, fz + sz * k, fx + sx * k, y + 3, fz + sz * k, post)
    b.set(fx, y + 3, fz, log(timber, "x" if dz else "z"))
    b.set(fx + dx, y + 1, fz + dz, slab("stone_brick"))
    b.set(fx + dx + sx * 2, y + 3, fz + dz + sz * 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    b.set(fx + dx + sx * 2, y + 2, fz + dz + sz * 2, fence(timber))
    b.set(fx + dx + sx * 2, y + 1, fz + dz + sz * 2, fence(timber))
    # ground floor windows, off the door side
    for (x, z, s) in ((x0, mz, "west"), (x1, mz, "east"), (mx, z0, "north"), (mx, z1, "south")):
        if s == door:
            continue
        b.box(x, y + 2, z, x, y + 3, z, pane())
    # inside: a stair-ladder, a table, a bed upstairs
    b.set(x0 + 1, y + 1, z0 + 1, BARREL)
    b.table(x0 + 2, y + 1, z0 + 2, "spruce", "minecraft:brown_carpet", w=2)
    for yy in range(y + 1, uy + 1):
        b.set(x1 - 1, yy, z0 + 1, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(x1 - 1, uy, z0 + 1, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(mx, y + h1 - 1, mz, HANG)
    return ridge


def planter(b, x, y, z, stone="stone_brick", tree=True, kind="azalea", rnd=None):
    """A square stone tub with a small clipped tree."""
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            b.set(x + dx, y, z + dz, slab(stone, "top") if (dx or dz) else "minecraft:moss_block")
    b.set(x, y + 1, z, log("oak"))
    b.set(x, y + 2, z, log("oak"))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            b.set(x + dx, y + 3, z + dz, leaves("azalea") if (dx + dz) % 2 else leaves("flowering_azalea"))
    b.set(x, y + 4, z, leaves("flowering_azalea"))


def fountain(b, cx, y, cz, r=4, stone="minecraft:polished_andesite", fam="polished_andesite", jet="minecraft:waxed_copper_block"):
    """A round fountain: a stepped basin, water in it, a pedestal with a dish, water falling from the top."""
    for dx in range(-r - 1, r + 2):
        for dz in range(-r - 1, r + 2):
            d = math.hypot(dx, dz)
            if d <= r - 0.6:
                b.set(cx + dx, y, cz + dz, "minecraft:water[level=0]")
                b.set(cx + dx, y - 1, cz + dz, "minecraft:prismarine_bricks")
            elif d <= r + 0.5:
                b.set(cx + dx, y, cz + dz, stone)
                b.set(cx + dx, y + 1, cz + dz, slab(fam))
    b.box(cx, y, cz, cx, y + 4, cz, jet)
    for (dx, dz, f) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
        b.set(cx + dx, y + 3, cz + dz, stair(fam, f, "top"))
        b.set(cx + dx, y + 4, cz + dz, "minecraft:water[level=0]")
        b.set(cx + dx * 2, y + 4, cz + dz * 2, slab(fam, "top"))
    b.set(cx, y + 5, cz, "minecraft:water[level=0]")


def bench(b, x, y, z, side, wood="spruce"):
    """A bench 3 long with its back to `side`."""
    dx, dz = DIRS[side]
    sx, sz = (1, 0) if dz else (0, 1)
    for k in (-1, 0, 1):
        b.set(x + sx * k, y, z + sz * k, stair(wood, side))
    b.set(x - sx * 2, y, z - sz * 2, trap(wood, "north" if sx == 0 else "west", "bottom", True))
    b.set(x + sx * 2, y, z + sz * 2, trap(wood, "south" if sx == 0 else "east", "bottom", True))


SUITS = {
    "heart": ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"],
    "diamond": ["0001000", "0011100", "0111110", "1111111", "0111110", "0011100", "0001000"],
    "spade": ["0001000", "0011100", "0111110", "1111111", "1111111", "0101010", "0011100"],
    "club": ["0011100", "0011100", "1111111", "1111111", "1101011", "0001000", "0011100"],
}


def suit(b, cx, y, cz, name, s):
    """A card suit laid into the paving, 7 blocks across."""
    rows = SUITS[name]
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c == "1":
                b.set(cx - 3 + i, y, cz - len(rows) // 2 + j, s)


def ring_course(b, cx, cz, r, y, fam):
    """A moulding round a round tower: upside-down stairs just outside a wall of radius r."""
    for a in range(0, 360, 6):
        x, z = round(cx + (r + 1) * math.cos(math.radians(a))), round(cz + (r + 1) * math.sin(math.radians(a)))
        dx, dz = x - cx, z - cz
        if b.get(x, y, z) in (None, AIR):
            f = ("west" if dx > 0 else "east") if abs(dx) >= abs(dz) else ("north" if dz > 0 else "south")
            b.set(x, y, z, stair(fam, f, "top"))


def beam_ring(b, x0, z0, x1, z1, y, wood, only=None):
    """A timber rail along the walls of a rectangle, stopping at openings."""
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if b.get(x, y, z) not in (None, AIR) and (only is None or b.get(x, y, z) == only):
                b.set(x, y, z, log(wood, "x"))
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            if b.get(x, y, z) not in (None, AIR) and (only is None or b.get(x, y, z) == only):
                b.set(x, y, z, log(wood, "z"))


def railing(b, x0, z0, x1, z1, y, wood, gaps=()):
    """A fence round a rectangle at height y, with `gaps` (x, z) left open."""
    cells = [(x, z) for x in range(x0, x1 + 1) for z in (z0, z1)] + [(x, z) for z in range(z0, z1 + 1) for x in (x0, x1)]
    for (x, z) in cells:
        if (x, z) not in gaps and b.get(x, y, z) in (None, AIR):
            b.set(x, y, z, fence(wood))


def bamboo(b, x, y, z, rnd, n=8, r=3):
    """A clump of bamboo, thick in the middle."""
    for _ in range(n):
        px, pz = x + rnd.randint(-r, r), z + rnd.randint(-r, r)
        if b.get(px, y, pz) in (None, AIR) and (b.get(px, y - 1, pz) or "").split("[")[0] in SOFT_GROUND:
            for yy in range(y, y + rnd.randint(4, 8)):
                if b.get(px, yy, pz) not in (None, AIR):
                    break
                b.set(px, yy, pz, "minecraft:bamboo[age=0,leaves=none,stage=0]")


def vines(b, rnd, chance=0.1, kind="jungle"):
    """Vines hanging off the underside of leaves."""
    leaf = leaves(kind)
    for (x, y, z), s in list(b.blocks.items()):
        if s == leaf and b.get(x, y - 1, z) in (None, AIR) and rnd.random() < chance:
            b.set(x, y - 1, z, "minecraft:vine[east=false,north=false,south=false,up=true,west=false]")


CONES = {"minecraft:red_concrete": ("red_nether_brick", "minecraft:red_nether_bricks")}


def cone_family(roof):
    """The stair family closest to a tower's roof block."""
    if roof in CONES:
        return CONES[roof]
    name = roof.split(":")[1].split("[")[0]
    for end in ("_bricks", "_tiles", "_planks"):
        if name.endswith(end):
            return (name[: -len(end)] + end[:-1], roof)
    for (word, fam, fill) in (("black", "blackstone", "minecraft:blackstone"), ("dark", "dark_oak", "minecraft:dark_oak_planks"), ("gray", "deepslate_tile", "minecraft:deepslate_tiles"),
                              ("blue", "warped", "minecraft:warped_planks"), ("cyan", "waxed_oxidized_cut_copper", "minecraft:waxed_oxidized_cut_copper"),
                              ("green", "waxed_oxidized_cut_copper", "minecraft:waxed_oxidized_cut_copper"), ("purple", "purpur", "minecraft:purpur_block"),
                              ("white", "quartz", "minecraft:quartz_block"), ("yellow", "smooth_sandstone", "minecraft:smooth_sandstone"), ("orange", "cut_copper", "minecraft:cut_copper")):
        if word in name:
            return (fam, fill)
    return ("dark_oak", "minecraft:dark_oak_planks")


WEATHERED = {
    "minecraft:stone_bricks": ["minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:andesite"],
    "minecraft:white_concrete": ["minecraft:calcite", "minecraft:polished_diorite"],
    "minecraft:calcite": ["minecraft:diorite", "minecraft:polished_diorite"],
    "minecraft:quartz_bricks": ["minecraft:smooth_quartz", "minecraft:calcite"],
    "minecraft:spruce_planks": ["minecraft:stripped_spruce_wood[axis=y]", "minecraft:dark_oak_planks"],
    "minecraft:dark_oak_planks": ["minecraft:spruce_planks", "minecraft:stripped_dark_oak_wood[axis=y]"],
    "minecraft:bricks": ["minecraft:granite", "minecraft:brown_terracotta"],
    "minecraft:gray_concrete": ["minecraft:andesite", "minecraft:polished_andesite"],
    "minecraft:smooth_sandstone": ["minecraft:sandstone", "minecraft:cut_sandstone"],
    "minecraft:cut_red_sandstone": ["minecraft:red_sandstone", "minecraft:smooth_red_sandstone"],
    "minecraft:polished_blackstone_bricks": ["minecraft:cracked_polished_blackstone_bricks", "minecraft:polished_blackstone"],
    "minecraft:polished_deepslate": ["minecraft:deepslate_bricks", "minecraft:cracked_deepslate_bricks"],
    "minecraft:white_terracotta": ["minecraft:smooth_quartz", "minecraft:calcite"],
    "minecraft:red_terracotta": ["minecraft:bricks", "minecraft:brown_terracotta"],
    "minecraft:green_terracotta": ["minecraft:moss_block", "minecraft:lime_terracotta"],
}
FAMILIES = {
    "minecraft:stone_bricks": "stone_brick", "minecraft:white_concrete": "quartz", "minecraft:calcite": "polished_diorite", "minecraft:quartz_bricks": "quartz",
    "minecraft:spruce_planks": "spruce", "minecraft:dark_oak_planks": "dark_oak", "minecraft:bricks": "brick", "minecraft:smooth_sandstone": "smooth_sandstone",
    "minecraft:cut_red_sandstone": "smooth_red_sandstone", "minecraft:polished_blackstone_bricks": "polished_blackstone_brick", "minecraft:polished_deepslate": "polished_deepslate",
}


def wall_family(wall):
    return FAMILIES.get(wall, "polished_blackstone_brick")


def weather(b, x0, y0, z0, x1, y1, z1, was):
    """Age on a wall: drifts of related blocks where the noise says, so it isn't one flat colour."""
    alts = WEATHERED.get(was)
    if not alts:
        return
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if b.get(x, y, z) == was:
                    n = noise(x * 3 + z * 3, y * 3, 21)
                    if n > 0.62:
                        b.set(x, y, z, alts[int(n * 100) % len(alts)])


def dress_edges(b, W, D, rnd, n=14):
    """Rocks and bushes in the empty ground near a land lair's edge, so its rim isn't bare."""
    placed = 0
    for _ in range(n * 30):
        if placed >= n:
            break
        x, z = rnd.randint(3, W - 3), rnd.randint(3, D - 3)
        if min(x, W - x, z, D - z) > 14:
            continue
        ground = (b.get(x, 0, z) or "").split("[")[0]
        if ground not in SOFT_GROUND:
            continue
        if any(b.get(x + dx, y, z + dz) not in (None, AIR) for dx in range(-3, 4) for dz in range(-3, 4) for y in (1, 2, 3)):
            continue
        if ground == "minecraft:sand":
            rock(b, x, 1, z, 1.4 + rnd.random(), rnd, blocks=("minecraft:sandstone", "minecraft:smooth_sandstone", "minecraft:cut_sandstone"))
        elif placed % 2:
            rock(b, x, 1, z, 1.4 + rnd.random(), rnd)
        else:
            bush(b, x, 1, z, rnd, "oak", 1.8)
        placed += 1


def line(b, p, q, wood="dark_oak"):
    """A rope from p to q through empty cells: it steps one axis at a time, and each fence joins the next, so it reads as a
    line and not a row of loose posts."""
    cells = [tuple(p)]
    c = list(p)
    total = max(1, sum(abs(q[i] - p[i]) for i in range(3)))
    done = [0, 0, 0]
    while tuple(c) != tuple(q):
        i = min(range(3), key=lambda k: (done[k] + 1) / abs(q[k] - p[k]) if q[k] != p[k] and done[k] < abs(q[k] - p[k]) else 9e9)
        c[i] += 1 if q[i] > p[i] else -1
        done[i] += 1
        cells.append(tuple(c))
    for k, cell in enumerate(cells):
        if b.get(*cell) not in (None, AIR):
            continue
        near = {cells[j] for j in (k - 1, k + 1) if 0 <= j < len(cells)}
        x, y, z = cell
        st = {"east": (x + 1, y, z) in near, "west": (x - 1, y, z) in near, "north": (x, y, z - 1) in near, "south": (x, y, z + 1) in near}
        b.set(x, y, z, f"minecraft:{wood}_fence[east={str(st['east']).lower()},north={str(st['north']).lower()},south={str(st['south']).lower()},waterlogged=false,west={str(st['west']).lower()}]")


def sail(b, x, cz, y0, y1, h0, h1, s, belly=3, wood="spruce"):
    """A square sail on a yard: the head stays on the yard, the cloth bellies forward (+x) like it is full of wind, the
    sides taper up the mast and the foot is cut in a curve. A spar across the top carries it."""
    def off(z, y):
        t = (y - y0) / max(1, y1 - y0)
        half = h0 + (h1 - h0) * t
        zn = min(1.0, abs(z) / max(1.0, half))
        return belly * (1 - zn * zn) * math.sin(math.pi * min(1.0, t * 0.82 + 0.14)) ** 0.9
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        half = h0 + (h1 - h0) * t
        for z in range(-int(half), int(half) + 1):
            zn = abs(z) / max(1.0, half)
            if y < y0 + (1 - zn * zn):
                continue   # the curved foot
            o = off(z, y)
            near = min(off(z + 1, y), off(z - 1, y), off(z, min(y + 1, y1)), off(z, max(y - 1, y0)), o)
            for xx in range(round(near), round(o) + 1):   # no gaps where the cloth curves away
                b.set(x + xx, y, cz + z, s)
    for z in range(-int(h1) - 2, int(h1) + 3):
        b.set(x, y1 + 1, cz + z, log(wood, "z"))
    for z in (-int(h1) - 2, int(h1) + 2):
        b.set(x, y1 + 1, cz + z, slab(wood))


def rig(b, x0, cz, dy, W, masts, s, rail):
    """Masts with two or three sails each, shrouds down to the rails, and stays between the mastheads."""
    tops = []
    for (mx, mh) in masts:
        x = x0 + mx
        tiers = 3 if mh >= 24 else 2 if mh >= 13 else 1
        lo, hi = dy + 5, dy + mh - 3
        share = {1: (1.0,), 2: (0.58, 0.42), 3: (0.42, 0.33, 0.25)}[tiers]
        y = lo
        full = W / 2 - 0.5
        widths = (full, full * 0.76, full * 0.56, full * 0.42)
        for i in range(tiers):
            top = y + round((hi - lo) * share[i]) - 1
            sail(b, x + 1, cz, y, top, widths[i], widths[i + 1] + 0.5, s, belly=2 if i == 0 else 1)
            y = top + 2   # the next sail starts right above this yard
        # shrouds from the first yard's height down to the rail, either side, just abaft the mast
        hy = lo + round((hi - lo) * share[0])
        for k in (1, 3, 5):
            for side in (-1, 1):
                rx = x - k
                rz = rail(rx)
                if rz:
                    line(b, (x, hy, cz + side), (rx, dy + 2, cz + side * rz))
        tops.append((x, dy + mh - 1))
    for (a, c) in zip(tops, tops[1:]):
        line(b, (a[0], a[1], cz), (c[0], c[1] - 4, cz))


def hull(b, x0, y0, z0, L, W, wall, deck, depth):
    """A ship's body with a shape: full in the middle, fine at the bow, the stem and stern raked out as they rise, and the
    sides coming back in a little above the widest point. Returns the deck level."""
    cz = z0 + W // 2
    for y in range(y0, y0 + depth + 1):
        t = (y - y0) / max(1, depth)
        stem = round((1 - t) * L * 0.11)
        post = round((1 - t) * L * 0.05)
        profile = (0.42 + 0.58 * min(1.0, t / 0.68)) * (1 - 0.09 * max(0.0, (t - 0.68) / 0.32))
        for x in range(x0 + post, x0 + L - stem):
            f = (x - x0 - post) / max(1, L - stem - post - 1)
            taper = 1.0 - max(0.0, (f - 0.62) / 0.38) ** 1.7 * 0.94 - max(0.0, (0.1 - f) / 0.1) ** 1.5 * 0.34
            half = max(0, round((W / 2 - 0.5) * profile * taper))
            for z in range(cz - half, cz + half + 1):
                edge = abs(z - cz) == half or y == y0
                b.set(x, y, z, wall if (edge or y < y0 + depth) else deck)
                if y == y0 + depth:
                    b.set(x, y, z, deck if abs(z - cz) < half else wall)
            if y == y0 + depth:
                for z in (cz - half, cz + half):
                    b.set(x, y + 1, z, fence("dark_oak"))
    return y0 + depth


def rail_half(b, cz, dy, wall, deck):
    """How far the deck reaches either side of the centre line at a given x."""
    def half(x):
        zs = [z for z in range(cz - 40, cz + 41) if b.get(x, dy, z) in (wall, deck)]
        return (cz - min(zs)) if zs else 0
    return half


def strakes(b):
    """Planking lines along each hull: every third course a different wood."""
    for (x0, y0, z0, L, W, wall, dy) in getattr(b, "ships", []):
        alt = WEATHERED.get(wall, ["minecraft:spruce_planks"])[0]
        for (x, y, z), s in list(b.blocks.items()):
            if s == wall and x0 - 1 <= x <= x0 + L and z0 - 1 <= z <= z0 + W and y0 < y < dy and (y - y0) % 3 == 1:
                if b.get(x, y, z - 1) in (None, AIR) or b.get(x, y, z + 1) in (None, AIR):
                    b.set(x, y, z, alt)


def tatter(b, s, rnd, others):
    """Old sails: the foot in rags, long tears down the cloth and stains, but still plainly a sail."""
    cells = [p for p, v in b.blocks.items() if v == s]
    for p in cells:
        n = noise(p[0] * 2 + p[2] * 3, p[1] * 2, 31)
        if 0.88 < n < 0.9:
            b.set(*p, AIR)   # a long, thin tear
        elif n > 0.6:
            b.set(*p, others[int(n * 100) % len(others)])
    foot = [p for p in cells if b.get(*p) not in (None, AIR) and b.get(p[0], p[1] - 1, p[2]) in (None, AIR)]
    for p in foot:   # a ragged foot, one block deep
        if rnd.random() < 0.3:
            b.set(*p, AIR)
