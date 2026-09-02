#!/usr/bin/env python3
"""
render_heatmap_svg.py — render data/contributions.json as an animated
53-week x 7-day contribution heatmap SVG.

Usage:
    python scripts/render_heatmap_svg.py [-i data/contributions.json] [-o contrib-heatmap.svg]

Design:
  - Classic GitHub-style grid: 53 columns (weeks) x 7 rows (days).
  - Rounded boxes colored by contribution level with a GitHub-ish
    green ramp (level 5 is a neon top end, brighter than GitHub's own).
  - Reveals once with a diagonal, line-after-line slide-down (CSS
    keyframes that play on load then freeze — no looping).
  - Less -> More legend plus a stats footer.
"""
import argparse
import datetime
import json

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none        lvl1        lvl2        lvl3        lvl4        neon top (lvl5, synthetic)

BOX_SIZE = 11
BOX_GAP = 3
CELL = BOX_SIZE + BOX_GAP
LEFT_MARGIN = 30       # room for day-of-week labels
TOP_MARGIN = 20         # room for month labels
LEGEND_HEIGHT = 20
FOOTER_HEIGHT = 24
WEEKS = 53
DAYS = 7

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Monday=0 .. Sunday=6, sparse labels like GitHub


def level_with_top_end(level: int, count: int) -> int:
    """Optionally push exceptionally high days to a synthetic 'neon' level 5."""
    if level >= 4 and count >= 15:
        return 5
    return min(level, 4)


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Bucket days into 53 weeks x 7 days (Mon-Sun), most recent last."""
    if not days:
        return []

    parsed = []
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        parsed.append({**d, "_date": date})
    parsed.sort(key=lambda d: d["_date"])

    last_date = parsed[-1]["_date"]
    # End on the most recent Sunday-aligned week end (GitHub weeks run Sun-Sat
    # in the API but we lay out Mon-Sun here for readability).
    end = last_date
    start = end - datetime.timedelta(weeks=WEEKS - 1)
    # Align start to a Monday
    start = start - datetime.timedelta(days=start.weekday())

    by_date = {d["_date"]: d for d in parsed}

    weeks = []
    cursor = start
    for _ in range(WEEKS):
        week = []
        for _ in range(DAYS):
            week.append(by_date.get(cursor))
            cursor += datetime.timedelta(days=1)
        weeks.append(week)
    return weeks


def build_svg(data: dict) -> str:
    days = data.get("days", [])
    stats = data.get("stats", {})
    weeks = build_weeks(days)

    grid_width = WEEKS * CELL
    grid_height = DAYS * CELL
    width = LEFT_MARGIN + grid_width + 10
    height = TOP_MARGIN + grid_height + LEGEND_HEIGHT + FOOTER_HEIGHT + 10

    boxes = []
    month_labels = []
    seen_months = set()

    total_cells = WEEKS * DAYS
    for w, week in enumerate(weeks):
        for d, cell in enumerate(week):
            x = LEFT_MARGIN + w * CELL
            y = TOP_MARGIN + d * CELL

            if cell is None:
                color = PALETTE[0]
                count = 0
            else:
                lvl = level_with_top_end(cell.get("level", 0), cell.get("count", 0))
                color = PALETTE[lvl]
                count = cell.get("count", 0)
                date = cell["_date"]
                month_key = (date.year, date.month)
                if date.day <= 7 and month_key not in seen_months:
                    seen_months.add(month_key)
                    month_labels.append((x, MONTH_NAMES[date.month - 1]))

            # diagonal stagger: order by (week + day) so it reveals top-left
            # to bottom-right in a diagonal sweep
            order = w + d
            delay = order * 0.008
            title = f"{count} contribution{'s' if count != 1 else ''}"
            if cell is not None:
                title += f" on {cell['_date'].isoformat()}"

            boxes.append(
                f'    <rect class="box" x="{x}" y="{y - 6}" width="{BOX_SIZE}" height="{BOX_SIZE}" '
                f'rx="2" ry="2" fill="{color}" style="animation-delay:{delay:.3f}s">'
                f'<title>{title}</title></rect>'
            )

    day_label_svgs = []
    for idx, label in DAY_LABELS.items():
        y = TOP_MARGIN + idx * CELL + BOX_SIZE
        day_label_svgs.append(
            f'  <text x="0" y="{y}" font-size="9" fill="#8b949e">{label}</text>'
        )

    month_label_svgs = []
    for x, label in month_labels:
        month_label_svgs.append(
            f'  <text x="{x}" y="{TOP_MARGIN - 6}" font-size="9" fill="#8b949e">{label}</text>'
        )

    legend_y = TOP_MARGIN + grid_height + 16
    legend_x = LEFT_MARGIN + grid_width - (len(PALETTE) * (BOX_SIZE + 4) + 40)
    legend_boxes = []
    legend_boxes.append(f'  <text x="{legend_x - 34}" y="{legend_y + 9}" font-size="9" fill="#8b949e">Less</text>')
    for i, color in enumerate(PALETTE):
        bx = legend_x + i * (BOX_SIZE + 4)
        legend_boxes.append(
            f'  <rect x="{bx}" y="{legend_y}" width="{BOX_SIZE}" height="{BOX_SIZE}" rx="2" ry="2" fill="{color}"/>'
        )
    legend_boxes.append(
        f'  <text x="{legend_x + len(PALETTE) * (BOX_SIZE + 4) + 4}" y="{legend_y + 9}" font-size="9" fill="#8b949e">More</text>'
    )

    total = stats.get("total_contributions", sum(c["count"] for c in days) if days else 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_y = legend_y + LEGEND_HEIGHT + 4
    footer = (
        f'  <text x="{LEFT_MARGIN}" y="{footer_y}" font-size="10" fill="#8b949e">'
        f'{total:,} contributions in the last year &#183; current streak {streak}d &#183; longest {longest}d</text>'
    )

    max_delay = total_cells * 0.008
    box_anim_dur = 0.35

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" font-family="'SFMono-Regular','Consolas','Liberation Mono','Menlo',monospace"
     style="background:transparent">
  <style>
    .box {{
      opacity: 0;
      transform: translate(-6px, -8px);
      animation-name: reveal;
      animation-duration: {box_anim_dur}s;
      animation-timing-function: cubic-bezier(0.3,0,0.2,1);
      animation-fill-mode: forwards;
    }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translate(-6px, -8px); }}
      to   {{ opacity: 1; transform: translate(0, 0); }}
    }}
  </style>
{chr(10).join(month_label_svgs)}
{chr(10).join(day_label_svgs)}
  <g>
{chr(10).join(boxes)}
  </g>
{chr(10).join(legend_boxes)}
{footer}
</svg>
'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="data/contributions.json")
    parser.add_argument("-o", "--output", default="contrib-heatmap.svg")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    svg = build_svg(data)
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
