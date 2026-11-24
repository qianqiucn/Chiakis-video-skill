# Flagship Quality Benchmark — Quantitative Telemetry Reference (`benchmark-quality.md`)

> **Content-free engineering baseline**: every number below was measured directly from a finished 71 s (`30 fps`, 5-act, 2K FLAC) flagship kinetic PV render, its runtime curve export (`curves.json`), its audio master, and its segment choreography — stripped of all subject matter, branding, and lyrics. Use these bands as an **objective quality yardstick** during Stage 6 Build, Gate B1 Self-Check, Stage 9 Review, and Stage 11 Independent 7-Dimension Scoring (`score_brief.md`).

---

## 1. How to Scale This Benchmark by Genre

The flagship reference below represents a **high-energy, fast-cut commercial kinetic PV** (`30 fps`, ~77 cuts/min). Adapt the **pacing & cut-rate** targets to your declared genre while keeping **curve cleanliness, living-frame continuity, contrast, detail density, and mastering precision** strictly at flagship level:

| Genre / Form | Cut Rate Target | Median Shot Length | Curve Cleanliness & Living Frames |
|---|---|---|---|
| **Fast-Cut Kinetic PV / Lyric MV / Hype Promo** (baseline) | `55–90 cuts/min` | `0.35–0.70 s` | **100% identical to baseline below** |
| **Editorial / Product / Brand Opener** | `25–50 cuts/min` | `0.90–2.00 s` | Same curve cleanliness (`0 FAIL / 0 NOTE`), `≥ 92%` living frames |
| **Literary / Atmospheric / Lyrical MAD** | `15–35 cuts/min` | `1.50–3.50 s` | Softer `Q1 ∈ [0.60, 0.78]`, smooth breathing settle, zero dead freezes |

---

## 2. Motion Curve Telemetry (`scripts/motion_lint.mjs --curves`)

An award-grade motion film looks effortless because **zero** curve defects leak into the timeline.

| Metric | Flagship Measured Value | Recommended Target Band | Red Flag (Fix Before Sign-Off) |
|---|---|---|---|
| **Static Lint (`motion_lint.mjs`)** | `0 FAIL / 0 NOTE` (5/5 strict segments) | `0 FAIL`, `0` hand-rolled eases / linear hacks | Any hand-rolled ease, frame table, or `FAIL` |
| **Runtime Curve Defects (`curves.json`)** | `0` dead stops · `0` velocity corners · `0` constant-velocity runs · `0` R3 NOTEs | **`0` dead stops, `0` corners, `0` plateaus** | Any dead stop or unmotivated velocity corner |
| **Probe Coverage Density** | `22–24` probes across 5 acts (`4–6 / act`, `~3.4 / 10 s`) | `≥ 3 / segment` (flagship: `4–6 / act`) | `< 3` probes or probes detached from real `render()` |
| **Arrival `Q1` (First-Quarter Travel Share)** | `min 0.602` · `p25 0.629` · **`p50 0.650`** · `p75 0.795` · `max 0.881` | **`[0.60, 0.88]`** (median `0.64–0.75`) | `< 0.60` (sluggish/symmetric) or `> 0.90` over `≥ 16 f` (cliff + dead tail) |
| **Arrival Duration** | `min 10.3 f` · `p25 12.5 f` · **`p50 18.8 f`** · `p75 23.5 f` (@ 30 fps) | `10–26 f` @ 30 fps (`8–20 f` @ 24 fps) | `< 8 f` teleport snaps (except declared 1–2 f impact hits) |
| **Arrival Peak Position (`peakPos`)** | `p25 = 0.00` · `p50 = 0.00` · `p75 = 0.00` | `≤ 0.15` (front-loaded energy) | `0.30–0.70` (mushy PowerPoint ease-in-out on entrances) |
| **Exit End Velocity (`endV`)** | `min 1.00` · `p50 = 1.00` · `max 1.00` | **`≥ 0.85`** (accelerates cleanly into cut) | `< 0.70` (slowing down awkwardly before leaving frame) |

---

## 3. Editing Rhythm & 5-Act Energy Arc (`scripts/framediff.py`)

Flagship films never run at flat uniform speed. They sculpt an unmistakable **macro bell curve of intensity** with high shot-length contrast:

### 3a. Shot-Length Contrast (Fast-Cut PV Baseline)
- **Measured cuts (`MAD > 24`, min 6 f spacing)**: `91` cuts in `71.0 s` (**`76.9 cuts/min`**).
- **Distribution**: `min 0.20 s` (6 f micro-accent) · `p25 0.32 s` · **`median 0.47 s`** · `mean 0.77 s` · `p90 1.33 s` · `max 7.73 s` (intentional opening/outro structural anchor).
- **Contrast Rule**: maintain **≥ 6× dynamic ratio** between fast micro-cuts (`0.20–0.35 s`) and breathing hero holds (`1.3–4.0+ s`). Uniform `1.5 s` cuts read like an automated slideshow.

