"""part_cutout.py — flagship 19-part anime single-layer RGBA & clean-plate extractor.

Combines:
  1. `24yearsold/l2d_sam_iter2` (Apache-2.0, 19-class Live2D/anime SemanticSam) on a
     neutral mid-gray character crop so bright/silver hair never blends into white backdrops.
  2. `joelseytre/toonout` (MIT, via sibling `cutout.py`) full-frame + 2K local part-bbox
     zoom refinement so fine 1-2 px hair wisps retain native 2K sharpness with 100% original RGB.
  3. Head-anchored connected-component filtering (auto-enabled for `hair`) to reject
     disconnected lower-body ribbon/sleeve false positives.
  4. Optional `--clean-plate` fast outer-background TELEA erasure strictly outside protected
     body/face/hat regions — eliminates double-exposure ghosting when animating hair/tails/wings
     with `T3.her.wave` + `T3.her.warp2` without diffusion redraw loss.

Supported `--part` names (comma-separated allowed, e.g. `--part hair` or `--part hair,headwear`):
  hair, headwear, face, eyes, eyewear, ears, earwear, nose, mouth, neck, neckwear,
  topwear, handwear, bottomwear, legwear, footwear, tail, wings, objects

Usage:
  python -X utf8 scripts/vision/part_cutout.py <in.png> <out_rgba.png>
        [--part hair] [--clean-plate clean.png] [--mask mask.png] [--json info.json]
        [--defringe 0.55] [--no-zoom] [--no-head-filter] [--cpu] [--fp32] [--offline]
  python -X utf8 scripts/vision/part_cutout.py --list-parts

Requires optional vision packages (same as `cutout.py`):
  pip install torch torchvision "transformers<5" timm einops kornia huggingface_hub opencv-python pillow
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_VISION_DIR = str(Path(__file__).resolve().parent)
if _VISION_DIR not in sys.path:
    sys.path.insert(0, _VISION_DIR)

VALID_BODY_PARTS = (
    "hair",
    "headwear",
    "face",
    "eyes",
    "eyewear",
    "ears",
    "earwear",
    "nose",
    "mouth",
    "neck",
    "neckwear",
    "topwear",
    "handwear",
    "bottomwear",
    "legwear",
    "footwear",
    "tail",
    "wings",
    "objects",
)

STRICT_OCC_CANDIDATES = (
    "hair",
    "headwear",
    "eyes",
    "eyewear",
    "ears",
    "earwear",
    "nose",
    "mouth",
    "neck",
    "neckwear",
    "topwear",
    "handwear",
    "bottomwear",
    "legwear",
    "footwear",
)


def _filter_head_anchored(p_target, p_face, p_headwear):
    """Keep target components anchored near the head (kills stray lower-body ribbons/sleeves)."""
    import cv2
    import numpy as np

    bin_h = (p_target > 0.35).astype(np.uint8)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(bin_h, connectivity=8)
    if num <= 1:
        return np.ones_like(p_target, dtype=np.float32)

    anchor = ((p_face > 0.35) | (p_headwear > 0.35)).astype(np.uint8)
    has_face = int(anchor.sum()) > 50
    if has_face:
        ay, ax = np.where(anchor > 0)
        head_r = max(32.0, float(ay.max() - ay.min()), float(ax.max() - ax.min()))
        ks = int(max(15, head_r * 0.25)) | 1
        anchor_dil = cv2.dilate(anchor, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks)))
    else:
        head_r = max(p_target.shape) * 0.25
        anchor_dil = np.zeros_like(bin_h)

    areas = stats[1:, cv2.CC_STAT_AREA]
    main_ids = set()
    if has_face:
        for cid in range(1, num):
            if stats[cid, cv2.CC_STAT_AREA] >= 30 and (labels == cid)[anchor_dil > 0].any():
                main_ids.add(cid)
    if not main_ids:
        main_ids.add(int(np.argmax(areas)) + 1)

    primary_mask = np.isin(labels, list(main_ids)).astype(np.uint8)
    dist_from_primary = cv2.distanceTransform(1 - primary_mask, cv2.DIST_L2, 5)
    max_gap = max(28.0, head_r * 0.55)
    keep_ids = set(main_ids)
    for cid in range(1, num):
        if cid in keep_ids or stats[cid, cv2.CC_STAT_AREA] < 15:
            continue
        comp_mask = labels == cid
        if float(dist_from_primary[comp_mask].min()) <= max_gap and float(p_target[comp_mask].mean()) > 0.45:
            keep_ids.add(cid)

    keep = np.isin(labels, list(keep_ids)).astype(np.float32)
    keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return cv2.GaussianBlur(keep, (0, 0), 2.5)


def _box_from_mask(mask_bool, sx=1.0, sy=1.0):
    import numpy as np

    ys, xs = np.where(mask_bool)
    if not xs.size:
        return None
    return [
        int(round(float(xs.min()) * sx)),
        int(round(float(ys.min()) * sy)),
        int(round(float(xs.max()) * sx)),
        int(round(float(ys.max()) * sy)),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Anime 19-part single-layer precision RGBA & clean-plate cutout (l2d_sam_iter2 + 2K ToonOut zoom)"
    )
    ap.add_argument("input", nargs="?", help="Input illustration path (PNG/JPG/WebP)")
    ap.add_argument("output", nargs="?", help="Output single-layer RGBA PNG path")
    ap.add_argument(
        "--part",
        default="hair",
        help="Target body part(s), comma-separated (default: hair). Run --list-parts to view all 19.",
    )
    ap.add_argument(
        "--clean-plate",
        default="",
        help="Optional output path for auto outer-background TELEA clean plate (zero double-ghosting in T3.her.wave)",
    )
    ap.add_argument("--mask", default="", help="Optional output path for 8-bit grayscale alpha mask PNG")
    ap.add_argument("--json", default="", help="Optional output path for detected part/face rig boxes JSON")
    ap.add_argument(
        "--defringe",
        type=float,
        default=0.55,
        help="Edge colour-decontamination strength 0..1 (default 0.55; 0 disables)",
    )
    ap.add_argument("--no-zoom", action="store_true", help="Disable 2nd-pass 2K local zoom ToonOut refinement")
    ap.add_argument(
        "--no-head-filter",
        action="store_true",
        help="Disable head-anchored connected-component filter (auto-enabled when extracting hair)",
    )
    ap.add_argument("--cpu", action="store_true", help="Force CPU execution")
    ap.add_argument("--fp32", action="store_true", help="Force FP32 for ToonOut (default FP16 on CUDA)")
    ap.add_argument("--offline", action="store_true", help="Force offline HuggingFace cache mode")
    ap.add_argument("--list-parts", action="store_true", help="Print all 19 supported anime body parts and exit")
    args = ap.parse_args()

    if args.list_parts:
        print("Supported 19 anime body parts (24yearsold/l2d_sam_iter2, Apache-2.0):")
        print("  " + ", ".join(VALID_BODY_PARTS))
        return 0

    if not args.input or not args.output:
        ap.error("input and output paths are required (or pass --list-parts)")

    parts = [p.strip().lower() for p in args.part.split(",") if p.strip()]
    invalid = [p for p in parts if p not in VALID_BODY_PARTS]
    if not parts or invalid:
        sys.exit(f"Unknown --part value(s): {invalid}. Valid: {', '.join(VALID_BODY_PARTS)}")

    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    try:
        import cv2
        import numpy as np
        import torch
        from PIL import Image
        import cutout as cutout_mod
        from _l2dsam import load_l2d_sam
    except ImportError as e:
        sys.exit(
            f"part_cutout.py requires optional vision packages ({e}). Install with:\n"
            '  pip install torch torchvision "transformers<5" timm einops kornia huggingface_hub opencv-python pillow'
        )

    device = "cpu" if (args.cpu or not torch.cuda.is_available()) else "cuda"
    use_fp16 = (device == "cuda") and (not args.fp32)

    t0 = time.time()
    sam_model = load_l2d_sam(device=device, offline=args.offline)
    toon_model = cutout_mod._load_model("toonout", device, use_fp16)
    t_load = time.time() - t0

    t1 = time.time()
    pil_rgb = Image.open(args.input).convert("RGB")
    orig_rgb = np.asarray(pil_rgb, dtype=np.uint8)
    H, W = orig_rgb.shape[:2]

    # 1. Full-frame ToonOut character silhouette
    a_fg = cutout_mod._infer_alpha(toon_model, pil_rgb, 1024, device, use_fp16)
    ys, xs = np.where(a_fg > 0.05)
    if not xs.size:
        sys.exit(f"part_cutout.py: no foreground character detected in {args.input}")

    # 2. Tight character crop composited on neutral mid-gray (gray128 preserves both silver and dark hair!)
    pad_x = max(24, int((xs.max() - xs.min()) * 0.05))
    pad_y = max(24, int((ys.max() - ys.min()) * 0.05))
    x0, y0 = max(0, int(xs.min()) - pad_x), max(0, int(ys.min()) - pad_y)
    x1, y1 = min(W, int(xs.max()) + pad_x), min(H, int(ys.max()) + pad_y)
    cw, ch = x1 - x0, y1 - y0
    a_crop = a_fg[y0:y1, x0:x1][..., None]
    crop_gray = np.clip(orig_rgb[y0:y1, x0:x1] * a_crop + 128.0 * (1.0 - a_crop), 0, 255).astype(np.uint8)

    with torch.inference_mode():
        logits = sam_model.inference(crop_gray)[0]
        probs = torch.sigmoid(logits).float().cpu().numpy()

    def cls_prob(name: str):
        idx = VALID_BODY_PARTS.index(name)
        return cv2.resize(probs[idx], (cw, ch), interpolation=cv2.INTER_LINEAR)

    # Target probability = union (pixelwise max) of requested part(s)
    p_target = np.zeros((ch, cw), dtype=np.float32)
    for nm in parts:
        p_target = np.maximum(p_target, cls_prob(nm))

    p_face = cls_prob("face")
    p_headwear = cls_prob("headwear")
    part_set = set(parts)

    # Competing non-target occluders
    p_occ = np.zeros((ch, cw), dtype=np.float32)
    for nm in STRICT_OCC_CANDIDATES:
        if nm not in part_set:
            p_occ = np.maximum(p_occ, cls_prob(nm))

    is_hair_mode = part_set.issubset({"hair", "headwear"}) and ("hair" in part_set)
    if "face" not in part_set:
        if is_hair_mode:
            # Bangs tips win cleanly over forehead/face; strict occluders (hat/ear/eyes/hand/clothes) win cleanly
            vs_face = np.clip((p_target - p_face + 0.18) / 0.30, 0.0, 1.0)
            vs_occ = np.clip((p_target - p_occ + 0.06) / 0.24, 0.0, 1.0)
        else:
            vs_face = np.clip((p_target - p_face + 0.06) / 0.24, 0.0, 1.0)
            vs_occ = np.clip((p_target - p_occ + 0.06) / 0.24, 0.0, 1.0)
        a_sem = np.clip((p_target - 0.32) / 0.30, 0.0, 1.0) * vs_face * vs_occ
    else:
        vs_occ = np.clip((p_target - p_occ + 0.06) / 0.24, 0.0, 1.0)
        a_sem = np.clip((p_target - 0.32) / 0.30, 0.0, 1.0) * vs_occ

    # Head-anchored component filter (auto-ON when extracting hair, kills lower-body ribbon false positives)
    if is_hair_mode and not args.no_head_filter:
        a_sem = a_sem * _filter_head_anchored(p_target, p_face, p_headwear)

    # 3. 2K Local-Zoom ToonOut refinement on the extracted part bounding box
    a_fg_hi = a_fg[y0:y1, x0:x1].copy()
    if not args.no_zoom and (a_sem > 0.25).any():
        py, px = np.where(a_sem > 0.25)
        hpad = max(48, int(max(px.max() - px.min(), py.max() - py.min()) * 0.18))
        zx0 = max(0, x0 + int(px.min()) - hpad)
        zy0 = max(0, y0 + int(py.min()) - hpad)
        zx1 = min(W, x0 + int(px.max()) + hpad)
        zy1 = min(H, y0 + int(py.max()) + hpad)
        if (zx1 - zx0) < W * 0.88 or (zy1 - zy0) < H * 0.88:
            a_zoom = cutout_mod._infer_alpha(toon_model, pil_rgb.crop((zx0, zy0, zx1, zy1)), 1024, device, use_fp16)
            zh, zw = a_zoom.shape
            w_mask = np.ones((zh, zw), dtype=np.float32)
            b = min(16, zh // 8, zw // 8)
            if b > 1:
                ramp = np.linspace(0, 1, b, dtype=np.float32)
                w_mask[:b, :] *= ramp[:, None]
                w_mask[-b:, :] *= ramp[::-1, None]
                w_mask[:, :b] *= ramp[None, :]
                w_mask[:, -b:] *= ramp[None, ::-1]
            ox0, oy0 = max(x0, zx0) - x0, max(y0, zy0) - y0
            ox1, oy1 = min(x1, zx1) - x0, min(y1, zy1) - y0
            sx0, sy0 = max(x0, zx0) - zx0, max(y0, zy0) - zy0
            sx1, sy1 = sx0 + (ox1 - ox0), sy0 + (oy1 - oy0)
            wm = w_mask[sy0:sy1, sx0:sx1]
            a_fg_hi[oy0:oy1, ox0:ox1] = a_fg_hi[oy0:oy1, ox0:ox1] * (1.0 - wm) + a_zoom[sy0:sy1, sx0:sx1] * wm

    # 4. Outer silhouette refinement strictly outside non-target body parts
    a_any_other = np.zeros((ch, cw), dtype=np.float32)
    for nm in VALID_BODY_PARTS:
        if nm not in part_set:
            a_any_other = np.maximum(a_any_other, cls_prob(nm))

    k_dil = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    a_dil = cv2.dilate(a_sem, k_dil)
    outer_zone = np.clip(
        (1.0 - np.clip((a_any_other - 0.18) / 0.28, 0.0, 1.0)) * (a_dil > 0.35).astype(np.float32),
        0.0,
        1.0,
    )
    outer_zone = cv2.GaussianBlur(outer_zone, (0, 0), 1.0)
    a_refined = np.maximum(a_sem * (1.0 - outer_zone), a_fg_hi * outer_zone)
    a_refined = np.clip(np.minimum(a_refined, a_fg_hi), 0.0, 1.0)
    a_refined[a_refined < 0.02] = 0.0

    full_alpha = np.zeros((H, W), dtype=np.float32)
    full_alpha[y0:y1, x0:x1] = a_refined

    rgb_clean = cutout_mod._defringe_rgb(orig_rgb, full_alpha, args.defringe)
    alpha_u8 = np.clip((full_alpha * 255.0).round(), 0, 255).astype(np.uint8)
    out_rgba = np.dstack([rgb_clean, alpha_u8])

    out_p = Path(args.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out_rgba, "RGBA").save(out_p)

    if args.mask:
        mp = Path(args.mask)
        mp.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(alpha_u8, "L").save(mp)

    # 5. Optional outer-background TELEA clean plate (erases static outer hair/part over pure bg only)
    if args.clean_plate:
        full_hat = np.zeros((H, W), dtype=np.float32)
        if "headwear" not in part_set:
            full_hat[y0:y1, x0:x1] = p_headwear
        p_body_only = np.zeros((ch, cw), dtype=np.float32)
        for nm in ("face",) + STRICT_OCC_CANDIDATES:
            if nm not in part_set and nm != "headwear":
                p_body_only = np.maximum(p_body_only, cls_prob(nm))
        full_body = np.zeros((H, W), dtype=np.float32)
        full_body[y0:y1, x0:x1] = p_body_only

        protect_body = cv2.dilate((full_body > 0.12).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
        protect_hat = cv2.dilate((full_hat > 0.25).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        protect = np.maximum(protect_body, protect_hat)

        over_bg = ((full_alpha > 0.08).astype(np.uint8)) & (1 - protect)
        over_bg_dil = cv2.dilate(over_bg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) & (1 - protect)
        bgr = cv2.cvtColor(orig_rgb, cv2.COLOR_RGB2BGR)
        inpaint_bgr = cv2.inpaint(bgr, (over_bg_dil * 255).astype(np.uint8), inpaintRadius=14, flags=cv2.INPAINT_TELEA)
        blend_m = cv2.GaussianBlur(over_bg_dil.astype(np.float32), (0, 0), 2.0) * (1.0 - protect.astype(np.float32))
        plate_bgr = np.clip(
            bgr.astype(np.float32) * (1.0 - blend_m[..., None]) + inpaint_bgr.astype(np.float32) * blend_m[..., None],
            0,
            255,
        ).astype(np.uint8)
        cp = Path(args.clean_plate)
        cp.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2RGB), "RGB").save(cp)

    t_infer = time.time() - t1
    fg_pct = float((full_alpha > 0.5).mean() * 100.0)
    full_face = np.zeros((H, W), dtype=bool)
    full_face[y0:y1, x0:x1] = p_face > 0.5
    full_hw = np.zeros((H, W), dtype=bool)
    full_hw[y0:y1, x0:x1] = p_headwear > 0.5

    if args.json:
        sx1080, sy1080 = 1920.0 / W, 1080.0 / H
        info = {
            "input": str(args.input),
            "output": str(out_p),
            "parts": parts,
            "size": [W, H],
            "fg_percent": round(fg_pct, 3),
            "native_boxes": {
                "part": _box_from_mask(full_alpha > 0.2),
                "face": _box_from_mask(full_face),
                "headwear": _box_from_mask(full_hw),
            },
            "layer1080_boxes": {
                "part": _box_from_mask(full_alpha > 0.2, sx1080, sy1080),
                "face": _box_from_mask(full_face, sx1080, sy1080),
                "headwear": _box_from_mask(full_hw, sx1080, sy1080),
            },
        }
        jp = Path(args.json)
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    extra = f" + clean_plate={Path(args.clean_plate).name}" if args.clean_plate else ""
    print(
        f"part_cutout [{','.join(parts)} | {device}{'/fp16' if use_fp16 else ''}]: "
        f"{Path(args.input).name} -> {out_p.name}{extra} | fg={fg_pct:.2f}% "
        f"(load {t_load:.1f}s, infer {t_infer:.2f}s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
