---
name: chiaki
description: Chiaki's-video-skill 统一快捷入口（/chiaki、/Chiaki 与 Codex $chiaki）：一条指令覆盖依赖体检安装向导（/chiaki 检查依赖 或 /chiaki setup）与旗舰级 13 步 2D + 2.5D + Blender 3D 动效视频全流程 — 开新片（/chiaki 或 /chiaki new）、多源出图（/chiaki art）、选字打包（/chiaki fonts）、Blender 3D 与 2.5D 浮雕/投影/免费素材（/chiaki 3d 或 /chiaki relief）、快速预览与曲线图（/chiaki preview）、三视角物理只读终审（/chiaki review）、终混渲染与独立打分→修一轮→重渲→Gate B2（/chiaki deliver）、进度与环境体检（/chiaki status）。仅在用户明确写 /chiaki、/Chiaki、$chiaki 或要求按 Chiaki's-video-skill 做视频/检查依赖时使用。
---

# `/chiaki`（Codex: `$chiaki`）— Chiaki's-video-skill 统一工作台入口

> 主技能目录 `<SKILL_DIR>`（若本文件被直接复制未自动替换占位符，则取同级目录 `../chiakis-video-skill`）。

先用文件读取工具按 UTF-8 读取主技能 `<SKILL_DIR>/SKILL.md`、`references/personas.md`、`references/house-style.md`、`references/crafts.md`、`references/motion-library.md` 与 `references/quality-bar.md`。涉及出图先读 `references/art-pipeline.md`，涉及景深或 Blender 3D 再读 `references/3d.md`。

> **硬性工作室分工纪律**：你只担任**总导演兼制片人**，绝不退化成「主线程大包大揽写完所有代码再自审」。每次调用 `chiaki-writer` / `chiaki-builder` / `chiaki-reviewer`（或 Codex/Claude 等价子代理）必须在 Prompt 顶部贴入 `references/personas.md` 原话身份与性格、附 `references/crafts.md` 工种卡与任务简报、并显式锁定 `Model`（`pro` / `flash` / `flash_lite`）；所有无头 Chrome 与 `blender -b` 命令一律经 `<SKILL_DIR>/scripts/run_queue.py` 排队执行。
>
> **宿主多模态死规矩（`rules/AGENTS.md` §3）**：**Gemini 宿主（Antigravity）**听音与审片**必须直接用 `read_file` 原生多模态直听 `.wav`/`.mp3`（`vocal_spec.py --wav-only`）并直看带声 720p/1080p `.mp4` 成片/分幕视频**，严禁跳过看视频仅凭静态拼图或频谱图审节奏、动效与对口型；**Claude / Codex 宿主**严格走**传统频谱分析（`vocal_spec.py` 声谱图 + `beats.py`/`onsets.py`）+ `snap.mjs` 密集截图拼图 + `motion_lint --curves` SVG 曲线图**路线。

---

## 子指令路由（解析 `/chiaki` 或 `$chiaki` 后的第一个词）

| 用户输入 | 路由动作 |
|---|---|
| `/chiaki setup`、`/Chiaki 检查依赖`、`/chiaki doctor` 或 `$chiaki 检查依赖` | **0. 交互式依赖体检与安装向导（先查 → 问需求与安装路径 → 一键配置）** |
| `/chiaki`、`$chiaki`、`/chiaki new <想法>` 或直接粘贴填好的需求表 | **1. 开新片（完整 13 步旗舰流）** |
| `/chiaki art <项目路径>` | **2. 多源出图与素材验收（`art_manifest.json` + `art_gen.py`）** |
| `/chiaki fonts [关键词 / 项目路径]` | **3. 选字、测缺字与本地打包** |
| `/chiaki 3d <需求>` 或 `/chiaki relief <图片路径> [参数]` | **4. Blender 2.5D 浮雕 · 相机投影 · 实景搭景 · 免费 3D 素材 · MCP 调光** |
| `/chiaki preview [起止秒]` | **5. 静态动效检查 + 720p 预览 + SVG 曲线图** |
| `/chiaki review` | **6. Gate B1 自查 + 三视角物理只读终审与复核** |
| `/chiaki deliver` | **7. 母带 → 一版渲染 → 独立 7 维打分 → 修一轮+质检 → 重渲 2K FLAC → Gate B2** |
| `/chiaki status` | **8. 只读项目进度、渲染队列与环境体检** |
| `/chiaki help` | 打印本速查表并询问下一步 |

