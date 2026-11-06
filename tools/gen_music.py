"""
A battle theme for every lair (assets/opbosses/sounds/music/<lair>.ogg), written for this mod.

Uses the One Piece Mod's own little synthesizer (its tools/sounds), so nothing is sampled or copied: every note is
math. Point ONEPIECE_SOUNDS at that folder:

    ONEPIECE_SOUNDS=../one-piece-mod/tools/sounds python3 tools/gen_music.py [lair ...]

How a theme is written: each lair has two 2-bar motifs in scale degrees (0 = the key's tonic, 7 = an octave up,
"b"/"#" bend a note, "^" is the leading tone). The A section plays motif A, moves it to another chord and back, then a
cadence onto the dominant; the B section does the same with motif B. Chords follow the motif, so the tune always fits.
Form: intro (4 bars), A (8), B (8), A again louder (8), a bridge that builds (4), then it loops.
"""
import functools
import os
import sys

import numpy as np

sys.path.insert(0, os.environ.get("ONEPIECE_SOUNDS", os.path.join(os.path.dirname(__file__), "..", "..", "one-piece-mod", "tools", "sounds")))
from synth import (SR, Song, accordion, bell, brass, choir, crash, env, fft_filter, fiddle, finish, hat, hz, kick, noise,  # noqa: E402
				   piano, pluck_bass, reverb, save_ogg, snare, strings, synth_bass, tambourine, timpani, tom, whistle)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "assets", "opbosses", "sounds", "music")
MINOR = [0, 2, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
		"A#": 10, "Bb": 10, "B": 11}


# ------------------------------------------------------------------ extra instruments (as in the main mod's music_more)

