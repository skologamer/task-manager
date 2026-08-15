#!/usr/bin/env python3
"""Generate PNG app icons from the project's SVG icon using cairosvg.

Run from project root after installing `cairosvg` (it's in requirements.txt).
"""
import os
from cairosvg import svg2png

SRC = os.path.join('static', 'icons', 'icon-512.svg')
OUTDIR = os.path.join('store', 'assets')
SIZES = [48, 72, 96, 144, 192, 256, 384, 512]

os.makedirs(OUTDIR, exist_ok=True)
if not os.path.exists(SRC):
    raise SystemExit(f"Source SVG not found: {SRC}")

for s in SIZES:
    out = os.path.join(OUTDIR, f'icon-{s}.png')
    svg2png(url=SRC, write_to=out, output_width=s, output_height=s)
    print('Wrote', out)

print('All icons generated to', OUTDIR)
