#!/usr/bin/env python3
"""Draws the boss gear and writes its JSON: for every set in opbosses/gear.json, the boss's Remnant, four armour icons,
the armour as worn (64x32 equipment textures), the weapon, their item models, recipes, repair tags and names.

    python3 tools/gen_gear.py src/main/resources [--sheet out.png]

Needs Pillow. The names also go into the lang file through gen_assets.py (which rewrites en_us.json), so either
script can be run on its own. --sheet draws every icon and a front view of every set, for looking at them.
"""
import json
import os
import random
import sys

from PIL import Image, ImageDraw

PIECES = ["helmet", "chestplate", "leggings", "boots"]
PIECE_NAMES = {"helmet": "Helmet", "chestplate": "Chestplate", "leggings": "Leggings", "boots": "Boots"}
DIAMOND = {"helmet": "minecraft:diamond_helmet", "chestplate": "minecraft:diamond_chestplate",
           "leggings": "minecraft:diamond_leggings", "boots": "minecraft:diamond_boots"}


def load(res):
    return json.load(open(os.path.join(res, "opbosses/gear.json")))["sets"]


def lang_entries(res):
    """Item names for every gear item, for en_us.json."""
    lang = {"itemGroup.opbosses.gear": "One Piece: Boss Gear"}
    for g in load(res):
        lang["item.opbosses.remnant_" + g["boss"]] = g["remnantName"]
        for piece in PIECES:
            lang["item.opbosses.%s_%s" % (g["set"], piece)] = "%s %s" % (g["setName"], PIECE_NAMES[piece])
        lang["item.opbosses." + g["weapon"]] = g["weaponName"]
    return lang


# ---- Colours ----

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def palette(g):
    main, dark, accent = tuple(g["main"]), tuple(g["dark"]), tuple(g["accent"])
    return {
        "O": shade(dark, 0.55),          # outline
        "D": dark,
        "M": main,
        "L": mix(main, (255, 255, 255), 0.35),   # highlight
        "A": accent,
        "a": shade(accent, 0.7),
        "W": mix(accent, (255, 255, 255), 0.6),  # glint
    }


# The badge on each set's chest (6x5, 'A' accent, 'O' outline, 'W' glint).
EMBLEMS = {
    "anchor": ["..AA..", "AAAAAA", "..AA..", "A.AA.A", ".AAAA."],
    "eye": [".AAAA.", "A.OO.A", "AAOWAA", "A.OO.A", ".AAAA."],
    "star": ["..AA..", "AAWAAA", ".AAAA.", ".A..A.", "A....A"],
    "swords": ["A....A", ".A..A.", "..AA..", ".A..A.", "A....A"],
    "gear": [".A..A.", "AAAAAA", ".AOOA.", "AAAAAA", ".A..A."],
    "wave": ["......", "..AA..", ".A..A.", "A.AA.A", "AA..AA"],
    "ring": ["..AA..", ".A..A.", "A....A", ".A..A.", "..AA.."],
    "skull": [".AAAA.", "AOAAOA", "AAAAAA", ".AWAA.", ".A.A.."],
    "crown": ["A.AA.A", "AAAAAA", "AWAAWA", "AAAAAA", "......"],
    "note": ["...AAA", "...A.A", "...A..", "AAA...", "AAA..."],
    "spade": ["..AA..", ".AAAA.", "AAAAAA", "AAWAAA", "..AA.."],
    "bell": ["..AA..", ".AAAA.", ".AAAA.", "AAAAAA", "..WW.."],
    "flower": [".A..A.", "AAWWAA", ".AWWA.", "AA..AA", "......"],
}


# ---- Armour icons (16x16 pixel art; '.' is clear) ----

