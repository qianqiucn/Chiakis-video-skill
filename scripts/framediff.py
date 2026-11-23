"""framediff.py — did a revision change only what it meant to? Run with the vision venv (-I).

  framediff.py <a.mp4> <b.mp4> [--from F --to T] [--box x0,y0,x1,y1] [--threshold 36]
        per-frame PSNR of B against A (frames 0-based, both at the same fps and size). Re-encoding alone scores about
        37–48 dB; a frame below the threshold (36 dB) really changed. Prints the changed frame ranges, the lowest
        frames and a summary. Use it before every delivery on the locked ranges (quality-bar Gate B2).
  framediff.py img <a.png> <b.png> [--box ...] [--out heat.jpg]
        max / mean difference, the share of pixels that moved by more than 6 levels, the changed area's bbox, and
        an optional heat map (look.py pair --diff draws the same side by side).
"""
import os, shutil
import argparse, glob, os, re, shutil, subprocess, sys, tempfile
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

def ranges(nums):
    out = []
    for n in nums:
        if out and n == out[-1][1] + 1: out[-1][1] = n
        else: out.append([n, n])
    return ", ".join(f"f{a}" if a == b else f"f{a}–{b}" for a, b in out)

if len(sys.argv) > 1 and sys.argv[1] == "img":
    ap = argparse.ArgumentParser(); ap.add_argument("mode"); ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--box"); ap.add_argument("--out"); a = ap.parse_args()
    A = Image.open(a.a).convert("RGB"); B = Image.open(a.b).convert("RGB")
    if B.size != A.size: B = B.resize(A.size, Image.LANCZOS); print("note: B resized to A's size")
    if a.box:
        bx = tuple(int(float(v)) for v in a.box.split(",")); A, B = A.crop(bx), B.crop(bx)
    d = np.abs(np.asarray(A, np.int16) - np.asarray(B, np.int16)).max(axis=2)
    ys, xs = np.nonzero(d > 6)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None
    print(f"max {int(d.max())}, mean {d.mean():.2f}, {(d > 6).mean():.2%} of pixels > 6 levels, changed bbox {bbox}")
    if a.out:
        g = np.asarray(A.convert("L"), np.float32) * 0.35
        Image.fromarray(np.stack([np.clip(g + d * 6, 0, 255), np.clip(g + d * 2, 0, 255), g], 2).astype(np.uint8)).save(a.out, quality=90)
        print("heat map ->", a.out)
    sys.exit()

ap = argparse.ArgumentParser()
ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("--from", dest="f0", type=int); ap.add_argument("--to", dest="f1", type=int)
ap.add_argument("--box"); ap.add_argument("--threshold", type=float, default=36.0)
a = ap.parse_args()
pre = []
if a.f0 is not None or a.f1 is not None:
    pre.append(f"trim=start_frame={a.f0 or 0}" + (f":end_frame={a.f1 + 1}" if a.f1 is not None else "") + ",setpts=PTS-STARTPTS")
if a.box:
    x0, y0, x1, y1 = [int(float(v)) for v in a.box.split(",")]; pre.append(f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0}")
chain = ",".join(pre) if pre else "null"
tmp = tempfile.mkdtemp(prefix="fdiff_"); log = os.path.join(tmp, "psnr.log")
r = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", os.path.abspath(a.a), "-i", os.path.abspath(a.b), "-lavfi",
                    f"[0:v]{chain}[x];[1:v]{chain}[y];[x][y]psnr=stats_file=psnr.log", "-f", "null", "-"],
                   cwd=tmp, capture_output=True, text=True, errors="ignore")
if r.returncode or not os.path.exists(log): sys.exit("ffmpeg psnr failed: " + r.stderr[-400:])
vals = []
for line in open(log, encoding="utf-8", errors="ignore"):
    m = re.search(r"n:(\d+).*psnr_avg:(\S+)", line)
    if m:
        v = m.group(2); vals.append((int(m.group(1)) - 1 + (a.f0 or 0), 99.0 if v == "inf" else float(v)))
shutil.rmtree(tmp, ignore_errors=True)
if not vals: sys.exit("no frames compared")
low = [n for n, v in vals if v < a.threshold]
fin = [v for _, v in vals]
print(f"compared {len(vals)} frames (f{vals[0][0]}–f{vals[-1][0]}): PSNR min {min(fin):.1f} dB, mean {sum(fin)/len(fin):.1f} dB "
      f"(identical frames count as 99)")
print(f"changed (< {a.threshold:g} dB): {len(low)} frames" + (f": {ranges(low)}" if low else " — none"))
for n, v in sorted(vals, key=lambda x: x[1])[:5]: print(f"  lowest: f{n} {v:.1f} dB")
