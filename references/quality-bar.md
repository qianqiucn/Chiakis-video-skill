# Quality Bar — Gates, Independent Scorecard & 2D Symptom-to-Fix

## Gate A — Before Art Generation & Building (Storyboard Lock)
Verify all five items **before generating images or spawning build crafts** (prevents wasted API credits and rework):
1. **Clear visual identity**: one cohesive non-repeating visual medium (`mg-styles.md`), palette, and bundled font pairing per act (`script-writing.md` §0–§1).
2. **Exact audio alignment**: all major cuts, chorus drops, and lyric entries map to measured frame indices from `beats.py` / `onsets.py` using exact rationals `f0 / FPS`.
3. **Every move grounded in `motion-library.md` & `shot-recipes.md`**: shot table specifies library IDs, shot recipe, curve family (`style-grammar.md` §6b), and intentional stepped zones (`§6e`) if any.
4. **Approved art & asset manifest (`art-pipeline.md`)**: `work/art_manifest.json` declares the provider (`user_files` | `gemini` | `codex` | `custom_api` | `code_only`) for every shot, with any paid external image API explicitly authorized by the client.
5. **Clear file ownership**: brief separates `blender/` + `rel/` + `b3d/` (3D), `seg_*.js` / `*_handoff.js` (Edit), `*_design.js` / `board.md` (Design), and `make_audio.py` (Sound).

## Gate B1 — Before Final Review (Automated Mechanical + Curve Check)
Run through `run_queue.py`:
```bash
python -X utf8 <sk>/scripts/run_queue.py web --lane qa -- node <sk>/scripts/qa.mjs web/index.html --from <start> --to <end>
```
Every item must pass before dispatching the 3-lens final review:
- **0 render errors & 0 page errors** across every frame of the timeline.
- **0 broken text** (`NaN`, `undefined`, `null`, missing glyphs via `T3.fonts.missing`).
- **0 unintended black or frozen stretches** (except declared dramatic holds or `Posterize Time` steps).
- **0 `motion_lint.mjs` FAILs**: all `// motion:` IDs valid, no hand-rolled ease functions, ≥ 3 `T3.motionProbe` curves per segment, SVG curve sheet inspected (`Q1`, peak velocity, settle, no accidental plateaus).
- **Font check clean**: `T3.fonts.report()` shows every packed local font `status: 'loaded'`, zero remote web font requests.

## Gate B2 — On Mastered Final Delivery (After Re-Render & Re-Score)
1. **Video spec**: exact duration, exact target FPS (`24` or `30`), `yuv420p` BT.709 color tags, clean `+faststart` MP4 (1080p/720p web + 2K `2560x1440` master).
2. **Audio spec**: 48 kHz stereo (FLAC on 2K archival master / 192–320k AAC on web MP4), integrated loudness **−14.0 ± 1.0 LUFS**, true peak **≤ −1.0 dBTP**, mono correlation **> 0.3**, zero clipping or boundary pops.
3. **Stepped-cadence & 3D parallax verification**: `cadence.py` MAD scan confirms zero leaked full-rate noise inside `Posterize Time` zones (`style-grammar.md` §6e), and `parallax.py` confirms spatial 3D shots pass (`>= 20 px`, `>= 15%`).
4. **Independent score & polish sign-off**: every dimension on the independent 7-dim scorecard is **≥ 8 / 10** (after the Stage 12 polish round + QC + Stage 13 re-render if V1 had deductions), plus full-res & phone-scale contact sheet check.
5. **Open-source credits ready**: both `python -X utf8 <sk>/scripts/fonts.py credits <project>` and `python -X utf8 <sk>/scripts/assets3d.py credits <project>` (if 3D assets used) included with delivery.

## Scorecard — Independent 7-Dimension Audit (Before Delivery)
Executed by a **physically read-only `chiaki-reviewer`** using `assets/workflows/score_brief.md` (never self-scored by the main thread). **Target: ≥ 8 / 10 on every single dimension** (do not average away a weak dimension):

| # | Dimension | What earns ≥ 8 / 10 | Automatic ≤ 6 failure triggers |
|---|---|---|---|
| 1 | **Concept & Originality** | Memorable visual medium & coherent design language throughout | Generic slideshow templates, random disconnected effects |
| 2 | **Motion & Curves** | Clean SVG curve sheets, expressive genre curves, crisp settle, zero stiffness | Hand-rolled linear ramps, dead stops after landings, abrupt velocity corners |
| 3 | **Rhythm & Editing** | Cuts lock to measured downbeats; strong tension/release & motivated hand-offs | Off-beat cuts, monotonous uniform shot lengths, jarring unmotivated wipes |
| 4 | **Typography & Graphic Design** | Expressive bundled fonts, clear hierarchy, per-glyph craft, clean safe margins | System fallback fonts, colliding text, unreadable phone-scale captions, slide-deck bars |
| 5 | **Visual Depth & Composition** | True 5-layer framing, harmonious colour arc, crisp textures & lighting | Flat single-layer graphics, harsh unmotivated neon, messy clutter |
| 6 | **Sound & Sync** | Clean `-14 LUFS` mix, crisp physical/procedural SFX synced to visuals, dynamic ducking | Missing SFX, muddy overlapping noise (> 3/f), clipping, out-of-sync hits |
| 7 | **Technical Craft** | 0 errors, clean BT.709 encode, zero aliasing/clipping/cadence leaks | Render glitches, broken fonts, leaked 30 fps grain inside 12 fps stepped shot, frozen frames |

## Symptom → Fix (2D Motion Troubleshooting)

| Symptom | Root Cause | Direct Fix |
|---|---|---|
| Motion looks stiff / PowerPoint-like | Symmetric ease on arrivals, dead stop after landing, or uniform stagger | Switch arrival to `T3.EZ.snap` (hype) or soft AE Bezier (`style-grammar.md` §6b), add `T3.mv.settle`, use shrinking `T3.mv.stagger` |
| Kinetic lyrics feel clunky / blocky | Whole sentence animated as one rigid bounding box | Split per glyph (`SplitText` or Canvas `measureText` per char), stagger 1–3 f with individual baseline/scale/blur (`graphic-design.md` §5) |
| Fast whip pan / camera throw strobes | Crisp unblurred frames jumping > 40 px/f | Wrap moving draw call in `T3.blur.shutter` (5-tap 180° or 10-tap 360° opaque) |
| `preserve-3d` multiplane looks flat | `opacity`, `filter`, or `overflow: hidden` set on the 3D world container | Move `opacity` / `filter` onto individual child planes (`lib/multiplane.js` header) |
| Semi-transparent hair/veil warp shows triangle seams | Single-pass `meshwarp` overlaps soft alpha edges | Use `T3.her.warp2` two-pass premultiplied + `1 - alpha` composite (`lib/motion/her2d.js`) |
| `Posterize Time` stepped shot still looks smooth/noisy | Grain, bokeh, camera shake, or lyrics still reading raw `f` | Shadow `f = T3.twos(f, anchor, { n: T3.FPS / targetFps, end })` at the very top of the shot function (`style-grammar.md` §6e) |
| Outlined/hollow text has ugly internal stroke overlaps | Variable font stroked directly | Pack a static merged cut via `python -X utf8 scripts/fonts.py use <project> "Font:900" --static` |
| Render produces wrong fallback font | Remote font blocked or missing glyphs in CJK subset | Run `scripts/fonts.py use <project>` after final text edits; check `T3.fonts.missing()` |
| Cut feels 1–2 frames late behind the beat | Rounded to coarse BPM grid instead of broadband transient | Run `scripts/onsets.py` around the hit and cut on `floor(onset_frame)` |
