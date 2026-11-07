#!/usr/bin/env python3
"""Builds every rogue's own body: the 3D model (Java) and the skin painted to fit it.

    python3 tools/gen_models.py .

Writes src/main/java/com/onepiecebosses/client/RogueModels.java and
src/main/resources/assets/opbosses/textures/entity/boss/<id>.png (128x128, or 256x256 if the boxes don't fit,
saved at skin.SCALE times that size with the faces redrawn in more detail, see skin.py).
Change a shape or a colour here and run it again; don't edit the generated files by hand.

Model space is Minecraft's: 16 px = 1 block, y points down, the front is -z, the right side is -x, and the feet
stand on y = 24. Each part has a pivot (where it turns: the neck, the shoulders, the hips); a box's x, y, z are
measured from its part's pivot, or from the box's own pivot when it has one (rotated boxes and swaying
cloth turn around that point). Arm and leg boxes are given for the right side and copied to the left.
The parts animate like a player's (walking, swinging, looking around); "sway" boxes (coat tails, trains, skirts)
also swing back as the boss walks: sway=1 swings out behind, sway=-1 out in front.
"""
import math
import os
import random
import sys

from PIL import Image

import anime
import skin

# ---------------- the rogues ----------------
# part pivots: head, body, arm (right shoulder; the left one is mirrored), leg (right hip; mirrored).
# box: (part, x, y, z, w, h, d, colour, pattern, extras) with extras like front='face', rot=(rx,ry,rz),
#      pivot=(px,py,pz) for a rotated box, sway=1, mirror=True (body/head boxes: also add a copy on the other side).

def B(part, x, y, z, w, h, d, colour, pattern=None, **extra):
    return dict(part=part, x=x, y=y, z=z, w=w, h=h, d=d, colour=colour, pattern=pattern, **extra)


