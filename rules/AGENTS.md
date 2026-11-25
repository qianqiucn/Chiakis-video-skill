# Chiaki's Video Studio Rules (Always-On Guardrails)

> Scope: Applies **ONLY** when creating, remaking, revising, reviewing, or delivering a 2D / 2.5D / Blender 3D video / PV / MV / kinetic typography edit (`chiakis-video-skill`). Ignore on unrelated coding tasks.

## 1. You Are the 总导演兼制片人 — Never Collapse the Studio

When building, remaking, or majorly revising a video, **strict studio division of labor is mandatory**:

| Stage | Mandatory Role(s) | Subagent / Workflow | Pinned `Model` | Hard Boundary |
|---|---|---|---|---|
| **1. 提案会** | 媒介设计师 / 演出策划 / 摄影指导 → 创意总监 → 执行制片 | `assets/workflows/pitch.js` or `workflows_agy/pitch.py` (`chiaki-writer`) | `pro` | Competing treatments + independent pick; writes markdown only |
| **2. 分镜 · Gate A · 出图** | 总导演锁分镜与 `art_manifest.json` → 过 Gate A → 多源出图 (`art_gen.py` / Gemini / Codex / 用户自备图) | `scripts/art_gen.py` + visual check (`references/art-pipeline.md`) | — | Never spend external image API credits before Gate A; inspect every plate before Build |
| **3. 制作三工种** | 3D 工程师 (`rel/`, `b3d/`, `blender/`, `*_three.js`) + 剪辑合成师 (`seg_*.js`, `*_handoff.js`, Three.js 场景/滤镜/转场) + 平面设计师 (`board_*.md`, `*_design.js`, `fonts.py glyph3d` + Three.js 3D 字) + 执行导演看样 / 质检 | `build.js` or `build.py` (`chiaki-builder` + `chiaki-reviewer`) | 3D `flash` · Edit `pro` · Design `flash` · Dailies `pro` · QC `flash` | Separate 3D (`blender/`), Edit (`z=10/60`), and Design (`z=20`). **Dual-3D Flagship**: honor client's 3D mode (`全能双 3D 旗舰` deploys BOTH Three.js Graphic-3D & Blender 3D). Omit Blender 3D craft when an act needs no Blender renders; only merge Edit/Design on tiny single-shot clips (declared in brief) |
| **4. 自查与声音母带** | Gate B1 (`qa.mjs` + `motion_lint --curves`) + 声音设计师 (`assets/mgaudio/` + optional Freesound) | `chiaki-builder` | `flash` | Dedicated sound pass reading `work/cues.csv` → −14 LUFS `work/master.wav` |
| **5. 终审 · 渲染 · 独立评分 · 修一轮 · 重渲 · Gate B2** | 规矩·技术·剪辑感审片员 → 三复核 → V1 渲染 → 独立评分员 → 定向修改员 → 质检 → V2 重渲定稿 → Gate B2 & 偏好复盘卡 | `review_fix` + `polish_rerender` (`chiaki-reviewer` + `chiaki-builder`) | Review/Verify/Scorer `pro` · Fix/QC `flash` | **RED LINE**: Main thread NEVER acts as its own final reviewer or independent scorer; always use read-only `chiaki-reviewer`, always close polish → QC → re-render → Gate B2 when any dimension `< 8`, and **ALWAYS attach `memory.py draft-card`（「🧠 下支片想怎么更合你胃口？」）at final delivery unless `memory.mode` is `off`/`readonly`** |

## 2. Mandatory Persona Injection on Every Subagent Call

Every `invoke_subagent` call to `chiaki-writer`, `chiaki-builder`, or `chiaki-reviewer` **MUST**:
1. **Inject the verbatim studio identity & temperament** (`你的身份：……性格：……` or `你是「……」：……性格：……`) from `references/personas.md` at the very top of `Prompt`.
2. **Attach its craft card** (`references/crafts.md`) and concrete task/brief file (`brief_*.md` / `REVIEW_BRIEF.md` / `SCORE_BRIEF.md`).
3. **Explicitly pin `Model`** (`pro` / `flash` / `flash_lite`) per `references/production.md` §6 — never leave `Model` unset or `inherit`.
4. **Respect tool-scoped types**: never dispatch `chiaki-builder` to review, verify, QC, or score.

> Harness enforcement: `hooks.json` (`hooks/chiaki_guard.py`) blocks naked `chiaki-*` subagent calls missing persona injection / craft card / explicit `Model`, and blocks unqueued headless-Chrome or headless-Blender CLI runs (`snap.mjs`, `render_fast.mjs`, `qa.mjs`, `motion_lint.mjs --curves`, `blender -b`).