ICONS = {
    "helmet": [
        "................",
        "................",
        "................",
        ".....OOOOOO.....",
        "...OOLLMMMMOO...",
        "..OLLMMMMMMMDO..",
        "..OLMMMMMMMMDO..",
        "..OAAAAAAAAAaO..",
        "..OMMMOOOOMMDO..",
        "..OMMO....OMDO..",
        "..OMDO....ODDO..",
        "..OODO....ODOO..",
        "...OO......OO...",
        "................",
        "................",
        "................",
    ],
    "chestplate": [
        "................",
        "..OOOO....OOOO..",
        ".OALMMO..OMMDaO.",
        ".OALMMMOOMMMDaO.",
        ".OOLMMMMMMMMDOO.",
        "..OOLMMAAMMDOO..",
        "...OLMAWAAMDO...",
        "...OLMMAAMMDO...",
        "...OLMMMMMMDO...",
        "...OAAAAAAAaO...",
        "...OLMMMMMMDO...",
        "...OLMMMMMMDO...",
        "...OOOOOOOOOO...",
        "................",
        "................",
        "................",
    ],
    "leggings": [
        "................",
        "................",
        "...OOOOOOOOOO...",
        "...OAAAWAAAaO...",
        "...OLMMMMMMDO...",
        "...OLMMOOMMDO...",
        "...OLMDOOLMDO...",
        "...OLMDOOLMDO...",
        "...OAaDOOAaDO...",
        "...OLMDOOLMDO...",
        "...OLMDOOLMDO...",
        "...OLMDOOLMDO...",
        "...OOOOOOOOOO...",
        "................",
        "................",
        "................",
    ],
    "boots": [
        "................",
        "................",
        "................",
        "................",
        "...OOOO..OOOO...",
        "...OLMO..OLMO...",
        "...OLMO..OLMO...",
        "...OAaO..OAaO...",
        "...OLMO..OLMO...",
        "..OLMMO..OLMMO..",
        ".OLMMMO..OLMMMO.",
        ".ODDDDO..ODDDDO.",
        ".OOOOOO..OOOOOO.",
        "................",
        "................",
        "................",
    ],
    "remnant": [
        "................",
        ".........O......",
        "........OWO.....",
        ".......OWAO.....",
        "......OLWAaO....",
        ".....OLMAAaO....",
        "....OLMMAaDO....",
        "...OLMMMaDDO....",
        "...OLMMDDDO.....",
        "....OLMDDO......",
        "....OOMDO.......",
        ".....OOO........",
        "................",
        "................",
        "................",
        "................",
    ],
}


def stamp(img, pattern, pal, x0, y0):
    """Draws an emblem pattern onto an image at (x0, y0)."""
    for yy, row in enumerate(pattern):
        for xx, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x0 + xx, y0 + yy), pal[ch] + (255,))


def icon(rows, pal):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        assert len(row) == 16, row
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), pal[ch] + (255,))
    return img


# ---- Weapon icons (drawn handle bottom-left, point top-right) ----

