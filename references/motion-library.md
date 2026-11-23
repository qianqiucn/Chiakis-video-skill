# Motion library: one id per move, its code and the home of its rule
Sections: Setup · How to use · Motion sheet · Curve sheet · Samples · Entries (curve · move · type · her · cam · trans · fx · time) · Pending · Retired.

Read before any motion is designed or coded: by every craft that moves anything, by the director at the shot table (`script-writing.md` §5), and when polishing a sample. The index gives each technique a stable id and points to the one file holding its rule and numbers; `assets/template/lib/motion/` module headers mirror these defaults.

**Entry format** (read by `scripts/motion_lint.mjs`): a bullet whose first line is: the id in bold backticks · name · grade · reuse · owner craft · code.
- **id**: `<group>.<slug>`, lower case.
- **grade**: `A` house-verified standard · `B` proven inside accepted 2D motion templates · `H` house rule · `R` reference idiom · `P` experimental / pending (under «Pending»).
- **reuse**: `craft` (free in any film) · `signature` (reusable helper only, never copy the visual look).
- **owner craft**: `edit` (editor/compositor), `design` (graphic designer), `all`.
- **code**: `LIB <module> <call>` (`assets/template/lib/motion/`) · `EXISTING <lib file> <call>` (`assets/template/lib/`) · `PROSE` (rule in its reference home).

## Setup
- **Loaded by the template** (`assets/template/index.html`), after `engine.js` and before any segment:
  `lib/gsap/gsap.min.js`, `CustomEase.min.js`, `SplitText.min.js`, `lib/gsap-bridge.js`, `lib/motion/ez.js`, `probe.js`, `moves.js`, `blur.js`, `timing.js`, `her2d.js`. `ez.js` throws a named `T3MotionError` if GSAP or `CustomEase` is missing and sets `window.__T3_MOTION`.
  - Optional libs stay optional: `T3.her.warp2` requires `lib/meshwarp.js`; `T3.tail` with `{ v0, h }` requires `lib/choreo.js`.
- **Mechanisms, not curves:** `T3.ease`, `T3.tab`, `T3.ramp`, `T3.lerp`, and `T3.clamp` (`engine.js`) map progress; easing shapes come from `T3.EZ`, and full moves come from their library entry («How to use»).
- **Static & runtime lint:** `scripts/motion_lint.mjs` (Node, no browser for static scan; `--curves` opens headless Chrome through `run_queue.py`):
  ```bash
  # Fast static scan (no browser, ~10 ms)
  node <sk>/scripts/motion_lint.mjs web/index.html [--segments segments/a.js,segments/b.js]

  # Runtime check + SVG curve sheet
  python -X utf8 <sk>/scripts/run_queue.py web --lane lint -- node <sk>/scripts/motion_lint.mjs web/index.html --curves
  ```
- **Strict by default.** `segments/example.js` is the starter house sample and passes the lint cleanly. Projects may only opt into note mode via `scripts/motion_legacy.json` or `T3_CONFIG.motionLegacy = '<reason>'` (director only).
- **Demo and tests:** `assets/examples/motion/` plays every `LIB` entry visually (`index.html`) and runs the full Node test suite (`node assets/examples/motion/run_tests.mjs`).

## How to use
**Look the move up here by id before writing it.** Use the entry's call (`LIB` / `EXISTING`) or prose method (`PROSE`) and cite its id in the segment header; only a move no entry covers is constructed from `T3.EZ`, with its reason noted in the motion sheet. `T3.EZ` alone times one number; an entry carries the whole move (parts, settle, blur, shake).
- **By group:** `curve` named curves & probes · `move` arrivals, exits, settles, staggers · `type` kinetic letters, words, counters · `her` 2D layered character motion · `cam` 2D/2.5D camera moves · `trans` cuts and carry-over transitions · `fx` motion blur, shake, flicker, accents · `time` clocks and sequence remapping.
- **Every segment starts with two header lines** within its first 15 lines:
  ```js
  // motion-sheet: work/motion_<key>.md
  // motion: move.arrive, move.settle, move.stagger, «shot-recipes: crash-zoom-punch», «mg-styles: 8 Morph»
  ```
  Every id resolves against this file, `**name**` in `shot-recipes.md`, or `**N Name**` in `mg-styles.md`.