def organ(f, d, v=1.0):
	n = int((d + 0.12) * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for k, a in ((0.5, 0.5), (1, 1.0), (2, 0.6), (3, 0.35), (4, 0.3), (6, 0.15), (8, 0.12)):
		if f * k < 9000:
			x += a * np.sin(2 * np.pi * f * k * t)
	x *= 1 + 0.08 * np.sin(2 * np.pi * 6.2 * t)
	return x * env(n, 0.03, 0.1, 0.9, 0.12, hold=d) * v * 0.1


def chip(f, d, v=1.0):
	n = int((d + 0.05) * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for k in range(1, 16, 2):
		if f * k < 12000:
			x += np.sin(2 * np.pi * f * k * t) / k
	return x * env(n, 0.004, 0.08, 0.6, 0.04, hold=d) * v * 0.16


def music_box(f, d, v=1.0):
	return bell(f, d, v, decay=0.45)


def harp(f, d, v=1.0):
	return pluck_bass(f, d, v) * 0.7


def marimba(f, d, v=1.0):
	return bell(f, d, v, decay=0.35)


def choir_oo(f, d, v=1.0):
	return choir(f, d, v, vowel="oo")


def clap(v=1.0):
	d = 0.2
	t = np.arange(int(d * SR)) / SR
	e = sum(np.exp(-np.clip(t - o, 0, None) / 0.006) * (t >= o) for o in (0, 0.01, 0.022)) + np.exp(-t / 0.05) * 0.6
	return fft_filter(noise(d), 900, 7000) * e * v * 0.4


def clank(v=1.0, seed=0):
	"""A struck piece of metal: anvils in the foundry, gears in the castle, chains on the reef."""
	rng = np.random.default_rng(seed)
	n = int(0.35 * SR)
	t = np.arange(n) / SR
	f = rng.uniform(900, 1500)
	x = sum(a * np.sin(2 * np.pi * f * r * t) for r, a in ((1, 1.0), (2.76, 0.6), (5.4, 0.35), (8.9, 0.2)))
	x = x * np.exp(-t / 0.07) + fft_filter(noise(0.35), 2000, 9000) * np.exp(-t / 0.01) * 0.5
	return x * v * 0.22


@functools.lru_cache(maxsize=None)
def _taiko(v):
	low = timpani(55, 0.4, v * 0.6)
	low[:int(0.5 * SR)] += tom(70, v) * 1.4
	return low


def taiko(v=1.0):
	return _taiko(round(v, 2))


INSTRUMENTS = {"brass": brass, "strings": strings, "choir": choir, "choir_oo": choir_oo, "accordion": accordion, "fiddle": fiddle,
			   "whistle": whistle, "piano": piano, "organ": organ, "chip": chip, "music_box": music_box, "harp": harp,
			   "marimba": marimba, "synth_bass": synth_bass, "pluck_bass": pluck_bass}


# ------------------------------------------------------------------ the lairs' themes

# lead: tonic of the tune (its octave sets the range). sA: where motif A moves (scale steps, -2 = the VI chord).
# bB: the chord the B section starts on; sB: where motif B moves from there. power: power chords (no thirds), for
# tunes that bend notes outside the scale.
THEMES = {
	"scrapheap_reef": dict(  # Rourke: a salvage crew's stomp. Accordion over clanking chains.
		key="D5", bpm=150, A="0:0.5 0:0.5 4:1 3:0.5 2:0.5 0:1 2:1.5 4:0.5 7:1 4:1", sA=-1,
		B="4:1 4:0.5 5:0.5 4:1 2:1 4:2 2:1 0:1", bB=-2, sB=1,
		lead="accordion", counter="fiddle", pad="strings", bass="drive", drums="rock", extra="chains"),
	"lantern_house": dict(  # Corvina: slow and foggy, a music box in the mist.
		key="E5", bpm=104, A="4:2 3:1 2:1 0:1.5 -1:0.5 0:2", sA=-2,
		B="7:1.5 6:0.5 4:1 2:1 4:3 r:1", bB=3, sB=-1,
		lead="music_box", counter="strings", pad="choir_oo", bass="pulse", drums="halftime", extra="bells"),
	"fort_iron_tide": dict(  # Graves: a deserters' march with snare and timpani.
		key="C5", bpm=124, A="0:1 0:0.5 0:0.5 2:1 4:1 7:2 4:1 2:1", sA=3,
		B="4:1.5 5:0.5 4:1 2:1 0:2 2:1 4:1", bB=-2, sB=1,
		lead="brass", counter="strings", pad="strings", bass="march", drums="march", extra="timpani"),
	"hollow_shrine": dict(  # Tsurugi: a lone flute, a koto and taiko drums.
		key="A4", bpm=108, A="0:1 1b:0.5 0:0.5 4:2 3:1 1b:0.5 0:0.5 0:2", sA=-2,
		B="4:1 5:0.5 4:0.5 7:2 5:1 4:1 3:0.5 1b:0.5 0:1", bB=3, sB=-1, power=True,
		lead="whistle", counter="harp", pad="strings", bass="pulse", drums="taiko", extra="koto"),
	"shipbreakers_foundry": dict(  # Gantz: an anvil-beat, organ and brass over a grinding bass.
		key="E5", bpm=142, A="0:0.5 0:0.5 2:0.5 0:0.5 4:1 3:1 2:1 0:1 -1:1 0:1", sA=-1,
		B="7:1 6:0.5 4:0.5 3:1 4:1 2:2 0:2", bB=3, sB=-1, power=True,
		lead="brass", counter="organ", pad="organ", bass="drive", drums="industrial", extra="anvils"),
	"abyssal_temple": dict(  # Nereus: a sunken cathedral, choir and organ.
		key="C#5", bpm=96, A="0:2 2:1 4:1 3:2 2:2", sA=-2,
		B="4:2 5:1 4:1 2:2 0:2", bB=3, sB=-1,
		lead="choir", counter="organ", pad="organ", bass="pulse", drums="epic", extra="bells"),
	"sunken_kasbah": dict(  # Khamsin: desert strings, tambourine and hand drums.
		key="D5", bpm=134, A="0:0.5 1b:0.5 0:0.5 1b:0.5 2#:1 1b:1 0:1.5 1b:0.5 0:2", sA=0,
		B="4:1 5b:1 4:1 2#:1 1b:2 0:2", bB=0, sB=-1, power=True,
		lead="fiddle", counter="whistle", pad="strings", bass="gallop", drums="desert", extra="none"),
	"gilded_wake": dict(  # Mortimer: a ghost ship's organ, a rolling shanty beat, rattling chains.
		key="G4", bpm=120, A="0:1 2:1 4:1 7:1 4:1.5 2:0.5 3:1 2:1", sA=-2,
		B="7:2 4:1 5:1 4:2 r:2", bB=3, sB=-1,
		lead="organ", counter="fiddle", pad="choir_oo", bass="pulse", drums="shanty", extra="chains"),
	"leviathan_pens": dict(  # Vasco: big brass and timpani, something huge moving under the water.
		key="F4", bpm=136, A="0:1.5 4:0.5 3:1 2:1 0:1 2:1 4:2", sA=3,
		B="4:1 7:1 6:1 4:1 4:2 2:2", bB=-2, sB=1,
		lead="brass", counter="choir", pad="strings", bass="drive", drums="epic", extra="timpani"),
	"laboratory_null": dict(  # Kreuz: cold electronics, a four-on-the-floor machine pulse.
		key="B4", bpm=150, A="0:0.5 2:0.5 4:0.5 7:0.5 4:0.5 2:0.5 0:0.5 2:0.5 3:1 2:1 0:2", sA=-2,
		B="7:0.5 7:0.5 6:0.5 4:0.5 7:1 4:1 2:1 3:1 4:2", bB=3, sB=-1,
		lead="chip", counter="chip", pad="strings", bass="drive", drums="four", extra="arp"),
	"gran_tesoro": dict(  # Tesoro: a casino big band, swinging brass and piano.
		key="C5", bpm=160, A="7:0.5 6:0.5 4:1 2:0.5 4:0.5 7:1 6:1 4:1 2:1 0:1", sA=3,
		B="4:1 4:0.5 5:0.5 4:1 2:1 3:1 2:1 0:2", bB=-2, sB=1,
		lead="brass", counter="piano", pad="strings", bass="walk", drums="swing", extra="bells"),
	"elegia_stage": dict(  # Uta: a concert. Bright, a voice over piano and a dance beat.
		key="A4", bpm=128, scale="major", A="4:1 4:0.5 5:0.5 4:1 2:1 0:1 2:1 4:2", sA=3,
		B="7:1.5 5:0.5 4:1 5:1 4:2 2:2", bB=-2, sB=-1,
		lead="choir", counter="piano", pad="strings", bass="four", drums="four", extra="arp"),
	"end_point": dict(  # Zephyr: a heroic, tragic Navy march on a burning island.
		key="D5", bpm=120, A="0:1.5 2:0.5 4:2 7:1 6:1 4:2", sA=-2,
		B="4:2 7:2 6:1 4:1 2:2", bB=3, sB=-1,
		lead="brass", counter="strings", pad="choir", bass="march", drums="march", extra="timpani"),
	"ironclad_colosseum": dict(  # Bullet: heavy and fast, a gladiator's war drum.
		key="E4", bpm=166, A="0:0.5 0:0.5 0:0.5 2:0.5 3:1 2:1 0:0.5 0:0.5 -1:1 0:2", sA=-2,
		B="4:1 4:1 2:1 4:1 7:2 4:2", bB=3, sB=-1, power=True,
		lead="brass", counter="strings", pad="organ", bass="drive", drums="rock", extra="anvils"),
	"merveille": dict(  # Shiki: soaring strings and brass over floating islands.
		key="G4", bpm=140, A="0:1 4:1 7:1.5 6:0.5 4:2 2:1 4:1", sA=3,
		B="9:2 7:1 4:1 7:2 4:2", bB=-2, sB=1,
		lead="brass", counter="choir", pad="strings", bass="drive", drums="epic", extra="timpani"),
	"gold_island": dict(  # El Drago: a booming pirate fanfare.
		key="A4", bpm=146, A="0:0.5 2:0.5 4:0.5 2:0.5 0:1 4:1 3:1 2:1 0:1 2:1", sA=-1,
		B="7:1 4:1 6:1 4:1 2:2 0:2", bB=3, sB=-1,
		lead="brass", counter="fiddle", pad="strings", bass="gallop", drums="rock", extra="timpani"),
	"salamander": dict(  # Gasparde: a warship's cold brass and a sea-shanty swing gone sour.
		key="F#4", bpm=136, A="0:1 2:1 4:0.5 3:0.5 2:1 0:1.5 -3:0.5 0:2", sA=-2,
		B="4:1 5:1 4:1 2:1 3:2 2:2", bB=3, sB=-1,
		lead="brass", counter="accordion", pad="strings", bass="drive", drums="shanty", extra="none"),
	"omatsuri_island": dict(  # Omatsuri: festival flutes and drums with something wrong underneath.
		key="E5", bpm=132, A="0:0.5 0:0.5 2:1 4:0.5 2:0.5 0:1 4:1 7:1 4:2", sA=3,
		B="7:1 9:1 7:1 4:1 4:2 2:2", bB=-2, sB=1,
		lead="whistle", counter="harp", pad="strings", bass="pulse", drums="festival", extra="bells"),
	"karakuri_castle": dict(  # Ratchet: ticking clockwork, marimba and chiptune gears.
		key="C5", bpm=144, A="0:0.5 4:0.5 2:0.5 4:0.5 0:0.5 4:0.5 2:0.5 4:0.5 3:1 4:1 2:2", sA=-1,
		B="7:0.5 6:0.5 4:0.5 6:0.5 7:1 4:1 2:1 3:1 4:2", bB=3, sB=-1,
		lead="chip", counter="marimba", pad="organ", bass="drive", drums="industrial", extra="clockwork"),
	"groseade": dict(  # Byrnndi World: enormous. Brass, choir and thundering drums.
		key="F4", bpm=156, A="0:1 0:0.5 2:0.5 4:1 7:1 4:1.5 2:0.5 0:2", sA=-2,
		B="7:1 4:1 9:1 7:1 4:2 7:2", bB=3, sB=-1,
		lead="brass", counter="choir", pad="strings", bass="drive", drums="rock", extra="timpani"),
	"clockwork_island": dict(  # Bear King: a clock tower's march, gears ticking under brass.
		key="D5", bpm=140, A="0:0.5 2:0.5 4:1 2:0.5 0:0.5 4:1 3:1 2:1 0:2", sA=-2,
		B="7:1 6:0.5 4:0.5 2:1 4:1 3:2 2:2", bB=3, sB=-1,
		lead="brass", counter="marimba", pad="organ", bass="drive", drums="industrial", extra="clockwork"),
	"delta_island": dict(  # Buena Festa: the pirate festival, a carnival band with a dangerous edge.
		key="A4", bpm=150, A="0:0.5 0:0.5 4:0.5 4:0.5 7:1 4:1 6:1 4:1 2:2", sA=3,
		B="4:1 5:0.5 4:0.5 2:1 4:1 7:2 4:2", bB=-2, sB=1,
		lead="brass", counter="accordion", pad="strings", bass="gallop", drums="festival", extra="bells"),
	"asuka_island": dict(  # Saga: a cursed blade's shrine, flute and koto over slow taiko.
		key="B4", bpm=116, A="0:1.5 2:0.5 4:1 7:1 6:1 4:1 2:2", sA=-2,
		B="4:1 5:0.5 4:0.5 2:1 1b:1 0:4", bB=3, sB=-1, power=True,
		lead="whistle", counter="harp", pad="strings", bass="pulse", drums="taiko", extra="koto"),
	"crown_island": dict(  # Count Butler: a stolen crown, a pompous court march gone wild.
		key="G4", bpm=128, A="0:1 4:1 2:0.5 4:0.5 7:1 6:1 4:1 2:1 4:1", sA=3,
		B="7:2 4:1 2:1 4:2 0:2", bB=-2, sB=1,
		lead="strings", counter="brass", pad="choir", bass="march", drums="march", extra="bells"),
}

# The cadences end each section on the dominant (V), so every section leads back to the tonic.
CAD_A = "5:1.5 4:0.5 2:1 0:1 1:1.5 2:0.5 1:1 -1^:1"  # over VI then V
CAD_B = "3:1 5:1 7:1.5 5:0.5 4:2 6^:2"  # over iv (IV) then V


# ------------------------------------------------------------------ building a theme

class Key:
	def __init__(self, tonic, scale):
		name = tonic.rstrip("0123456789")
		self.tonic = NOTE[name] + 12 * (int(tonic[len(name):]) + 1)
		self.scale = MAJOR if scale == "major" else MINOR
		self.minor = scale != "major"

	def note(self, token, shift=0):
		"""A scale-degree token ('4', '-1', '1b', '2#', '6^') -> midi number."""
		bend = 0
		if token.endswith("^"):
			d = int(token[:-1])
			return self.tonic + 12 * ((d + 1) // 7) - 1
		if token[-1] in "b#":
			bend = -1 if token[-1] == "b" else 1
			token = token[:-1]
		d = int(token) + shift
		return self.tonic + 12 * (d // 7) + self.scale[d % 7] + bend

	def chord(self, degree, octave_root, power=False):
		"""The triad on a scale degree, rooted near octave_root. In minor the V chord is major."""
		d = degree % 7
		root = self.tonic % 12 + self.scale[d]
		while root < octave_root:
			root += 12
		while root >= octave_root + 12:
			root -= 12
		if power:
			return [root, root + 7, root + 12]
		third = (self.scale[(d + 2) % 7] - self.scale[d]) % 12
		if self.minor and d == 4:
			third = 4
		fifth = (self.scale[(d + 4) % 7] - self.scale[d]) % 12
		return [root, root + third, root + fifth]


def melody(key, line, shift=0):
	"""'0:1 4:0.5 r:1' -> [(midi or None, beats)]."""
	out = []
	for tok in line.split():
		deg, beats = tok.split(":")
		out.append((None if deg == "r" else key.note(deg, shift), float(beats)))
	assert abs(sum(b for _, b in out) - 8) < 1e-6, f"{line}: {sum(b for _, b in out)} beats, want 8"
	return out


def play(s, at, notes, inst, gain, transpose=0, legato=0.92):
	b = at
	for m, beats in notes:
		if m is not None:
			s.add(b, inst(hz(m + transpose), beats * s.spb * legato), gain)
		b += beats


def section(key, motif, start, shift):
	"""8 bars: the motif, the motif moved, the motif again, then the cadence. Returns (notes per 2 bars, chords)."""
	cad = CAD_A if start == 0 else CAD_B
	parts = [melody(key, motif, start), melody(key, motif, start + shift), melody(key, motif, start), melody(key, cad)]
	chords = [start, start, start + shift, start + shift, start, start, 5 if start == 0 else 3, 4]
	return parts, chords


def bass_line(s, key, b0, chords, style, inst, power):
	for i, c in enumerate(chords):
		r = key.chord(c, 36, power)[0]
		fifth, octave = r + 7, r + 12
		bar = b0 + i * 4
		hits = {
			"drive": [(k * 0.5, [r, r, octave, r, fifth, r, octave, fifth][k], 0.45) for k in range(8)],
			"pulse": [(0, r, 1.8), (2, r, 1.8)],
			"march": [(0, r, 0.9), (1, fifth, 0.9), (2, r, 0.9), (3, fifth, 0.9)],
			"gallop": [(0, r, 0.4), (0.75, r, 0.2), (1, r, 0.4), (2, r, 0.4), (2.75, r, 0.2), (3, fifth, 0.4)],
			"walk": [(0, r, 0.9), (1, r + key.chord(c, 36)[1] - key.chord(c, 36)[0], 0.9), (2, fifth, 0.9), (3, octave - 1, 0.9)],
			"four": [(k * 0.5, r if k % 2 == 0 else octave, 0.4) for k in range(8)],
		}[style]
		for at, m, ln in hits:
			s.add(bar + at, inst(hz(m), ln * s.spb, 0.85), 0.7)


def drum_bar(s, bar, style, fill, intensity=1.0):
	g = intensity
	if style == "rock":
		for k in range(8):
			s.add(bar + k * 0.5, hat(0.7 if k % 2 else 1.0), 0.5 * g)
		for at in (0, 1.5, 2):
			s.add(bar + at, kick(), 0.9 * g)
		for at in (1, 3):
			s.add(bar + at, snare(), 0.8 * g)
	elif style == "march":
		for at in (0, 2):
			s.add(bar + at, kick(), 0.8 * g)
		for at in (1, 3):
			s.add(bar + at, snare(0.9), 0.7 * g)
		for at in (0.75, 2.75, 3.5):
			s.add(bar + at, snare(0.45, 0.12), 0.6 * g)
	elif style == "halftime":
		s.add(bar, kick(0.8), 0.7 * g)
		s.add(bar + 2, snare(0.6), 0.5 * g)
		for k in range(4):
			s.add(bar + k, hat(0.5), 0.35 * g)
	elif style == "taiko":
		for at in (0, 1.5, 2, 3):
			s.add(bar + at, taiko(1.0 if at == 0 else 0.7), 0.8 * g)
		s.add(bar + 3.5, tom(140, 0.6), 0.5 * g)
	elif style == "industrial":
		for at in (0, 0.75, 2, 2.5):
			s.add(bar + at, kick(), 0.9 * g)
		for at in (1, 3):
			s.add(bar + at, snare(), 0.75 * g)
		for k in range(4):
			s.add(bar + k + 0.5, clank(0.6, seed=k), 0.5 * g)
	elif style == "epic":
		s.add(bar, timpani(55, 0.8), 0.9 * g)
		s.add(bar + 2, timpani(55, 0.8), 0.8 * g)
		for at in (0, 2.5):
			s.add(bar + at, kick(), 0.8 * g)
		s.add(bar + 1, snare(0.7), 0.6 * g)
		s.add(bar + 3, snare(0.9), 0.7 * g)
	elif style == "desert":
		for k in range(8):
			s.add(bar + k * 0.5, tambourine(0.8 if k % 2 else 1.0), 0.4 * g)
		for at in (0, 1.5, 2.5):
			s.add(bar + at, tom(110, 0.9), 0.7 * g)
		for at in (1, 3):
			s.add(bar + at, clap(), 0.7 * g)
	elif style == "shanty":
		for at in (0, 2):
			s.add(bar + at, kick(), 0.85 * g)
		for at in (1, 3):
			s.add(bar + at, snare(0.7), 0.6 * g)
		for k in range(4):
			s.add(bar + k + 0.5, tambourine(0.8), 0.4 * g)
	elif style == "four":
		for k in range(4):
			s.add(bar + k, kick(), 0.9 * g)
			s.add(bar + k + 0.5, hat(1.0, open_=True), 0.4 * g)
		for at in (1, 3):
			s.add(bar + at, clap(), 0.7 * g)
	elif style == "swing":
		for at in (0, 1, 1.67, 2, 3, 3.67):
			s.add(bar + at, hat(0.8), 0.45 * g)
		for at in (0, 2.67):
			s.add(bar + at, kick(0.8), 0.7 * g)
		for at in (1, 3):
			s.add(bar + at, snare(0.7), 0.6 * g)
	elif style == "festival":
		for at in (0, 1, 2, 2.5, 3):
			s.add(bar + at, taiko(0.9), 0.7 * g)
		for k in range(8):
			s.add(bar + k * 0.5, tambourine(0.7), 0.3 * g)
	if fill:
		for k, f in enumerate((200, 160, 130, 100)):
			s.add(bar + 3 + k * 0.25, tom(f, 0.9), 0.6 * g)


def extra_bar(s, key, bar, chord, style, i):
	if style == "chains":
		if i % 2 == 0:
			s.add(bar + 3.5, clank(0.5, seed=i), 0.5)
	elif style == "anvils":
		s.add(bar + 1, clank(0.9, seed=1), 0.6)
		s.add(bar + 3, clank(0.9, seed=2), 0.6)
	elif style == "clockwork":
		for k in range(8):
			s.add(bar + k * 0.5, clank(0.25, seed=k % 2), 0.35)
	elif style == "timpani":
		if i % 2 == 1:
			for k in range(4):
				s.add(bar + 3 + k * 0.25, timpani(hz(chord[0] - 12), 0.3, 0.7), 0.5)
	elif style == "bells":
		s.add(bar, bell(hz(chord[0] + 24), 3.5 * s.spb, 0.6), 0.35)
	elif style in ("arp", "koto"):
		inst = harp if style == "koto" else chip
		tones = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[0] + 24]
		for k in range(8):
			s.add(bar + k * 0.5, inst(hz(tones[[0, 1, 2, 3, 2, 1, 2, 3][k]]), 0.45 * s.spb, 0.6), 0.25)


def theme(name):
	t = THEMES[name]
	key = Key(t["key"], t.get("scale", "minor"))
	power = t.get("power", False)
	lead, counter, pad_inst = INSTRUMENTS[t["lead"]], INSTRUMENTS[t["counter"]], INSTRUMENTS[t["pad"]]
	bass_inst = synth_bass if t["drums"] in ("rock", "industrial", "four") else pluck_bass
	a_parts, a_chords = section(key, t["A"], 0, t["sA"])
	b_parts, b_chords = section(key, t["B"], t["bB"], t["sB"])
	form = [("intro", [0, 0, 5, 4]), ("A", a_chords), ("B", b_chords), ("A2", a_chords), ("bridge", [3, 4, 5, 4])]
	s = Song(t["bpm"], sum(len(c) for _, c in form) * 4)
	bar = 0
	pad_root = 48 + (key.tonic % 12 if key.tonic % 12 < 7 else key.tonic % 12 - 12)
	for part, chords in form:
		b0 = bar * 4
		chord_tones = [key.chord(c, pad_root, power) for c in chords]
		bass_line(s, key, b0, chords, t["bass"], bass_inst, power)
		for i, c in enumerate(chord_tones):
			quiet = part == "intro" and i < 2
			drum_bar(s, b0 + i * 4, t["drums"], fill=i == len(chords) - 1, intensity=0.6 if quiet else 1.0)
			extra_bar(s, key, b0 + i * 4, c, t["extra"], i)
			for m in c:
				s.add(b0 + i * 4, pad_inst(hz(m), 3.9 * s.spb, 0.8), (0.55 if part != "intro" else 0.8) / len(c) ** 0.5)
		s.add(b0, crash(), 0.7)
		if part == "intro":
			# The motif's opening as stabs, then a held dominant.
			play(s, b0 + 8, a_parts[0][:4], lead, 0.55, transpose=-12)
			for k in (14, 15, 15.5):
				for m in chord_tones[3]:
					s.add(b0 + k, brass(hz(m + 12), 0.3 * s.spb), 0.25)
		elif part == "A":
			for k, notes in enumerate(a_parts):
				play(s, b0 + k * 8, notes, lead, 0.8)
		elif part == "B":
			for k, notes in enumerate(b_parts):
				play(s, b0 + k * 8, notes, counter, 0.8)
				play(s, b0 + k * 8, notes, lead, 0.35, transpose=-12)
		elif part == "A2":
			for k, notes in enumerate(a_parts):
				play(s, b0 + k * 8, notes, lead, 0.75)
				play(s, b0 + k * 8, notes, counter, 0.45, transpose=12 if t["counter"] not in ("choir", "organ") else -12)
		elif part == "bridge":
			for i, c in enumerate(chord_tones):
				for m in c:
					s.add(b0 + i * 4, brass(hz(m), 3.8 * s.spb, 0.7), 0.35 / len(c) ** 0.5)
			for k in range(16):  # snare build into the loop
				s.add(b0 + 8 + k * 0.5, snare(0.4 + k * 0.035, 0.15), 0.7)
		bar += len(chords)
	return finish(loop(s))


def loop(song, wet=0.18, size=1.6, decay=0.5):
	"""Render with reverb and wrap the echo tail back to the start, so the loop has no gap."""
	L = int(song.length * SR)
	full = reverb(song.buf, size, decay, wet)
	out = full[:L].copy()
	rest = full[L:L * 2]
	out[:len(rest)] += rest
	return out


if __name__ == "__main__":
	names = sys.argv[1:] or list(THEMES)
	for name in names:
		x = theme(name)
		save_ogg(x, os.path.join(OUT, name + ".ogg"), quality=0, rate=32000)
		print(name, round(len(x) / SR, 1), "s")
