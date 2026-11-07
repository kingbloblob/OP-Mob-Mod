"""Sharper skins for the bosses, still pixel art.

gen_models.py paints every skin at 1 texel per model pixel. This scales it up SCALE times with no smoothing (each
texel becomes a crisp SCALE x SCALE block, so cloth and armour look exactly as before) and then redraws every face
at the full resolution, so eyes, brows and mouths get enough pixels to read as the anime characters: eyes with a
lash line, iris and highlight, brows that frown, a nose shadow and a proper mouth. The model's boxes and UVs don't
change: Minecraft maps a skin by its declared size (128 or 256), so a bigger PNG just has more pixels per face.
"""
from PIL import Image

SCALE = 2


def upscale(img):
    return img.resize((img.width * SCALE, img.height * SCALE), Image.Resampling.NEAREST)


def hexc(c):
    if isinstance(c, tuple):
        return c
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def paint_face(img, x0, y0, w, h, box):
    """Pixel-art anime face on the front of a face box: (x0, y0) is the face's corner on the 1x skin, w x h its size."""
    s = SCALE
    X, Y = x0 * s, y0 * s
    W, H = int(round(w)) * s, int(round(h)) * s
    px = img.load()

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[X + x, Y + y] = hexc(c) + (255,)

    skin = hexc(box['colour'])
    # Clean skin with a darker column down each side, like the rest of the boxes' shading.
    for y in range(H):
        for x in range(W):
            put(x, y, shade(skin, 0.9) if x in (0, W - 1) else skin)
    cx = W // 2
    ey = int(H * 0.5)
    female = bool(box.get('lashes'))
    gap = 1 if W < 14 else 2
    ew = 3 if W < 18 else 4
    eyes = (cx - gap - ew, cx + gap)   # left x of her/his right eye (screen left) and the other
    dark = (24, 18, 22)
    if box.get('goggles'):
        for ex in eyes:
            for dx in range(ew):
                for dy in (-1, 0, 1):
                    put(ex + dx, ey + dy, '#ffb43c' if dy < 1 else '#c87820')
            put(ex, ey - 1, '#ffe8a8')
        for x in range(eyes[0] + ew, eyes[1]):
            put(x, ey, '#5a4a3a')
    elif box.get('eyes'):
        iris = hexc(box['eyes'])
        for i, ex in enumerate(eyes):
            inner = ex + ew - 1 if i == 0 else ex
            outer = ex if i == 0 else ex + ew - 1
            if box.get('slit'):
                for dx in range(ew):
                    put(ex + dx, ey, iris)
                    put(ex + dx, ey + 1, iris)
                put(ex + ew // 2, ey, dark); put(ex + ew // 2, ey + 1, dark)
                continue
            if box.get('narrow'):
                for dx in range(ew):
                    put(ex + dx, ey, dark)
                put(inner - (1 if i == 0 else -1), ey + 1, iris)
                continue
            for dx in range(ew):
                put(ex + dx, ey - 1, dark)             # lash line
                put(ex + dx, ey, '#f8f6f2')            # white
                put(ex + dx, ey + 1, '#f8f6f2')
            # the iris sits on the inner side, looking at you, with a highlight on top
            ix = [inner, inner - 1] if i == 0 else [inner, inner + 1]
            for x in ix:
                put(x, ey, iris)
                put(x, ey + 1, shade(iris, 0.6))
            put(ix[1], ey, shade(iris, 1.6))
            if female:
                put(outer + (-1 if i == 0 else 1), ey - 1, dark)   # flicked lashes
                put(outer + (-1 if i == 0 else 1), ey - 2, dark)
                put(ex + 1, ey + 3, shade(skin, 0.86) if False else (236, 150, 150))   # blush
    if box.get('shades'):
        sc = hexc(box['shades'])
        for x in range(1, W - 1):
            put(x, ey - 1, (20, 20, 24))
            put(x, ey, sc)
            put(x, ey + 1, shade(sc, 0.75))
        put(2, ey, shade(sc, 1.5)); put(cx + 2, ey, shade(sc, 1.5))
    if box.get('monocle'):
        ex = eyes[1]
        for dx in range(-1, ew + 1):
            put(ex + dx, ey - 2, '#e8c040'); put(ex + dx, ey + 2, '#e8c040')
        for dy in range(-1, 2):
            put(ex - 1, ey + dy, '#e8c040'); put(ex + ew, ey + dy, '#e8c040')
        for dy in range(3, H - ey):
            put(ex + ew, ey + dy, '#c8a030')
    if box.get('brows'):
        bc = box['brows']
        by = ey - 3 if H >= 12 else ey - 2
        for i, ex in enumerate(eyes):
            for dx in range(ew + 1):
                x = ex - 1 + dx if i == 0 else ex + dx
                inner_end = (dx >= ew - 1) if i == 0 else (dx <= 1)
                put(x, by + (1 if inner_end else 0), bc)   # the inner ends dip: a frown
    if box.get('scar'):
        for i in range(5):
            put(eyes[0] - 1 + i, ey - 3 + i + (i // 2), '#a05a50')
    put(cx - (0 if W % 2 else 1), ey + 3, shade(skin, 0.78))   # nose shadow
    mouth = box.get('mouth')
    my = H - 3 if H >= 12 else H - 2
    line = shade(skin, 0.45)
    if mouth == 'smirk':
        for dx in range(-2, 2):
            put(cx + dx, my, line)
        put(cx + 2, my - 1, line)
    elif mouth == 'grin':
        for dx in range(-3, 3):
            put(cx + dx, my - 1, line)
            put(cx + dx, my, '#f8f8f0')
            put(cx + dx, my + 1, line if abs(dx + 0.5) < 2.5 else skin)
        put(cx - 1, my, '#e8c040')   # a gold tooth
        put(cx - 4, my - 1, line); put(cx + 3, my - 1, line)
    elif mouth == 'roar':
        for dx in range(-3, 3):
            put(cx + dx, my - 1, '#f4f0e8' if dx % 2 else '#3a0a0a')
            put(cx + dx, my, '#3a0a0a')
            put(cx + dx, my + 1, '#f4f0e8' if dx % 2 == 0 else '#3a0a0a')
    elif mouth == 'gap':
        for dx in range(-3, 3):
            put(cx + dx, my, '#2a1010' if dx in (-2, 1) else '#f4f0e0')
            put(cx + dx, my - 1, line)
    elif mouth == 'grit':
        for dx in range(-3, 3):
            put(cx + dx, my, '#f0f0e8' if dx % 2 else '#c8c8c0')
            put(cx + dx, my - 1, line)
            put(cx + dx, my + 1, line)
