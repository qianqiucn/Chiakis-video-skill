"""cutout.py — flagship MIT-licensed high-resolution foreground & anime cutout for Chiaki's-video-skill.

Empirically verified on 2K anime & botanical/prop plates (~0.8-1.0 s/image on RTX GPU FP16):
  - `hr` (default): `ZhengPeng7/BiRefNet_HR` (MIT, native 2048x2048).
    Best universal 2K all-rounder for props, flowers, objects, and clean-edge characters without white-cloth holes.
  - `toonout`: `joelseytre/toonout` (`birefnet_finetuned_toonout.pth` on `ZhengPeng7/BiRefNet`, MIT weights, 1024x1024).
    Best specialist for stylized anime characters on dark/busy painted scenes (preserves glowing VFX wisps & solid white sleeves).
  - `hr-matting`: `ZhengPeng7/BiRefNet_HR-matting` (MIT, native 2048x2048).
    Specialist ONLY for genuinely translucent materials (glass, smoke, bridal veils, real human hair); avoid on solid white anime cloth over dark mist.

Usage:
  python -X utf8 scripts/vision/cutout.py <in.png> <out_rgba.png> [--model hr|toonout|hr-matting]
        [--res 2048] [--mask <out_mask.png>] [--defringe 0.65] [--cpu] [--offline]

Requires optional vision packages: `pip install torch torchvision "transformers<5" timm einops kornia huggingface_hub opencv-python pillow`.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODELS = {
    "toonout": {
        "repo": "ZhengPeng7/BiRefNet",
        "weights_repo": "joelseytre/toonout",
        "weights_file": "birefnet_finetuned_toonout.pth",
        "default_res": 1024,
        "license": "MIT",
    },
    "hr": {
        "repo": "ZhengPeng7/BiRefNet_HR",
        "default_res": 2048,
        "license": "MIT",
    },
    "hr-matting": {
        "repo": "ZhengPeng7/BiRefNet_HR-matting",
        "default_res": 2048,
        "license": "MIT",
    },
}


def _defringe_rgb(rgb_u8, alpha_f32, strength: float):
    """Suppress background colour bleed in semi-transparent boundary pixels (0.02 < alpha < 0.96).

    Computes a local alpha-weighted foreground colour estimate (normalized convolution) and blends it
    smoothly into soft-edge pixels so hair wisps stay crisp on both dark and light backgrounds.
    """
    import cv2
    import numpy as np

    if strength <= 0.0:
        return rgb_u8

    rgb = rgb_u8.astype(np.float32)
    # Weight strongly toward confident interior foreground pixels
    w = np.clip((alpha_f32 - 0.55) / 0.45, 0.0, 1.0) ** 2
    w3 = w[..., None]
    # Multi-scale blur spreads true foreground hue outward into hairline edges
    fg_num = cv2.GaussianBlur(rgb * w3, (0, 0), 5.0)
    fg_den = cv2.GaussianBlur(w, (0, 0), 5.0)[..., None]
    valid = fg_den > 1e-4
    fg_est = np.where(valid, fg_num / np.maximum(fg_den, 1e-4), rgb)

    # Apply only on soft edge band (leave solid interior alpha >= 0.96 untouched)
    edge_band = np.clip((0.96 - alpha_f32) / 0.94, 0.0, 1.0) * (alpha_f32 > 0.01).astype(np.float32)
    mix = (edge_band * float(np.clip(strength, 0.0, 1.0)))[..., None]
    out = rgb * (1.0 - mix) + fg_est * mix
    return np.clip(out.round(), 0, 255).astype(np.uint8)


def _load_model(model_key: str, device: str, use_fp16: bool):
    import torch
    from transformers import AutoModelForImageSegmentation

    cfg = MODELS[model_key]
    if "weights_repo" not in cfg:
        model = AutoModelForImageSegmentation.from_pretrained(cfg["repo"], trust_remote_code=True)
    else:
        from huggingface_hub import hf_hub_download

        model = AutoModelForImageSegmentation.from_pretrained(cfg["repo"], trust_remote_code=True)
        pth = hf_hub_download(repo_id=cfg["weights_repo"], filename=cfg["weights_file"])
        sd = torch.load(pth, map_location="cpu", weights_only=False)
        if isinstance(sd, dict) and "state_dict" in sd:
            sd = sd["state_dict"]
        # Strip DDP (`module.`) and torch.compile (`_orig_mod.`) prefixes cleanly
        clean_sd = {}
        for k, v in sd.items():
            nk = k
            for pref in ("module.", "_orig_mod."):
                if nk.startswith(pref):
                    nk = nk[len(pref):]
            clean_sd[nk] = v
        missing, unexpected = model.load_state_dict(clean_sd, strict=True)
        if missing or unexpected:
            print(f"  [note] {model_key} state_dict: {len(missing)} missing, {len(unexpected)} unexpected keys")

    model.to(device).eval()
    if use_fp16:
        model.half()
    return model


def _infer_alpha(model, pil_rgb, res: int, device: str, use_fp16: bool):
    import numpy as np
    import torch
    from PIL import Image
    from torchvision import transforms

    orig_w, orig_h = pil_rgb.size
    tfm = transforms.Compose([
        transforms.Resize((res, res), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    x = tfm(pil_rgb).unsqueeze(0).to(device)
    if use_fp16:
        x = x.half()

    with torch.no_grad():
        preds = model(x)
        if isinstance(preds, (list, tuple)):
            logits = preds[-1]
        elif hasattr(preds, "logits"):
            logits = preds.logits
        else:
            logits = preds
        prob = logits.sigmoid().float().cpu()[0, 0].numpy()

    alpha_img = Image.fromarray(np.clip((prob * 255.0).round(), 0, 255).astype(np.uint8), mode="L")
    alpha_full = alpha_img.resize((orig_w, orig_h), Image.BILINEAR)
    return np.asarray(alpha_full, dtype=np.float32) / 255.0


def main() -> int:
    ap = argparse.ArgumentParser(description="High-res MIT foreground & anime cutout (BiRefNet_HR / ToonOut / HR-matting)")
    ap.add_argument("input", help="Input RGB image path")
    ap.add_argument("output", help="Output RGBA PNG path")
    ap.add_argument("--model", choices=tuple(MODELS.keys()), default="hr",
                    help="hr (default, 2048px universal/2K props & characters), toonout (1024px anime/FX specialist), or hr-matting (2048px translucent glass/veils)")
    ap.add_argument("--res", type=int, default=0, help="Inference resolution (0 = model default: 2048 or 1024)")
    ap.add_argument("--mask", default="", help="Optional path to save grayscale alpha matte PNG")
    ap.add_argument("--defringe", type=float, default=0.65,
                    help="Foreground edge colour decontamination strength 0..1 (default 0.65; 0 disables)")
    ap.add_argument("--cpu", action="store_true", help="Force CPU execution")
    ap.add_argument("--offline", action="store_true", help="Force offline HuggingFace cache mode")
    a = ap.parse_args()

    if a.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"

    try:
        import numpy as np
        import torch
        from PIL import Image
    except ImportError as e:
        sys.exit(
            f"cutout.py requires optional vision packages ({e}). "
            'Install them with: pip install torch torchvision "transformers<5" timm einops kornia huggingface_hub opencv-python pillow'
        )

    device = "cpu" if a.cpu or not torch.cuda.is_available() else "cuda"
    use_fp16 = (device == "cuda")
    res = a.res if a.res > 0 else MODELS[a.model]["default_res"]

    t0 = time.time()
    img = Image.open(a.input).convert("RGB")
    model = _load_model(a.model, device, use_fp16)
    t1 = time.time()
    alpha = _infer_alpha(model, img, res, device, use_fp16)
    t2 = time.time()

    rgb_u8 = np.asarray(img, dtype=np.uint8)
    if a.defringe > 0:
        rgb_u8 = _defringe_rgb(rgb_u8, alpha, a.defringe)

    alpha_u8 = np.clip((alpha * 255.0).round(), 0, 255).astype(np.uint8)
    rgba = np.dstack([rgb_u8, alpha_u8])

    out_p = Path(a.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(out_p)
    if a.mask:
        mp = Path(a.mask)
        mp.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(alpha_u8, mode="L").save(mp)

    fg_pct = float((alpha > 0.5).mean() * 100.0)
    soft_pct = float(((alpha > 0.05) & (alpha < 0.95)).mean() * 100.0)
    print(
        f"cutout [{a.model} @ {res}px, {device}{'/fp16' if use_fp16 else ''}]: "
        f"{Path(a.input).name} -> {out_p} | fg={fg_pct:.1f}% soft_edge={soft_pct:.2f}% "
        f"(load {t1 - t0:.1f}s, infer {t2 - t1:.2f}s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
