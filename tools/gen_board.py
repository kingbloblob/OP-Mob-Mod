#!/usr/bin/env python3
"""Draws the Marine Bounty Board block (opbosses:marine_bounty_board): model, textures, blockstate and item model.

    python3 tools/gen_board.py src/main/resources

A standing notice board on two spruce posts under a navy Marine roof. The front (north, z = 0 side; the blockstate
turns it to face the player) is a cork board with the Marines' white gull on a navy header and three Wanted notices
pinned below. Same conventions as gen_chests.py: 16 units = 1 block, textures 16x16 with row 0 at the top.
"""
import json
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


NAVY = '#1f3a6b'
WHITE = '#eef2f6'
CORK = '#a8774a'
PAPER = '#e9dcb4'
RED = '#a5302a'
INK = '#3a2c22'
WOOD = '#5b3f27'


def front():
    img = new(CORK, 0.18, 1)
    # Navy header (panel rows 2-4) with a white trim line and the gull.
    rect(img, 0, 2, 15, 4, NAVY)
    rect(img, 0, 5, 15, 5, WHITE)
    # The Marine gull: a wide shallow "v" of wings with a head in the middle.
    for x, y in [(4, 3), (5, 2), (6, 3), (7, 4), (8, 4), (9, 3), (10, 2), (11, 3)]:
        put(img, x, y, WHITE)
    put(img, 7, 3, WHITE); put(img, 8, 3, WHITE)
    # Three Wanted notices, each with a red WANTED bar, a face and a bounty line, and a pin.
    rnd = random.Random(7)
    for i, x0 in enumerate((1, 6, 11)):
        y0 = 6 + (i % 2)
        rect(img, x0, y0, x0 + 3, y0 + 5, PAPER)
        rect(img, x0, y0 + 1, x0 + 3, y0 + 1, RED)
        rect(img, x0 + 1, y0 + 2, x0 + 2, y0 + 3, shade(rgb(INK), 0.9 + 0.3 * rnd.random()))
        rect(img, x0, y0 + 5, x0 + 3, y0 + 5, shade(rgb(PAPER), 0.8))
        put(img, x0 + 1, y0 + 4, INK); put(img, x0 + 2, y0 + 4, INK)
        put(img, x0 + 1, y0, '#c9c9c9')
    # Dark edge of the frame showing under the notices.
    rect(img, 0, 13, 15, 13, shade(rgb(CORK), 0.7))
    return img


def back():
    img = new(WOOD, 0.14, 2)
    for y in range(0, S, 4):
        rect(img, 0, y, 15, y, shade(rgb(WOOD), 0.75))
    rect(img, 0, 2, 15, 4, NAVY)
    return img


def frame():
    img = new(WOOD, 0.14, 3)
    for y in (0, 15):
        rect(img, 0, y, 15, y, shade(rgb(WOOD), 0.7))
    return img


def roof():
    img = new(NAVY, 0.1, 4)
    rect(img, 0, 0, 15, 0, WHITE)
    rect(img, 0, 15, 15, 15, WHITE)
    for x in range(0, S, 4):
        put(img, x, 7, shade(rgb(NAVY), 1.3))
    return img


def box(frm, to, faces, uv=None):
    out = {}
    for name, tex in faces.items():
        face = {"texture": tex}
        if uv and name in uv:
            face["uv"] = uv[name]
        if name == "down" and frm[1] == 0:
            face["cullface"] = "down"
        out[name] = face
    return {"from": frm, "to": to, "faces": out}


def all_faces(tex):
    return {f: tex for f in ("north", "south", "east", "west", "up", "down")}


def model():
    elements = [
        # Posts.
        box([1, 0, 7], [3, 15.5, 9], all_faces("#post")),
        box([13, 0, 7], [15, 15.5, 9], all_faces("#post")),
        # The board: cork face north, plank back south.
        box([0, 3, 7.5], [16, 14, 8.5], {"north": "#front", "south": "#back", "east": "#frame", "west": "#frame",
                                          "up": "#frame", "down": "#frame"},
            uv={"north": [0, 2, 16, 13], "south": [0, 2, 16, 13]}),
        # Frame rails above and below the board.
        box([0, 14, 7], [16, 15, 9], all_faces("#frame")),
        box([0, 2.5, 7], [16, 3.5, 9], all_faces("#frame")),
        # The navy roof that keeps the rain off the notices.
        box([-1, 15, 5.5], [17, 16.5, 10.5], all_faces("#roof")),
    ]
    return {
        "parent": "minecraft:block/block",
        "textures": {"front": "opbosses:block/bounty_board/front", "back": "opbosses:block/bounty_board/back",
                     "frame": "opbosses:block/bounty_board/frame", "roof": "opbosses:block/bounty_board/roof",
                     "post": "minecraft:block/spruce_log", "particle": "opbosses:block/bounty_board/frame"},
        "elements": elements,
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main(res):
    assets = os.path.join(res, "assets/opbosses")
    tex = os.path.join(assets, "textures/block/bounty_board")
    os.makedirs(tex, exist_ok=True)
    for name, draw in (("front", front), ("back", back), ("frame", frame), ("roof", roof)):
        draw().save(os.path.join(tex, name + ".png"))
    write_json(os.path.join(assets, "models/block/marine_bounty_board.json"), model())
    write_json(os.path.join(assets, "blockstates/marine_bounty_board.json"), {"variants": {
        "facing=north": {"model": "opbosses:block/marine_bounty_board"},
        "facing=east": {"model": "opbosses:block/marine_bounty_board", "y": 90},
        "facing=south": {"model": "opbosses:block/marine_bounty_board", "y": 180},
        "facing=west": {"model": "opbosses:block/marine_bounty_board", "y": 270}}})
    write_json(os.path.join(assets, "items/marine_bounty_board.json"),
               {"model": {"type": "minecraft:model", "model": "opbosses:block/marine_bounty_board"}})
    print("Drew the Marine Bounty Board")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "src/main/resources")
