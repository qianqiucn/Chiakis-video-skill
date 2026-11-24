# Review Brief Template (`REVIEW_BRIEF.md`)

Fill in and place at `<project>/work/REVIEW_BRIEF.md` before running `review_fix.js` or `review_fix.py`.

- **Project**: `<name>` (`<project path>`)
- **Mode**: `<Original 2D PV / MV Remake / Kinetic Promo / Study Replica>`
- **Timeline**: `<start_s>s – <end_s>s` at `<24 | 30> fps`
- **Master / Preview files**:
  - Draft / Master MP4 (**required for Gemini native multimodal video watching via `read_file`**; for long films also list 10–25 s per-act 720p `.mp4` clips): `<path>`
  - Vocal micro-WAVs / spectrograms (`work/vocal/`): `<path or N/A>`
  - QA Report: `<project>/web/qa/qa_report.txt`
  - Curve Sheets: `<project>/work/motion_*/curves.svg` + `lint.txt`
  - Audio Report: `<project>/work/audio_report.txt` (`work/master.wav`)
- **Host-Split Review Iron Rule (`rules/AGENTS.md` §3)**:
  - **Gemini hosts**: MUST watch the rendered `.mp4` directly via multimodal `read_file` (use stills only for pixel inspection); NEVER judge motion/pacing/sync from stills alone.
  - **Claude / Codex hosts**: inspect contact sheets (`snap.mjs`) + transition frames + `curves.svg` + `vocal_spec.py` PNG spectrograms + QA metrics.
- **Declared intentional departures from defaults (`house-style.md` §0)**:
  - `<e.g. Act B uses deliberate 12 fps Posterize Time (T3.twos n=2.5) for darkroom contact-sheet vibe — do not flag as stutter>`
  - `<e.g. None>`
- **Key timestamps / beat drops to inspect**:
  - `<f0 / t0s — Hook>`
  - `<f1 / t1s — Hero title / Chorus drop>`
  - `<f2 / t2s — Act hand-off>`
  - `<f3 / t3s — End card / button>`
