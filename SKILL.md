---
name: chiakis-video-skill
description: Create ORIGINAL flagship 2D + 2.5D + Blender 3D motion graphics, fast-cut PV/MV, kinetic lyric videos, MADs, promo edits, and frame-exact study replicas — 快闪快切、卡点、闪白、故障转场、动态歌词排版、逐字动效、柔和贝塞尔运镜、抽帧节奏、2D 角色局部动效、Blender 2.5D 深度浮雕、相机投影推入与实景 3D 搭景 — as a deterministic HTML/JS/Canvas 2D web timeline + optional Blender 3D sequences rendered frame by frame to 1080p/2K MP4 with mastered audio. Use this whenever the user wants to make a 2D/3D animated video, lyric PV, MV remake (重置 PV), kinetic typography edit, fast-cut promo/opener (片头/宣传片/快剪), or study/replicate a reference video's motion grammar ("做一个这种风格的", "学一下这个视频", "复刻/仿") — even if they never mention HTML, web, Blender, or code.
---

# Chiaki's-video-skill

Contents: modes · imagination first · studio role · Read this when · Talk to the client · Pipeline (steps 1–7) · Toolkit · Pitfalls · Honest limits.

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
| `references/3d.md` | **whenever adding depth or Blender 3D**: parallax target (`parallax.py`), 2.5D depth relief (`depth.py --soften` → `depth_relief.py` → `T3.relX`), camera projection (`projection/`), free 3D asset library (`assets3d.py` + `asset_lib.py`), built sets (`emissive_card`/`contact_shadow`/`anime_look`), and live look-dev via **Blender MCP** |
| `references/shot-recipes.md` | 124 named motion-design shot recipes (openings, cuts, type, rhythm, camera, effects, transitions, outros; from `video-shotcraft`, Apache-2.0) |
| `references/mg-styles.md` | 15 motion-design visual forms (2D + 2.5D + 3D Render) with checkable signature techniques (from `mg-styles-15`, MIT) |
| `references/graphic-design.md` | typography & layout: titles, per-glyph kinetic typography, bundled local font selection, colour arcs, 5-layer framing, tagline cards, code helpers |
| `references/quality-bar.md` | Gate A (pre-build), Gate B1 (pre-final-review), Gate B2 (pre-delivery), 7-dimension independent scorecard, 2D symptom → fix table |
| `references/build-brief.md` | briefing builder subagents (copy & fill into project before build) |
| `assets/workflows/` & `assets/workflows_agy/` | `pitch`, `build`, `review_fix`, `review_brief.md`, `score_brief.md` (JS workflows + Antigravity Python `run_workflow` equivalents) |

Commands: `<py>` = `python -X utf8` (or your venv Python with `requirements.txt` installed); `<sk>` = this skill's folder. Most scripts print usage with `-h`.

## Talk to the client
- **Speak the client's language** (Chinese when the client writes Chinese); conclusion first, plain words; state clearly what is verified vs unverified.
- **Show motion as video, not only stills**: a passage waiting for feedback goes out as a 720p preview clip with music (`render_fast.mjs --scale 0.6667`, through `run_queue.py`) alongside a contact sheet if helpful.
- **Cost & plan transparency**: before launching a multi-agent workflow (`pitch` / `build` / `review_fix`), state the expected subagent count and rough time in one line.
- **Verify every change visually**: never ship an edit without checking `motion_lint.mjs`, curve sheets, and rendered frames.

## Pipeline

### 1. Brief
Confirm topic, duration, target FPS (`24` or `30`), music track (or procedural `mgaudio` style), aspect ratio (`1920x1080` default; 2K delivery `2560x1440`), provided visual assets (illustrations, logos, lyrics, stock clips), and mode (Original / Lyric PV / Study Replica). Fill harmless gaps with clean defaults and state them in one concise status line.

### 2. Audio & Reference Analysis (never guess beats by ear)
- Run `python -X utf8 <sk>/scripts/beats.py <audio> --fps <FPS>` to get BPM, beat grid, and top accents.
- For tight drops/hits, run `python -X utf8 <sk>/scripts/onsets.py <audio> <f0-f1> --fps <FPS>` to locate exact broadband downbeats (`floor(onset_frame)`).
- If studying a reference video, extract frame cadence (`scripts/cadence.py`), optical flow / motion speed (`scripts/motion.py`), brightness/saturation (`scripts/look.py`), and cut diffs (`scripts/framediff.py`).

### 3. Pitch & Storyboard (`script-writing.md`)
1. Run the **Pitch Meeting** (`assets/workflows/pitch.js` or `assets/workflows_agy/pitch.py`, or manual `chiaki-writer` roles with verbatim personas from `references/personas.md`): three distinct angles (`媒介设计师` / `演出策划` / `摄影指导`) → `创意总监` picks one bold form → `执行制片` checks pacing & variety across acts.
2. Write the **Shot Table**: exact rational time bounds (`f0 / FPS` to `f1 / FPS`), visual content, 2D layers & motion IDs (`references/motion-library.md`), typography plan, transitions, and sound cues (`cues.csv`).
3. Pass **Gate A** (`quality-bar.md`) before writing segment code.

