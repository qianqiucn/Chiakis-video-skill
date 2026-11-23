# 2.5D Depth Relief & Parallax (`depth_relief.py`, `multiplane.js`, `depth3d.js`)

Bring still 2D illustrations, manga panels, posters, and backgrounds to life with real depth parallax and optical depth of field — without building full 3D assets.

## 1. Choosing the Right 2.5D Method

| Shot Need | Best Tool | Why |
|---|---|---|
| Separated PNG layers (BG + subject + FG) | `assets/template/lib/multiplane.js` (`cam.multiplane`) | Zero offline render, true clean occlusion edges when layers slide |
| Subtle real-time WebGL2 push on 1 image | `assets/template/lib/depth3d.js` (`cam.depth3d`) | Instant browser render, keep `x/y <= 0.04`, `dolly <= 0.15` |
| **Rich camera orbit / crane / macro DOF on 1 illustration** | **`scripts/blender/depth_relief.py`** (`cam.orbit-crane`) | Real 50 mm optical camera + aperture DOF (`--dof 0.20–0.35`) + smooth high-subdiv relief rendered to PNG sequence for `lib/sequence.js` |
| Soft character motion (hair, veil, blink) | `assets/template/lib/motion/her2d.js` + `lib/meshwarp.js` | Keep camera gentle; animate hair/veil/eyes directly in 2D (`style-grammar.md` §6d) |

## 2. Blender Relief Workflow (3 Commands)

### Step A — Pixel-aligned depth map (`scripts/vision/depth.py`)
```bash
# Requires: pip install torch transformers Pillow opencv-python
python -X utf8 scripts/vision/depth.py art.png work/art_depth_soft.png --bits 16 --model small --soften
```
- `--bits 16` eliminates contour stair-stepping in Blender displacement.
- `--soften` applies median-7 + Gaussian-5 blur so sharp depth jumps do not tear like a rubber sheet at silhouettes.
- Never use AI-painted depth maps (misaligned outlines cause halos); always generate pixel-aligned depth via `depth.py`.

### Step B — Headless Blender Relief Render (`scripts/blender/depth_relief.py`)
Always run through `scripts/run_queue.py blender`:
```bash
python -X utf8 scripts/run_queue.py blender --lane relief -- \
  blender -b --python scripts/blender/depth_relief.py -- \
  --image art.png --depth work/art_depth_soft.png --out web/assets/rel/shot01 \
  --frames 48 --fps 24 --orbit -8 --crane 4 --target-uv 0.5,0.45 --push 0.08 --strength 0.30 --dof 0.28 --subdiv 8
```
- **Camera numbers & safe limits**:
  - **Orbit / crane (`--orbit`, `--crane`)**: start at `±6°–9°` (`--overscan 1.15` keeps edges covered up to `|orbit| <= 16°` and `|crane| <= 16°`). Put `--target-uv` on the **near subject** (`--target-depth auto`) so the subject stays grounded while the background slides past.
  - **Push + truck (inserts / macro props)**: `--push 0.25–0.35 --truck 0.08–0.12 --dof 0.25` (real visible DOF on this 2-unit plane starts around `f/0.20–0.35`; `f/2.8` is nearly sharp everywhere).
  - **Displacement strength**: keep `--strength 0.22–0.35`; if a shot looks flat, add a blurred foreground element or split onto `lib/multiplane.js` instead of cranking `--strength` past `0.4`.
  - **Colours**: `depth_relief.py` sets `view_transform = "Standard"` so illustration colours match verbatim with zero Filmic/AgX tone shift.
  - **Speed**: Eevee renders ~0.3 s/frame at 1080p after shader warmup; `--engine cycles` auto-detects `OPTIX`, `CUDA`, `METAL`, `HIP`, or `ONEAPI`.

### Step C — Verify Real Parallax (`scripts/vision/parallax.py`)
```bash
python -X utf8 scripts/vision/parallax.py web/assets/rel/shot01/f001.png web/assets/rel/shot01/f048.png \
  --depth work/art_depth_soft.png --out work/parallax_check.jpg
```
- **Target for spatial shots**: ≥ **20 px** subject-vs-background separation and ≥ **15 %** of total frame motion over ~23 frames (`exit 0 = PASS`). Inserts and gentle holds are exempt.

## 3. Frame-Exact Playback & Retiming (`lib/sequence.js` + `T3.relX`)
`depth_relief.py` keys camera travel with Blender's SINE ease-in-out (`u = (1 - cos(pi * k)) / 2`).
- Load `lib/sequence.js` and enable fractional blending (`frac: true`) so the relief never parks or stutters when retimed onto any `T3.EZ` curve:
```js
const rel = T3.sequence(layer, { dir: 'assets/rel/shot01', count: 48, ext: 'png', blend: 'normal', frac: true });
// In render(t): drive desired progress s via T3.EZ, then undo Blender's SINE with T3.relX (time.relief):
const s = T3.EZ.at(f, f0, dur, 'p4out');
rel.render(T3.relX(s, 48));
```
- Keep foreground overlays/particles moving in the **same direction** as the relief camera (faster for nearer depth). Never stack a large CSS 2D zoom/pan on top of a relief sequence — it dilutes the perceived parallax share.
