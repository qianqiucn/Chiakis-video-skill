# House Style — 2D Video Creative Brief

This file sets the studio's creative standards. It overrides defaults in other reference files when they conflict.

## 0. Hierarchy of Decisions & Imagination First
1. **The client's explicit direction** wins over every house default.
2. **Imagination & visual concept**: every original film starts from one bold, memorable 2D visual form chosen in the pitch (`script-writing.md` §0) — a cohesive visual medium, typographic system, and transition language. Target quality is award-winning commercial motion design (Buck / ManvsMachine / top Bilibili/YouTube editorial & PV level).
3. **Fixed goals** (never break): deterministic frame accuracy, zero render/page errors, legible typography, beat-locked music/SFX sync, `-14 LUFS` clean audio master, local bundled fonts only (no remote web fonts), and independent read-only review before delivery.
4. **Breakable defaults**: any house default below (shot lengths, palette counts, layer counts, transition cadence) may be broken **on purpose** when the chosen visual form calls for it — declare the departure and its reason in the storyboard / `REVIEW_BRIEF.md` so reviewers judge intent rather than flagging deliberate style choices as mistakes.

## 1. Format, Energy & Music
- **Resolution & FPS**: author on a `1920x1080` logical stage at native **24 fps** (cinematic / hype / editorial) or **30 fps** (lyric PV / UI / crisp web MG); review at 720p first when iterating fast, and deliver 1080p web MP4 plus optional **2K (`2560x1440`)** master with lossless 48 kHz FLAC audio (pass `--grain` to `render_fast.mjs` when tactile grain/paper overlays are prominent).
- **Music & vocal timing first**: cut percussion hits to measured beat grids (`scripts/beats.py`) and broadband onsets (`scripts/onsets.py` — `floor(onset_frame)`). For **sung lyrics / vocal PVs**, NEVER rely on drum trackers alone: run `scripts/vocal_spec.py` before Gate A and lock lyric entries by direct multimodal listening (`read_file` on micro-WAVs) + 300 Hz–4 kHz vocal spectrograms.
- **Sound strategy (`pure_song` vs `full_sfx` — declare explicitly in brief)**:
  - **Song PVs / Lyric MVs (default: `pure_song` clean master)**: preserve the finished vocal/musical recording cleanly mastered to **−14 LUFS integrated, true peak ≤ −1.1 dBTP, 48 kHz stereo** with **zero added whooshes/risers/glitches** unless the client explicitly asks for SFX accents — artificial swooshes fight vocal clarity and studio mastering.
  - **Promos / Openers / Trailers / Original Procedural Scores (default: `full_sfx` via `assets/mgaudio/` + optional `scripts/freesound.py`)**: real-world physical actions use recorded SFX where available; procedural `mgaudio.sfx` handles swooshes, risers, hits, UI clicks, glitches, paper, and tonal accents. Keep mixes uncrowded (≤ 3 concurrent SFX per frame), duck music ~3 dB on hero hits, keep stereo mono-compatible (`stereo_corr > 0.3`), and master to **−14 LUFS / ≤ −1.1 dBTP**.

## 2. Story, Clarity & Focal Hierarchy
- **One clear focal point per beat**: every shot has one primary read (hero title, lyric phrase, key illustration, or visual metaphor). Secondary typography, HUD accents, and graphic overlays support the hero rather than fighting it.
- **One hero title moment per act**: commit to a memorable, well-crafted typographic build (`graphic-design.md` §1–§2) rather than repeating five generic slide titles.
- **Safe margins & mobile readability**: verify hero text reads cleanly at phone size (720p contact sheet); keep critical copy inside a safe 5–8 % inner margin.

## 3. Typography & Bundled Local Fonts
- **Zero remote fonts**: never load Google Fonts `<link>` or remote URLs in `index.html`; offline headless rendering and portability break. Always pack local commercial-safe fonts (OFL-1.1 / Apache-2.0) from `assets/fonts/` via `scripts/fonts.py use`.
- **Match typeface to mood**: pair at most 2–3 disciplined families per film (1 expressive display/serif/calligraphy voice + 1 crisp sans/CJK body + 1 tabular monospace for technical details).
- **Per-glyph kinetic typography**: in fast-cut vocal/lyric PVs, avoid sliding whole multi-character sentences as rigid bricks; animate per-glyph staggered arrivals, baseline waves, optical blurs, or expressive size hierarchies (`graphic-design.md` §5).

## 4. 2D Motion Blur, Layering & Visual Depth
- **Motion blur belongs on fast motion only**: use `T3.blur.shutter` (180° 5-tap or 360° 10-tap opaque) on whip pans, fast camera slides, and rapid throws; keep held frames and landing subjects crisp.
- **Five-layer 2D depth (`graphic-design.md` §5)**: build depth from (1) moving/parallax base, (2) translucent graphic/texture materials (`assets/textures/` grain, dust, paper, washi), (3) hero subject or kinetic typography, (4) sparse high-contrast accent marks (`lib/accents.js`), and (5) unified atmosphere/vignette/grade.
- **2D character/illustration plates**: animate separated PNG layers gently with `T3.her.wave` + `T3.her.warp2` (`lib/meshwarp.js`), `T3.her.eyes`, `T3.multiplane`, or `T3.depth3d`; never inflate camera moves to disguise a dead static frame.

## 5. Curves & Determinism
- Every segment `render(t)` must be **100 % pure in `t`** (zero `Math.random()`, `Date.now()`, `performance.now()`, or accumulated frame-to-frame mutable state). Seeking backward or to any arbitrary frame must produce identical pixels.
- Use `lib/motion` (`T3.EZ`, `T3.mv`, `T3.blur`, `T3.twos`, `T3.her`) and register `T3.motionProbe` curves checked via `scripts/motion_lint.mjs --curves` (`motion-library.md`).

## 6. Restraint Budget (Avoid Visual Noise)
- **No dead freezes**: landed elements carry subtle `move.settle` (1–3 px/s drift or 0.5 % scale creep) or ambient air (`move.drift`), unless a deliberate `Posterize Time` stepped cadence is declared (`style-grammar.md` §6e).
- **Budget impacts and shakes**: reserve full-frame flashes, impact frames (`T3.impact`), and heavy shakes (`T3.shake`) for true musical accents (typically 1–3 hero hits per 15 s act), never every cut.
- **One sheen per shot**: avoid stacking competing lens flares, heavy glows, and neon strokes on top of each other.

## 7. Studio Division of Labor (Section 10 Mirror)
## 10. Studio Roles & Sign-off
- **总导演兼制片人 (Main Thread)**: owns creative direction, storyboard, schedule, integration (`index.html`), and final sign-off. Never acts as its own final reviewer or independent scorer.
- **提案会团队 (`chiaki-writer`)**: three competing creative treatments (`媒介设计师`, `演出策划`, `摄影指导`) → `创意总监` picks → `执行制片` checks act-to-act variety.
- **制作工种 (`chiaki-builder`)**: separate **剪辑合成师** (`segments/seg_*.js`, `*_handoff.js` at `z = 10 / 60`), **平面设计师** (`design/board.md`, fonts, `segments/*_design.js` at `z = 20`), and **声音设计师** (`work/make_audio.py`, `work/master.wav`).
- **独立审片与评分团 (`chiaki-reviewer`, physically read-only)**: `执行导演` (first-cut dailies), 3-lens final review (`规矩`, `技术`, `剪辑感`) + 3 independent verifiers, `质检` (recheck after fixes), and `独立成片评分员` (7-dimension scorecard).
