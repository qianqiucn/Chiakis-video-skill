---
name: chiaki
description: Chiaki's-video-skill 统一快捷入口（/chiaki）：一条指令覆盖 2D 动效视频全流程 — 开新片（/chiaki 或 /chiaki new）、选字打包（/chiaki fonts）、2.5D Blender 浮雕（/chiaki relief）、快速预览与曲线图（/chiaki preview）、三视角物理只读终审（/chiaki review）、终混交片与独立打分（/chiaki deliver）、进度与环境体检（/chiaki status）。仅在用户明确写 /chiaki、/Chiaki、$chiaki 或要求按 Chiaki's-video-skill 做视频时使用。
---

# `/chiaki` — Chiaki's-video-skill 统一工作台入口

先用 `read_file` 读取主技能 `<SKILL_DIR>/SKILL.md`、`references/personas.md`、`references/house-style.md`、`references/crafts.md` 与 `references/motion-library.md`。

> **硬性工作室分工纪律**：你只担任**总导演兼制片人**，绝不退化成「主线程大包大揽写完所有代码再自审」。每次调用 `chiaki-writer` / `chiaki-builder` / `chiaki-reviewer` 必须在 Prompt 顶部贴入 `references/personas.md` 原话身份与性格、附 `references/crafts.md` 工种卡与任务简报、并显式锁定 `Model`（`pro` / `flash` / `flash_lite`）；所有无头 Chrome 与 `blender -b` 命令一律经 `<SKILL_DIR>/scripts/run_queue.py` 排队执行（`hooks/chiaki_guard.py` 会自动拦截违规调用）。

---

## 子指令路由（解析 `/chiaki` 后的第一个词）

| 用户输入 | 路由动作 |
|---|---|
| `/chiaki`、`/chiaki new <想法/歌名>` 或 `/chiaki <任意创作需求>` | **1. 开新片** |
| `/chiaki fonts [关键词 / 项目路径]` | **2. 选字、测缺字与打包** |
| `/chiaki relief <图片路径> [运镜参数]` | **3. 2D 插画转 Blender 2.5D 深度浮雕** |
| `/chiaki preview [起止秒]` | **4. 静态动效检查 + 720p 预览 + SVG 曲线图** |
| `/chiaki review` | **5. Gate B1 + 三视角物理只读终审与定向修复** |
| `/chiaki deliver` | **6. `mgaudio` `-14 LUFS` 终混 + 1080p/2K FLAC + 独立 7 维打分 + 字体鸣谢** |
| `/chiaki status` | **7. 只读项目进度、渲染队列与环境体检** |
| `/chiaki help` | 打印本速查表并询问下一步 |

---

## 各子指令执行流程

### 1. 开新片（`new` 或直接写需求）
1. **环境体检**：快速运行 `python -X utf8 "<SKILL_DIR>/scripts/doctor.py"` 确认 Node ≥ 22、Chrome、FFmpeg 与依赖就绪（若缺项先提示安装命令）。
2. **明确 Brief**：确认主题/歌名、目标时长、帧率（24 或 30 fps）、模式（原创 PV/MG / 歌词 MV / 复刻学习）、已有音乐与视觉素材；缺失项用合理默认值补齐并一行告知。
3. **测节拍（绝不靠猜）**：有音乐时立即跑 `scripts/beats.py` 与关键落点 `scripts/onsets.py` 锁定精确帧号。
4. **开工前一行报成本**：说明预计子代理数、模型档位（`pro`/`flash`）与大致耗时。
5. **提案会（Stage 2）**：写 `work/PITCH_BRIEF.md`，运行 `<SKILL_DIR>/assets/workflows_agy/pitch.py`（或同等分工的 `chiaki-writer` `Model="pro"`：媒介设计师 / 演出策划 / 摄影指导 → 创意总监拍板 → 执行制片统筹）。
6. **建脚手架与制作（Stage 4）**：拷贝 `<SKILL_DIR>/assets/template/` 到 `<project>/web/`，写分镜表过 Gate A，按 `build.py` 严格分离 **剪辑合成师 (`pro`, `seg_*.js` z=10 & `*_handoff.js` z=60)** 与 **平面设计师 (`flash`, `board_*.md` & `*_design.js` z=20)** + 只读 **执行导演看样 (`chiaki-reviewer`, `pro`)** + **质检 (`flash`)**。

