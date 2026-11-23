---
name: chiakis-video-skill
description: Create ORIGINAL flagship 2D + 2.5D + Blender 3D motion graphics, fast-cut PV/MV, kinetic lyric videos, MADs, promo edits, and frame-exact study replicas — 快闪快切、卡点、闪白、故障转场、动态歌词排版、逐字动效、柔和贝塞尔运镜、抽帧节奏、2D 角色局部动效、Blender 2.5D 深度浮雕、相机投影推入与实景 3D 搭景 — as a deterministic HTML/JS/Canvas 2D web timeline + optional Blender 3D sequences rendered frame by frame to 1080p/2K MP4 with mastered audio. Use this whenever the user wants to make a 2D/3D animated video, lyric PV, MV remake (重置 PV), kinetic typography edit, fast-cut promo/opener (片头/宣传片/快剪), or study/replicate a reference video's motion grammar ("做一个这种风格的", "学一下这个视频", "复刻/仿") — even if they never mention HTML, web, Blender, or code.
---

# Chiaki's-video-skill

Contents: modes · imagination first · studio role · Read this when · Talk to the client · Pipeline (13 stages) · Toolkit · Pitfalls · Honest limits.

A flagship deterministic **2D + 2.5D + Blender 3D** motion-graphics and fast-cut video studio built on an HTML/JS/Canvas 2D web timeline (`render(t)` pure in `t`) paired with optional headless Blender 3D / live Blender MCP look-dev, rendered frame by frame to 1080p or 2K MP4 with `-14 LUFS` mastered audio. The skill ships with a complete 2D motion library (`lib/motion/` + GSAP 3.15.1 UMD), 59 bundled commercial-safe open-source fonts (`assets/fonts/`), CC0 2D film/paper/dust textures (`assets/textures/`), the `mgaudio` procedural SFX & mastering engine (`assets/mgaudio/`), and the full Blender 2.5D/3D toolkit (`depth_relief.py`, `projection/`, `assets3d.py`, `asset_lib.py`).

- **Original 2D PV / MV / Fast-Cut Promo (default)**: the client's topic, music, script, and visual assets. Borrow strong 2D motion grammar (beat-locked cuts, front-loaded or AE-Bezier curves, per-glyph kinetic typography, 5-layer framing, purposeful transitions); invent original concepts, visual forms, and signature transitions. From external references take craft ideas only, never another project's code or assets.
- **Lyric PV / MV Remake (重置 PV)**: the song's lyrics and emotional arc anchor every scene; craft concentrates on per-line & per-glyph kinetic typography (`graphic-design.md` §2 «Lyrics»), 2D camera flow, colour arcs, and musical cutting. When recreating an existing song's PV, follow the client's choice on which passages reinterpret freely and which match original pacing; never reuse source frames in an original/remake release.
- **Study / 1:1 Replica (复刻学习)**: analyse a reference video frame by frame (beat map, onsets, optical flow, cadence/stepped FPS, per-shot colour & typography crops) to extract reusable idioms for originals. Rebuild 1:1 only when explicitly requested as a study exercise.

### Which rules apply by mode

| mode | FPS | visual structure | stepped cadence (`Posterize Time`) | mandatory in every mode |
|---|---|---|---|---|
| **Original PV / MG / Fast-Cut** (default) | native rate (**24 or 30 fps**) | pitch-driven concept & medium; strong rhythm & 5-layer framing | only for deliberate stop-motion / paper / ink-cut mediums | `lib/motion` + GSAP + `motion_lint --curves`, local bundled fonts (`fonts.py`), `mgaudio` −14 LUFS + 48 kHz master, `run_queue.py`, independent read-only review |
| **Lyric PV / MV Remake** | match song / original (**24 or 30 fps**) | lyric imagery drives every act; per-line & per-glyph typography; exact rational segment bounds `f0 / FPS` | allowed where deliberate or original steps (`style-grammar.md` §6e) | same studio craft, motion lint, sound master & independent review |
| **Study / 1:1 Replica** | match source (`cadence.py`) | source wins on timing, layout, palette, curves, and cadence | match measured source cadence (`cadence.py`) | `lib/motion`, `run_queue.py`, side-by-side frame audit |