ROGUES = {
    # A walking wall of muscle: barrel chest, Popeye forearms that reach the ground, little legs,
    # a slab of an underbite jaw, and his anchor slung across his back.
    "saltjaw_rourke": dict(
        pivots=dict(head=(0, 1, -2), body=(0, 0, 0), arm=(-9.5, 3, 0), leg=(-3, 19, 0)),
        boxes=[
            B('head', -3.5, -7, -3.5, 7, 6, 7, '#c48c64', None, front='face', eyes='#202020', brows='#3a2a1a', mouth=None),
            B('head', -5, -3, -5.5, 10, 5, 8, '#c48c64', 'stubble', front='jaw', teeth='underbite'),
            B('head', -4, -8, -4, 8, 2, 8, '#a82828', 'cloth'),                       # bandana
            B('head', 0, -0.5, -1, 3, 1, 4, '#a82828', 'cloth', rot=(0, 0, 0.5), pivot=(3.5, -7, 3)),  # bandana knot tail
            B('body', -8, 1, -5, 16, 11, 10, '#9a8c70', 'cloth', front='vest'),        # barrel chest in an open vest
            B('body', -7, 12, -4.5, 14, 7, 9, '#4a4a5a', 'cloth', front='belt'),       # belly and belt
            B('body', -1, -3, 5, 2, 20, 2, '#7a7a80', 'iron'),                         # anchor shank on his back
            B('body', -7, 13, 5, 14, 2, 2, '#7a7a80', 'iron'),                         # anchor arms
            B('body', -8, 9, 5, 2, 5, 2, '#7a7a80', 'iron', mirror=True),              # anchor flukes
            B('body', -3, -6, 5, 6, 3, 2, '#7a7a80', 'iron'),                          # anchor ring
            B('body', -6, 0, -5.4, 2, 12, 1, '#8a8a90', 'chain', rot=(0, 0, -0.5)),     # chain across the chest
            B('arm', -3, -3, -3, 6, 7, 6, '#9a8c70', 'cloth'),                         # shoulder
            B('arm', -4.5, 4, -4, 8, 10, 8, '#c48c64', 'tattoo'),                      # huge forearm
            B('arm', -4, 14, -3.5, 7, 5, 7, '#b88060', None, front='knuckles'),        # fist
            B('leg', -2, 0, -2, 4, 3, 4, '#4a4a5a', 'cloth'),
            B('leg', -2.5, 3, -3, 5, 2, 5, '#3a2a1a', 'leather'),
        ]),
    # Impossibly tall and thin: stilt legs, a wasp waist, arms past her knees, a hat as wide as a table
    # with a veil, and a long train of fog-grey coat behind her. Her lantern hangs from one hand.
    "corvina_fog_widow": dict(
        pivots=dict(head=(0, -9, 0), body=(0, -9, 0), arm=(-4.5, -7, 0), leg=(-1.6, 5, 0)),
        boxes=[
            B('head', -3, -7, -3, 6, 7, 6, '#e6d2c8', None, front='face', eyes='#8cc8dc', brows='#1a1820', mouth='smirk', lashes=True),
            B('head', -3.5, -7.5, 1.5, 7, 13, 2, '#1a1820', 'hair'),                   # long black hair
            B('head', -9, -7.5, -9, 18, 1, 18, '#24202e', 'cloth'),                    # hat brim
            B('head', -3.5, -12, -3.5, 7, 5, 7, '#24202e', 'cloth', front='hatband'),   # hat crown
            B('head', -3.5, -6.5, -3.9, 7, 3, 1, '#3c3848', 'veil'),                   # veil
            B('body', -3.5, 0, -2, 7, 6, 4, '#3c3448', 'cloth', front='corset'),
            B('body', -4.5, -1.5, -3, 9, 3, 6, '#6a6478', 'ruff'),                    # high collar
            B('body', -1.5, 6, -1.5, 3, 4, 3, '#2a2434', 'cloth'),                     # wasp waist
            B('body', -3.5, 10, -2.5, 7, 4, 5, '#2a2434', 'cloth'),                    # hips
            B('body', -5, 0, 0, 10, 30, 1, '#4a4658', 'fog', sway=1, pivot=(0, 1, 2.5)),  # long coat train
            B('arm', -1.5, -1, -1, 2, 17, 2, '#3c3448', 'cloth'),
            B('arm', -1.7, 15, -1.2, 2.4, 2, 2.4, '#e6d2c8'),                          # hand
            B('arm', -2.5, 17, -1.5, 3, 4, 3, '#e8c060', None, front='lantern', only='right'),
            B('leg', -1, 0, -1, 2, 17, 2, '#2a2434', 'cloth'),
            B('leg', -1.2, 17, -2, 2.4, 2, 3, '#14121a', 'leather'),
        ]),
    # A slab-shouldered officer gone bad: V-shaped torso twice as wide as his hips, a chin you could
    # land a ship on, a towering Marine cap, epaulettes like serving trays and a torn "Justice" coat.
    "iron_tide_graves": dict(
        pivots=dict(head=(0, -5, -1), body=(0, -4, 0), arm=(-10, -2, 0), leg=(-2.2, 12, 0)),
        boxes=[
            B('head', -3, -8, -3.5, 6, 6, 7, '#cda07d', None, front='face', eyes='#284060', brows='#9a9aa0', mouth=None, scar=True),
            B('head', -4, -2.5, -5.5, 8, 4, 7, '#cda07d', 'stubble', front='jaw', teeth='grim'),   # the chin
            B('head', -4.5, -13, -4.5, 9, 5, 9, '#f0f0f4', 'cloth', front='anchor_badge'),   # cap crown
            B('head', -4, -8.5, -4, 8, 1, 8, '#28304a', 'cloth'),                    # cap band
            B('head', -4, -8.5, -6.5, 8, 1, 3, '#14141c', 'leather'),                # peak
            B('body', -8, 0, -4, 16, 7, 8, '#f0f0f4', 'cloth', front='shirt'),        # shoulders and chest
            B('body', -5.5, 7, -3, 11, 7, 6, '#323850', 'cloth', front='buttons'),
            B('body', -6, 13, -3.5, 12, 3, 7, '#14141c', 'leather', front='buckle'),
            B('body', -8, 0, 0, 16, 12, 1, '#f0f0f4', 'justice', sway=1, pivot=(0, 0, 4.5)),   # coat cape
            B('body', -9, 0, 0, 18, 10, 1, '#f0f0f4', 'justice_low', sway=1, pivot=(0, 12, 0), parent='sway0'),
            B('arm', -3.5, -3, -3.5, 7, 3, 7, '#d8b040', 'fringe'),                  # epaulette
            B('arm', -2.5, 0, -2.5, 5, 13, 5, '#f0f0f4', 'cloth'),
            B('arm', -2, 13, -2, 4, 3, 4, '#cda07d'),
            B('leg', -2, 0, -2, 4, 9, 4, '#323850', 'cloth'),
            B('leg', -2.5, 9, -2.5, 5, 3, 5, '#14141c', 'leather'),
        ]),
    # Hollow armour with nothing inside: every piece floats apart from the rest, held by nothing.
    # A crescent-crested helm over two glowing eyes, shoulder plates like doors, a plated skirt.
    "hollow_ronin_tsurugi": dict(
        pivots=dict(head=(0, -6, 0), body=(0, -2, 0), arm=(-8, 0, 0), leg=(-2.4, 15, 0)),
        boxes=[
            B('head', -4, -6, -4, 8, 4, 8, '#08080c', None, front='void_eyes'),       # empty face
            B('head', -4.5, -10, -4.5, 9, 5, 9, '#2c2834', 'lacquer'),                 # kabuto bowl
            B('head', -6, -6, -2, 12, 3, 7, '#2c2834', 'plates'),                     # neck guard
            B('head', -3.5, -3, -4.8, 7, 4, 1, '#8c2028', 'lacquer', front='menpo'),   # mask
            B('head', -0.5, -7, -0.5, 1, 8, 1, '#c8a040', 'gold', rot=(0, 0, -0.55), pivot=(-1, -9, -4.6), mirror=True),  # crest
            B('body', -3.5, 0, -2, 7, 13, 4, '#08080c'),                              # the void inside
            B('body', -5, 1, -3, 10, 9, 6, '#8c2028', 'lacquer', front='lacing'),     # chest armour
            B('body', -5.5, 0, 0, 11, 6, 1, '#2c2834', 'plates', sway=-1, pivot=(0, 10, -3.6)),  # front skirt plates
            B('body', -5.5, 0, 0, 11, 6, 1, '#2c2834', 'plates', sway=1, pivot=(0, 10, 3.0)),     # back skirt plates
            B('arm', -5, -3, -3.5, 6, 8, 7, '#8c2028', 'plates'),                    # sode (shoulder plate)
            B('arm', -1.5, 5, -1.5, 3, 9, 3, '#2c2834', 'lacquer'),
            B('arm', -2, 14, -2, 4, 3, 4, '#2c2834', 'plates'),
            B('leg', -2, 0, -2, 4, 7, 4, '#2c2834', 'plates'),
            B('leg', -2.5, 7, -3, 5, 2, 5, '#1c1820', 'lacquer'),
        ]),
    # A ship's boiler with a man somewhere on top: a riveted belly as big as a cabin with a glowing firebox,
    # two smokestacks, piston arms ending in sledgehammer fists, stubby iron legs and a tiny goggled head.
    "boilerheart_gantz": dict(
        pivots=dict(head=(0, -7, -4), body=(0, -6, 0), arm=(-11, -2, 0), leg=(-4.5, 14, 0)),
        boxes=[
            B('head', -2.5, -5, -2.5, 5, 5, 5, '#b4785a', None, front='face', eyes=None, brows=None, mouth='grit', goggles=True),
            B('head', -3, -4, -3, 6, 2, 6, '#5a4a3a', 'leather'),                    # goggle strap
            B('body', -9, 0, -8, 18, 20, 16, '#8a5a3a', 'rivets', front='firebox'),   # the boiler
            B('body', -9.5, 4, -8.5, 19, 2, 17, '#5a5a62', 'iron'),                   # boiler bands
            B('body', -9.5, 14, -8.5, 19, 2, 17, '#5a5a62', 'iron'),
            B('body', -6, -9, 4, 3, 10, 3, '#3a3a40', 'soot'),                        # smokestacks
            B('body', 3, -12, 4, 3, 13, 3, '#3a3a40', 'soot'),
            B('body', -1.5, -2, -8.6, 3, 2, 1, '#d8c070', 'gold'),                    # pressure gauge
            B('arm', -3, -3, -3, 6, 6, 6, '#5a5a62', 'rivets'),                       # shoulder joint
            B('arm', -1.5, 3, -1.5, 3, 8, 3, '#9a9aa4', 'piston'),                    # piston rod
            B('arm', -4, 11, -4, 8, 8, 8, '#5a5a62', 'rivets', front='knuckles'),     # sledgehammer fist
            B('leg', -1.5, 0, -1.5, 3, 5, 3, '#9a9aa4', 'piston'),
            B('leg', -3, 5, -3.5, 6, 5, 7, '#5a5a62', 'rivets'),                      # iron boots
        ]),
    # Tall and eerie: a long robed body, arms that hang to his knees, a great dorsal fin, fin ears,
    # a shark's jaw full of fangs, white hair streaming back and a crown of coral.
    "nereus_vane": dict(
        pivots=dict(head=(0, -6, 0), body=(0, -6, 0), arm=(-8, -5, 0), leg=(-2.5, 14, 0)),
        boxes=[
            B('head', -4, -8, -4, 8, 6, 8, '#5a96a0', 'scales', front='face', eyes='#f8f078', brows=None, mouth=None, slit=True),
            B('head', -4.5, -3, -5, 9, 4, 6, '#5a96a0', 'scales', front='jaw', teeth='fangs'),
            B('head', -4, -1.5, -0.5, 8, 16, 2, '#e8eef0', 'hair', sway=1, pivot=(0, -7, 3)),   # white hair
            B('head', -0.5, -5, -2, 1, 5, 5, '#3c7884', 'fin', rot=(0, 0, -0.6), pivot=(-4.2, -5, 0), mirror=True),   # fin ears
            B('head', -0.5, -6, -0.5, 1, 6, 1, '#e87860', 'coral', rot=(0, 0, -0.35), pivot=(-2.5, -8, -2), mirror=True),
            B('head', -0.5, -7, -0.5, 1, 7, 1, '#e87860', 'coral', pivot=(0, -8, -2.5)),
            B('body', -7, 0, -3.5, 14, 4, 7, '#1e3a5a', 'robe', front='trim'),        # broad shoulders
            B('body', -5, 4, -3, 10, 14, 6, '#1e3a5a', 'robe', front='trim'),         # long body
            B('body', -0.5, -3, 0, 1, 12, 7, '#3c7884', 'fin', rot=(0.25, 0, 0), pivot=(0, 1, 3)),   # dorsal fin
            B('body', -6, 0, 0, 12, 12, 1, '#1e3a5a', 'robe', sway=-1, pivot=(0, 18, -3.4)),   # robe, front
            B('body', -6, 0, 0, 12, 12, 1, '#1e3a5a', 'robe', sway=1, pivot=(0, 18, 3.2)),     # robe, back
            B('arm', -2, -1, -2, 4, 20, 4, '#5a96a0', 'scales', front='bands'),
            B('arm', -2.5, 19, -2.5, 5, 4, 5, '#4a8690', 'web'),
            B('leg', -2, 0, -2, 4, 10, 4, '#5a96a0', 'scales'),
        ]),

    # ---------------- the second band of rogues ----------------
    # Khamsin "Sandshackle" Rahd: a dune of a man. A hunched torso as wide as a cart, a small head sunk forward
    # between his shoulders in a turban and veil with only his amber eyes showing, gorilla arms wrapped in the chains
    # and broken shackles of everyone who escaped him, a gold-coin belt, baggy trousers on short legs, a desert cape.
    "khamsin_sandshackle": dict(
        pivots=dict(head=(0, -3, -3), body=(0, -4, 0), arm=(-11, -2, 0), leg=(-3.5, 12, 0)),
        boxes=[
            B('head', -3, -6, -3, 6, 6, 6, '#9a6a48', None, front='face', eyes='#f0b030', brows='#1a1410', mouth=None),
            B('head', -3.3, -2.6, -3.4, 6.6, 2.6, 1, '#2a2430', 'cloth'),                 # veil over his mouth
            B('head', -4, -9, -3.6, 8, 4, 7.6, '#e8e0cc', 'turban'),
            B('head', -0.6, -8, -3.9, 1.2, 1.2, 0.4, '#d02030', 'gold'),                  # ruby on the turban
            B('head', -1, 0, 0, 2, 9, 1, '#e8e0cc', 'turban', sway=1, pivot=(2, -7, 3.6)),  # its tail
            B('body', -8, -3, -3.5, 16, 4, 9, '#c8a070', 'cloth'),                        # the hump of his shoulders
            B('body', -9, 1, -5, 18, 11, 10, '#c8a070', 'robe', front='sash'),           # the dune of a torso
            B('body', -7, 12, -4.5, 14, 4, 9, '#8a2a2a', 'cloth', front='coins'),        # gold-coin belt
            B('body', -7, 0, -5.4, 2, 13, 1, '#8a8a90', 'chain', rot=(0, 0, -0.6)),     # a chain across his chest
            B('body', -9, 0, 0, 18, 22, 1, '#a87848', 'stripes', sway=1, pivot=(0, -2, 5.2)),   # desert cape
            B('arm', -4, -3, -4, 8, 6, 8, '#6a5a48', 'leather'),                         # leather spaulder
            B('arm', -3.5, 3, -3.5, 7, 7, 7, '#9a6a48', 'muscle'),
            B('arm', -4, 10, -4, 8, 6, 8, '#7a7a80', 'chain'),                           # forearm wrapped in chain
            B('arm', -4.5, 15, -4.5, 9, 2, 9, '#5a5a60', 'iron'),                        # a broken shackle
            B('arm', -3, 17, -3, 6, 4, 6, '#9a6a48', None, front='knuckles'),
            B('arm', -0.5, 0, -0.5, 1, 6, 1, '#8a8a90', 'chain', pivot=(-4, 17, 0)),     # its snapped chain
            B('leg', -3, 0, -3, 6, 8, 6, '#3a3048', 'cloth'),                            # baggy trousers
            B('leg', -3, 8, -3.5, 6, 4, 7, '#5a3a20', 'leather'),
        ]),
    # Captain Mortimer Gale: drowned and cursed, all bone under a ragged coat. A tricorne twice as wide as his
    # shoulders hung with seaweed, a skull with teal fire in its sockets, gold coins stuck in his ribs, a long
    # rotting coat to the ground, a gold hook for a right hand and a peg for a left leg.
    "mortimer_gale": dict(
        pivots=dict(head=(0, -11, 0), body=(0, -11, 0), arm=(-5, -9, 0), leg=(-1.8, 6, 0)),
        boxes=[
            B('head', -3.5, -7, -3.5, 7, 7, 7, '#e4dcc4', 'bone', front='skull'),
            B('head', -3, -1, -3.2, 6, 2, 6, '#d8d0b8', 'bone', front='jaw', teeth='grim'),
            B('head', -8, -8, -7, 16, 1, 14, '#1e1a22', 'coat'),                          # tricorne brim
            B('head', -4, -12, -4, 8, 4, 8, '#1e1a22', 'cloth', front='hatband'),
            B('head', -8, -10, -7.2, 16, 2, 1, '#1e1a22', 'coat'),                        # its upturned front
            B('head', -8, -10, 6.2, 16, 2, 1, '#1e1a22', 'coat'),                         # and back
            B('head', -6.5, -7, -6.5, 1, 6, 1, '#3a6a3a', 'kelp', mirror=True),          # seaweed off the brim
            B('head', 4, -7, 5, 1, 4, 1, '#3a6a3a', 'kelp'),
            B('body', -5, -1, -2.5, 10, 3, 5, '#2a3a40', 'coat'),                         # coat shoulders
            B('body', -3.5, 2, -2, 7, 9, 4, '#e4dcc4', 'ribs'),                          # ribcage, coins in it
            B('body', -1, 11, -1, 2, 3, 2, '#d8d0b8', 'bone'),                           # spine
            B('body', -3, 14, -2, 6, 3, 4, '#d8d0b8', 'bone'),                           # pelvis
            B('body', -5, 2, -2.6, 1.5, 14, 5.2, '#2a3a40', 'coat', mirror=True),        # the open coat
            B('body', -5, 0, 0, 10, 27, 1, '#2a3a40', 'tatters', sway=1, pivot=(0, 2, 2.8)),   # to the ground
            B('arm', -1.5, -1, -1.5, 3, 7, 3, '#2a3a40', 'coat'),
            B('arm', -0.75, 6, -0.75, 1.5, 8, 1.5, '#e4dcc4', 'bone'),
            B('arm', -1.25, 14, -1.25, 2.5, 2, 2.5, '#e4dcc4', 'bone', only='left'),
            B('arm', -1.5, 14, -1.5, 3, 2, 3, '#e8c040', 'gold', only='right'),           # the hook's cuff
            B('arm', -0.5, 16, -0.5, 1, 4, 1, '#e8c040', 'gold', only='right'),
            B('arm', -0.5, 19, -2.5, 1, 1, 2, '#e8c040', 'gold', only='right'),           # the hook's point
            B('leg', -1.5, 0, -1.5, 3, 6, 3, '#4a3a2a', 'cloth'),                         # breeches
            B('leg', -0.75, 6, -0.75, 1.5, 10, 1.5, '#e4dcc4', 'bone', only='right'),
            B('leg', -1.5, 16, -2, 3, 2, 3.5, '#2a2018', 'leather', only='right'),
            B('leg', -0.75, 6, -0.75, 1.5, 12, 1.5, '#6a4a2a', 'wood', only='left'),       # peg leg
        ]),
    # "Tidebreaker" Vasco Morrow rides a young Sea King: a scaled serpent body under a saddle, its neck rearing in
    # front of him to a fanged head with a red crest, a tail out behind and two front flippers that walk it.
    # Vasco is a shirtless brute in a harness with a shark-tooth pauldron, a red headband and a red cape.
    "vasco_tidebreaker": dict(
        pivots=dict(head=(0, -6, -0.5), body=(0, 0, 0), arm=(-7, -5, 0), leg=(-6, 17, -5)),
        boxes=[
            B('head', -3.5, -7, -3.5, 7, 7, 7, '#b07850', None, front='face', eyes='#2a4a6a', brows='#2a1a10', mouth='grin', scar=True),
            B('head', -4, -8.5, -4, 8, 2, 8, '#d84a3a', 'cloth'),                        # headband
            B('head', -3.5, -11, -2, 7, 3, 6, '#1a2a3a', 'hair'),                         # wild hair, swept back
            B('head', -3, -1, -4, 6, 3, 2, '#1a2a3a', 'hair'),                            # beard
            B('body', -4, -6, -2.5, 8, 10, 5, '#b07850', 'muscle', front='harness'),      # Vasco
            B('body', -5, -6, 2, 10, 12, 1, '#8a2a2a', 'coat', sway=1, pivot=(0, -6, 2.6)),   # his cape
            B('body', -9, 4, -3, 2, 7, 4, '#3a3a50', 'cloth', mirror=True),              # his legs down her sides
            B('body', -9.2, 10, -3.5, 2.4, 3, 5, '#2a1a10', 'leather', mirror=True),
            B('body', -5, 4, -4, 10, 2, 9, '#6a3a20', 'leather'),                         # saddle
            B('body', -7, 6, -8, 14, 12, 18, '#3a7a8a', 'scales'),                       # the Sea King's body
            B('body', -6, 15, -7, 12, 3.5, 15, '#c8d8b0', 'scales'),                     # her pale belly
            B('body', -4, 8, 10, 8, 7, 7, '#3a7a8a', 'scales'),                          # tail
            B('body', -2.5, 0, 0, 5, 5, 8, '#3a7a8a', 'scales', sway=1, pivot=(0, 10, 17)),   # tail tip
            B('body', -0.5, 1, 1, 1, 5, 12, '#d84a3a', 'fin'),                            # back fin
            B('body', -3.5, -1, -13, 7, 11, 6, '#3a7a8a', 'scales'),                     # her neck
            B('body', -5, -7, -21, 10, 7, 11, '#3a7a8a', 'scales', front='seaking_face'),
            B('body', -4.5, 0, -20, 9, 3, 9, '#2e6a78', 'scales', front='jaw', teeth='fangs'),
            B('body', -0.5, -12, -18, 1, 5, 8, '#d84a3a', 'fin'),                         # red crest
            B('body', -6.5, -7, -14, 1, 5, 4, '#d84a3a', 'fin', mirror=True),           # fin ears
            B('body', -3, -3, -8.5, 6, 1, 6, '#8a8a90', 'chain'),                         # reins
            B('arm', -3, -2, -3, 5, 4, 6, '#e8e4d8', 'teeth'),                            # shark-tooth pauldron
            B('arm', -2, 2, -2, 4, 7, 4, '#b07850', 'tattoo'),
            B('arm', -2.3, 8, -2.3, 4.6, 3, 4.6, '#5a3a20', 'leather'),                  # bracer
            B('arm', -1.8, 11, -1.8, 3.6, 3, 3.6, '#b07850', None, front='knuckles'),
            B('leg', -2, -1, -3, 4, 6, 6, '#3a7a8a', 'scales'),                           # her front flippers
            B('leg', -2.5, 5, -4, 5, 2, 7, '#2a6a7a', 'web'),
        ]),
    # Dr. Aldous Kreuz: a shrivelled old scientist with a cranium three sizes too big, his own brain floating in a
    # glass dome on top, round green goggles, a torn Navy lab coat, a reactor on his back with two mechanical arms
    # reaching over his head, a stolen Pacifista arm with a paw-pad palm for a right arm, and walker stilts for legs.
    "doctor_kreuz": dict(
        pivots=dict(head=(0, -10, -1), body=(0, -10, 0), arm=(-6, -8, 0), leg=(-3, 4, 0)),
        boxes=[
            B('head', -6, -11, -5.5, 12, 8, 11, '#e0c0a8', None),                           # the cranium
            B('head', -5.5, -16, -5, 11, 5, 10, '#9ad8e8', 'brainjar'),                    # brain in a glass dome
            B('head', -5, -8, -5.9, 10, 3, 1, '#2a2a30', None, front='lenses'),           # goggles
            B('head', -3, -3, -3.5, 6, 3, 5, '#e0c0a8', None, front='face', eyes=None, brows=None, mouth='grin'),
            B('head', -7.2, -9, -3, 1.5, 5, 6, '#f0f0f0', 'hair', mirror=True),              # white tufts
            B('body', -3.5, 0, -2.5, 7, 8, 5, '#f4f4f4', 'cloth', front='labcoat'),
            B('body', -4, 0, 0, 8, 22, 1, '#f4f4f4', 'justice_low', sway=1, pivot=(0, 1, 2.8)),   # lab coat tails
            B('body', -4, 0, 2.5, 8, 8, 4, '#5a6a7a', 'rivets'),                           # reactor pack
            B('body', -1.5, 2, 6.5, 3, 3, 0.5, '#60e0ff', 'glow'),                         # its core
            B('body', -0.75, -14, -0.75, 1.5, 14, 1.5, '#7a8a9a', 'piston', rot=(0.25, 0, -0.5), pivot=(-3, 1, 5), mirror=True),
            B('body', -1.5, -17, -1.5, 3, 3, 3, '#60e0ff', 'glow', rot=(0.25, 0, -0.5), pivot=(-3, 1, 5), mirror=True),  # emitters
            B('body', -4, 8, -2, 8, 3, 4, '#4a5a6a', 'rivets'),                            # walker hips
            B('arm', -4, -3, -4, 7, 6, 8, '#5a6a7a', 'rivets', only='right'),              # the Pacifista arm
            B('arm', -3.5, 3, -3.5, 6, 10, 7, '#6a7a8a', 'rivets', only='right'),
            B('arm', -4, 13, -4, 7, 4, 7, '#3a3a40', None, front='paw', only='right'),
            B('arm', -1.5, -1, -1.5, 3, 10, 3, '#f4f4f4', 'cloth', only='left'),
            B('arm', -1.2, 9, -1.2, 2.4, 2, 2.4, '#e0c0a8', None, only='left'),
            B('leg', -1, 0, -1, 2, 9, 2, '#7a8a9a', 'piston'),                             # walker stilts
            B('leg', -1.5, 9, -1.5, 3, 2, 3, '#4a5a6a', 'rivets'),
            B('leg', -0.75, 11, -0.75, 1.5, 7, 1.5, '#7a8a9a', 'piston'),
            B('leg', -2, 18, -3, 4, 2, 5, '#3a4a5a', 'rivets'),
        ]),

    # ---------------- the sea bosses (captains of the flagships, see tools/ships) ----------------
    # "Harpoon Queen" Maribel Sedge: a rangy, long-limbed whaler in a yellow oilskin coat that sweeps the deck, a
    # sou'wester hat with a brim like a dinghy, a thick red braid, a necklace of Sea King fangs, a quiver of harpoons
    # on her back, one arm in a huge whaler's gauntlet and sea boots up to her thighs.
    "maribel_sedge": dict(
        pivots=dict(head=(0, -8, 0), body=(0, -8, 0), arm=(-5, -6, 0), leg=(-2, 6, 0)),
        boxes=[
            B('head', -3, -7, -3, 6, 7, 6, '#d8a888', None, front='face', eyes='#3a6a7a', brows='#a83a1a', mouth='grin', scar=True),
            B('head', -7, -7.5, -7, 14, 1, 14, '#c8a030', 'leather'),                     # sou'wester brim
            B('head', -3.5, -11, -3.5, 7, 4, 7, '#c8a030', 'leather', front='hatband'),   # its crown
            B('head', -1, -1, 3, 2, 14, 2, '#b83a1a', 'hair'),                             # the red braid
            B('body', -4, 0, -2.5, 8, 7, 5, '#e0b838', 'cloth', front='vest'),             # oilskin over her shirt
            B('body', -4.5, -0.5, -2.9, 9, 1, 0.5, '#f0ece0', 'teeth'),                    # Sea King fang necklace
            B('body', -3.5, 7, -2, 7, 6, 4, '#4a3a2a', 'leather', front='belt'),
            B('body', -5, 0, 0, 10, 26, 1, '#d8ac30', 'cloth', sway=1, pivot=(0, 1, 2.8)), # the long oilskin coat
            B('body', -0.5, -9, -0.5, 1, 16, 1, '#8a8a90', 'iron', rot=(0, 0, 0.3), pivot=(-2, 2, 4)),  # harpoons in the quiver
            B('body', -0.5, -9, -0.5, 1, 15, 1, '#8a8a90', 'iron', rot=(0, 0, -0.2), pivot=(1, 2, 4)),
            B('body', -2, 0, -1.5, 4, 8, 3, '#5a3a20', 'leather', pivot=(0, 2, 4)),      # the quiver
            B('arm', -2, -1, -2, 4, 6, 4, '#e0b838', 'cloth'),                             # oilskin shoulder
            B('arm', -1.25, 5, -1.25, 2.5, 9, 2.5, '#d8a888', 'tattoo', only='left'),
            B('arm', -1.5, 14, -1.5, 3, 2, 3, '#d8a888', only='left'),
            B('arm', -2.5, 5, -2.5, 5, 9, 5, '#5a3a20', 'leather', only='right'),         # the whaler's gauntlet
            B('arm', -3, 14, -3, 6, 4, 6, '#4a3020', 'rivets', front='knuckles', only='right'),
            B('leg', -1.5, 0, -1.5, 3, 10, 3, '#3a3a4a', 'cloth'),
            B('leg', -2, 10, -2.5, 4, 8, 5, '#2a2a2a', 'leather'),                         # sea boots
        ]),
    # Cardinal Severo Lume, the Red Tithe: impossibly tall and gaunt, a pale long-jawed face under a towering red
    # mitre with gold bands, a crimson robe falling to the deck in a train, a high gold collar, arms like candles that
    # reach his knees, and a gold chain with a coin of the Tithe on his chest.
    "severo_lume": dict(
        pivots=dict(head=(0, -12, 0), body=(0, -12, 0), arm=(-5, -10, 0), leg=(-1.6, 7, 0)),
        boxes=[
            B('head', -3, -8, -3, 6, 8, 6, '#ece0d8', None, front='face', eyes='#c02020', brows='#e8e8ec', mouth='smirk', narrow=True),
            B('head', -3.5, -17, -2.5, 7, 9, 5, '#b01c1c', 'robe', front='hatband'),     # the mitre
            B('head', -3.6, -12, -2.6, 7.2, 1, 5.2, '#e8c040', 'gold'),                  # its gold bands
            B('head', -0.5, -17, -2.7, 1, 9, 0.5, '#e8c040', 'gold'),
            B('body', -4.5, -1.5, -3, 9, 3, 6, '#e8c040', 'gold'),                       # the high gold collar
            B('body', -3.5, 1, -2, 7, 11, 4, '#b01c1c', 'robe'),
            B('body', -1.5, 3, -2.3, 3, 3, 0.5, '#e8c040', 'gold'),                      # the Tithe coin
            B('body', -5, 12, -3, 10, 7, 6, '#9a1818', 'robe'),                          # robe skirt over the legs
            B('body', -6, 0, 0, 12, 31, 1, '#8a1414', 'robe', sway=1, pivot=(0, 1, 2.8)),  # the train
            B('arm', -1.5, -1, -1.5, 3, 4, 3, '#b01c1c', 'robe'),
            B('arm', -1, 3, -1, 2, 14, 2, '#b01c1c', 'robe'),                            # sleeves
            B('arm', -1.5, 15, -1.5, 3, 2, 3, '#e8c040', 'gold'),                        # gold cuffs
            B('arm', -1, 17, -1, 2, 2, 2, '#ece0d8'),
            B('leg', -1.5, 0, -1.5, 3, 15, 3, '#7a1010', 'robe'),
            B('leg', -1.6, 15, -2.4, 3.2, 2, 4, '#e8c040', 'gold'),                      # gold slippers
        ]),
    # Kael Ashgrave, the Ash Corsair: a furnace of a man. Shoulders like a smokestack deck with two iron funnels
    # venting from his pauldrons, charred grey skin cracked with ember light, a burning mane, coal-red eyes, a coat of
    # scorched black leather open on a chest crossed by bandoliers of fire shot, forearms in iron, big iron boots.
    "kael_ashgrave": dict(
        pivots=dict(head=(0, -6, -1), body=(0, -5, 0), arm=(-10, -3, 0), leg=(-2.6, 12, 0)),
        boxes=[
            B('head', -3.5, -7, -3.5, 7, 7, 7, '#6a6466', 'soot', front='face', eyes='#ff6020', brows='#2a1a10', mouth='grit', scar=True),
            B('head', -4.5, -11, -2, 9, 6, 7, '#ff8a20', 'mane'),                          # the burning mane
            B('head', -3, -12, 0, 6, 3, 5, '#ffd040', 'mane'),
            B('body', -8, 0, -4, 16, 7, 8, '#6a6466', 'muscle', front='pecs'),             # chest and shoulders
            B('body', -6, 7, -3.5, 12, 7, 7, '#1e1a1c', 'leather', front='belt'),
            B('body', -8.5, -0.5, -4.3, 17, 7.5, 1, '#2a2224', 'leather', front='lacing'), # bandoliers
            B('body', -8.5, 0, 0, 17, 20, 1, '#1e1a1c', 'tatters', sway=1, pivot=(0, 0, 4.5)),  # the scorched coat
            B('arm', -4.5, -4, -4.5, 9, 5, 9, '#2a2a30', 'rivets'),                        # iron pauldron
            B('arm', -1.5, -10, -1.5, 3, 6, 3, '#3a3a40', 'soot'),                         # its funnel
            B('arm', -1.5, -11, -1.5, 3, 1, 3, '#ff8a20', 'glow'),                         # venting fire
            B('arm', -3, 1, -3, 6, 7, 6, '#6a6466', 'muscle'),
            B('arm', -3.5, 8, -3.5, 7, 7, 7, '#3a3a40', 'rivets'),                         # iron forearms
            B('arm', -3, 15, -3, 6, 3, 6, '#5a5458', None, front='knuckles'),
            B('leg', -2.5, 0, -2.5, 5, 8, 5, '#1e1a1c', 'leather'),
            B('leg', -3, 8, -3.5, 6, 4, 7, '#2a2a30', 'rivets'),                           # iron boots
        ]),

}

