---
name: chiakis-video-skill
description: Create ORIGINAL flagship 2D + Three.js Stylized Graphic-3D + Blender Cinematic 3D motion graphics, fast-cut PV/MV, kinetic lyric videos, MADs, promo edits, and frame-exact study replicas — 快闪快切、卡点、闪白、故障转场、动态歌词排版、逐字动效、Three.js 真 3D 挤出中/日/英立体字、角色 Z 夹心 3D 歌词环、3D 歌词走廊、实时色散玻璃棱镜、3D 百叶窗转场、柔和贝塞尔运镜、抽帧节奏、2D 角色局部动效、Blender 2.5D 深度浮雕、相机投影推入与实景 3D 搭景 — as a deterministic HTML/JS/Canvas 2D + WebGL Three.js timeline + optional Blender 3D sequences rendered frame by frame to 1080p/2K MP4 with mastered audio. Use this whenever the user wants to make a 2D/3D animated video, lyric PV, MV remake (重置 PV), kinetic typography edit, fast-cut promo/opener (片头/宣传片/快剪), or study/replicate a reference video's motion grammar ("做一个这种风格的", "学一下这个视频", "复刻/仿") — even if they never mention HTML, web, Three.js, Blender, or code.
---

# Chiaki's-video-skill

Contents: modes · imagination first · studio role · Read this when · Talk to the client · Pipeline (13 stages) · Toolkit · Pitfalls · Honest limits.

A flagship deterministic **2D + Three.js Stylized Graphic-3D + Blender Cinematic 3D** motion-graphics and fast-cut video studio built on an HTML/JS/Canvas 2D + WebGL Three.js timeline (`render(t)` pure in `t`) paired with headless Blender 3D / live Blender MCP look-dev, rendered frame by frame to 1080p or 2K MP4 with `-14 LUFS` mastered audio. **Both Three.js Stylized Graphic-3D and Blender Cinematic 3D are flagship-quality standards freely selectable by the client** (`全能双 3D 旗舰` / `Three.js 风格化 3D` / `Blender 电影级 3D` / `纯 2D` in `docs/PROMPT_TEMPLATE.md`). The skill ships with a complete 2D motion library (`lib/motion/` + GSAP 3.15.1 UMD), **`lib/look_fx.js`** (per-shot tactile coat, cached print-plate shaders, live-footage `lumaMatte` transitions, OKLCH `okMix` ground-walks & monotone vocal splines), bundled offline **Three.js r160 (MIT) + `lib/three_kit.js`** + offline CJK/JP/Latin 3D glyph extractor (`fonts.py glyph3d`), 59 bundled commercial-safe open-source fonts (`assets/fonts/`), CC0 2D film/paper/dust textures (`assets/textures/`), the `mgaudio` procedural SFX & mastering engine (`assets/mgaudio/`), and the full Blender 2.5D/3D toolkit (`depth_relief.py`, `projection/`, `assets3d.py`, `asset_lib.py`).

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

