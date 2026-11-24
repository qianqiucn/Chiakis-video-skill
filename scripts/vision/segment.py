"""segment.py — text-prompted cut-outs using Grounding DINO + SAM 2.1.

Grounding DINO locates each named subject and SAM 2.1 masks it to the pixel. Useful for:
  - 2.5D parallax foreground/background separation (character cut-out vs clean plate)
  - Occlusion masks (kinetic typography passing behind a character's head/arm)
  - Pixel-aligned surgical edits when paired with `scripts/vision/pasteback.py`

Usage:
  python -X utf8 scripts/vision/segment.py <image> "girl. sword. ribbon." <outdir>
        [--box 0.30] [--text 0.25] [--feather 1.2] [--all] [--pick whole|best] [--offline]

Prompt format: lowercase English phrases, each ending with "." (Grounding DINO format).
Writes per phrase: <name>_mask.png (L, soft edge), <name>.png (RGBA cut-out), plus
union_mask.png, preview.jpg (coloured overlay + boxes), and boxes.json.
Requires optional depth/vision packages: `pip install torch transformers`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GD = "IDEA-Research/grounding-dino-tiny"
SAM = "facebook/sam2.1-hiera-tiny"
COLOURS = [
    (255, 80, 80),
    (80, 200, 255),
    (255, 200, 60),
    (120, 255, 120),
    (220, 120, 255),
    (255, 140, 200),
]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "obj"


def main() -> int:
    ap = argparse.ArgumentParser(description="Text-prompted Grounding DINO + SAM 2.1 subject cut-outs")
    ap.add_argument("image", help="Input image path")
    ap.add_argument("prompt", help='Lowercase English phrases ending with ".", e.g. "girl. hat."')
    ap.add_argument("outdir", help="Output directory for masks, RGBA cut-outs, preview.jpg, boxes.json")
    ap.add_argument("--box", type=float, default=0.30, help="Box score threshold (default 0.30)")
    ap.add_argument("--text", type=float, default=0.25, help="Text match threshold (default 0.25)")
    ap.add_argument("--feather", type=float, default=1.2, help="Mask edge blur radius in px (default 1.2)")
    ap.add_argument("--all", action="store_true", help="Keep every detected box, not only the best per phrase")
    ap.add_argument(
        "--pick",
        default="whole",
        choices=("whole", "best"),
        help="whole = largest confident SAM candidate (default); best = highest IoU score (often a sub-part)",
    )
    ap.add_argument("--offline", action="store_true", help="Force offline HuggingFace cache mode (HF_HUB_OFFLINE=1)")
    a = ap.parse_args()

    if a.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"

    try:
        import numpy as np
        import torch
        from PIL import Image, ImageDraw, ImageFilter
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor, Sam2Model, Sam2Processor
    except ImportError as e:
        sys.exit(
            f"segment.py requires optional vision packages ({e}). "
            "Install them with: pip install torch transformers pillow numpy"
        )

    os.makedirs(a.outdir, exist_ok=True)
    prompt = a.prompt.strip().lower()
    if not prompt.endswith("."):
        prompt += "."

    t0 = time.time()
    img = Image.open(a.image).convert("RGB")
    W, H = img.size

    gp = AutoProcessor.from_pretrained(GD)
    gm = AutoModelForZeroShotObjectDetection.from_pretrained(GD).eval()
    inp = gp(images=img, text=prompt, return_tensors="pt")
    with torch.no_grad():
        out = gm(**inp)
    res = gp.post_process_grounded_object_detection(
        out, inp.input_ids, threshold=a.box, text_threshold=a.text, target_sizes=[(H, W)]
    )[0]
    labels = res.get("text_labels", res.get("labels"))
    dets = [(str(l), float(s), [float(v) for v in b]) for l, s, b in zip(labels, res["scores"], res["boxes"])]
    t1 = time.time()

    if not a.all:
        best = {}
        for l, s, b in dets:
            if l not in best or s > best[l][1]:
                best[l] = (l, s, b)
        dets = list(best.values())
    if not dets:
        print("no objects found — lower --box/--text or rephrase the prompt")
        return 1

    sp = Sam2Processor.from_pretrained(SAM)
    sm = Sam2Model.from_pretrained(SAM).eval()
    sin = sp(images=img, input_boxes=[[d[2] for d in dets]], return_tensors="pt")
    with torch.no_grad():
        so = sm(**sin, multimask_output=True)
    allm = sp.post_process_masks(so.pred_masks.cpu(), sin["original_sizes"])[0]  # (n, 3, H, W)
    iou = so.iou_scores.cpu()[0]  # (n, 3)

    if a.pick == "best":
        pick = iou.argmax(-1)
    else:
        area = allm.flatten(2).float().mean(-1)
        ok = iou >= (iou.max(-1, keepdim=True).values - 0.08)
        pick = torch.where(ok, area, torch.full_like(area, -1)).argmax(-1)

    masks = torch.stack([allm[k, pick[k]] for k in range(len(dets))]).unsqueeze(1)
    sam_scores = [float(iou[k, pick[k]]) for k in range(len(dets))]
    t2 = time.time()

    rgba = np.array(img.convert("RGBA"))
    union = np.zeros((H, W), np.uint8)
    prev = img.convert("RGBA")
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(over)
    info, used = [], {}

    for k, (label, score, box) in enumerate(dets):
        m = masks[k, 0].numpy().astype(np.uint8) * 255
        mi = Image.fromarray(m, "L")
        if a.feather > 0:
            mi = mi.filter(ImageFilter.GaussianBlur(a.feather))
        name = slug(label)
        used[name] = used.get(name, 0) + 1
        if used[name] > 1:
            name = f"{name}_{used[name]}"
        mi.save(os.path.join(a.outdir, f"{name}_mask.png"))
        cut = rgba.copy()
        cut[..., 3] = np.array(mi)
        Image.fromarray(cut, "RGBA").save(os.path.join(a.outdir, f"{name}.png"))
        union = np.maximum(union, np.array(mi))
        c = COLOURS[k % len(COLOURS)]
        tint = Image.new("RGBA", img.size, c + (0,))
        tint.putalpha(mi.point(lambda v: int(v * 0.45)))
        over = Image.alpha_composite(over, tint)
        draw = ImageDraw.Draw(over)
        draw.rectangle(box, outline=c + (255,), width=4)
        draw.text((box[0] + 6, box[1] + 4), f"{label} {score:.2f}", fill=c + (255,))
        info.append({
            "name": name,
            "label": label,
            "score": round(score, 3),
            "sam": round(sam_scores[k], 3),
            "box": [round(v) for v in box],
            "area": round(float((np.array(mi) > 127).mean()), 4),
        })

    Image.fromarray(union, "L").save(os.path.join(a.outdir, "union_mask.png"))
    Image.alpha_composite(prev, over).convert("RGB").save(os.path.join(a.outdir, "preview.jpg"), quality=88)
    with open(os.path.join(a.outdir, "boxes.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)

    for d in info:
        print(f"  {d['name']:<18} find {d['score']:.2f}  mask {d['sam']:.2f}  box {d['box']}  area {d['area']:.3f}")
    print(f"{len(info)} cut-outs -> {a.outdir}  (detect {t1 - t0:.1f} s, segment {t2 - t1:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