# The film villains are canon characters, built to their anime proportions in anime.py.
ROGUES.update(anime.FILM)

# ---------------- painting ----------------

def rgb(hexstr):
    h = hexstr.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def paint_face_texture(img, x0, y0, w, h, colour, pattern, rnd, face):
    """One face of a box: base colour, light per face, then the pattern."""
    px = img.load()
    light = {'top': 1.12, 'bottom': 0.72, 'front': 1.0, 'back': 0.86, 'right': 0.92, 'left': 0.92}[face]
    base = shade(colour, light)
    for y in range(h):
        for x in range(w):
            c = base
            n = rnd.random()
            if pattern in ('cloth', 'robe', 'fog'):
                c = shade(base, 0.94 + 0.1 * n)
                if pattern == 'robe' and y % 5 == 0:
                    c = shade(base, 0.9)
                if pattern == 'fog' and (x + y * 2) % 7 == 0:
                    c = shade(base, 1.15)
            elif pattern in ('hair',):
                c = shade(base, 0.85 + 0.25 * ((x * 3 + n * 2) % 3) / 3)
            elif pattern == 'stubble':
                c = shade(base, 0.82) if n < 0.3 else base
            elif pattern == 'tattoo':
                c = (40, 70, 120) if (x + y) % 6 == 0 and 2 < y < h - 2 else shade(base, 0.96 + 0.06 * n)
            elif pattern in ('iron', 'soot'):
                c = shade(base, 0.85 + 0.25 * n)
                if pattern == 'soot' and y < 2:
                    c = (25, 25, 28)
            elif pattern == 'rivets':
                c = shade(base, 0.9 + 0.12 * n)
                if (x % 4 == 1 and y % 4 == 1):
                    c = (200, 190, 170)
                if y % 8 == 0:
                    c = shade(base, 0.7)
            elif pattern == 'chain':
                c = shade(base, 1.2) if y % 2 == 0 else shade(base, 0.6)
            elif pattern == 'leather':
                c = shade(base, 0.9 + 0.15 * n)
            elif pattern == 'veil':
                c = shade(base, 1.3) if (x + y) % 2 == 0 else shade(base, 0.7)
            elif pattern == 'ruff':
                c = shade(base, 1.2) if x % 2 == 0 else shade(base, 0.85)
            elif pattern in ('justice', 'justice_low'):
                c = shade(base, 0.95 + 0.07 * n)
                if pattern == 'justice_low' and y >= h - 2 and (x * 7 + y) % 3 == 0:
                    c = (0, 0, 0)   # ragged hem (cut out)
            elif pattern == 'fringe':
                c = shade(base, 1.15) if y == 0 else (shade(base, 0.85) if x % 2 else base)
            elif pattern == 'lacquer':
                c = shade(base, 1.0 + 0.08 * n)
                if x == 0 or y == 0:
                    c = shade(base, 1.35)
            elif pattern == 'plates':
                c = shade(base, 0.95 + 0.05 * n)
                if y % 3 == 2:
                    c = (200, 160, 70)   # gold lacing between the plates
            elif pattern == 'gold':
                c = shade(base, 0.9 + 0.3 * n)
            elif pattern == 'piston':
                c = shade(base, 1.25) if x == w // 2 else shade(base, 0.9)
            elif pattern == 'scales':
                c = shade(base, 0.92 + 0.12 * ((x + (y % 2)) % 2))
            elif pattern == 'fin':
                c = shade(base, 0.85) if y % 2 == 0 else base
            elif pattern == 'coral':
                c = shade(base, 1.2) if n < 0.3 else base
            elif pattern == 'web':
                c = shade(base, 0.8) if x % 2 == 0 else base
            elif pattern == 'muscle':
                c = shade(base, 0.95 + 0.06 * n)
                if (x * 5 + y * 3) % 11 == 0:
                    c = shade(base, 0.82)   # muscle shading and veins
            elif pattern in ('fur', 'mane'):
                c = shade(base, 0.8 + 0.35 * ((x * 7 + y * 3 + int(n * 3)) % 5) / 5)
                if pattern == 'mane' and (x + 2 * y) % 9 == 0:
                    c = shade(base, 1.2)
            elif pattern == 'coat':
                c = shade(base, 0.94 + 0.08 * n)
                if x in (0, w - 1) or y == h - 1:
                    c = (200, 160, 60)   # gold trim
            elif pattern == 'blade':
                c = shade(base, 1.15) if x == 0 or y == h - 1 else shade(base, 0.9 + 0.1 * n)
                if face in ('left', 'right') and x == w - 1:
                    c = (250, 250, 255)   # the edge
            elif pattern == 'frills':
                c = shade(base, 1.12) if y % 3 == 0 else shade(base, 0.95 + 0.06 * n)
                if y == h - 1 and x % 2:
                    c = (0, 0, 0)   # scalloped hem (cut out)
            elif pattern == 'hairy':
                c = shade(base, 0.95 + 0.06 * n)
                if n < 0.22:
                    c = (40, 30, 26)   # body hair
            elif pattern == 'pinstripe':
                c = shade(base, 1.45) if x % 3 == 0 else shade(base, 0.95 + 0.06 * n)
            elif pattern == 'afro':
                c = shade(base, 0.75 + 0.5 * ((x * 5 + y * 7 + int(n * 4)) % 4) / 4)
            elif pattern == 'stripes':
                c = shade(base, 0.62) if x % 3 == 0 else shade(base, 0.95 + 0.1 * n)
                if y == h - 1 and (x * 7) % 3 == 0:
                    c = (0, 0, 0)   # tattered hem (cut out)
            elif pattern == 'stars':
                c = shade(base, 0.96 + 0.05 * n)
                if (x * 3 + y * 5) % 11 == 0:
                    c = (232, 192, 64)   # gold stars
            elif pattern == 'wood':
                c = shade(base, 0.85 + 0.2 * ((x + int(n * 2)) % 3) / 3)
            elif pattern == 'smasher':
                c = shade(base, 0.92 + 0.12 * n)
                if y % 4 == 0 or x % 6 == 0:
                    c = (60, 60, 70)
                if (x % 6 == 3 and y % 4 == 2):
                    c = (210, 200, 230)   # rivets
            elif pattern == 'turban':
                c = shade(base, 0.9 + 0.08 * n)
                if (y + x // 3) % 3 == 0:
                    c = shade(base, 0.78)   # the wraps
            elif pattern == 'bone':
                c = shade(base, 0.92 + 0.1 * n)
                if n < 0.06:
                    c = shade(base, 0.7)
            elif pattern == 'ribs':
                c = shade(base, 0.95 + 0.06 * n)
                if y % 2 == 1:
                    c = (0, 0, 0) if face in ('front', 'back') and 0 < x < w - 1 else shade(base, 0.6)   # gaps between the ribs
                if face == 'front' and (x * 5 + y * 3) % 13 == 0 and y % 2 == 0:
                    c = (240, 200, 60)   # cursed coins stuck in the bone
            elif pattern == 'tatters':
                c = shade(base, 0.9 + 0.1 * n)
                if n < 0.05:
                    c = (58, 106, 58)   # seaweed caught in it
                if y >= h - 3 and (x * 5 + y) % 3 == 0:
                    c = (0, 0, 0)   # rotted hem (cut out)
            elif pattern == 'kelp':
                c = shade(base, 0.8 + 0.4 * n)
            elif pattern == 'brainjar':
                c = shade(base, 1.0 + 0.1 * n)
                if face != 'bottom' and 1 <= x < w - 1 and 1 <= y and (math.hypot(x - w / 2, y - h) < min(w, 2 * h) / 2.3):
                    c = (232, 150, 170) if (x + y) % 3 else (200, 110, 140)   # the brain inside
            elif pattern == 'glow':
                c = shade(base, 1.1 + 0.1 * n)
            elif pattern == 'teeth':
                c = shade(base, 0.95 + 0.05 * n)
                if (x + y) % 3 == 0:
                    c = (250, 250, 245) if y % 2 else (150, 140, 120)   # shark teeth sewn on
            elif pattern == 'flowers':
                c = shade(base, 0.95 + 0.07 * n)
                if (x * 5 + y * 7) % 13 == 0:
                    c = (236, 168, 40)   # orange-yellow flowers
                elif (x * 5 + y * 7) % 13 in (1, 12) and y % 2 == 0:
                    c = (250, 214, 90)
            elif pattern == 'gears':
                c = shade(base, 0.95 + 0.08 * n)
                if (x % 5 in (1, 3) and y % 5 == 2) or (x % 5 == 2 and y % 5 in (1, 3)):
                    c = (200, 40, 40)   # red gear teeth
                if x % 5 == 2 and y % 5 == 2:
                    c = (120, 20, 20)
            elif pattern in ('purple_trim', 'crossed'):
                c = shade(base, 0.94 + 0.08 * n)
                if x in (0, w - 1) or y == h - 1:
                    c = (138, 80, 180) if pattern == 'purple_trim' else (200, 160, 60)
            elif pattern == 'bone':
                c = shade(base, 0.9 + 0.12 * n)
                if y % 3 == 0:
                    c = shade(base, 0.8)
            elif pattern in ('ring', 'wheel'):
                # A ring (hair loop) or a ship's wheel: the big faces are cut out in the middle.
                c = shade(base, 0.9 + 0.15 * n)
                if w >= 5 and h >= 5:
                    cx, cy = (w - 1) / 2, (h - 1) / 2
                    r = math.hypot((x - cx) / (w / 2), (y - cy) / (h / 2))
                    spoke = pattern == 'wheel' and (abs(x - cx) < 0.6 or abs(y - cy) < 0.6 or abs(abs(x - cx) - abs(y - cy)) < 0.6)
                    if r > 1.0 or (r < 0.62 and not spoke and r > 0.2):
                        c = (0, 0, 0)
            if c == (0, 0, 0):
                px[x0 + x, y0 + y] = (0, 0, 0, 0)
            else:
                px[x0 + x, y0 + y] = c + (255,)


def dot(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), rgb(c) + (255,) if isinstance(c, str) else c + (255,))