### 宿主多模态死规矩与能力声明（Hard Rule: Host Capability Declaration & Multimodal Split）
- **启动时显式声明本宿主审片通道**：每个工程启动及每份审片/交付报告顶部，必须注明本宿主实际支持的审片能力（`playback` 原生带声视频播放 / `stills` 抽帧与接触表 / `metrics` 曲线·响度·频谱数值），并在结论旁标注证据来源，方便 Antigravity / Claude Code / Codex / WorkBuddy 等任意宿主透明对齐。
- **Gemini 宿主（Antigravity 等原生音视频多模态模型 · `playback+stills+metrics`）**：**必须直接用 `read_file` 原生多模态直听音频（原曲 / `vocal_spec.py --wav-only` 微切片 `.wav`）并直看带声渲染视频（720p/1080p `.mp4` 或分幕 10–25 s 片段）** 来锁人声起唱、审一版看样、三视角终审、复核与独立 7 维评分；`beats.py`/`onsets.py` 与 `snap.mjs` 仅作帧号校验与单帧像素查错，**严禁在 Gemini 上跳过直看带声视频、只靠静态拼图或频谱图打分/签字**！
- **Claude / Codex / WorkBuddy 等图像+文本宿主（`stills+metrics`）**：走**传统频谱分析 + 密集截图 + 曲线/数值路线** —— 用 `beats.py` + `onsets.py` + `vocal_spec.py`（高反差帧号 300 Hz–4 kHz 人声声谱图 `spec_*.png`）锁音轨，用 `snap.mjs --sheet`（含每个转场 `cut-1/cut/cut+1` 帧对与字幕停留中帧）+ `motion_lint.mjs --curves` SVG 曲线图 + `cadence.py` / `parallax.py` / `qa.mjs` 审片与评分。
- **Gemini / Antigravity（AGY）专属导演与审美纪律（Claude Opus 豁免 · 详见 `rules/AGENTS.md` §4–§5 & `references/production.md` §7）**：仅约束 Gemini 模型 / AGY 默认会话（Claude Opus 天然严谨，完全豁免）：① > 30 s 中长片先死磕 **10–16 s Gate A 黄金样板**过审再抽共享引擎铺全片；② Swarm 开工前先落共享视觉着色/世界坐标引擎，工人先交「因为…所以…」因果分镜再写代码；③ 锁 1 根紧扣主题的核心视觉物理主线，严禁对 `three_kit.js` / 装饰贴纸集邮打卡；④ 动态歌词 PV 允许单幕单画布融合「世界物件 + 文字」，禁止凭空 `alpha → 0` 淡出；⑤ 验图走五指/地标挑错清单，看片必配 `scripts/visual_metrics.py` 测饱和度、实黑占比与 `motion_wave.png` 波形；⑥ 汇报只写事实与实测数字，禁用「完美/彻底/100%」等自夸词；⑦ 把 Skill 当零件军火库（逐镜 `T3.look.coat` + `bakePrint`、实拍素材优先当 `T3.look.lumaMatte` 因果转场、真快门 `T3.blur.shutter` + OKLCH `T3.look.okMix`）；⑧ Swarm 指挥遵循「大改先 `kill` 清上下文、1 幕 1 全栈单画布、分镜跨幕查重 + `open.actN` 纯函数预调用契约、总导演集中出图 + 占位并行 + 交图使用说明书、3–6 行去情绪公屏短帖」。

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
| `references/benchmark-quality.md` | **objective flagship quality yardstick** (content-free telemetry bands): `Q1` curve range, 5-act cut/energy bell curve, `≥ 92%` living-motion ratio, contrast/edge-density sweet spots, cutout ratios, and `−14.0 LUFS` mastering baseline |
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
- If all required items are `[OK]` and `studio_memory.initialized` is `true` (or the client already specified a memory switch in their prompt), proceed straight to Stage 1 with a one-line status note.
- If `studio_memory.initialized` is `false` on a brand-new user's first run (and their prompt did not specify a switch), ask once alongside any needed setup questions whether they want Studio Self-Iteration Memory enabled (`ask` default / `auto` / `readonly` / `off`) and save it via `scripts/memory.py mode <mode>` (never re-ask on subsequent runs).
- If required dependencies are missing or the client explicitly asks to configure the environment, show a concise status table and ask **three questions before installing anything**:
  1. **Which tier they want**: `2d` (core `requirements.txt` + vocal/drum stem separation `audio-separator` & `faster-whisper`; pass `--no-stems` for ultra-slim ~180 MB pure 2D), `3d` (`2d` + Blender + `CHIAKI_ASSETS3D` + zero-dependency `scripts/blender/mcp_bridge.py`), or `full` (`3d` + PyTorch vision stack for `vision/cutout.py`, `vision/part_cutout.py` & `vision/depth.py`).
  2. **Where to install**: custom Python venv path (e.g. a non-system drive) or current Python, plus optional `CHIAKI_BLENDER`, `CHIAKI_ASSETS3D`, `CHIAKI_FONTS`, `CHIAKI_STEM_MODELS` / `CHIAKI_STEM_PYTHON` (reuses an existing `audio-separator`/`demucs` venv or keeps RoFormer/Whisper weights off C:), `HF_HOME`, and MCP client target (`antigravity` / `codex` / `claude`).
  3. **Studio self-iteration memory (`~/.chiaki-studio/` or custom `CHIAKI_MEMORY_DIR`)**: `ask` (default: ≤ 5-line confirmation card after each film), `auto` (auto-record after Gate B2), `readonly`, or `off`.
