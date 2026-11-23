"""Depth map generator for 2D illustrations using Depth Anything V2 (pixel-aligned; white = near, black = far).

Optional dependencies (only needed if generating depth maps for Blender relief or lib/depth3d.js):
  pip install torch transformers

Usage:
  python -X utf8 scripts/vision/depth.py <image.png> <out_depth.png> [--bits 8|16] [--model small|base] [--soften]

Flags:
  --bits 16   Recommended for Blender depth_relief.py (smooth 16-bit displacement without stair-stepping).
  --soften    Apply median-7 + Gaussian-5 softening so Blender relief silhouettes never tear like a rubber sheet.
  --model     small (fast, ~98 MB download on first run) or base (~390 MB, finer detail).

Set HF_HOME to customize the HuggingFace cache directory; set HF_HUB_OFFLINE=1 to force offline cache mode.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import torch
    from PIL import Image, ImageFilter
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
except ImportError as e:
    sys.exit(f"depth.py requires torch, transformers, and Pillow ({e}). Install with: pip install torch transformers Pillow")

MODELS = {
    "small": "depth-anything/Depth-Anything-V2-Small-hf",
    "base": "depth-anything/Depth-Anything-V2-Base-hf",
}


def main():
    ap = argparse.ArgumentParser(description="Generate pixel-aligned depth map with Depth Anything V2")
    ap.add_argument("image")
    ap.add_argument("out")
    ap.add_argument("--bits", type=int, default=16, choices=(8, 16))
    ap.add_argument("--model", default="small", choices=tuple(MODELS))
    ap.add_argument("--soften", action="store_true", help="Median-7 + Gaussian-5 softening for tear-free Blender relief")
    a = ap.parse_args()

    t0 = time.time()
    img = Image.open(a.image).convert("RGB")
    proc = AutoImageProcessor.from_pretrained(MODELS[a.model])
    model = AutoModelForDepthEstimation.from_pretrained(MODELS[a.model]).eval()
    t1 = time.time()

    with torch.no_grad():
        pred = model(**proc(images=img, return_tensors="pt")).predicted_depth
    pred = torch.nn.functional.interpolate(
        pred.unsqueeze(1), size=img.size[::-1], mode="bicubic", align_corners=False
    )[0, 0]
    d = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)

    if a.soften:
        # Soften in 8-bit PIL or float -> smooth edges prevent rubber-sheet stretching in Blender DISPLACE
        try:
            import cv2
            import numpy as np
            arr = d.cpu().numpy().astype("float32")
            u8 = (arr * 255.0).round().clip(0, 255).astype("uint8")
            u8 = cv2.medianBlur(u8, 7)
            arr = cv2.GaussianBlur(u8.astype("float32") / 255.0, (0, 0), 5.0)
            d = torch.from_numpy(arr)
        except ImportError:
            tmp = Image.fromarray((d * 255).round().clamp(0, 255).to(torch.uint8).numpy(), mode="L")
            tmp = tmp.filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.GaussianBlur(5))
            import numpy as np
            d = torch.from_numpy(np.asarray(tmp, dtype="float32") / 255.0)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.bits == 16:
        Image.fromarray((d * 65535).round().clamp(0, 65535).to(torch.int32).numpy().astype("uint16")).save(a.out)
    else:
        Image.fromarray((d * 255).round().clamp(0, 255).to(torch.uint8).numpy(), mode="L").save(a.out)
    print(f"depth {img.size[0]}x{img.size[1]} ({a.bits}-bit{' softened' if a.soften else ''}) -> {a.out}  (load {t1 - t0:.1f}s, infer {time.time() - t1:.1f}s)")


if __name__ == "__main__":
    main()
