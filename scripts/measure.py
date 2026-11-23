"""measure.py — numbers before pictures: luma, saturation and frame-to-frame change of a region, per frame.
Run with Python: python -X utf8 scripts/measure.py ...

  measure.py <video.mp4 | frames dir | image ...> [--box x0,y0,x1,y1] [--mask m.png] [--frames 0-387:1] [--csv out.csv]

Per frame or image: Y mean and Y p95 (Rec.709 luma, 0–255), saturation mean (HSV S, 0–100), and ΔY against the previous
one. Then a summary: min / max / mean of Y and the largest jump with its frame. Typical uses: is the radar area dark
enough, does a run of cuts rise monotonically (adjacent ≤ 1 %), how bright is the white flash, how saturated is a shot.
Frames are 0-based, as qa.mjs / snap.mjs / look.py count them. The mask (white = measured) is scaled to the frame.
"""
import os, shutil
import argparse, csv, glob, os, shutil, subprocess, sys
import numpy as np
from PIL import Image

def ffmpeg():
    for env in ("CHIAKI_FFMPEG", "FFMPEG_PATH", "QCRV_FFMPEG"):
        v = os.environ.get(env)
        if v and os.path.exists(v):
            return v
    w = shutil.which("ffmpeg")
    if w:
        return w
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    sys.exit("ffmpeg not found: install ffmpeg on PATH or `pip install imageio-ffmpeg`, or set CHIAKI_FFMPEG")

def parse_frames(spec):
    out = []
    for part in spec.split(","):
        rng, _, step = part.strip().partition(":")
        a_, _, b_ = rng.partition("-")
        a0 = int(a_); b0 = int(b_) if b_ else a0
        out += list(range(a0, b0 + 1, int(step) if step else 1))
    return sorted(set(out))

def video_size(path):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-i", path], capture_output=True, text=True, errors="ignore").stderr
    import re
    m = re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", r)
    return (int(m.group(1)), int(m.group(2))) if m else sys.exit("can't read the video size")

def stats(rgb, mask):
    f = rgb.astype(np.float32)
    y = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    mx, mn = f.max(axis=2), f.min(axis=2)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0) * 100
    if mask is not None: y, s = y[mask], s[mask]
    return float(y.mean()), float(np.percentile(y, 95)), float(s.mean())

ap = argparse.ArgumentParser()
ap.add_argument("src", nargs="+"); ap.add_argument("--box"); ap.add_argument("--mask"); ap.add_argument("--frames"); ap.add_argument("--csv")
a = ap.parse_args()
box = tuple(int(float(v)) for v in a.box.split(",")) if a.box else None
items = []   # (label, rgb array)

src0 = a.src[0]
if len(a.src) == 1 and os.path.splitext(src0)[1].lower() in (".mp4", ".mov", ".mkv", ".webm"):
    W, H = video_size(src0)
    x0, y0, x1, y1 = box or (0, 0, W, H); w, h = x1 - x0, y1 - y0
    nums = parse_frames(a.frames) if a.frames else None
    vf = ["format=rgb24", f"crop={w}:{h}:{x0}:{y0}"]   # crop after rgb24: on yuv420 an odd size gets rounded
    if nums:
        runs = []                                  # consecutive frames → one between() each
        for n in nums:
            if runs and n == runs[-1][1] + 1: runs[-1][1] = n
            else: runs.append([n, n])
        vf.insert(0, "select='" + "+".join(f"between(n\\,{lo}\\,{hi})" for lo, hi in runs) + "'")
    data = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", src0, "-vf", ",".join(vf),
                           "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fs = w * h * 3
    for k in range(len(data) // fs):
        items.append((f"f{nums[k] if nums else k}", np.frombuffer(data, np.uint8, fs, k * fs).reshape(h, w, 3)))
    if nums and len(items) != len(nums): print(f"warning: asked {len(nums)} frames, got {len(items)} (past the end?)")
else:
    paths = []
    for s in a.src:
        paths += sorted(glob.glob(os.path.join(s, "*.png")) + glob.glob(os.path.join(s, "*.jpg"))) if os.path.isdir(s) else [s]
    for pth in paths:
        im = Image.open(pth).convert("RGB")
        if box: im = im.crop(box)
        items.append((os.path.basename(pth), np.asarray(im)))
if not items: sys.exit("nothing measured")
mask = None
if a.mask:
    mh, mw = items[0][1].shape[:2]
    mask = np.asarray(Image.open(a.mask).convert("L").resize((mw, mh))) > 127

rows, prev = [], None
for lab, rgb in items:
    ym, yp, sm = stats(rgb, mask)
    dy = None if prev is None else ym - prev
    rows.append((lab, ym, yp, sm, dy)); prev = ym
print(f"{'frame':>12} {'Y mean':>7} {'Y p95':>7} {'Sat':>6} {'ΔY':>7}")
for lab, ym, yp, sm, dy in rows:
    print(f"{lab:>12} {ym:7.1f} {yp:7.1f} {sm:6.1f} {'' if dy is None else f'{dy:+7.1f}'}")
ys = [r[1] for r in rows]
j = max(range(1, len(rows)), key=lambda i: abs(rows[i][4]), default=None)
print(f"summary: {len(rows)} measured, Y min {min(ys):.1f} max {max(ys):.1f} mean {sum(ys)/len(ys):.1f}"
      + (f", largest jump {rows[j][4]:+.1f} at {rows[j][0]}" if j else ""))
if a.csv:
    with open(a.csv, "w", newline="", encoding="utf-8") as f:
        w_ = csv.writer(f); w_.writerow(["frame", "y_mean", "y_p95", "sat", "dy"]); w_.writerows(rows)
