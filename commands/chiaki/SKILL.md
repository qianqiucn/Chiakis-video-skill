---
name: chiaki
description: Chiaki's-video-skill 统一快捷入口（/chiaki、/Chiaki 与 Codex $chiaki）：一条指令覆盖依赖体检安装向导（/chiaki 检查依赖 或 /chiaki setup）与旗舰级 13 步 2D + Three.js 风格化 3D + Blender 电影级 3D 双引擎动效视频全流程 — 开新片（/chiaki 或 /chiaki new）、多源出图（/chiaki art）、选字打包与 3D 挤出字形（/chiaki fonts）、Three.js 3D 字/棱镜/百叶窗与 Blender 2.5D 浮雕/投影/免费素材（/chiaki 3d 或 /chiaki relief）、快速预览与曲线图（/chiaki preview）、三视角物理只读终审（/chiaki review）、终混渲染与独立打分→修一轮→重渲→Gate B2 偏好复盘（/chiaki deliver）、自迭代记忆管理与开关（/chiaki memory）、进度与环境体检（/chiaki status）。仅在用户明确写 /chiaki、/Chiaki、$chiaki 或要求按 Chiaki's-video-skill 做视频/检查依赖时使用。
---

# `/chiaki`（Codex: `$chiaki`）— Chiaki's-video-skill 统一工作台入口

> 主技能目录 `<SKILL_DIR>`（若本文件被直接复制未自动替换占位符，则取同级目录 `../chiakis-video-skill`）。

先用文件读取工具按 UTF-8 读取主技能 `<SKILL_DIR>/SKILL.md`、`references/personas.md`、`references/house-style.md`、`references/crafts.md`、`references/motion-library.md`、`references/quality-bar.md` 与量化标杆 `references/benchmark-quality.md`。涉及出图先读 `references/art-pipeline.md`，涉及景深或 Blender 3D 再读 `references/3d.md`。

> **硬性工作室分工纪律**：你只担任**总导演兼制片人**，绝不退化成「主线程大包大揽写完所有代码再自审」。每次调用 `chiaki-writer` / `chiaki-builder` / `chiaki-reviewer`（或 Codex/Claude 等价子代理）必须在 Prompt 顶部贴入 `references/personas.md` 原话身份与性格、附 `references/crafts.md` 工种卡与任务简报、并显式锁定 `Model`（`pro` / `flash` / `flash_lite`）；所有无头 Chrome 与 `blender -b` 命令一律经 `<SKILL_DIR>/scripts/run_queue.py` 排队执行。
>
> **宿主多模态与人音双轨分离死规矩（`rules/AGENTS.md` §3）**：只要用户给了外部音乐文件，**开剪写分镜前第一件事先跑 `scripts/stem_sync.py`** 拆轨并自动判别有无唱词（`has_vocals`）——检出人声则纯伴奏 `instrumental.wav` 测鼓与局部 BPM 漂移、纯干人声 `vocals.wav` 锁逐字，纯器乐则自动跳过干声图与 Whisper；**Gemini 宿主（Antigravity）**听音与审片**必须直接用 `read_file` 原生多模态直听干人声 `.wav` 并直看带声 720p/1080p `.mp4` 成片/分幕视频**，严禁跳过看视频仅凭静态拼图或混合频谱图审节奏、动效与对口型；**Claude / Codex 宿主**严格走**干声声谱（`dry_*.png` / `vocal_spec.py vocals.wav` + `vocal_words.json`）+ 纯伴奏 `beats.py`/`onsets.py` + `snap.mjs` 密集截图拼图 + `motion_lint --curves` SVG 曲线图**路线。
>
> **Gemini / AGY 专属导演纪律（`rules/AGENTS.md` §4–§5 · Claude Opus 豁免）**：在 Gemini / Antigravity 会话中，> 30 s 中长片须先做出 **10–16 s Gate A 黄金样板**（含总导演独占共享引擎 + 分幕 HTML + `scripts/visual_metrics.py` 饱和度/实黑/帧差波形体检）再开 Swarm 铺全片；Swarm 指挥须大改先 `kill` 清上下文、动态歌词 PV 优先 1 幕 1 全栈单画布、两段门禁审分镜跨幕查重并锁 `open.actN` 纯函数预调用接缝、总导演集中出图（≤ 4 张/幕）+ 占位并行 + 交图附朝向/裁切/尺度/动效备注、公屏 3–6 行去情绪短帖；把 Skill 当零件军火库灵活组合 `T3.look.coat`/`bakePrint`/`lumaMatte`/`okMix` + `T3.blur.shutter`（不服务母题的工具主动弃用）；汇报只写事实与数字严禁自夸词；Claude Opus 完全豁免此节额外限制。

