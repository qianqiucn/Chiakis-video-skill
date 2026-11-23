"""Does a 3D camera move read as 3D, or as a flat 2D zoom/pan? Measures the parallax between two frames of one shot.

Tracks corners from frame A to frame B (Shi-Tomasi + normalised cross-correlation, coarse to fine, forward-backward
checked; numpy + PIL only), fits one global similarity (zoom + rotation + shift = all a flat 2D move can do) and
reports what is left over = parallax, in px at 1080p, its share of the overall move, and PASS/FAIL against the
target in references/relief-25d.md (>= 20 px subject vs background AND >= 15 % of the overall move, first vs last frame
of a ~23-frame shot; a little more than a flat push, not a big swing).
  no --depth : the similarity follows the dominant layer (RANSAC); parallax = P90 of the residual
  --depth    : the similarity is fitted on the background only (depth <= --mask-far); parallax = median residual
               of the subject (depth >= --mask-near) = subject vs background. Prefer this.

Usage:
  python -X utf8 scripts/vision/parallax.py A.png B.png [--depth A_depth.png] [--mask-far 0.2]
      [--mask-near 0.6] [--exclude "x0,y0,x1,y1;..."] [--search 128] [--target-px 20] [--target-share 0.15]
      [--out arrows.jpg]
Frames from an MP4 (ffmpeg 9 has no -vsync):  ffmpeg -i v.mp4 -vf "select=eq(n\\,219)" -fps_mode passthrough
  -frames:v 1 A.png    (relief/multiplane frames can be used directly)
--depth: depth of FRAME A, white = near: run depth.py on A itself (~1 s); or a subject mask of the subject
  (white = subject). --exclude: boxes in A's 1080p px (HUD, text) that move with the screen, not with the scene.
--out: frame B with the residual arrows x3 (red = subject, blue = background, grey = rest).
Exit code: 0 PASS, 1 FAIL, 2 could not measure.
"""
import argparse, math, sys
import numpy as np
from PIL import Image, ImageDraw


def load(path, size=None):
    im = Image.open(path).convert("RGB")
    size = size or (max(1, round(im.width * 1080 / im.height)), 1080)          # work at 1080p height
    if im.size != size:
        im = im.resize(size, Image.BICUBIC)
    a = np.asarray(im, np.float32) / 255.0
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2], im


def down2(a):
    a = a[: a.shape[0] // 2 * 2, : a.shape[1] // 2 * 2]
    return 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])


def sample(img, Mi, off, fill=0.0):
    """out(X) = img(Mi X + off) in continuous coords (pixel i spans [i, i+1], PIL's convention)"""
    data = (Mi[0, 0], Mi[0, 1], off[0], Mi[1, 0], Mi[1, 1], off[1])
    out = Image.fromarray(np.ascontiguousarray(img, np.float32), "F").transform(
        img.shape[::-1], Image.AFFINE, data, resample=Image.BILINEAR, fillcolor=fill)
    return np.asarray(out, np.float32)


def integral(x):
    S = np.zeros((x.shape[0] + 1, x.shape[1] + 1))
    S[1:, 1:] = x.cumsum(0).cumsum(1)
    return S


def boxsum(x, r):
    S = integral(np.pad(x, r, mode="edge").astype(np.float64))
    k = 2 * r + 1
    return S[k:, k:] - S[:-k, k:] - S[k:, :-k] + S[:-k, :-k]


def phase_corr(a, b, win):
    """shift d with b(x) = a(x - d), and the peak height"""
    R = np.fft.fft2((b - b.mean()) * win) * np.conj(np.fft.fft2((a - a.mean()) * win))
    r = np.fft.ifft2(R / (np.abs(R) + 1e-9)).real
    iy, ix = np.unravel_index(int(np.argmax(r)), r.shape)
    h, w = r.shape
    return (ix if ix < w / 2 else ix - w), (iy if iy < h / 2 else iy - h), float(r[iy, ix])


def init_global(A, B):
    """zoom search x phase correlation at quarter res -> similarity A->B:  Q - c = M (P - c) + t"""
    a, b = down2(down2(A)), down2(down2(B))
    c = np.array([a.shape[1] / 2, a.shape[0] / 2])
    win = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    best = None
    for s in np.exp(np.linspace(math.log(1 / 1.6), math.log(1.6), 121)):
        bs = sample(b, np.eye(2) * s, c - s * c, fill=np.nan)                 # bs(p) = b(s (p - c) + c)
        bs = np.where(np.isnan(bs), np.nanmean(bs), bs)
        dx, dy, pk = phase_corr(a, bs, win)
        if best is None or pk > best[0]:
            best = (pk, s, dx, dy)
    _, s, dx, dy = best
    return np.eye(2) * s, np.array([dx, dy]) * s * 4.0


