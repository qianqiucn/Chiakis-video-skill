# Chiaki's-video-skill

> **Deterministic HTML / JS / Canvas 2D Motion Graphics, Fast-Cut PV / MV, and Kinetic Typography Studio Skill for AI Coding Agents**  
> 面向 AI 编码代理（Claude Code / Antigravity / Codex 等）的 **2D 动效与快剪视频工作室技能**：确定性帧级网页时间线引擎 + 2D 动效库 + GSAP 3.15.1 + 59 套开源商用字体库 + `mgaudio` 过程化音频引擎 + CC0 胶片纸张纹理 + 完整多工种审片工作流，开箱即用。

---

## ✨ What Is Included / 开箱即用的核心内容

| Module | Path | Highlights |
|---|---|---|
| **Deterministic 2D Timeline Engine** | `assets/template/` | `engine.js` (`render(t)` pure in `t`), frame-exact seeking, zero clock drift, 1080p / 2K MP4 rendering via persistent headless Chrome (`_cdp.mjs`) |
| **2D Motion Library + GSAP 3.15.1** | `assets/template/lib/motion/`, `lib/gsap/` | Named house curves (`T3.EZ`), deterministic GSAP bridge (`lib/gsap-bridge.js`), curve probes & SVG curve-sheet plotter (`T3.motionProbe`), arrivals/exits/settle/stagger/per-char type (`T3.mv`), 180°/360° sub-frame shutter & radial blur (`T3.blur`), stepped `Posterize Time` clock (`T3.twos`), 2D hair/veil travelling-wave & blink staging (`T3.her` + `meshwarp.js`), CSS-3D multi-plane (`multiplane.js`), depth push (`depth3d.js`), polygon accents & kinetic helpers (`accents.js`, `choreo.js`, `emblem3d.js`, `sequence.js`) |
| **Bundled Open-Source Font Library** | `assets/fonts/` | **59 commercial-safe OFL-1.1 / Apache-2.0 families** (~99 MB, every file < 24 MB): 47 Latin/Display/Blackletter/Didone/Condensed/Tech/Mono/Pixel/Brush/Script/Stencil families + 12 essential CJK/JP families (`Noto Sans SC`, `Noto Serif SC`, `Smiley Sans`, `Zhuque Fangsong`, `Ma Shan Zheng`, `Zhi Mang Xing`, `ZCOOL XiaoWei`, `LXGW Marker Gothic`, `ZCOOL KuaiLe`, `Dela Gothic One`, `Rampart One`, `DotGothic16`, `Fusion Pixel`). Offline subsetting + Base64 packing via `scripts/fonts.py`, plus on-demand download of 1,900+ Google Fonts |
| **Bundled Procedural Audio Engine (`mgaudio`)** | `assets/mgaudio/` | 48 kHz float-stereo synth, drums, procedural SFX (`whoosh`, `impact`, `riser`, `glitch`, `text_hit`, `paper`, `ui`...), beat-grid arrangement, and `-14 LUFS` true-peak mastering (MIT, pure Python) |
| **Bundled CC0 2D Textures** | `assets/textures/` | 4K dust overlays (`dust_01..04`), 35mm & fine film grain (`2048px`), paper & washi textures (~11 MB, CC0) |
| **2.5D Blender Depth Relief (Optional)** | `scripts/blender/depth_relief.py`, `scripts/vision/{depth,parallax}.py` | Turn any 2D illustration into a displaced 2.5D relief with real optical orbit/crane/DOF (`Depth Anything V2` `--soften` + headless Blender Eevee/Cycles) and play it back deterministically via `lib/sequence.js` + `T3.relX` (`references/relief-25d.md`) |
| **Cross-Platform CLI Toolchain** | `scripts/` | `doctor.py` (one-command setup check), `install_agy_plugin.py`, `snap.mjs` (contact sheets), `render_fast.mjs` (parallel piped MP4 / 2K render), `qa.mjs`, `motion_lint.mjs`, `run_queue.py` (`web` + `blender` queue), `beats.py` / `onsets.py` / `cadence.py` / `motion.py` / `look.py` / `measure.py` / `framediff.py`, `fonts.py`, `freesound.py`, `skill_check.py`, `pack_skill.py` |
| **2D Studio Craft & Multi-Agent Guardrails** | `references/`, `assets/workflows/`, `assets/workflows_agy/`, `rules/`, `hooks/`, `agents/` | 12 focused craft manuals (`house-style`, `style-grammar`, `graphic-design`, `motion-library`, `mg-styles`, `shot-recipes`, `script-writing`, `quality-bar`, `crafts`, `personas`, `build-brief`, `production`), pitch/build/review workflows, verbatim persona roster, and optional Antigravity guardrail hook (`hooks/chiaki_guard.py`) |

