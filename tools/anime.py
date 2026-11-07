"""The film villains, built to their anime proportions, still out of Minecraft cubes.

The original rogues in gen_models.py are designed box by box with wild proportions. The film villains are canon
characters, so they are built here from one anime figure instead (figure()): a head about a seventh of the height
with a drawn face (skin.py), a neck, a chest that steps in to the waist, hips, arms that reach mid-thigh and long
legs. Each character then sets its build (shoulders, waist,
limb thickness, head count), its clothes, and adds its hair and props on top, measured from the figure's landmarks.

Proportions follow each character's look in the films (One Piece fandom wiki character pages and film stills):
heads-tall, how broad the shoulders are against the head, where the waist sits, how long the legs are.
"""


def B(part, x, y, z, w, h, d, colour, pattern=None, **extra):
    return dict(part=part, x=x, y=y, z=z, w=w, h=h, d=d, colour=colour, pattern=pattern, **extra)


class L:
    """A figure's landmarks, for placing hair and props. Head boxes: y runs -hh (crown) to 0 (chin), x across
    -hw..hw, z -hd (face) .. hd. Body boxes: y 0 is the shoulder line, T is the hip line. Arm boxes start at the
    shoulder joint (A long); leg boxes at the hip joint (LL long)."""


def figure(H, heads=7.0, *, head_w=0.8, head_d=0.92, chin=0.78, neck=0.3, neck_w=0.42,
           shoulder=5.0, chest_d=4.6, waist=3.4, hip=3.9, belly_d=None,
           arm=3.0, fore=2.7, hand=2.5, leg=3.6, calf=2.9, foot=3.0, legs=0.48, reach=0.1,
           skin='#e0b090', face=None,
           top='#f0f0f0', top_pat='cloth', top_front=None,
           belly=None, belly_pat=None, belly_front=None,
           belt=None, belt_pat='leather', belt_front='buckle',
           sleeve=None, sleeve_pat=None, fore_col=None, fore_pat=None, cuff=None,
           sleeve_left=None, fore_left=None, left_pat=None,
           hand_col=None, hand_pat=None, hand_front=None,
           pants='#303038', pants_pat='cloth', shin=None, shin_pat=None, shoes='#202024', shoes_pat='leather',
           right_arm=True, shins=True, feet=True, pivots_extra=None):
    l = L()
    l.H = H
    l.hh = hh = H / heads
    l.top = top_y = 24 - H
    chin_y = top_y + hh
    l.y_s = y_s = chin_y + neck * hh
    l.y_h = y_h = 24 - legs * H
    l.T = T = y_h - y_s
    l.hw = hw = hh * head_w / 2
    l.hd = hd = hh * head_d / 2
    l.cw = cw = shoulder - arm * 0.32
    l.waist, l.hip, l.chest_d = waist, hip, chest_d
    belly_d = belly_d or chest_d * 0.9
    l.belly_d = belly_d
    arm_y = y_s + arm * 0.4
    l.A = A = (y_h + reach * H) - arm_y
    l.upper, l.fore_len, l.hand_len = A * 0.42, A * 0.38, A * 0.2
    l.LL = LL = 24 - y_h
    l.foot_h = foot_h = max(1.4, LL * 0.085)
    lx = max(hip * 0.48, leg * 0.5 + 0.05)
    l.lx = lx
    face = dict(face or {})
    sleeve = sleeve or top
    sleeve_pat = sleeve_pat if sleeve_pat is not None else top_pat
    fore_col = fore_col or sleeve
    fore_pat = fore_pat if fore_pat is not None else sleeve_pat
    belly = belly or top
    belly_pat = belly_pat if belly_pat is not None else top_pat
    shin = shin or pants
    shin_pat = shin_pat if shin_pat is not None else pants_pat

    boxes = [
        B('head', -hw, -hh, -hd, 2 * hw, hh, 2 * hd, skin, None, front='face', **face),
        B('body', -hh * neck_w / 2, -neck * hh - 0.8, -hh * neck_w / 2, hh * neck_w, neck * hh + 1.6, hh * neck_w * 0.9, skin),
        B('body', -cw, -0.2, -chest_d / 2, 2 * cw, T * 0.55 + 0.2, chest_d, top, top_pat, front=top_front),
        B('body', -waist, T * 0.55 - 0.3, -belly_d / 2, 2 * waist, T * 0.27 + 0.6, belly_d, belly, belly_pat, front=belly_front),
    ]
    if belt:
        bw = waist + (hip - waist) * 0.45 + 0.25
        boxes.append(B('body', -bw, T * 0.8, -belly_d / 2 - 0.25, 2 * bw, max(1.0, T * 0.08), belly_d + 0.5, belt, belt_pat, front=belt_front))
    pw = waist + (hip - waist) * 0.5
    boxes.append(B('body', -pw, T * 0.82, -belly_d / 2, 2 * pw, T * 0.18 + 1.2, belly_d, pants, pants_pat))

    def arm_boxes(sl, fc, sp, fp, only):
        ex = dict(only=only) if only else {}
        return [
            B('arm', -arm / 2, 0, -arm / 2, arm, l.upper + 0.5, arm, sl, sp, **ex),
            B('arm', -fore / 2, l.upper, -fore / 2, fore, l.fore_len + 0.3, fore, fc, fp, front=cuff, **ex),
        ]
    if right_arm:
        if sleeve_left or fore_left:
            boxes += arm_boxes(sleeve, fore_col, sleeve_pat, fore_pat, 'right')
            boxes += arm_boxes(sleeve_left or sleeve, fore_left or fore_col, left_pat or sleeve_pat, left_pat or fore_pat, 'left')
        else:
            boxes += arm_boxes(sleeve, fore_col, sleeve_pat, fore_pat, None)
        boxes.append(B('arm', -hand * 0.45, l.upper + l.fore_len, -hand * 0.5, hand * 0.9, l.hand_len, hand,
                       hand_col or skin, hand_pat, front=hand_front))
    else:
        boxes += arm_boxes(sleeve_left or sleeve, fore_left or fore_col, left_pat or sleeve_pat, left_pat or fore_pat, 'left')
        boxes.append(B('arm', -hand * 0.45, l.upper + l.fore_len, -hand * 0.5, hand * 0.9, l.hand_len, hand,
                       hand_col or skin, hand_pat, front=hand_front, only='left'))
    boxes.append(B('leg', -leg / 2, -0.6, -leg / 2, leg, LL * 0.5 + 0.6, leg, pants, pants_pat))
    if shins:
        boxes.append(B('leg', -calf / 2, LL * 0.5 - 0.1, -calf / 2, calf, LL * 0.5 - foot_h + 0.4, calf, shin, shin_pat))
    if feet:
        boxes.append(B('leg', -foot * 0.45, LL - foot_h, -foot * 0.78, foot * 0.9, foot_h, foot * 1.45, shoes, shoes_pat))
    pivots = dict(head=(0, chin_y, 0), body=(0, y_s, 0), arm=(-shoulder, arm_y, 0), leg=(-lx, y_h, 0))
    return dict(pivots=pivots, boxes=boxes), l