- **Curves:** call `T3.EZ.<name>(k)`, `T3.EZ.at(f, f0, dur, name)`, or a custom Bezier via `T3.EZ.get('M0,0 C...')`; GSAP timelines (`T3.gsapTimeline`) accept the same names. Never hand-roll ad-hoc ease math, constant-speed arrivals, or per-frame value tables (`style-grammar.md` §6b).
- **Planned exceptions** carry an inline pragma with reason:
  `// motion-ok: <kind> <reason>` where `<kind>` is one of `steps`, `scan`, `typewriter`, `blink`, `flick`, `stepped`, `measured`, `hold`.

## Motion sheet
One sheet per craft per act/sample, written before code (`work/motion_<key>.md` for Edit, `work/motion_<key>_design.md` for Design; `// motion-sheet: inline` only for very short standalone samples). Never share one sheet between parallel crafts.
```markdown
# Motion sheet <key> (<craft>) · curve family: <style-grammar §6b row> · beat: <frames per beat>
| moment | element | frames (start / length) | id | ease | stagger / settle | departure and reason |
|---|---|---|---|---|---|---|
| title in | lead word | 12 / 14 | move.arrive | T3.EZ.snap | 2 f stagger; settle 0.5 % | — |
Probes: <ids, at least 3>
```
- Every id in `// motion:` appears in the sheet; frames align to the beat grid (`beats.py` / `onsets.py`).

## Curve sheet
- **Probes:** register at least three probes per segment in `init()` via `T3.motionProbe(id, f0, f1, f => ({ x, y, s, r, o }))` on the exact pure pose functions `render()` draws with (at least an arrival, an exit, and a camera or transition move).
- **Plot:** run `motion_lint.mjs --curves` to write `lint.txt`, `curves.svg`, and `curves.json` (in `--out <dir>`, never sharing one output folder across parallel lanes).
- **Read the curve sheet** against `style-grammar.md` §6b before sharing any preview: confirm front-loaded (or cushioned AE-Bezier) arrivals, accelerating exits into cuts, non-zero settle after landing, and zero unintended flat plateaus or velocity corners.

## Samples
Even a short preview sample follows the same workflow: template `lib/motion` loaded, library ids cited, motion sheet written, static `motion_lint` clean (0 FAIL), and curve sheet inspected before sending to the client.

## Entries

### curve
- **`curve.house`** · named house curves · H · craft · all · LIB ez.js T3.EZ
  Look: genre curve families (`snap`, `expoOut`, `p4out`, `quintOut`, `p3in`, `expoIn`, `back`, `elastic`, `sine`, `roll`, `fly`, `bump`), clamped, GSAP underneath · Timing: → `style-grammar.md` §6b; custom AE Bezier paths via `T3.EZ.get('M0,0 C...')`.
- **`curve.probe`** · curve probe and curve sheet · H · craft · edit · LIB probe.js T3.motionProbe
  Look: samples position, scale, rotation, and opacity every ¼ f and plots velocity/progress · Timing: → «Curve sheet».

### move
- **`move.rise`** · crisp editorial rise in, sink out · A · craft · edit, design · LIB moves.js T3.mv.rise
  Look: fade, short rise, and soft-to-sharp de-blur in; shorter lift and blur out; zero overshoot · When: clean titles, labels, and refined UI (not hype slams).
- **`move.arrive`** · snap arrival, fast head and long settle · H · craft · edit, design · LIB moves.js T3.mv.arrive
  Look: front-loaded travel into place with a smooth braking tail · Timing: → `style-grammar.md` §6b (swap `ease` to soft AE Bezier path for lyrical PVs).
- **`move.leave`** · accelerating exit into the cut · H · craft · edit, design · LIB moves.js T3.mv.leave
  Look: speed rises to peak on the cut frame · Timing: → `style-grammar.md` §6b, §3c.
- **`move.settle`** · after-landing drift and scale creep · H · craft · edit, design · LIB moves.js T3.mv.settle
  Look: landed elements retain subtle drift (1–3 px/s) or 0.5 % scale creep so frames never freeze dead · Timing: → `style-grammar.md` §6b.
- **`move.stagger`** · shrinking-interval stagger · H · craft · edit, design · LIB moves.js T3.mv.stagger
  Look: batch items dealt or revealed with geometrically tightening gaps (e.g. `8 -> 3 f`) · Timing: → `style-grammar.md` §6b.
- **`move.decay`** · landing without bounce · H · craft · edit, design · EXISTING choreo.js T3.decay
  Timing: → `graphic-design.md` §7.
- **`move.pop`** · back or elastic pop · R · craft · edit, design · LIB ez.js T3.EZ.back
  Timing: → `style-grammar.md` §6b (`T3.EZ.elastic` sparingly on heavy objects).