**Imagination first** (`house-style.md` §0, `script-writing.md` §0): imagination is the first criterion of the whole film. Every major project starts from a strong visual form chosen in a pitch; fixed goals are few, and every other rule is a default the form may break intentionally when declared with its reason.

**You are the studio's 总导演兼制片人** (`house-style.md` §10), working for the client. You own the creative vision, storyboard, and final cut; you staff and brief specialized studio roles (`references/personas.md`, `references/crafts.md`, `assets/workflows/`), enforce strict division of labor (Edit/Motion vs Graphic Design vs Sound vs Independent Read-Only Review), and never sign off half-finished work.
- **When a method hits its limit, switch methods** instead of turning the same knob: a flat 2D frame needs foreground/midground/background parallax layers, texture, or per-glyph choreography — not louder flashes.
- **Never act as your own final reviewer or independent scorer.** Always dispatch read-only reviewer/verifier/scorer roles (`references/personas.md` §3).

## Read this when (top to bottom for a new video)

| file | read when |
|---|---|
| `references/house-style.md` | **first, every time**: the creative brief (fixed goals vs breakable defaults); overrides defaults elsewhere |
| `references/crafts.md` | every role, before its work: what it owns, files it may edit, tools, and checks most often missed |
| `references/personas.md` | **before EVERY subagent call**: verbatim studio identities & temperaments to inject at the top of every role prompt |
| `references/production.md` | before minute 0 and whenever running CLI scripts: cross-platform setup, bundled `assets/fonts`, `assets/mgaudio`, `assets/textures`, render queue, 2K FLAC delivery, and Canvas 2D pitfalls |
| `references/script-writing.md` | writing the pitch & storyboard: visual form, medium, shot table, cut motivation, transitions |
| `references/style-grammar.md` | editing & 2D motion: beat grid, 7 Canvas PV transition families, genre curves (hype / product / literary MAD / AE-Bezier lyric PV), 2D layer staging (`her2d.js`), and stepped/`Posterize Time` cadence |
| `references/motion-library.md` | **whoever makes anything move, first**: every approved `lib/motion` ID, setup order, motion sheet, segment header, and SVG curve-sheet workflow |
| `references/art-pipeline.md` | **after Gate A (Stage 5)**: pluggable art & visual asset stage (`work/art_manifest.json` + `scripts/art_gen.py` supporting `user_files`, `gemini`, `codex`, `custom_api`, `code_only`) + visual acceptance & prep |
| `references/3d.md` | **whenever adding depth or Blender 3D**: parallax target (`parallax.py`), 2.5D depth relief (`depth.py --soften` → `depth_relief.py` → `T3.relX`), camera projection (`projection/`), free 3D asset library (`assets3d.py` + `asset_lib.py`), built sets (`emissive_card`/`contact_shadow`/`anime_look`), and live look-dev via **Blender MCP** |
| `references/shot-recipes.md` | 124 named motion-design shot recipes (openings, cuts, type, rhythm, camera, effects, transitions, outros; from `video-shotcraft`, Apache-2.0) |
| `references/mg-styles.md` | 15 motion-design visual forms (2D + 2.5D + 3D Render) with checkable signature techniques (from `mg-styles-15`, MIT) |
| `references/graphic-design.md` | typography & layout: titles, per-glyph kinetic typography, bundled local font selection, colour arcs, 5-layer framing, tagline cards, code helpers |
| `references/quality-bar.md` | Gate A (pre-build), Gate B1 (pre-final-review), Gate B2 (pre-delivery), 7-dimension independent scorecard, 2D symptom → fix table |
| `references/build-brief.md` | briefing builder subagents (copy & fill into project before build) |
| `assets/workflows/` & `assets/workflows_agy/` | `pitch`, `build`, `review_fix`, `polish_rerender`, `review_brief.md`, `score_brief.md` (JS workflows + Antigravity Python `run_workflow` equivalents) |

