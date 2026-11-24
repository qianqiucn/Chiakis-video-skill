"""prep_texture.py — extract crisp, H.264-surviving tactile textures from raw scans.

Many raw paper scans (including bundled `assets/textures/paper/Paper001_4K_color.jpg`) have a very
narrow luminance spread (e.g. [236..252]), which disappears after Canvas `multiply` + H.264 compression.
This helper high-pass flattens uneven illumination and contrast-stretches the real fiber/mineral tooth
into a ready-to-composite multiply or overlay plate.

Usage:
  python -X utf8 scripts/prep_texture.py <in_img> <out_img> [--mode paper|stone|grain] [--strength 1.0] [--size 1920x1080] [--blur 24]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _luma_stats(arr: np.ndarray) -> str:
    y = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    p5, p50, p95 = np.percentile(y, [5, 50, 95])
    return f"min={y.min():.0f} p5={p5:.0f} p50={p50:.0f} p95={p95:.0f} max={y.max():.0f} (span={p95 - p5:.0f})"


def _fit_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    w, h = img.size
    scale = max(target_w / w, target_h / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    res = img.resize((nw, nh), Image.LANCZOS)
    x0 = (nw - target_w) // 2
    y0 = (nh - target_h) // 2
    return res.crop((x0, y0, x0 + target_w, y0 + target_h))


def main() -> int:
    ap = argparse.ArgumentParser(description="High-pass contrast stretch for tactile paper/stone/grain overlays")
    ap.add_argument("input", help="Source texture image")
    ap.add_argument("output", help="Output PNG/JPG path")
    ap.add_argument("--mode", choices=("paper", "stone", "grain"), default="paper",
                    help="paper=warm multiply [175..255], stone=deep multiply [145..255], grain=neutral overlay [64..192]")
    ap.add_argument("--strength", type=float, default=1.0, help="Contrast multiplier (default 1.0)")
    ap.add_argument("--size", default="", help="Optional target WxH (e.g. 1920x1080) via cover-crop")
    ap.add_argument("--blur", type=float, default=24.0, help="High-pass Gaussian radius in px (default 24)")
    a = ap.parse_args()

    img = Image.open(a.input).convert("RGB")
    if a.size:
        tw, th = [int(v) for v in a.size.lower().split("x", 1)]
        img = _fit_cover(img, tw, th)

    src = np.asarray(img, dtype=np.float32)
    low = np.asarray(img.filter(ImageFilter.GaussianBlur(radius=a.blur)), dtype=np.float32)
    hp = src - low  # zero-mean tactile tooth

    # Normalize using luminance high-pass percentiles to preserve natural channel warmth
    hp_y = 0.299 * hp[..., 0] + 0.587 * hp[..., 1] + 0.114 * hp[..., 2]
    lo, hi = np.percentile(hp_y, [2.0, 98.0])
    scale = max(1e-3, (hi - lo) * 0.5)
    norm = np.clip(hp / scale, -1.5, 1.5)  # ~[-1, +1]

    if a.mode == "paper":
        # Multiply-ready white-anchored sheet with crisp dark fibers [~175..255]
        # Shift so +1 lands near 253 and -1 lands near (253 - 78 * strength)
        depth = 40.0 * a.strength
        out = 252.0 - depth + norm * depth
        # Keep gentle warm paper tone from original mean chromaticity
        mean_rgb = src.mean(axis=(0, 1))
        chroma = mean_rgb / max(1.0, float(mean_rgb.max()))
        out = out * (0.65 + 0.35 * chroma)
    elif a.mode == "stone":
        depth = 56.0 * a.strength
        out = 250.0 - depth + norm * depth
    else:
        # Neutral 128-centered plate for overlay / soft-light film grain
        amp = 64.0 * a.strength
        out = 128.0 + norm * amp

    out_u8 = np.clip(out.round(), 0, 255).astype(np.uint8)
    out_p = Path(a.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out_u8, mode="RGB").save(out_p, quality=92)
    print(f"prep_texture ({a.mode}, strength={a.strength:g}): {a.input} -> {out_p} ({img.size[0]}x{img.size[1]})")
    print(f"  in  luma: {_luma_stats(src)}")
    print(f"  out luma: {_luma_stats(out_u8.astype(np.float32))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
