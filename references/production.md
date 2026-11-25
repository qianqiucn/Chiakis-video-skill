# Production Manual — Cross-Platform 2D Toolchain & Delivery

## 1. Environment & Bundled Dependencies
Everything required for 2D animation, fonts, textures, and procedural sound is bundled inside the skill repository:
- **Node.js ≥ 22**: runs `_cdp.mjs`, `snap.mjs`, `render_fast.mjs`, `qa.mjs`, `motion_lint.mjs`, and `assets/examples/motion/run_tests.mjs` with **zero `npm install`** (built-in `fetch` + `WebSocket`).
- **Headless Chrome / Chromium / Edge**: auto-detected across Windows, macOS, and Linux in `scripts/_cdp.mjs` (override with `CHIAKI_CHROME`).
- **FFmpeg**: auto-detected via `CHIAKI_FFMPEG`, system `PATH`, or Python's `imageio-ffmpeg`.
- **Python ≥ 3.10**: install packages once with `pip install -r <sk>/requirements.txt` (`fonttools`, `brotli`, `Pillow`, `numpy`, `opencv-python`, `imageio-ffmpeg`, `scipy`, `numba`, `soundfile`, `pedalboard`).
- **Bundled 2D + Stylized 3D Motion Runtime**: `assets/template/` (`engine.js`, GSAP 3.15.1 UMD + `lib/gsap-bridge.js`, **`lib/look_fx.js`** per-shot coat / print-plate shaders / `lumaMatte` / OKLCH `okMix`, **Three.js r160 MIT + `lib/three_kit.js`**, `lib/motion/*`, `lib/accents.js`, `lib/choreo.js`, `lib/depth3d.js`, `lib/emblem3d.js`, `lib/fonts.js`, `lib/meshwarp.js`, `lib/multiplane.js`, `lib/sequence.js`).
- **Bundled Open-Source Fonts (`assets/fonts/`)**: 59 commercial-safe OFL-1.1 / Apache-2.0 families (47 Latin/Display/Mono/Pixel + 12 CJK/JP), indexed in `assets/fonts/catalog.json` and `assets/fonts/catalog.md`.
- **Bundled Procedural Audio Engine (`assets/mgaudio/`)**: MIT-licensed 48 kHz synth, drums, SFX, mixing & `-14 LUFS` mastering engine.
- **Bundled CC0 2D Textures (`assets/textures/`)**: 4K dust, film/fine grain, paper, and washi overlays.

## 2. Queue Discipline (`scripts/run_queue.py`)
Every command that opens headless Chrome (`snap.mjs`, `snap_clean.mjs`, `render_fast.mjs`, `qa.mjs`, `motion_lint.mjs --curves`) MUST run through `run_queue.py`:
```bash
python -X utf8 <sk>/scripts/run_queue.py web --lane <role> -- <command ...>
python -X utf8 <sk>/scripts/run_queue.py --status
```
- Caps concurrent headless browser jobs to 1 (configurable via `CHIAKI_WEB_SLOTS`), caps `render_fast.mjs --workers` to 2 (`CHIAKI_MAX_WORKERS`), and enforces a free-RAM floor so parallel agents never OOM the host.
- Works on Windows (Win32 Job Objects + `msvcrt`) and macOS/Linux (`fcntl.flock` + process groups). Queue lock directory defaults to `<tempdir>/chiaki_video_queue` (override via `CHIAKI_QUEUE_DIR`).

## 3. CLI Toolkit Quick Reference

