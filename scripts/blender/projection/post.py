"""Linear-light compositing post pass for projection dolly shots. Run with `python -X utf8`.
Frames 1-16 pass through straight from Blender; frames 17-23 composite an overexposure white flash bursting out
of the window (mask B) around the subject silhouette (mask G) and foreground shelves (mask R).
Writes ../../frames/ours_0001.png ... and ../flash_stats.json.
Usage: python -X utf8 post.py [render_dir_name]
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exrio import read_png16, to8, luma8, srgb2lin, lin2srgb
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ROOT = os.path.dirname(ENG)
REN = os.path.join(ENG, sys.argv[1] if len(sys.argv) > 1 else "render")
OUT = os.path.join(ROOT, "frames")
os.makedirs(OUT, exist_ok=True)
H, W = 1080, 1920
WARM = np.array([1.0, 0.95, 0.86], np.float32)

T_WHITE = [17.5, 25.0, 36.0, 50.5, 70.0, 87.5, 99.7]
T_SHELF = [70, 77, 88, 104, 170, 215, 238]
T_MEAN = [121, 140, 163, 187, 221, 240, 243]
SAT = [0.80, 0.74, 0.64, 0.52, 0.18, 0.06, 0.0]
SUB_T = [0.0, 0.03, 0.10, 0.25, 1.0, 1.0, 1.0]
SUB_HOLD = [1.0, 0.95, 0.88, 0.80, 0.0, 0.0, 0.0]
OCC = [0.92, 0.90, 0.86, 0.72, 0.35, 0.10, 0.0]
SKY = [0.10, 0.18, 0.30, 0.45, 0.65, 0.85, 1.0]
BURN = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
VIGN = [0.0, 0.0, 0.0, 0.03, 0.08, 0.15, 0.25]
SIG = [8, 24, 64, 160, 420]
WIN_HOLD = [0.85, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0]


class Geo:
    def __init__(self, scale):
        self.sc, self.h, self.w = scale, H // scale, W // scale
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32) * scale
        self.sky = np.exp(-(((xx - 960) / 520) ** 2 + ((yy + 60) / 300) ** 2) / 2).astype(np.float32)
        self.r2 = ((((xx - 960) / 960) ** 2 + ((yy - 540) / 540) ** 2) / 2.0).astype(np.float32)

    def pyramid(self, S):
        out = []
        for s in SIG:
            s_ = s / self.sc
            if s >= 60:
                sm = cv2.resize(S, (self.w // 4, self.h // 4), interpolation=cv2.INTER_AREA)
                b = cv2.GaussianBlur(sm, (0, 0), sigmaX=s_ / 4, sigmaY=s_ / 4 * 1.35)
                b = cv2.resize(b, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
            else:
                b = cv2.GaussianBlur(S, (0, 0), sigmaX=s_, sigmaY=s_)
            out.append(b / max(float(b.max()), 1e-6))
        return out


PSF_W = [0.42, 0.24, 0.15, 0.11, 0.08]
ILLUM = 0.055
SHADE = [0.88, 0.84, 0.78, 0.62, 0.30, 0.10, 0.0]


class Frame:
    def __init__(self, B, M, k, g):
        self.B, self.M, self.k, self.g = B, M, k, g
        s, h, w = M[..., 0], M[..., 1], M[..., 2]
        self.S = np.clip(w * (1 - h * (1 - SUB_T[k])), 0, 1).astype(np.float32)
        pyr = g.pyramid(self.S)
        veil = sum(wt * p for wt, p in zip(PSF_W, pyr))
        self.veil = ((veil + g.sky * SKY[k] * 0.12) * (1 - s * OCC[k]) * (1 - h * SUB_HOLD[k])
                     * (1 - w * WIN_HOLD[k])).astype(np.float32)
        self.lift_w = (1 - s * SHADE[k]).astype(np.float32)
        self.boost = (1 + self.S * BURN[k]).astype(np.float32)
        self.shelf = s > 0.5
        self.sub = h > 0.5

    def compose(self, I):
        k = self.k
        C = self.B * ((1 + ILLUM * I * self.lift_w) * self.boost)[..., None] + (I * self.veil)[..., None] * WARM
        C = np.clip(C, 0, 1)
        Y = (0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2])[..., None]
        C = Y + SAT[k] * (C - Y)
        C = C * (1 - VIGN[k] * self.g.r2)[..., None]
        return np.clip(C, 0, 1)


def stats(C):
    L = luma8(to8(C))
    return float(L.mean()), float((L >= 200).mean() * 100), L


def to8_dither(lin, seed):
    rng = np.random.default_rng(seed)
    v = lin2srgb(lin) * 255.0 + rng.random(lin.shape[:2], dtype=np.float32)[..., None]
    return np.clip(np.floor(v), 0, 255).astype(np.uint8)


def solve(fr, I_min):
    lo, hi = max(I_min, 1e-3), 400.0
    if stats(fr.compose(lo))[1] >= T_WHITE[fr.k]:
        return lo
    for _ in range(30):
        mid = np.sqrt(lo * hi)
        if stats(fr.compose(mid))[1] < T_WHITE[fr.k]:
            lo = mid
        else:
            hi = mid
    return np.sqrt(lo * hi)


def white_width(L, row):
    m = L[row] >= 200
    if not m.any():
        return 0
    xs = np.nonzero(m)[0]
    c = xs[np.argmin(np.abs(xs - 960))]
    l = r = c
    while l > 0 and m[l - 1]:
        l -= 1
    while r < W - 1 and m[r + 1]:
        r += 1
    return int(r - l + 1)


if __name__ == "__main__":
    G4, G1 = Geo(4), Geo(1)
    log, I_prev = [], 0.0
    for n in range(1, 24):
        B = read_png16(os.path.join(REN, "beauty", f"b_{n:04d}.png"))
        if n <= 16:
            C = B
            m, wf, L = stats(C)
            log.append(dict(frame=n, mean=round(m, 1), white200=round(wf, 1)))
        else:
            k = n - 17
            M = read_png16(os.path.join(REN, "mask", f"m_{n:04d}.png"))
            small = Frame(cv2.resize(B, (W // 4, H // 4), interpolation=cv2.INTER_AREA),
                          cv2.resize(M, (W // 4, H // 4), interpolation=cv2.INTER_AREA), k, G4)
            I = solve(small, I_prev)
            I_prev = I
            C = Frame(B, M, k, G1).compose(I)
            m, wf, L = stats(C)
            rowc = int(np.median(np.nonzero(M[..., 2].max(1) > 0.5)[0]))
            hm, sm = M[..., 1] > 0.5, M[..., 0] > 0.5
            log.append(dict(frame=n, source_I=round(float(I), 3), mean=round(m, 1),
                            target_mean=T_MEAN[k], white200=round(wf, 1), target_white=T_WHITE[k],
                            white_width_px=white_width(L, rowc), subject_luma=round(float(L[hm].mean()), 1),
                            shelf_luma=round(float(np.median(L[sm])), 1),
                            corner_luma=round(float(np.mean([L[:60, :60].mean(), L[:60, -60:].mean(), L[-60:, :60].mean(), L[-60:, -60:].mean()])), 1),
                            sat=SAT[k]))
        Image.fromarray(to8_dither(C, 1000 + n)).save(os.path.join(OUT, f"ours_{n:04d}.png"))
        print(log[-1], flush=True)
    with open(os.path.join(ENG, "flash_stats.json"), "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=1)
