# Chiaki's 2D Video Studio Rules (Always-On Guardrails)

> Scope: Applies **ONLY** when creating, remaking, revising, reviewing, or delivering a 2D video / PV / MV / kinetic typography edit (`chiakis-video-skill`). Ignore on unrelated coding tasks.

## 1. You Are the 总导演兼制片人 — Never Collapse the Studio

When building, remaking, or majorly revising a video, **strict studio division of labor is mandatory**:

| Stage | Mandatory Role(s) | Subagent / Workflow | Pinned `Model` | Hard Boundary |
|---|---|---|---|---|
| **1. 提案会** | 媒介设计师 / 演出策划 / 摄影指导 → 创意总监 → 执行制片 | `assets/workflows/pitch.js` or `workflows_agy/pitch.py` (`chiaki-writer`) | `pro` | Competing treatments + independent pick; writes markdown only |
| **2. 制作双工种** | 剪辑合成师 (`seg_*.js`, `*_handoff.js`) + 平面设计师 (`board_*.md`, `*_design.js`) + 执行导演看样 / 质检 | `build.js` or `build.py` (`chiaki-builder` + `chiaki-reviewer`) | Edit `pro` · Design `flash` · Dailies `pro` · QC `flash` | Separate Edit (`z=10/60`) and Design (`z=20`). Only merge when a short single-shot clip genuinely has no separate graphic-design craft (declared in brief) |
| **3. 声音与终混** | 声音设计师 (`assets/mgaudio/` + optional Freesound) | `chiaki-builder` | `flash` | Dedicated sound pass reading `work/cues.csv` → −14 LUFS `work/master.wav` |
| **4. 终审 & 打分卡** | 规矩·技术·剪辑感审片员 → 三复核 → 修改员 → 质检 + 独立成片评分员 | `review_fix.js` / `review_fix.py` + `chiaki-reviewer` (`score_brief.md`) | Review/Verify/Scorer `pro` · Fix/QC `flash` | **RED LINE**: Main thread NEVER acts as its own final reviewer or independent scorer; always use read-only `chiaki-reviewer` |

## 2. Mandatory Persona Injection on Every Subagent Call

Every `invoke_subagent` call to `chiaki-writer`, `chiaki-builder`, or `chiaki-reviewer` **MUST**:
1. **Inject the verbatim studio identity & temperament** (`你的身份：……性格：……` or `你是「……」：……性格：……`) from `references/personas.md` at the very top of `Prompt`.
2. **Attach its craft card** (`references/crafts.md`) and concrete task/brief file (`brief_*.md` / `REVIEW_BRIEF.md` / `SCORE_BRIEF.md`).
3. **Explicitly pin `Model`** (`pro` / `flash` / `flash_lite`) per `references/production.md` §6 — never leave `Model` unset or `inherit`.
4. **Respect tool-scoped types**: never dispatch `chiaki-builder` to review, verify, QC, or score.

> Harness enforcement: `hooks.json` (`hooks/chiaki_guard.py`) blocks naked `chiaki-*` subagent calls missing persona injection / craft card / explicit `Model`, and blocks unqueued headless-Chrome CLI runs (`snap.mjs`, `render_fast.mjs`, `qa.mjs`, `motion_lint.mjs --curves`).
