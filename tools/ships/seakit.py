"""The sea bosses' flagships, built with the One Piece Mod's own ship kit (its tools/ships/shipkit.py).

    python3 tools/ships/build_flagships.py [widowmaker tithe_cathedral cinderwake] [--previews=DIR]

The main mod's repository must sit next to this one (../one-piece-mod), or set ONEPIECE_TOOLS to its tools folder.
Each flagship writes
    src/main/resources/data/opbosses/structure/ships/<id>.nbt    the blocks
    src/main/resources/data/opbosses/ships/<id>.json             name, waterline, size ("faction": "boss")
The main mod's ShipTemplates reads every data pack's ships/ folder, so it sails them like its own famous ships.
"faction": "boss" keeps them out of its random pirate and Marine encounters: only SeaBosses sends them out.

Rules are the main mod's (its tools/ships/SPECS.md): +x is the bow, the sea surface is y 0, one Ship's Wheel, no
natural blocks, no floating blocks, under 4,500 blocks. Each flagship also has a strongroom: a lair chest locked
to its captain's key (the key the captain drops when beaten aboard).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_TOOLS = os.environ.get("ONEPIECE_TOOLS", os.path.join(os.path.dirname(REPO), "one-piece-mod", "tools"))
sys.path.insert(0, os.path.join(MAIN_TOOLS, "ships"))
os.environ.setdefault("MOD_ASSETS", os.path.join(os.path.dirname(MAIN_TOOLS), "src", "main", "resources", "assets"))

import shipkit  # noqa: E402
from shipkit import *  # noqa: E402,F401,F403
from shipkit import Ship, AIR  # noqa: E402

RES = os.path.join(REPO, "src", "main", "resources")


class BossShip(Ship):
    """A flagship: saved under the opbosses namespace, with the captain's locked strongroom chest."""

    def __init__(self, sid, name, captain, crew):
        super().__init__(sid, name, faction="boss", tiers=(), crew=crew)
        self.captain = captain

    def strongroom(self, x, y, z, facing="south"):
        """The captain's chest: this ship's own lair chest (opbosses:<id>_chest), opened only with key_<captain>."""
        self.set(x, y, z, f"opbosses:{self.sid}_chest[facing={facing}]",
                 {"id": "opbosses:lair_chest", "LootTable": f"opbosses:chests/{self.sid}",
                  "lock": {"items": f"opbosses:key_{self.captain}"}})

    def save(self, res=RES):
        for m in self.check():
            print("  !!", m)
        for m in self.natural_blocks():
            print("  !!", m)
        solid = {p: s for p, s in self.blocks.items() if s != AIR}
        tmp = shipkit._CanvasB()
        tmp.blocks = solid
        tmp.nbt = {p: d for p, d in self.nbt.items() if p in solid}
        tmp.entities = []
        tmp.save(os.path.join(res, "data", "opbosses", "structure", "ships", f"{self.sid}.nbt"))
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        meta = {
            "name": self.name,
            "template": f"opbosses:ships/{self.sid}",
            "bow": "east",
            "waterline": self.water_depth(),
            "faction": "boss",
            "tiers": [],
            "crew": self.crew,
            "length": x1 - x0 + 1,
            "beam": z1 - z0 + 1,
            "height": y1 - y0 + 1,
            "blocks": len(solid),
        }
        jp = os.path.join(res, "data", "opbosses", "ships", f"{self.sid}.json")
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        print(f"{self.sid}: {len(solid)} blocks, {meta['length']}x{meta['height']}x{meta['beam']} (l x h x w), "
              f"waterline {meta['waterline']}")
        return meta


# ---------------------------------------------------------------- checks shared by the flagships
def loose_blocks(s):
    """(blocks not joined to the rest of the ship even diagonally, non-rope blocks with no face neighbour)."""
    solid = {p for p, b in s.blocks.items() if b != AIR}
    start = min(solid, key=lambda p: (p[1], abs(p[2])))
    seen = {start}
    stack = [start]
    while stack:
        x, y, z = stack.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    n = (x + dx, y + dy, z + dz)
                    if n in solid and n not in seen:
                        seen.add(n)
                        stack.append(n)
    faces = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    unsupported = [p for p in solid if "fence" not in s.blocks[p] and "chain" not in s.blocks[p]
                   and not any((p[0] + d[0], p[1] + d[1], p[2] + d[2]) in solid for d in faces)]
    return sorted(solid - seen), sorted(unsupported)


def brace_skin(s, unsupported):
    """Hull skin blocks that touch the ship only diagonally: fill the hollow cell beside them."""
    for (x, y, z) in unsupported:
        mat = s.blocks[(x, y, z)]
        for n in ((x, y, z - (1 if z > 0 else -1)), (x, y - 1, z), (x, y + 1, z)):
            if s._inside(*n) and s.get(*n) in (None, AIR):
                s.set(n[0], n[1], n[2], mat)
                break