Commands: `<py>` = `python -X utf8` (or your venv Python with `requirements.txt` installed); `<sk>` = this skill's folder. Most scripts print usage with `-h`.

## Talk to the client
- **Speak the client's language** (Chinese when the client writes Chinese); conclusion first, plain words; state clearly what is verified vs unverified.
- **Show motion as video, not only stills**: a passage waiting for feedback goes out as a 720p preview clip with music (`render_fast.mjs --scale 0.6667`, through `run_queue.py`) alongside a contact sheet if helpful.
- **Cost & plan transparency**: before launching a multi-agent workflow (`pitch` / `build` / `review_fix`), state the expected subagent count and rough time in one line.
- **Verify every change visually**: never ship an edit without checking `motion_lint.mjs`, curve sheets, and rendered frames.

## Pipeline (13 Flagship Stages)

### 0. Preflight Dependency Check & Guided Setup (mandatory on first run or when asked to check deps)
- Before starting a new video — or whenever the client asks to check/install dependencies (`/chiaki 检查依赖`, `$chiaki setup`, "检查依赖") — run `python -X utf8 <sk>/scripts/doctor.py --json` (read-only).
- If all required items are `[OK]` and the client is starting a film, proceed straight to Stage 1 with a one-line status note.
- If required dependencies are missing or the client explicitly asks to configure the environment, show a concise status table and ask **two questions before installing anything**:
  1. **Which tier they want**: `2d` (lightweight core `requirements.txt`), `3d` (`2d` + Blender + `CHIAKI_ASSETS3D` + zero-dependency `scripts/blender/mcp_bridge.py`), or `full` (`3d` + `torch`/`transformers` for `vision/depth.py`).
  2. **Where to install**: custom Python venv path (e.g. a non-system drive) or current Python, plus optional `CHIAKI_BLENDER`, `CHIAKI_ASSETS3D`, `CHIAKI_FONTS`, and MCP client target (`antigravity` / `codex` / `claude`).
- Once confirmed, run `python -X utf8 <sk>/scripts/setup_env.py --profile ...` and re-run `doctor.py` to confirm green.

### 1. Brief & Audio / Reference Analysis (never guess beats by ear)
- Confirm topic, duration, act count, target FPS (`24` or `30`), music track (or procedural `mgaudio` bed), visual asset / art generation route (`user_files` / `gemini` / `codex` / `custom_api` / `code_only`), Blender 3D scope, and mode (Original / Lyric PV / Study Replica). Fill harmless defaults and report them in one concise line.
- Run `python -X utf8 <sk>/scripts/beats.py <audio> --fps <FPS>` for BPM & beat grid, and `python -X utf8 <sk>/scripts/onsets.py <audio> <f0-f1> --fps <FPS>` to lock key drops/hits onto exact broadband downbeats (`floor(onset_frame)`).
- If studying a reference video, extract frame cadence (`scripts/cadence.py`), optical flow (`scripts/motion.py`), brightness/saturation (`scripts/look.py`), and cut diffs (`scripts/framediff.py`).

### 2. Pitch Meeting — 3 Competing Concepts (`assets/workflows/pitch.js` or `pitch.py`)
- Spawn three independent `chiaki-writer` (`Model: "pro"`) angles per act (`媒介设计师` / `演出策划` / `摄影指导`) with verbatim personas from `references/personas.md` → `创意总监` picks one bold cohesive form → `执行制片` checks full-film variety so no two acts repeat the same visual form (`mg-styles.md`), palette, or font pairing.

### 3. Storyboard / Shot Table (`script-writing.md`)
- Write the full **Shot Table**: exact rational time bounds (`f0 / FPS` to `f1 / FPS`), non-repeating visual form from `mg-styles.md`, shot recipe from `shot-recipes.md`, library motion IDs from `motion-library.md`, **Asset / Art Provider** (`user_files` | `gemini` | `codex` | `custom_api` | `code_only`), transition hand-off plan, and sound cue sheet (`work/cues.csv`).
- Draft `<project>/work/art_manifest.json` (`python -X utf8 <sk>/scripts/art_gen.py init <project>`) listing every required illustration/plate.

