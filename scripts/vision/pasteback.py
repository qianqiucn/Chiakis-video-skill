"""pasteback.py — pixel-aligned clean plate & surgical edit composite.

Takes an edited image ONLY inside a feathered mask and preserves every pixel outside the mask
from the original plate. Because alignment stays locked to the original, overlays, occlusion masks,
and Blender 2.5D relief camera rigs keep working without shifting shot timing.

Usage:
  python -X utf8 scripts/vision/pasteback.py <original.png> <edit.png> <mask> <out.png>
        [--grow 7] [--feather 10] [--region x0,y0,x1,y1 ...] [--min-area 400] [--align] [--lf 40]

Mask modes:
  <mask.png>             grayscale mask file (white = take from edit, e.g. segment.py *_mask.png)
  diff / diff:<thresh>   auto-mask where edit differs from original (default thresh 24 after 2px blur)
  box                    fill the --region x0,y0,x1,y1 boxes directly (use --grow 0 --feather 8)
  ellipse                fill ellipses inscribed in the --region boxes (ideal for eyes/mouths)

Alignment & colour matching:
  --align     register edit onto original via SIFT (outside --region) + RANSAC similarity transform;
              prints matched inliers, scale, and pixel shift so drift is caught before compositing.
  --lf SIGMA  match edit's low-frequency colour/exposure to original (Gaussian sigma px, e.g. 40)
              so seam brightness/hue shifts vanish while crisp local marks stay intact.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Pixel-aligned clean plate & surgical edit composite")
    ap.add_argument("orig", help="Original reference image")
    ap.add_argument("edit", help="Edited image to composite inside mask")
    ap.add_argument("mask", help="Mask image path, or 'diff' / 'diff:<thresh>' / 'box' / 'ellipse'")
    ap.add_argument("out", help="Output PNG path (also writes <out>_mask.png)")
    ap.add_argument("--grow", type=int, default=7, help="Dilate mask in px (default 7)")
    ap.add_argument("--feather", type=float, default=10.0, help="Feather mask edge in px (default 10)")
    ap.add_argument("--region", action="append", default=[], help="x0,y0,x1,y1 in original pixels (repeatable)")
    ap.add_argument("--min-area", type=int, default=400, help="Drop diff specks smaller than this area in px")
    ap.add_argument("--align", action="store_true", help="Register edit onto original via SIFT + RANSAC")
    ap.add_argument("--lf", type=float, default=0.0, help="Match edit low-frequency colour to original (sigma px, e.g. 40)")
    a = ap.parse_args()

    o = Image.open(a.orig).convert("RGB")
    e = Image.open(a.edit).convert("RGB").resize(o.size, Image.LANCZOS)

    def region_boxes():
        for r in a.region:
            x0, y0, x1, y1 = [int(float(v)) for v in r.split(",")]
            yield max(0, x0), max(0, y0), x1, y1

    def align_img(orig_img: Image.Image, edit_img: Image.Image):
        try:
            import cv2
        except ImportError:
            return None, "opencv-python not installed (`pip install opencv-python`)"
        g1 = cv2.cvtColor(np.asarray(orig_img), cv2.COLOR_RGB2GRAY)
        g2 = cv2.cvtColor(np.asarray(edit_img), cv2.COLOR_RGB2GRAY)
        feat = np.full(g1.shape, 255, np.uint8)
        for x0, y0, x1, y1 in region_boxes():
            feat[y0:y1, x0:x1] = 0
        sift = cv2.SIFT_create(8000)
        k1, d1 = sift.detectAndCompute(g1, feat)
        k2, d2 = sift.detectAndCompute(g2, feat)
        if d1 is None or d2 is None:
            return None, "no feature points"
        good = [
            p[0]
            for p in cv2.BFMatcher().knnMatch(d2, d1, k=2)
            if len(p) == 2 and p[0].distance < 0.7 * p[1].distance
        ]
        if len(good) < 12:
            return None, f"only {len(good)} matching points"
        p2 = np.float32([k2[x.queryIdx].pt for x in good])
        p1 = np.float32([k1[x.trainIdx].pt for x in good])
        M, inl = cv2.estimateAffinePartial2D(p2, p1, method=cv2.RANSAC, ransacReprojThreshold=1.5)
        if M is None:
            return None, "no transform"
        print(
            f"align: {len(good)} matches, {int(inl.sum())} inliers, "
            f"scale {np.hypot(M[0, 0], M[1, 0]):.4f}, shift {M[0, 2]:+.1f},{M[1, 2]:+.1f} px"
        )
        warped = cv2.warpAffine(
            np.asarray(edit_img), M, orig_img.size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return Image.fromarray(warped), ""

    if a.align:
        warped, why = align_img(o, e)
        if warped is None:
            print(f"ALIGN FAILED ({why}): pasted unaligned — inspect seam for doubled edges")
        else:
            e = warped

    if a.lf > 0:
        try:
            import cv2
        except ImportError:
            sys.exit("--lf requires opencv-python (`pip install opencv-python`)")
        of, ef = np.asarray(o, np.float32), np.asarray(e, np.float32)
        bo, be = cv2.GaussianBlur(of, (0, 0), a.lf), cv2.GaussianBlur(ef, (0, 0), a.lf)
        gain = (bo + 1.0) / (be + 1.0)
        print(
            f"lf: sigma {a.lf:g}, mean gain R {gain[..., 0].mean():.3f} "
            f"G {gain[..., 1].mean():.3f} B {gain[..., 2].mean():.3f}"
        )
        e = Image.fromarray(np.clip(ef * gain, 0, 255).round().astype(np.uint8))

    def boxes(shape):
        keep = np.zeros(shape, bool)
        for x0, y0, x1, y1 in region_boxes():
            keep[y0:y1, x0:x1] = True
        return keep

    if a.mask == "ellipse":
        if not a.region:
            sys.exit("ellipse needs --region x0,y0,x1,y1 (the box each ellipse fills)")
        mask = Image.new("L", o.size, 0)
        dr = ImageDraw.Draw(mask)
        for x0, y0, x1, y1 in region_boxes():
            dr.ellipse([x0, y0, x1, y1], fill=255)
        print(f"ellipse mask: {len(a.region)} ellipse(s), {np.asarray(mask).mean() / 255:.1%} of the frame")
    elif a.mask == "box":
        if not a.region:
            sys.exit("box needs --region x0,y0,x1,y1")
        m = boxes((o.size[1], o.size[0]))
        mask = Image.fromarray((m * 255).astype(np.uint8), "L")
        print(f"box mask: {len(a.region)} region(s), {m.mean():.1%} of the frame")
    elif a.mask.startswith("diff"):
        thr = float(a.mask.split(":", 1)[1]) if ":" in a.mask else 24.0
        ob = np.asarray(o.filter(ImageFilter.GaussianBlur(2)), np.int16)
        eb = np.asarray(e.filter(ImageFilter.GaussianBlur(2)), np.int16)
        m = np.abs(eb - ob).max(axis=2) > thr
        if a.region:
            m &= boxes(m.shape)
        try:
            from scipy import ndimage
            if a.align:
                m = ndimage.binary_opening(m, iterations=2)
            m = ndimage.binary_closing(m, iterations=2)
            lab, n = ndimage.label(m)
            if n:
                area = ndimage.sum(m, lab, range(1, n + 1))
                m = np.isin(lab, [i + 1 for i, s in enumerate(area) if s >= a.min_area])
            m = ndimage.binary_fill_holes(m)
        except ImportError:
            pass
        mask = Image.fromarray((m * 255).astype(np.uint8), "L")
        print(f"diff mask: threshold {thr:g}, regions {len(a.region) or 'whole frame'}, {m.mean():.1%} of the frame")
    else:
        mask = Image.open(a.mask).convert("L").resize(o.size, Image.LANCZOS)

    if a.grow > 0:
        mask = mask.filter(ImageFilter.MaxFilter(2 * a.grow + 1))
    mask_used = mask
    if a.feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(a.feather))

    out_dir = os.path.dirname(os.path.abspath(a.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    Image.composite(e, o, mask).save(a.out)
    mask_used.save(os.path.splitext(a.out)[0] + "_mask.png")

    d = ImageChops.difference(Image.open(a.out).convert("RGB"), o).convert("L")
    outside = Image.composite(Image.new("L", o.size, 0), d, mask.point(lambda v: 255 if v > 0 else 0))
    print(
        "pasteback ->",
        a.out,
        "| changed bbox:",
        d.point(lambda v: 255 if v > 3 else 0).getbbox(),
        "| max change outside mask:",
        max(outside.getdata()) if outside.getbbox() else 0,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