def weapon_icon(g):
    pal = palette(g)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    O, D, M, L, A, W = (pal[k] + (255,) for k in "ODMLAW")
    grip = (92, 60, 36, 255)
    shape = g["weaponShape"]

    def blade(x0, y0, x1, y1, edge=L, body=M):
        d.line([(x0, y0), (x1, y1)], fill=body, width=2)
        d.line([(x0 + 1, y0 - 1), (x1 + 1, y1 - 1)], fill=edge)

    def handle(length=4, guard=True):
        d.line([(1, 14), (1 + length, 14 - length)], fill=grip, width=2)
        d.point([(1, 14)], fill=A)
        if guard:
            gx, gy = 2 + length, 13 - length
            d.line([(gx - 2, gy - 1), (gx + 1, gy + 2)], fill=A, width=2)

    if shape == "anchor":
        d.line([(3, 12), (12, 3)], fill=D, width=2)                       # shank
        d.line([(10, 1), (14, 5)], fill=D, width=2)                       # stock
        d.arc([0, 7, 9, 16], 90, 270, fill=M, width=2); d.arc([0, 7, 9, 16], 270, 360, fill=M, width=2)
        d.polygon([(0, 9), (2, 7), (3, 10)], fill=L); d.polygon([(8, 15), (10, 13), (7, 13)], fill=L)
        d.ellipse([12, 0, 15, 3], outline=A)                              # ring
    elif shape == "rapier":
        d.line([(5, 10), (15, 0)], fill=L); d.line([(5, 11), (14, 2)], fill=M)
        handle(3); d.arc([1, 8, 7, 14], 200, 20, fill=A)
    elif shape in ("cutlass", "scimitar"):
        pts = [(5, 10), (8, 6), (11, 3), (14, 1), (14, 3), (12, 6), (9, 9), (6, 11)]
        if shape == "scimitar":
            pts = [(5, 10), (8, 8), (11, 5), (13, 1), (15, 2), (14, 6), (10, 10), (6, 12)]
        d.polygon(pts, fill=M); d.line(pts[:4], fill=L)
        handle(3); d.arc([0, 9, 6, 15], 180, 360, fill=A)
    elif shape == "katana":
        d.line([(5, 10), (14, 1)], fill=M, width=2); d.line([(6, 10), (15, 1)], fill=L)
        d.line([(1, 14), (4, 11)], fill=D, width=2); d.point([(2, 13), (3, 12)], fill=A)
        d.ellipse([3, 9, 6, 12], fill=A)                                  # tsuba
    elif shape == "hammer":
        d.line([(1, 14), (9, 6)], fill=grip, width=2)
        d.polygon([(6, 3), (10, 0), (15, 5), (11, 9)], fill=M); d.line([(6, 3), (10, 0)], fill=L)
        d.line([(8, 6), (12, 2)], fill=A, width=2); d.line([(11, 9), (15, 5)], fill=D)
    elif shape in ("trident", "harpoon"):
        d.line([(1, 14), (11, 4)], fill=D if shape == "trident" else grip, width=2)
        if shape == "trident":
            d.line([(9, 2), (14, 7)], fill=M, width=2)
            for (x, y) in ((9, 2), (12, 3), (14, 7)):
                d.line([(x, y), (x + 2, y - 2)], fill=L)
            d.point([(15, 0)], fill=W)
        else:
            d.polygon([(10, 3), (15, 0), (12, 5)], fill=M); d.line([(10, 3), (15, 0)], fill=L)
            d.point([(11, 5), (9, 3)], fill=A)
        d.line([(3, 11), (5, 13)], fill=A)
    elif shape == "laser":
        d.line([(1, 14), (5, 10)], fill=D, width=3)
        d.line([(5, 10), (14, 1)], fill=A, width=3); d.line([(6, 9), (14, 1)], fill=W)
        d.point([(2, 13)], fill=L)
    elif shape == "cane":
        d.line([(2, 15), (11, 6)], fill=M, width=2); d.line([(3, 15), (12, 6)], fill=L)
        d.arc([9, 1, 15, 8], 180, 90, fill=M, width=2); d.ellipse([10, 2, 13, 5], fill=A)
    elif shape == "mic":
        d.line([(1, 14), (10, 5)], fill=D, width=2); d.line([(2, 14), (10, 6)], fill=M)
        d.ellipse([9, 0, 15, 6], fill=M); d.ellipse([10, 1, 14, 5], fill=L)
        d.line([(10, 3), (14, 3)], fill=A); d.line([(12, 1), (12, 5)], fill=A)
        d.line([(4, 11), (6, 13)], fill=A)                                # ribbon
    elif shape == "gauntlet":
        d.rectangle([2, 6, 13, 14], fill=M); d.rectangle([2, 6, 13, 7], fill=L)
        for x in (3, 6, 9, 12):
            d.rectangle([x, 3, x + 1, 6], fill=D)
        d.rectangle([2, 10, 13, 11], fill=A); d.rectangle([5, 12, 10, 14], fill=D)
        d.point([(4, 8), (11, 8)], fill=W)
    elif shape == "claw":
        # A gold gauntlet with three long hooked nails.
        d.rectangle([1, 10, 6, 15], fill=D); d.rectangle([1, 10, 6, 11], fill=A)
        for i in range(3):
            x, y = 3 + 2 * i, 9 - i
            d.line([(x, y), (x + 4, y - 4), (x + 7, y - 5)], fill=M, width=1)
            d.line([(x + 1, y), (x + 5, y - 4)], fill=L)
            d.point([(x + 8, y - 4)], fill=W)
    elif shape == "drill":
        d.line([(1, 14), (5, 10)], fill=D, width=2)
        d.polygon([(4, 8), (7, 11), (15, 0)], fill=M)
        for t in (0.3, 0.55, 0.8):
            x0, y0 = 4 + t * 11, 8 - t * 8; x1, y1 = 7 + t * 8, 11 - t * 11
            d.line([(x0, y0), (x1, y1)], fill=A)
        d.line([(4, 8), (15, 0)], fill=L)
    elif shape == "halberd":
        d.line([(1, 15), (13, 3)], fill=grip, width=2)
        d.polygon([(8, 2), (12, 0), (13, 6), (10, 8)], fill=M); d.line([(8, 2), (10, 8)], fill=L)
        d.polygon([(13, 3), (15, 1), (15, 4)], fill=A)
        d.line([(12, 4), (15, 0)], fill=W)
    else:
        blade(5, 10, 14, 1); handle(3)
    return img


