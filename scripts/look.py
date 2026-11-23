"""look.py — one labelled sheet instead of many image reads (the viewing budget: compare in one picture, then look once).
Run with Python: python -X utf8 scripts/look.py ...

  look.py crop  <out.jpg> <img> [<img> ...] [--box x0,y0,x1,y1 ...] [--scale 1] [--cols 4]
        every image × every box (no box = the whole image), e.g. the same region across five versions
  look.py pair  <out.jpg> <a> <b> [--box ...] [--scale 1] [--diff]
        A | B side by side per box (the same box on both), --diff adds a heat map of |A−B| (where an edit drifted)
  look.py video <out.jpg> <video.mp4> --frames 120,130-140:2 [--box ...] [--scale 0.33] [--cols 6]
        frames by number (0-based, as qa.mjs / snap.mjs count them), optionally cropped to boxes

Boxes are in the source's own pixels. Each tile is labelled with its source (file name or frame) and box.
Default scale: 1 for crops (full size: what the eye checks), 0.33 for whole 1080p frames.
"""
import argparse, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

def boxes(args):
    return [tuple(int(float(v)) for v in b.split(",")) for b in (args.box or [])] or [None]

def parse_frames(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part: continue
        rng, _, step = part.partition(":")
        a, _, b = rng.partition("-")
        a = int(a); b = int(b) if b else a; s = int(step) if step else 1
        out += list(range(a, b + 1, s))
    return sorted(set(out))

def font(px):
    for f in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(f):
            try: return ImageFont.truetype(f, px)
            except Exception: pass
    return ImageFont.load_default()

def tile(img, box, scale, label):
    im = img.crop(box) if box else img
    if scale != 1: im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    d = ImageDraw.Draw(im); f = font(14)
    tw = d.textlength(label, font=f)
    d.rectangle([0, 0, tw + 8, 20], fill=(0, 0, 0)); d.text((4, 2), label, fill=(255, 210, 60), font=f)
    return im

def sheet(tiles, cols, out):
    cols = max(1, min(cols, len(tiles)))
    rows = (len(tiles) + cols - 1) // cols
    cw = max(t.width for t in tiles); ch = max(t.height for t in tiles)
    s = Image.new("RGB", (cols * cw + (cols - 1) * 4, rows * ch + (rows - 1) * 4), (20, 20, 20))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * (cw + 4), (i // cols) * (ch + 4)))
    s.save(out, quality=90)
    print(f"{out}: {len(tiles)} tiles, {s.width}x{s.height}")

def heat(a, b):
    d = np.abs(np.asarray(a, np.int16) - np.asarray(b.resize(a.size), np.int16)).max(axis=2)
    g = np.asarray(a.convert("L"), np.float32) * 0.35
    rgb = np.stack([np.clip(g + d * 6, 0, 255), np.clip(g + d * 2, 0, 255), g], axis=2).astype(np.uint8)
    return Image.fromarray(rgb), int(d.max()), float((d > 6).mean())

def frames_from_video(path, nums):
    tmp = tempfile.mkdtemp(prefix="look_")
    sel = "+".join(f"eq(n\\,{n})" for n in nums)
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", path, "-vf", f"select='{sel}'",
                    "-fps_mode", "passthrough", os.path.join(tmp, "f%04d.png")], check=True)
    files = sorted(glob.glob(os.path.join(tmp, "f*.png")))
    if len(files) != len(nums): print(f"warning: asked {len(nums)} frames, got {len(files)} (past the end?)")
    return tmp, list(zip(nums, files))

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["crop", "pair", "video"]); ap.add_argument("out"); ap.add_argument("src", nargs="+")
ap.add_argument("--box", action="append"); ap.add_argument("--scale", type=float); ap.add_argument("--cols", type=int)
ap.add_argument("--frames"); ap.add_argument("--diff", action="store_true")
a = ap.parse_args()
B = boxes(a)
if a.mode == "crop":
    sc = a.scale if a.scale is not None else (1.0 if B[0] else 0.33)
    tiles = [tile(Image.open(p).convert("RGB"), b, sc, f"{os.path.basename(p)} {b or ''}") for p in a.src for b in B]
    sheet(tiles, a.cols or (len(a.src) if B[0] else 4), a.out)
elif a.mode == "pair":
    if len(a.src) != 2: sys.exit("pair needs exactly two images")
    A_, B_ = Image.open(a.src[0]).convert("RGB"), Image.open(a.src[1]).convert("RGB")
    if B_.size != A_.size: B_ = B_.resize(A_.size, Image.LANCZOS)
    sc = a.scale if a.scale is not None else (1.0 if B[0] else 0.33)
    tiles = []
    for b in B:
        tiles += [tile(A_, b, sc, f"A {os.path.basename(a.src[0])} {b or ''}"), tile(B_, b, sc, f"B {os.path.basename(a.src[1])}")]
        if a.diff:
            h, mx, frac = heat(A_.crop(b) if b else A_, B_.crop(b) if b else B_)
            tiles.append(tile(h, None, sc, f"|A-B| max {mx}, {frac:.1%} > 6"))
            print(f"box {b or 'whole'}: max difference {mx}, {frac:.1%} of pixels differ by > 6 levels")
    sheet(tiles, a.cols or (3 if a.diff else 2), a.out)
else:
    if not a.frames: sys.exit("video needs --frames, e.g. 120,130-140:2")
    nums = parse_frames(a.frames)
    tmp, got = frames_from_video(a.src[0], nums)
    try:
        sc = a.scale if a.scale is not None else (1.0 if B[0] else 0.33)
        tiles = [tile(Image.open(f).convert("RGB"), b, sc, f"f{n} {b or ''}") for n, f in got for b in B]
        sheet(tiles, a.cols or (6 if not B[0] else max(1, len(B))), a.out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