> **Scope note**: This edition focuses on **2D motion graphics, fast-cut PV/MV, lyric typography, MAD, optional 2.5D Blender depth-relief for illustrations, and study replicas**. Leaderboard/ranking dashboards, full 3D set/rigging pipelines, and proprietary AI character-generation wrappers have been removed to keep the repository lean and portable.

---

## 🚀 Quickstart / 快速上手

### 1. Prerequisites / 环境依赖
- **Node.js ≥ 22** (built-in `fetch` + `WebSocket` for DevTools protocol; zero `npm install` needed!)
- **Google Chrome / Chromium / Edge** (auto-detected on Windows, macOS, Linux, or set `CHIAKI_CHROME`)
- **Python ≥ 3.10** + packages for font subsetting, audio/cadence analysis, `mgaudio`, and bundled `imageio-ffmpeg`:
  ```bash
  # Recommended: create an isolated venv (or run `pip install -r requirements.txt` directly)
  python -m venv .venv
  # Windows PowerShell: .venv\Scripts\Activate.ps1   |   macOS / Linux: source .venv/bin/activate
  pip install -r requirements.txt
  ```

### 2. One-Command Health Check & Self-Test / 一键体检与本地自检
```bash
# 0. Check Node >= 22, Chrome/Edge, FFmpeg, Python deps, and bundled assets
python -X utf8 scripts/doctor.py

# 1. Verify skill cross-references, motion library index, workflows, and hygiene
python -X utf8 scripts/skill_check.py

# 2. Run all 2D motion library unit tests (Node >= 22, 174 assertions)
node assets/examples/motion/run_tests.mjs

# 3. Lint the starter 2D template
node scripts/motion_lint.mjs assets/template/index.html

# 4. Search the 59 bundled offline fonts
python -X utf8 scripts/fonts.py search --local "Smiley"
```

### 3. Render the Included 5-Second Demo / 渲染内置 5 秒 2D 动效样片
```bash
# Contact sheet (fast review)
python -X utf8 scripts/run_queue.py web --lane demo -- node scripts/snap.mjs assets/template/index.html out/snaps "0-119:10" --sheet preview

# Full 1080p + 720p MP4 render
python -X utf8 scripts/run_queue.py web --lane demo -- node scripts/render_fast.mjs assets/template/index.html 0 5 out/demo.mp4

# Static + runtime motion lint + SVG curve sheet
python -X utf8 scripts/run_queue.py web --lane demo -- node scripts/motion_lint.mjs assets/template/index.html --curves
```

---

## 🧩 Installing as an AI Agent Skill / 安装到 AI 代理

### Claude Code / Codex
Copy or symlink this folder into your skills directory:
```bash
# Claude Code
cp -r "Chiaki's-video-skill" ~/.claude/skills/chiakis-video-skill

# Codex
cp -r "Chiaki's-video-skill" ~/.codex/skills/chiakis-video-skill
```
Or package a `.skill` zip archive (use `--lite` for platforms with a 200-file upload limit such as claude.ai):
```bash
python -X utf8 scripts/pack_skill.py           # full .skill (includes bundled fonts & textures)
python -X utf8 scripts/pack_skill.py --lite    # <=200 files (fetches fonts on demand via fonts.py)
```