def hair(l, colour, pat='hair', lift=0.6, back=0.75, sides=0.5, fringe=None, thick=1.6):
    """A head of hair over the figure's skull: a cap, the back, the sides, and an optional fringe."""
    hh, hw, hd = l.hh, l.hw, l.hd
    out = [
        # a cap over the crown, stopping above the eyes
        B('head', -hw - 0.4, -hh - lift, -hd - 0.3, 2 * hw + 0.8, hh * 0.2 + lift, 2 * hd + 0.7, colour, pat),
        B('head', -hw - 0.35, -hh * 0.8, hd * 0.2, 2 * hw + 0.7, hh * back, hd * 0.8 + 0.4, colour, pat),
    ]
    if sides:
        out.append(B('head', -hw - 0.45, -hh * 0.82, -hd + hh * 0.25, 1.1, hh * sides, 2 * hd - hh * 0.25, colour, pat, mirror=True))
    if fringe:
        out.append(B('head', -hw, -hh * 0.82, -hd - 0.45, 2 * hw, hh * fringe, 0.8, colour, pat))
    return out


FILM = {}


# Gild Tesoro (Film Gold): very tall and lean-muscled, about 7.5 heads, broad shoulders and long legs. Slicked-back
# green hair, tinted shades and star earrings; a white show jacket dotted with gold stars and a rose, over a gold shirt,
# gold trousers and shoes, a ring on every finger and a star on a chain at his right shoulder.
def _tesoro():
    s, l = figure(41, 7.5, skin='#a06e4a', shoulder=6.2, chest_d=4.8, waist=3.4, hip=3.9, arm=3.1, fore=2.7, hand=2.5,
                  leg=3.5, calf=2.8, foot=2.9, legs=0.5, chin=0.74,
                  face=dict(eyes=None, brows=None, mouth='grin', shades='#e8c040'),
                  top='#f4f0e6', top_pat='stars', top_front='tesoro_jacket', belly='#f4f0e6', belly_pat='stars',
                  belt='#d8b030', belt_pat='gold', cuff='cuff', hand_front='rings',
                  pants='#d8b030', pants_pat='cloth', shoes='#e8c040', shoes_pat='gold')
    hh, hw, hd = l.hh, l.hw, l.hd
    s['boxes'] += hair(l, '#3a9a50', lift=0.7, back=0.8, sides=0.35)
    s['boxes'] += [
        B('head', -0.6, -hh * 1.05, hd - 1.2, 1.2, 1.4, 2.8, '#3a9a50', 'hair', rot=(0.5, 0, 0), pivot=(0, 0, 0)),   # swept back off the crown
        B('head', -hw - 0.6, -hh * 0.6, -hd + 0.3, 0.8, 1.2, 1.6, '#e8c040', 'gold', mirror=True),   # the shades' arms
        B('head', -hw - 0.3, -hh * 0.32, -0.4, 0.5, 1.0, 0.8, '#f0d050', 'gold', mirror=True),       # star earrings
        B('body', -l.cw - 0.2, 0.4, -l.chest_d / 2 - 0.4, 0.8, 4.5, 0.6, '#f0d050', 'chain'),        # chain at his right shoulder
        B('body', -l.cw - 0.6, 4.6, -l.chest_d / 2 - 0.5, 1.6, 1.6, 0.6, '#f0d050', 'gold'),          # and its star
        B('body', -l.cw - 0.3, -0.6, -l.chest_d / 2 - 0.35, 2 * l.cw + 0.6, 1.6, l.chest_d + 0.7, '#f4f0e6', 'cloth'),   # jacket collar
        B('body', -l.cw, 0, 0, 2 * l.cw, l.T * 0.95, 0.9, '#f4f0e6', 'stars', sway=1, pivot=(0, l.T * 0.55, l.chest_d / 2)),   # jacket tails
    ]
    return s


