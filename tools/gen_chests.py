#!/usr/bin/env python3
"""Draws each lair's own chest: the block model, its textures, blockstate and item model.

    python3 tools/gen_chests.py src/main/resources

One chest per lair (the block is opbosses:<lair>_chest, registered from LairChests.CHESTS in Java). They're static
models (no opening lid) made of boxes, like any block model: 16 units = 1 block, x east, y up, z south, and the
front faces north (z = 0); the blockstate turns it to face the player. Textures are 16x16 and painted where the boxes
sit: a face shows the part of its texture under it, so a front texture is a picture of the chest's front (row 0 is
the top, y = 16). A box with full=True shows the whole texture on each face instead (dials, emblems).
Nothing is see-through, so the blocks need no special render layer.
"""
import json
import math
import os
import random
import sys

from PIL import Image

S = 16


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def new(base, noise=0.08, seed=0):
    rnd = random.Random(seed)
    img = Image.new('RGBA', (S, S))
    c = rgb(base)
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), shade(c, 1 - noise / 2 + noise * rnd.random()) + (255,))
    return img


def put(img, x, y, c):
    if 0 <= x < S and 0 <= y < S:
        img.putpixel((int(x), int(y)), (rgb(c) if isinstance(c, str) else c) + (255,))


def rect(img, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(img, x, y, c)


def frame(img, x0, y0, x1, y1, c):
    for x in range(x0, x1 + 1):
        put(img, x, y0, c); put(img, x, y1, c)
    for y in range(y0, y1 + 1):
        put(img, x0, y, c); put(img, x1, y, c)


def planks(base, seam, seed=0, rows=4):
    img = new(base, 0.14, seed)
    rnd = random.Random(seed)
    for y in range(S):
        if y % rows == rows - 1:
            for x in range(S):
                put(img, x, y, seam)
        elif rnd.random() < 0.15:
            put(img, rnd.randrange(S), y, shade(rgb(base), 0.8))
    return img


def metal(base, rivet, seed=0, edge=None):
    img = new(base, 0.1, seed)
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14), (7, 1), (7, 14), (1, 7), (14, 7)):
        put(img, x, y, rivet)
    if edge:
        frame(img, 0, 0, 15, 15, edge)
    return img


