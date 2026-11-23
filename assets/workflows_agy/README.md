# Antigravity Python Workflows (`run_workflow`)

These three scripts mirror `assets/workflows/*.js` for Antigravity's native `run_workflow` tool, enforcing strict tool-scoped subagent types (`chiaki-writer`, `chiaki-builder`, `chiaki-reviewer`), pinned models (`pro` / `flash`), and verbatim persona injection from `references/personas.md`.

| Script | Stage | Roles |
|---|---|---|
| `pitch.py` | Stage 2 Pitch Meeting | `媒介设计师`, `演出策划`, `摄影指导` → `创意总监` → `执行制片` |
| `build.py` | Stage 4 2D Studio Build | `剪辑合成师` + `平面设计师` → `执行导演` → `修改员` → `质检` |
| `review_fix.py` | Stage 6 Final Adversarial Review | `规矩` / `技术` / `剪辑感` 审片员 → 3 复核员 → `修改员` → `质检` |