# Uta (Film Red): a slim young woman about 6.5 heads tall, narrow shoulders and long legs. Hair split red (her right)
# and white (her left), a white fringe over her left eye, two hoops on top, long hair down her back, purple eyes, gold
# cone headphones; a short white dress with a frilled skirt and a black bow, a light-blue left sleeve, white boots.
def _uta():
    s, l = figure(40, 6.6, skin='#f6e0d4', shoulder=3.9, chest_d=3.2, waist=2.3, hip=3.1, arm=1.9, fore=1.7, hand=1.7,
                  leg=2.5, calf=1.9, foot=2.1, legs=0.52, chin=0.7, neck=0.32, neck_w=0.34,
                  face=dict(eyes='#9a5ac8', brows=None, mouth='smirk', lashes=True),
                  top='#f8f6f8', top_pat='cloth', top_front='uta_dress', belly='#f8f6f8',
                  sleeve='#f6e0d4', sleeve_pat=None, sleeve_left='#8ad0f0', fore_left='#8ad0f0', left_pat='cloth',
                  pants='#f6e0d4', pants_pat=None, shin='#f4f4f8', shin_pat='leather', shoes='#f4f4f8')
    hh, hw, hd = l.hh, l.hw, l.hd
    red, white = '#d83040', '#f4f4f8'
    s['boxes'] += [
        # her hair, the two colours split down the middle
        B('head', -hw - 0.5, -hh - 0.7, -hd - 0.4, hw + 0.5, hh * 0.2 + 0.7, 2 * hd + 0.8, red, 'hair'),
        B('head', 0, -hh - 0.7, -hd - 0.4, hw + 0.5, hh * 0.2 + 0.7, 2 * hd + 0.8, white, 'hair'),
        B('head', -hw - 0.5, -hh * 0.85, -hd + 1.2, 1.2, hh * 1.0, 2 * hd - 0.8, red, 'hair'),
        B('head', hw - 0.7, -hh * 0.85, -hd + 1.2, 1.2, hh * 1.0, 2 * hd - 0.8, white, 'hair'),
        B('head', -hw - 0.4, -hh * 0.8, hd * 0.2, hw + 0.4, hh * 0.85, hd * 0.8 + 0.4, red, 'hair'),   # the back
        B('head', 0, -hh * 0.8, hd * 0.2, hw + 0.4, hh * 0.85, hd * 0.8 + 0.4, white, 'hair'),
        B('head', 0.4, -hh * 0.82, -hd - 0.5, hw * 0.8, hh * 0.28, 0.8, white, 'hair'),   # fringe over her left eye
        B('head', -hw, -hh * 0.82, -hd - 0.45, hw * 0.8, hh * 0.22, 0.7, red, 'hair'),
        # hoops on top
        B('head', -2.5, -4.6, -0.5, 5, 5, 1, red, 'ring', rot=(0, 0, 0.3), pivot=(-hw * 0.6, -hh, 0)),
        B('head', -2.5, -4.6, -0.5, 5, 5, 1, white, 'ring', rot=(0, 0, -0.3), pivot=(hw * 0.6, -hh, 0)),
        # cone headphones and their light-blue band
        B('head', -hw - 1.3, -hh * 0.62, -1.4, 1.4, 2.8, 2.8, '#e8c040', 'gold', mirror=True),
        B('head', -hw - 0.3, -hh - 0.9, -0.8, 2 * hw + 0.6, 0.8, 1.6, '#8ad0f0', 'cloth'),
        # long hair down her back, swaying
        B('body', -l.cw, 0, 0, l.cw, l.T * 0.8, 1.2, red, 'hair', sway=1, pivot=(0, -0.5, l.chest_d / 2 + 0.3)),
        B('body', 0, 0, 0, l.cw, l.T * 0.8, 1.2, white, 'hair', sway=1, pivot=(0, -0.5, l.chest_d / 2 + 0.3)),
        # frilled collar and the short skirt, flaring out
        B('body', -l.cw * 0.7, -0.7, -l.chest_d / 2 - 0.2, l.cw * 1.4, 1.2, l.chest_d + 0.4, '#f8f6f8', 'frills'),
        B('body', -l.waist - 0.2, l.T * 0.78, -l.belly_d / 2 - 0.2, 2 * l.waist + 0.4, l.T * 0.22 + l.LL * 0.22, l.belly_d + 0.4,
          '#f8f6f8', 'frills'),
        # puffed right sleeve
        B('arm', -1.4, -1, -1.4, 2.8, 3, 2.8, '#f8f6f8', 'frills', only='right'),
    ]
    return s


# Zephyr (Film Z): a mountain of an old Admiral, about 7 heads, very broad and deep-chested. Purple hair and beard, a
# purple visor, the Neo Marines' black coat with a high collar, and the Battle Smasher, a seastone war-arm bigger than
# his chest, on his right.
def _zephyr():
    s, l = figure(37, 7.0, skin='#c89070', shoulder=7.6, chest_d=6.2, waist=4.8, hip=5.0, arm=3.8, fore=3.3, hand=3.0,
                  leg=4.3, calf=3.5, foot=3.6, legs=0.45, chin=0.82, neck=0.25, neck_w=0.55,
                  face=dict(eyes=None, brows=None, mouth=None, shades='#6a3a9a', scar=True),
                  top='#1e2028', top_front='neo_coat', belt='#2a2a34', cuff='cuff',
                  pants='#2a2a34', shoes='#141418', right_arm=False)
    hh, hw, hd = l.hh, l.hw, l.hd
    purple = '#8a5ab8'
    s['boxes'] += hair(l, purple, lift=0.9, back=0.6, sides=0.45)
    s['boxes'] += [
        B('head', -hw * 0.8, -hh * 0.3, -hd - 0.6, hw * 1.6, hh * 0.5, 2.2, purple, 'hair'),   # beard
        B('body', -l.cw - 0.8, -1.6, -l.chest_d / 2 - 0.4, 2 * l.cw + 1.6, 2.8, l.chest_d + 0.8, '#3a2a50', 'ruff'),   # coat collar
        B('body', -l.cw - 0.3, 0, 0, 2 * l.cw + 0.6, l.T + l.LL * 0.35, 1.0, '#1e2028', 'coat', sway=1, pivot=(0, l.T * 0.4, l.chest_d / 2 + 0.2)),
        # the Battle Smasher
        B('arm', -6, -4, -5, 10, 8, 10, '#4a4a58', 'rivets', only='right'),
        B('arm', -6.5, 4, -6, 11, l.A - 9, 12, '#5a4a78', 'smasher', front='smasher_face', only='right'),
        B('arm', -5.5, l.A - 5, -5.5, 9, 5, 11, '#3a3a48', 'rivets', front='knuckles', only='right'),
    ]
    return s


