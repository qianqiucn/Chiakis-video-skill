# Studio Craft Cards

Every role reads its craft card here together with its verbatim persona from `references/personas.md` before starting work. Strict file ownership ensures parallel crafts never overwrite one another.

---

## 1. Pitch Team (`chiaki-writer` · Model: `pro`)
- **Roles**: `媒介设计师` (`medium`), `演出策划` (`stage`), `摄影指导` (`lens`), `创意总监` (`choose`), `执行制片` (`slate`).
- **Reread**: `house-style.md` §0–§2, `script-writing.md`, `mg-styles.md`, `shot-recipes.md`.
- **Owns**: `<project>/work/pitch/*.md` only (never edits `.js`, `.html`, or audio files).
- **Done looks like**: concrete visual medium, colour arc, bundled font pairing suggestion, shot-by-shot visual rhythm, and explicit creative risks — never vague mood adjectives without a concrete 2D execution mechanism.

---

## 2. Editing & 2D Motion (`chiaki-builder` · Model: `pro`)
- **Role**: `剪辑合成师` (primary motion choreographer & compositor).
- **Reread**: `house-style.md` §4–§6, `style-grammar.md`, `motion-library.md`, `shot-recipes.md`, `build-brief.md`.
- **Owns**:
  - `work/motion_<key>.md` (written BEFORE coding)
  - `web/segments/seg_<key>.js` (`z = 10`) and `web/segments/<key>_handoff.js` (`z = 60`)
  - NEVER modifies `web/index.html` (director owns registration), `*_design.js`, or another act's segments.
- **Tools**: `motion_lint.mjs`, `snap.mjs`, `render_fast.mjs` (via `run_queue.py`), `beats.py`, `onsets.py`.
- **Most often missed checks**:
  1. First 15 lines carry `// motion-sheet:` and `// motion:` with valid IDs from `motion-library.md`.
  2. At least 3 `T3.motionProbe(...)` calls registered in `init()` sharing the exact pose functions called in `render(t)`.
  3. Landed elements carry `move.settle` or live ambient `move.drift` (no dead freezes unless deliberate `Posterize Time`).
  4. Fast slides/whips use `T3.blur.shutter`; stepped passages shadow `f = T3.twos(...)` at entry so zero full-rate grain/drift leaks through.
  5. Static `motion_lint.mjs` passes with 0 FAIL and `--curves` SVG sheet is visually checked before handoff.

---

## 3. Graphic Design & Typography (`chiaki-builder` · Model: `flash`)
- **Role**: `平面设计师` (typography, layout hierarchy, graphic framing, tagline/title systems).
- **Reread**: `house-style.md` §2–§3, `graphic-design.md`, `motion-library.md`, `build-brief.md`.
- **Owns**:
  - `design/board_<key>.md` (typography specs, colour tokens, safe margins, 5-layer framing notes)
  - `work/motion_<key>_design.md`
  - `web/segments/<key>_design.js` (`z = 20`)
  - Bundled font packing via `python -X utf8 <sk>/scripts/fonts.py use <project> ...` (coordinated with director on `index.html`).
- **Most often missed checks**:
  1. Zero remote fonts (`https://`); all fonts local via `fonts.py use`, and `T3.fonts.missing()` checked for every CJK/JP character.
  2. Outlined/hollow display text uses `fonts.py use ... --static` to eliminate variable-font internal contour seams.
  3. Fast-cut lyric PVs animate per glyph (`T3.mv.chars`, `SplitText`, or Canvas per-char) instead of sliding whole text blocks.
  4. Text clears faces/focal subjects and reads cleanly at phone scale (720p contact sheet).

---