- **`move.drift`** · sine drift for backgrounds and calm shots · H · craft · edit, design · LIB ez.js T3.EZ.sine
  Timing: → `style-grammar.md` §6b (backgrounds & calm/atmospheric shots only; never for arrivals).

### type
- **`type.slam`** · title slam · R · craft · design · PROSE
  Timing: → `graphic-design.md` §1, `T3.EZ.snap` + `move.settle` (`style-grammar.md` §6b).
- **`type.reveal`** · word and line reveals · H · craft · design · PROSE
  Look: default `move.rise`; genre options include «shot-recipes: blur-slide», per-letter de-blur (`graphic-design.md` §6), and per-glyph kinetic typography (`graphic-design.md` §5).
- **`type.lyric-line`** · distinct choreography per sung lyric line · A · craft · design · PROSE
  Timing: → `graphic-design.md` §2 «Lyrics» and §5 (per-glyph kinetic rules).
- **`type.stencil`** · stencil plate and knock-out halo · R · craft · design · EXISTING choreo.js T3.stencil
  Timing: → `graphic-design.md` §7 (`T3.stencil`, `T3.knockHalo`).
- **`type.chars`** · per-character rise and prefix-preserving word swap · B · craft · design · LIB moves.js T3.mv.chars, T3.mv.swap
  Look: characters rise sequentially (1 f per char); on a word swap the shared prefix holds completely still while differing suffixes exit and enter cleanly.
- **`type.roll`** · instrument-like tabular value roll · B · craft · design · LIB moves.js T3.mv.roll
  Look: quadratic ease-out onto target value over 12–24 f with tabular digits (`font-variant-numeric: tabular-nums`) and preserved decimals.

### her
- **`her.wave`** · rooted travelling wave for 2D hair, ribbons, and veils (two-pass alpha warp) · A · craft · edit · LIB her2d.js T3.her.wave, T3.her.warp2
  Look: hair and translucent veil layers bend root-to-tip in a travelling wave; warped as two opaque passes (`multiply` + `lighter`) via `lib/meshwarp.js` so soft alpha edges never seam · Timing: → `style-grammar.md` §6d.
- **`her.eyes`** · eased eye states: blink, gaze, glance · A · craft · edit · LIB her2d.js T3.her.eyes
  Look: 4-frame opacity-blended blink (`50 / 100 / 100 / 50 %`) and smooth direct gaze blends · Timing: → `style-grammar.md` §6d.
- **`her.camera`** · cosine 2D group camera still moving at the cut · A · craft · edit · LIB her2d.js T3.her.cam
  Timing: → `style-grammar.md` §6d.
- **`her.motes`** · drifting dust motes with 5-tap sub-frame shutter blur · A · craft · edit · LIB her2d.js T3.her.motes
  Timing: ~8 wind-driven motes (1–9 px/f, 4-f fades, 2.2 px wobble, 5 sub-frame samples over ±¼ f).
- **`her.hand`** · rigid layered hand/prop slide · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §6d.
- **`her.stepped-fall`** · figure floating along a smooth path through a stepped world · R · craft · edit · PROSE
  When: deliberate stepped / `Posterize Time` passages only · Timing: → `style-grammar.md` §6e.

### cam
- **`cam.her-hold`** · subject moves while 2D camera nearly holds · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §6c.
- **`cam.insert-push`** · gentle S-curve push or pull on an insert · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §6c.
- **`cam.orbit-crane`** · Blender 2.5D depth-relief orbit or crane · H · craft · edit · PROSE
  Timing: → `relief-25d.md` §2 (`scripts/blender/depth_relief.py` + `scripts/vision/depth.py --soften`).
- **`cam.punch`** · crash-zoom punch at the cut · R · craft · edit · PROSE
  Timing: → «shot-recipes: crash-zoom-punch».
- **`cam.multiplane`** · layered 2D planes at CSS-3D depths · H · craft · edit · EXISTING multiplane.js T3.multiplane
  Timing: → `style-grammar.md` §6d (`lib/multiplane.js` header).
- **`cam.depth3d`** · single illustration + depth map gentle WebGL2 parallax · H · craft · edit · EXISTING depth3d.js T3.depth3d
  Timing: → `lib/depth3d.js` header (keep camera angles gentle to avoid edge stretch).
- **`cam.emblem`** · layered CSS-3D emblem standing up on the beat · H · craft · design · EXISTING emblem3d.js T3.standUp
  Timing: → `graphic-design.md` §7 (`T3.emblem3d`, `T3.standUp`).