### Preview, QA, Lint & Rendering
- **Labelled contact sheet & frame list** (`snap.mjs`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane preview -- node <sk>/scripts/snap.mjs web/index.html out/snaps "0-240:8" --sheet s1 --cols 6 --scale 0.5 --fps 24
  ```
- **Clean full-res stills — single frame OR frame list (no burned-in frame label)** (`snap_clean.mjs`):
  ```bash
  # Single clean still (file path + single frame index)
  python -X utf8 <sk>/scripts/run_queue.py web --lane stills -- node <sk>/scripts/snap_clean.mjs web/index.html out/f048.png 48 --fps 24
  # Multiple clean stills into a directory (directory path + frame list)
  python -X utf8 <sk>/scripts/run_queue.py web --lane stills -- node <sk>/scripts/snap_clean.mjs web/index.html out/stills "0,48,120" --fps 24 --png
  ```
- **Static motion lint (no browser, ~10 ms)** (`motion_lint.mjs`):
  ```bash
  node <sk>/scripts/motion_lint.mjs web/index.html [--segments segments/seg_a.js]
  ```
- **Runtime motion lint + SVG curve sheet** (`motion_lint.mjs --curves`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane lint -- node <sk>/scripts/motion_lint.mjs web/index.html --curves --out work/motion_check
  ```
- **Automated Gate B1 QA — 5 timed stages with incremental `qa_report.txt` + `qa_state.json`** (`qa.mjs`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane qa -- node <sk>/scripts/qa.mjs web/index.html --from 0 --to 30 [--draft out/preview_720p.mp4] [--stage-timeout 120]
  ```
- **Fast MP4 / 2K Render — per-worker heartbeat, auto GPU→CPU retry, stall watchdog & atomic `.part.mp4`** (`render_fast.mjs`):
  ```bash
  # 1080p + 720p web outputs in one piped pass (atomic commit; auto-retries stalled frames)
  python -X utf8 <sk>/scripts/run_queue.py web --lane render -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24 [--frame-timeout 30 --stall-timeout 60]

  # 720p fast preview clip
  python -X utf8 <sk>/scripts/run_queue.py web --lane preview -- node <sk>/scripts/render_fast.mjs web/index.html 0 10 out/preview.mp4 --audio work/master.wav --fps 24 --scale 0.6667

  # 2K master (2560x1440; add --grain for tactile paper/35mm films)
  python -X utf8 <sk>/scripts/run_queue.py web --lane master -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24 --2k --grain

  # Local revision without full re-render (--disk --keep cache + --patch-frames or --encode-only)
  python -X utf8 <sk>/scripts/run_queue.py web --lane patch -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24 --patch-frames "120-180,500-540"
  python -X utf8 <sk>/scripts/run_queue.py web --lane remux -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master_v2.wav --fps 24 --encode-only
  ```

### Bundled Fonts (`scripts/fonts.py`)
- **Search bundled offline library**: `python -X utf8 <sk>/scripts/fonts.py search --local "Smiley"` or `--group cjk-serif` or `--text "重要歌词"`
- **Search & download any Google Font online**: `python -X utf8 <sk>/scripts/fonts.py search "Syne"` → `python -X utf8 <sk>/scripts/fonts.py get "Syne"`
- **Pack into a project (WOFF2 subset + Base64 `fontpack.js` + `index.html` tags)**:
  ```bash
  python -X utf8 <sk>/scripts/fonts.py use <project> "Smiley Sans" "Syne" "JetBrains Mono"
  # Outlined/hollow display font (merges variable font strokes):
  python -X utf8 <sk>/scripts/fonts.py use <project> "Montserrat:900" --static --alias "Montserrat Outline"
  # Extract compact 3D vector glyph contours for Three.js T3.three.extrudeText (supports CJK/JP/Latin!):
  python -X utf8 <sk>/scripts/fonts.py glyph3d <project> "Smiley Sans" "星尘破晓WORLD" --alias hero3d
  ```
- **Generate open-source font end-credits**: `python -X utf8 <sk>/scripts/fonts.py credits <project>`

### Audio, Dual-Stem Separation & Rhythm Analysis (`stem_sync.py`, `beats.py`, `onsets.py`, `vocal_spec.py`)
- **Stage-1 Vocal/Instrumental Stem Separation & Auto Vocal-Presence Sync (`stem_sync.py` — run FIRST on any user-provided music track before storyboarding or locking beats/lyrics)**:
  ```bash
  # SOTA Mel-Band RoFormer split + auto vocal-presence detection + pure-backing kick/BPM drift check + dry-vocal phrases/charts + optional faster-whisper word alignment:
  python -X utf8 <sk>/scripts/stem_sync.py song.wav --out work/stems --fps 30 --whisper --lang ja --lyrics work/lyrics.txt
  # Faster lightweight 60 MB ONNX model (CPU-friendly):
  python -X utf8 <sk>/scripts/stem_sync.py song.wav --out work/stems --fps 30 --fast
  # Reuse an existing audio-separator / demucs venv without reinstalling:
  python -X utf8 <sk>/scripts/stem_sync.py song.wav --out work/stems --fps 30 --stem-python "<path/to/stem-venv/python>" --model-dir "<path/to/stem-models>"
  ```
  - Automatically classifies `track_type` (`vocal_song` vs `instrumental` via `has_vocals`): when vocals are present, produces `work/stems/vocals.wav` + `work/stems/instrumental.wav`, `kick_grid.json` (with 30 s per-section local BPM drift warnings), `vocal_phrases.json`, `vocal_charts/dry_*.wav` + `dry_*.png`, and optional `vocal_words.json` (cross-snapped to dry vocal flux attacks to flag Whisper leading-breath padding; auto-discovers `CHIAKI_WHISPER_MODELS` or sibling `whisper_models/`). When pure instrumental is detected, automatically skips empty vocal charts & Whisper.
- **BPM, beat grid & top accents** (stdlib only — feed `work/stems/instrumental.wav` on vocal songs!): `python -X utf8 <sk>/scripts/beats.py work/stems/instrumental.wav --fps 30 --json work/beats.json`
- **Exact broadband onset frame** (numpy — feed `work/stems/instrumental.wav` on vocal songs!): `python -X utf8 <sk>/scripts/onsets.py work/stems/instrumental.wav 210-240 420-450 --fps 30`
- **Targeted dry-vocal micro-WAVs / spectrograms** (`vocal_spec.py` — feed `work/stems/vocals.wav`!): `python -X utf8 <sk>/scripts/vocal_spec.py work/stems/vocals.wav --out work/vocal --fps 30 [--wav-only] [--ranges f4200-f4725]`

### Reference Video Analysis (`motion.py`, `cadence.py`, `look.py`, `measure.py`, `framediff.py`)
- **In-shot motion energy & front/back ratio**: `python -X utf8 <sk>/scripts/motion.py film.mp4 0 15 [ref.mp4 0 15]`
- **Visual density, colour saturation, true-black ink & per-frame MAD waveform** (`visual_metrics.py` — mandatory on Gemini/AGY Gate A & act previews per `rules/AGENTS.md` §5; optional on Opus):
  ```bash
  python -X utf8 <sk>/scripts/visual_metrics.py out/preview_720p.mp4 --out work/metrics [--ref ref.mp4 --ref-from 192.08 --ref-dur 15.25]
  ```
- **Stepped cadence & `Posterize Time` verification**: `python -X utf8 <sk>/scripts/cadence.py film.mp4 0 15 --snap work/cad_snaps`
- **Luma / saturation / colour profile**: `python -X utf8 <sk>/scripts/look.py film.mp4 0 15`
- **Motion tracking / measurement**: `python -X utf8 <sk>/scripts/measure.py ...`
- **Frame-to-frame diff / cut detection**: `python -X utf8 <sk>/scripts/framediff.py film.mp4`

### Online Textures & Live-Action Footage (`scripts/media_lib.py`, full guide in `references/art-pipeline.md` §4)
- **Check active sources**: `python -X utf8 <sk>/scripts/media_lib.py sources` (zero-key `bundled` + `ambientCG` + `Poly Haven` + `Internet Archive stock_footage` + `NASA` ready immediately; optional `PEXELS_API_KEY` / `PIXABAY_API_KEY` / `CHIAKI_FOOTAGE_DIR`).
- **Search & download**: `media_lib.py search texture|footage "<query>"` → `media_lib.py get <provider> <id> --project <proj> [--prep paper|stone|grain | --seq --fps 24 --dur 5 --blend screen]`; export credits via `media_lib.py credits <proj>`.

### Vision Cut-outs & Clean Plates (`scripts/vision/`, full flags in `references/art-pipeline.md` §4)
- **Whole foreground RGBA** (`cutout.py`, MIT): `python -X utf8 <sk>/scripts/vision/cutout.py art.png art_rgba.png --model toonout` (anime characters) or `--model hr` (2K props/objects).
- **Anime 19-part single-layer + clean plate** (`part_cutout.py`, Apache-2.0 + MIT): `python -X utf8 <sk>/scripts/vision/part_cutout.py art.png hair.png --part hair --clean-plate clean.png --json work/hair_rig.json` (ready for `T3.her.wave` + `T3.her.warp2`).
- **Pixel-aligned edit paste-back** (`pasteback.py`): `python -X utf8 <sk>/scripts/vision/pasteback.py orig.png edit.png diff out.png --align --lf 40 --region x0,y0,x1,y1`.

### 3D & Dual-3D Toolchain (Three.js Stylized Graphic-3D + Blender Cinematic 3D)
- **Three.js Stylized Graphic-3D** (bundled offline, zero install; see `references/3d.md` §5e):
  Load `<script src="lib/three/three.min.js">` + `<script src="lib/three_kit.js">` in `web/index.html`, extract 3D CJK/JP/Latin contours with `fonts.py glyph3d`, and compose `T3.three.extrudeText` / `textRing` / `textCorridor` / `prismOverlay` / `louverTransition` / `field` / `relief` / `stage` deterministically in any segment `render(t)`.
- **Softened 16-bit depth map** (requires optional `pip install torch transformers`):
  `python -X utf8 <sk>/scripts/vision/depth.py art.png work/art_depth.png --bits 16 --soften`
- **Headless Blender 2.5D relief sequence** (always through `run_queue.py blender`; see `references/3d.md` §3.2):
  `python -X utf8 <sk>/scripts/run_queue.py blender --lane relief -- blender -b --python <sk>/scripts/blender/depth_relief.py -- --image art.png --depth work/art_depth.png --out web/assets/rel/shot01 --frames 48 --fps 24 --orbit -8 --crane 4 --dof 0.28`
- **Camera projection dolly** (`scripts/blender/projection/`, see `references/3d.md` §3.6):
  Copy `scripts/blender/projection/` to `<proj>/blender/<SHOT>/eng/scripts/`, run `design.py sim` → `design.py build <y0>` → `textures.py`, then render via `run_queue.py blender -- blender -b --python dolly_scene.py -- --eng <SHOT>/eng --out <dir>`.
- **Free 3D asset library** (`scripts/assets3d.py` + `scripts/blender/asset_lib.py`, see `references/3d.md` §5b):
  `python -X utf8 <sk>/scripts/assets3d.py search all "studio lamp" --kind model --license cc0,by`
  `python -X utf8 <sk>/scripts/assets3d.py get polyhaven studio_small_09 --res 2k --project <proj>`
  `python -X utf8 <sk>/scripts/assets3d.py credits <proj>`
- **Parallax check**: `python -X utf8 <sk>/scripts/vision/parallax.py f001.png f048.png --depth work/art_depth.png --out work/parallax.jpg`
- **Live look-dev via Blender MCP** (`references/3d.md` §5d): use open Blender MCP (official Blender 5.1+ Lab add-on via `<sk>/scripts/blender/mcp_bridge.py`, or `uvx blender-mcp` on Blender 4.2+) for interactive staging, lighting, and camera tweaks; always run final batch renders headless through `run_queue.py blender`.

### Studio Self-Iteration Memory (`scripts/memory.py`, stored outside repo at `~/.chiaki-studio/` or `$CHIAKI_MEMORY_DIR`)
- **Check / toggle switch**: `python -X utf8 <sk>/scripts/memory.py status` · `memory.py mode ask|auto|readonly|off` · `memory.py show`
- **Stage-sliced context injection** (≤ 1800 chars, never bloats prompts): `python -X utf8 <sk>/scripts/memory.py context --stage brief|pitch|craft|review`
- **Gate B2 retrospective commit**: `python -X utf8 <sk>/scripts/memory.py apply work/memory_proposal.json [--confirm]` (`ask` prints ≤ 5-line confirmation card first; `auto` writes directly and flags `hits >= 2` skill-upgrade candidates; `readonly`/`off` skips writing).

### Audio (`mgaudio` & Freesound)
Always insert `<sk>/assets/mgaudio` onto `sys.path` inside each audio script (so fresh shells never fail `ModuleNotFoundError`):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"<sk>") / "assets" / "mgaudio"))
import mgaudio as mg
from mgaudio import recipes, sfx, drums, synth
```
- Procedural SFX (`sfx.whoosh`, `sfx.impact`, `sfx.riser`, `sfx.text_hit`, `sfx.glitch`, `sfx.paper`, `sfx.ui`, ...) and 15 musical recipes (`recipes.for_style(...)`) work out of the box with zero large sample downloads.
- `m.export(..., spectrogram="work/audio_spec.png")` automatically falls back to a built-in pure `numpy + scipy + Pillow` renderer when optional `matplotlib` is not installed (never aborts mastering).
- Optional recorded real-world SFX: set `FREESOUND_API_KEY` and use `python -X utf8 <sk>/scripts/freesound.py search "camera shutter"` / `get <id> --project <proj>`.

## 4. 2K Lossless Master Delivery
After rendering `out/film_2k.mp4` (`--2k`), mux lossless 48 kHz / 24-bit FLAC audio from `work/master.wav` when delivering an archival or Bilibili/YouTube master:
```bash
ffmpeg -hide_banner -y -i out/film_2k.mp4 -i work/master.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a flac -ar 48000 -movflags +faststart out/film_2k_flac.mp4
```

## 5. Canvas 2D & Environment Pitfalls
- **Windows console UTF-8**: always run Python scripts with `python -X utf8` (isolated mode ignores `PYTHONUTF8`); write helper scripts to `.py` files instead of quoting Chinese inside PowerShell `-c` strings.
- **FFmpeg v8/v9+ frame extraction**: use `-fps_mode vfr` or `-fps_mode passthrough` (never the removed `-vsync 0`).
- **Exact rational segment bounds**: on 24 or 30 fps timelines, declare segment `start` and `end` as exact fractions (`f0 / FPS`, `f1 / FPS`), never rounded decimals (`11.67`), or Chrome and `T3.seek` will miss a boundary frame by 1 frame.
- **Canvas `ctx.save()` / `ctx.restore()` discipline**: never mutate `ctx.filter`, `ctx.globalAlpha`, or `ctx.globalCompositeOperation` without balanced `save`/`restore`, and always reset `ctx.shadowBlur = 0` after glows so downstream layers do not inherit expensive blurs.
- **Canvas text layout**: set `ctx.font` *before* calling `ctx.measureText(...)` so per-glyph kinetic typography spacing stays pixel-exact across frames.
- **Zero state leak**: never cache animation progress in closure variables across frames; derive every pixel solely from `t` / `T3.frame(t)`.

## 6. Agent Models & Cross-Platform Tier Mapping
| Role & Scoped Agent Type | Antigravity (`Model`) | Claude Code | Codex | Rationale |
|---|---|---|---|---|
| Pitch writers, Creative Director, Executive Producer (`chiaki-writer`) | `pro` | `opus` | High reasoning / flagship | High-leverage creative originality & full-film pacing |
| Editor / 2D Motion Compositor (`chiaki-builder`) | `pro` | `opus` | High reasoning / flagship | Primary animation curves, Canvas 2D choreography & transitions |
| 3D Engineer, Graphic Designer, Sound Designer, Fixer (`chiaki-builder`) | `flash` | `sonnet` | Medium / standard | Scoped craft execution against concrete specs & briefs |
| Production Assistant (`chiaki-builder`) | `flash_lite` | `haiku` | Low / mini | Mechanical beat tables, asset copying & batch contact sheets |
| Dailies Executive Director, 3 Final Review Lenses, 3 Verifiers, Independent Scorer (`chiaki-reviewer`, read-only) | `pro` | `opus` | High reasoning / flagship | Strict adversarial critique, frame-level evidence & 7-dim scoring |
| QC Recheck (`chiaki-reviewer`, read-only) | `flash` | `sonnet` | Medium / standard | Fast visual verification of scoped fix checklist |

## 7. Antigravity Swarm (`/teamwork`) Hybrid Playbook

Use Antigravity's native `swarm` board for **collaborative production stages (Stage 6 Build, Stage 8 Sound, Stage 12 Polish)** where multiple crafts align frame numbers, `layout.js` coordinates, and cut hand-offs live — while keeping **Stage 2 Blind Pitch** (`chiaki-writer`) and **Stage 9 / 11 Read-Only Review & Independent Scoring** (`chiaki-reviewer`) on isolated `invoke_subagent` / `run_workflow`.

### Recommended Roster Pattern (`workspace: "inherit"`, 3–5 active workers)
- **Before adding workers**: load `swarm_pane` and prepare `.system_generated/swarm/plan.json` grouping `threads` by film outcome/act (e.g. `act-a`, `act-b`, `audio-master`), never by agent name.
- **Concrete model pinning**: call `swarm(action="models")` once; omit `model` to inherit coordinator's flagship model for `edit-*` leads, or pin a fast concrete model for scoped `design-*` / `3d-*` / `sound` workers. If any worker hits quota mid-act, switch it in place with `swarm(action="model", name="...", model="...")` — **never kill & re-add** (keeps full act context).
- **Disjoint file ownership (replaces git branches)**:
  - `3d-a`: owns `blender/act_a/`, `web/assets/rel/<ID>/`, `web/assets/b3d/<ID>/` (posts exact frame counts & SINE range to board when done)
  - `edit-a`: owns `web/segments/seg_a.js`, `web/segments/a_handoff.js`, `work/motion_a.md` (`z=10/60`)
  - `design-a`: owns `design/board_a.md`, `web/segments/seg_a_design.js`, `work/motion_a_design.md` (`z=20`; reads `edit-a`'s posted focal boxes & safe margins on the board)
  - `sound`: owns `work/make_audio.py`, `work/master.wav` (reads `work/cues.csv` + board hand-off updates)
- **Queue & timeline discipline**:
  - Keep **≤ 5 active build workers** at once so `scripts/run_queue.py` (1 headless Chrome / 2 Blender slots) stays responsive; code in parallel, queue `snap.mjs` / `motion_lint.mjs --curves` / `depth_relief.py` staggered.
  - Instruct visual workers in their brief to save milestone full-window renders/snaps under their own conversation brain folder and post `Screenshot: <absolute path> | <≤10-word visual change>` so the Swarm UI renders a live visual timeline.
  - When a craft finishes and its files are verified, leave it `waiting` (0 cost) until final delivery so Stage 12 Polish can `@mention` the exact original author with full memory; `kill` workers only after Gate B2 sign-off (or before a clean-slate major reboot).

### Gemini / AGY Coordinator Playbook (Claude Opus Exempt)
> Applies only to **Gemini / Antigravity default sessions**; **Claude Opus is exempt**.

1. **Clean-slate reboots & lean full-stack single-canvas roster**: when restarting a major version (e.g. V2 → V4), `kill` every stale worker first so old habits do not pollute new acts. For kinetic lyric PVs where type IS a physical scene object, prefer **1 flagship full-stack worker per act** (`≤ 5` active, unified single canvas owning props + type + transitions) over splitting 10 `edit` + `design` workers — eliminates intra-act collision churn and frees board bandwidth for cross-act coordination.
2. **Pre-build 4 hard foundations before spawning**: land ① the signed 10–16 s Gate A golden clip + source, ② a coordinator-owned shared visual/world library (workers read-only; request schema changes via `@coordinator`), ③ standalone per-act preview HTMLs + assembly HTML, and ④ `scripts/visual_metrics.py` thresholds. When a worker reports measured audio/frame corrections from direct WAV listening, update the shared skeleton immediately rather than forcing workarounds.
3. **Two-stage `[storyboard]` gate — cross-act de-duplication & pre-roll seam contract**: require workers to submit `[storyboard]` first and wait for `@coordinator` sign-off before coding. On review:
   - Cross-check parallel acts (e.g. Chorus 1 vs Chorus 2 vs Finale) to kill duplicate motifs/props before a single line of JS is written; block legacy template relapses (`louverTransition`, flat portrait slow-zooms) and cap repeated tricks (`whip ≤ 3/act`, `glitch` only when physically motivated).
   - Lock cross-act seams as a **pure-function pre-roll contract**: incoming act exposes `open.actN(ctx, f)` safe to invoke `8–12` frames early with zero side effects (plus matching end-state parameters like spin angle / ground hex), then let adjacent workers confirm directly peer-to-peer on the board.
4. **Centralized art queue + non-blocking placeholders + pixel-level plate usage notes**: forbid Swarm workers from calling image-gen APIs directly. Workers list needed plates (`≤ 4/act`) in their storyboard; coordinator generates in the background while workers build with placeholders, inspects every plate at full resolution (plus hand crops), **immediately broadcasts a stop-use notice** if a plate fails anatomy/composition, and attaches a **1-line usage note** to every approved plate (axis tilt / gaze direction, safe crop region, max hand width e.g. `≤ 500 px`, and motion trick such as shifting the whole arm `y - 40..60 px` while holding the platter still).
5. **High-density, zero-hype board style**: keep `@coordinator` posts to **3–6 factual lines** (verdict + numbered frame/pixel/metric adjustments + exact next action). Ban exclamation-heavy praise (`完美 / 100/100 / 封神 / 炸裂`) so downstream workers report hard measured numbers instead of hype.