### 2. 选字与打包（`fonts`）
1. 先离线检索内置 59 套商用开源字库：`python -X utf8 "<SKILL_DIR>/scripts/fonts.py" search --local <关键词或分组>`（需要更多字体再搜在线 `search` 并 `get`）。
2. 有歌词或标题文案时带 `--text "<文案>"` 检查缺字，给出 2–3 套风格搭配建议。
3. 确认后执行 `python -X utf8 "<SKILL_DIR>/scripts/fonts.py" use <project> "<字体1>" "<字体2>"` 子集化 WOFF2 + Base64 注入项目（空心描边字自动加 `--static` 合并轮廓）。

### 3. 插画转 Blender 2.5D 深度浮雕（`relief`）
先读 `<SKILL_DIR>/references/relief-25d.md`，然后按三步走：
1. 生成柔化 16-bit 像素对齐深度图：`python -X utf8 "<SKILL_DIR>/scripts/vision/depth.py" <img.png> work/<id>_depth.png --bits 16 --soften`。
2. 经队列渲染无头 Blender 浮雕：`python -X utf8 "<SKILL_DIR>/scripts/run_queue.py" blender --lane relief -- blender -b --python "<SKILL_DIR>/scripts/blender/depth_relief.py" -- --image <img.png> --depth work/<id>_depth.png --out web/assets/rel/<id> --frames 48 --fps 24 --orbit -8 --crane 4 --dof 0.28`。
3. 用 `scripts/vision/parallax.py` 核验前后景视差，输出可直接贴入片段的 `T3.sequence({ frac: true })` + `T3.relX(...)` 代码。

### 4. 快速预览（`preview`）
1. 先跑静态检查：`node "<SKILL_DIR>/scripts/motion_lint.mjs" web/index.html`（有 FAIL 先修）。
2. 经 `run_queue.py web` 同步生成：
   - SVG 曲线图：`motion_lint.mjs web/index.html --curves --out work/motion_preview`
   - 关键帧拼图：`snap.mjs web/index.html work/snaps "<f0>-<f1>:6" --sheet preview --fps <FPS>`
   - 720p 带音乐预览 MP4：`render_fast.mjs web/index.html <start> <end> out/preview.mp4 --scale 0.6667 --fps <FPS>`
3. 亲眼审完曲线图与关键帧后再把预览交给用户。

### 5. 三视角物理只读终审（`review`）
1. 先跑 Gate B1：`python -X utf8 "<SKILL_DIR>/scripts/run_queue.py" web --lane qa -- node "<SKILL_DIR>/scripts/qa.mjs" web/index.html --from <start> --to <end>`。
2. 写 `work/REVIEW_BRIEF.md`（写清主动打破的默认项及原因），运行 `<SKILL_DIR>/assets/workflows_agy/review_fix.py`（`chiaki-reviewer` `pro` 三视角审片 → 三复核 → `chiaki-builder` `flash` 最小化修改 → `chiaki-reviewer` `flash` 逐条截图复验）。主线程严禁代审。

### 6. 终混与交片（`deliver`）
1. 派独立 **声音设计师** (`chiaki-builder`, `Model="flash"`) 读 `work/cues.csv`，用 `<SKILL_DIR>/assets/mgaudio` 产出 `-14 LUFS / <= -1.1 dBTP` 48 kHz 母带 `work/master.wav` 与响度报告。
2. 经 `run_queue.py web` 渲染 1080p/720p 成片与 2K (`--2k`)，按 `references/production.md` §4 封装 48 kHz FLAC 2K 母版。
3. 派物理只读 **独立成片评分员** (`chiaki-reviewer`, `Model="pro"`, `assets/workflows/score_brief.md`) 按 7 维严格打分（每维 ≥ 8 及格）。
4. 导出开源字体片尾鸣谢：`python -X utf8 "<SKILL_DIR>/scripts/fonts.py" credits <project>`，一并交付。

### 7. 巡检（`status`）
只读汇总：当前目录项目进度、最近曲线图/QA 状态、`python -X utf8 "<SKILL_DIR>/scripts/run_queue.py" --status` 以及 `doctor.py` 环境概况。
