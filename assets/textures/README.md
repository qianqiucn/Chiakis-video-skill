# Bundled 2D Textures (CC0)

Zero-dependency 2D film grain, dust particles, paper, and washi overlays ready for Canvas 2D / CSS `mix-blend-mode` compositing.

| Folder | Files | Recommended Blend Mode & H.264-Surviving Opacity |
|---|---|---|
| `grain/` | `grain_fine_2048.png`, `grain_film35_2048.png` | `overlay` / `soft-light`, **film35** at `0.14–0.24` (avoid `grain_fine` ≤ `0.08` at 720p — H.264 strips it!), shift/flip per frame |
| `dust/` | `dust_01..04_3840x2160.png` | `screen`, opacity `0.16–0.32`, alternate & rotate on 2s (`T3.twos`) or 4s |
| `paper/` | `Paper001_4K_color.jpg` | **Pre-stretch first!** Raw scan luma sits in `[236..252]` (nearly invisible under naive `multiply`). Run `scripts/prep_texture.py` → `multiply` at `0.24–0.42` |
| `washi/` | `washi_solid_12.png`, `washi_solid_14.png` | `multiply` / `soft-light`, opacity `0.20–0.38`, organic paper/editorial/ink PVs |

## Tactile Visibility & Compression Survival Rules (v1.5.0)
1. **Paper luma trap**: raw scans like `Paper001_4K_color.jpg` have only a 16-level luminance span `[236..252]`. Before wiring into a scene, extract real fiber tooth with:
   ```bash
   python -X utf8 <sk>/scripts/prep_texture.py <sk>/assets/textures/paper/Paper001_4K_color.jpg web/assets/tex/paper_tooth.png --mode paper --size 1920x1080
   ```
2. **Unified `film_texture.js` at `z = 45`**: coat BOTH art (`z = 10`) AND typography (`z = 20`) under one consistent film/paper overlay (`z = 45`, below `*_handoff.js` at `z = 60`), so lettering feels printed on the same physical medium instead of pasted on glass.
   - **Face protection**: mask or gently attenuate heavy paper/dust over character faces (`radialGradient` mask around the face anchor) so grain never looks like skin blemishes.
   - **Stepped-cadence lock**: inside any `Posterize Time` / `12 fps` / `8 fps` passage, drive texture tile offsets and dust swaps from the **stepped frame `T3.twos(f, ...)`**, never raw `f` (`cadence.py` zero-leak rule).
3. **Preserve grain through H.264**: whenever a film relies on 35mm grain or subtle paper tooth, pass **`--grain`** to `scripts/render_fast.mjs` so 720p/1080p/2K bitrates don't smear fine texture into flat banding.

Source & License: CC0 / public domain textures originally curated in `mg-styles-15` (MIT). See root `THIRD_PARTY_NOTICES.md`.
