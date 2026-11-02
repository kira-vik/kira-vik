#!/usr/bin/env python3
"""Turn source-prepped.png into a monochrome, self-typing ASCII SVG.

Each row wipes in left-to-right (SMIL) with a block cursor riding the edge,
staggered top to bottom. Plays once, then freezes.

Usage: python scripts/make_ascii_svg.py [--cols 100] [--in source-prepped.png]
Env:   STATIC=1 -> no animation (for local previews)
"""
import argparse
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
FG = "#c9d1d9"
BG = "#0d1117"
CW, LH, FS = 6.0, 11.0, 10  # char width, line height, font size
PAD = 14


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=str(ROOT / "source-prepped.png"))
    ap.add_argument("--out", default=str(ROOT / "ascii-portrait.svg"))
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--gamma", type=float, default=1.0, help=">1 darkens midtones")
    args = ap.parse_args()
    static = os.environ.get("STATIC") == "1"

    if not Path(args.src).exists():
        raise SystemExit(f"{args.src} not found - run scripts/prep_photo.py first")

    img = Image.open(args.src).convert("L")
    rows = max(1, round(img.height / img.width * args.cols * (CW / LH)))
    img = img.resize((args.cols, rows), Image.LANCZOS)
    px = np.asarray(img, dtype=np.float32) / 255.0
    px = px ** args.gamma

    lines = []
    for r in range(rows):
        line = "".join(RAMP[min(int((1 - v) * len(RAMP)), len(RAMP) - 1)] for v in px[r])
        lines.append(line)

    W = args.cols * CW + PAD * 2
    H = rows * LH + PAD * 2
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="#30363d"/>',
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}" fill="{FG}">',
    ]
    defs = []
    body = []
    n = len(lines)
    row_dur = 0.55
    stagger = min(0.045, 3.2 / max(n, 1))  # whole portrait prints in ~3s

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        lead = len(stripped) - len(stripped.lstrip())
        text = stripped.lstrip()
        if not text:
            continue
        x = PAD + lead * CW
        y = PAD + i * LH + FS
        w = len(text) * CW
        begin = 0.3 + i * stagger
        esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        t = (f'<text x="{x:.1f}" y="{y:.1f}" textLength="{w:.1f}" lengthAdjust="spacing" '
             f'xml:space="preserve"')
        if static:
            body.append(f'{t}>{esc}</text>')
            continue
        cid = f"c{i}"
        defs.append(
            f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{PAD + i * LH:.1f}" width="0" height="{LH:.1f}">'
            f'<animate attributeName="width" from="0" to="{w + CW:.1f}" begin="{begin:.2f}s" '
            f'dur="{row_dur}s" fill="freeze"/></rect></clipPath>')
        body.append(f'{t} clip-path="url(#{cid})">{esc}</text>')
        body.append(
            f'<rect x="{x:.1f}" y="{PAD + i * LH + 1:.1f}" width="{CW:.1f}" height="{LH - 2:.1f}" '
            f'fill="#39d353" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{x:.1f}" to="{x + w:.1f}" begin="{begin:.2f}s" '
            f'dur="{row_dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + row_dur:.2f}s"/></rect>')

    if defs:
        out.insert(1, "<defs>" + "".join(defs) + "</defs>")
    out += body + ["</g>", "</svg>"]
    Path(args.out).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {args.out} ({args.cols}x{rows} chars, {Path(args.out).stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