## 4. Sound Design & Mastering (`chiaki-builder` · Model: `flash`)
- **Role**: `声音设计师` (procedural SFX, optional recorded SFX, beat-synced mixing, −14 LUFS mastering).
- **Reread**: `house-style.md` §1, `production.md` «Audio (`mgaudio` & Freesound)», `assets/mgaudio/README.md`.
- **Owns**: `work/make_audio.py`, `work/master.wav`, `work/audio_report.txt` (reads `work/cues.csv` from storyboard).
- **Most often missed checks**:
  1. Pass exact visual event timestamps (`m.sfx(sound, at=t)`) — `mgaudio` aligns sync points automatically (do not double-offset whooshes/risers).
  2. ≤ 3 concurrent SFX per frame; ~3 dB music ducking on hero hits; tonal SFX keyed to the music chord.
  3. Integrated loudness **−14.0 ± 1.0 LUFS**, true peak **≤ −1.1 dBTP**, stereo correlation **> 0.3** (mono-safe).

---

## 5. Production Assistant (`chiaki-builder` · Model: `flash_lite`)
- **Role**: `制片助理` (mechanical scaffolding, beat/onset tables, texture copying, batch contact sheets).
- **Owns**: mechanical data prep scripts and contact sheets assigned by the director; never alters creative decisions or motion curves.

---

## 6. Independent Review, Verification, QC & Scoring (`chiaki-reviewer` · physically read-only)
- **Roles**:
  - `执行导演` (first-cut dailies, Model `pro`)
  - 3 Final Review Lenses (`规矩审片员`, `技术审片员`, `剪辑感审片员`, Model `pro`)
  - 3 Independent Verifiers (`规矩复核员`, `技术复核员`, `剪辑感复核员`, Model `pro`)
  - `质检` (post-fix recheck, Model `flash`)
  - `独立成片评分员` (7-dimension scorecard via `score_brief.md`, Model `pro`)
- **Reread**: `house-style.md`, `quality-bar.md`, `style-grammar.md`, `REVIEW_BRIEF.md` / `SCORE_BRIEF.md`.
- **Hard boundary**: physically **cannot edit project code**. Every finding must cite exact frame numbers/timestamps, measured metrics or visual evidence, and an actionable fix assigned to the owning craft.

---

## 7. 3D & Depth — Blender 2.5D Relief, Projection & Built Sets (`chiaki-builder` · Model: `flash`)
- **Role**: `3D 工程师` (Blender depth relief, camera projection, built sets, optical mechanisms, and optional live look-dev via Blender MCP).
- **Reread**: `3d.md` (full), `house-style.md` §4 & §7, `production.md` §3 «3D & Blender».
- **Owns**:
  - `<project>/blender/` (Blender shot scripts, `design.json`, `.blend` files)
  - `<project>/web/assets/rel/<ID>/` (SINE-keyed `depth_relief.py` sequences, played via `T3.relX`)
  - `<project>/web/assets/b3d/<ID>/` (per-frame curved camera projection & built-set sequences, played frame-for-frame)
  - `<project>/work/assets3d_used.json` (borrowed 3D asset credits via `scripts/assets3d.py get ... --project`)
  - NEVER edits `.js` segment files or `web/index.html`.
- **Tools**: `scripts/vision/depth.py`, `scripts/vision/parallax.py`, `scripts/blender/depth_relief.py`, `scripts/blender/projection/*`, `scripts/assets3d.py`, `scripts/blender/asset_lib.py`, `scripts/run_queue.py blender`, optional live **Blender MCP** (look-dev only).
- **Most often missed checks**:
  1. Render 2–3 sample frames (first + last) and inspect full-size before batch rendering a sequence.
  2. Always queue headless `blender -b` commands through `scripts/run_queue.py blender`; use live Blender MCP for interactive look-dev only (never batch renders), and never `taskkill /IM blender.exe`.
  3. Run `scripts/vision/parallax.py` on every spatial shot (`>= 20 px` and `>= 15 %` share) and report camera constants + measured parallax.
  4. Never mix `T3.relX` onto `b3d/` sequences (already curve-keyed) and never skip `T3.relX` on `rel/` sequences (SINE-keyed).
  5. Record every Poly Haven / ambientCG / Sketchfab / BlenderKit asset with `--project` so `assets3d.py credits` is complete.