---

## 子指令路由（解析 `/chiaki` 或 `$chiaki` 后的第一个词）

| 用户输入 | 路由动作 |
|---|---|
| `/chiaki setup`、`/Chiaki 检查依赖`、`/chiaki doctor` 或 `$chiaki 检查依赖` | **0. 交互式依赖体检与安装向导（先查 → 问需求与安装路径 → 一键配置）** |
| `/chiaki`、`$chiaki`、`/chiaki new <想法>` 或直接粘贴填好的需求表 | **1. 开新片（先问本期额度档位 `Lite`/`Pro`/`Ultra` → 自动匹配精简/满血流程）** |
| `/chiaki tier [lite\|pro\|ultra]` | **1b. 查看或切换默认推荐额度档位（`memory.py tier`）** |
| `/chiaki art <项目路径>` | **2. 多源出图、在线质感层/实拍层挑拣下载与验收（`art_gen.py` + `media_lib.py`）** |
| `/chiaki fonts [关键词 / 项目路径]` | **3. 选字、测缺字与本地打包** |
| `/chiaki 3d <需求>` 或 `/chiaki relief <图片路径> [参数]` | **4. 双 3D 旗舰：Three.js 风格化 3D 字/场景/棱镜/百叶窗 + Blender 2.5D 浮雕/投影/搭景/MCP** |
| `/chiaki preview [起止秒]` | **5. 静态动效检查 + 720p 预览 + SVG 曲线图** |
| `/chiaki review` | **6. Gate B1 自查 + 三视角物理只读终审与复核** |
| `/chiaki deliver` | **7. 母带 → 一版渲染 → 独立 7 维打分 → 修一轮+质检 → 重渲 2K FLAC → Gate B2** |
| `/chiaki status` | **8. 只读项目进度、渲染队列与环境体检** |
| `/chiaki memory [show\|mode <ask\|auto\|readonly\|off>\|forget <ID>\|reset]` | **9. 工作室自迭代记忆：查喜好/避坑/履历、切开关、删条或重置** |
| `/chiaki help` | 打印本速查表并询问下一步 |

---

## 各子指令执行流程