# Douglas Bullet (Film Stampede): a giant built like a gorilla, about 7 heads, traps up to his ears, arms thicker than
# his body that hang past his knees, a bare chest; the Clank-Clank Fruit's scrap fused into gauntlets and a riveted
# back plate. Long white hair swept back down his back, red eyes, white brows.
def _bullet():
    s, l = figure(34, 6.4, skin='#8a5a40', shoulder=10.5, chest_d=8.0, waist=5.8, hip=6.0, arm=6.0, fore=6.6, hand=6.2,
                  leg=5.0, calf=4.4, foot=4.6, legs=0.4, reach=0.2, chin=0.86, neck=0.3, neck_w=0.8, head_w=0.9,
                  face=dict(eyes='#e02020', brows='#e8e8ec', mouth='grit'),
                  top='#8a5a40', top_pat='muscle', top_front='pecs', belly_front='abs',
                  belt='#2a2a30', fore_col='#5a5a64', fore_pat='rivets', hand_col='#4a4a54', hand_pat='rivets', hand_front='knuckles',
                  pants='#3a3a44', shoes='#202024')
    hh, hw, hd = l.hh, l.hw, l.hd
    white = '#e8e8ec'
    s['boxes'] += hair(l, white, lift=0.7, back=0.9, sides=0.55)
    s['boxes'] += [
        B('body', -l.cw * 0.85, -0.6, -2.0, 1.7 * l.cw, 3.0, 5.0, '#8a5a40', 'muscle'),   # traps
        B('body', -l.cw + 1, 0, l.chest_d / 2 - 0.4, 2 * l.cw - 2, l.T * 0.75, 2, '#6a6a74', 'rivets'),   # scrap on his back
        B('body', -1, -5, 5.5, 2, 6, 2, '#5a5a64', 'iron', mirror=True),
        B('body', -hw, 0, 0, 2 * hw, 10, 1, white, 'hair', sway=1, pivot=(0, -l.hh * 0.6, l.chest_d / 2 + 0.6)),   # his mane
    ]
    return s


# Shiki (Strong World): a huge old man about 6 heads tall (his mane makes the head big), long-bodied. A golden mane to
# the ground, bald on top where part of a ship's wheel is stuck in his skull, a black moustache and goatee, a gold
# chin tuft and a cigar. A red kimono to the knee, a green sash and gold chain, a yellow-striped haori over his
# shoulders, and from the knees down his legs are his two swords.
def _shiki():
    s, l = figure(42, 6.4, skin='#e4c09c', shoulder=6.2, chest_d=5.0, waist=4.4, hip=4.6, arm=3.8, fore=3.6, hand=2.6,
                  leg=4.2, calf=3.2, legs=0.42, chin=0.8,
                  face=dict(eyes='#2a2a2a', brows='#141414', mouth=None),
                  top='#9a2020', top_pat='robe', top_front='shiki_kimono', belly='#9a2020',
                  belt='#2a5a3a', belt_pat='cloth', belt_front=None, cuff='cuff',
                  sleeve='#9a2020', sleeve_pat='robe', pants='#9a2020', pants_pat='robe', shins=False, feet=False)
    hh, hw, hd = l.hh, l.hw, l.hd
    gold = '#f0c840'
    LL = l.LL
    s['boxes'] += [
        B('head', -hw * 0.5, -hh * 0.36, -hd - 0.3, hw, 0.7, 0.6, '#141414'),   # moustache
        B('head', -hw * 0.55, -hh * 0.36, -hd - 0.3, 0.7, 1.6, 0.6, '#141414', mirror=True),
        B('head', -0.9, -hh * 0.2, -hd - 0.2, 1.8, 1.4, 0.8, '#141414'),        # goatee
        B('head', -1, -0.4, -hd + 0.2, 2, 3, 1.6, gold, 'mane'),                  # gold chin tuft
        B('head', -hw * 0.6 - 0.4, -hh * 0.3, -hd - 2.2, 0.8, 0.8, 2.4, '#7a5030', 'wood'),   # cigar
        B('head', -hw - 2.4, -hh * 0.95, hd - 1.4, 2 * hw + 4.8, hh + 4, 2.2, gold, 'mane'),   # mane behind the head
        B('head', -hw - 1.8, -hh * 0.85, -hd + 0.8, 1.9, hh * 1.3, 2 * hd - 0.6, gold, 'mane', mirror=True),   # and down the sides
        B('head', -0.5, -4.5, -4.5, 1, 9, 9, '#6a4020', 'wheel', rot=(0.3, 0, 0), pivot=(0, -hh - 0.5, 0.5)),   # the wheel in his head
        B('body', -l.cw - 0.8, -0.8, -l.chest_d / 2 - 0.5, 2 * l.cw + 1.6, 3.2, l.chest_d + 1, '#e8c030', 'stripes'),   # haori over his shoulders
        B('body', -l.cw - 0.8, 2.4, -l.chest_d / 2 - 0.6, 2.2, l.T * 0.8, 0.6, '#e8c030', 'stripes', mirror=True),
        B('body', -l.cw - 0.8, 0, 0, 2 * l.cw + 1.6, l.T * 1.2, 1, '#e8c030', 'stripes', sway=1, pivot=(0, 1, l.chest_d / 2 + 0.5)),
        B('body', -l.cw, 0, 0, 2 * l.cw, l.T + LL - 1, 1.2, gold, 'mane', sway=1, pivot=(0, -1, l.chest_d / 2 + 1.7)),   # mane to the ground
        B('body', -l.hip - 0.3, l.T * 0.8, -l.belly_d / 2 - 0.3, 2 * l.hip + 0.6, l.T * 0.2 + LL * 0.5, l.belly_d + 0.6,
          '#9a2020', 'robe'),   # kimono skirt to the knee
        B('body', -l.waist - 0.6, l.T * 0.86, -l.belly_d / 2 - 0.45, 2 * l.waist + 1.2, 0.7, l.belly_d + 0.9, '#e8c040', 'chain'),   # gold chain
        # his legs are swords from the knee down
        B('leg', -1.2, LL * 0.5, -1.2, 2.4, 2.8, 2.4, '#2a2020', 'leather'),     # hilt
        B('leg', -2.2, LL * 0.5 + 2.8, -2.2, 4.4, 0.9, 4.4, '#c8a040', 'gold'),   # guard
        B('leg', -0.5, LL * 0.5 + 3.7, -1.6, 1, LL * 0.5 - 3.7, 3.2, '#e0e4ec', 'blade'),
    ]
    return s