### Antigravity (Plugin Mode with Studio Guardrails)
Run the included installer script to stage the exact Antigravity plugin layout (`skills/chiakis-video-skill/SKILL.md`, `rules/AGENTS.md`, `agents/chiaki-*.md`, and resolved `hooks.json`):
```bash
python -X utf8 scripts/install_agy_plugin.py           # installs to ~/.gemini/config/plugins/chiakis-video-skill
python -X utf8 scripts/install_agy_plugin.py --dry-run # preview first without writing files
```

---

## 📂 Repository Structure / 目录结构

```text
Chiaki's-video-skill/
├── SKILL.md                    # Agent entrypoint & 7-step 2D video studio pipeline
├── README.md                   # This guide
├── LICENSE                     # MIT License
├── THIRD_PARTY_NOTICES.md      # GSAP, mg-styles-15, video-shotcraft, OFL/Apache fonts
├── package.json                # Convenience npm scripts (zero node_modules required)
├── requirements.txt            # Python deps (fonttools, numpy, cv2, mgaudio)
├── references/                 # 12 studio craft manuals (2D motion, typography, cadence, QA, personas)
├── scripts/                    # Cross-platform render, QA, lint, audio/video analysis, font & queue CLIs
├── assets/
│   ├── template/               # engine.js, index.html, GSAP 3.15.1, lib/motion/*, 2D/2.5D helpers
│   ├── examples/               # motion unit tests & demos (motion/, layers/, demo3d/)
│   ├── fonts/                  # 59 bundled OFL-1.1/Apache-2.0 fonts + catalog.json + catalog.md
│   ├── mgaudio/                # MIT 48 kHz procedural SFX, synth & -14 LUFS mastering engine
│   ├── textures/               # CC0 film grain, dust, paper, washi 2D overlays
│   ├── workflows/              # JS studio workflows (pitch, build, review_fix, briefs)
│   └── workflows_agy/          # Antigravity Python run_workflow scripts
├── rules/                      # Always-on studio division-of-labor rule (AGENTS.md)
├── hooks/                      # Optional pre-tool guardrail (chiaki_guard.py)
└── agents/                     # Scoped subagent definitions (writer, builder, reviewer)
```

---

## 🔧 Environment Variables (All Optional) / 可选环境变量

| Variable | Default | Purpose |
|---|---|---|
| `CHIAKI_CHROME` | Auto-detected Chrome/Chromium/Edge | Path to browser binary for headless CDP rendering |
| `CHIAKI_FFMPEG` | `ffmpeg` on `PATH` or `imageio-ffmpeg` | Path to FFmpeg executable |
| `CHIAKI_BLENDER` | Auto-detected Blender (optional) | Path to Blender executable for 2.5D depth relief (`scripts/blender/depth_relief.py`) |
| `CHIAKI_FONTS` | `<repo>/assets/fonts` | Custom local font library directory |
| `CHIAKI_QUEUE_DIR` | `<tempdir>/chiaki_video_queue` | Shared render queue lock folder |
| `CHIAKI_WEB_SLOTS` | `1` | Max simultaneous headless-Chrome jobs |
| `CHIAKI_BLENDER_SLOTS` | `2` | Max simultaneous headless-Blender jobs |
| `CHIAKI_MAX_WORKERS` | `2` | Max Chrome render workers per job |
| `FREESOUND_API_KEY` | `~/.config/chiaki-video/freesound_api_key.txt` | Optional Freesound API key for recorded real-world SFX |

---

## 📜 License & Credits / 协议与致谢

Original skill docs, scripts, and templates are licensed under **MIT** (`LICENSE`). Third-party bundled components retain their original open/standard licenses — see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