# ---- Armour as worn (64x32, vanilla humanoid layout) ----

def faces(u, v, w, h, dp):
    """The six faces of a model cube at texture offset (u, v): name -> (x, y, width, height)."""
    return {
        "top": (u + dp, v, w, dp), "bottom": (u + dp + w, v, w, dp),
        "right": (u, v + dp, dp, h), "front": (u + dp, v + dp, w, h),
        "left": (u + dp + w, v + dp, dp, h), "back": (u + dp + w + dp, v + dp, w, h),
    }


class Painter:
    def __init__(self, g, seed):
        self.pal = palette(g)
        self.img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        self.rand = random.Random(seed)

    def px(self, x, y, key, jitter=0.07):
        c = self.pal[key] if isinstance(key, str) else key
        f = 1 + self.rand.uniform(-jitter, jitter)
        self.img.putpixel((x, y), shade(c, f) + (255,))

    def clear(self, x, y):
        self.img.putpixel((x, y), (0, 0, 0, 0))

    def face(self, rect, rows=None, trim=True):
        """Fills a face with plate metal: lit at the top, dark at the edges. rows limits it to those rows."""
        x0, y0, w, h = rect
        for yy in range(h):
            if rows is not None and yy not in rows:
                continue
            for xx in range(w):
                key = "M"
                if trim and (xx == 0 or xx == w - 1):
                    key = "D"
                elif yy == (min(rows) if rows else 0):
                    key = "L"
                self.px(x0 + xx, y0 + yy, key)

    def band(self, rect, row, key="A"):
        x0, y0, w, h = rect
        for xx in range(w):
            self.px(x0 + xx, y0 + row, key, 0.04)


