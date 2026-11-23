"""Depth design for camera-projection dolly shots (3D engineer). Run with `python -X utf8`.
Builds the per-pixel optical-axis depth rho (far-wall centre = 1) of every layer, consistent with:
  - a virtual camera (example: f = 1159 px, pitched up 16 deg, horizon ~870 px);
  - vertical structures (wall, towers, near layers, subject) as vertical planes: rho = Yn * rowfactor(y);
  - one floor plane rho_floor(y) = A / (y - y0) that every structure stands on (base contact = same depth);
  - a 16-bit depth map (scripts/vision/depth.py on plate.png) ordering structures onto their floor rows.

Usage:
  python -X utf8 design.py sim            -> parallax table for candidate y0 values
  python -X utf8 design.py build <y0>     -> eng/rho_plate.npy, eng/design.json, eng/rho_plate_vis.png
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENG = os.path.join(ROOT, "eng")
W, H = 1920, 1080
F = 1159.0
TH = np.radians(16.0)
TAN = np.tan(TH)
Y_WALL = 878.0          # wall/floor junction row (1080p)
Y_FEET = 884.0          # subject base contact row
Y_SHELF = 956.0         # near foreground plinth bottom
# painted-floor disparity model fitted from plate_depth.png
D_SLOPE = 0.005474 * 941.0 / 1080.0
Y_H = 758.0 * 1080.0 / 941.0


def rowfactor(y):
    return 1.0 / (1.0 + (np.asarray(y, np.float64) - 540.0) * TAN / F)


def travel(n):
    return 0.1309 * (1.0 - (1.0 - (n - 1) / 28.0) ** 4)


def load_depth():
    d = np.asarray(Image.open(os.path.join(ROOT, "plate_depth.png"))).astype(np.float64) / 65535.0
    im = Image.fromarray(d.astype(np.float32), "F").resize((W, H), Image.BILINEAR)
    return np.asarray(im, np.float64)


def load_mask(name, thr=None):
    a = Image.open(os.path.join(ROOT, name))
    if a.mode == "RGBA":
        a = a.getchannel("A")
    a = np.asarray(a.convert("L").resize((W, H), Image.BILINEAR), np.float64) / 255.0
    return a if thr is None else a > thr


def smooth_depth(d, shelf):
    """Median 9 (kills texture noise), dilate near side 4 px (near wins at silhouettes), light blur 2 px."""
    import cv2
    from scipy import ndimage
    a = ndimage.median_filter(np.clip(d, 0, 1).astype(np.float32), size=9)
    a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    a = cv2.GaussianBlur(a, (0, 0), 2.0)
    return a.astype(np.float64)


def plate_rho(d, y0, A, shelf_cover):
    yy = np.repeat(np.arange(H, dtype=np.float64)[:, None] + 0.5, W, 1)
    yb = Y_H + d / D_SLOPE
    yb = np.maximum(yb, Y_WALL)
    yb = np.where(shelf_cover, np.minimum(yb, Y_SHELF - 8.0), yb)
    floor_rows = yy >= yb - 8.0
    yb = np.where(floor_rows, np.maximum(yy, Y_WALL), yb)
    rho_f = A / (yb - y0)
    Yn = rho_f / rowfactor(yb)
    rho = Yn * rowfactor(yy)
    yn_s = (A / (Y_SHELF - y0)) / rowfactor(Y_SHELF)
    rho = np.where(shelf_cover & (yy < Y_SHELF), np.maximum(rho, 1.03 * yn_s * rowfactor(yy)), rho)
    return rho, yb


def params(y0):
    A = rowfactor(Y_WALL) * (Y_WALL - y0)
    rf = lambda y: A / (y - y0)
    yn_shelf = rf(Y_SHELF) / rowfactor(Y_SHELF)
    yn_sub = rf(Y_FEET) / rowfactor(Y_FEET)
    return A, yn_shelf, yn_sub


def sim(y0, d, masks, n_b=17, verbose=True):
    A, yn_s, yn_h = params(y0)
    shelf = masks["shelf"]
    rho_p, _ = plate_rho(d, y0, A, masks["shelf_cover"])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    rho_s = yn_s * rowfactor(yy)
    rho_h = yn_h * rowfactor(yy)
    t = travel(n_b)

    def move(rho):
        s = rho / (rho - t)
        return 960 + (xx - 960) * s, 540 + (yy - 540) * s

    out = {}
    step = 6
    sel = np.zeros((H, W), bool); sel[::step, ::step] = True
    wall = sel & masks["wallzone"] & ~shelf & ~masks["subject"]
    near = sel & shelf
    sub = sel & masks["subject"]
    towers = sel & masks["towers"] & ~shelf
    floor = sel & masks["floorzone"] & ~shelf
    P = {}
    for nm, m, rho in (("wall", wall, rho_p), ("near", near, rho_s), ("subject", sub, rho_h),
                       ("towers", towers, rho_p), ("floor", floor, rho_p)):
        bx, by = move(rho)
        P[nm] = ((xx[m] - 960) + 1j * (yy[m] - 540), (bx[m] - 960) + 1j * (by[m] - 540), rho[m])
    p, q, _ = P["wall"]
    pm, qm = p.mean(), q.mean()
    a = ((q - qm) * np.conj(p - pm)).sum() / (np.abs(p - pm) ** 2).sum()
    b = qm - a * pm
    for nm in P:
        p, q, r = P[nm]
        res = np.abs(q - (a * p + b))
        out[nm] = (float(np.median(res)), float(np.percentile(res, 90)), float(np.median(r)), float(np.median(np.abs(q / p))) if len(p) else 0)
    if verbose:
        print(f"y0={y0:.0f} A={A:.1f}  shelf Yn={yn_s:.3f} (rho base {yn_s*rowfactor(Y_SHELF):.3f}, mid {yn_s:.3f}, top {yn_s*rowfactor(0):.3f})"
              f"  subject Yn={yn_h:.3f} base {yn_h*rowfactor(Y_FEET):.3f}  floor rho@1080={A/(1080-y0):.3f} s_end={A/(1080-y0)/(A/(1080-y0)-travel(23)):.2f}"
              f"  wall-fit zoom {abs(a):.4f}")
        for nm, (med, p90, rmed, sc) in out.items():
            print(f"   {nm:7s} parallax vs wall: median {med:6.1f} px  P90 {p90:6.1f}   rho median {rmed:.3f}  scale {sc:.3f}")
    return out


def get_masks(d):
    shelf = np.maximum(load_mask("shelf_L.png"), load_mask("shelf_R.png")) > 0.5
    shelf_cover = np.asarray(Image.fromarray((shelf * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 127
    sub_file = "subject.png" if os.path.exists(os.path.join(ROOT, "subject.png")) else "girl.png"
    sub = load_mask(sub_file) > 0.5
    yy = np.repeat(np.arange(H)[:, None], W, 1)
    yb = Y_H + d / D_SLOPE
    floorzone = (yy >= yb - 8.0) & (yy > Y_WALL + 4)
    wallzone = (yb <= Y_WALL + 1) & ~floorzone
    towers = (yb > Y_WALL + 6) & ~floorzone
    return dict(shelf=shelf, shelf_cover=shelf_cover, subject=sub, floorzone=floorzone, wallzone=wallzone, towers=towers)


if __name__ == "__main__":
    cmd = sys.argv[1]
    d_raw = load_depth()
    shelf0 = np.maximum(load_mask("shelf_L.png"), load_mask("shelf_R.png")) > 0.5
    d = smooth_depth(d_raw, shelf0)
    masks = get_masks(d)
    if cmd == "sim":
        for y0 in [float(v) for v in (sys.argv[2:] or [760, 770, 780, 790, 800, 810])]:
            sim(y0, d, masks)
    elif cmd == "build":
        y0 = float(sys.argv[2])
        A, yn_s, yn_h = params(y0)
        rho_p, yb = plate_rho(d, y0, A, masks["shelf_cover"])
        os.makedirs(ENG, exist_ok=True)
        np.save(os.path.join(ENG, "rho_plate.npy"), rho_p.astype(np.float32))
        Image.fromarray(np.clip((1.0 / rho_p - 0.6) / 2.4 * 255, 0, 255).astype(np.uint8)).save(os.path.join(ENG, "rho_plate_vis.png"))
        out = sim(y0, d, masks)
        js = dict(F=F, pitch_deg=16.0, y0=y0, A=A, Y_WALL=Y_WALL, Y_FEET=Y_FEET, Y_SHELF=Y_SHELF,
                  yn_shelf=yn_s, yn_subject=yn_h, travel=[travel(n) for n in range(1, 24)],
                  sim_f1_f17={k: dict(median=v[0], p90=v[1], rho=v[2], scale=v[3]) for k, v in out.items()})
        with open(os.path.join(ENG, "design.json"), "w", encoding="utf-8") as fh:
            json.dump(js, fh, indent=1)
        print("wrote", os.path.join(ENG, "design.json"))