# El Drago (One Piece: The Movie): a tall, broad pirate, about 7 heads, dark skin and a red mane. Gold-alloy shoulder
# armour and gorget over a white shirt, a gold belt, and hard golden nails. The Goe Goe Fruit: his mouth is the weapon.
def _drago():
    s, l = figure(38, 7.0, skin='#5a3a28', shoulder=6.8, chest_d=5.2, waist=4.0, hip=4.3, arm=3.4, fore=3.0, hand=2.8,
                  leg=3.9, calf=3.2, legs=0.47, chin=0.82,
                  face=dict(eyes='#f0c040', brows='#c02818', mouth='roar'),
                  top='#f0eee8', top_front='drago_shirt', belt='#d8b030', belt_pat='gold',
                  pants='#3a2a2a', shoes='#1e1618')
    hh, hw, hd = l.hh, l.hw, l.hd
    red = '#c02818'
    s['boxes'] += hair(l, red, pat='mane', lift=1.2, back=1.3, sides=1.1, thick=2.6)
    s['boxes'] += [
        B('body', -l.cw - 0.5, -1.2, -l.chest_d / 2 - 0.4, 2 * l.cw + 1, 3, l.chest_d + 0.8, '#e8c040', 'gold'),   # gorget
        B('arm', -3.2, -3.0, -3.0, 5.2, 4.0, 6.0, '#e8c040', 'plates'),   # gold shoulder armour
        B('arm', -1.3, l.A - 0.8, -1.6, 2.6, 1.6, 0.9, '#e8c040', 'gold', front='knuckles'),   # golden nails
    ]
    return s


# Gasparde (Dead End Adventure): tall and muscular, about 7.3 heads, a heavy chin and narrow eyes, dark-blonde hair
# combed to the sides and flaring out behind. An ornate Marine officer's jacket (insignia crossed out on the back), a
# purple scarf, a black belt with two buckles, brown gloves and steel boots.
def _gasparde():
    s, l = figure(40, 7.3, skin='#e0b48c', shoulder=6.4, chest_d=5.0, waist=3.7, hip=4.0, arm=3.2, fore=2.8, hand=2.6,
                  leg=3.7, calf=3.1, legs=0.48, chin=0.88,
                  face=dict(eyes='#2a2a30', brows='#7a6030', mouth=None, narrow=True),
                  top='#2e4a3e', top_front='gasparde_coat', belt='#1a1a1e', belt_front='two_buckles', cuff='cuff',
                  hand_col='#6a4a2a', hand_pat='leather', pants='#1e1e22', shin='#9aa0a8', shin_pat='iron', shoes='#9aa0a8', shoes_pat='iron')
    hh, hw, hd = l.hh, l.hw, l.hd
    hc = '#a88a48'
    s['boxes'] += hair(l, hc, lift=0.6, back=0.7, sides=0.55)
    s['boxes'] += [
        B('head', -hw - 1.6, -hh * 0.85, hd - 1.2, 2 * hw + 3.2, hh * 0.9, 1.4, hc, 'hair'),   # flaring out behind
        B('body', -l.cw * 0.8, -1, -l.chest_d / 2 - 0.4, l.cw * 1.6, 2.2, l.chest_d + 0.8, '#6a3a8a', 'cloth'),   # purple scarf
        B('body', -l.cw * 0.6, 1.2, -l.chest_d / 2 - 0.5, 1.6, 4, 0.6, '#6a3a8a', 'cloth'),
        B('body', -l.cw - 0.3, 0, 0, 2 * l.cw + 0.6, l.T + l.LL * 0.15, 1, '#2e4a3e', 'crossed', sway=1, pivot=(0, l.T * 0.55, l.chest_d / 2 + 0.2)),
        B('arm', -3.3, -2.8, -3.1, 6, 2, 6.2, '#d8b040', 'fringe'),   # epaulettes
    ]
    return s