### 0. 交互式依赖体检与安装向导（`setup` / `检查依赖` / `安装依赖` / `doctor`）
**原则：先只读体检，再询问用户「要装什么」和「想装在哪里」，绝不未经确认私自往系统盘塞大包。**
1. **只读全盘体检**：运行 `python -X utf8 "<SKILL_DIR>/scripts/doctor.py" --json`，把结果整理成一张简明中文状态表发给用户（区分「核心 2D 必选」「Blender 3D / MCP 可选」「2.5D AI 深度图可选」）。
2. **向用户确认三件事**（若核心依赖已全绿且 `studio_memory.initialized` 为 `true`，直接告知已就绪无需配置；否则把未配项一次问清）：
   - **① 需要哪一档功能？**
     - **`2d`（2D 动效 + 人音分离卡点版）**：核心渲染/字体/音效依赖（`requirements.txt`）+ **人声/伴奏分离与逐字对齐工具（`audio-separator` + `faster-whisper`，自动适配 N 卡 CUDA；如只需 ~180 MB 极简纯 2D 可加 `--no-stems` 跳过）**；
     - **`3d`（2D + 人音分离 + Blender 3D / MCP 旗舰版）**：以上全部 + 绑定 Blender 路径（`CHIAKI_BLENDER`）+ 免费 3D 素材缓存（`CHIAKI_ASSETS3D`）+ 自动把零依赖 `scripts/blender/mcp_bridge.py` 接入当前 AI 客户端（Antigravity / Codex / Claude Code）；
     - **`full`（全功能满血版）**：以上全部 + PyTorch 视觉依赖（`vision/cutout.py` MIT 2K 抠图、`vision/part_cutout.py` 二次元 19 部位精拆与 `vision/depth.py` 深度图）。
   - **② 想安装/存放到哪个目录或盘符？**
     - Python 虚拟环境路径（例如默认 `<SKILL_DIR>/.venv`，或指定非 C 盘目录如 `D:\AI\chiaki-venv`；也可选择直接装入当前 Python）；
     - 分人声/Whisper 模型缓存目录（`CHIAKI_STEM_MODELS`，建议放非 C 盘；如本机已有现成 `audio-separator`/`demucs` 环境可直接传 `--stem-python <python路径>` 复用，免重装）；
     - 若选 `3d`/`full`：本机已有 `blender.exe` 的路径（若未装，给出 Windows `winget` / macOS `brew` / 官网安装引导）、3D 素材库缓存目录（`CHIAKI_ASSETS3D`）、以及是否自动配置当前 AI 客户端的 Blender MCP；
     - 若选 `full`：HuggingFace AI 模型权重缓存目录（`HF_HOME`，建议指到非 C 盘目录防占满系统盘；`setup_env.py` 会自动检测 N 卡安装 CUDA `cu128` 版 PyTorch）；
     - 可选共享字体库目录（`CHIAKI_FONTS`）。
   - **③ 是否开启「工作室自迭代记忆」？（仅首次未初始化时问一次，以后永不重复打扰）**
     - 选模式：`ask`（默认推荐：每片完片出 ≤ 5 行确认卡，点头再记）/ `auto`（完片自动沉淀）/ `readonly`（只读不写）/ `off`（关闭）；
     - 存哪儿：默认 `~/.chiaki-studio/`（独立于 Skill 仓库、升级永不丢失、三端共享），或指定自定义目录（`CHIAKI_MEMORY_DIR`）。
3. **经用户点头后一键落地并复查**：
   - 运行 `python -X utf8 "<SKILL_DIR>/scripts/setup_env.py" --profile <2d|3d|full> --venv "<用户指定路径>" [--stem-models "<路径>" | --stem-python "<路径>" | --no-stems] [--blender "<路径>"] [--assets3d "<路径>"] [--fonts-dir "<路径>"] [--hf-home "<路径>"] [--memory-mode <ask|auto|readonly|off>] [--memory-dir "<路径>"] [--wire-mcp <antigravity|codex|claude|none>]`（先跑 `--dry-run` 或直接按确认方案执行）。
   - 若缺 **Node.js ≥ 22** 或 **Chrome/Edge** 等系统软件，给出对应系统的一键命令（如 `winget` / `brew`）或在用户明确同意后代为执行。
   - 装完自动用目标 Python 重跑 `doctor.py`，把最终全绿验收报告发给用户。