### 3b. Five-Quintile Macro Pacing & Visual Arc (Measured Baseline)

| Timeline Quintile | Role in Film Structure | Cuts / 10 s | Mean Luma | Luma Contrast (`std`) | Mean Saturation | Frame Motion (`MAD p50`) | Static Frames (`%`) |
|---|---|---:|---:|---:|---:|---:|---:|
| **Q1 (`0–20%`)** | **Hook & World Anchor** — crisp bright establish + signature hero card | `8.5` | `177.0` | `52.8` | `71.4` | `3.81` | `1.2%` |
| **Q2 (`20–40%`)** | **Verse Acceleration** — `2.2×` cut density + darker contrast tension | `18.3` | `123.1` | `58.8` | `76.2` | `8.67` | `3.8%` |
| **Q3 (`40–60%`)** | **Pre-Drop Vacuum → Chorus Climax** — peak cuts (`2.8×`), peak chroma, **0% static** | **`23.9`** | `125.7` | `58.5` | **`86.9`** | **`10.92`** | **`0.0%`** |
| **Q4 (`60–80%`)** | **Chorus Exhale & Bridge** — rhythmic release + brightness lift | `9.2` | `165.5` | `49.6` | `70.6` | `2.77` | `2.6%` |
| **Q5 (`80–100%`)** | **Locked-Container Outro & End Slate** — symmetry, calm chroma, clean resolve | `4.2` | `178.5` | `45.9` | `51.6` | `1.75` | `17.2%` *(fade-out)* |

> **Key Structural Pattern — The Pre-Drop Vacuum**: right before the Q3 peak explosion, drop visual density by ~80% for `0.6–1.2 s` (clean dark grid + single floating focal specimen + minimal level meter), so the very next frame's full-colour chorus eruption feels twice as big without louder effects.

---

## 4. Living-Frame Continuity & Optical Flow (`scripts/motion.py`, `scripts/cadence.py`)

| Metric | Flagship Measured Value | Target Standard | Diagnostic Meaning |
|---|---|---|---|
| **Living-Motion Frame Ratio** (`MAD ≥ 0.35`) | **`95.07%`** (`100%` in climax Q3) | **`≥ 92%`** (excl. final fade & declared stepped beats) | Every landed shot breathes (`move.settle` / subtle parallax / meter / border drift) |
| **High-Energy Action Ratio** (`MAD ≥ 8.0`) | **`35.79%`** | `20%–45%` (fast-cut) / `10%–25%` (editorial) | Balances kinetic hits (~1/3) with legible breathing holds (~2/3) |
| **Optical Flow Stratification** (720p `px/f`) | `p25 0.63` · **`p50 1.42`** · `p75 7.0` · `p90 20.6` · `p95 peak 53–370` | Clear 3-tier velocity ladder: settle (`0.5–2 px/f`), active (`5–15 px/f`), whip (`25+ px/f` + `T3.blur.shutter`) | Flat `0 px/f` = dead slides; constant `> 15 px/f` = exhausting visual soup |
| **Extreme Flash / Pure Black Restraint** | `72 / 2130` frames (**`3.4%`**, incl. fade-out) | **`≤ 4–5%`** of total frames | Reserves full-white flashes & blackouts strictly for musical peaks |

---

## 5. Visual Richness, Contrast & Colour Discipline (`scripts/look.py`)

| Metric | Flagship Measured Value | Target Band | Why It Separates Pro From Amateur |
|---|---|---|---|
| **Luminance Contrast (`luma_std`)** | `p25 42.4` · **`p50 56.8`** · `p75 64.0` · `mean 53.1` | **`42–68`** (median `≥ 50`) | Crisp figure-ground separation; `< 30` reads washed-out/muddy |
| **Graphic / Edge Detail Density** (Canny `%`) | `p25 10.7%` · **`p50 13.3%`** · `p75 16.0%` · `mean 12.8%` | **`9%–17%`** (sweet spot `11%–15%`) | `< 5%` = bare slides lacking 5-layer depth; `> 22%` = unreadable clutter |
| **Palette Discipline & Chroma** (`HSV S`) | `p25 46.7` · **`p50 65.0`** · `p90 115.5` · `max 204.7` | **3-token base palette** (1 clean ground + 1 ink + 1 signature accent) + **1 deliberate climax hue flip** | Cohesive art direction across 85% of runtime, with one unforgettable complementary inversion at peak climax |
| **Readable Luminance Range** (`luma_mean`) | `p10 78.6` · `p50 161.3` · `p90 207.1` | Distinct act-level light/dark polarity (`≥ 45` luma swing between light anchor acts and dark tension acts) | Prevents monotone lighting across a multi-act film |

---

## 6. Layering, Typography & Choreography Engineering Ratios

Quantitative anatomy of what a flagship codebase actually contains (pure structural ratios, independent of content):

