#!/usr/bin/env python3
"""Prep a photo for ASCII conversion.

1. Remove the background (rembg)
2. Crop to the subject
3. Boost local contrast (CLAHE) so a flat-lit face gets highlights/shadows
4. Composite onto pure white (white -> blank end of the ASCII ramp)

Usage: python scripts/prep_photo.py my-photo.jpg [--out source-prepped.png] [--no-rembg]
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--out", default=str(ROOT / "source-prepped.png"))
    ap.add_argument("--no-rembg", action="store_true", help="skip background removal")
    ap.add_argument("--clip", type=float, default=3.0, help="CLAHE clip limit (higher = punchier)")
    args = ap.parse_args()

    img = Image.open(args.photo).convert("RGBA")

    if not args.no_rembg:
        from rembg import remove  # heavy import, only when needed
        img = remove(img)  # RGBA, background transparent

    alpha = np.array(img.split()[-1])

    # crop to subject with a little padding
    ys, xs = np.where(alpha > 20)
    if len(xs) and not args.no_rembg:
        pad = int(0.06 * max(img.size))
        box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0),
               min(xs.max() + pad, img.width), min(ys.max() + pad, img.height))
        img = img.crop(box)
        alpha = np.array(img.split()[-1])

    # composite on white
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.alpha_composite(img)
    gray = cv2.cvtColor(np.array(white.convert("RGB")), cv2.COLOR_RGB2GRAY)

    # local contrast
    clahe = cv2.createCLAHE(clipLimit=args.clip, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # force the (removed) background back to pure white
    if not args.no_rembg:
        gray[alpha < 20] = 255

    Image.fromarray(gray).save(args.out)
    print(f"wrote {args.out} ({gray.shape[1]}x{gray.shape[0]})")


if __name__ == "__main__":
    main()