---

## 各子指令执行流程

### 0. 交互式依赖体检与安装向导（`setup` / `检查依赖` / `安装依赖` / `doctor`）
**原则：先只读体检，再询问用户「要装什么」和「想装在哪里」，绝不未经确认私自往系统盘塞大包。**
1. **只读全盘体检**：运行 `python -X utf8 "<SKILL_DIR>/scripts/doctor.py" --json`，把结果整理成一张简明中文状态表发给用户（区分「核心 2D 必选」「Blender 3D / MCP 可选」「2.5D AI 深度图可选」）。
2. **向用户确认两件事**（如果一切已全绿，直接告知已就绪无需安装；如有缺项或用户想补齐可选功能，则一次问清）：
   - **① 需要哪一档功能？**
     - **`2d`（轻量纯 2D 版）**：仅补齐核心渲染/字体/音效依赖（`requirements.txt`，约 180 MB），不装 Blender 和 PyTorch；
     - **`3d`（2D + Blender 3D / MCP 旗舰版）**：核心 2D + 绑定 Blender 路径（`CHIAKI_BLENDER`）+ 免费 3D 素材缓存（`CHIAKI_ASSETS3D`）+ 自动把零依赖 `scripts/blender/mcp_bridge.py` 接入当前 AI 客户端（Antigravity / Codex / Claude Code）；
     - **`full`（全功能满血版）**：以上全部 + 2.5D AI 深度图依赖（`torch` + `transformers`，约 1.5–3 GB）。
   - **② 想安装/存放到哪个目录或盘符？**
     - Python 虚拟环境路径（例如默认 `<SKILL_DIR>/.venv`，或指定非 C 盘目录如 `D:\AI\chiaki-venv`；也可选择直接装入当前 Python）；
     - 若选 `3d`/`full`：本机已有 `blender.exe` 的路径（若未装，给出 Windows `winget` / macOS `brew` / 官网安装引导）、3D 素材库缓存目录（`CHIAKI_ASSETS3D`）、以及是否自动配置当前 AI 客户端的 Blender MCP；
     - 可选共享字体库目录（`CHIAKI_FONTS`）。
3. **经用户点头后一键落地并复查**：
   - 运行 `python -X utf8 "<SKILL_DIR>/scripts/setup_env.py" --profile <2d|3d|full> --venv "<用户指定路径>" [--blender "<路径>"] [--assets3d "<路径>"] [--fonts-dir "<路径>"] [--wire-mcp <antigravity|codex|claude|none>]`（先跑 `--dry-run` 或直接按确认方案执行）。
   - 若缺 **Node.js ≥ 22** 或 **Chrome/Edge** 等系统软件，给出对应系统的一键命令（如 `winget` / `brew`）或在用户明确同意后代为执行。
   - 装完自动用目标 Python 重跑 `doctor.py`，把最终全绿验收报告发给用户。

