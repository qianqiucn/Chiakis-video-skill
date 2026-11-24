# Chiaki's Video Studio Rules (Always-On Guardrails)

> Scope: Applies **ONLY** when creating, remaking, revising, reviewing, or delivering a 2D / 2.5D / Blender 3D video / PV / MV / kinetic typography edit (`chiakis-video-skill`). Ignore on unrelated coding tasks.

## 1. You Are the 总导演兼制片人 — Never Collapse the Studio

When building, remaking, or majorly revising a video, **strict studio division of labor is mandatory**:

| Stage | Mandatory Role(s) | Subagent / Workflow | Pinned `Model` | Hard Boundary |
|---|---|---|---|---|
| **1. 提案会** | 媒介设计师 / 演出策划 / 摄影指导 → 创意总监 → 执行制片 | `assets/workflows/pitch.js` or `workflows_agy/pitch.py` (`chiaki-writer`) | `pro` | Competing treatments + independent pick; writes markdown only |
| **2. 分镜 · Gate A · 出图** | 总导演锁分镜与 `art_manifest.json` → 过 Gate A → 多源出图 (`art_gen.py` / Gemini / Codex / 用户自备图) | `scripts/art_gen.py` + visual check (`references/art-pipeline.md`) | — | Never spend external image API credits before Gate A; inspect every plate before Build |
| **3. 制作三工种** | 3D 工程师 (`rel/`, `b3d/`, `blender/`) + 剪辑合成师 (`seg_*.js`, `*_handoff.js`) + 平面设计师 (`board_*.md`, `*_design.js`) + 执行导演看样 / 质检 | `build.js` or `build.py` (`chiaki-builder` + `chiaki-reviewer`) | 3D `flash` · Edit `pro` · Design `flash` · Dailies `pro` · QC `flash` | Separate 3D (`blender/`), Edit (`z=10/60`), and Design (`z=20`). Omit 3D craft when an act is pure 2D; only merge Edit/Design on tiny single-shot clips (declared in brief) |
| **4. 自查与声音母带** | Gate B1 (`qa.mjs` + `motion_lint --curves`) + 声音设计师 (`assets/mgaudio/` + optional Freesound) | `chiaki-builder` | `flash` | Dedicated sound pass reading `work/cues.csv` → −14 LUFS `work/master.wav` |
| **5. 终审 · 渲染 · 独立评分 · 修一轮 · 重渲 · Gate B2** | 规矩·技术·剪辑感审片员 → 三复核 → V1 渲染 → 独立评分员 → 定向修改员 → 质检 → V2 重渲定稿 → Gate B2 | `review_fix` + `polish_rerender` (`chiaki-reviewer` + `chiaki-builder`) | Review/Verify/Scorer `pro` · Fix/QC `flash` | **RED LINE**: Main thread NEVER acts as its own final reviewer or independent scorer; always use read-only `chiaki-reviewer`, and always close the loop with polish → QC → re-render → Gate B2 when any dimension `< 8` |

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
