"""Builds the sea bosses' flagships: python3 tools/ships/build_flagships.py [ids...] [--previews=DIR] [--no-preview]

With no ids it builds all of them. See seakit.py for where the files go and the rules.
"""
import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seakit  # noqa: E402

FLAGSHIPS = ["widowmaker", "tithe_cathedral", "cinderwake"]

previews = os.path.join(seakit.REPO, "build", "ship_previews")
names = []
for a in sys.argv[1:]:
    if a.startswith("--previews="):
        previews = a[len("--previews="):]
    elif not a.startswith("--"):
        names.append(a)
names = names or FLAGSHIPS
if "--no-preview" not in sys.argv:
    seakit.install_preview_colours()
for name in names:
    t = time.time()
    ship = importlib.import_module(name).build()
    ship.save(seakit.RES)
    if "--no-preview" not in sys.argv:
        outs = ship.preview(previews, cuts=getattr(sys.modules[name], "CUTS", ()))
        print("  previews:", ", ".join(outs))
    print(f"  {time.time() - t:.1f}s")