### 1. 开新片（额度自适应三档流：`new` 或直接写需求）
1. **环境体检 & 必问「本期额度档位」**：跑 `python -X utf8 "<SKILL_DIR>/scripts/doctor.py" --json`；若用户未在首句/需求表里显式指定档位，**每次开新片先用极简单选询问本期额度档位**（默认高亮 `studio_memory.quota_tier` 上次选择，向 Pro 用户推荐 **`Pro` 均衡主力流**），选定后用 `memory.py tier <lite|pro|ultra>` 记住下次默认项：
   - **`Lite` 极简省额流**（省 ~85% · 4 幕约 6–8 代理 / 2–3 `pro`）：主线程 2 个 3 行方向秒选 → 1 幕 1 全栈单画布（副歌 `pro` / 过渡 `flash`）→ 成曲主线程脚本直出母带 → 直出 V1 带声片 → 1 名只读 `pro` 综合审片评分 → 原代理热修 1 轮 → 重渲定稿；
   - **`Pro` 均衡主力流（推荐 Pro / Plus）**（省 ~70–75% · 4 幕约 10–14 代理 / 4–6 `pro`）：主线程 2–3 个跨幕方向简案拍板 → 中长片先打穿 10–16 s 样板 → 1 幕 1 全栈单画布（按需挂 `flash` 3D 师）→ `flash` 声音师出 `-14 LUFS` 母带 → 合并 Stage 9+11（直出 V1 后 1 名只读 `pro` 独立 7 维评委 → 原代理热修 1 轮 → 1 名只读 `flash` QC → 重渲 2K FLAC）；
   - **`Ultra` 满血旗舰流**（Max / Ultra · 4 幕约 50–70 代理 / ~33 `pro`）：完整 13 步（每幕 3 路盲写提案会 + 三工种分拆 + Dailies + Stage 9 三视角三复核 + Stage 11–13 独立评分与多轮精修）。
   - 若 `studio_memory.initialized` 为 `false` 且需求表未填记忆开关，顺带问一次 `ask`/`auto`/`off` 并落盘。补齐主题、幕数、时长、FPS（24/30）、音乐、**音效策略**（`pure_song` / `full_sfx`）、出图路线、**3D 引擎规格**并一行汇报；**只要用户提供了外部音乐文件，开剪写分镜前第一件事先跑 `scripts/stem_sync.py <audio> --out <proj>/work/stems --fps <FPS> [--whisper --lyrics <txt>]`** 自动判别有无唱词并拆双轨（检出人声走纯伴奏测鼓+纯干声锁字，纯器乐自动跳过干声图与 Whisper）。
2. **开工前一行报预算**：按所选档位写明预计子代理总数、`pro`/`flash` 次数与总耗时（如：`Pro 均衡档 · 预计 12 代理 [5 pro + 7 flash]`）。
3. **提案定方向**：
   - **`Lite` / `Pro`**：总导演（主线程）查 `memory.py context --stage pitch` 防撞型后，直接给出 **2（Lite）或 2–3（Pro）套紧凑跨幕方向简案**（媒介、色板、核心母题、字体，不撞型）让用户直接拍板（`0` 提案子代理）；
   - **`Ultra`**：跑 `<SKILL_DIR>/assets/workflows_agy/pitch.py`（或 `pitch.js`）每幕 3 路盲写 → 创意总监 → 执行制片。
4. **分镜表 + Gate A（先锁分镜再出图）**：写完整分镜表（精确有理数帧界、人声起唱帧、动效 ID 白名单、出图来源、`work/cues.csv`）和 `work/art_manifest.json`；**每幕简报顶部附 20 行浓缩工艺卡**（省掉子代理重复冷读 6 本参考书）；先过 Gate A 再动出图额度。
5. **多源出图与资产准备**：按 `references/art-pipeline.md` 跑 `art_gen.py` → 肉眼验图 → 按需 `vision/cutout.py` / `part_cutout.py` / `pasteback.py` → `media_lib.py` 下载免 Key 质感层与实拍层 → `fonts.py use`（含 `glyph3d`）→ `vision/depth.py` / `assets3d.py`。
6. **按档搭建**：拷贝 `<SKILL_DIR>/assets/template/` 到 `<proj>/web/`，运行 `build.py` / `build.js`（传 `tier="lite"|"pro"|"ultra"`）或 Swarm：
   - **`Lite` / `Pro`**：1 幕 1 全栈单画布（真需 Blender 3D 才按幕挂 `flash` 3D 师），跳过幕内 Dailies/QC，保留原制作代理上下文待热修；
   - **`Ultra`**：三工种并行分拆 → 执行导演一版看样 (`pro`) → 分工种修改员 (`flash`) → 质检 (`flash`)。
