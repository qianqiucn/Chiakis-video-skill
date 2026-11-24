# Production Manual — Cross-Platform 2D Toolchain & Delivery

## 1. Environment & Bundled Dependencies
Everything required for 2D animation, fonts, textures, and procedural sound is bundled inside the skill repository:
- **Node.js ≥ 22**: runs `_cdp.mjs`, `snap.mjs`, `render_fast.mjs`, `qa.mjs`, `motion_lint.mjs`, and `assets/examples/motion/run_tests.mjs` with **zero `npm install`** (built-in `fetch` + `WebSocket`).
- **Headless Chrome / Chromium / Edge**: auto-detected across Windows, macOS, and Linux in `scripts/_cdp.mjs` (override with `CHIAKI_CHROME`).
- **FFmpeg**: auto-detected via `CHIAKI_FFMPEG`, system `PATH`, or Python's `imageio-ffmpeg`.
- **Python ≥ 3.10**: install packages once with `pip install -r <sk>/requirements.txt` (`fonttools`, `brotli`, `Pillow`, `numpy`, `opencv-python`, `imageio-ffmpeg`, `scipy`, `numba`, `soundfile`, `pedalboard`).
- **Bundled 2D Motion Runtime**: `assets/template/` (`engine.js`, GSAP 3.15.1 UMD + `lib/gsap-bridge.js`, `lib/motion/*`, `lib/accents.js`, `lib/choreo.js`, `lib/depth3d.js`, `lib/emblem3d.js`, `lib/fonts.js`, `lib/meshwarp.js`, `lib/multiplane.js`, `lib/sequence.js`).
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
- **Contact sheet screenshots** (`snap.mjs`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane preview -- node <sk>/scripts/snap.mjs web/index.html out/snaps "0-240:8" --sheet s1 --cols 6 --scale 0.5 --fps 24
  ```
- **Clean full-res stills (no burned-in frame label)** (`snap_clean.mjs`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane stills -- node <sk>/scripts/snap_clean.mjs web/index.html out/stills "0,48,120" --png
  ```
- **Static motion lint (no browser, ~10 ms)** (`motion_lint.mjs`):
  ```bash
  node <sk>/scripts/motion_lint.mjs web/index.html [--segments segments/seg_a.js]
  ```
- **Runtime motion lint + SVG curve sheet** (`motion_lint.mjs --curves`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane lint -- node <sk>/scripts/motion_lint.mjs web/index.html --curves --out work/motion_check
  ```
- **Automated Gate B1 QA** (`qa.mjs`):
  ```bash
  python -X utf8 <sk>/scripts/run_queue.py web --lane qa -- node <sk>/scripts/qa.mjs web/index.html --from 0 --to 30
  ```
- **Fast MP4 / 2K Render** (`render_fast.mjs`):
  ```bash
  # 1080p + 720p web outputs in one piped pass
  python -X utf8 <sk>/scripts/run_queue.py web --lane render -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24

  # 720p fast preview clip
  python -X utf8 <sk>/scripts/run_queue.py web --lane preview -- node <sk>/scripts/render_fast.mjs web/index.html 0 10 out/preview.mp4 --audio work/master.wav --fps 24 --scale 0.6667

  # 2K master (2560x1440)
  python -X utf8 <sk>/scripts/run_queue.py web --lane master -- node <sk>/scripts/render_fast.mjs web/index.html 0 30 out/film.mp4 --audio work/master.wav --fps 24 --2k
  ```

### Bundled Fonts (`scripts/fonts.py`)
- **Search bundled offline library**: `python -X utf8 <sk>/scripts/fonts.py search --local "Smiley"` or `--group cjk-serif` or `--text "重要歌词"`
- **Search & download any Google Font online**: `python -X utf8 <sk>/scripts/fonts.py search "Syne"` → `python -X utf8 <sk>/scripts/fonts.py get "Syne"`
- **Pack into a project (WOFF2 subset + Base64 `fontpack.js` + `index.html` tags)**:
  ```bash
  python -X utf8 <sk>/scripts/fonts.py use <project> "Smiley Sans" "Syne" "JetBrains Mono"
  # Outlined/hollow display font (merges variable font strokes):
  python -X utf8 <sk>/scripts/fonts.py use <project> "Montserrat:900" --static --alias "Montserrat Outline"
  ```
- **Generate open-source font end-credits**: `python -X utf8 <sk>/scripts/fonts.py credits <project>`

### Audio & Rhythm Analysis (`beats.py`, `onsets.py`)
- **BPM, beat grid & top accents** (stdlib only): `python -X utf8 <sk>/scripts/beats.py music.mp3 --fps 24 --json work/beats.json`
- **Exact broadband onset frame** (numpy): `python -X utf8 <sk>/scripts/onsets.py music.mp3 210-240 420-450 --fps 24`

### Reference Video Analysis (`motion.py`, `cadence.py`, `look.py`, `measure.py`, `framediff.py`)
- **In-shot motion energy & front/back ratio**: `python -X utf8 <sk>/scripts/motion.py film.mp4 0 15 [ref.mp4 0 15]`
- **Stepped cadence & `Posterize Time` verification**: `python -X utf8 <sk>/scripts/cadence.py film.mp4 0 15 --snap work/cad_snaps`
- **Luma / saturation / colour profile**: `python -X utf8 <sk>/scripts/look.py film.mp4 0 15`
- **Motion tracking / measurement**: `python -X utf8 <sk>/scripts/measure.py ...`
- **Frame-to-frame diff / cut detection**: `python -X utf8 <sk>/scripts/framediff.py film.mp4`

### Vision Cut-outs & Clean Plates (`scripts/vision/`, full flags in `references/art-pipeline.md` §4)
- **Whole foreground RGBA** (`cutout.py`, MIT): `python -X utf8 <sk>/scripts/vision/cutout.py art.png art_rgba.png --model toonout` (anime characters) or `--model hr` (2K props/objects).
- **Anime 19-part single-layer + clean plate** (`part_cutout.py`, Apache-2.0 + MIT): `python -X utf8 <sk>/scripts/vision/part_cutout.py art.png hair.png --part hair --clean-plate clean.png --json work/hair_rig.json` (ready for `T3.her.wave` + `T3.her.warp2`).
- **Pixel-aligned edit paste-back** (`pasteback.py`): `python -X utf8 <sk>/scripts/vision/pasteback.py orig.png edit.png diff out.png --align --lf 40 --region x0,y0,x1,y1`.

### 3D & Blender (`depth_relief.py`, `projection/`, `assets3d.py`, `asset_lib.py`, Blender MCP)
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
```python
import sys
sys.path.insert(0, "<sk>/assets/mgaudio")
import mgaudio as mg
from mgaudio import recipes, sfx, drums, synth
```
- Procedural SFX (`sfx.whoosh`, `sfx.impact`, `sfx.riser`, `sfx.text_hit`, `sfx.glitch`, `sfx.paper`, `sfx.ui`, ...) and 15 musical recipes (`recipes.for_style(...)`) work out of the box with zero large sample downloads.
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