### 4. Visual Assets, Fonts & Textures
- **Fonts (offline-first, zero remote web fonts)**: search bundled 59 OFL/Apache families via `python -X utf8 <sk>/scripts/fonts.py search --local ...` (or fetch any Google Font via `fonts.py get ...`), then pack subset WOFF2 + Base64 into the project with `python -X utf8 <sk>/scripts/fonts.py use <project> "FamilyA" "FamilyB"`.
- **2D Textures**: copy needed CC0 overlays from `<sk>/assets/textures/` (`grain/`, `dust/`, `paper/`, `washi/`) into `<project>/web/assets/tex/`.
- **2D Layers, 2.5D Relief & Blender 3D**: if the client supplies layered PNGs, wire `T3.her.wave` + `T3.her.warp2` (`lib/meshwarp.js`), `T3.her.eyes`, `T3.multiplane`, or `T3.depth3d`. For optical camera orbit/crane/DOF on a single illustration, render a Blender 2.5D depth relief (`depth.py --soften` → `depth_relief.py` → `T3.sequence` + `T3.relX`). For true camera travel through space, use Blender camera projection (`scripts/blender/projection/`) or a built Blender set dressed via `scripts/assets3d.py` + `scripts/blender/asset_lib.py` (with optional live look-dev via **Blender MCP**; all batch renders queued through `run_queue.py blender`; see `references/3d.md`).

### 5. Build (`assets/workflows/build.js` or `build.py`)
- **Scaffold**: copy `<sk>/assets/template/` into `<project>/web/`, set `window.T3_CONFIG = { fps, start, end, audio, bpm, beatOffset }`.
- **Z-order convention**: scene/animation segments `z = 10`; dedicated graphic-design/typography overlays `z = 20` (`*_design.js`); cross-cut transitions / hand-offs `z = 60` (`*_handoff.js`).
- **Studio Division of Labor**:
  - **3D 工程师 (`3D`, optional when act uses Blender)**: owns `blender/`, `web/assets/rel/` (SINE-keyed reliefs), `web/assets/b3d/` (projection / built-set sequences), and `work/assets3d_used.json`; uses live Blender MCP for interactive look-dev when available, runs all batch renders headless through `run_queue.py blender`, and verifies spatial parallax via `parallax.py`.
  - **平面设计师 (`Design`)**: owns `design/board.md`, bundled font choices, colour tokens, and `segments/*_design.js` (`z = 20`).
  - **剪辑合成师 (`Edit / Motion`)**: owns `segments/seg_*.js` (`z = 10`) and `segments/*_handoff.js` (`z = 60`); writes the inline motion sheet, cites library IDs, registers `T3.motionProbe(...)`, and checks `motion_lint.mjs --curves` + `snap.mjs` before handoff.
  - **执行导演 (`Dailies`, read-only)**: reviews first-cut curve sheets + contact sheets + draft clip; assigns targeted fixes.
- **Gate B1** (`quality-bar.md`): run `qa.mjs` through `run_queue.py` (0 render errors, 0 page errors, 0 bad text, 0 unintended freezes, 0 `motion_lint` FAILs).

### 6. Sound & Mastering (dedicated 声音设计师)
- Add `<sk>/assets/mgaudio` to `sys.path` to synthesize beat-synced procedural SFX (`whoosh`, `impact`, `riser`, `text_hit`, `glitch`, `ui`, `paper`...) and optional music beds; supplement real-world physical sounds with `scripts/freesound.py` if an API key is configured.
- Mix with `mgaudio.Mix`: ≤ 3 simultaneous SFX layers per frame, ~3 dB music ducking on hero hits, mono-safe stereo (`stereo_corr > 0.3`), mastered to **−14 LUFS integrated, true peak ≤ −1.1 dBTP**, exported as 48 kHz / 24-bit `work/master.wav`.

### 7. Final Review, Independent Score & Delivery
- Run **3-lens adversarial review** (`assets/workflows/review_fix.js` or `review_fix.py`): `规矩审片员` + `技术审片员` + `剪辑感审片员` → 3 independent verifiers → targeted `修改员` pass → read-only `质检` verification.
- Render **2K master** (`render_fast.mjs ... --2k`) and optional lossless FLAC remux (`ffmpeg -i video -i master.wav -c:v copy -c:a flac -ar 48000`) plus 720p/1080p web delivery.
- Run **Gate B2** and **Independent 7-Dim Scorecard** (`assets/workflows/score_brief.md` via read-only reviewer; ≥ 8/10 across every dimension).
- Deliver clean files + open-source font & 3D asset credits (`fonts.py credits <project>` and `assets3d.py credits <project>`).

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
