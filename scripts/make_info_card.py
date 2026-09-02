#!/usr/bin/env python3
"""
make_info_card.py — hand-authored neofetch-style info card SVG.

Usage:
    python scripts/make_info_card.py            # writes info-card.svg (animated)
    STATIC=1 python scripts/make_info_card.py    # writes a frozen frame (Quick Look preview)

Edit the CONTENT dict below to change what shows up on the card.
"""
import os

TITLE = "Dmg0920@github"
UNDERLINE_CHAR = "-"

# Edit these to taste — this is the "story numbers can't tell" part.
CONTENT = [
    ("Now", "Building things that click"),
    ("Prev", "—"),
    ("Stack", "Python · TypeScript · Go"),
    ("Highlights", "Open source · Side projects · Automation"),
]

KEY_COLOR = "#39d353"     # neon green, matches heatmap top end
VALUE_COLOR = "#c9d1d9"
TITLE_COLOR = "#58a6ff"
BG_COLOR = "transparent"
FONT_FAMILY = "'SFMono-Regular','Consolas','Liberation Mono','Menlo',monospace"

LINE_HEIGHT = 26
FONT_SIZE = 15
PAD_X = 20
PAD_TOP = 24
CARD_WIDTH = 490
STAGGER_S = 0.12
FADE_DUR_S = 0.4


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static: bool) -> str:
    lines = [("__title__", TITLE)]
    lines.append(("__rule__", UNDERLINE_CHAR * len(TITLE)))
    for k, v in CONTENT:
        lines.append((k, v))

    height = PAD_TOP + len(lines) * LINE_HEIGHT + 16

    body = []
    for i, (key, value) in enumerate(lines):
        y = PAD_TOP + i * LINE_HEIGHT
        delay = i * STAGGER_S

        if key == "__title__":
            text = f'<text x="{PAD_X}" y="{y}" fill="{TITLE_COLOR}" font-weight="bold">{escape_xml(value)}</text>'
        elif key == "__rule__":
            text = f'<text x="{PAD_X}" y="{y}" fill="{TITLE_COLOR}">{escape_xml(value)}</text>'
        else:
            text = (
                f'<tspan fill="{KEY_COLOR}" font-weight="bold">{escape_xml(key)}</tspan>'
                f'<tspan fill="{VALUE_COLOR}">: {escape_xml(value)}</tspan>'
            )
            text = f'<text x="{PAD_X}" y="{y}">{text}</text>'

        if static:
            body.append(f"  {text}")
        else:
            body.append(
                f'  <g opacity="0" transform="translate(-8,0)">\n'
                f'    {text}\n'
                f'    <animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.2f}s" dur="{FADE_DUR_S:.2f}s" fill="freeze"/>\n'
                f'    <animateTransform attributeName="transform" type="translate" '
                f'from="-8,0" to="0,0" begin="{delay:.2f}s" dur="{FADE_DUR_S:.2f}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1"/>\n'
                f'  </g>'
            )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_WIDTH} {height}"
     width="{CARD_WIDTH}" height="{height}" font-family="{FONT_FAMILY}"
     font-size="{FONT_SIZE}" style="background:{BG_COLOR}">
{chr(10).join(body)}
</svg>
'''
    return svg


def main():
    static = os.environ.get("STATIC") == "1"
    out_name = "info-card-static.svg" if static else "info-card.svg"
    svg = build_svg(static)
    with open(out_name, "w") as f:
        f.write(svg)
    print(f"wrote {out_name}")


if __name__ == "__main__":
    main()