1. **Five-Layer Collage / Staging Depth (every hero shot)**:
   - **L1 Living Substrate**: engineered coordinate grid, halftone dots, diagonal tape, perspective floor, or slow ghost micro-type (never flat untextured solid fill).
   - **L2 Graphic Container Chrome**: film sprockets, cropped frame windows, stamp borders, ribbon marquees, live waveform/VU meters, circular seals, or split panels.
   - **L3 Alpha-Cutout Hero Subject**: flagship ratio measured **`71%` alpha-transparent cutouts (`15` RGBA cutouts vs `6` full-bleed plates)** — cutouts unlock true Z-layering, text-behind-subject occlusion, and dynamic collage silhouettes without rectangular sticker boxes.
   - **L4 Per-Glyph Kinetic Typography**: **`~1.5` per-glyph draw passes/sec** (`108` across 71 s) — mixed scale hierarchy (large primary glyphs vs compact secondary particles), hollow-stroke preview flashes, diagonal contrast bars, arc/stepped layouts, and climax 3D Z-scatter.
   - **L5 Tactile Coat & Corner Telemetry**: paper/35mm grain (`z = 45` unified coat), soft vignette, corner registration crosshairs, and subtle timecode/frame ticks.
2. **Modular Kit + Per-Beat Choreography Density**:
   - **Shared Visual-Kit Module** (`~1,000–1,400` lines of reusable primitives: borders, grids, meters, kinetic type helpers, transition wipes) keeps visual grammar 100% unified across acts while preventing copy-paste bloat.
   - **Per-Act Bespoke Choreography**: measured **`~196 lines/sec` total (`2,200–2,970` lines per ~14 s act)**, **`2.6` `ctx.save()` state scopes/sec**, **`0.62` `.clip()` geometric mask passes/sec**, **`249` `T3.EZ` + `153` `T3.mv` calls** — proving flagship motion graphics cannot be faked by a 150-line generic slideshow loop.
3. **Typography System**:
   - **3–4 disciplined functional voices** (heavy condensed display + editorial serif + clean CJK/body sans + tabular mono/pixel for edge telemetry), locally subsetted into offline WOFF2 (`~1.0–1.8 MB` total payload, `0` remote font URLs).

---

## 7. Audio Mastering & Delivery Spec Benchmarks

| Spec | Flagship Measured Value | Delivery Gate (`quality-bar.md` Gate B2) |
|---|---|---|
| **Integrated Loudness** | **`−14.0 LUFS`** | `−14.0 ± 1.0 LUFS` |
| **True Peak** | **`−1.8 dBTP`** | `≤ −1.1 dBTP` |
| **Stereo Phase Correlation** | **`+0.752`** | `> +0.30` (mono-safe) |
| **Crest Factor (Dynamic Punch)** | **`14.68 dB`** | `10–16 dB` (punchy, zero brickwall clipping) |
| **Archival Master (`--2k`)** | `2560×1440` `yuv420p` `bt709` `tv` progressive · `14.6 Mb/s` H.264 + `48 kHz / 24-bit FLAC` (`1.69 Mb/s`) | Native 2K BT.709 + lossless 48 kHz FLAC |
| **Review / Mobile Preview (720p)** | `1280×720` `bt709` `tv` · `~2–6 Mb/s` H.264 + `197 kb/s` 48 kHz AAC | Fast `< 25 MB` review clip (add `--grain` if heavy paper/35mm grain) |

---

## 8. Fast Diagnostic Mapping (Using This Benchmark in Review & Scoring)

When a reviewer or independent scorer (`score_brief.md`) evaluates a film, compare its measured telemetry against this baseline:

| Observed Telemetry Gap | Root Quality Deficit | Direct Craft Upgrade |
|---|---|---|
| `edge_density < 6%` or `luma_std < 35` | Flat single-layer slides; missing graphic chrome / contrast | Add L1 living substrate + L2 frame/grid chrome + L5 `z=45` tactile paper/grain (`prep_texture.py`) |
| `living_motion < 85%` or `flow_p50 < 0.3 px/f` | Dead static freezes between cuts | Add continuous `move.settle` / breathing scale / subtle L1 grid or meter motion on every held shot |
| Flat cut density across Q1–Q5 (no peak in Q3) | Monotone rhythm; no tension/release arc | Compress Q3 climax shot lengths (`0.25–0.50 s`), add a `0.8 s` pre-drop vacuum, and calm Q5 outro |
| `arrive Q1 < 0.60` or `> 0.90` (on `≥ 16 f`) | Sluggish symmetric ramps OR cliff-snap with dead tail | Re-curve with `T3.EZ.snap` / `T3.EZ.out3` / AE Soft Bezier (`style-grammar.md` §6b) so `Q1 ∈ [0.62, 0.85]` |
| `alpha cutouts < 30%` (all rectangular plates) | Boxy collage / no foreground-background depth | Cut out hero subjects (`scripts/vision/segment.py`) for Z-sandwich typography and free silhouette staging |
| `exit endV < 0.75` or `deadStops > 0` | Elements brake awkwardly before cutting out | Drive exits with accelerating curves (`in3` / `inExpo`) peaking at the cut frame |