- Once confirmed, run `python -X utf8 <sk>/scripts/setup_env.py --profile ... [--stem-models ... --stem-python ... --hf-home ... --memory-mode ... --memory-dir ...]` (auto-detects NVIDIA GPU → CUDA `cu128` PyTorch + `audio-separator[gpu]` + `faster-whisper`, plus `transformers<5` + `huggingface_hub<1` on `full`) and re-run `doctor.py` to confirm green.

### 1. Brief & Dual-Stem Audio / Vocal / Reference Analysis (never guess beats or vocals)
- Confirm topic, duration, act count, target FPS (`24` or `30`), music track (or procedural `mgaudio` bed), **audio strategy** (`pure_song` default for song/lyric PVs vs `full_sfx` for promos/openers/original scores), visual asset / art generation route (`user_files` / `gemini` / `codex` / `custom_api` / `code_only`), **3D engine specification** (client's choice from `docs/PROMPT_TEMPLATE.md`: `全能双 3D 旗舰` co-starring Three.js Stylized Graphic-3D + Blender Cinematic 3D | `Three.js 风格化 3D` | `Blender 电影级 3D` | `纯 2D`), **self-iteration memory switch** (`ask` default | `auto` | `readonly` | `off`), and delivery cadence (720p review first → 2K FLAC final). When memory switch ≠ `off`, run `python -X utf8 <sk>/scripts/memory.py context --stage brief` to recall durable user defaults (explicit brief entries always override). Fill harmless defaults and report them in one concise line.
- **Dual-Stem Split FIRST (mandatory for ANY vocal song PV / lyric MV before locking beats or lyrics)**:
  - Run `python -X utf8 <sk>/scripts/stem_sync.py <audio> --out <proj>/work/stems --fps <FPS> [--lyrics <proj>/work/lyrics.txt --whisper --lang <ja|zh|en|auto>]` right at the start of Stage 1 to isolate pure dry vocals (`work/stems/vocals.wav`) and pure instrumental (`work/stems/instrumental.wav`). Skip only on pure-instrumental / non-vocal tracks.
  - **Lock drums/beats on pure `instrumental.wav`** (zero vocal bleed!): run `scripts/beats.py work/stems/instrumental.wav --fps <FPS>` + `scripts/onsets.py work/stems/instrumental.wav <f0-f1> --fps <FPS>` and inspect `work/stems/kick_grid.json` `drift_warnings` so section-level BPM shifts (e.g. Chorus 2 vs Finale) are caught BEFORE storyboarding.
  - **Lock sung lyrics on pure `vocals.wav` (Host-Split Iron Rule)**: `beats.py` / `onsets.py` track drums, NOT human vocals.
    - **Gemini hosts**: listen directly via native multimodal `read_file` on `work/stems/vocal_charts/dry_*.wav` (and tight slices via `vocal_spec.py work/stems/vocals.wav --out <proj>/work/vocal --fps <FPS> --wav-only`), cross-checked with `vocal_phrases.json` & optional `vocal_words.json` BEFORE Gate A.
    - **Claude / Codex hosts**: inspect the noise-free dry vocal spectrograms (`work/stems/vocal_charts/dry_*.png` or `vocal_spec.py work/stems/vocals.wav`) + `vocal_phrases.json` + optional `vocal_words.json` (checking `audible_start_f` / `snapped_start_f` to strip Whisper leading-breath padding) BEFORE Gate A.
- If studying a reference video, extract frame cadence (`scripts/cadence.py`), optical flow (`scripts/motion.py`), brightness/saturation (`scripts/look.py`), and cut diffs (`scripts/framediff.py`).

### 2. Pitch Meeting — 3 Competing Concepts (`assets/workflows/pitch.js` or `pitch.py`)
- Spawn three independent `chiaki-writer` (`Model: "pro"`) angles per act (`媒介设计师` / `演出策划` / `摄影指导`) with verbatim personas from `references/personas.md` → `创意总监` picks one bold cohesive form → `执行制片` checks full-film variety so no two acts repeat the same visual form (`mg-styles.md`), palette, or font pairing. When memory switch ≠ `off`, pass `scripts/memory.py context --stage pitch` into the brief so recent films' visual forms/fonts are not repeated across projects and user aesthetic red lines are respected.

### 3. Storyboard / Shot Table (`script-writing.md`)
- Write the full **Shot Table**: exact rational time bounds (`f0 / FPS` to `f1 / FPS`), non-repeating visual form from `mg-styles.md`, shot recipe from `shot-recipes.md`, library motion IDs from `motion-library.md`, **Asset / Art Provider** (`user_files` | `gemini` | `codex` | `custom_api` | `code_only`), transition hand-off plan, and sound cue sheet (`work/cues.csv`).
- Draft `<project>/work/art_manifest.json` (`python -X utf8 <sk>/scripts/art_gen.py init <project>`) listing every required illustration/plate.

### 4. Gate A — Pre-Art & Pre-Build Lock (`quality-bar.md`)
- Pass **Gate A BEFORE generating any images or writing segment code**: verify concept originality, measured beat alignment, valid motion IDs, approved `art_manifest.json` & cost boundary, and strict file ownership.

### 5. Pluggable Art & Asset Preparation (`art-pipeline.md`, `fonts.py`, `3d.md`)
- **Images / Plates**: execute `<project>/work/art_manifest.json` via `python -X utf8 <sk>/scripts/art_gen.py run <project> --workers 3` (supports per-shot `refs: [...]` multi-reference anchoring and automatic 429/5xx backoff retries, or use the host's native Gemini/Codex image tool), verify every plate visually at full resolution, and confirm completeness with `art_gen.py check <project>`. For RGBA layers and clean plates (`art-pipeline.md` §4): use **`scripts/vision/cutout.py`** (`--model toonout` anime / `--model hr` 2K props) for whole foregrounds, **`scripts/vision/part_cutout.py`** (`--part hair --clean-plate ...` and 18 other anime parts) for single-layer 2K hair/part motion with zero double-ghosting, and **`scripts/vision/pasteback.py --align --lf 40`** for pixel-aligned surgical/eye edits.
- **Fonts, 3D Vector Glyphs, Online Tactile Textures & Real-Shot Footage**: search bundled 59 OFL/Apache fonts (`scripts/fonts.py search --local ...`) or fetch Google Fonts on demand, pack WOFF2 + Base64 locally via `scripts/fonts.py use <project> ...` (`--static` for stroked/outlined glyphs), and extract compact CJK/JP/Latin 3D vector outlines via `scripts/fonts.py glyph3d <project> "<Family>" "<HeroText>"` whenever Three.js 3D typography (`T3.three.extrudeText`) is planned; automatically pick & fetch matching CC0 tactile textures (zero-key `ambientCG` / `Poly Haven` / bundled `assets/textures/`, with `--prep paper|stone|grain`) and live-action stock overlays (`archive` 4K ink/smoke/film-burn/timelapse, `nasa`, plus optional `pexels`/`pixabay`/`CHIAKI_FOOTAGE_DIR`, auto-converted via `--seq` into deterministic `T3.sequence` frames) using **`scripts/media_lib.py`** (`art-pipeline.md` §4).
- **Depth & 3D Assets**: generate softened 16-bit depth maps (`scripts/vision/depth.py ... --bits 16 --soften`) for relief/projection shots, and fetch free HDRIs / PBR materials / models via `scripts/assets3d.py get ... --project <project>` (self-contained attribution is recorded in `work/assets3d_used.json`).

### 6. 3-Craft Studio Build (`assets/workflows/build.js` or `build.py`)
- **Scaffold**: copy `<sk>/assets/template/` into `<project>/web/`, set `window.T3_CONFIG = { fps, start, end, audio, bpm, beatOffset }`.
- **Z-order & material coat convention**: scene/animation segments `z = 10`; dedicated graphic-design/typography overlays `z = 20` (`*_design.js`, or unified inside `z = 10` when lyrics live as world objects); **prefer per-shot tactile material coats (`T3.look.coat` inside each shot) + `T3.look.bakePrint` / `lumaMatte` / `okMix`** over slapping one blanket `z = 45` `film_texture.js` multiply sheet across the entire film (use `z = 45` only when every shot shares the exact same paper world); cross-cut transitions / hand-offs `z = 60` (`*_handoff.js`).
- **Parallel 3-Craft Division of Labor (Dual-3D Flagship)**:
  - **3D 工程师 (`flash`, when act uses Blender or bespoke Three.js 3D sets)**: owns `blender/`, `web/assets/rel/` (SINE-keyed reliefs via `T3.relX`), `web/assets/b3d/` (projection / built-set sequences, played frame-for-frame), optional `segments/*_three.js`, and `work/assets3d_used.json`; optional live Blender MCP for look-dev, all batch renders queued via `run_queue.py blender`, verified by `parallax.py`.
  - **剪辑合成师 (`pro`)**: owns `segments/seg_*.js` (`z = 10`) and `segments/*_handoff.js` (`z = 60`), including Three.js graphic-3D stages/grids (`T3.three.field`/`relief`), live chromatic prism overlays (`T3.three.prismOverlay`), and `z = 60` 3D louver wipes (`T3.three.louverTransition`) when Three.js is active; writes motion sheet, cites library IDs, registers ≥ 3 `T3.motionProbe(...)` curves.
  - **平面设计师 (`flash`)**: owns `design/board.md`, bundled font choices (`fonts.py use` + `fonts.py glyph3d`), colour tokens, and `segments/*_design.js` (`z = 20`, per-glyph kinetic typography + Three.js `T3.three.extrudeText` / `textRing` / `textCorridor` when Three.js is active).
  - **执行导演 (`Dailies`, read-only `pro`) → 并行分专业修改员 (`flash`, Edit + Design + 3D) → 质检 (`flash`)**: first-cut review on curve sheets, contact sheets, and draft clip, closed in one parallel pass across crafts.

### 7. Self-Check & Gate B1 (`quality-bar.md`)
- Run static `motion_lint.mjs` (0 FAIL), queued `motion_lint.mjs --curves` (inspect SVG curve sheets — check both sluggish `Q1 < 0.60` and `Q1 > 0.90` cliff arrivals with long flat tails), `qa.mjs` (0 render/page/text/freeze errors; check in-shot motion & dark-frame `p5 >= 30`), `snap.mjs --sheet` contact sheets, `parallax.py` on spatial shots, and `cadence.py` on stepped passages.

### 8. Sound Design & Mastering (dedicated `声音设计师` · `flash`)
- **Song PVs / Lyric MVs (`pure_song` default)**: cleanly trim, fade edges gently, and master the original recording to **−14.0 ± 1.0 LUFS integrated, true peak ≤ −1.1 dBTP, 48 kHz / 24-bit** (`work/master.wav`) with **zero competing swooshes/risers** unless the client explicitly requested SFX.
- **Promos / Openers / Original Scores (`full_sfx`)**: add `<sk>/assets/mgaudio` to `sys.path` to synthesize beat-synced procedural SFX (`whoosh`, `impact`, `riser`, `text_hit`, `glitch`, `ui`, `paper`...) and optional music beds; supplement physical sounds via `scripts/freesound.py`; mix with `mgaudio.Mix` (≤ 3 concurrent SFX/frame, ~3 dB ducking, `stereo_corr > 0.3`) and master to **−14.0 ± 1.0 LUFS / ≤ −1.1 dBTP** (`work/master.wav`).

### 9. Internal 3-Lens Adversarial Review (`assets/workflows/review_fix.js` or `review_fix.py`)
- Physically read-only `规矩审片员` + `技术审片员` + `剪辑感审片员` (`pro`) → 3 independent verifiers (`pro`) → targeted pre-render fixes (`flash`) → read-only `质检` (`flash`).
- **Host-Split Review Rule**: on **Gemini**, render a quick 720p audiovisual preview clip (`out/preview_720p.mp4` or per-act 720p clips) BEFORE running Stage 9 so all reviewers & verifiers **watch the real `.mp4` via native multimodal `read_file`** (using stills only for pixel inspection); on **Claude / Codex**, audit via `snap.mjs --sheet` contact sheets + transition frames + `curves.svg` + `qa.mjs`.
- **Short-Film (< 60 s) Fast-Track**: clear confirmed blockers (sync drift, render/font defects, legibility collisions, dead frames) quickly so you reach Stage 10's full audiovisual render without stalling in multi-round still-frame loops; reserve fine cosmetic polish for Stage 12 after watching the rendered video + Stage 11 independent scoring.

### 10. First Full Audiovisual Render (V1)
- Render the full timeline with mastered audio through `run_queue.py web` (`render_fast.mjs web/index.html 0 <end> out/film_v1.mp4 --audio work/master.wav --fps <FPS> [--scale 0.6667] [--grain]`) — add **`--grain`** whenever 35mm film grain or paper fiber overlays are used, and prefer 720p first during review before upgrading the approved final to 2K `--2k`.

### 11. Independent 7-Dimension Scorecard (`assets/workflows/polish_rerender.js` or `polish_rerender.py`)
- Dispatch a physically read-only `chiaki-reviewer` (`pro`, `assets/workflows/score_brief.md`) to audit the V1 render, curve sheets, QA log, and loudness report across all 7 dimensions (**≥ 8 / 10 on every single dimension**, never averaged). **Host-Split Iron Rule**: on **Gemini**, the scorer MUST watch `out/film_v1.mp4` (and per-act 720p clips for long films) + listen to climax vocal micro-WAVs directly via native multimodal `read_file`; on **Claude / Codex**, inspect `vocal_spec.py` PNG spectrograms + `snap.mjs` contact sheets + `curves.svg` + QA/loudness metrics. Outputs `work/SCORE_V1.md` with verdict `DELIVER` or `REVISE`.

### 12. Targeted Polish Round + QC (`修一轮`)
- For every deduction or `< 8` dimension in `work/SCORE_V1.md`, `polish_rerender` dispatches scoped `修改员` (`flash`) by owning craft/files for minimal surgical fixes, followed by read-only `质检` (`flash`) frame-by-frame verification. (Skipped only if V1 already passed `DELIVER` with zero blocking issues.)

### 13. Re-Render Final + Re-Score + Gate B2 Delivery (`重渲染 → Gate B2`)
- Re-render the final 1080p web MP4 + 2K master (`--2k`) and mux lossless 48 kHz FLAC archival master (`references/production.md` §4).
- Re-verify any previously `< 8` dimensions via read-only `chiaki-reviewer`, pass **Gate B2** (`quality-bar.md`), and deliver final files + scorecard + open-source credits (`fonts.py credits <project>`, `media_lib.py credits <project>`, and `assets3d.py credits <project>`).
- **Mandatory Post-Delivery Preference Ask & Self-Iteration Retrospective (`Gate B2 Item #6`, `scripts/memory.py`)**: whenever `memory.py status --json` is NOT `off` or `readonly`, you **MUST**:
  1. Distill a compact `work/memory_proposal.json` (delivered film summary + durable preferences observed + generalized `[trigger -> mistake -> rule]` guardrails from any `< 8` deductions/reworks — never one-off plot trivia);
  2. Run `python -X utf8 <sk>/scripts/memory.py draft-card --proposal work/memory_proposal.json` and **append the generated「🧠 下支片想怎么更合你胃口？」3-bullet preference ask + candidate memory card to the very end of your final delivery reply**;
  3. Commit via `memory.py apply work/memory_proposal.json --confirm` after user approval in `ask` mode (or immediately via `memory.py apply` in `auto` mode, still keeping the 3-bullet preference ask so the user can steer future films). **Never finish a film silently without asking the user's preferences when memory is active.**

## Toolkit (quick reference)
- **Stage-1 vocal/instrumental stem separation & dual-stem sync**: `python -X utf8 <sk>/scripts/stem_sync.py <song> --out <proj>/work/stems --fps <FPS> [--whisper --lang <ja|zh|en> --lyrics <lyrics.txt>]`
- **Online tactile textures & live-action footage (zero-key + optional Pexels/Pixabay)**: `python -X utf8 <sk>/scripts/media_lib.py search texture|footage "<q>"` · `media_lib.py get <src> <id> --project <proj> [--prep paper | --seq --fps 24]`
- **Studio self-iteration memory (`~/.chiaki-studio/`)**: `python -X utf8 <sk>/scripts/memory.py status | mode ask|auto|readonly|off | context --stage brief|pitch|craft|review | apply <proposal.json> [--confirm]`
- **Preview contact sheets**: `python -X utf8 <sk>/scripts/run_queue.py web --lane review -- node <sk>/scripts/snap.mjs web/index.html out/snaps "0-240:8" --sheet s1 --fps 24`
- **Motion lint + SVG curve sheet**: `python -X utf8 <sk>/scripts/run_queue.py web --lane lint -- node <sk>/scripts/motion_lint.mjs web/index.html --curves`
- **Automated QA**: `python -X utf8 <sk>/scripts/run_queue.py web --lane qa -- node <sk>/scripts/qa.mjs web/index.html --from 0 --to 30`
- **Visual & motion-density metrics** (mandatory on Gemini/AGY previews, optional on Opus): `python -X utf8 <sk>/scripts/visual_metrics.py out/preview_720p.mp4 --out work/metrics`
- **Fast MP4 / 2K render**: `python -X utf8 <sk>/scripts/run_queue.py web --lane render -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24 --2k`

## Pitfalls
- **Never hand-roll easing formulas** (`t*t`, `Math.sin` for arrivals, per-frame lookup tables): always use `T3.EZ.*` / `T3.mv.*` / GSAP `CustomEase` (`motion-library.md`).
- **Never use remote Google Fonts `<link>` or `https://` fonts**: offline rendering and portability break; always pack local fonts via `scripts/fonts.py use`.
- **Never mix `CSS transform` and `filter/opacity` on a `preserve-3d` parent**: it flattens 3D children (`lib/multiplane.js`).
- **Never leak sub-step motion in a `Posterize Time` passage**: shadow `t` / `f` at the top of `render()` (`style-grammar.md` §6e) so camera, particles, blur, and type step in lockstep.
- **Never run multiple headless Chromes without `run_queue.py`**: concurrent Chromes exhaust RAM and drop frames.

## Honest limits
- Deterministic browser rendering + headless/MCP Blender 3D excels at 2D motion graphics, kinetic typography, Canvas 2D compositing, SVG morphing, CSS 3D multiplane parallax, mesh-warped 2D character layers, Blender 2.5D depth relief, camera projection into painted scenes, and built 3D sets dressed from open asset libraries. It does **not** generate custom hand-drawn frame-by-frame anime sakuga or AI character art from scratch; when a shot needs bespoke illustrations or live-action footage, ask the client to supply those plates and stage/animate them deterministically in 2D or 3D.