### trans
- **`trans.flash`** · white flash · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3.
- **`trans.whip`** · whip push and whip pan · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3, §3b.
- **`trans.ink`** · ink dissolve · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3.
- **`trans.wipe-fg`** · foreground or object wipe · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3, §3b.
- **`trans.shape-mask`** · shape-mask reveal · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3, §3b, §3c.
- **`trans.bloom`** · overexposure bloom · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3, §3c.
- **`trans.glitch`** · glitch montage and glitch slice · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3, §3b.
- **`trans.letterbox`** · letterbox close · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3.
- **`trans.light-leak`** · light leak over the cut · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3b.
- **`trans.match-cut`** · match cut · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3b, §3c.
- **`trans.page-curl`** · page curl along a moving fold · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3b.
- **`trans.handoff`** · cross-act hand-off carried by one transforming element · R · craft · edit · PROSE
  Timing: → `style-grammar.md` §3c (5–15 f).
- **`trans.implode`** · implode to dot or mark · R · craft · design · EXISTING choreo.js T3.implode
  Timing: → `graphic-design.md` §7; `style-grammar.md` §3b.
- **`trans.tail`** · carry-over afterimage / afterglow across the cut · B · craft · edit · LIB timing.js T3.tail
  Look: outgoing frame or highlight lingers across frames 0–3 of the incoming shot (`afterimage`: 38 / 16 / 5 / 2 %, `afterglow`: 30 / 14 / 6 / 2 %) · Timing: → `style-grammar.md` §3c.

### fx
- **`fx.shutter`** · sub-frame 2D motion blur · A · craft · edit · LIB blur.js T3.blur.shutter
  Look: averages moving elements across sub-frame taps (180° shutter: 5 centred taps ±¼ f; 360° opaque shutter: 10 trailing taps ending on `f`, backed by `destination-over`) · Timing: → `house-style.md` §4.
- **`fx.radial`** · decaying radial push blur after a cut · A · craft · edit · LIB blur.js T3.blur.radial
  Look: 10 scaled copies (`1 .. 1 + spread`) at `1/(i + 1)` alpha, `spread = 0.22 * exp(-0.55 * k)` over 9 f; pairs with `T3.blur.push`.
- **`fx.shake`** · decaying hit shake · B · craft · edit · LIB timing.js T3.shake
  Look: `amp * (1 - k)^2` over 7 f alternating sides with deterministic per-frame hash jitter (`T3.rand`) · How many per act: → `house-style.md` §6.
- **`fx.flick`** · power-on flicker · H · craft · design · EXISTING choreo.js T3.flick
  Timing: → `graphic-design.md` §7.
- **`fx.preglow`** · light rising ahead of an arrival · H · craft · design · EXISTING choreo.js T3.preglow
  Timing: → `graphic-design.md` §7.
- **`fx.impact`** · impact frames · R · craft · design · EXISTING accents.js T3.impact
  Timing: → `graphic-design.md` §5; impact frame restraint budget in `house-style.md` §6.
- **`fx.polygons`** · fast-cut polygon accents · R · craft · design · EXISTING accents.js T3.accents
  Timing: → `graphic-design.md` §5; polygon strobe accent restraint in `house-style.md` §6.

### time
- **`time.twos`** · stepped clock (`Posterize Time`) with optional landing re-anchors · A · craft · edit · LIB timing.js T3.twos
  When: deliberate stepped / `Posterize Time` passages or PV remakes (`n = T3.FPS / targetFps`, e.g. `2.5` for 12 fps on 30 fps) · Timing: → `style-grammar.md` §6e.
- **`time.relief`** · relief sequence playback remapper undoing Blender's SINE ease · B · craft · edit · LIB timing.js T3.relX
  Look: maps progress `s` via `(n - 1) * acos(1 - 2s) / pi` so Blender `depth_relief.py` sequences play on any `T3.EZ` curve through `T3.sequence({ frac: true })` · Timing: → `relief-25d.md` §3.

## Pending
- **`trans.sheet`** · shared-plane rotation transition · P · signature · edit · PROSE
- **`fx.loupe`** · live scene-redrawing 2D magnifier lens · P · craft · edit · PROSE
- **`trans.ground-walk`** · background colour walked smoothly in OKLCH across a cut · P · craft · edit · PROSE
- **`type.letter-land`** · letter landing with bump + ink splash · P · craft · design · PROSE

## Retired
- `T3.meshwarp.sway` for human hair or translucent veils: use `her.wave` (`T3.her.wave` + `T3.her.warp2`); reserve plain `meshwarp.sway` for tails, flags, and ribbons.