def decorate_front(img, x0, y0, w, h, box):
    """The details drawn on a box's front face: faces, jaws, buckles, the firebox..."""
    kind = box.get('front')
    cx = x0 + w // 2
    if kind == 'face':
        ey = y0 + h // 2
        if box.get('goggles'):
            for gx in (cx - 2, cx + 1):
                for dx in range(2):
                    dot(img, gx + dx, ey - 1, '#ffb43c'); dot(img, gx + dx, ey, '#c87820')
            dot(img, cx - 1, ey - 1, '#5a4a3a'); dot(img, cx, ey - 1, '#5a4a3a')
        elif box.get('eyes'):
            for ex in (cx - 2 - (w > 6), cx + 1 + (w > 6)):
                dot(img, ex, ey, '#f4f4f4' if not box.get('slit') else box['eyes'])
                dot(img, ex + (1 if ex < cx else -1) * 0, ey, box['eyes'])
                if box.get('lashes'):
                    dot(img, ex, ey - 1, '#101010')
        if box.get('monocle'):
            dot(img, cx + 2, ey - 1, '#e8c040'); dot(img, cx + 3, ey, '#e8c040'); dot(img, cx + 2, ey + 1, '#e8c040'); dot(img, cx + 1, ey, '#e8c040')
        if box.get('shades'):
            for dx in range(-(w // 2) + 1, w // 2 - 1):
                dot(img, cx + dx, ey, box['shades']); dot(img, cx + dx, ey - 1, '#141418')
        if box.get('brows'):
            for bx in range(w // 2 - 1):
                dot(img, x0 + 1 + bx, ey - 2, box['brows']); dot(img, x0 + w - 2 - bx, ey - 2, box['brows'])
        if box.get('scar'):
            for i in range(4):
                dot(img, x0 + 1 + i, ey - 3 + i, '#a05a50')
        mouth = box.get('mouth')
        my = y0 + h - 2
        if mouth == 'smirk':
            dot(img, cx - 1, my, '#8a3a4a'); dot(img, cx, my, '#8a3a4a'); dot(img, cx + 1, my - 1, '#8a3a4a')
        elif mouth == 'grin':
            for dx in range(-2, 3):
                dot(img, cx + dx, my, '#f8f8f0' if abs(dx) < 2 else '#4a2020')
            dot(img, cx - 1, my, '#e8c040')   # a gold tooth
        elif mouth == 'roar':
            for dx in range(-2, 2):
                dot(img, cx + dx, my, '#3a0a0a'); dot(img, cx + dx, my - 1, '#f4f0e8' if dx % 2 else '#3a0a0a')
            dot(img, cx - 2, my + 1, '#3a0a0a'); dot(img, cx + 1, my + 1, '#3a0a0a')
        elif mouth == 'gap':
            for dx in range(-2, 3):
                dot(img, cx + dx, my, '#f4f0e0' if dx not in (-1, 1) else '#2a1010')   # missing teeth
        elif mouth == 'grit':
            for dx in range(-2, 2):
                dot(img, cx + dx, my, '#f0f0e8' if dx % 2 else '#303030')
    elif kind == 'jaw':
        my = y0 + h // 2
        teeth = box.get('teeth')
        for dx in range(-(w // 2) + 1, w // 2 - 1):
            dot(img, cx + dx, my, '#3a1a1a')
            if teeth == 'underbite' and dx % 2 == 0:
                dot(img, cx + dx, my - 1, '#f4f0e0')
            if teeth == 'fangs':
                dot(img, cx + dx, my - 1, '#f8f8f0'); dot(img, cx + dx, my + 1, '#f8f8f0' if dx % 2 else '#3a1a1a')
            if teeth == 'grim' and abs(dx) < 3:
                dot(img, cx + dx, my - 1, '#e8e4dc')
    elif kind == 'vest':
        for y in range(h):
            for x in range(w // 2 - 3, w // 2 + 3):
                dot(img, x0 + x, y0 + y, shade(rgb(box['colour']) if False else (196, 140, 100), 0.95 + 0.05 * ((x + y) % 2)))
        for y in range(2, 5):
            dot(img, cx - 1, y0 + y, '#6a4a30'); dot(img, cx + 1, y0 + y, '#6a4a30')   # chest hair
    elif kind == 'belt':
        for x in range(w):
            dot(img, x0 + x, y0 + 1, '#3a2a1a'); dot(img, x0 + x, y0 + 2, '#3a2a1a')
        for dx in range(-1, 2):
            dot(img, cx + dx, y0 + 1, '#d0b040'); dot(img, cx + dx, y0 + 2, '#d0b040')
    elif kind == 'knuckles':
        for x in range(1, w - 1, 2):
            dot(img, x0 + x, y0 + 1, shade(rgb(box['colour']), 0.75))
    elif kind == 'hatband':
        for x in range(w):
            dot(img, x0 + x, y0 + h - 2, '#8a2a3a')
        dot(img, x0 + 1, y0 + h - 3, '#d8d8e0'); dot(img, x0 + 2, y0 + h - 4, '#d8d8e0')   # a feather
    elif kind == 'corset':
        for y in range(0, h, 2):
            dot(img, cx - 1, y0 + y, '#c8a050'); dot(img, cx, y0 + y + 1, '#c8a050')
    elif kind == 'lantern':
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                dot(img, x0 + x, y0 + y, '#fff0a0')
    elif kind == 'anchor_badge':
        for dy in range(3):
            dot(img, cx, y0 + 1 + dy, '#d8b040')
        dot(img, cx - 1, y0 + 3, '#d8b040'); dot(img, cx + 1, y0 + 3, '#d8b040')
    elif kind == 'shirt':
        for y in range(h):
            dot(img, cx, y0 + y, '#c8c8d0')
        for y in range(2, h):
            dot(img, x0 + 1, y0 + y, '#323850'); dot(img, x0 + 2, y0 + y, '#323850')
            dot(img, x0 + w - 2, y0 + y, '#323850'); dot(img, x0 + w - 3, y0 + y, '#323850')
    elif kind == 'buttons':
        for y in range(1, h, 2):
            dot(img, cx - 2, y0 + y, '#d8b040'); dot(img, cx + 1, y0 + y, '#d8b040')
    elif kind == 'buckle':
        for dx in range(-1, 2):
            dot(img, cx + dx, y0 + 1, '#d8b040')
    elif kind == 'void_eyes':
        ey = y0 + h // 2
        for ex in (cx - 2, cx + 1):
            dot(img, ex, ey, '#78e6ff'); dot(img, ex + 1, ey, '#c8f8ff')
    elif kind == 'menpo':
        for dx in range(-2, 2):
            dot(img, cx + dx, y0 + 2, '#f0f0f0' if dx % 2 else '#200808')
    elif kind == 'lacing':
        for y in range(1, h, 2):
            for x in range(1, w - 1):
                dot(img, x0 + x, y0 + y, '#d8b048' if (x + y) % 3 else '#a07a30')
    elif kind == 'firebox':
        gy, gh = y0 + h // 2, 6
        for y in range(gh):
            for x in range(-4, 4):
                c = '#ffd060' if (x + y) % 2 == 0 else '#ff7a18'
                if y in (0, gh - 1) or x in (-4, 3) or x == 0:
                    c = '#2a2a2e'
                dot(img, cx + x, gy + y, c)
    elif kind == 'trim':
        for y in range(h):
            dot(img, cx - 1, y0 + y, '#f0dc96'); dot(img, cx, y0 + y, '#f0dc96')
    elif kind == 'pecs':
        for x in range(2, w - 2):
            dot(img, x0 + x, y0 + h // 2 + 1, shade(rgb(box['colour']), 0.75))
        for y in range(1, h // 2 + 2):
            dot(img, cx, y0 + y, shade(rgb(box['colour']), 0.75))
        for x in (3, w - 4):   # scars
            dot(img, x0 + x, y0 + 2, '#b88070'); dot(img, x0 + x + 1, y0 + 3, '#b88070')
    elif kind == 'abs':
        for y in range(0, h, 2):
            for x in range(2, w - 2):
                dot(img, x0 + x, y0 + y, shade(rgb(box['colour']), 0.8))
        for y in range(h):
            dot(img, cx, y0 + y, shade(rgb(box['colour']), 0.75))
    elif kind == 'suit_gold':
        for y in range(h):
            dot(img, cx, y0 + y, '#f8f8f8')
            dot(img, cx - 1 - min(y, 2), y0 + y, '#e8c040'); dot(img, cx + min(y, 2), y0 + y, '#e8c040')   # gold lapels
        for y in (3, 5, 7):
            dot(img, cx, y0 + y, '#e8c040')
        for x in range(1, w - 1):   # gold chains
            dot(img, x0 + x, y0 + 4 + abs(x - w // 2) // 2, '#f0d050')
    elif kind == 'cuff':
        for x in range(w):
            dot(img, x0 + x, y0 + h - 1, '#e8c040'); dot(img, x0 + x, y0 + h - 2, '#e8c040')
    elif kind == 'rings':
        for x in range(w):
            dot(img, x0 + x, y0 + 1, '#fff2a0' if x % 2 else '#b08020')
    elif kind == 'neo_coat':
        for y in range(h):
            for x in range(-2, 2):
                dot(img, cx + x, y0 + y, '#c89070' if y < 4 else '#3a3a48')   # open coat, chest and shirt
        for y in range(1, h, 3):
            dot(img, x0 + 1, y0 + y, '#8a5ab8'); dot(img, x0 + w - 2, y0 + y, '#8a5ab8')
    elif kind == 'smasher_face':
        for y in range(3, h - 3):
            for x in range(2, w - 2):
                if (x - 2) % 3 == 0:
                    dot(img, x0 + x, y0 + y, '#2a2a34')   # vents
        for x in range(1, w - 1):
            dot(img, x0 + x, y0 + 1, '#c8a8ff')   # seastone glow
    elif kind == 'kimono':
        for y in range(h):
            dot(img, cx - 1 + y // 3, y0 + y, '#c8a040'); dot(img, cx + 1 - y // 3, y0 + y, '#c8a040')
    elif kind == 'uta_top':
        for x in range(cx - 2, cx + 2):
            dot(img, x, y0 + 1, '#e890b8'); dot(img, x, y0 + 2, '#e890b8')   # pink bow
        dot(img, cx - 3, y0 + 1, '#e890b8'); dot(img, cx + 2, y0 + 1, '#e890b8')
        for y in range(3, h):
            dot(img, cx - 1, y0 + y, '#3a2a40'); dot(img, cx, y0 + y, '#3a2a40')
    elif kind == 'phones':
        for x in (0, 1, w - 2, w - 1):
            for y in range(h):
                dot(img, x0 + x, y0 + y, '#e890b8' if y == 1 else '#d8d8e0')
    elif kind == 'tesoro_jacket':
        for y in range(h):
            o = max(0, 2 - y // 3)
            for x in range(cx - 1 - o, cx + 1 + o):
                dot(img, x, y0 + y, '#e8c040' if y < 9 else '#f4f0e6')   # gold shirt in the open jacket
        dot(img, x0 + w - 3, y0 + 2, '#c81830'); dot(img, x0 + w - 2, y0 + 2, '#c81830'); dot(img, x0 + w - 3, y0 + 3, '#2a7a30')   # rose
    elif kind == 'uta_dress':
        for x in range(w):
            dot(img, x0 + x, y0, '#ffffff' if x % 2 else '#d8d4dc')   # frilled neck
        for x in range(cx - 2, cx + 2):
            dot(img, x, y0 + 1, '#141418')   # black bow
        for y in range(3, h, 2):
            dot(img, cx - 1, y0 + y, '#141418')   # buttons
    elif kind == 'shiki_kimono':
        for y in range(h):
            o = min(y // 3, 2)
            for x in range(cx - 1 - o, cx + 1 + o):
                dot(img, x, y0 + y, '#1a1414' if y < 7 else '#9a2020')   # black under-kimono
            dot(img, cx - 2 - o, y0 + y, '#e87a20'); dot(img, cx + 1 + o, y0 + y, '#e87a20')   # orange trim
    elif kind == 'strawhat':
        for x in range(w):
            dot(img, x0 + x, y0 + 4, '#e8c860')   # the drawing of a straw hat
        dot(img, cx - 1, y0 + 3, '#c83030'); dot(img, cx, y0 + 3, '#c83030')
        dot(img, cx - 1, y0 + 2, '#e8c860'); dot(img, cx, y0 + 2, '#e8c860')
    elif kind == 'sash':
        for y in range(h):
            dot(img, x0 + 1 + y, y0 + y, '#8a2a2a'); dot(img, x0 + 2 + y, y0 + y, '#8a2a2a')   # a sash from shoulder to hip
    elif kind == 'coins':
        for x in range(1, w - 1, 2):
            dot(img, x0 + x, y0 + 1, '#f0c840'); dot(img, x0 + x, y0 + 2, '#c89a20')
    elif kind == 'skull':
        ey = y0 + h // 2
        for ex in (cx - 2, cx + 1):
            for dx in range(2):
                dot(img, ex + dx, ey - 1, '#101014'); dot(img, ex + dx, ey, '#101014')
            dot(img, ex, ey, '#40f0d0')   # teal fire in the sockets
        dot(img, cx - 1, ey + 2, '#202024'); dot(img, cx, ey + 2, '#202024')   # nose hole
    elif kind == 'seaking_face':
        ey = y0 + h // 2 - 1
        for ex in (x0 + 1, x0 + w - 3):
            dot(img, ex, ey, '#f8e040'); dot(img, ex + 1, ey, '#202010')   # reptile eyes
        for x in range(2, w - 2):
            dot(img, x0 + x, y0 + h - 2, shade(rgb(box['colour']), 0.7))
        dot(img, cx - 1, y0 + 2, '#1a3a40'); dot(img, cx, y0 + 2, '#1a3a40')   # nostrils
    elif kind == 'harness':
        for y in range(h):
            dot(img, x0 + y * w // h, y0 + y, '#4a2a18'); dot(img, x0 + w - 1 - y * w // h, y0 + y, '#4a2a18')
        dot(img, cx, y0 + h // 2, '#d8d8d0'); dot(img, cx - 1, y0 + h // 2, '#d8d8d0')   # a tooth on the buckle
    elif kind == 'lenses':
        for gx in (x0 + 1, x0 + w - 4):
            for dx in range(3):
                for dy in range(h):
                    dot(img, gx + dx, y0 + dy, '#50f070' if (dx, dy) != (1, 1) else '#d8ffd0')
    elif kind == 'labcoat':
        for y in range(h):
            dot(img, cx - 1, y0 + y, '#5a5a6a'); dot(img, cx, y0 + y, '#3a6ac8')   # shirt and tie under the coat
        for y in range(2, 5):
            dot(img, x0 + 1, y0 + y, '#3a6ac8' if y % 2 else '#c83a3a')   # pens in his pocket
        dot(img, x0 + w - 2, y0 + 2, '#28304a'); dot(img, x0 + w - 2, y0 + 3, '#28304a')   # torn Navy badge
    elif kind == 'paw':
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                dot(img, x0 + x, y0 + y, '#e890a8' if (x, y) not in ((1, 1), (w - 2, 1)) else '#3a3a40')   # paw pad
        for x in (1, 3, 5):
            if x < w - 1:
                dot(img, x0 + x, y0, '#e890a8')   # toe beans
    elif kind == 'drago_shirt':
        for y in range(h):
            dot(img, cx - 1, y0 + y, '#d8d4cc')
        for y in range(0, 3):
            for x in range(cx - 1 - (2 - y), cx + 1 + (2 - y)):
                dot(img, x, y0 + y, '#5a3a28')   # open neck
    elif kind == 'gasparde_coat':
        for y in range(h):
            o = max(0, 3 - y // 3)
            for x in range(cx - 1 - o, cx + 1 + o):
                dot(img, x, y0 + y, '#e0b48c' if y < 5 else '#6a4a2a')   # bare chest, then the brown shirt
            dot(img, cx - 2 - o, y0 + y, '#d8b040'); dot(img, cx + 1 + o, y0 + y, '#d8b040')   # gold-trimmed lapels
        for y in (2, 5, 8):
            dot(img, x0 + 1, y0 + y, '#d8b040'); dot(img, x0 + w - 2, y0 + y, '#d8b040')
    elif kind == 'two_buckles':
        for x in (x0 + 1, x0 + w - 3):
            dot(img, x, y0, '#c8c8d0'); dot(img, x + 1, y0, '#c8c8d0'); dot(img, x, y0 + 1, '#c8c8d0'); dot(img, x + 1, y0 + 1, '#c8c8d0')
    elif kind == 'omatsuri_suit':
        for y in range(h):
            dot(img, cx - 1, y0 + y, '#2a1c40')
        for y in (1, 3, 5):
            dot(img, cx, y0 + y, '#e8c040')
    elif kind == 'lily_face':
        # Five yellow petals with red joints and two red dots on each; a smiling face in the middle.
        dot(img, x0 + 1, y0, '#c82020'); dot(img, x0 + w - 2, y0, '#c82020')
        dot(img, x0, y0 + 1, '#c82020'); dot(img, x0 + w - 1, y0 + 1, '#c82020'); dot(img, cx, y0 + h - 1, '#c82020')
        dot(img, cx - 1, y0 + 1, '#1a1a1a'); dot(img, cx + 1 if w > 3 else cx, y0 + 1, '#1a1a1a')
        dot(img, cx - 1, y0 + 2, '#8a2020'); dot(img, cx, y0 + 2, '#8a2020')
    elif kind == 'lens':
        for y in range(h):
            for x in range(w):
                edge = x in (0, w - 1) or y in (0, h - 1)
                dot(img, x0 + x, y0 + y, '#f0a040' if edge else '#fff0d8')
        dot(img, x0 + 1, y0 + 1, '#4a3a2a')   # the wiper
    elif kind == 'overalls':
        for y in range(0, 5):
            dot(img, x0 + 1, y0 + y, '#c09820'); dot(img, x0 + w - 2, y0 + y, '#c09820')   # bib straps
        for x in range(cx - 2, cx + 2):
            dot(img, x, y0 + 5, '#c09820'); dot(img, x, y0 + 7, '#c09820')               # pocket
        dot(img, x0 + 1, y0 + 4, '#f0e0a0'); dot(img, x0 + w - 2, y0 + 4, '#f0e0a0')
    elif kind == 'teddy':
        # The teddy-bear hat's face: two button eyes over its snout.
        ey = y0 + h - 3
        dot(img, cx - 2, ey, '#141414'); dot(img, cx + 1, ey, '#141414')
    elif kind == 'spade':
        # A golden spade standing up behind his head.
        for y in range(h):
            half = min(y + 1, w // 2) if y < h - 2 else 1
            for x in range(cx - half, cx + half):
                dot(img, x, y0 + y, '#f8d860')
        dot(img, cx - 1, y0 + h - 1, '#b08820'); dot(img, cx, y0 + h - 1, '#b08820')
    elif kind == 'pips':
        for y in range(0, 3):   # open at the neck
            for x in range(cx - 2 + y, cx + 2 - y):
                dot(img, x, y0 + y, '#d8a47c')
        dot(img, x0 + 1, y0 + 4, '#1a1a1a'); dot(img, x0 + w - 2, y0 + 5, '#d02020')       # clover and heart
        dot(img, cx, y0 + 7, '#d02020'); dot(img, x0 + 2, y0 + 8, '#1a1a1a')               # diamond, spade
        for y in range(4, h, 2):
            dot(img, cx, y0 + y, '#f0f0f0')
    elif kind == 'festa_coat':
        for y in range(h):
            dot(img, cx - 1, y0 + y, '#f4f0e8'); dot(img, cx, y0 + y, '#f4f0e8')               # the shirt
        for y in range(1, h, 3):
            dot(img, cx - 2, y0 + y, '#e8c040'); dot(img, cx + 1, y0 + y, '#e8c040')            # gold buttons
        for y in range(h):
            dot(img, x0, y0 + y, '#e8c040'); dot(img, x0 + w - 1, y0 + y, '#e8c040')           # gold trim
    elif kind == 'saga_robe':
        for y in range(h):   # the crossed front of the robe
            dot(img, cx - 2 + y // 3, y0 + y, '#701414')
        for y in range(0, 3):
            for x in range(cx - 1, cx + 1 + (2 - y)):
                dot(img, x, y0 + y, '#b07850')
    elif kind == 'butler_coat':
        for y in range(h):
            o = max(0, 2 - y // 4)
            for x in range(cx - o, cx + o):
                dot(img, x, y0 + y, '#e8e4dc')   # white waistcoat
        for y in (2, 5, 8):
            dot(img, cx - 2, y0 + y, '#e8c040')
    elif kind == 'violin':
        for y in range(h):
            for x in range(w):
                if x in (1, w - 2):
                    dot(img, x0 + x, y0 + y, '#4a2a14')   # the strings' shadow
    elif kind == 'bands':
        for y in range(2, h, 5):
            for x in range(w):
                dot(img, x0 + x, y0 + y, '#f0dc96')


# ---------------- layout ----------------

def expand(spec):
    """Mirrors the arm and leg boxes to the left side, and mirrored body/head boxes to the other side."""
    out = []
    for i, b in enumerate(spec['boxes']):
        part = b['part']
        if part in ('arm', 'leg'):
            right = dict(b, part='right_' + part)
            left = dict(b, part='left_' + part, x=-(b['x'] + b['w']))
            if 'pivot' in b:
                px, py, pz = b['pivot']
                left['pivot'] = (-px, py, pz)
            if 'rot' in b:
                rx, ry, rz = b['rot']
                left['rot'] = (rx, -ry, -rz)
            only = b.get('only')
            if only != 'left':
                out.append(right)
            if only != 'right':
                out.append(left)
        else:
            out.append(b)
            if b.get('mirror'):
                m = dict(b, x=-(b['x'] + b['w']), mirror=False)
                if 'pivot' in b:
                    px, py, pz = b['pivot']
                    m['pivot'] = (-px, py, pz)
                if 'rot' in b:
                    rx, ry, rz = b['rot']
                    m['rot'] = (rx, -ry, -rz)
                out.append(m)
    return out


def pack(boxes, size):
    """Shelf-packs every box's UV net (2d+2w wide, d+h tall). Returns (u, v) per box, or None if it won't fit."""
    x = y = shelf = 0
    spots = []
    for b in boxes:
        # Room for the net as painted (whole pixels per side), which can be a pixel wider than the exact sizes.
        rw, rh, rd = (int(round(b[k])) for k in ('w', 'h', 'd'))
        bw = max(int(2 * b['d'] + 2 * b['w']), 2 * rd + 2 * rw) + 1
        bh = max(int(b['d'] + b['h']), rd + rh) + 1
        if x + bw > size:
            x, y, shelf = 0, y + shelf, 0
        if y + bh > size or bw > size:
            return None
        spots.append((x, y))
        x += bw
        shelf = max(shelf, bh)
    return spots


def paint_box(img, u, v, b, rnd):
    w, h, d = int(round(b['w'])), int(round(b['h'])), int(round(b['d']))
    colour = rgb(b['colour'])
    pat = b.get('pattern')
    faces = {
        'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d),
        'right': (u, v + d, d, h), 'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h),
    }
    for name, (fx, fy, fw, fh) in faces.items():
        paint_face_texture(img, fx, fy, fw, fh, colour, pat, rnd, name)
    if b.get('front'):
        fx, fy, fw, fh = faces['front']
        decorate_front(img, fx, fy, fw, fh, b)
    if b.get('pattern') == 'crossed':
        fx, fy, fw, fh = faces['back']
        mx, my = fx + fw // 2, fy + 4
        for dx in range(-3, 4):
            dot(img, mx + dx, my + abs(dx) // 2, (230, 230, 236))   # the Marines' gull
        for i in range(-3, 4):
            dot(img, mx + i, my - 2 + (i + 3), (200, 30, 30)); dot(img, mx - i, my - 2 + (i + 3), (200, 30, 30))   # crossed out
    if b.get('pattern') in ('justice', ) and b['w'] >= 12:
        # The Navy's "Justice" on the back of the coat, torn through.
        fx, fy, fw, fh = faces['back']
        for i, x in enumerate(range(fx + 2, fx + fw - 2)):
            if i % 3 != 2 and i != 5:
                dot(img, x, fy + 3, (40, 48, 74)); dot(img, x, fy + 4 + (i % 2), (40, 48, 74))


# ---------------- Java ----------------

def f(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return (s if s not in ('-0', '') else '0') + 'F'


def java(rogues, layouts):
    lines = []
    w = lines.append
    w('package com.onepiecebosses.client;')
    w('')
    w('import java.util.Map;')
    w('import java.util.Set;')
    w('')
    w('import net.minecraft.client.model.HumanoidModel;')
    w('import net.minecraft.client.model.geom.ModelLayerLocation;')
    w('import net.minecraft.client.model.geom.PartPose;')
    w('import net.minecraft.client.model.geom.builders.CubeDeformation;')
    w('import net.minecraft.client.model.geom.builders.CubeListBuilder;')
    w('import net.minecraft.client.model.geom.builders.LayerDefinition;')
    w('import net.minecraft.client.model.geom.builders.MeshDefinition;')
    w('import net.minecraft.client.model.geom.builders.PartDefinition;')
    w('')
    w('import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;')
    w('')
    w('import com.onepiecebosses.BossesMod;')
    w('')
    w('/**')
    w(' * Every rogue\'s own body, with wild One Piece proportions instead of the player shape. Each keeps the player')
    w(' * model\'s parts (head, body, arms, legs) so it walks, swings and looks around like one, but the parts sit where')
    w(' * that rogue\'s body needs them and are built from its own boxes. Skins are 128x128 (or 256) and match these boxes;')
    w(' * the PNGs are drawn at twice that, so faces get more pixels.')
    w(' * GENERATED by tools/gen_models.py, which also paints the skins: change the shapes there and run it again')
    w(' * instead of editing this file.')
    w(' */')
    w('public final class RogueModels {')
    w('\tpublic static final Set<String> IDS = Set.of(%s);' % ', '.join('"%s"' % i for i in rogues))
    w('')
    w('\t/** Each rogue\'s right shoulder (x, y, z); RogueModel keeps the arms there while the boss swings. */')
    w('\tpublic static final Map<String, float[]> SHOULDERS = Map.ofEntries(%s);' % ', '.join(
        'Map.entry("%s", new float[] {%s})' % (i, ', '.join(f(v) for v in rogues[i]['pivots']['arm'])) for i in rogues))
    w('')
    w('\t/** How far below the shoulder each rogue\'s hand is, in pixels (a player\'s is about 10). */')
    w('\tpublic static final Map<String, Float> HANDS = Map.ofEntries(%s);' % ', '.join(
        'Map.entry("%s", %sF)' % (i, f(max(b['y'] + b['h'] for b in rogues[i]['boxes'] if b['part'] == 'arm' and 'pivot' not in b and b.get('only') != 'right') - 1.5)[:-1]) for i in rogues))
    w('')
    w('\tprivate RogueModels() {')
    w('\t}')
    w('')
    w('\tpublic static ModelLayerLocation layer(String id) {')
    w('\t\treturn new ModelLayerLocation(BossesMod.id("rogue_" + id), "main");')
    w('\t}')
    w('')
    w('\t/** Registers one model layer per rogue. BossesClient calls this. */')
    w('\tpublic static void register() {')
    w('\t\tfor (String id : IDS) {')
    w('\t\t\tModelLayerRegistry.registerModelLayer(layer(id), () -> create(id));')
    w('\t\t}')
    w('\t}')
    w('')
    w('\tpublic static LayerDefinition create(String id) {')
    w('\t\t// Start from the player model so every part HumanoidModel looks for exists, then rebuild the parts.')
    w('\t\tMeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);')
    w('\t\tint size = switch (id) {')
    for i in rogues:
        w('\t\t\tcase "%s" -> %s(mesh);' % (i, camel(i)))
    w('\t\t\tdefault -> 64;')
    w('\t\t};')
    w('\t\treturn LayerDefinition.create(mesh, size, size);')
    w('\t}')
    w('')
    w('\t/** The basic parts at this rogue\'s pivots, with no boxes of their own (the boxes are their children). */')
    w('\tprivate static PartDefinition[] parts(MeshDefinition mesh, float[] head, float[] body, float[] arm, float[] leg) {')
    w('\t\tPartDefinition root = mesh.getRoot();')
    w('\t\tPartDefinition headPart = root.addOrReplaceChild("head", CubeListBuilder.create(), PartPose.offset(head[0], head[1], head[2]));')
    w('\t\theadPart.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO);')
    w('\t\treturn new PartDefinition[] {')
    w('\t\t\theadPart,')
    w('\t\t\troot.addOrReplaceChild("body", CubeListBuilder.create(), PartPose.offset(body[0], body[1], body[2])),')
    w('\t\t\troot.addOrReplaceChild("right_arm", CubeListBuilder.create(), PartPose.offset(arm[0], arm[1], arm[2])),')
    w('\t\t\troot.addOrReplaceChild("left_arm", CubeListBuilder.create(), PartPose.offset(-arm[0], arm[1], arm[2])),')
    w('\t\t\troot.addOrReplaceChild("right_leg", CubeListBuilder.create(), PartPose.offset(leg[0], leg[1], leg[2])),')
    w('\t\t\troot.addOrReplaceChild("left_leg", CubeListBuilder.create(), PartPose.offset(-leg[0], leg[1], leg[2])),')
    w('\t\t};')
    w('\t}')
    sway = {}
    for i, spec in rogues.items():
        boxes, spots, size = layouts[i]
        p = spec['pivots']
        w('')
        w('\tprivate static int %s(MeshDefinition mesh) {' % camel(i))
        w('\t\tPartDefinition[] p = parts(mesh, new float[] {%s}, new float[] {%s}, new float[] {%s}, new float[] {%s});' % tuple(
            ', '.join(f(v) for v in p[k]) for k in ('head', 'body', 'arm', 'leg')))
        w('\t\tPartDefinition head = p[0], body = p[1], rightArm = p[2], leftArm = p[3], rightLeg = p[4], leftLeg = p[5];')
        var = {'head': 'head', 'body': 'body', 'right_arm': 'rightArm', 'left_arm': 'leftArm', 'right_leg': 'rightLeg', 'left_leg': 'leftLeg'}
        sways = []
        named = {}
        paths = {}
        for n, (b, (u, v)) in enumerate(zip(boxes, spots)):
            name = 'b%d' % n
            parent = var[b['part']]
            if b.get('parent'):
                parent = named[b['parent']]
            if b.get('sway'):
                name = 'sway%d' % len(sways)
                path = (paths[b['parent']] if b.get('parent') else b['part']) + '/' + name
                paths[name] = path
                sways.append((path, b['sway'], b.get('parent') is not None))
            pv = b.get('pivot', (0, 0, 0))
            rot = b.get('rot', (0, 0, 0))
            # A box with its own pivot is drawn relative to that pivot (its x, y, z start from there).
            decl = 'PartDefinition %s = ' % name if b.get('sway') else ''
            w('\t\t%s%s.addOrReplaceChild("%s", CubeListBuilder.create().texOffs(%d, %d).addBox(%s, %s, %s, %s, %s, %s),' % (
                decl, parent, name, u, v, f(b['x']), f(b['y']), f(b['z']), f(b['w']), f(b['h']), f(b['d'])))
            w('\t\t\t\tPartPose.offsetAndRotation(%s, %s, %s, %s, %s, %s));' % tuple(f(x) for x in tuple(pv) + tuple(rot)))
            if b.get('sway'):
                named[name] = name
                named['sway%d' % (len(sways) - 1)] = name
        w('\t\treturn %d;' % size)
        w('\t}')
        sway[i] = sways
    w('')
    w('\t/** Coat tails, trains and skirts that swing as the boss walks, by their path from the model root: 1 swings out behind, -1 in front. */')
    w('\tpublic static Map<String, Integer> sway(String id) {')
    w('\t\treturn switch (id) {')
    for i, sw in sway.items():
        if sw:
            w('\t\t\tcase "%s" -> Map.of(%s);' % (i, ', '.join('"%s", %d' % (n, d) for n, d, _ in sw)))
    w('\t\t\tdefault -> Map.of();')
    w('\t\t};')
    w('\t}')
    w('}')
    return '\n'.join(lines) + '\n'


def camel(s):
    a = s.split('_')
    return a[0] + ''.join(x.title() for x in a[1:])


def main(root):
    res = os.path.join(root, 'src/main/resources/assets/opbosses/textures/entity/boss')
    os.makedirs(res, exist_ok=True)
    layouts = {}
    for i, spec in ROGUES.items():
        boxes = expand(spec)
        for size in (128, 256):
            spots = pack(boxes, size)
            if spots:
                break
        else:
            sys.exit('%s: the boxes do not fit in a 256x256 skin' % i)
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        rnd = random.Random(i)
        for b, (u, v) in zip(boxes, spots):
            paint_box(img, u, v, b, rnd)
        # The skin is saved at skin.SCALE times its declared size, with every face redrawn at that resolution.
        big = skin.upscale(img)
        for b, (u, v) in zip(boxes, spots):
            if b.get('front') == 'face':
                d = int(round(b['d']))
                skin.paint_face(big, u + d, v + d, b['w'], b['h'], b)
        big.save(os.path.join(res, i + '.png'))
        layouts[i] = (boxes, spots, size)
    out = os.path.join(root, 'src/main/java/com/onepiecebosses/client/RogueModels.java')
    with open(out, 'w') as fh:
        fh.write(java(ROGUES, layouts))
    print('Built %d rogue models' % len(ROGUES))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
