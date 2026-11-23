# Camera Projection onto Proxies — Per-Shot Blender Template

**What it is.** Project an intricate 2D illustration from its own virtual camera onto simple proxy geometry in Blender:
- a depth-displaced plate (walls, far structures, floor);
- vertical alpha cards for separated foreground/midground layers (e.g. near shelves, foreground pillars, character cutout), each standing on the floor plane at its base contact row;
- an additive light card (e.g. breathing window glow);
- volumetric dust quads across 3 depth layers.

Frame 1 reproduces the illustration pixel for pixel, and the camera then performs a true 3D dolly along its axis with real perspective parallax.

**When to use it.** Use camera projection when travelling into an ornate space whose visual detail is specific to the illustration (library book stacks, stained glass, cathedral tracery, hand-painted alleys). For modular/generic spaces where the camera looks around or travels deeply, use a built Blender set dressed via `scripts/assets3d.py` + `scripts/blender/asset_lib.py` (`references/3d.md` §5c).

## Files
Copy this folder to `<project>/blender/<SHOT>/eng/scripts/` (each script resolves the shot folder three levels up):

| File | Run with | Purpose |
|---|---|---|
| `design.py` | `python -X utf8 design.py sim` → `design.py build <y0>` | Camera focal/pitch fit and per-pixel depth `rho` standing vertical structures on one floor plane; writes `eng/rho_plate.npy` & `eng/design.json` (see `example_design.json`) |
| `textures.py` | `python -X utf8 textures.py` | 2× Lanczos upscaled card textures (prevents GPU bilinear softening during 1.15–1.6× push magnification) + RGB window-light masks |
| `shelf_edge.py` | `python -X utf8 shelf_edge.py` (optional) | Fits straight-line anti-aliased alpha along architectural pillar edges so foreground masks never tear as they slide |
| `dolly_scene.py` | `python -X utf8 <skill>/scripts/run_queue.py blender --lane 3d -- blender -b --python dolly_scene.py -- --eng <SHOT>/eng --out <dir> [--frames 1-23 --mblur 0.25 --dust 180 --save-blend scene.blend]` | Builds the exact shader-projected scene and renders 16-bit beauty + mask passes (always queue Blender through `run_queue.py`) |
| `post.py` | `python -X utf8 post.py [render]` (shot-specific) | Linear-light compositing pass (example: window overexposure bloom into a white-flash handoff) |
| `exrio.py` | — | Linear sRGB / 16-bit PNG / OpenEXR helpers |

**Expected inputs in `<SHOT>/`:**
- `scene.png`: original illustration.
- `plate.png`: clean background plate with separated foreground layers painted out.
- Layer RGBA cutouts (e.g. `shelf_L.png`, `shelf_R.png`, `subject.png` / `girl.png`).
- `plate_depth.png`: 16-bit depth map of `plate.png` from `scripts/vision/depth.py`.
- `window_mask.png` (optional): light-source mask if using an additive glow card.

## Per-Shot Adaptation
1. **Recover the painting's camera**: measure converging verticals and horizon row → update `F`, `TH`, `Y_WALL`, `Y_FEET`, `Y_SHELF`, `D_SLOPE`, `Y_H` at the top of `design.py`.
2. **Assign proxies**: decide what stays on the displaced plate vs vertical alpha cards (`vplane()` / `card_mat()` in `dolly_scene.py`).
3. **Simulate first (`design.py sim`)**: pick `y0` from the parallax readout (near layer vs far wall ≥ 20 px), then run `design.py build <y0>`.
4. **Tune travel**: `travel(n)` applies a quartic ease-out along the camera axis. Keep travel modest (typically ≤ 1.4× magnification) so disoccluded areas stay clean.
5. **Sample 2 frames first**: render `--frames 1,23`, inspect full-size for disocclusion seams, then render `--frames 1-N` into `<project>/web/assets/b3d/<ID>/`. Play back frame-for-frame in `lib/sequence.js` (**no** `T3.relX` SINE retime — the curve is already baked into the camera keys).

## Verification Before Handoff
- Frame 1 matches `scene.png` (only negligible resampling diff).
- `scripts/vision/parallax.py` passes on first vs last frame (`>= 20 px` and `>= 15%` share for spatial shots).
- Disoccluded edges at the final frame show clean background texture (no streaks, duplicated limbs/objects, or mirrored kaleidoscope patches).
- Grade, grain, dust, and motion blur match neighbouring 2D shots (`references/house-style.md` §4).