def finish(s):
    """Braces the hull skin and reports anything still loose."""
    loose, unsupported = loose_blocks(s)
    if unsupported:
        brace_skin(s, unsupported)
        loose, unsupported = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:12]}")
    if unsupported:
        print(f"  !! {len(unsupported)} blocks without a face neighbour, e.g. {unsupported[:12]}")
    helms = [p for p, b in s.blocks.items() if "ships_wheel" in b]
    for p in helms:
        if p != s.helm_pos:
            s.set(p[0], p[1], p[2], "onepiece:navigators_desk[facing=east]")
    return s


# ---------------------------------------------------------------- previews without the game's textures
# The kit's renderer averages the real block textures. Without the vanilla client assets every vanilla block comes
# out magenta, so fall back to a colour by name: enough to judge shapes and colours here (the in-game test takes
# the real screenshots).
_NAMED = {
    "white": (233, 236, 236), "orange": (240, 118, 19), "magenta": (189, 68, 179), "light_blue": (58, 175, 217),
    "yellow": (248, 197, 39), "lime": (112, 185, 25), "pink": (237, 141, 172), "gray": (62, 68, 71),
    "light_gray": (142, 142, 134), "cyan": (21, 137, 145), "purple": (121, 42, 172), "blue": (53, 57, 157),
    "brown": (114, 71, 40), "green": (84, 109, 27), "red": (161, 39, 34), "black": (20, 21, 25),
}
_WOOD = {"oak": (162, 130, 78), "spruce": (114, 84, 48), "birch": (196, 179, 123), "jungle": (160, 115, 80),
         "acacia": (168, 90, 50), "dark_oak": (66, 43, 20), "mangrove": (117, 54, 48), "cherry": (226, 178, 172),
         "pale_oak": (220, 210, 205), "bamboo": (193, 173, 80), "crimson": (101, 48, 70), "warped": (43, 104, 99)}
_MISC = {"bone_block": (229, 225, 207), "gold_block": (246, 208, 62), "iron_block": (220, 220, 220),
         "chain": (60, 64, 76), "blackstone": (42, 36, 41), "polished_blackstone": (53, 48, 56),
         "polished_blackstone_bricks": (48, 42, 50), "deepslate_tiles": (54, 54, 55), "deepslate_bricks": (70, 70, 71),
         "nether_bricks": (44, 21, 26), "red_nether_bricks": (69, 7, 9), "quartz": (235, 229, 222),
         "smooth_quartz": (235, 229, 222), "calcite": (223, 224, 220), "glowstone": (171, 131, 84),
         "shroomlight": (240, 146, 70), "lantern": (110, 90, 60), "soul_lantern": (70, 110, 120), "bell": (250, 200, 60),
         "candle": (230, 200, 160), "barrel": (110, 80, 45), "chest": (160, 110, 40), "cauldron": (70, 70, 75),
         "furnace": (110, 110, 110), "blast_furnace": (90, 90, 95), "campfire": (230, 140, 40), "bricks": (150, 97, 83),
         "mud_bricks": (137, 103, 79), "anvil": (68, 68, 68), "iron_bars": (110, 110, 110), "lightning_rod": (200, 110, 80),
         "end_rod": (240, 236, 220), "copper": (190, 105, 75), "cut_copper": (190, 105, 75), "terracotta": (152, 94, 67),
         "tinted_glass": (44, 38, 46), "ladder": (125, 96, 52), "netherite_block": (66, 61, 63), "obsidian": (15, 10, 24),
         "crying_obsidian": (40, 10, 70), "redstone_block": (175, 24, 5), "skeleton_skull": (200, 200, 200),
         "bookshelf": (117, 94, 60), "lectern": (170, 135, 85), "smoker": (90, 85, 80), "hay_block": (166, 135, 20)}


def _fallback(state):
    name = state.split("[")[0].split(":")[1]
    if name in _MISC:
        return _MISC[name]
    for color, rgb in sorted(_NAMED.items(), key=lambda kv: -len(kv[0])):
        if name.startswith(color + "_"):
            return rgb
    for wood, rgb in sorted(_WOOD.items(), key=lambda kv: -len(kv[0])):
        if wood in name:
            return rgb
    for key, rgb in _MISC.items():
        if key in name:
            return rgb
    if "glass" in name:
        return (175, 210, 225)
    if state.startswith("onepiece:") or state.startswith("opbosses:"):
        return None
    return (128, 128, 128)


def install_preview_colours():
    import render
    original = render.block_colors

    def colours(state):
        out = original(state)
        if out is not None and not (out[1][0] >= 190 and out[1][1] < 40 and out[1][2] >= 190):
            return out
        rgb = _fallback(state)
        if rgb is None:
            return out
        import numpy as np
        return (np.array([min(255, c * 1.08) for c in rgb]), np.array(rgb, dtype=float))
    render.block_colors = colours
    render._cache.clear()