def ncc_map(T, W):
    """normalised cross-correlation of template T (k x k) at every offset inside window W"""
    k = T.shape[0]
    T0 = T - T.mean()
    tn = math.sqrt(float((T0 * T0).sum()))
    if tn < 1e-3:
        return None
    m = W.shape[0] - k + 1
    cc = np.fft.irfft2(np.fft.rfft2(W) * np.conj(np.fft.rfft2(T0, s=W.shape)), s=W.shape)[:m, :m]
    S1, S2 = integral(W), integral(W * W)
    sw = S1[k:, k:] - S1[:-k, k:] - S1[k:, :-k] + S1[:-k, :-k]
    sw2 = S2[k:, k:] - S2[:-k, k:] - S2[k:, :-k] + S2[:-k, :-k]
    return cc / (np.sqrt(np.maximum(sw2 - sw * sw / (k * k), 1e-12)) * tn)


def peak(ncc, R, excl=0):
    """sub-pixel offset (dx, dy) of the best match and its score; None at the window edge or if ambiguous"""
    py, px = np.unravel_index(int(np.argmax(ncc)), ncc.shape)
    pk = float(ncc[py, px])
    if px in (0, 2 * R) or py in (0, 2 * R):
        return None
    if excl:
        z = ncc.copy()
        z[max(0, py - excl):py + excl + 1, max(0, px - excl):px + excl + 1] = -1
        if z.max() > pk - 0.03:
            return None
    def par(m, c0, p):
        d = m - 2 * c0 + p
        return 0.0 if abs(d) < 1e-9 else 0.5 * (m - p) / d
    return (px - R + par(ncc[py, px - 1], pk, ncc[py, px + 1]),
            py - R + par(ncc[py - 1, px], pk, ncc[py + 1, px]), pk)


