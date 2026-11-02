#!/usr/bin/env python3
"""Render data/contributions.json as a full-width green bar chart of contributions per month.

Shows the last 12 calendar months (the current month is in progress). Bars grow up once
(SMIL), then freeze. Width matches the heatmap so the README edges line up.
Env: STATIC=1 -> no animation (for previews)
"""
import json
import os
from collections import OrderedDict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "monthly-commits.svg"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
W = 860
LEFT, RIGHT, TOP, PLOT_H = 56, 24, 58, 130
BASE = TOP + PLOT_H
BAR_W = 40
GREEN, NEON, EMPTY = "#26a641", "#69f0a0", "#161b22"


def nice_top(m: int) -> int:
    if m <= 4:
        return 4
    unit = 10 ** (len(str(m)) - 1) // 2 or 1   # e.g. 873 -> 50, 60 -> 5
    unit = max(unit, 2)
    top = -(-m // unit) * unit
    return top + (top % 2)                       # keep even so the midline is a whole number


def main():
    static = os.environ.get("STATIC") == "1"
    data = json.loads(DATA.read_text())

    months = OrderedDict()
    for d in data["days"]:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    items = list(months.items())[-12:]
    vals = [v for _, v in items]
    top = nice_top(max(vals) if vals else 4)
    peak = max(vals) if vals else 0

    slot = (W - LEFT - RIGHT) / len(items)
    els, grid = [], []

    for frac in (0, 0.5, 1):
        y = BASE - PLOT_H * frac
        label = f"{round(top * frac):,}"
        stroke = "#30363d" if frac == 0 else "#21262d"
        dash = "" if frac == 0 else ' stroke-dasharray="3 4"'
        grid.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{W - RIGHT}" y2="{y:.1f}" stroke="{stroke}"{dash}/>')
        grid.append(f'<text x="{LEFT - 8}" y="{y + 4:.1f}" text-anchor="end">{label}</text>')

    for i, (ym, v) in enumerate(items):
        year, mo = int(ym[:4]), int(ym[5:7])
        cx = LEFT + slot * (i + 0.5)
        x = cx - BAR_W / 2
        h = max(PLOT_H * v / top, 2)
        y = BASE - h
        color = NEON if (v == peak and v > 0) else (GREEN if v > 0 else EMPTY)
        begin = 0.25 + i * 0.09

        if static:
            els.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{BAR_W}" height="{h:.1f}" rx="4" fill="{color}"/>')
            els.append(f'<text x="{cx:.1f}" y="{y - 7:.1f}" text-anchor="middle" fill="#c9d1d9">{v:,}</text>')
        else:
            els.append(
                f'<rect x="{x:.1f}" y="{BASE}" width="{BAR_W}" height="0" rx="4" fill="{color}">'
                f'<animate attributeName="height" from="0" to="{h:.1f}" begin="{begin:.2f}s" dur="0.6s" fill="freeze"/>'
                f'<animate attributeName="y" from="{BASE}" to="{y:.1f}" begin="{begin:.2f}s" dur="0.6s" fill="freeze"/></rect>')
            els.append(
                f'<text x="{cx:.1f}" y="{y - 7:.1f}" text-anchor="middle" fill="#c9d1d9" opacity="0">{v:,}'
                f'<set attributeName="opacity" to="1" begin="{begin + 0.6:.2f}s"/></text>')

        els.append(f'<text x="{cx:.1f}" y="{BASE + 18}" text-anchor="middle">{MONTHS[mo - 1]}</text>')
        if i == 0 or mo == 1:
            els.append(f'<text x="{cx:.1f}" y="{BASE + 32}" text-anchor="middle" fill="#6e7681" font-size="10">{year}</text>')

    H = BASE + 46
    total = sum(vals)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<rect width="100%" height="100%" rx="10" fill="#0d1117" stroke="#30363d"/>
<g font-family="{FONT}" font-size="11" fill="#8b949e">
<text x="{LEFT}" y="26" font-size="13" font-weight="700" fill="#39d353">{escape(data["username"])}@github</text>
<text x="{LEFT + 128}" y="26" font-size="13" fill="#6e7681">~ contributions --per-month</text>
<text x="{W - RIGHT}" y="26" text-anchor="end">{total:,} in the last 12 months</text>
{"".join(grid)}
{"".join(els)}
</g>
</svg>'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({W}x{H}, {len(items)} months, peak {peak:,})")


if __name__ == "__main__":
    main()