# Baron Omatsuri (Baron Omatsuri and the Secret Island): tall and lean, about 7.5 heads, broad shoulders, long limbs,
# a thin waist and a long, pointed head. Palm-tree hair, an upswept moustache and pointed goatee, pink goggles; a
# dark purple suit with orange-yellow flowers, a white collar, and Lily Carnation on his left shoulder.
def _omatsuri():
    s, l = figure(42, 7.4, skin='#d8a880', shoulder=6.0, chest_d=4.4, waist=2.6, hip=3.2, arm=2.8, fore=2.4, hand=2.3,
                  leg=3.1, calf=2.5, legs=0.5, chin=0.42, head_w=0.78,
                  face=dict(eyes='#2a2a2a', brows='#141414', mouth=None),
                  top='#3e2a5a', top_pat='flowers', top_front='omatsuri_suit', cuff='cuff',
                  pants='#3e2a5a', pants_pat='cloth', shoes='#1e1a22')
    hh, hw, hd = l.hh, l.hw, l.hd
    hc = '#2a2018'
    s['boxes'] += [
        B('head', -hw - 0.3, -hh - 0.8, -hd - 0.3, 2 * hw + 0.6, 1.6, 2 * hd + 0.6, hc, 'hair'),
        B('head', -1, -hh - 4.2, -1, 2, 3.6, 2, hc, 'hair'),   # palm-tree tuft
        B('head', 0, -0.6, -1.2, 6, 1.2, 2.4, hc, 'hair', rot=(0, 0, 0.55), pivot=(0.5, -hh - 3.6, 0), mirror=True),
        B('head', -1.2, -0.6, 0, 2.4, 1.2, 5.5, hc, 'hair', rot=(-0.55, 0, 0), pivot=(0, -hh - 3.6, 0.5)),
        B('head', -1.2, -0.6, -5.5, 2.4, 1.2, 5.5, hc, 'hair', rot=(0.55, 0, 0), pivot=(0, -hh - 3.6, -0.5)),
        B('head', -hw - 0.2, -hh * 0.88, -hd - 0.5, 2 * hw + 0.4, 1.2, 0.8, '#f080b0', 'gold'),   # pink goggles on his forehead
        B('head', -0.4, -hh * 0.5, -hd - 0.9, 0.8, 1.8, 1.0, '#d8a880'),       # pointed nose
        B('head', -hw * 0.75, -hh * 0.3, -hd + 0.2, 1.6, 0.5, 0.5, '#141414', rot=(0, 0, 0.5), pivot=(0, 0, 0), mirror=True),   # moustache, upswept
        B('head', -0.6, -0.8, -hd * 0.4 - 0.4, 1.2, 2.6, 1.0, '#141414'),     # pointed goatee
        B('body', -l.cw * 0.6, -0.9, -l.chest_d / 2 - 0.3, l.cw * 1.2, 2.4, 1.2, '#f4f4f0', 'cloth'),   # white collar
        B('body', l.cw - 0.5, -3, -0.5, 1, 3, 1, '#3a8a3a'),                                   # Lily's stem
        B('body', l.cw - 1.9, -6.8, -0.6, 3.8, 3.8, 1.2, '#f0d030', None, front='lily_face'),
    ]
    return s


# Dr. Ratchet (Karakuri Castle): a thin, lanky young inventor about 6.5 heads tall. Light brown hair parted to one
# side, round orange mechanical glasses, loose yellow overalls and a thick black scarf printed with red gears.
def _ratchet():
    s, l = figure(34.5, 6.5, skin='#f0cca8', shoulder=4.4, chest_d=3.4, waist=2.7, hip=3.0, arm=2.3, fore=2.1, hand=2.0,
                  leg=2.6, calf=2.2, legs=0.5, chin=0.72,
                  face=dict(eyes=None, brows='#8a6038', mouth='smirk'),
                  top='#e8c430', top_front='overalls', pants='#e8c430', shoes='#5a3a22')
    hh, hw, hd = l.hh, l.hw, l.hd
    hc = '#b08050'
    s['boxes'] += hair(l, hc, lift=0.6, back=0.7, sides=0.45)
    s['boxes'] += [
        B('head', -hw, -hh * 0.82, -hd - 0.5, hw * 1.3, hh * 0.24, 0.8, hc, 'hair'),   # parted to one side
        B('head', -hw * 0.85, -hh * 0.62, -hd - 0.5, hw * 0.8, hh * 0.3, 0.6, '#f0a040', None, front='lens'),
        B('head', hw * 0.05, -hh * 0.62, -hd - 0.5, hw * 0.8, hh * 0.3, 0.6, '#f0a040', None, front='lens'),
        B('body', -l.cw - 0.3, -1.4, -l.chest_d / 2 - 0.6, 2 * l.cw + 0.6, 2.8, l.chest_d + 1.2, '#1a1a1e', 'gears'),   # thick black scarf
        B('body', -l.cw * 0.6, 0, 0, 2, 7, 0.7, '#1a1a1e', 'gears', sway=-1, pivot=(0, 1.4, -l.chest_d / 2 - 0.5)),
    ]
    return s


# Byrnndi World (the 3D2Y special): very tall and broad, about 7 heads, huge bare arms on thin legs. A horned helmet with
# one horn broken off, a green beard and paler W moustache, a gap-toothed grin, an open sleeveless black-and-purple coat
# over his bare chest, green trousers, a brown belt and shoes.
def _world():
    s, l = figure(40, 7.0, skin='#c89068', shoulder=9.6, chest_d=7.0, waist=5.2, hip=5.0, arm=6.2, fore=6.0, hand=5.4,
                  leg=3.4, calf=2.8, foot=3.4, legs=0.42, reach=0.14, chin=0.84, neck=0.18, neck_w=0.65,
                  face=dict(eyes='#2a2a2a', brows='#3a7a3a', mouth='gap'),
                  top='#c89068', top_pat='muscle', top_front='pecs', belly_front='abs',
                  sleeve='#c89068', sleeve_pat='muscle', hand_front='knuckles',
                  belt='#6a4a2a', pants='#3a6a3a', shoes='#6a4a2a')
    hh, hw, hd = l.hh, l.hw, l.hd
    s['boxes'] += [
        B('head', -hw * 0.95, -hh * 0.38, -hd - 0.9, hw * 1.9, hh * 0.7, 2.6, '#3a7a3a', 'hair'),   # green beard
        B('head', -hw * 0.8, -hh * 0.45, -hd - 1.0, hw * 1.6, 0.9, 0.6, '#7aba6a', 'hair'),   # W moustache
        B('head', -hw - 0.5, -hh - 1.4, -hd - 0.5, 2 * hw + 1, hh * 0.45 + 1.4, 2 * hd + 1, '#5a4a3a', 'iron'),   # helmet
        B('head', -0.7, -6, -0.7, 1.4, 6, 1.4, '#e8e0c8', 'bone', rot=(0, 0, -0.6), pivot=(-hw, -hh * 0.9, 0)),   # his horn
        B('head', -0.7, -2.2, -0.7, 1.4, 2.2, 1.4, '#e8e0c8', 'bone', rot=(0, 0, 0.6), pivot=(hw, -hh * 0.9, 0)),   # the broken one
        B('body', -l.cw - 0.4, -2, -0.6, 2 * l.cw + 0.8, 3, l.chest_d / 2 + 1, '#6a3a8a', 'ruff'),   # purple collar
        B('body', -l.cw - 0.4, -0.6, -l.chest_d / 2 - 0.4, 3.4, l.T + 0.4, l.chest_d + 0.8, '#1e1a24', 'purple_trim', mirror=True),   # the open coat
        B('body', -l.cw - 0.4, 0, 0, 2 * l.cw + 0.8, l.T + l.LL * 0.3, 1, '#1e1a24', 'purple_trim', sway=1, pivot=(0, l.T * 0.5, l.chest_d / 2 + 0.3)),
    ]
    return s


