#!/usr/bin/env python3
"""
make_ascii_svg.py — convert source-prepped.png into a self-typing,
monochrome ASCII-art SVG.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [-o avi-ascii.svg]

Design:
  - Downsample the prepped image to a character grid (~100 wide).
  - Map each cell's average brightness to a glyph from a density ramp
    (bright/sparse -> dark/dense). A leading space in the ramp means
    background pixels render as nothing.
  - Monochrome: a single light-gray fill. No per-character color.
  - Each row is wrapped in a clip-path that wipes left-to-right, with
    rows staggered top-to-bottom, so the portrait "types" itself in
    once and freezes (no looping).
"""
import argparse
import os
import sys

from PIL import Image

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

GRID_COLS = 100
CHAR_W = 6.2
CHAR_H = 11.5
FONT_SIZE = 12
FILL_COLOR = "#c9d1d9"
BG_COLOR = "transparent"
ROW_STAGGER_S = 0.045  # seconds between each row starting its wipe
ROW_DURATION_S = 0.35  # how long each row's wipe takes


def image_to_grid(img: Image.Image, cols: int) -> list[str]:
    w, h = img.size
    # Character cells are taller than wide; correct aspect ratio so the
    # portrait isn't squashed vertically.
    aspect_correction = 0.55
    rows = max(1, round(cols * (h / w) * aspect_correction))
    small = img.convert("L").resize((cols, rows), Image.LANCZOS)
    pixels = small.load()

    ramp_len = len(RAMP)
    lines = []
    for y in range(rows):
        line_chars = []
        for x in range(cols):
            brightness = pixels[x, y]  # 0=black .. 255=white
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines: list[str]) -> str:
    cols = max((len(l) for l in lines), default=0)
    rows = len(lines)
    width = cols * CHAR_W + 20
    height = rows * CHAR_H + 20

    svg_rows = []
    for i, line in enumerate(lines):
        row_width = len(line) * CHAR_W
        start = i * ROW_STAGGER_S
        end = start + ROW_DURATION_S
        clip_id = f"clip{i}"
        text_escaped = escape_xml(line)
        y = 10 + (i + 1) * CHAR_H - 2

        svg_rows.append(f'''
    <clipPath id="{clip_id}">
      <rect x="10" y="{10 + i * CHAR_H}" width="0" height="{CHAR_H}">
        <animate attributeName="width" from="0" to="{row_width}"
                 begin="{start:.3f}s" dur="{ROW_DURATION_S:.3f}s"
                 fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1"/>
      </rect>
    </clipPath>''')

    text_elements = []
    for i, line in enumerate(lines):
        clip_id = f"clip{i}"
        text_escaped = escape_xml(line)
        y = 10 + (i + 1) * CHAR_H - 2
        text_elements.append(
            f'    <text x="10" y="{y:.1f}" clip-path="url(#{clip_id})">{text_escaped}</text>'
        )

    total_duration = rows * ROW_STAGGER_S + ROW_DURATION_S

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}"
     width="{width:.0f}" height="{height:.0f}" font-family="'SFMono-Regular','Consolas','Liberation Mono','Menlo',monospace"
     font-size="{FONT_SIZE}" style="background:{BG_COLOR}">
  <defs>{"".join(svg_rows)}
  </defs>
  <style>
    text {{ fill: {FILL_COLOR}; white-space: pre; }}
  </style>
  <g>
{chr(10).join(text_elements)}
  </g>
</svg>
'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="source-prepped.png")
    parser.add_argument("-o", "--output", default="avi-ascii.svg")
    parser.add_argument("--cols", type=int, default=GRID_COLS)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(
            f"error: {args.input} not found. Run prep_photo.py first, "
            "or pass a path to an already-prepped grayscale image.",
            file=sys.stderr,
        )
        sys.exit(1)

    img = Image.open(args.input)
    lines = image_to_grid(img, args.cols)
    svg = build_svg(lines)

    with open(args.output, "w") as f:
        f.write(svg)
    print(f"wrote {args.output} ({len(lines)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()