7. **本地 0 额度硬检（Gate B1，三档全保留）**：静态 `motion_lint.mjs`（0 FAIL）+ `--curves` SVG 曲线图 + `qa.mjs` + `visual_metrics.py` + `parallax.py`/`cadence.py`。
8. **声音设计与母带**：`Lite` 成曲 PV 可由主线程直接脚本母带至 `-14 LUFS / <= -1.1 dBTP` 48 kHz `work/master.wav`；`Pro`/`Ultra` 或原创配乐派独立 `声音设计师` (`flash`)。
9. **终审、一版渲染与独立评分精修闭环**：
   - **`Lite` / `Pro`（合并 Stage 9+11）**：直接经 `run_queue.py web` 渲染带声一版 `out/film_v1.mp4` → 运行 `polish_rerender.py` / `.js`（`tier="lite"|"pro"`）：**1 名物理只读 `pro` 独立评分审片员**直看带声片出 7 维分与帧级问题单 → **优先向原制作代理发消息热修 1 轮**（或 `flash` 修改员）→ `Pro` 跑 1 名只读 `flash` QC 复验（`Lite` 静态 lint + 抽帧确认后跳过独立 QC）；
   - **`Ultra`**：先跑 `review_fix`（三视角+三复核+修+QC）→ 渲 V1 → 再跑 `polish_rerender`（独立 7 维评委 → 修改员 → QC）。
10. **重渲染定稿 & Gate B2 交付 + 必发偏好复盘卡**：升渲 1080p Web + 2K `--2k`（纹理片带 `--grain`）+ 48 kHz FLAC 母版，过 Gate B2 并附开源鸣谢；只要 `memory.mode` 非 `off`/`readonly`，**必须**运行 `memory.py draft-card` 把「🧠 下支片想怎么更合你胃口？」附在最终交付消息末尾。

### 1b. 查看或切换默认额度档位（`tier`）
- 查看当前默认档位：`python -X utf8 "<SKILL_DIR>/scripts/memory.py" status`
- 切换推荐默认档位：`python -X utf8 "<SKILL_DIR>/scripts/memory.py" tier <lite|pro|ultra>`（下次开新片仍会单选确认一次，并高亮此默认项）。

### 2. 多源出图、在线质感/实拍素材与验收（`art`）
先读 `<SKILL_DIR>/references/art-pipeline.md`，然后按需执行：
- 初始化/干跑/出图/验收：`art_gen.py init|run|check <project>`（或调用当前宿主自带的 Gemini / Codex 生图工具）并原尺寸肉眼验图；
- 在线免 Key 挑拣下载质感层与实拍层：`python -X utf8 "<SKILL_DIR>/scripts/media_lib.py" search texture|footage "<关键词>"` → `media_lib.py get <provider> <id> --project <project> [--prep paper|stone|grain | --seq --fps 24 --dur 5]`（自动缓存、抽帧并记录鸣谢到 `work/media_used.json`）。

### 3. 选字与打包（`fonts`）
1. 先离线检索内置 59 套商用开源字库：`python -X utf8 "<SKILL_DIR>/scripts/fonts.py" search --local <关键词或分组>`（需要更多字体再搜在线 `search` 并 `get`）。
2. 有歌词或标题文案时带 `--text "<文案>"` 检查缺字，给出 2–3 套风格搭配建议。
3. 确认后执行 `python -X utf8 "<SKILL_DIR>/scripts/fonts.py" use <project> "<字体1>" "<字体2>"` 子集化 WOFF2 + Base64 注入项目（空心描边字自动加 `--static` 合并轮廓）。

