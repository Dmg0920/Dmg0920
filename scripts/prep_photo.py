#!/usr/bin/env python3
"""
prep_photo.py — prepare a source photo for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg

Pipeline:
  1. Remove the background with rembg so only the subject remains.
  2. Boost local contrast with CLAHE (contrast-limited adaptive
     histogram equalization) so a flatly-lit face gets real
     highlights/shadows instead of converting to a dark blob.
  3. Composite onto pure white so the background maps to the blank
     end of the ASCII ramp (white -> space).

Output: source-prepped.png (grayscale, next to the input file).
"""
import sys
import os

import numpy as np
import cv2
from PIL import Image


def prep_photo(input_path: str) -> str:
    from rembg import remove  # imported lazily; heavy dependency

    with open(input_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with transparent background.
    result_bytes = remove(input_bytes)
    rgba = Image.open(__import__("io").BytesIO(result_bytes)).convert("RGBA")

    # 2. Composite onto pure white.
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # 3. Convert to grayscale and boost local contrast with CLAHE.
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-flatten any near-white background that CLAHE darkened slightly,
    # so it still maps cleanly to blank space later.
    _, mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
    contrasted = np.where(mask == 255, 255, contrasted).astype(np.uint8)

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(input_path)) or ".",
        "source-prepped.png",
    )
    Image.fromarray(contrasted).save(out_path)
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python scripts/prep_photo.py source-photo.jpg", file=sys.stderr)
        sys.exit(1)
    prep_photo(sys.argv[1])