# Bear King (Clockwork Island Adventure): a big man about 7 heads tall, black hair and whiskers under a big teddy-bear
# hat. A furred red captain's jacket with a golden spade collar, a blue shirt with card pips left unbuttoned, relatively
# thin hairy forearms with fur bands at the wrists. The Kachi Kachi Fruit makes his fists hard and hot.
def _bear_king():
    s, l = figure(37.5, 7.0, skin='#d8a47c', shoulder=6.4, chest_d=5.2, waist=4.2, hip=4.3, arm=3.2, fore=2.4, hand=2.7,
                  leg=3.8, calf=3.1, legs=0.47, chin=0.84,
                  face=dict(eyes='#202020', brows='#141414', mouth='grin'),
                  top='#3a6ac8', top_front='pips', belt='#2a1a14', sleeve='#7a2a2a', fore_col='#d8a47c', fore_pat='hairy',
                  hand_front='knuckles', pants='#2a2a34', shoes='#1a1410')
    hh, hw, hd = l.hh, l.hw, l.hd
    s['boxes'] += [
        B('head', -hw - 0.3, -hh * 0.9, -hd + 0.8, 2 * hw + 0.6, hh * 0.65, 2 * hd - 0.4, '#18181c', 'hair'),   # black hair under the hat
        B('head', -hw * 0.95, -hh * 0.36, -hd - 0.15, 1.8, 0.4, 0.3, '#18181c', None, mirror=True, rot=(0, 0, 0.2), pivot=(0, 0, 0)),   # whiskers
        B('head', -hw - 1.0, -hh - 5, -hd - 1.0, 2 * hw + 2, 5.8, 2 * hd + 2, '#8a5a32', 'fur', front='teddy'),   # teddy hat
        B('head', -hw - 0.6, -hh - 6.4, -1.0, 2.4, 2.4, 1.6, '#8a5a32', 'fur', mirror=True),   # its ears
        B('head', -1.5, -hh - 2.4, -hd - 1.8, 3, 2, 1.2, '#c89a6a', 'fur'),   # its snout
        B('body', -l.cw, -5, l.chest_d / 2 - 0.6, 2 * l.cw, 5.5, 1, '#e8c040', 'gold', front='spade'),   # golden spade collar
        B('body', -l.cw - 0.4, -0.5, -l.chest_d / 2 - 0.4, 2.4, l.T + 1, l.chest_d + 0.8, '#7a2a2a', 'cloth', mirror=True),   # the open jacket
        B('body', -l.cw - 0.5, -0.9, -l.chest_d / 2 - 0.5, 2 * l.cw + 1, 1.6, l.chest_d + 1, '#ece6d8', 'fur'),   # fur trim
        B('body', -l.cw - 0.4, 0, 0, 2 * l.cw + 0.8, l.T * 1.1, 1, '#7a2a2a', 'cloth', sway=1, pivot=(0, 1, l.chest_d / 2 + 0.3)),
        B('arm', -1.5, l.upper + l.fore_len - 1.4, -1.5, 3, 1.6, 3, '#ece6d8', 'fur'),   # fur wrist bands
    ]
    return s


# Buena Festa (Stampede): a middle-aged showman about 7 heads tall, of average build, under a huge dark afro with his
# glasses pushed up into it. A fancy buttoned coat, a belt wrapped round his chest, pinstripe trousers and boots.
def _festa():
    s, l = figure(38.4, 7.0, skin='#d8a884', shoulder=5.4, chest_d=4.8, waist=4.0, hip=4.0, arm=2.9, fore=2.6, hand=2.5,
                  leg=3.4, calf=2.8, legs=0.47, chin=0.78,
                  face=dict(eyes='#2a2a2a', brows='#1e1612', mouth='grin'),
                  top='#a8324a', top_front='festa_coat', cuff='cuff', pants='#4a4a52', pants_pat='pinstripe', shoes='#2a1a14')
    hh, hw, hd = l.hh, l.hw, l.hd
    s['boxes'] += [
        B('head', -hw - 2.4, -hh - 6, -hd - 1.4, 2 * hw + 4.8, 8.6, 2 * hd + 3.4, '#1e1612', 'afro'),   # the afro
        B('head', -hw - 1.0, -hh * 0.9, -hd + 1.4, 1.6, hh * 0.65, 2 * hd - 1.2, '#1e1612', 'afro', mirror=True),
        B('head', -hw * 0.9, -hh - 1.6, -hd - 1.6, hw * 0.85, 1.6, 0.6, '#d8c070', None, front='lens'),   # glasses up in the afro
        B('head', hw * 0.05, -hh - 1.6, -hd - 1.6, hw * 0.85, 1.6, 0.6, '#d8c070', None, front='lens'),
        B('head', -1.3, -hh * 0.3, -hd - 0.2, 2.6, 0.9, 0.5, '#1e1612'),   # moustache
        B('body', -l.cw * 0.6, -0.9, -l.chest_d / 2 - 0.3, l.cw * 1.2, 1.8, 1, '#f4f0e8', 'cloth'),   # shirt collar
        B('body', -l.cw - 0.3, l.T * 0.3, -l.chest_d / 2 - 0.3, 2 * l.cw + 0.6, 1.3, l.chest_d + 0.6, '#3a2418', 'leather', front='buckle'),   # belt round his chest
        B('body', -l.cw - 0.2, 0, 0, 2 * l.cw + 0.4, l.T + l.LL * 0.2, 1, '#a8324a', 'cloth', sway=1, pivot=(0, l.T * 0.6, l.chest_d / 2 + 0.2)),
        B('arm', -0.6, l.A - 2, -4.6, 1.2, 1.6, 3.4, '#5a3a22', 'wood', only='right'),   # his flintlock
    ]
    return s