### 4. 双 3D 旗舰：Three.js 风格化 3D + Blender 电影级 3D（`3d` / `relief`）
先读 `<SKILL_DIR>/references/3d.md`（含 §5e Three.js Graphic-3D），严禁未排队直接跑 `blender -b`：
- **Three.js 风格化 3D（免装、2D 原生质感、与 Blender 并列旗舰）**：在 `index.html` 引入内置 `lib/three/three.min.js` + `lib/three_kit.js`，用 `fonts.py glyph3d <proj> "<字体>" "<文案>"` 离线提取紧凑中/日/英 3D 矢量轮廓，按镜头选用 `T3.three.extrudeText`（真 3D 挤出立体字：`flat`/`toon`+黑描边/`glass`/`wire`）、`textRing`（角色 Z 夹心 360° 歌词环）、`textCorridor`（3D 歌词走廊）、`prismOverlay`（实时色散玻璃棱镜折穿 2D 画面）、`louverTransition`（`z=60` 3D 百叶窗翻转转场）、`field`（风格化 3D 几何空间）与 `relief`（免 Blender GPU 深度浮雕）。
- **Blender 2.5D 深度浮雕 (`relief`)**：`vision/depth.py --bits 16 --soften` → `run_queue.py blender -- blender -b --python <SKILL_DIR>/scripts/blender/depth_relief.py -- ...` → `vision/parallax.py` 验收 → 前端用 `T3.sequence({ frac: true })` + `T3.relX(...)`。
- **Blender 相机投影推入 (`projection`)**：拷贝 `<SKILL_DIR>/scripts/blender/projection/` → `design.py sim/build` → `textures.py` → `run_queue.py blender -- blender -b --python dolly_scene.py` → 逐帧播放（不用 `T3.relX`）。
- **Blender 实景 3D 搭景 & 免费素材 (`assets3d`)**：`assets3d.py search/get --project <proj>` + `asset_lib.py`（`use_hdri` / `pbr_material` / `import_model` / `emissive_card` / `contact_shadow` / `anime_look`）；有 **Blender MCP**（`127.0.0.1:9876`）时用于实时调光看样，批量出帧仍走 `run_queue.py blender`。

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
4. 重渲染 1080p + 2K (`--2k`) + 48 kHz FLAC 母版，复评确认全维 ≥ 8，过 Gate B2，附 `fonts.py credits`、`media_lib.py credits` 与 `assets3d.py credits` 交付。
5. **必发偏好复盘卡（Gate B2 第 6 项）**：若 `memory.mode` 非 `off`/`readonly`，写出 `work/memory_proposal.json` 并运行 `python -X utf8 "<SKILL_DIR>/scripts/memory.py" draft-card --proposal work/memory_proposal.json`，将「🧠 下支片想怎么更合你胃口？」3 条偏好提问与候选沉淀卡直接附在最终交付消息末尾（用户回复确认后执行 `memory.py apply work/memory_proposal.json --confirm` 或 `add-pref`）。

### 8. 巡检（`status`）
只读汇总：当前目录项目进度、最近曲线图/QA 状态、`run_queue.py --status`、`memory.py status` 以及 `doctor.py` 环境概况（含 Blender 与 Blender MCP 状态）。

### 9. 工作室自迭代记忆（`memory`）
管理位于 `~/.chiaki-studio/`（可用 `CHIAKI_MEMORY_DIR` 自定义，独立于 Skill 仓库、升级永不丢失）的轻量化长期记忆：
- 查看状态与条目：`python -X utf8 "<SKILL_DIR>/scripts/memory.py" status` / `show`
- 切换自迭代开关：`python -X utf8 "<SKILL_DIR>/scripts/memory.py" mode <ask|auto|readonly|off>`
- 手动增删条目：`add-pref` / `add-mistake` / `forget <P##|M##|F###>` / `reset --yes`（重置前必须经用户明确确认）。
