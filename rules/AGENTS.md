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