def worn_textures(g, seed):
    """(humanoid, humanoid_leggings): helmet, chestplate and boots on the first, leggings on the second."""
    p = Painter(g, seed)
    # Helmet: the head cube (0, 0), 8x8x8.
    head = faces(0, 0, 8, 8, 8)
    for name in ("top", "right", "left", "back"):
        p.face(head[name])
    for name in ("right", "left", "back"):
        p.band(head[name], 5)
    fx, fy, fw, fh = head["front"]
    for yy in range(8):
        for xx in range(8):
            edge = xx in (0, 7)
            if yy < 2 or edge:
                p.px(fx + xx, fy + yy, "L" if yy == 0 else ("D" if edge else "M"))
            elif yy == 2:
                p.px(fx + xx, fy + yy, "A", 0.03)                      # brow band
            elif yy == 3 and xx in (1, 6):
                p.px(fx + xx, fy + yy, "O")
            elif yy >= 5 and xx in (1, 6):
                p.px(fx + xx, fy + yy, "D")                            # cheek guards
    p.px(fx + 3, fy + 1, "W", 0); p.px(fx + 4, fy + 1, "W", 0)            # crest stud
    # Crest on the hat layer (32, 0): a ridge along the top.
    hat = faces(32, 0, 8, 8, 8)
    tx, ty, tw, th = hat["top"]
    for yy in range(th):
        p.px(tx + 3, ty + yy, "A"); p.px(tx + 4, ty + yy, "a")

    # Chestplate: body (16, 16) 8x12x4 and arms (40, 16) 4x12x4.
    body = faces(16, 16, 8, 12, 4)
    for name in ("top", "right", "left", "back", "front"):
        p.face(body[name])
    for name in ("front", "back", "right", "left"):
        p.band(body[name], 10, "D")                                     # belt line
    bx, by, bw, bh = body["front"]
    for yy in range(1, 9):
        p.px(bx + 1, by + yy, "L"); p.px(bx + 6, by + yy, "D")        # chest plates
    for yy, row in enumerate(EMBLEMS[g["emblem"]]):                   # the set's badge
        for xx, ch in enumerate(row):
            if ch != ".":
                p.px(bx + 1 + xx, by + 2 + yy, ch, 0.03)
    arm = faces(40, 16, 4, 12, 4)
    for name in ("top", "right", "left", "back", "front"):
        p.face(arm[name], rows=range(0, 9) if name != "top" else None)
    for name in ("right", "left", "back", "front"):
        p.band(arm[name], 0, "A"); p.band(arm[name], 1, "a")             # pauldron
        p.band(arm[name], 8, "D")                                       # cuff

    # Boots: the leg cube (0, 16) 4x12x4, lower rows only, and the sole.
    leg = faces(0, 16, 4, 12, 4)
    for name in ("right", "left", "back", "front"):
        p.face(leg[name], rows=range(7, 12))
        p.band(leg[name], 8, "A")
        p.band(leg[name], 11, "O")
    p.face(leg["bottom"], trim=False)
    humanoid = p.img

    # Leggings: waist on the body cube and the upper legs, on their own layer.
    q = Painter(g, seed + 1)
    body2 = faces(16, 16, 8, 12, 4)
    for name in ("right", "left", "back", "front"):
        q.face(body2[name], rows=range(7, 12))
        q.band(body2[name], 7, "A")
    lx, ly, lw, lh = body2["front"]
    q.px(lx + 3, ly + 7, "W", 0); q.px(lx + 4, ly + 7, "W", 0)           # buckle
    leg2 = faces(0, 16, 4, 12, 4)
    for name in ("right", "left", "back", "front"):
        q.face(leg2[name], rows=range(0, 9))
    fx, fy, fw, fh = leg2["front"]
    for xx in range(1, 3):
        q.px(fx + xx, fy + 4, "A", 0.03); q.px(fx + xx, fy + 5, "a", 0.03)   # knee guard
    q.face(leg2["top"], trim=False)
    return humanoid, q.img