### 1. 开新片（13 步旗舰全流程：`new` 或直接写需求）
1. **环境体检 & Brief**：跑 `python -X utf8 "<SKILL_DIR>/scripts/doctor.py"`；补齐主题、幕数、时长、FPS（24/30）、音乐、**音效策略**（成曲/歌词 PV 默认纯原曲洁净母带 `pure_song`；片头/宣传片/原创编曲默认全套 `full_sfx`）、出图路线（`user_files` / `gemini` / `codex` / `custom_api` / `code_only`）、Blender 3D 范围并一行汇报；有音乐立即跑 `scripts/beats.py` + `scripts/onsets.py` 锁鼓点，**带人声歌词的成曲 PV 按宿主死规矩执行：Gemini 跑 `vocal_spec.py --wav-only` 用 `read_file` 原生直听微 WAV 锁起唱帧，Claude/Codex 跑 `vocal_spec.py` 查 300Hz–4kHz 帧号声谱图**。
2. **开工前一行报成本**：说明预计子代理数、模型档位与总耗时。
3. **提案会（3 套方案）**：跑 `<SKILL_DIR>/assets/workflows_agy/pitch.py`（或 `assets/workflows/pitch.js`）：媒介设计师 / 演出策划 / 摄影指导并行交 3 份方案 → 创意总监拍板 → 执行制片核查各幕不撞型（15 种 `mg-styles.md` 严禁同片重复）。
4. **分镜表 + Gate A（先锁分镜再出图）**：写完整分镜表（精确有理数帧界、人声起唱帧、镜头配方 `shot-recipes.md`、动效 ID、出图来源、`work/cues.csv`）和 `work/art_manifest.json`，**先过 Gate A 再动出图额度**。
5. **多源出图与资产准备**：按 `references/art-pipeline.md` 跑 `scripts/art_gen.py run <proj> --workers 3`（支持多参考图 `refs` 与自动重试，或调用宿主自带 Gemini/Codex 生图）→ 原尺寸肉眼验图 → 按需用 `vision/segment.py` 抠图 / `vision/pasteback.py --align --lf 40` 对齐补图 → 打包本地字体（`fonts.py use`，描边字用 `--static`）→ 纸纹高反差提取（`prep_texture.py`）→ 16-bit 柔化深度图（`vision/depth.py --soften`）与免费 3D 素材（`assets3d.py`）。
6. **三工种并行搭建**：拷贝 `<SKILL_DIR>/assets/template/` 到 `<proj>/web/`，按 `build.py` / `build.js` 严格分工 **3D 工程师 (`flash`)** + **剪辑合成师 (`pro`)** + **平面设计师 (`flash`)**（全片统一纸纹/颗粒罩层放 `z=45` `film_texture.js`）→ 执行导演一版看样 (`pro`) → **按工种并行修改员 (`flash`)** → 质检 (`flash`)。
7. **自查（Gate B1）**：静态 `motion_lint.mjs`（0 FAIL）+ `--curves` SVG 曲线图（核查 `Q1` 滞后及 `> 0.90` 悬崖长死尾）+ `qa.mjs` + `snap.mjs --sheet` + 空间 `parallax.py` + 定格 `cadence.py`。
8. **声音设计与母带**：派独立 **声音设计师** (`flash`) 按所选音效策略执行 —— 成曲/歌词 PV 默认 `pure_song` 洁净母带（零额外 swoosh 干扰人声），片头/原创配乐走 `assets/mgaudio` + Freesound 全套混音与压低 —— 统一母带至 `-14 LUFS / <= -1.1 dBTP` 48 kHz `work/master.wav`。
9. **初版三视角内审**：运行 `review_fix.py` / `review_fix.js`（物理只读 `规矩·技术·剪辑感` 三视角 → 三复核 → 定向修阻断项 → 质检；短片 `< 60 s` 快速通道优先清零阻断项直奔带声一版渲染）。
10. **一版带声渲染**：经 `run_queue.py web` 先出带 `master.wav` 的 720p/1080p 一版全片 MP4（`out/film_v1.mp4`；纸纹/胶片感影片加 `--grain` 保颗粒）。
11. **独立 7 维评分 → 修一轮 → 质检**：运行 `polish_rerender.py` / `polish_rerender.js`（物理只读 `独立成片评分员` `pro` 按 `score_brief.md` 严格打分，歌词 PV 必抽查 ≥ 2 句高潮人声对口型，每维 ≥ 8 及格 → 若有扣分项则派 `修改员` `flash` 定向修一轮 → `质检` `flash` 逐条原尺寸复验）。
12. **重渲染定稿 & 复评**：审片确认后升渲 1080p Web + 2K `--2k`（纹理片带 `--grain`）并封装 48 kHz FLAC 母版，由只读评分员复验扣分项已达标。
13. **Gate B2 交付**：核验硬指标 + 开源鸣谢（`fonts.py credits` 与 `assets3d.py credits`），交付成片、评分卡、决策记录与已验证/未验证清单。

