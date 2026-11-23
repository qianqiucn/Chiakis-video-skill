"""Texture prep for Blender projection cards. Run with `python -X utf8`.
Creates 2x Lanczos upscaled copies of separated layers (keeps painted detail crisp under 1.15-1.6x dolly push
magnification) plus RGB window-light masks (R sharp window, G breathing weight, B soft glow).
Writes eng/tex_plate.png, tex_shelfL.png, tex_shelfR.png, tex_subject.png, tex_win.png."""
import os
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENG = os.path.join(ROOT, "eng")
S = 2


def up(im):
    return im.resize((im.width * S, im.height * S), Image.LANCZOS)


def rgba_up(path, dst):
    im = Image.open(path).convert("RGBA")
    rgb = up(im.convert("RGB"))
    a = up(im.getchannel("A"))
    out = Image.merge("RGBA", (*rgb.split(), a))
    out.save(dst)
    print(dst, out.size)


os.makedirs(ENG, exist_ok=True)
up(Image.open(os.path.join(ROOT, "plate.png")).convert("RGB")).save(os.path.join(ENG, "tex_plate.png"))
rgba_up(os.path.join(ENG, "shelf_L_fix.png"), os.path.join(ENG, "tex_shelfL.png"))   # shelf_edge.py
rgba_up(os.path.join(ENG, "shelf_R_fix.png"), os.path.join(ENG, "tex_shelfR.png"))
sub_src = os.path.join(ROOT, "subject.png") if os.path.exists(os.path.join(ROOT, "subject.png")) else os.path.join(ROOT, "girl.png")
rgba_up(sub_src, os.path.join(ENG, "tex_subject.png"))

w = np.asarray(Image.open(os.path.join(ROOT, "window_mask.png")).convert("L"), np.float32) / 255.0
w = cv2.morphologyEx(w, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
sharp = cv2.GaussianBlur(w, (0, 0), 0.8)
g25 = cv2.GaussianBlur(w, (0, 0), 25)
g80 = cv2.GaussianBlur(w, (0, 0), 80)
breathe = np.clip(np.maximum(sharp, 0.55 * g25 / max(g25.max(), 1e-6) + 0.30 * g80 / max(g80.max(), 1e-6)), 0, 1)
glow = g80 / max(g80.max(), 1e-6) * 0.6 + g25 / max(g25.max(), 1e-6) * 0.4
glow = np.clip(glow, 0, 1)
rgb = np.dstack([sharp, breathe, glow])
img = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), "RGB")
img = up(img)
img.save(os.path.join(ENG, "tex_win.png"))
print("tex_win", img.size)