# ---- Writing ----

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def save_png(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def item_files(assets, name, texture, parent="minecraft:item/generated"):
    save_png(texture, os.path.join(assets, "textures/item", name + ".png"))
    write_json(os.path.join(assets, "models/item", name + ".json"),
               {"parent": parent, "textures": {"layer0": "opbosses:item/" + name}})
    write_json(os.path.join(assets, "items", name + ".json"),
               {"model": {"type": "minecraft:model", "model": "opbosses:item/" + name}})


def main(res, sheet=None):
    sets = load(res)
    bosses = {b["id"] for b in json.load(open(os.path.join(res, "opbosses/bosses.json")))["bosses"]}
    assets = os.path.join(res, "assets/opbosses")
    data = os.path.join(res, "data/opbosses")
    shots = []
    for i, g in enumerate(sets):
        pal = palette(g)
        remnant = "remnant_" + g["boss"]
        icons = {remnant: icon(ICONS["remnant"], pal)}
        for piece in PIECES:
            icons["%s_%s" % (g["set"], piece)] = icon(ICONS[piece], pal)
        stamp(icons["%s_chestplate" % g["set"]], EMBLEMS[g["emblem"]], pal, 5, 4)
        for name, img in icons.items():
            item_files(assets, name, img)
        weapon = weapon_icon(g)
        item_files(assets, g["weapon"], weapon, "minecraft:item/handheld")

        humanoid, leggings = worn_textures(g, 1000 + i)
        save_png(humanoid, os.path.join(assets, "textures/entity/equipment/humanoid", g["set"] + ".png"))
        save_png(leggings, os.path.join(assets, "textures/entity/equipment/humanoid_leggings", g["set"] + ".png"))
        write_json(os.path.join(assets, "equipment", g["set"] + ".json"), {"layers": {
            "humanoid": [{"texture": "opbosses:" + g["set"]}],
            "humanoid_leggings": [{"texture": "opbosses:" + g["set"]}]}})

        # Recipes: the diamond piece (or sword) and three of the boss's Remnants.
        for piece in PIECES + ["weapon"]:
            out = g["weapon"] if piece == "weapon" else "%s_%s" % (g["set"], piece)
            base = "minecraft:diamond_sword" if piece == "weapon" else DIAMOND[piece]
            recipe = {
                "type": "minecraft:crafting_shapeless",
                "category": "equipment",
                "group": "opbosses_" + g["set"],
                "ingredients": [base, "opbosses:" + remnant, "opbosses:" + remnant, "opbosses:" + remnant],
                "result": {"id": "opbosses:" + out, "count": 1}}
            if g["boss"] not in bosses:
                # The boss isn't in bosses.json yet (another branch adds it): only load once its items are registered.
                recipe = {"fabric:load_conditions": [{"condition": "fabric:registry_contains", "registry": "minecraft:item",
                                                      "values": ["opbosses:" + remnant]}], **recipe}
            write_json(os.path.join(data, "recipe", out + ".json"), recipe)
        write_json(os.path.join(data, "tags/item", "repairs_%s_armor.json" % g["set"]),
                   {"values": [{"id": "opbosses:" + remnant, "required": False}]})
        shots.append((g, icons, weapon, humanoid, leggings))

    # Names, kept alongside gen_assets.py's.
    lang_path = os.path.join(assets, "lang/en_us.json")
    lang = json.load(open(lang_path)) if os.path.exists(lang_path) else {}
    lang.update(lang_entries(res))
    write_json(lang_path, lang)
    if sheet:
        draw_sheet(shots, sheet)
    print("Drew %d gear sets" % len(sets))


def front_view(humanoid, leggings):
    """A flat front view of the armour on a grey figure: head, body, arms and legs, 16x32."""
    fig = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    skin = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(skin)
    d.rectangle([4, 0, 11, 7], fill=(200, 160, 130, 255)); d.rectangle([4, 8, 11, 19], fill=(90, 110, 160, 255))
    d.rectangle([0, 8, 3, 19], fill=(200, 160, 130, 255)); d.rectangle([12, 8, 15, 19], fill=(200, 160, 130, 255))
    d.rectangle([4, 20, 11, 31], fill=(60, 60, 90, 255))
    fig.alpha_composite(skin)
    for layer, parts in ((leggings, [((20, 20, 28, 32), (4, 8)), ((4, 20, 8, 32), (4, 20)), ((4, 20, 8, 32), (8, 20))]),
                         (humanoid, [((8, 8, 16, 16), (4, 0)), ((20, 20, 28, 32), (4, 8)), ((44, 20, 48, 32), (0, 8)),
                                     ((44, 20, 48, 32), (12, 8)), ((4, 20, 8, 32), (4, 20)), ((4, 20, 8, 32), (8, 20))])):
        for box, at in parts:
            fig.alpha_composite(layer.crop(box), at)
    return fig


def draw_sheet(shots, path):
    scale = 6
    cell_w, cell_h = 16 * 6 + 16 * 3 + 20, 34
    img = Image.new("RGBA", (cell_w * scale, cell_h * scale * ((len(shots) + 1) // 2)), (44, 46, 52, 255))
    for i, (g, icons, weapon, humanoid, leggings) in enumerate(shots):
        cx, cy = (i % 2) * cell_w // 2 * scale, (i // 2) * cell_h * scale
        tile = Image.new("RGBA", (cell_w // 2, cell_h), (0, 0, 0, 0))
        tile.alpha_composite(front_view(humanoid, leggings), (2, 1))
        for k, im in enumerate(list(icons.values()) + [weapon]):
            tile.alpha_composite(im, (20 + (k % 3) * 17, 1 + (k // 3) * 17))
        img.alpha_composite(tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST), (cx, cy))
        ImageDraw.Draw(img).text((cx + 4, cy + cell_h * scale - 14), g["setName"], fill=(240, 240, 240, 255))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = None
    if "--sheet" in sys.argv:
        out = sys.argv[sys.argv.index("--sheet") + 1]
        args = [a for a in args if a != out]
    main(args[0] if args else "src/main/resources", out)