def track(Ap, B, valid, search, cell=24):
    """corners of Ap (A warped into B's frame) -> rows (x, y, dx, dy): position in Ap, sub-pixel offset to B"""
    H, W = Ap.shape
    g = boxsum(Ap, 2) / 25.0
    gy, gx = np.gradient(g)
    Sxx, Syy, Sxy = boxsum(gx * gx, 3), boxsum(gy * gy, 3), boxsum(gx * gy, 3)
    lam = (Sxx + Syy) / 2 - np.sqrt(((Sxx - Syy) / 2) ** 2 + Sxy ** 2)
    ok = valid.copy()
    ok[:, :16] = ok[:, -16:] = ok[:16] = ok[-16:] = False
    lam = np.where(ok, lam, 0)
    if not (lam > 0).any():
        return np.zeros((0, 4))
    thr = 0.03 * np.percentile(lam[lam > 0], 99.5)
    pts = []
    for y in range(0, H - cell + 1, cell):
        for x in range(0, W - cell + 1, cell):
            blk = lam[y:y + cell, x:x + cell]
            j = int(np.argmax(blk))
            if blk.flat[j] > thr:
                pts.append((x + j % cell, y + j // cell))
    rh, Rh, r, Rf = 8, max(4, search // 2), 12, 4          # coarse: 17 px template at half res; fine: 25 px, +-4 px
    ah, bh = down2(Ap), down2(B)
    pad = Rh + rh + 2
    bhp = np.pad(bh, pad, mode="constant", constant_values=float(bh.mean()))
    validh = down2(valid.astype(np.float32)) > 0.999
    out = []
    for x, y in pts:
        xh, yh = x // 2, y // 2
        if not (rh <= xh < ah.shape[1] - rh and rh <= yh < ah.shape[0] - rh):
            continue
        if not validh[yh - rh:yh + rh + 1, xh - rh:xh + rh + 1].all():
            continue
        m = ncc_map(ah[yh - rh:yh + rh + 1, xh - rh:xh + rh + 1],
                    bhp[yh + pad - Rh - rh:yh + pad + Rh + rh + 1, xh + pad - Rh - rh:xh + pad + Rh + rh + 1])
        p = None if m is None else peak(m, Rh, excl=3)
        if p is None or p[2] < 0.7:
            continue
        ix, iy = x + int(round(2 * p[0])), y + int(round(2 * p[1]))            # coarse match in full-res px
        if not (r + Rf <= ix < W - r - Rf and r + Rf <= iy < H - r - Rf):
            continue
        m = ncc_map(Ap[y - r:y + r + 1, x - r:x + r + 1], B[iy - Rf - r:iy + Rf + r + 1, ix - Rf - r:ix + Rf + r + 1])
        p = None if m is None else peak(m, Rf)
        if p is None or p[2] < 0.8:
            continue
        dx, dy = ix - x + p[0], iy - y + p[1]
        jx, jy = x + int(round(dx)), y + int(round(dy))                         # backward check: B -> Ap
        if not (r <= jx < W - r and r <= jy < H - r):
            continue
        m = ncc_map(B[jy - r:jy + r + 1, jx - r:jx + r + 1], Ap[y - Rf - r:y + Rf + r + 1, x - Rf - r:x + Rf + r + 1])
        p = None if m is None else peak(m, Rf)
        if p is None or math.hypot(p[0] - (jx - x - dx), p[1] - (jy - y - dy)) > 1.0:
            continue
        out.append((x + 0.5, y + 0.5, dx, dy))
    return np.array(out).reshape(-1, 4)


def fit_sim(P, Q):
    """least squares Q = a P + b; complex a = zoom * rotation, b = shift (P, Q complex, centred)"""
    pm, qm = P.mean(), Q.mean()
    a = ((Q - qm) * np.conj(P - pm)).sum() / max(float((np.abs(P - pm) ** 2).sum()), 1e-9)
    return a, qm - a * pm


def ransac_sim(P, Q, thr=2.0, iters=800, seed=1):
    """similarity of the largest group of points that move together (2-point hypotheses), refined by LS"""
    rng = np.random.default_rng(seed)
    i, j = rng.integers(0, len(P), iters), rng.integers(0, len(P), iters)
    keep = np.abs(P[i] - P[j]) > 40
    i, j = i[keep], j[keep]
    if len(i):
        a = (Q[i] - Q[j]) / (P[i] - P[j])
        b = Q[i] - a * P[i]
        k = int(np.argmax((np.abs(Q[None, :] - (a[:, None] * P[None, :] + b[:, None])) < thr).sum(1)))
        a, b = a[k], b[k]
    else:
        a, b = fit_sim(P, Q)
    for _ in range(3):
        inl = np.abs(Q - (a * P + b)) < thr
        if inl.sum() >= 3:
            a, b = fit_sim(P[inl], Q[inl])
    return a, b, np.abs(Q - (a * P + b)) < thr


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("A"); ap.add_argument("B")
    ap.add_argument("--depth", help="depth (or subject mask) of frame A, white = near")
    ap.add_argument("--mask-far", type=float, default=0.2, help="background = depth <= this (0..1)")
    ap.add_argument("--mask-near", type=float, default=0.6, help="subject = depth >= this (0..1)")
    ap.add_argument("--exclude", default="", help='"x0,y0,x1,y1;..." boxes in A (1080p px) to ignore')
    ap.add_argument("--search", type=int, default=128, help="largest parallax to look for, px")
    ap.add_argument("--target-px", type=float, default=20.0)
    ap.add_argument("--target-share", type=float, default=0.15)
    ap.add_argument("--out", help="arrow sheet .jpg")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    A, _ = load(a.A)
    B, imB = load(a.B, size=A.shape[::-1])
    H, W = A.shape
    c = np.array([W / 2, H / 2])
    M0, t0 = init_global(A, B)
    Mi = np.linalg.inv(M0)
    off = c - Mi @ (c + t0)
    Ap = sample(A, Mi, off)                                                      # A in B's frame
    rows = track(Ap, B, sample(np.ones_like(A), Mi, off) > 0.999, a.search)
    Qf = rows[:, :2] + rows[:, 2:4]                                              # positions in B
    Pf = (rows[:, :2] - c - t0) @ Mi.T + c                                       # the same points in A
    if a.exclude and len(Pf):
        keep = np.ones(len(Pf), bool)
        for box in a.exclude.split(";"):
            x0, y0, x1, y1 = (float(v) for v in box.split(","))
            keep &= ~((Pf[:, 0] >= x0) & (Pf[:, 0] <= x1) & (Pf[:, 1] >= y0) & (Pf[:, 1] <= y1))
        Pf, Qf = Pf[keep], Qf[keep]
    n = len(Pf)
    print(f"A {a.A}\nB {a.B}\ntracked {n} features ({W}x{H})")
    if n < 30:
        print("RESULT could not measure: too few trackable features (blank/dark frames, or a cut between A and B)")
        sys.exit(2)
    P = (Pf[:, 0] - c[0]) + 1j * (Pf[:, 1] - c[1])
    Q = (Qf[:, 0] - c[0]) + 1j * (Qf[:, 1] - c[1])

    d = None
    if a.depth:
        dm = np.asarray(Image.open(a.depth).convert("F").resize((W, H), Image.BILINEAR), np.float64)
        dm = (dm - dm.min()) / max(dm.max() - dm.min(), 1e-9)
        d = dm[np.clip(Pf[:, 1].astype(int), 0, H - 1), np.clip(Pf[:, 0].astype(int), 0, W - 1)]
        far, near = d <= a.mask_far, d >= a.mask_near
        order = np.argsort(d)
        if far.sum() < 12:
            far = np.zeros(n, bool); far[order[:max(12, n // 7)]] = True
            print(f"note: < 12 features with depth <= {a.mask_far}; background = the farthest {far.sum()} features")
        if near.sum() < 12:
            near = np.zeros(n, bool); near[order[-max(12, n // 7):]] = True
            print(f"note: < 12 features with depth >= {a.mask_near}; subject = the nearest {near.sum()} features")
        ga, gb, inl = ransac_sim(P[far], Q[far])
        res, glob = np.abs(Q - (ga * P + gb)), np.abs(ga * P + gb - P)
        par, p90, overall = float(np.median(res[near])), float(np.percentile(res[near], 90)), float(np.median(glob[near]))
        fit_txt = f"fit on {far.sum()} background features, {inl.mean() * 100:.0f} % within 2 px"
        par_txt = f"parallax subject vs background ({near.sum()} features): median {par:.1f} px, P90 {p90:.1f} px"
    else:
        ga, gb, inl = ransac_sim(P, Q)
        res, glob = np.abs(Q - (ga * P + gb)), np.abs(ga * P + gb - P)
        par, overall = float(np.percentile(res, 90)), float(np.median(glob))
        fit_txt = f"fit on the dominant layer = {inl.mean() * 100:.0f} % of features"
        par_txt = f"parallax vs the dominant layer: P90 {par:.1f} px (median {np.median(res):.1f} px)"
    share = par / overall if overall >= 1.0 else 0.0                             # no camera move: nothing to share
    print(f"global move ({fit_txt}): zoom {(abs(ga) - 1) * 100:+.1f} %, rotation {math.degrees(np.angle(ga)):+.2f} deg, "
          f"shift {gb.real:+.1f}, {gb.imag:+.1f} px (about the frame centre: a zoom can hide the direction)")
    bg = (Q - P)[far] if d is not None else (Q - P)
    sx, sy = float(np.median(bg.real)), float(np.median(bg.imag))
    print(f"background slides {abs(sx):.0f} px {'right' if sx >= 0 else 'left'}, {abs(sy):.0f} px {'down' if sy >= 0 else 'up'} "
          f"(median of {'the background' if d is not None else 'all'} features: the shot's screen direction)")
    print(f"overall move{' at the subject' if d is not None else ''}: {overall:.0f} px (median)")
    print(f"{par_txt} = {share * 100:.1f} % of the overall move")
    if d is None:
        print("note: pass --depth (depth.py of frame A) to measure subject vs background")
    low_px, low_share = par < a.target_px, share < a.target_share
    ok = not (low_px or low_share)
    verdict = "PASS" if ok else "FAIL"
    why = ("" if ok else "  -> reads as a flat 2D zoom/pan" if low_px and low_share else
           "  -> too little parallax" if low_px else "  -> parallax drowned by the overall 2D move")
    print(f"target: >= {a.target_px:.0f} px and >= {a.target_share * 100:.0f} % (first vs last frame of a ~23-frame shot)")
    print(f"RESULT {verdict}  parallax {par:.1f} px = {share * 100:.1f} % of {overall:.0f} px"
          + why + ("" if ok else "; fixes: references/relief-25d.md"))
    if par > 3 * a.target_px:
        print(f"note: {par:.0f} px is far more than needed; a smaller angle reads calmer (3d.md §1: subtle depth)")

    if a.out:
        im = Image.eval(imB.convert("RGB").resize((W // 2, H // 2)), lambda v: int(v * 0.6))
        dr = ImageDraw.Draw(im)
        pred = ga * P + gb
        for k in range(n):
            x0, y0 = Qf[k] / 2
            v = (Q[k] - pred[k]) * 1.5                                          # x3 at half size
            if d is not None:
                col = (255, 70, 70) if near[k] else (80, 140, 255) if far[k] else (150, 150, 150)
            else:
                col = (255, 70, 70) if res[k] > max(2.0, 0.5 * par) else (150, 150, 150)
            dr.line((x0, y0, x0 + v.real, y0 + v.imag), fill=col, width=2)
            dr.ellipse((x0 - 1.5, y0 - 1.5, x0 + 1.5, y0 + 1.5), fill=col)
        dr.rectangle((0, 0, W // 2, 18), fill=(0, 0, 0))
        dr.text((4, 3), f"{verdict}  parallax {par:.1f} px = {share * 100:.1f} % of {overall:.0f} px   residual arrows x3",
                fill=(255, 255, 0))
        im.save(a.out, quality=88)
        print(f"arrows -> {a.out}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
