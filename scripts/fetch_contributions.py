#!/usr/bin/env python3
"""
fetch_contributions.py — scrape a public GitHub contribution calendar.

No GraphQL API, no personal access token. GitHub serves the calendar
as public HTML at https://github.com/users/<username>/contributions
(the same fragment the profile page itself uses).

Usage:
    python scripts/fetch_contributions.py [username]

If no username is given, reads GITHUB_USERNAME env var, falling back
to the default below.

Output: data/contributions.json with raw days plus derived stats
(current streak, longest streak, best day, monthly totals).
"""
import datetime
import json
import os
import sys

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "Dmg0920"
URL_TMPL = "https://github.com/users/{username}/contributions"


def fetch_html(username: str) -> str:
    resp = requests.get(
        URL_TMPL.format(username=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as a <td> with data-date + data-level (newer
    # markup) or a <rect> with data-date + data-count (older markup).
    # Handle both.
    cells = soup.select("td.ContributionCalendar-day, td[data-date]")
    if cells:
        for cell in cells:
            date = cell.get("data-date")
            if not date:
                continue
            level = cell.get("data-level")
            tooltip_id = cell.get("id")
            count = 0
            tooltip = None
            if tooltip_id:
                tooltip = soup.find(attrs={"for": tooltip_id})
            if tooltip is None:
                # fallback: aria-label on the cell itself
                label = cell.get("aria-label") or cell.get("title") or ""
            else:
                label = tooltip.get_text(strip=True)
            count = _extract_count(label)
            days.append(
                {
                    "date": date,
                    "count": count,
                    "level": int(level) if level is not None else _level_from_count(count),
                }
            )
    else:
        rects = soup.select("rect[data-date]")
        for rect in rects:
            date = rect.get("data-date")
            count = int(rect.get("data-count", 0))
            level = rect.get("data-level")
            days.append(
                {
                    "date": date,
                    "count": count,
                    "level": int(level) if level is not None else _level_from_count(count),
                }
            )

    days.sort(key=lambda d: d["date"])
    return days


def _extract_count(label: str) -> int:
    label = label.lower()
    if "no contributions" in label:
        return 0
    # e.g. "12 contributions on January 5th."
    parts = label.split()
    for p in parts:
        if p.isdigit():
            return int(p)
    return 0


def _level_from_count(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    total = sum(d["count"] for d in days)

    # Streaks
    longest = current = 0
    best_run_end = None
    run_start = None
    today = datetime.date.today()

    streak = 0
    max_streak = 0
    for d in days:
        if d["count"] > 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    longest = max_streak

    # current streak: walk backwards from the most recent day
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"])

    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": monthly,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }


def main():
    username = (
        sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME)
    )
    html = fetch_html(username)
    days = parse_days(html)
    stats = compute_stats(days)

    out = {
        "username": username,
        "days": days,
        "stats": stats,
    }

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "contributions.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"wrote {out_path} ({len(days)} days, {stats.get('total_contributions', 0)} contributions)")


if __name__ == "__main__":
    main()
