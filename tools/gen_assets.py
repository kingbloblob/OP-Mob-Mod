#!/usr/bin/env python3
"""Draws the poster, trophy and lair key art and writes the item JSON and names for every rogue boss in bosses.json.
(The bosses' bodies and skins are tools/gen_models.py.)

    python3 tools/gen_assets.py src/main/resources

Needs Pillow. A new boss's trophy needs a look in TROPHIES, or this stops and says which one is missing.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_chests import CHESTS  # noqa: E402  (the lair chests' names)

# Trophy item: (main colour, shade, shape).
TROPHIES = {
    "rusted_anchor_link": ((150, 90, 50), (90, 55, 30), "ring"),
    "widows_lantern": ((230, 190, 90), (60, 50, 70), "lantern"),
    "deserters_epaulette": ((210, 180, 60), (130, 100, 30), "epaulette"),
    "hollow_menpo": ((40, 36, 46), (120, 230, 255), "mask"),
    "cracked_boiler_core": ((255, 140, 30), (80, 60, 50), "core"),
    "abyssal_conch": ((240, 220, 200), (60, 140, 160), "conch"),
    "broken_shackle": ((120, 120, 128), (200, 160, 90), "shackle"),
    "cursed_doubloon": ((236, 196, 64), (64, 240, 208), "doubloon"),
    "sea_king_bridle": ((110, 70, 40), (58, 122, 138), "bridle"),
    "prototype_core": ((96, 224, 255), (90, 106, 122), "prototype"),
    "golden_casino_chip": ((240, 200, 60), (170, 30, 40), "chip"),
    "diva_headphones": ((244, 244, 248), (232, 144, 184), "headphones"),
    "smasher_knuckle": ((110, 90, 150), (50, 50, 60), "knuckle"),
    "clank_clank_rivet": ((150, 150, 160), (70, 70, 80), "rivet"),
    "golden_lion_helm": ((140, 90, 48), (240, 200, 64), "wheel"),
    "golden_nail": ((240, 200, 64), (150, 100, 30), "claw"),
    "syrup_spike": ((230, 160, 50), (150, 80, 20), "spike"),
    "red_arrow": ((200, 40, 40), (240, 200, 60), "arrow"),
    "clockwork_gear": ((200, 170, 70), (200, 40, 40), "gear"),
    "broken_horn": ((232, 224, 200), (110, 60, 140), "horn"),
    "sea_king_harpoon": ((180, 180, 190), (110, 70, 40), "arrow"),
    "red_tithe_censer": ((230, 180, 50), (150, 20, 20), "lantern"),
    "cinder_heart": ((255, 120, 30), (40, 34, 36), "core"),
}

TROPHY_NAMES = {
    "rusted_anchor_link": "Rusted Anchor Link",
    "widows_lantern": "Widow's Lantern",
    "deserters_epaulette": "Deserter's Epaulette",
    "hollow_menpo": "Hollow Menpo",
    "cracked_boiler_core": "Cracked Boiler Core",
    "abyssal_conch": "Abyssal Conch",
    "broken_shackle": "Broken Sandshackle",
    "cursed_doubloon": "Cursed Doubloon",
    "sea_king_bridle": "Sea King Bridle",
    "prototype_core": "Prototype Core",
    "golden_casino_chip": "Tesoro's Golden Chip",
    "diva_headphones": "Diva's Headphones",
    "smasher_knuckle": "Battle Smasher Knuckle",
    "clank_clank_rivet": "Clank-Clank Rivet",
    "golden_lion_helm": "Golden Lion's Helm",
    "golden_nail": "El Drago's Golden Nail",
    "syrup_spike": "Hardened Syrup Spike",
    "red_arrow": "Red Arrow of Omatsuri",
    "clockwork_gear": "Karakuri Clockwork Gear",
    "broken_horn": "World's Broken Horn",
    "sea_king_harpoon": "Harpoon Queen's Harpoon",
    "red_tithe_censer": "Red Tithe Censer",
    "cinder_heart": "Cinder Heart",
}

# The Sea King mini-bosses (sea/SeaKingBosses.java): entity name, and the trophy each drops (id, name, look).
SEA_KINGS = {
    "gulpmaw": ("Gulpmaw, the Lantern Deep", ("gulpmaw_lure", "Gulpmaw's Lure", ((150, 255, 200), (40, 60, 70), "core"))),
    "ironscale": ("Ironscale, the Keelbreaker", ("ironscale_plate", "Ironscale Plate", ((120, 130, 140), (60, 70, 80), "shackle"))),
    "thundercoil": ("Thundercoil, the Storm Serpent", ("thundercoil_fang", "Thundercoil Fang", ((240, 240, 160), (60, 90, 200), "claw"))),
}


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def box(d, x, y, w, h, c):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=c + (255,))


def item_texture(main, dark, shape):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shape == "ring":
        d.ellipse([2, 3, 13, 12], outline=main + (255,), width=3); d.point([(4, 9), (10, 5)], fill=dark + (255,))
    elif shape == "lantern":
        box(d, 6, 1, 4, 2, dark); box(d, 4, 3, 8, 10, dark); box(d, 5, 4, 6, 8, main); box(d, 5, 13, 6, 2, dark)
    elif shape == "epaulette":
        d.ellipse([2, 4, 13, 10], fill=main + (255,)); [box(d, x, 10, 1, 4, dark) for x in range(3, 13, 2)]
    elif shape == "mask":
        d.ellipse([2, 2, 13, 14], fill=main + (255,)); box(d, 4, 6, 3, 2, dark); box(d, 9, 6, 3, 2, dark)
        box(d, 5, 11, 6, 1, (90, 20, 24))
    elif shape == "core":
        d.ellipse([2, 2, 13, 13], fill=dark + (255,)); d.ellipse([5, 5, 10, 10], fill=main + (255,))
        d.line([(3, 4), (7, 8), (6, 12)], fill=(20, 20, 20, 255))
    elif shape == "conch":
        d.polygon([(2, 12), (8, 2), (14, 9), (9, 14)], fill=main + (255,)); d.line([(4, 11), (9, 5), (12, 9)], fill=dark + (255,))
    elif shape == "chip":
        d.ellipse([1, 1, 14, 14], fill=main + (255,)); d.ellipse([4, 4, 11, 11], outline=dark + (255,))
        for (x, y) in ((7, 1), (7, 13), (1, 7), (13, 7)):
            box(d, x, y, 2, 2, dark)
        box(d, 7, 6, 2, 4, shade(main, 0.7))
    elif shape == "headphones":
        d.arc([2, 1, 13, 12], 180, 360, fill=main + (255,), width=2)
        box(d, 1, 7, 4, 6, dark); box(d, 11, 7, 4, 6, dark); box(d, 2, 8, 2, 4, main); box(d, 12, 8, 2, 4, main)
    elif shape == "knuckle":
        box(d, 2, 4, 12, 9, main); [box(d, x, 3, 2, 2, dark) for x in (3, 6, 9, 12)]
        box(d, 2, 8, 12, 1, dark); box(d, 4, 10, 8, 1, (200, 170, 255))
    elif shape == "rivet":
        d.polygon([(8, 1), (14, 5), (14, 11), (8, 15), (2, 11), (2, 5)], fill=main + (255,))
        d.ellipse([5, 5, 10, 10], fill=dark + (255,)); d.point([(6, 6)], fill=(230, 230, 240, 255))
    elif shape == "wheel":
        d.ellipse([2, 2, 13, 13], outline=main + (255,), width=2)
        d.line([(8, 0), (8, 15)], fill=main + (255,)); d.line([(0, 8), (15, 8)], fill=main + (255,))
        d.line([(3, 3), (12, 12)], fill=main + (255,)); d.line([(12, 3), (3, 12)], fill=main + (255,))
        d.ellipse([6, 6, 9, 9], fill=dark + (255,))
    elif shape == "shackle":
        # An iron cuff snapped open, its chain broken off.
        d.arc([2, 2, 11, 11], 30, 330, fill=main + (255,), width=2); box(d, 10, 5, 2, 3, dark)
        for i, (x, y) in enumerate(((11, 9), (12, 11), (13, 13))):
            d.ellipse([x, y, x + 2, y + 2], outline=shade(main, 1.2) + (255,))
    elif shape == "doubloon":
        # A gold coin with a skull struck on it, glowing with the curse.
        d.ellipse([1, 1, 14, 14], fill=main + (255,)); d.ellipse([2, 2, 13, 13], outline=shade(main, 0.75) + (255,))
        d.ellipse([5, 4, 10, 9], fill=shade(main, 0.6) + (255,)); box(d, 6, 6, 1, 1, dark); box(d, 9, 6, 1, 1, dark)
        box(d, 6, 10, 4, 1, shade(main, 0.6)); d.point([(1, 1), (14, 2), (13, 14)], fill=dark + (255,))
    elif shape == "bridle":
        # Leather reins and a bit sized for a Sea King's jaw, with a scale charm.
        d.arc([1, 1, 14, 14], 200, 340, fill=main + (255,), width=2); d.line([(3, 12), (8, 4), (12, 12)], fill=main + (255,), width=2)
        box(d, 2, 11, 3, 3, (180, 180, 190)); box(d, 11, 11, 3, 3, (180, 180, 190)); d.ellipse([6, 9, 10, 13], fill=dark + (255,))
    elif shape == "prototype":
        # A Pacifista prototype's reactor core: a glowing cell in a steel cage.
        box(d, 4, 1, 8, 2, dark); box(d, 4, 13, 8, 2, dark); box(d, 5, 3, 6, 10, main); box(d, 7, 4, 2, 8, (230, 255, 255))
        for x in (3, 12):
            box(d, x, 2, 1, 12, dark)
    elif shape == "claw":
        # A hooked golden fingernail.
        d.polygon([(4, 14), (6, 4), (10, 1), (13, 3), (9, 6), (8, 14)], fill=main + (255,))
        d.line([(10, 2), (6, 12)], fill=shade(main, 1.15) + (255,)); box(d, 4, 13, 5, 2, dark)
    elif shape == "spike":
        # A spike of set amber syrup, still dripping.
        d.polygon([(8, 0), (12, 13), (4, 13)], fill=main + (255,)); d.line([(8, 2), (6, 12)], fill=(255, 220, 140, 255))
        box(d, 3, 13, 10, 2, dark); box(d, 11, 14, 1, 2, main)
    elif shape == "arrow":
        d.line([(2, 13), (12, 3)], fill=(120, 80, 40, 255), width=1)
        d.polygon([(10, 2), (14, 1), (13, 5)], fill=main + (255,))
        d.polygon([(1, 12), (3, 15), (4, 11)], fill=dark + (255,)); d.polygon([(2, 10), (5, 12), (5, 9)], fill=main + (255,))
    elif shape == "gear":
        for a in range(0, 360, 45):
            import math as _m
            x, y = 7.5 + 6 * _m.cos(_m.radians(a)), 7.5 + 6 * _m.sin(_m.radians(a))
            box(d, int(round(x)) - 1, int(round(y)) - 1, 2, 2, main)
        d.ellipse([2, 2, 13, 13], fill=main + (255,)); d.ellipse([5, 5, 10, 10], fill=shade(main, 0.6) + (255,))
        d.ellipse([6, 6, 9, 9], fill=dark + (255,))
    elif shape == "horn":
        d.polygon([(3, 14), (7, 14), (10, 6), (9, 3), (6, 7)], fill=main + (255,))
        d.line([(9, 3), (10, 6)], fill=(150, 140, 120, 255)); d.point([(8, 4), (10, 4), (9, 5)], fill=(150, 140, 120, 255))   # the break
        box(d, 2, 13, 7, 2, dark)
    elif shape == "key":
        # An old iron-bound key: a ring bow in the boss's colour, a long shaft and a toothed bit.
        d.ellipse([1, 1, 7, 7], outline=main + (255,), width=2); d.point([(4, 4)], fill=dark + (255,))
        d.line([(6, 6), (13, 13)], fill=shade(main, 0.8) + (255,), width=2)
        box(d, 10, 12, 2, 3, dark); box(d, 12, 10, 3, 2, dark); box(d, 13, 13, 2, 2, dark)
    elif shape == "charter":
        # A rolled charter with a gold seal: the lair's plans, to rebuild it.
        box(d, 3, 2, 10, 12, (225, 205, 160)); box(d, 2, 1, 12, 2, (150, 110, 70)); box(d, 2, 13, 12, 2, (150, 110, 70))
        for y in (4, 6, 8):
            box(d, 5, y, 6, 1, (110, 90, 70))
        d.ellipse([8, 8, 13, 13], fill=main + (255,)); d.point([(10, 10)], fill=dark + (255,))
    elif shape == "poster":
        box(d, 2, 1, 12, 14, (215, 190, 140)); box(d, 3, 2, 10, 2, (90, 40, 30))
        box(d, 5, 5, 6, 5, (120, 110, 100)); box(d, 7, 6, 2, 1, (40, 30, 30))   # a figure in shadow
        box(d, 4, 11, 8, 1, (90, 40, 30)); box(d, 6, 13, 4, 1, (90, 40, 30))
        box(d, 12, 1, 2, 2, main)                                                  # tier-coloured seal
    return img


POSTER_SEAL = {1: (230, 230, 230), 2: (120, 200, 120), 3: (240, 200, 60), 4: (170, 80, 220), 5: (220, 40, 40)}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main(res):
    bosses = json.load(open(os.path.join(res, "opbosses/bosses.json")))["bosses"]
    assets = os.path.join(res, "assets/opbosses")
    missing = [b["trophy"] for b in bosses if b.get("trophy") and b["trophy"] not in TROPHIES]
    if missing:
        sys.exit("No look yet for: " + ", ".join(missing) + " (add them to TROPHIES)")
    lang = {"itemGroup.opbosses.bosses": "One Piece: Rogue Bosses", "entity.opbosses.rogue_boss": "Rogue Boss",
            "entity.opbosses.wandering_hunter": "Wandering Bounty Hunter", "entity.opbosses.rookie_raider": "Rookie Raider"}
    for b in bosses:
        items = [("rumor_" + b["id"], item_texture(POSTER_SEAL[b["tier"]], None, "poster"))]
        key_c, key_d = (TROPHIES[b["trophy"]][:2] if b.get("trophy") else ((200, 170, 70), (70, 60, 50)))
        items.append(("key_" + b["id"], item_texture(key_c, key_d, "key")))
        if b.get("trophy"):
            main_c, dark, shape = TROPHIES[b["trophy"]]
            items.append((b["trophy"], item_texture(main_c, dark, shape)))
            lang["item.opbosses." + b["trophy"]] = TROPHY_NAMES.get(b["trophy"], b["trophy"].replace("_", " ").title())
        for name, texture in items:
            os.makedirs(os.path.join(assets, "textures/item"), exist_ok=True)
            texture.save(os.path.join(assets, "textures/item", name + ".png"))
            write_json(os.path.join(assets, "models/item", name + ".json"),
                       {"parent": "minecraft:item/generated", "textures": {"layer0": "opbosses:item/" + name}})
            write_json(os.path.join(assets, "items", name + ".json"),
                       {"model": {"type": "minecraft:model", "model": "opbosses:item/" + name}})
    for sid, (name, (trophy, trophy_name, (main_c, dark, shape))) in SEA_KINGS.items():
        lang["entity.opbosses." + sid] = name
        lang["item.opbosses." + trophy] = trophy_name
        item_texture(main_c, dark, shape).save(os.path.join(assets, "textures/item", trophy + ".png"))
        write_json(os.path.join(assets, "models/item", trophy + ".json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": "opbosses:item/" + trophy}})
        write_json(os.path.join(assets, "items", trophy + ".json"), {"model": {"type": "minecraft:model", "model": "opbosses:item/" + trophy}})
    charter = item_texture((220, 170, 50), (150, 30, 30), "charter")
    os.makedirs(os.path.join(assets, "textures/item"), exist_ok=True)
    charter.save(os.path.join(assets, "textures/item", "lair_charter.png"))
    write_json(os.path.join(assets, "models/item", "lair_charter.json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": "opbosses:item/lair_charter"}})
    write_json(os.path.join(assets, "items", "lair_charter.json"), {"model": {"type": "minecraft:model", "model": "opbosses:item/lair_charter"}})
    lang["item.opbosses.lair_charter"] = "Lair Restoration Charter"
    for cid, c in CHESTS.items():
        lang["block.opbosses." + cid + "_chest"] = c["name"]
    write_json(os.path.join(assets, "lang/en_us.json"), lang)
    print("Drew %d bosses" % len(bosses))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "src/main/resources")