# Saga (Curse of the Sacred Sword): a tall, lean swordsman about 7.5 heads, tanned skin and long white hair worn loose
# down his back, a red robe to the knees with a white sash, a white band on his left arm, red shoes, and the Seven
# Star Sword at his hip.
def _saga():
    s, l = figure(41.8, 7.5, skin='#b07850', shoulder=5.6, chest_d=4.4, waist=3.3, hip=3.6, arm=2.8, fore=2.5, hand=2.3,
                  leg=3.2, calf=2.6, legs=0.5, chin=0.76,
                  face=dict(eyes='#3a2a20', brows='#e8e8ee', mouth=None, narrow=True),
                  top='#b02424', top_pat='robe', top_front='saga_robe', belt='#f0ece4', belt_pat='cloth', belt_front=None, cuff='cuff',
                  pants='#2a2024', shoes='#b02424')
    hh, hw, hd = l.hh, l.hw, l.hd
    white = '#ececf2'
    s['boxes'] += hair(l, white, lift=0.6, back=1.0, sides=1.1, fringe=0.3)
    s['boxes'] += [
        B('body', -l.cw + 0.4, -1, 0, 2 * l.cw - 0.8, l.T * 0.9, 1.2, white, 'hair', sway=1, pivot=(0, 0.5, l.chest_d / 2 + 0.3)),   # long white hair
        B('body', -l.hip - 0.3, 0, 0, 2 * l.hip + 0.6, l.LL * 0.45, 1, '#b02424', 'robe', sway=-1, pivot=(0, l.T * 0.85, -l.belly_d / 2 - 0.4)),   # robe to the knees
        B('body', -l.hip - 0.3, 0, 0, 2 * l.hip + 0.6, l.LL * 0.45, 1, '#b02424', 'robe', sway=1, pivot=(0, l.T * 0.85, l.belly_d / 2 - 0.2)),
        B('body', l.hip, 0, -0.6, 1.2, 12, 1.2, '#2a2420', 'leather', rot=(0.5, 0, 0), pivot=(0, l.T * 0.8, -1)),   # the Seven Star Sword's scabbard
        B('body', l.hip, -3.4, -0.6, 1.2, 3.4, 1.2, '#3a7a4a', 'leather', rot=(0.5, 0, 0), pivot=(0, l.T * 0.8, -1)),   # its hilt
        B('arm', -1.6, 3, -1.6, 3.2, 1.6, 3.2, '#f4f4f0', 'cloth', only='left'),   # white armband
    ]
    return s


# Count Butler (Chopper's Kingdom on the Island of Strange Animals): a tall, thin, pale gentleman scientist about 7.5
# heads, a long chin, slicked-back hair and a monocle, a long tailcoat with a white cravat, white gloves, and the violin
# he hypnotises animals with. (The wiki gives no colours for him, so these are ours.)
def _butler():
    s, l = figure(42.4, 7.5, skin='#ecd8c8', shoulder=4.7, chest_d=3.8, waist=2.7, hip=3.0, arm=2.4, fore=2.2, hand=2.1,
                  leg=2.7, calf=2.3, legs=0.5, chin=0.62, head_w=0.74,
                  face=dict(eyes='#5a2a6a', brows='#2a1a30', mouth='smirk', monocle=True),
                  top='#5a2a6a', top_front='butler_coat', cuff='cuff', hand_col='#f4f4f0', hand_pat='cloth',
                  pants='#2a2030', shoes='#141014')
    hh, hw, hd = l.hh, l.hw, l.hd
    s['boxes'] += hair(l, '#3a2440', lift=0.5, back=0.75, sides=0.4)
    s['boxes'] += [
        B('body', -1.6, -0.9, -l.chest_d / 2 - 0.5, 3.2, 2.6, 1, '#f4f4f0', 'frills'),   # white cravat
        B('body', -l.cw, 0, 0, l.cw * 0.9, l.T + l.LL * 0.55, 1, '#5a2a6a', 'cloth', sway=1, pivot=(0, l.T * 0.6, l.chest_d / 2 + 0.2), mirror=True),   # the two tails
        B('arm', -1.2, l.A * 0.45, -6, 2.4, 1.6, 6.5, '#a8582a', 'wood', front='violin', only='left'),   # the violin
        B('arm', -0.4, l.A - 1.5, -6, 0.6, 0.6, 7, '#e8e0c8', None, only='right'),   # and its bow
    ]
    return s


for _id, _fn in (('douglas_bullet', _bullet), ('gild_tesoro', _tesoro), ('zephyr_z', _zephyr),
                 ('shiki_golden_lion', _shiki), ('uta_diva', _uta), ('el_drago', _drago), ('gasparde', _gasparde),
                 ('baron_omatsuri', _omatsuri), ('ratchet', _ratchet), ('byrnndi_world', _world),
                 ('bear_king', _bear_king), ('buena_festa', _festa), ('saga', _saga), ('count_butler', _butler)):
    FILM[_id] = _fn()
