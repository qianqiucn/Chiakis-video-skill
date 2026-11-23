"""Near-pillar alpha edge straightening (optional). Run with `python -X utf8`.
Segmentation masks often stop slightly inside an architectural pillar's lit bevel, causing a torn edge when the
layer slides outward. Detects the strongest luminance step along each row, fits a robust RANSAC line per pillar,
and unions an anti-aliased half-plane with the original mask.
Writes eng/shelf_L_fix.png, eng/shelf_R_fix.png and eng/check_shelf_edge.png."""
import os
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENG = os.path.join(ROOT, "eng")
os.makedirs(ENG, exist_ok=True)
sc = np.asarray(Image.open(os.path.join(ROOT, "scene.png")).convert("RGB"), np.float32)
L = cv2.GaussianBlur(0.299 * sc[..., 0] + 0.587 * sc[..., 1] + 0.114 * sc[..., 2], (0, 0), 0.8)
H, W = L.shape
gx = np.zeros_like(L); gx[:, 1:-1] = (L[:, 2:] - L[:, :-2]) * 0.5


def fit_line(ys, xs, iters=400, thr=1.5, seed=3):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(iters):
        i, j = rng.choice(len(ys), 2, replace=False)
        if abs(ys[i] - ys[j]) < 50:
            continue
        b = (xs[j] - xs[i]) / (ys[j] - ys[i]); a = xs[i] - b * ys[i]
        inl = np.abs(xs - (a + b * ys)) < thr
        if best is None or inl.sum() > best[0]:
            best = (inl.sum(), inl)
    inl = best[1]
    b, a = np.polyfit(ys[inl], xs[inl], 1)
    return a, b, inl


def fix(side, y_max):
    rgba = np.asarray(Image.open(os.path.join(ROOT, f"shelf_{side}.png")).convert("RGBA")).copy()
    al = rgba[..., 3].astype(np.float32) / 255.0
    sgn = 1 if side == "R" else -1
    ys, xs, st = [], [], []
    for y in range(0, y_max):
        inside = np.nonzero(al[y] > 0.5)[0]
        if not len(inside):
            continue
        xm = inside.min() if side == "R" else inside.max()
        if side == "R":
            lo, hi = max(1, xm - 26), min(W - 2, xm + 3)
            seg = gx[y, lo:hi]
        else:
            lo, hi = max(1, xm - 3), min(W - 2, xm + 27)
            seg = -gx[y, lo:hi]
        k = int(np.argmax(seg))
        if 0 < k < len(seg) - 1:
            d = seg[k - 1] - 2 * seg[k] + seg[k + 1]
            off = 0.5 * (seg[k - 1] - seg[k + 1]) / d if abs(d) > 1e-6 else 0.0
        else:
            off = 0.0
        ys.append(y); xs.append(lo + k + off); st.append(seg[k])
    ys, xs, st = np.array(ys, float), np.array(xs, float), np.array(st, float)
    good = st > np.percentile(st, 35)
    a, b, inl = fit_line(ys[good], xs[good])
    xm_old = np.array([(np.nonzero(al[int(y)] > 0.5)[0].min() if side == "R" else np.nonzero(al[int(y)] > 0.5)[0].max()) for y in ys])
    line = a + b * ys
    ext = sgn * (xm_old - line)
    print(f"{side}: line x = {a:.1f} + {b:.4f} y over rows 0-{y_max}; inliers {inl.sum()}/{good.sum()}; "
          f"grow median {np.median(ext):.1f} px, P10 {np.percentile(ext, 10):.1f}, P90 {np.percentile(ext, 90):.1f}")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xl = a + b * (yy + 0.5)
    half = np.clip((xx + 0.5 - xl) + 0.5, 0, 1) if side == "R" else np.clip((xl - (xx + 0.5)) + 0.5, 0, 1)
    wrow = np.clip((y_max - yy) / 12.0, 0, 1)
    near = cv2.dilate((al > 0.5).astype(np.uint8), np.ones((1, 81), np.uint8)).astype(np.float32)
    new = np.maximum(al, half * wrow * near)
    rgba[..., 3] = np.clip(new * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(ENG, f"shelf_{side}_fix.png"))
    return new, a, b


newL, aL, bL = fix("L", 585)
newR, aR, bR = fix("R", 640)


def edge(m):
    m = (m > 0.5).astype(np.uint8)
    return (m == 1) & (cv2.erode(m, np.ones((3, 3), np.uint8)) == 0)


oldL = np.asarray(Image.open(os.path.join(ROOT, "shelf_L.png")).getchannel("A")) > 127
oldR = np.asarray(Image.open(os.path.join(ROOT, "shelf_R.png")).getchannel("A")) > 127
img = sc.astype(np.uint8).copy()
img[edge(oldL) | edge(oldR)] = [255, 40, 40]
img[edge(newL) | edge(newR)] = [40, 255, 40]
tiles = []
for y0 in (10, 200, 400, 520):
    for x0 in (int(aL + bL * (y0 + 40)) - 45, int(aR + bR * (y0 + 40)) - 45):
        tiles.append(Image.fromarray(img).crop((x0, y0, x0 + 90, y0 + 90)).resize((270, 270), Image.NEAREST))
sheet = Image.new("RGB", (270 * 4, 270 * 2))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i // 2) * 270, (i % 2) * 270))
sheet.save(os.path.join(ENG, "check_shelf_edge.png"))
print("sheet", os.path.join(ENG, "check_shelf_edge.png"))