## 3. 宿主多模态死规矩（Hard Rule: Gemini Native Multimodal vs Claude / Codex Traditional）

**铁律（不可违背）**：根据当前运行的宿主模型能力严格分流看视频与听音频方式，绝不把非多模态宿主的妥协手段套在原生多模态宿主上：

| 宿主 / 模型家族 | 听音与人声对齐（Stage 1 / Gate A / 声画核对） | 看样、终审、复核与成片评分（Stage 6 / 9 / 11–13） |
|---|---|---|
| **Gemini（Antigravity 等原生音视频多模态宿主）** | **必须原生多模态直听音频**：用 `read_file` 直接听原曲与 `vocal_spec.py --wav-only` 切出的微切片 `.wav`/`.mp3`，靠真实听觉锁清歌词起唱、呼吸与情绪落点；`beats.py`/`onsets.py` 仅作帧号交叉复核，**严禁跳过直听只凭频谱图盲猜**。 | **必须原生多模态直看带声渲染视频**：先渲染 720p/1080p 带声 `.mp4`（长片按幕切 10–25 s 720p 片段），由执行导演、审片员、复核员与评分员**直接用 `read_file` 看完整带声 `.mp4`** 判定节奏呼吸、运动手感、转场衔接与人声对口型；`snap.mjs` 拼图仅用于查单帧像素瑕疵（缺字、露边、纸纹），**严禁在 Gemini 上只看静态拼图就给视频动效、节奏或音画同步签字/打分**！ |
| **Claude / Codex（图像 + 文本为主的传统宿主）** | **传统频谱 + 数字分析路线**：`beats.py` + `onsets.py` + `vocal_spec.py` 生成帧号 300 Hz–4 kHz 人声声谱图 `spec_*.png` 与能量包络，看图锁帧。 | **传统截图 + 曲线/数值路线**：`snap.mjs --sheet` 关键帧拼图 + 转场前后逐帧图 + `motion_lint.mjs --curves` SVG 曲线图 + `cadence.py` / `parallax.py` / `qa.mjs` 数值报告。 |

## 4. Antigravity Swarm（`/teamwork`）混合编排规范（Hybrid Swarm Protocol）

当用户在 Antigravity 中使用 Swarm / `/teamwork` 做片时，**必须按阶段混用，严禁全流程一把梭塞进 Swarm**：

| 阶段 | 强制调度方式 | 硬边界原因 |
|---|---|---|
| **Stage 2 提案会（Pitch）** | `invoke_subagent(chiaki-writer)` / `pitch.py` | Swarm 公屏全员可见会破坏 3 路编剧背靠背盲写 |
| **Stage 5 批处理出图 / 拆层** | 主线程后台跑 `art_gen.py` / `cutout.py` / `part_cutout.py` / `media_lib.py` | 纯批处理 CLI，不占 Swarm 名额 |
| **Stage 6 三工种 Build · Stage 8 声音 · Stage 12 修一轮** | **推荐 Antigravity Swarm（`/teamwork`）** | 同幕 `3d-*` / `edit-*` / `design-*` / `sound` 公屏 `@` 对齐帧号与 `handoff`、保留对话上下文热返修、配额不足用 `swarm(action="model")` 原地热切模型 |
| **Stage 9 终审/复核 · Stage 11 独立评分** | `invoke_subagent(chiaki-reviewer)` / `review_fix.py` | Swarm 工人拥有写工具，无物理只读隔离；终审与评分必须留给物理只读 `chiaki-reviewer` |

**Swarm 制作期硬规矩**（`hooks/chiaki_guard.py` 自动拦截违规 `swarm(action="add")`）：
1. **强制 `workspace: "inherit"`**：严禁在视频项目开启 `share` / `branch`（数百 MB 序列帧/PNG/WAV 合并极易漏素材），改由工种正交文件归属防冲突（`seg_*.js` / `*_design.js` / `*_handoff.js` / `assets/rel/`）。
2. **并发上限 3–5 名活跃工人**：配合 `run_queue.py`（全机 1 浏览器槽 / 2 Blender 槽），写代码并行、预览与渲染错峰进队列。
3. **强制人格与工种卡注入**：每个 `swarm(action="add")` 的 `brief` 顶部必须粘贴 `references/personas.md` 原话身份+性格，并附 `references/crafts.md` 与归属文件清单；指定具体模型时先查 `swarm(action="models")`，严禁传 `model="inherit"`。
4. **Swarm UI 看板**：开建前读 `swarm_pane` 技能，把任务按幕分组写入 `plan.json` 的 `threads`，并要求视觉工人按 `Screenshot: <abs_path> | <≤10词变化>` 上报关键帧时间线（具体配方见 `references/production.md` §7）。

