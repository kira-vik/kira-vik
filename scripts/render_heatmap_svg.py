#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 contribution heatmap SVG.

Cells slide in diagonally once (CSS keyframes), then freeze.
Env: STATIC=1 -> no animation (for previews)
"""
import json
import os
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL, GAP = 12, 3
PITCH = CELL + GAP
LEFT, TOP = 44, 62
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def level_of(day, neon_cut):
    lv = min(day["level"], 4)
    if lv == 4 and day["count"] >= neon_cut:
        return 5
    return lv


def main():
    static = os.environ.get("STATIC") == "1"
    data = json.loads(DATA.read_text())
    days = data["days"]

    # top ~10% of active days get the neon level
    active = sorted(d["count"] for d in days if d["count"] > 0)
    neon_cut = active[int(len(active) * 0.9)] if len(active) >= 10 else 10**9

    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # weeks start on Sunday
    ncols = (len(days) - 1 + offset) // 7 + 1

    W = LEFT + ncols * PITCH + 20
    grid_bottom = TOP + 7 * PITCH
    H = grid_bottom + 58

    cells, month_labels = [], []
    last_label_col = -10
    seen_month = None
    for i, d in enumerate(days):
        pos = i + offset
        col, row = divmod(pos, 7)
        x, y = LEFT + col * PITCH, TOP + row * PITCH
        lv = level_of(d, neon_cut)
        delay = (col + row) * 0.018
        cls = "" if static else f' class="c" style="animation-delay:{delay:.3f}s"'
        cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[lv]}"{cls}/>')

        if row == 0 or i == 0:  # first cell of a column decides the month label
            m = int(d["date"][5:7])
            if m != seen_month:
                if col - last_label_col >= 3:
                    month_labels.append(f'<text x="{x}" y="{TOP - 10}">{MONTHS[m - 1]}</text>')
                    last_label_col = col
                seen_month = m

    day_labels = "".join(
        f'<text x="{LEFT - 10}" y="{TOP + r * PITCH + 10}" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))

    # legend (bottom right)
    lx = W - 20 - (6 * PITCH + 70)
    ly = grid_bottom + 22
    legend = f'<text x="{lx}" y="{ly + 10}">Less</text>'
    for i, c in enumerate(PALETTE):
        legend += f'<rect x="{lx + 32 + i * PITCH}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>'
    legend += f'<text x="{lx + 32 + 6 * PITCH + 4}" y="{ly + 10}">More</text>'

    best = data["best_day"]
    footer1 = f'{data["total"]:,} contributions in the last year'
    footer2 = (f'current streak {data["current_streak"]}d  |  longest {data["longest_streak"]}d'
               f'  |  best day {best["count"]} ({best["date"]})')

    style = "" if static else (
        "<style>.c{opacity:0;animation:drop .5s ease-out forwards}"
        "@keyframes drop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}</style>")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
{style}
<rect width="100%" height="100%" rx="10" fill="#0d1117" stroke="#30363d"/>
<g font-family="{FONT}" font-size="11" fill="#8b949e">
<text x="{LEFT}" y="24" font-size="13" font-weight="700" fill="#39d353">{escape(data["username"])}@github</text>
<text x="{LEFT + 128}" y="24" font-size="13" fill="#6e7681">~ contributions --last-year</text>
{"".join(month_labels)}
{day_labels}
</g>
{"".join(cells)}
<g font-family="{FONT}" font-size="11" fill="#8b949e">
<text x="{LEFT}" y="{grid_bottom + 28}" font-size="12" fill="#c9d1d9">{escape(footer1)}</text>
<text x="{LEFT}" y="{grid_bottom + 46}">{escape(footer2)}</text>
{legend}
</g>
</svg>'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({W}x{H}, {ncols} weeks, {OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