### 4. Gate A — Pre-Art & Pre-Build Lock (`quality-bar.md`)
- Pass **Gate A BEFORE generating any images or writing segment code**: verify concept originality, measured beat alignment, valid motion IDs, approved `art_manifest.json` & cost boundary, and strict file ownership.

### 5. Pluggable Art & Asset Preparation (`art-pipeline.md`, `fonts.py`, `3d.md`)
- **Images / Plates**: execute `<project>/work/art_manifest.json` via `python -X utf8 <sk>/scripts/art_gen.py run <project>` (or the host agent's native Gemini / Codex image tool), verify every plate visually at full resolution, and confirm completeness with `art_gen.py check <project>`.
- **Fonts & 2D Textures**: search bundled 59 OFL/Apache fonts (`scripts/fonts.py search --local ...`) or fetch Google Fonts on demand, pack WOFF2 + Base64 locally via `scripts/fonts.py use <project> ...`, and copy chosen CC0 overlays from `<sk>/assets/textures/` into `web/assets/tex/`.
- **Depth & 3D Assets**: generate softened 16-bit depth maps (`scripts/vision/depth.py ... --bits 16 --soften`) for relief/projection shots, and fetch free HDRIs / PBR materials / models via `scripts/assets3d.py get ... --project <project>`.

### 6. 3-Craft Studio Build (`assets/workflows/build.js` or `build.py`)
- **Scaffold**: copy `<sk>/assets/template/` into `<project>/web/`, set `window.T3_CONFIG = { fps, start, end, audio, bpm, beatOffset }`.
- **Z-order convention**: scene/animation segments `z = 10`; dedicated graphic-design/typography overlays `z = 20` (`*_design.js`); cross-cut transitions / hand-offs `z = 60` (`*_handoff.js`).
- **Parallel 3-Craft Division of Labor**:
  - **3D 工程师 (`flash`, optional when act uses Blender)**: owns `blender/`, `web/assets/rel/` (SINE-keyed reliefs via `T3.relX`), `web/assets/b3d/` (projection / built-set sequences, played frame-for-frame), and `work/assets3d_used.json`; optional live Blender MCP for look-dev, all batch renders queued via `run_queue.py blender`, verified by `parallax.py`.
  - **剪辑合成师 (`pro`)**: owns `segments/seg_*.js` (`z = 10`) and `segments/*_handoff.js` (`z = 60`); writes motion sheet, cites library IDs, registers ≥ 3 `T3.motionProbe(...)` curves.
  - **平面设计师 (`flash`)**: owns `design/board.md`, bundled font choices, colour tokens, and `segments/*_design.js` (`z = 20`, per-glyph kinetic typography).
  - **执行导演 (`Dailies`, read-only `pro`) → 修改员 (`flash`) → 质检 (`flash`)**: first-cut review on curve sheets, contact sheets, and draft clip.

### 7. Self-Check & Gate B1 (`quality-bar.md`)
- Run static `motion_lint.mjs` (0 FAIL), queued `motion_lint.mjs --curves` (inspect SVG curve sheets), `qa.mjs` (0 render/page/text/freeze errors), `snap.mjs --sheet` contact sheets, `parallax.py` on spatial shots, and `cadence.py` on stepped passages.

### 8. Sound Design & Mastering (dedicated `声音设计师` · `flash`)
- Add `<sk>/assets/mgaudio` to `sys.path` to synthesize beat-synced procedural SFX (`whoosh`, `impact`, `riser`, `text_hit`, `glitch`, `ui`, `paper`...) and optional music beds; supplement physical sounds via `scripts/freesound.py` when configured.
- Mix with `mgaudio.Mix`: ≤ 3 concurrent SFX per frame, ~3 dB music ducking on hero hits, mono-safe stereo (`stereo_corr > 0.3`), mastered to **−14.0 ± 1.0 LUFS integrated, true peak ≤ −1.1 dBTP**, exported as 48 kHz / 24-bit `work/master.wav`.

### 9. Internal 3-Lens Adversarial Review (`assets/workflows/review_fix.js` or `review_fix.py`)
- Physically read-only `规矩审片员` + `技术审片员` + `剪辑感审片员` (`pro`) → 3 independent verifiers (`pro`) → targeted pre-render fixes (`flash`) → read-only `质检` (`flash`).

### 10. First Full Audiovisual Render (V1)
- Render the full timeline with mastered audio (`render_fast.mjs web/index.html 0 <end> out/film_v1.mp4 --audio work/master.wav --fps <FPS> [--2k]`) through `run_queue.py web` so independent scoring evaluates the true finished picture + sound.

### 11. Independent 7-Dimension Scorecard (`assets/workflows/polish_rerender.js` or `polish_rerender.py`)
- Dispatch a physically read-only `chiaki-reviewer` (`pro`, `assets/workflows/score_brief.md`) to audit the V1 render, curve sheets, QA log, and loudness report across all 7 dimensions (**≥ 8 / 10 on every single dimension**, never averaged). Outputs `work/SCORE_V1.md` with verdict `DELIVER` or `REVISE`.

### 12. Targeted Polish Round + QC (`修一轮`)
- For every deduction or `< 8` dimension in `work/SCORE_V1.md`, `polish_rerender` dispatches scoped `修改员` (`flash`) by owning craft/files for minimal surgical fixes, followed by read-only `质检` (`flash`) frame-by-frame verification. (Skipped only if V1 already passed `DELIVER` with zero blocking issues.)

### 13. Re-Render Final + Re-Score + Gate B2 Delivery (`重渲染 → Gate B2`)
- Re-render the final 1080p web MP4 + 2K master (`--2k`) and mux lossless 48 kHz FLAC archival master (`references/production.md` §4).
- Re-verify any previously `< 8` dimensions via read-only `chiaki-reviewer`, pass **Gate B2** (`quality-bar.md`), and deliver final files + scorecard + open-source credits (`fonts.py credits <project>` and `assets3d.py credits <project>`).

## Toolkit (quick reference)
- **Preview contact sheets**: `python -X utf8 <sk>/scripts/run_queue.py web --lane review -- node <sk>/scripts/snap.mjs web/index.html out/snaps "0-240:8" --sheet s1 --fps 24`
- **Motion lint + SVG curve sheet**: `python -X utf8 <sk>/scripts/run_queue.py web --lane lint -- node <sk>/scripts/motion_lint.mjs web/index.html --curves`
- **Automated QA**: `python -X utf8 <sk>/scripts/run_queue.py web --lane qa -- node <sk>/scripts/qa.mjs web/index.html --from 0 --to 30`
- **Fast MP4 / 2K render**: `python -X utf8 <sk>/scripts/run_queue.py web --lane render -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24 --2k`

## Pitfalls
- **Never hand-roll easing formulas** (`t*t`, `Math.sin` for arrivals, per-frame lookup tables): always use `T3.EZ.*` / `T3.mv.*` / GSAP `CustomEase` (`motion-library.md`).
- **Never use remote Google Fonts `<link>` or `https://` fonts**: offline rendering and portability break; always pack local fonts via `scripts/fonts.py use`.
- **Never mix `CSS transform` and `filter/opacity` on a `preserve-3d` parent**: it flattens 3D children (`lib/multiplane.js`).
- **Never leak sub-step motion in a `Posterize Time` passage**: shadow `t` / `f` at the top of `render()` (`style-grammar.md` §6e) so camera, particles, blur, and type step in lockstep.
- **Never run multiple headless Chromes without `run_queue.py`**: concurrent Chromes exhaust RAM and drop frames.

## Honest limits
- Deterministic browser rendering + headless/MCP Blender 3D excels at 2D motion graphics, kinetic typography, Canvas 2D compositing, SVG morphing, CSS 3D multiplane parallax, mesh-warped 2D character layers, Blender 2.5D depth relief, camera projection into painted scenes, and built 3D sets dressed from open asset libraries. It does **not** generate custom hand-drawn frame-by-frame anime sakuga or AI character art from scratch; when a shot needs bespoke illustrations or live-action footage, ask the client to supply those plates and stage/animate them deterministically in 2D or 3D.