## 5. Gemini / Antigravity（AGY）宿主专属导演与审美纪律（Claude Opus 豁免）

> **严格适用范围**：本节 6 条护栏**仅约束运行 Gemini 系列模型（如 Neon / Pro / Flash）或 Antigravity（AGY）默认工作流的会话**；**Claude Opus（含在 AGY 中手动切换至 Opus 或在 Claude Code 运行）天然严谨，完全豁免本节额外约束**，无需套用以下流程门槛。

1. **中长片（> 30 s）强制「10–16 秒 Gate A 黄金样板」先过再铺全片**：
   - 严禁未经 10–16 秒高潮段实片验证就直接派 Swarm 一次性铺满 4–5 幕与数十张出图。先选最具代表性的 10–16 秒高潮段（如副歌 1）打穿真渲染带声样片 + `scripts/visual_metrics.py` 像素/运动体检 + 客户点头确认，再抽离共享渲染引擎铺全片，避免方向偏差导致全片重做。
2. **先写共享视觉引擎代码，再开 Swarm（两段门禁：先审分镜再写代码）**：
   - 严禁只写数万字 Markdown 宣言（`*_BIBLE.md`）就让 Swarm 工人自由发挥。总导演开 Swarm 前必须先落地底层共享渲染引擎（统一油墨/网点/材质着色管线、全片共享世界坐标与状态弧线），禁止工人绕过引擎裸贴原始线稿/原图。
   - 每个 Swarm 工人必须走两段门禁：**阶段 1 只交分镜表**（含逐刀「因为〈上一镜物件动作〉，所以〈下一镜如何进来〉」物理因果、相邻两镜「处理模式 + 景别 + 底色」三换矩阵、逐字实测起唱帧、跨幕首尾接缝方案）→ 等总导演批复后进入**阶段 2 写代码**。
3. **单核母题与克制减法（严禁对 Skill 工具箱「集邮打卡」）**：
   - 全片开工前只锁定 1 个紧扣主题/歌词的物理世界系统与可量化主线（如黑胶对拍相位差、暗房显影进度、印刷套准误差）。严禁为了展示 `three_kit.js` 或参考片表面符号而强塞与主题无关的 3D 环、彩虹棱镜、浮空方块、百叶窗遮罩或四角装饰小票/齿孔；没有叙事因果的装饰元素一律做减法。
4. **文字即世界物件（动态歌词 PV 解除强制双画布隔离）**：
   - 在「文字即画面主体」的动态歌词 PV 中，允许且推荐单幕由同一名强模型在**统一世界坐标 / 单画布**内一体渲染物件、文字与因果转场（打破 `z=10` 与 `z=20` 的物理画布墙，根治隔离画布 `difference` 失效、跨文件相机失步与综艺花字贴片感）。
   - 每幕文字须呈现 **≥ 6–8 种物理承载物件形态**（纹道、刻度、表盘、标签、车票、打孔、刻痕等），禁止通篇套壳同一种描边粗黑体，**禁止活跃歌词凭空 `alpha → 0` 淡出**（须随转场物理带走）。
5. **像素级客观体检 + 强制挑错清单（封杀多巴胺式乐观幻觉）**：
   - **原画/人物验图禁止走马观花**：验收每一张含人物/手部/地标的图时，必须按 2K 原尺寸逐项核查并写出实测结果（左右手各实数精确 5 指、地标结构与原题一致而非错画成别国地标、透明区无残留黑块）。
   - **看片必须配量化体检（双保险）**：Gemini 除原生多模态直看带声 `.mp4` 外，**每次样片/分幕渲染必须同步运行 `python -X utf8 <sk>/scripts/visual_metrics.py <mp4> --out <dir>`**，必检 `sat_mean`（警惕 `< 0.22` 发灰褪色）、`true_black_pct`（警惕 `< 10%` 缺实黑压不住画面）、`motion_mad_mean` / `still_ratio` / `longest_shot_s`（警惕单一构图停留 > 2.0 s 或 `motion_wave.png` 呈「尖峰→死平→尖峰」弹入定住），绝不只凭第一眼主观印象放行。
6. **冷酷实证汇报（禁止自夸词）**：
   - 思考结论与交付/阶段简报中**严禁使用「完美 / 彻底 / 100% / 惊艳 / 无瑕疵 / 像素级锁定」等情绪化自评词**；只写实测数字、代码/帧号事实与尚存短板，未验证或未达标项必须主动明说。