### 2. 多源出图与素材验收（`art`）
先读 `<SKILL_DIR>/references/art-pipeline.md`，然后按需执行：
- 初始化清单：`python -X utf8 "<SKILL_DIR>/scripts/art_gen.py" init <project>`
- 干跑预览：`python -X utf8 "<SKILL_DIR>/scripts/art_gen.py" run <project> --dry`
- 执行出图/复制：`python -X utf8 "<SKILL_DIR>/scripts/art_gen.py" run <project>`（或按清单调用当前宿主自带的 Gemini / Codex 生图工具）
- 完整性核验：`python -X utf8 "<SKILL_DIR>/scripts/art_gen.py" check <project>`，并原尺寸肉眼验收每张图。

### 3. 选字与打包（`fonts`）
1. 先离线检索内置 59 套商用开源字库：`python -X utf8 "<SKILL_DIR>/scripts/fonts.py" search --local <关键词或分组>`（需要更多字体再搜在线 `search` 并 `get`）。
2. 有歌词或标题文案时带 `--text "<文案>"` 检查缺字，给出 2–3 套风格搭配建议。
3. 确认后执行 `python -X utf8 "<SKILL_DIR>/scripts/fonts.py" use <project> "<字体1>" "<字体2>"` 子集化 WOFF2 + Base64 注入项目（空心描边字自动加 `--static` 合并轮廓）。

### 4. Blender 2.5D 浮雕与真 3D（`3d` / `relief`）
先读 `<SKILL_DIR>/references/3d.md`，严禁未排队直接跑 `blender -b`：
- **2.5D 深度浮雕 (`relief`)**：`vision/depth.py --bits 16 --soften` → `run_queue.py blender -- blender -b --python <SKILL_DIR>/scripts/blender/depth_relief.py -- ...` → `vision/parallax.py` 验收 → 前端用 `T3.sequence({ frac: true })` + `T3.relX(...)`。
- **相机投影推入 (`projection`)**：拷贝 `<SKILL_DIR>/scripts/blender/projection/` → `design.py sim/build` → `textures.py` → `run_queue.py blender -- blender -b --python dolly_scene.py` → 逐帧播放（不用 `T3.relX`）。
- **实景 3D 搭景 & 免费素材 (`assets3d`)**：`assets3d.py search/get --project <proj>` + `asset_lib.py`（`use_hdri` / `pbr_material` / `import_model` / `emissive_card` / `contact_shadow` / `anime_look`）；有 **Blender MCP**（`127.0.0.1:9876`）时用于实时调光看样，批量出帧仍走 `run_queue.py blender`。

### 5. 快速预览（`preview`）
1. 先跑静态检查：`node "<SKILL_DIR>/scripts/motion_lint.mjs" web/index.html`（有 FAIL 先修）。
2. 经 `run_queue.py web` 生成 SVG 曲线图（`--curves`）、关键帧拼图（`snap.mjs --sheet`）与 720p 带音乐预览（`render_fast.mjs --scale 0.6667`），审完再发给用户。

### 6. 自查与三视角终审（`review`）
1. 跑 Gate B1：`python -X utf8 "<SKILL_DIR>/scripts/run_queue.py" web --lane qa -- node "<SKILL_DIR>/scripts/qa.mjs" web/index.html --from <start> --to <end>`。
2. 写 `work/REVIEW_BRIEF.md`，运行 `review_fix.py` / `review_fix.js`（三视角审片 → 三复核 → 最小化修复 → 质检）。主线程严禁代审。

### 7. 终混、独立评分、修一轮、重渲与 Gate B2（`deliver`）
1. 独立 **声音设计师** (`flash`) 产出 `-14 LUFS` `work/master.wav`。
2. 经 `run_queue.py web` 渲染 V1 带声全片 `out/film_v1.mp4`。
3. 运行 `polish_rerender.py` / `polish_rerender.js`：独立 7 维评分（`pro`）→ 若有扣分则定向修一轮（`flash`）→ 质检（`flash`）。
4. 重渲染 1080p + 2K (`--2k`) + 48 kHz FLAC 母版，复评确认全维 ≥ 8，过 Gate B2，附 `fonts.py credits` 与 `assets3d.py credits` 交付。

### 8. 巡检（`status`）
只读汇总：当前目录项目进度、最近曲线图/QA 状态、`run_queue.py --status` 以及 `doctor.py` 环境概况（含 Blender 与 Blender MCP 状态）。