def lacquer(base, seed=0):
    img = new(base, 0.04, seed)
    for i in range(S):
        put(img, i, i // 3, shade(rgb(base), 1.25))   # a shine across it
    return img


# ---------------------------------------------------------------- the chests
# Each chest: name (shown in game), textures {key: Image}, boxes [(from, to, faces, extras)].
# faces is one texture key for every face, or a dict of front/back/side/top/bottom (missing ones use 'all').
CHESTS = {}


def chest(cid, name):
    def deco(fn):
        CHESTS[cid] = dict(name=name, build=fn)
        return fn
    return deco


def box(f, t, faces, **extra):
    return (f, t, faces, extra)


@chest("scrapheap_reef", "Rourke's Sea Chest")
def _():
    # A weathered sea chest hauled off the reef: green-slimed planks, rusted iron straps, barnacles, a chain lock.
    wood = planks('#5a4630', '#2e2418', 1)
    for (x, y) in ((2, 13), (3, 14), (9, 15), (12, 12), (5, 10), (13, 6)):
        put(wood, x, y, '#4a6a48'); put(wood, x + 1, y, '#3e5a3c')   # algae
    front = planks('#5a4630', '#2e2418', 2)
    for x in range(S):
        put(front, x, 15, '#4a6a48')
    rust = metal('#7a4a2a', '#c08050', 3)
    for (x, y) in ((3, 5), (9, 11), (12, 3)):
        put(rust, x, y, '#a85a28')
    barn = new('#d8d0bc', 0.2, 4)
    put(barn, 7, 7, '#5a5048'); put(barn, 8, 8, '#5a5048')
    chain = new('#4a4a50', 0.1, 5)
    for y in range(0, S, 2):
        for x in range(S):
            put(chain, x, y, '#2a2a30')
    tex = dict(wood=wood, front=front, rust=rust, barn=barn, chain=chain)
    boxes = [
        box([1, 0, 1], [15, 9, 15], dict(all='wood', front='front')),
        box([1, 9, 1], [15, 13, 15], dict(all='wood', front='front')),
        box([2, 13, 2], [14, 14.5, 14], 'wood'),
        box([3, -0.01, 0.5], [5, 14, 15.5], 'rust'),
        box([11, -0.01, 0.5], [13, 14, 15.5], 'rust'),
        box([2, 14.5, 3], [5, 15, 13], 'rust'),
        box([11, 14.5, 3], [14, 15, 13], 'rust'),
        box([6.5, 7, 0.3], [9.5, 11, 1], 'rust'),
        box([7.5, 3.5, 0.1], [8.5, 7, 0.6], 'chain'),
        box([14.6, 2, 4], [15.6, 4, 6], 'barn'),
        box([0.4, 5, 9], [1.4, 6.5, 10.5], 'barn'),
        box([9, 14.5, 9], [10.5, 15.5, 10.5], 'barn'),
        box([2, 0.5, 0.6], [3.5, 2, 1.1], 'barn'),
    ]
    return tex, boxes


@chest("lantern_house", "The Widow's Casket")
def _():
    # A narrow black casket with silver fittings, her wide-brimmed hat on the lid and her lantern hanging off the corner.
    black = lacquer('#1e1a24', 6)
    front = lacquer('#1e1a24', 7)
    for x in range(2, 14):
        put(front, x, 8, '#6a5a8a')   # violet piping where the lid meets the body
    silver = metal('#b8b8c4', '#ffffff', 8)
    glow = new('#ffe8a0', 0.1, 9)
    rect(glow, 6, 4, 9, 11, '#fff8d0')
    violet = new('#6a5a8a', 0.1, 60)
    tex = dict(black=black, front=front, silver=silver, glow=glow, violet=violet)
    boxes = [
        box([2, 0, 1], [14, 8, 15], dict(all='black', front='front')),
        box([1.5, 8, 0.5], [14.5, 11, 15.5], dict(all='black', front='front')),
        box([3, 11, 2], [13, 12, 14], 'black'),
        box([-0.5, 12, -0.5], [16.5, 12.6, 16.5], 'black'),      # her wide-brimmed hat on the lid, brim past the edges
        box([5, 12.6, 5], [11, 15.5, 11], 'black'),
        box([4.9, 12.6, 4.9], [11.1, 13.6, 11.1], 'violet'),     # hatband
        box([13.6, 9.5, 0.2], [14.4, 10.3, 1.2], 'silver'),       # lantern bracket on the corner
        box([12.8, 5.5, -0.6], [15.2, 9.5, 1.8], 'glow', light=14),  # her lantern
        box([12.6, 9.3, -0.8], [15.4, 9.8, 2], 'silver'),
        box([12.6, 5.2, -0.8], [15.4, 5.7, 2], 'silver'),
        box([1.6, 0, 0.6], [2.6, 8, 1.6], 'silver'),
        box([13.4, 0, 0.6], [14.4, 8, 1.6], 'silver'),
        box([1.6, 0, 14.4], [2.6, 8, 15.4], 'silver'),
        box([13.4, 0, 14.4], [14.4, 8, 15.4], 'silver'),
        box([6.5, 4.5, 0.4], [9.5, 8.5, 1], 'silver'),
        box([7.2, 5.2, 0.2], [8.8, 7.6, 0.5], 'glow', light=12),
    ]
    return tex, boxes


@chest("fort_iron_tide", "Marine Strongbox")
def _():
    # A Navy strongbox: white steel, navy bands, a gold anchor badge and gold handles.
    white = metal('#e8e8ec', '#9a9aa8', 10, edge='#b8b8c4')
    front = metal('#e8e8ec', '#9a9aa8', 11)
    for y in range(6, 16):
        put(front, 1, y, '#28304a'); put(front, 14, y, '#28304a')
    gold = '#d8b040'
    for y in range(8, 14):
        put(front, 7, y, gold); put(front, 8, y, gold)        # anchor shank
    for x in range(5, 11):
        put(front, x, 9, gold)                                 # stock
    for x in (5, 6, 9, 10):
        put(front, x, 13 - abs(x - 7.5) // 2, gold)            # arms
    put(front, 4, 12, gold); put(front, 11, 12, gold)
    rect(front, 7, 7, 8, 7, gold)                              # ring
    navy = metal('#28304a', '#c8c8d0', 12)
    goldt = new('#d8b040', 0.2, 13)
    tex = dict(white=white, front=front, navy=navy, gold=goldt)
    boxes = [
        box([1, 0, 1], [15, 10, 15], dict(all='white', front='front')),
        box([0.8, 10, 0.8], [15.2, 13, 15.2], 'navy'),
        box([1, 13, 1], [15, 13.6, 15], 'white'),
        box([15, 5, 6], [15.8, 6, 10], 'gold'),
        box([0.2, 5, 6], [1, 6, 10], 'gold'),
        box([7, 9.5, 0.4], [9, 12, 0.8], 'gold'),
    ]
    return tex, boxes


@chest("hollow_shrine", "Karabitsu Armour Chest")
def _():
    # A samurai's armour chest: red lacquer on short black legs, a black lid with a gold crest, gold corner fittings.
    red = lacquer('#a01e1e', 14)
    black = lacquer('#1a1414', 15)
    lidtop = lacquer('#1a1414', 16)
    for a in range(0, 360, 30):
        put(lidtop, 8 + 3 * math.cos(math.radians(a)), 8 + 3 * math.sin(math.radians(a)), '#d8b048')   # mon
    put(lidtop, 8, 8, '#d8b048'); put(lidtop, 7, 7, '#d8b048')
    gold = new('#d8b048', 0.2, 17)
    rope = new('#c83030', 0.2, 18)
    for y in range(0, S, 3):
        for x in range(S):
            put(rope, x, y, '#e8c060')
    tex = dict(red=red, black=black, lidtop=lidtop, gold=gold, rope=rope)
    boxes = [box([x, 0, z], [x + 2, 3, z + 2], 'black') for x in (1.5, 12.5) for z in (1.5, 12.5)]
    boxes += [
        box([1, 3, 1], [15, 11, 15], 'red'),
        box([0.5, 11, 0.5], [15.5, 14, 15.5], dict(all='black', top='lidtop')),
    ]
    boxes += [box([x, 3, z], [x + 1.6, 11.2, z + 1.6], 'gold') for x in (0.8, 13.6) for z in (0.8, 13.6)]
    boxes += [
        box([7, 9, 0.2], [9, 12.5, 0.6], 'gold'),
        box([15.4, 7, 7.5], [16, 10.5, 8.5], 'rope'),
        box([0, 7, 7.5], [0.6, 10.5, 8.5], 'rope'),
    ]
    return tex, boxes


@chest("shipbreakers_foundry", "Boiler Safe")
def _():
    # A riveted boiler-iron safe with a brass combination dial, a glowing firebox slot, a steam pipe and a gauge.
    iron = metal('#3a3a40', '#8a8a90', 19)
    front = metal('#3a3a40', '#8a8a90', 20)
    frame(front, 2, 2, 13, 13, '#26262a')     # the door
    dial = new('#c89838', 0.12, 21)
    for a in range(0, 360, 15):
        r = 7 if a % 45 else 6
        put(dial, 7.5 + r * math.cos(math.radians(a)), 7.5 + r * math.sin(math.radians(a)), '#5a4010')
    rect(dial, 6, 6, 9, 9, '#8a6820'); rect(dial, 7, 2, 8, 6, '#5a4010')
    fire = new('#ff8a20', 0.3, 22)
    for x in range(0, S, 3):
        for y in range(S):
            put(fire, x, y, '#2a1a10')
    brass = new('#c89838', 0.15, 23)
    gauge = new('#f0ece0', 0.05, 24)
    frame(gauge, 0, 0, 15, 15, '#c89838'); frame(gauge, 1, 1, 14, 14, '#c89838')
    for i in range(6):
        put(gauge, 8 + i, 8 - i, '#c02020')
    tex = dict(iron=iron, front=front, dial=dial, fire=fire, brass=brass, gauge=gauge)
    boxes = [
        box([1, 0, 1], [15, 13, 15], dict(all='iron', front='front')),
        box([5.5, 5.5, 0.3], [10.5, 10.5, 1], dict(all='brass', front='dial'), full=True),
        box([4, 1.5, 0.5], [12, 3.5, 1.05], 'fire', full=True, light=10),
        box([13.4, 2.5, 0.4], [14.6, 5, 1], 'brass'),
        box([13.4, 8.5, 0.4], [14.6, 11, 1], 'brass'),
        box([10, 13, 9], [12, 16, 11], 'iron'),
        box([9.5, 15.5, 8.5], [12.5, 16.5, 11.5], 'brass'),
        box([3, 13, 3.5], [6.5, 16, 4.5], dict(all='brass', front='gauge'), full=True),
    ]
    return tex, boxes


@chest("abyssal_temple", "Abyssal Clam")
def _():
    # A giant clam: ridged teal shells, a pearl peeking out of the lip, coral growing on its sides.
    shell = new('#3a8a8a', 0.1, 25)
    for x in range(0, S, 3):
        for y in range(S):
            put(shell, x, y, '#2a6a70')
            put(shell, x + 1, y, '#5ab0a8')
    top = new('#3a8a8a', 0.1, 26)
    for a in range(-60, 61, 20):
        for r in range(2, 16):
            put(top, 8 + r * math.sin(math.radians(a)) * 0.6, 15 - r * math.cos(math.radians(a)), '#2a6a70')
    pearl = new('#f4f0ec', 0.06, 27)
    rect(pearl, 3, 3, 6, 6, '#ffffff')
    lip = new('#f0b8c0', 0.1, 28)
    coral = new('#e86a7a', 0.25, 29)
    tex = dict(shell=shell, top=top, pearl=pearl, lip=lip, coral=coral)
    boxes = [
        box([0.5, 0, 1], [15.5, 5.5, 15.5], dict(all='shell', top='top')),
        box([1, 5.5, 0.8], [15, 6.5, 15.2], 'lip'),
        box([1, 6.5, 1.5], [15, 10, 15.5], dict(all='shell', top='top')),
        box([3, 10, 3], [13, 11.5, 14.5], dict(all='shell', top='top')),
        box([6.5, 5, 0.3], [9.5, 7.5, 1.6], 'pearl', full=True),
        box([14.6, 0, 10], [16, 4.5, 11.4], 'coral'),
        box([13.8, 3.5, 11.4], [15.2, 6, 12.6], 'coral'),
        box([0, 0, 3], [1.4, 3, 4.4], 'coral'),
        box([0.6, 2.5, 4.4], [1.6, 4.5, 5.4], 'coral'),
    ]
    return tex, boxes


@chest("sunken_kasbah", "Rahd's Plunder Coffer")
def _():
    # A sandstone-and-brass coffer bound in his chains, a heavy padlock on the front and gold coins heaped on the lid.
    sand = new('#d8b880', 0.12, 70)
    for y in (3, 8, 13):
        for x in range(S):
            put(sand, x, y, '#b89860')   # courses of carved stone
    front = new('#d8b880', 0.12, 71)
    for x in range(S):
        put(front, x, 2, '#b89860'); put(front, x, 13, '#b89860')
    for x in range(3, 13):
        put(front, x, 5 + (x % 2), '#8a6a3a')   # a zigzag carved band
    brass = metal('#c8a040', '#fff0a0', 72)
    chain = new('#6a6a72', 0.1, 73)
    for y in range(S):
        for x in range(S):
            if (x + y) % 3 == 0:
                put(chain, x, y, '#3a3a40')
    lock = new('#5a5a62', 0.1, 74)
    rect(lock, 6, 6, 9, 9, '#2a2a30'); put(lock, 7, 8, '#c8a040')
    coins = new('#f0c840', 0.3, 75)
    for (x, y) in ((2, 3), (7, 9), (12, 5), (4, 12), (10, 13)):
        put(coins, x, y, '#a07a20')
    tex = dict(sand=sand, front=front, brass=brass, chain=chain, lock=lock, coins=coins)
    boxes = [
        box([1, 0, 2], [15, 9, 14], dict(all='sand', front='front')),
        box([0.6, 9, 1.6], [15.4, 12, 14.4], 'brass'),
        box([1.5, 12, 2.5], [14.5, 13, 13.5], 'sand'),
        box([3, 13, 4], [9, 14.2, 10], 'coins'),                  # coins heaped on the lid
        box([8, 13, 7], [12, 13.8, 11], 'coins'),
        box([4, -0.01, 1.4], [5.5, 13.2, 14.6], 'chain'),         # his chains around it
        box([10.5, -0.01, 1.4], [12, 13.2, 14.6], 'chain'),
        box([6, 4.5, 0.6], [10, 9.5, 1.6], 'lock', full=True),    # padlock
        box([7, 9.5, 1], [9, 11, 1.4], 'chain'),
        box([0.5, -0.01, 1.5], [2, 2, 3], 'brass'), box([14, -0.01, 1.5], [15.5, 2, 3], 'brass'),
        box([0.5, -0.01, 13], [2, 2, 14.5], 'brass'), box([14, -0.01, 13], [15.5, 2, 14.5], 'brass'),
    ]
    return tex, boxes


@chest("gilded_wake", "The Cursed Hoard")
def _():
    # A sea-rotted black chest with gold bands, barnacles and weed, overflowing gold, and the curse glowing out of the lock.
    wood = planks('#2a2620', '#141210', 76)
    for (x, y) in ((1, 14), (6, 12), (11, 15), (14, 10)):
        put(wood, x, y, '#3a6a3a'); put(wood, x, y - 1, '#3a6a3a')   # weed
    front = planks('#2a2620', '#141210', 77)
    gold = new('#e8c040', 0.2, 78)
    hoard = new('#f0c840', 0.35, 79)
    for (x, y) in ((3, 4), (8, 2), (12, 9), (5, 11), (10, 13), (14, 3)):
        put(hoard, x, y, '#ffffff' if (x + y) % 2 else '#40f0d0')   # glints and a cursed shimmer
    glow = new('#40f0d0', 0.15, 80)
    barn = new('#c8c0a8', 0.25, 81)
    put(barn, 7, 7, '#504840')
    tex = dict(wood=wood, front=front, gold=gold, hoard=hoard, glow=glow, barn=barn)
    boxes = [
        box([1, 0, 2], [15, 8, 14], dict(all='wood', front='front')),
        box([1, 8, 2], [15, 11, 14], dict(all='wood', front='front')),
        box([0.8, 11, 1.8], [15.2, 11.6, 14.2], 'gold'),
        box([2, 11, 3], [14, 13.5, 13], 'hoard'),                 # the lid can't shut over the gold
        box([4, 13.5, 5], [11, 14.8, 11], 'hoard'),
        box([7, 14.8, 7], [9.5, 15.6, 9.5], 'hoard'),
        box([0.8, -0.01, 4], [15.2, 11.2, 5], 'gold'),            # gold bands
        box([0.8, -0.01, 11], [15.2, 11.2, 12], 'gold'),
        box([6.5, 5, 1.4], [9.5, 9, 2], 'gold'),
        box([7.3, 5.6, 1.1], [8.7, 7.6, 1.5], 'glow', light=10),  # the curse through the keyhole
        box([12.5, 1, 1.3], [14.5, 3, 2], 'barn'), box([1.5, 6, 1.3], [3, 7.5, 2], 'barn'),
        box([14.6, 3, 8], [15.5, 5, 10], 'barn'),
    ]
    return tex, boxes


@chest("leviathan_pens", "Sea King Skull Chest")
def _():
    # The skull of a Sea King the tamer couldn't break, hollowed into a chest: bone jaws with fangs, a red crest, scales.
    bone = new('#e4dcc4', 0.12, 82)
    for (x, y) in ((3, 4), (11, 9), (6, 13)):
        put(bone, x, y, '#b0a890')
    front = new('#e4dcc4', 0.12, 83)
    for x in range(S):
        put(front, x, 8, '#3a2a20')                              # where the jaws close
    for x in range(1, 15, 2):
        put(front, x, 7, '#ffffff'); put(front, x + 1, 9, '#ffffff')   # fangs
    rect(front, 3, 2, 5, 4, '#202020'); rect(front, 10, 2, 12, 4, '#202020')   # eye sockets
    put(front, 4, 3, '#f8e040'); put(front, 11, 3, '#f8e040')
    scales = new('#3a7a8a', 0.1, 84)
    for y in range(S):
        for x in range(S):
            if (x + (y % 2) * 2) % 4 == 0:
                put(scales, x, y, '#2a5a68')
    crest = new('#d84a3a', 0.15, 85)
    rope = new('#8a6a40', 0.15, 86)
    for i in range(S):
        put(rope, i, i, '#5a4020')
    tex = dict(bone=bone, front=front, scales=scales, crest=crest, rope=rope)
    boxes = [
        box([1, 0, 1], [15, 8, 15], dict(all='bone', front='front')),
        box([0.5, 8, 0.5], [15.5, 12, 15.5], dict(all='bone', front='front')),
        box([2, 12, 3], [14, 13, 14], 'scales'),
        box([7.5, 12, 2], [8.5, 16, 14], 'crest'),               # the crest along the top
        box([-0.3, 9, 5], [0.7, 13, 9], 'crest'), box([15.3, 9, 5], [16.3, 13, 9], 'crest'),   # fin ears
        box([2, 0, 0.2], [3, 6, 1], 'bone'), box([13, 0, 0.2], [14, 6, 1], 'bone'),           # tusks
        box([0.8, 3, 0.8], [15.2, 4, 15.2], 'rope'),             # his rope still lashed round it
    ]
    return tex, boxes


@chest("laboratory_null", "Prototype Containment Pod")
def _():
    # A steel pod with hazard stripes and a round window on a glowing Pacifista core, cables on the sides.
    steel = metal('#8a96a4', '#d8e0e8', 87, edge='#5a6676')
    front = metal('#8a96a4', '#d8e0e8', 88)
    for x in range(S):
        put(front, x, 14, '#202020' if (x // 2) % 2 else '#f0c020'); put(front, x, 15, '#202020' if (x // 2) % 2 == 0 else '#f0c020')
    window = new('#204050', 0.1, 89)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 7.5, y - 7.5)
            if r < 7.5:
                put(window, x, y, '#a8f0ff' if r < 3 else '#60e0ff' if r < 5.5 else '#3a6a7a')
            else:
                put(window, x, y, '#5a6676')
    stripes = new('#f0c020', 0.05, 90)
    for y in range(S):
        for x in range(S):
            if ((x + y) // 3) % 2:
                put(stripes, x, y, '#202020')
    cable = new('#2a2a30', 0.1, 91)
    for y in range(0, S, 3):
        for x in range(S):
            put(cable, x, y, '#c83a3a')
    lamp = new('#ff3030', 0.1, 92)
    tex = dict(steel=steel, front=front, window=window, stripes=stripes, cable=cable, lamp=lamp)
    boxes = [
        box([1.5, 0, 1.5], [14.5, 1.5, 14.5], 'stripes'),
        box([2, 1.5, 2], [14, 12, 14], dict(all='steel', front='front')),
        box([1, 12, 1], [15, 13.5, 15], 'steel'),
        box([4, 13.5, 4], [12, 14.5, 12], 'steel'),
        box([4, 4, 1.4], [12, 12, 2], 'window', full=True, light=12),   # the core behind the glass
        box([0.4, 2, 6], [2, 11, 8], 'cable'), box([14, 2, 8], [15.6, 11, 10], 'cable'),
        box([7, 14.5, 7], [9, 15.5, 9], 'lamp', light=8),               # warning light on top
    ]
    return tex, boxes


@chest("gran_tesoro", "Tesoro's Gold Vault")
def _():
    # Solid gold, a roulette wheel for a lock, gold bars and a stack of casino chips on the lid.
    gold = new('#e8c040', 0.18, 30)
    for i in range(S):
        put(gold, i, (i * 5) % S, '#fff0a0')
    bright = new('#f4d050', 0.15, 31)
    frame(bright, 0, 0, 15, 15, '#c8a030')
    wheel = new('#e8c040', 0.05, 32)
    for y in range(S):
        for x in range(S):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            if 2.5 < r < 7.2:
                seg = int((math.degrees(math.atan2(dy, dx)) + 180) // 30)
                put(wheel, x, y, '#c01e28' if seg % 2 else '#1a1a1e')
            elif r <= 2.5:
                put(wheel, x, y, '#f4d050')
    rect(wheel, 7, 0, 8, 2, '#ffffff')   # the ball
    bar = new('#f0c838', 0.1, 33)
    frame(bar, 0, 0, 15, 15, '#c09020')
    chip = new('#c01e28', 0.05, 34)
    for y in range(0, S, 4):
        for x in range(S):
            put(chip, x, y, '#ffffff')
    tex = dict(gold=gold, bright=bright, wheel=wheel, bar=bar, chip=chip)
    boxes = [
        box([1, 0, 1], [15, 10, 15], 'gold'),
        box([0.7, 10, 0.7], [15.3, 13, 15.3], 'bright'),
        box([4.5, 2.5, 0.3], [11.5, 9.5, 1], dict(all='gold', front='wheel'), full=True),
        box([3, 13, 4], [7, 14.5, 7], 'bar'),
        box([8, 13, 4], [12, 14.5, 7], 'bar'),
        box([5.5, 14.5, 4.5], [9.5, 16, 6.5], 'bar'),
        box([10, 13, 9.5], [12.5, 15.5, 12], 'chip'),
        box([6, 13, 10], [8.5, 14, 12.5], 'chip'),
    ]
    return tex, boxes


@chest("elegia_stage", "Uta's Music Box")
def _():
    # A white-and-red music box: gold music note on the lid, a crank on the side, pink notes along the front.
    white = lacquer('#f4f0f4', 35)
    front = lacquer('#f4f0f4', 36)
    for x in range(S):
        put(front, x, 9, '#d83040'); put(front, x, 15, '#d83040')
    for (x, y) in ((2, 11), (7, 10), (12, 11)):   # eighth notes: a round head, a stem and a flag
        rect(front, x, y + 2, x + 1, y + 3, '#c02860')
        for yy in range(y - 1, y + 3):
            put(front, x + 1, yy, '#c02860')
        put(front, x + 2, y - 1, '#c02860'); put(front, x + 2, y, '#c02860')
    red = lacquer('#c82838', 37)
    gold = new('#e8c040', 0.15, 38)
    tex = dict(white=white, front=front, red=red, gold=gold)
    boxes = [
        box([1, 0, 2], [15, 8, 14], dict(all='white', front='front')),
        box([0.5, 8, 1.5], [15.5, 11, 14.5], 'red'),
        box([2, 11, 3], [14, 11.5, 13], 'white'),
        box([7.5, 11.5, 6.5], [11, 14, 9.5], 'gold'),          # a big gold eighth note: head,
        box([7.5, 14, 7.5], [8.5, 19, 8.5], 'gold'),          # stem
        box([5, 18, 7.5], [7.5, 19, 8.5], 'gold'),             # and flag (to the viewer's right: -x)
        box([5, 16.5, 7.5], [6, 18, 8.5], 'gold'),
        box([15, 4, 7.5], [16, 5, 8.5], 'gold'),
        box([16, 2, 7.5], [17, 5, 8.5], 'gold'),
        box([1.5, -0.01, 2.5], [3, 0.6, 4], 'gold'),
        box([13, -0.01, 2.5], [14.5, 0.6, 4], 'gold'),
        box([1.5, -0.01, 12], [3, 0.6, 13.5], 'gold'),
        box([13, -0.01, 12], [14.5, 0.6, 13.5], 'gold'),
    ]
    return tex, boxes


@chest("end_point", "Neo Marine Arms Crate")
def _():
    # A black steel arms crate with seastone corners, purple bands and a NEO stencil.
    black = metal('#1e2028', '#5a5a68', 39)
    front = metal('#1e2028', '#5a5a68', 40)
    P = '#9a6ad0'
    letters = {'N': ['X..X', 'XX.X', 'X.XX', 'X..X', 'X..X'], 'E': ['XXX', 'X..', 'XX.', 'X..', 'XXX'],
               'O': ['XXX', 'X.X', 'X.X', 'X.X', 'XXX']}
    for (cx, letter) in ((2, 'N'), (7, 'E'), (11, 'O')):   # rows 8..12, under the clasp
        for dy, row in enumerate(letters[letter]):
            for dx, ch in enumerate(row):
                if ch == 'X':
                    put(front, cx + dx, 8 + dy, P)
    lid = metal('#1e2028', '#5a5a68', 41)
    for x in range(S):
        put(lid, x, 6, P); put(lid, x, 7, P); put(lid, 6, x, P); put(lid, 7, x, P)
    stone = new('#3a4a4a', 0.2, 42)
    band = new('#8a5ab8', 0.12, 43)
    tex = dict(black=black, front=front, lid=lid, stone=stone, band=band)
    boxes = [
        box([1, 0, 1], [15, 11, 15], dict(all='black', front='front')),
        box([0.6, 11, 0.6], [15.4, 13, 15.4], dict(all='band', top='lid')),
    ]
    boxes += [box([x, 0, z], [x + 2, 11, z + 2], 'stone') for x in (0.5, 13.5) for z in (0.5, 13.5)]
    boxes += [
        box([5, 13, 7], [11, 14, 9], 'stone'),
        box([7, 10, 0.4], [9, 12.5, 0.9], 'stone'),
    ]
    return tex, boxes


@chest("ironclad_colosseum", "Gashapon Scrap Crate")
def _():
    # A crate welded from scrap plates, bolted patches, a pipe, and a gashapon capsule on top.
    scrap = metal('#6a6a70', '#c0c0c8', 44)
    rect(scrap, 0, 0, 6, 5, '#7a4a2a'); rect(scrap, 9, 9, 15, 15, '#8a6a40')
    for x in range(S):
        put(scrap, x, 8, '#3a3a40')
    iron = metal('#4a4a52', '#a0a0a8', 45)
    copper = metal('#b06a3a', '#e0b080', 46)
    grey = metal('#8a8a90', '#d0d0d8', 47)
    cwhite = new('#f0f0f0', 0.05, 48)
    cred = new('#d82828', 0.08, 49)
    put(cred, 4, 4, '#ff9090'); put(cred, 5, 4, '#ff9090')
    tex = dict(scrap=scrap, iron=iron, copper=copper, grey=grey, cwhite=cwhite, cred=cred)
    boxes = [
        box([1, 0, 1], [15, 10, 15], 'scrap'),
        box([0.7, 10, 0.7], [15.3, 12, 15.3], 'iron'),
        box([2, 2, 0.4], [7, 7, 1], 'copper', full=True),
        box([9, 4, 0.4], [14, 9, 1], 'grey', full=True),
        box([3, 12, 3], [13, 14.5, 13], 'cwhite'),            # a big gashapon capsule: white base,
        box([2.7, 14.2, 2.7], [13.3, 14.9, 13.3], 'iron'),    # seam,
        box([3.5, 14.9, 3.5], [12.5, 17.5, 12.5], 'cred'),    # red dome
        box([5, 17.5, 5], [11, 18.5, 11], 'cred'),
        box([15, 6, 3], [16.5, 8, 5], 'iron'),
        box([0.3, 3, 9], [1, 8, 14], 'copper', full=True),
    ]
    return tex, boxes


@chest("merveille", "Golden Lion's Chest")
def _():
    # Navy and gold, with a golden lion's head on the front and Shiki's crossed swords on the lid.
    navy = lacquer('#1a2a44', 50)
    frame(navy, 0, 0, 15, 15, '#d8b040')
    lid = lacquer('#1a2a44', 51)
    frame(lid, 0, 0, 15, 15, '#d8b040')
    for i in range(2, 14):
        put(lid, i, i, '#e8ecf4'); put(lid, 15 - i, i, '#e8ecf4')   # crossed swords
    rect(lid, 2, 2, 3, 3, '#8a5a30'); rect(lid, 12, 2, 13, 3, '#8a5a30')   # hilts
    mane = new('#f0c040', 0.3, 52)
    for y in range(S):
        for x in range(S):
            if (x + 2 * y) % 5 == 0:
                put(mane, x, y, '#c89020')
    face = new('#f0c848', 0.08, 53)
    rect(face, 4, 4, 5, 5, '#2a2010'); rect(face, 10, 4, 11, 5, '#2a2010')     # eyes
    rect(face, 7, 8, 8, 9, '#6a3a20')                                           # nose
    for x in range(5, 11):
        put(face, x, 12, '#6a3a20')                                             # mouth
    rect(face, 3, 2, 6, 2, '#c89020'); rect(face, 9, 2, 12, 2, '#c89020')       # brows
    gold = new('#d8b040', 0.15, 54)
    tex = dict(navy=navy, lid=lid, mane=mane, face=face, gold=gold)
    boxes = [
        box([1, 0, 1], [15, 9, 15], 'navy'),
        box([0.7, 9, 0.7], [15.3, 13, 15.3], dict(all='navy', top='lid')),
        box([3.5, 1, 0.2], [12.5, 10, 1], 'mane', full=True),
        box([5, 2.5, -0.3], [11, 8.5, 0.2], dict(all='mane', front='face'), full=True),
        box([1.5, -0.01, 1.5], [3, 1, 3], 'gold'),
        box([13, -0.01, 1.5], [14.5, 1, 3], 'gold'),
        box([1.5, -0.01, 13], [3, 1, 14.5], 'gold'),
        box([13, -0.01, 13], [14.5, 1, 14.5], 'gold'),
    ]
    return tex, boxes


@chest("gold_island", "Woonan's Treasure Chest")
def _():
    # The old pirate Woonan's chest: worn timber in gold bands, gold coins spilling over the lid, and El Drago's
    # golden claw marks gouged across the front where he tried to tear it open.
    wood = planks('#6a4a2a', '#3a2614', 55)
    front = planks('#6a4a2a', '#3a2614', 56)
    for i in range(4):
        for (x0, y0) in ((3, 2), (6, 1), (9, 2)):
            put(front, x0 + i, y0 + i * 2, '#e8c040'); put(front, x0 + i, y0 + i * 2 + 1, '#a07820')   # claw marks
    band = new('#d8b030', 0.12, 57)
    frame(band, 0, 0, 15, 15, '#a07820')
    coins = new('#e8c040', 0.3, 58)
    rnd = random.Random(59)
    for _ in range(18):
        x, y = rnd.randrange(S), rnd.randrange(S)
        put(coins, x, y, '#fff0a0'); put(coins, x + 1, y, '#b08820')
    lock = new('#c8a030', 0.1, 60)
    rect(lock, 6, 5, 9, 9, '#2a2010')
    tex = dict(wood=wood, front=front, band=band, coins=coins, lock=lock)
    boxes = [
        box([1, 0, 2], [15, 9, 14], dict(all='wood', front='front')),
        box([1, 9, 2], [15, 12, 14], dict(all='wood', front='front')),
        box([0.6, 0, 1.6], [2.4, 12.5, 14.4], 'band'),
        box([13.6, 0, 1.6], [15.4, 12.5, 14.4], 'band'),
        box([2.4, 8.6, 1.6], [13.6, 9.6, 14.4], 'band'),
        box([6.5, 7, 1.2], [9.5, 11, 2], 'lock', full=True),
        box([2.5, 12, 3.5], [13.5, 13.5, 12.5], 'coins'),            # the hoard spilling over the top
        box([4, 13.5, 5], [12, 14.8, 11], 'coins'),
        box([6, 14.8, 6.5], [10, 15.8, 9.5], 'coins'),
        box([13.5, 0, 0.3], [15.5, 1.2, 2.3], 'coins'),              # and onto the floor
        box([1, 0, 14.2], [3.5, 0.8, 15.8], 'coins'),
    ]
    return tex, boxes


@chest("salamander", "Gasparde's Syrup Safe")
def _():
    # A Navy-green steel safe from the Salamander, its gull crest crossed out, with amber syrup oozing over the top
    # and running down the front.
    steel = metal('#2e4a3e', '#8aa090', 61, edge='#1e3028')
    front = metal('#2e4a3e', '#8aa090', 62, edge='#1e3028')
    for x in range(4, 12):
        put(front, x, 4 + abs(x - 8) // 2, '#e8e8ec')   # the gull
    for i in range(6):
        put(front, 5 + i, 2 + i, '#c82020'); put(front, 10 - i, 2 + i, '#c82020')   # crossed out
    dial = new('#c8c8d0', 0.06, 63)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 7.5, y - 7.5)
            if r > 7.4:
                put(dial, x, y, '#2e4a3e')
            elif r < 2:
                put(dial, x, y, '#4a4a52')
    for a in range(0, 360, 30):
        put(dial, 7.5 + 6 * math.cos(math.radians(a)), 7.5 + 6 * math.sin(math.radians(a)), '#1a1a1e')
    syrup = new('#d89030', 0.12, 64)
    for x in range(S):
        put(syrup, x, (x * 3) % S, '#f8c870')
    tex = dict(steel=steel, front=front, dial=dial, syrup=syrup)
    boxes = [
        box([1, 0, 1], [15, 12, 15], dict(all='steel', front='front')),
        box([9.5, 2, 0.4], [13.5, 6, 1], 'dial', full=True),
        box([1.5, 12, 1.5], [14.5, 13.5, 14.5], 'syrup'),              # syrup over the top,
        box([3, 13.5, 4], [10, 14.5, 12], 'syrup'),
        box([2, 7, 0.5], [4, 12.5, 1.5], 'syrup'),                     # running down the front
        box([2.5, 4.5, 0.6], [3.5, 7, 1.4], 'syrup'),
        box([11, 9, 0.5], [13, 12.5, 1.5], 'syrup'),
        box([14.5, 6, 6], [15.5, 13, 8], 'syrup'),                     # and the side
        box([0.8, -0.01, 0.8], [3, 1.5, 3], 'steel'),
        box([13, -0.01, 0.8], [15.2, 1.5, 3], 'steel'),
    ]
    return tex, boxes


@chest("omatsuri_island", "Festival Prize Box")
def _():
    # The Trials of Hell's prize box: red lacquer with gold corners, a red-and-white festival rope, a paper lantern on
    # a post, and Lily Carnation herself sitting on the lid, smiling.
    red = lacquer('#b82028', 65)
    front = lacquer('#b82028', 66)
    for x in range(S):
        put(front, x, 5, '#ffffff' if x % 4 < 2 else '#c82020'); put(front, x, 6, '#c82020' if x % 4 < 2 else '#ffffff')
    rect(front, 6, 9, 9, 12, '#e8c040')
    gold = new('#e8c040', 0.15, 67)
    lantern = new('#f8e8c0', 0.05, 68)
    for y in (0, 15):
        for x in range(S):
            put(lantern, x, y, '#2a2020')
    for x in range(4, 12):
        put(lantern, x, 7, '#c82020'); put(lantern, x, 8, '#c82020')
    petal = new('#f0d030', 0.08, 69)
    put(petal, 4, 4, '#c82020'); put(petal, 11, 4, '#c82020'); put(petal, 4, 11, '#c82020'); put(petal, 11, 11, '#c82020')
    face = new('#f8e070', 0.05, 70)
    rect(face, 4, 5, 5, 6, '#1a1a1a'); rect(face, 10, 5, 11, 6, '#1a1a1a')
    for x in range(5, 11):
        put(face, x, 10 + (1 if 6 < x < 9 else 0), '#8a2020')
    stem = new('#3a8a3a', 0.1, 71)
    tex = dict(red=red, front=front, gold=gold, lantern=lantern, petal=petal, face=face, stem=stem)
    boxes = [
        box([1, 0, 2], [15, 9, 14], dict(all='red', front='front')),
        box([0.6, 9, 1.6], [15.4, 11, 14.4], 'red'),
        box([0.4, -0.01, 1.4], [2.4, 11.4, 3.4], 'gold'),
        box([13.6, -0.01, 1.4], [15.6, 11.4, 3.4], 'gold'),
        box([0.4, -0.01, 12.6], [2.4, 11.4, 14.6], 'gold'),
        box([13.6, -0.01, 12.6], [15.6, 11.4, 14.6], 'gold'),
        box([12.5, 11, 11], [13.5, 17, 12], 'stem'),                   # the lantern's post
        box([11.5, 13, 10], [14.5, 16.5, 13], 'lantern', full=True, light=10),
        box([6.5, 11, 7.5], [7.5, 13, 8.5], 'stem'),                   # Lily Carnation's stem
        box([3.5, 13, 7], [10.5, 17, 8], dict(all='petal', front='face'), full=True),
        box([4.5, 12, 7.2], [9.5, 13, 8.8], 'petal'),
    ]
    return tex, boxes


@chest("karakuri_castle", "Clockwork Turtle Chest")
def _():
    # One of Ratchet's Zogame-kun turtles built as a strongbox: a riveted bronze body, a green plated shell for a lid,
    # a turtle head and four stubby legs, and a big wind-up key in its back.
    bronze = metal('#a8703a', '#e0b080', 72)
    shell = new('#3a7a4a', 0.1, 73)
    for y in range(S):
        for x in range(S):
            if (x + (y // 4) * 2) % 8 == 0 or y % 4 == 0:
                put(shell, x, y, '#24502e')
    head = new('#5a9a5a', 0.1, 74)
    rect(head, 3, 5, 5, 7, '#ffffff'); put(head, 4, 6, '#c82020')
    rect(head, 10, 5, 12, 7, '#ffffff'); put(head, 11, 6, '#c82020')        # glowing red eyes
    for x in range(4, 12):
        put(head, x, 11, '#2a3a2a')
    key = new('#d8b040', 0.12, 75)
    frame(key, 0, 0, 15, 15, '#a07820')
    tex = dict(bronze=bronze, shell=shell, head=head, key=key)
    boxes = [
        box([2, 2, 2], [14, 9, 14], 'bronze'),
        box([1, 9, 1], [15, 11, 15], 'shell'),
        box([2.5, 11, 2.5], [13.5, 13, 13.5], 'shell'),
        box([4.5, 13, 4.5], [11.5, 14.5, 11.5], 'shell'),
        box([5.5, 5, -1.5], [10.5, 10, 2], dict(all='bronze', front='head'), full=True),   # the head, out front
        box([1, 0, 1], [4, 3, 4], 'bronze'),
        box([12, 0, 1], [15, 3, 4], 'bronze'),
        box([1, 0, 12], [4, 3, 15], 'bronze'),
        box([12, 0, 12], [15, 3, 15], 'bronze'),
        box([7.5, 5, 14], [8.5, 7, 16], 'key'),                           # the key's shaft
        box([5, 4, 15.5], [11, 9, 16.5], 'key', full=True),               # and its bow
    ]
    return tex, boxes


@chest("groseade", "World's War Chest")
def _():
    # Byrnndi World's chest from the Groseade: black iron with purple bands, a horn bolted to one corner, and one of the
    # cannon shells he likes to throw lying on the lid.
    iron = metal('#1e1a24', '#5a4a6a', 76)
    front = metal('#1e1a24', '#5a4a6a', 77)
    for (x, y) in ((4, 4), (5, 5), (6, 4), (7, 5), (8, 4), (9, 5), (10, 4), (11, 5)):
        put(front, x, y + 4, '#8a5ab8'); put(front, x, y + 5, '#8a5ab8')   # a W, his mark
    band = new('#6a3a8a', 0.12, 78)
    horn = new('#e8e0c8', 0.12, 79)
    for y in range(0, S, 3):
        for x in range(S):
            put(horn, x, y, '#c8c0a8')
    shell = new('#b08840', 0.1, 80)
    for x in range(S):
        put(shell, x, 3, '#e0c070')
    tip = new('#5a5a62', 0.1, 81)
    tex = dict(iron=iron, front=front, band=band, horn=horn, shell=shell, tip=tip)
    boxes = [
        box([1, 0, 1], [15, 11, 15], dict(all='iron', front='front')),
        box([0.6, 3, 0.6], [15.4, 4.5, 15.4], 'band'),
        box([0.6, 9, 0.6], [15.4, 11.5, 15.4], 'band'),
        box([4, 11.5, 6], [11, 14, 9], 'shell'),                         # a cannon shell on the lid
        box([11, 12, 6.5], [13.5, 13.5, 8.5], 'tip'),
        box([0.5, 11, 0.5], [3, 13.5, 3], 'horn'),                       # a horn on the corner
        box([0.8, 13.5, 0.8], [2.4, 16.5, 2.4], 'horn'),
        box([1.1, 16.5, 1.1], [2, 18.5, 2], 'horn'),
    ]
    return tex, boxes


@chest("clockwork_island", "Trump Card Strongbox")
def _():
    # Bear King's strongbox from Trump Castle: a red lacquered box with gold corners, the four card suits on its face, a
    # clock dial on the lid and a golden spade standing up behind it like his collar.
    red = lacquer('#9a2424', 82)
    front = lacquer('#9a2424', 83)
    rect(front, 1, 6, 14, 13, '#f4ecd8')   # a playing card across the front
    for (x, c) in ((3, '#1a1a1a'), (6, '#d02020'), (9, '#1a1a1a'), (12, '#d02020')):
        rect(front, x, 8, x + 1, 9, c); put(front, x, 10, c)
    gold = metal('#d8b040', '#f8e080', 84)
    dial = new('#f4ecd8', 0.04, 85)
    frame(dial, 0, 0, 15, 15, '#d8b040')
    for (x, y) in ((7, 1), (14, 7), (7, 14), (1, 7)):
        rect(dial, x, y, x + 1, y + 1, '#1a1a1a')
    for i in range(5):
        put(dial, 7 + i // 2, 7 - i, '#1a1a1a'); put(dial, 8, 8 + i // 2, '#c82020')
    spade = new('#f0c840', 0.1, 86)
    tex = dict(red=red, front=front, gold=gold, dial=dial, spade=spade)
    boxes = [
        box([1, 0, 2], [15, 10, 14], dict(all='red', front='front')),
        box([0.6, 10, 1.6], [15.4, 12, 14.4], 'red'),
        box([0.4, -0.01, 1.4], [2.4, 12.4, 3.4], 'gold'),
        box([13.6, -0.01, 1.4], [15.6, 12.4, 3.4], 'gold'),
        box([0.4, -0.01, 12.6], [2.4, 12.4, 14.6], 'gold'),
        box([13.6, -0.01, 12.6], [15.6, 12.4, 14.6], 'gold'),
        box([4.5, 12, 4], [11.5, 12.8, 11], 'dial', full=True),          # the clock on the lid
        box([6, 12, 12.5], [10, 15, 13.5], 'spade'),                     # the spade behind it
        box([5, 15, 12.5], [11, 17, 13.5], 'spade'),
        box([7, 17, 12.5], [9, 18.5, 13.5], 'spade'),
    ]
    return tex, boxes


@chest("delta_island", "Festival Treasure Chest")
def _():
    # The Pirates Expo's prize chest: Festa's bait. Striped like a festival tent, gold-trimmed, a rocket of fireworks
    # tied to each side and a big gold star on the lid.
    stripes = new('#d83a4a', 0.06, 87)
    for y in range(S):
        for x in range(S):
            if (x // 3) % 2:
                put(stripes, x, y, '#f4ece0')
    front = stripes.copy()
    rect(front, 5, 5, 10, 10, '#e8c040'); rect(front, 6, 6, 9, 9, '#2a1a14')   # a gold lock plate
    gold = metal('#e8c040', '#fff0a0', 88)
    rocket = new('#3a7ad8', 0.1, 89)
    for y in range(0, S, 4):
        for x in range(S):
            put(rocket, x, y, '#f4ece0')
    star = new('#f8d040', 0.06, 90)
    tex = dict(stripes=stripes, front=front, gold=gold, rocket=rocket, star=star)
    boxes = [
        box([1.5, 0, 2], [14.5, 10, 14], dict(all='stripes', front='front')),
        box([1, 10, 1.5], [15, 11.5, 14.5], 'gold'),
        box([2, 11.5, 2.5], [14, 13, 13.5], 'stripes'),
        box([-0.5, 1, 6.5], [1.5, 12, 8.5], 'rocket'),                   # fireworks rockets on the sides
        box([14.5, 1, 6.5], [16.5, 12, 8.5], 'rocket'),
        box([0, 12, 7], [1, 14, 8], 'gold'),
        box([15, 12, 7], [16, 14, 8], 'gold'),
        box([6.5, 13, 7], [9.5, 17, 8.5], 'star'),                       # the star on top
        box([5, 14.2, 7], [11, 15.8, 8.5], 'star'),
    ]
    return tex, boxes


@chest("asuka_island", "Seven Star Reliquary")
def _():
    # The shrine box the Seven Star Sword was sealed in: black lacquer with red bands, seven gold stars like the Big
    # Dipper across the front, paper seals, and the cursed sword laid across the lid, still smouldering green.
    black = lacquer('#1a1418', 91)
    front = lacquer('#1a1418', 92)
    for (x, y) in ((2, 5), (4, 6), (6, 6), (8, 7), (10, 9), (12, 8), (13, 11)):
        put(front, x, y, '#f0d060'); put(front, x + 1, y, '#c8a040')
    band = new('#a82020', 0.08, 93)
    seal = new('#f0e8d0', 0.05, 94)
    for y in range(3, 13, 3):
        rect(seal, 6, y, 9, y, '#a82020')
    blade = new('#d8e0dc', 0.06, 95)
    for x in range(S):
        put(blade, x, 0, '#60e070')
    hilt = new('#2a6a3a', 0.12, 96)
    for x in range(0, S, 2):
        put(hilt, x, 8, '#e8c040')
    tex = dict(black=black, front=front, band=band, seal=seal, blade=blade, hilt=hilt)
    boxes = [
        box([1, 0, 2], [15, 10, 14], dict(all='black', front='front')),
        box([0.5, 10, 1.5], [15.5, 12, 14.5], 'black'),
        box([0.4, 2, 1.4], [15.6, 3.5, 14.6], 'band'),
        box([0.4, 10.2, 1.4], [15.6, 11.2, 14.6], 'band'),
        box([3, 4, 1.6], [5, 10, 2], 'seal'),                            # paper seals over the lid's edge
        box([11, 4, 1.6], [13, 10, 2], 'seal'),
        box([2, 12, 7.5], [11, 12.8, 8.5], 'blade'),                     # the sword on the lid
        box([11, 11.8, 7], [11.6, 13.2, 9], 'band'),                     # its guard
        box([11.6, 12, 7.6], [15, 12.8, 8.4], 'hilt'),
        box([1, 12, 6], [3, 13, 10], 'seal'),                            # the shrine's stand under its tip
    ]
    return tex, boxes


@chest("crown_island", "Butler's Specimen Case")
def _():
    # Count Butler's specimen case: polished purple wood and brass, a glass top over the golden horns he came to
    # eat, and a crown of gold on the corner for Crown Island's animal king.
    wood = planks('#4a2448', '#2a1428', 97)
    front = planks('#4a2448', '#2a1428', 98)
    rect(front, 6, 6, 9, 9, '#d8b040'); put(front, 7, 8, '#2a1428'); put(front, 8, 8, '#2a1428')
    brass = metal('#c89a40', '#f0d080', 99)
    glass = new('#a8d0d8', 0.06, 100)
    for i in range(S):
        put(glass, i, i // 2, '#e8f4f8')
    horn = new('#f0c040', 0.12, 101)
    for y in range(0, S, 3):
        for x in range(S):
            put(horn, x, y, '#d89820')
    tex = dict(wood=wood, front=front, brass=brass, glass=glass, horn=horn)
    boxes = [
        box([1, 0, 2], [15, 9, 14], dict(all='wood', front='front')),
        box([0.6, 9, 1.6], [15.4, 10.5, 14.4], 'brass'),
        box([1.5, 10.5, 2.5], [14.5, 14, 13.5], 'glass'),                 # the glass case
        box([4, 10.5, 6], [6, 13, 8], 'horn'),                            # the golden horns inside
        box([4.6, 13, 6.6], [5.4, 13.8, 7.4], 'horn'),
        box([10, 10.5, 6], [12, 13, 8], 'horn'),
        box([10.6, 13, 6.6], [11.4, 13.8, 7.4], 'horn'),
        box([0.6, -0.01, 1.6], [2, 10.5, 3], 'brass'),
        box([14, -0.01, 1.6], [15.4, 10.5, 3], 'brass'),
        box([12.5, 14, 2.5], [14.5, 15, 4.5], 'brass'),                   # a little crown on the corner
        box([12.5, 15, 2.5], [13, 16, 3], 'brass'),
        box([14, 15, 2.5], [14.5, 16, 3], 'brass'),
        box([12.5, 15, 4], [13, 16, 4.5], 'brass'),
        box([14, 15, 4], [14.5, 16, 4.5], 'brass'),
    ]
    return tex, boxes


# ---------------------------------------------------------------- writing

FACE = dict(north='front', south='back', east='side', west='side', up='top', down='bottom')


def model_json(cid, tex, boxes):
    elements = []
    for f, t, faces, extra in boxes:
        fm = faces if isinstance(faces, dict) else {'all': faces}
        el = {"from": f, "to": t, "faces": {}}
        for face, key in FACE.items():
            k = fm.get(key, fm.get('all'))
            d = {"texture": "#" + k}
            if extra.get('full'):
                d["uv"] = [0, 0, 16, 16]
            if face == 'down' and f[1] <= 0:
                d["cullface"] = "down"
            el["faces"][face] = d
        if extra.get('light'):
            el["light_emission"] = extra['light']
        elements.append(el)
    first = boxes[0][2] if isinstance(boxes[0][2], str) else boxes[0][2]['all']
    textures = {k: f"opbosses:block/chest/{cid}/{k}" for k in tex}
    textures["particle"] = textures[first]
    return {"parent": "minecraft:block/block", "textures": textures, "elements": elements}


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump(obj, fh, indent=2)
        fh.write('\n')


# ---------------------------------------------------------------- the sea bosses' strongrooms (on their flagships)
@chest("widowmaker", "Maribel's Scrimshaw Chest")
def _():
    # A whaler's chest of tarred planks bound in whalebone, a Sea King tooth for a hasp, scrimshaw on the lid.
    wood = planks('#4a3828', '#22180e', 51)
    front = planks('#4a3828', '#22180e', 52)
    for x in range(3, 13):
        put(front, x, 4, '#d8d0b8')                                      # a scrimshaw harpoon across the front
    put(front, 12, 3, '#d8d0b8'); put(front, 12, 5, '#d8d0b8'); put(front, 13, 4, '#d8d0b8')
    bone = new('#e4dcc4', 0.1, 53)
    for y in range(0, S, 4):
        for x in range(S):
            put(bone, x, y, '#c8bea4')
    lid = planks('#4a3828', '#22180e', 54)
    for (x, y) in ((4, 4), (5, 5), (6, 6), (7, 6), (8, 6), (9, 5), (10, 4), (7, 3), (7, 4)):
        put(lid, x, y, '#d8d0b8')                                        # a little Sea King etched on the lid
    tooth = new('#f4f0e0', 0.06, 55)
    tex = dict(wood=wood, front=front, bone=bone, lid=lid, tooth=tooth)
    boxes = [
        box([1, 0, 1], [15, 9, 15], dict(all='wood', front='front')),
        box([1, 9, 1], [15, 13, 15], dict(all='wood', top='lid', front='front')),
        box([0.5, 0, 0.5], [2, 13.5, 15.5], 'bone'),
        box([14, 0, 0.5], [15.5, 13.5, 15.5], 'bone'),
        box([0.5, 8.5, 0.4], [15.5, 9.5, 15.6], 'bone'),
        box([7, 6, 0.2], [9, 12, 1], 'tooth'),
        box([7.5, 4.5, 0.3], [8.5, 6, 0.9], 'tooth'),
    ]
    return tex, boxes


@chest("tithe_cathedral", "The Tithe Reliquary")
def _():
    # A gilded reliquary: crimson velvet panels framed in gold, a pointed gothic lid, a gold coin of the Tithe.
    velvet = new('#8a1414', 0.1, 61)
    for y in range(S):
        for x in range(S):
            if (x + y) % 4 == 0:
                put(velvet, x, y, '#a01c1c')
    gold = lacquer('#e0b030', 62)
    coin = new('#f0c840', 0.05, 63)
    for y in range(3, 13):
        put(coin, 8, y, '#2a2020')
    for x in range(4, 13):
        put(coin, x, 6, '#2a2020')
    frame(coin, 0, 0, 15, 15, '#b08020')
    roof = new('#2a2a30', 0.08, 64)
    for y in range(0, S, 3):
        for x in range(S):
            put(roof, x, y, '#1a1a20')
    tex = dict(velvet=velvet, gold=gold, coin=coin, roof=roof)
    boxes = [
        box([1, 0, 2], [15, 1.5, 14], 'gold'),
        box([1.5, 1.5, 2.5], [14.5, 10, 13.5], 'velvet'),
        box([1, 1.5, 2], [2.5, 10, 3.5], 'gold'),
        box([13.5, 1.5, 2], [15, 10, 3.5], 'gold'),
        box([1, 1.5, 12.5], [2.5, 10, 14], 'gold'),
        box([13.5, 1.5, 12.5], [15, 10, 14], 'gold'),
        box([1, 10, 2], [15, 11, 14], 'gold'),
        box([2, 11, 3], [14, 13, 13], 'roof'),
        box([4, 13, 5], [12, 15, 11], 'roof'),
        box([7, 15, 7], [9, 16, 9], 'gold'),
        box([5.5, 3, 2.1], [10.5, 8, 2.5], 'coin', full=True),
    ]
    return tex, boxes


@chest("cinderwake", "Ashgrave's Furnace Safe")
def _():
    # An iron safe built like a furnace: blackened riveted plates, a glowing grate in the door, a wheel lock.
    iron = metal('#2e2a2c', '#5a5458', 71, edge='#1a1618')
    door = metal('#3a3436', '#6a6468', 72, edge='#1a1618')
    grate = new('#ff8a20', 0.2, 73)
    for x in range(0, S, 3):
        for y in range(S):
            put(grate, x, y, '#2a1a10')
    for y in range(0, S, 4):
        for x in range(S):
            put(grate, x, y, '#2a1a10')
    wheel = new('#8a8a90', 0.06, 74)
    frame(wheel, 0, 0, 15, 15, '#5a5a60')
    for i in range(S):
        put(wheel, i, 7, '#5a5a60'); put(wheel, 7, i, '#5a5a60')
    tex = dict(iron=iron, door=door, grate=grate, wheel=wheel)
    boxes = [
        box([1, 0, 1], [15, 14, 15], dict(all='iron', front='door')),
        box([0.5, 13, 0.5], [15.5, 14.5, 15.5], 'iron'),
        box([0.5, 0, 0.5], [15.5, 1, 15.5], 'iron'),
        box([4, 2, 0.6], [12, 6, 1.1], 'grate', full=True),
        box([6, 8, 0.4], [10, 12, 1], 'wheel', full=True),
        box([2, 14.5, 6], [4, 16, 10], 'iron'),                          # a little chimney
    ]
    return tex, boxes


def main(res):
    A = os.path.join(res, 'assets/opbosses')
    for cid, c in CHESTS.items():
        tex, boxes = c['build']()
        block = cid + "_chest"
        for k, img in tex.items():
            p = os.path.join(A, 'textures/block/chest', cid, k + '.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            img.save(p)
        write(os.path.join(A, 'models/block', block + '.json'), model_json(cid, tex, boxes))
        write(os.path.join(A, 'blockstates', block + '.json'), {"variants": {
            f"facing={d}": {"model": f"opbosses:block/{block}", **({"y": y} if y else {})}
            for d, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}})
        write(os.path.join(A, 'items', block + '.json'), {"model": {"type": "minecraft:model", "model": f"opbosses:block/{block}"}})
        write(os.path.join(res, 'data/opbosses/loot_table/blocks', block + '.json'), {
            "type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"opbosses:{block}"}],
                                                  "conditions": [{"condition": "minecraft:survives_explosion"}]}]})
        print('%-34s %-26s %d boxes, %d textures' % (block, c['name'], len(boxes), len(tex)))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'src/main/resources')
