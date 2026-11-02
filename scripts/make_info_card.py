#!/usr/bin/env python3
"""Neofetch-style info card. Edit CARD below, then run:

    python scripts/make_info_card.py           # animated
    STATIC=1 python scripts/make_info_card.py  # frozen frame for previews
"""
import os
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

USER = "kira-vik"
HOST = "github"

# (key, value) - edit freely. Long values are word-wrapped automatically.
CARD = [
    ("Name", "Weke Victor"),
    ("Now", "Java Spring Boot APIs, ERPNext custom modules, Python analytics & reporting"),
    ("Looking", "Help scaling ETL pipelines, pipeline performance, cloud-native analytics"),
    ("Learning", "Advanced ETL, cloud analytics platforms, Kafka-style streaming, SQL tuning"),
    ("Stack", "Java, Python, SQL, Spring Boot, Django, FastAPI, Flask, Postgres, MySQL, Docker"),
    ("Tools", "Power BI, Pandas, Plotly, Git, Postman"),
    ("Ask me", "Python analytics, ETL design, ERPNext, Spring Boot, Power BI, messy-data cleanup"),
    ("Contact", "linkedin.com/in/victor-weke-3a7ba22a5"),
]

W = 490
FS = 12.5
CW = 7.5           # approx monospace char width at FS
KEY_X, VAL_X = 22, 112
WRAP = int((W - VAL_X - 18) / CW)
LINE = 19
BG, BORDER = "#0d1117", "#30363d"
C_USER, C_KEY, C_VAL, C_DIM = "#39d353", "#58a6ff", "#c9d1d9", "#6e7681"
SWATCH = ["#f85149", "#d29922", "#39d353", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]


def main():
    static = os.environ.get("STATIC") == "1"
    y = 78
    els = []
    idx = 0

    def delay():
        nonlocal idx
        d = 0.35 + idx * 0.16
        idx += 1
        return "" if static else f' class="l" style="animation-delay:{d:.2f}s"'

    title = f"{USER}@{HOST}"
    els.append(f'<text x="{KEY_X}" y="{y}" font-weight="700" fill="{C_USER}"{delay()}>{escape(title)}</text>')
    y += 17
    els.append(f'<text x="{KEY_X}" y="{y}" fill="{C_DIM}"{delay()}>{"-" * len(title)}</text>')
    y += 24

    for key, val in CARD:
        wrapped = textwrap.wrap(val, WRAP) or [""]
        d = delay()
        els.append(f'<text x="{KEY_X}" y="{y}" font-weight="700" fill="{C_KEY}"{d}>{escape(key)}</text>')
        for seg in wrapped:
            els.append(f'<text x="{VAL_X}" y="{y}" fill="{C_VAL}"{d}>{escape(seg)}</text>')
            y += LINE
        y += 3

    y += 6
    sw = [f'<rect x="{KEY_X + i * 26}" y="{y}" width="22" height="12" rx="2" fill="{c}"/>'
          for i, c in enumerate(SWATCH)]
    els.append(f'<g{delay()}>' + "".join(sw) + "</g>")
    H = y + 12 + 22

    style = "" if static else (
        "<style>.l{opacity:0;animation:in .5s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}</style>")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
{style}
<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>
<path d="M0 10a10 10 0 0 1 10-10h{W-20}a10 10 0 0 1 10 10v26H0z" fill="#161b22"/>
<circle cx="20" cy="18" r="5" fill="#f85149"/><circle cx="38" cy="18" r="5" fill="#d29922"/><circle cx="56" cy="18" r="5" fill="#39d353"/>
<text x="{W/2}" y="22" text-anchor="middle" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="11" fill="{C_DIM}">neofetch</text>
<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}">
{chr(10).join(els)}
</g>
</svg>'''
    out = ROOT / "info-card.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({W}x{H})")


if __name__ == "__main__":
    main()
