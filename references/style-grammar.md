# Style grammar — 2D editing, motion curves, transitions & cadence
Sections: §1 act structure · §2 rhythm · §3 cuts and transitions · §3a transitions by genre · §3b more families · §3c hand-offs · §6b motion curves · §6c where motion lives · §6d 2D staging · §6e stepped cadence (`Posterize Time`). (Titles, typography, colour, 5-layer framing, tagline cards, and helpers live in `graphic-design.md` §1–§7.)

Read before storyboarding the cut. `house-style.md` wins where they differ.

## 1. Act structure & pacing
A strong fast-cut 2D film balances tension and release across acts (typically 8–20 s per act or verse/chorus section):
- **Hook / Cold Open (1–3 s)**: establish visual medium, palette, and tempo immediately; open already moving.
- **Build / Development (4–12 s)**: escalate density through shorter cuts, layered graphic accents, or per-glyph lyric choreography toward the drop or chorus.
- **Drop / Climax**: mark the downbeat (`floor(onset_frame)` from `scripts/onsets.py`) with a deliberate carrier transition (§3c) or full-canvas visual shift.
- **Release / Button (1–3 s)**: let the final hero motif or end card settle gently (`move.settle`) without freezing dead.

## 2. Rhythm (24 fps)
| unit | frames | note |
|---|---|---|
| beat | 1440 / BPM (126 → 11.43); bar 46, 16-beat phrase 183 | tempo from `beats.py`, whose grid is only an estimate; phase and every drop frame from the measured downbeats (`onsets.py`; the fitted grid below; SKILL.md Pitfalls) |
| montage shot | 2 beats ≈ 23 | the backbone: fast-cut montages commonly anchor around 2-beat (~20–24 f) shots |
| burst cut | ½ / ¼ beat ≈ 6 / 3 | runs of 2–6-f cuts, e.g. accelerating into the drop |
| title shot (ours: the title moment) · logo card | ≈ 34 · ≈ 65 | the only long shots besides the breath |
| breath | ≈ 55 (2.3 s) | usually one passage (ink → dissolve → her reading) |
- **The backbone counts picture changes, not type changes.** A painting held for several beats while only its type
  animates reads as a slideshow, whatever the type does: the shot itself changes on the backbone (a new picture, a new
  framing of it, its action reaching a new phase), and the long holds are only the ones the table names. Holding a static picture for 1.5–2.5 s while only text moves reads sluggish; fast-cut hype sections typically refresh visual composition every ~0.5–1.0 s.
- **Fit the grid to measured hits:** `onsets.py` downbeats at every drop plus 4–6 strong bars, then a least-squares
  t = t0 + n·T. Residuals ≤ ½ f: the grid holds; a trend: fix `bpm`; a step: a tempo change or a splice, fit per
  section. Half- or double-time is decided by data: the right grid puts the kicks on whole beats.
- **What drives what** (calibration): kick (< 150 Hz) → impacts, shakes; snare or clap (150–500 Hz + a 1–3 kHz crack)
  → swaps (cuts, card swaps); hats (6–14 kHz) → the density of micro-motion, dense where the hats run, sparse where
  they stop (never frozen: house-style §6). The hit list is a pool to choose from, never a trigger list.
- **Where each cut lands:** regular hard cuts on the fitted grid's beats, isolated accents (flashes, slams) on the
  measured transient, each on the frame that contains it (floor); start an arrival ~2 f early so the end of its fast
  head is the beat frame, its settle running on past the beat (§6b). On high-energy whip/zoom sequences, a hard cut
  itself may lead the beat by 2–4 f so the incoming motion blur or rack focus finishes sharp on the downbeat (fast-cut PV timing). The last hold lands on the last real transient where the RMS falls silent, not on a reverb tail.
  Clips and samples align by their own peak: start = cut frame − the clip's peak frame (`measure.py` on the clip).
- Music window: work back from the drop (= the drop slam). A 50 ms RMS scan (ffmpeg → s16le → Python) shows where the breaks are; the hit frames come from the downbeat (SKILL.md Pitfalls). 
- **Re-cutting to a new song** with every asset reused (beat-remapped wrapper pattern):
  - **Measure first.** Get the new song's tempo, its downbeats and the build-up → drop arcs, then tell the client how far the song is from the old one and which parts need care.
  - **Map beats, not seconds.** Each intro's old beat k goes to the new beat k. A wrapper around `T3.register` hands every intro layer its original time, so the approved segment code stays untouched; the drops simply take the new drop, switch and off frames.
  - **Place the extra frames with the picture in mind** when the song is slower:
    - put the repeats where the approved render moves least (rounding the map evenly put repeats into fast motion);
    - pin hard cuts, shot starts and drops to beats, and never repeat a shot's first or last two frames;
    - segments that can take a fractional frame (camera pushes, image-sequence crossfades, pose blends) draw real in-betweens; mechanical motion (ratchets, flash frames, card swaps) keeps whole frames;
    - a blink keeps the sample's four frames instead of stretching with the song;
    - a faster song is the same problem in reverse: drop frames where the picture is stillest.
  - **Fit the song to the film where it lacks arcs.** A song with fewer build-ups into a drop than the film needs (one per major act or drop) is rearranged by bars . Each splice sits at the same relative position inside identical stop bars, with a crossfade of a few milliseconds, and nobody can hear it; the spliced song stays float until the master (production.md «Splicing the soundtrack»).
    - A few-ms crossfade hides a splice only between matching bars. Where the energy or a tail differs (an 808 tail cut into a sparse opening), use an equal-power crossfade of about 0.5 s with a gradual low-pass on the outgoing side, keep the drop frames where they were, and re-check them with `onsets.py`.
  - **Shorten in whole shots, by beats, and check what a dropped shot carried** (a layer's only home: house-style §5).
  - **Line up the sound cues again.** Each intro had moments built on a specific sound, such as a stop, a whisper or a heavy hit. Find the nearest matching sound in the new song, or the nearest strong beat.

## 3. Cuts and transitions (measured)
| name | frames | how |
|---|---|---|
| hard cut | 0 | most cuts; the new shot often starts defocused and sharpens in 2 f |
| fade-up from black | 2 | intro start after a cut to black (15 % → 60 % → 100 %) |
| white flash | 6 + 2–3 | light blooms out of a bright area to flat #F2F4F4, hard cut, the next shot dark and defocused for 2–3 f |
| overexposure bloom | 8 + 9 | a leak burns one side of the frame to white, hard cut on the peak, the next shot clears from a light-grey fog (into the drop; measured: §3c) |
| whip push | 4 + 1 black | accelerating push with motion blur into an object (the inkwell), then one pure-black frame |
| ink dissolve | 12 | ink-in-water footage on black, crossfade; the ink lingers as a fading red tint on the next shot |
| foreground wipe | 9 | a huge defocused, rim-lit object (a petal) sweeps across; the cut hides behind it |
| fade to black | 4 + 4 black + 2 up | before a section change |
| letterbox close | ~31 | 2.35:1 bars (132 px each) close into a glowing horizontal line; hard cut |
| glitch montage | 21 | 1-f cuts: white, side shot, magenta noise, 9 posterised frames with translucent bars jumping each frame (tint pink → icy white), 4 dark frames |
| shape-mask reveal | 3–5 | the logo shape opens as a hole in black onto the next shot (measured: §3c) |
| line → dot → shape | ~10 | the tagline collapses into a line, then a dot, then the logo shape (→ mask reveal; measured: §3c) |
| mosaic resolve | 3 | 30–40 px blocks → clear |
| ASCII swap | 1 + 1–3 | the new shape appears as random glyphs for 1–3 f, then resolves |

## 3a. Transitions belong to the genre
| genre | transitions (the three intros share almost none) | feel |
|---|---|---|
| idol PV / hype / fast-cut | spotlights switching on in pairs (one pair per frame, centre outward), overexposure flash cuts, letterbox close, glitch montage, ink-shadow sweep to black, line → dot → star, star-mask reveal into the drop | punchy, light- and glitch-driven |
| mechanical / graphic chronicle (ASCII, HUD, print) | every scene swapped within a frame through 1–3 f of glyph noise; the logo fades in inside a glyph ring; the ASCII layer fades out over the drop | never leaves the medium; no plain crossfades |
| literary MAD / atmospheric | 2-f fade-up, tumbling letters, white flash + defocus-in, whip push + 1 black, ink dissolve, petal wipe, fade 4 + 4, overexposure into the drop | soft, object-based (focus, ink, petals from her world); no glitch |
- **Every transition has a material**: light, footage, glyph noise, an object of her world, the medium itself. A flat
  colour pattern wiped across the frame (solid diamonds, plain bars) reads as a presentation template, not an edit
  (avoid slide-deck wipes).
- Take the set from the entry's genre and vary within it (a transition from another genre needs a story reason). Per intro: 3–4 families besides hard cuts, none more than ~3×; the motif about 3 times (plant, build, payoff); one signature transition, once, at the climax.
- Across major act/drop boundaries: pick one carrier transition (§3c) that matches the piece's visual medium.

## 3b. More families (for originals — keep to the genre)
| family | frames | how |
|---|---|---|
| match cut | 0 | B starts with A's last shape at the same place, size and colour (ideally the same motion) |
| zoom-through | 6–10 | push fast into a dark or bright area of A (multiplane z ↑, blur), emerge from B's centre |
| whip pan | 4–6 | both shots slide 1920 px with directional blur |
| light leak | 6–12 | light-leak overlay sequence (`lib/sequence.js`) or bundled textures (`assets/textures/`) screen-blended, its peak hiding the cut; at full speed it strobes — half speed, warm grade, opacity ≈ 0.4 → 0.12, one burst on the downbeat |
| luma wipe | 8–12 | B shows where a grey map (ink footage, clouds, scanlines) passes a rising threshold |
| shape mask | 4–8 | the logo/emblem shape grows as a hole — the signature one |
| object wipe | 6–10 | a foreground object (fish school, page, cable) crosses the lens; cut behind it |
| glitch slice | 3–8 | bands of A and B offset and swapped, RGB split, settle |
| flash frame | 1–2 | one white or colour frame on an accent |
| speed ramp | 6–12 | the camera accelerates (`expo.in`) into the cut, B decelerates out |
| page curl | 8–12 | A curls from a corner along a moving fold (paper back, curl highlight, shadow on B); a full-frame rotateY leaves the frame at 90° |
| particle dissolve | 10–16 | A breaks into particles (precomputed colour grid) that re-form as B |
| implode → dot → mark *ours* | ≈ 10–12 | graphic-design §7 |
| monotone bridge (red-sandwich) | 2–10 | last 1–2 f of A and first 1–2 f of B share one duotone grade (e.g. crimson/burgundy + LED dot mesh → directional smear → white/dark peak), stitching clashing palettes across a cut |
| center-circle anchor morph | 4–8 | a circular disc stays locked at frame centre across a rotational spin-flash cut, swapping only its interior art and surrounding layout so the eye never jumps |
| dark black-hole breather | 3 | three static matte charcoal frames with a central black void dropped mid-burst on a beat to reset visual density before the next slam |
| continuous 2.5D table pan | 4–6 | camera glides diagonally or vertically across one connected collage surface with linear directional shutter blur (`panBlurX/Y`) rather than spinning isolated title cards |
| pixel-locked object / anchor match cut | 0 | hero prop (flower, centre card of a 3-beat deck, or outro CRT) stays locked to identical `(x, y, scale, rot)` pixels across a hard cut while the surrounding world snaps on beat 1 (apply identical soft circular/edge clip on both sides of the cut so cropped sprite edges never peek; never spin a locked-anchor match cut) |
| foreground framing anchor | 0 + 4 out | foreground character/hands/viewfinder stay stably anchored in the outer frame while only an inner UI window rotates/stacks on beats, saving a tight 4-f whip-spin for the exit |
| vacuum contraction → blinding drop | 8–10 + 3 | drop all colour and noise to near-black (`#09080C`) with a single razor-thin white wave/whisper for 8–10 f, sweep a 3-f foreground wipe, then explode into a blinding high-key chorus — cutting loud pink into loud pink flattens the drop |

- **Transition discipline (Canvas 2D PV best practices):**
  - Never put the same full-frame whip-spin on every cut ("centrifuge fatigue"): vary across the families above, keep full-frame spins to 4–5 f on high-torque accents only, and never break locked-centre match cuts (card decks, outro TV sequences) by spinning the anchor.
  - Stage lyric/headline cards cumulatively every 4–6 f on vocal syllables instead of slamming a finished 4-word card that sits frozen for 20+ frames; evolve multi-beat stages (e.g. a timeline with 3 diamond frames) in place rather than smash-cutting mid-phrase.
  - Never leave a solid opaque white blank frame (`#FFFFFF`) on a soft release cut: cap translucent blush/white release veils at `alpha ≤ 0.50` decaying via `expoOut` so the incoming figure already breathes through frame 2.

## 3c. Why strong cross-act hand-offs read as one movement
A great hand-off into a chorus, drop, or new act is **one continuous motion carried by a single element** — never an arbitrary screen wipe pasted on top of a cut:
1. **Shape morph / mask reveal**: a hero emblem, aperture, or frame in shot A expands or rotates over 5–15 f so shot B opens *inside* that shape (`trans.shape-mask`).
2. **Pre-laid geometry**: the closing shot already aligns a grid, horizon, or typography baseline that shot B locks straight onto (`trans.match-cut`).
3. **Overexposure bloom / atmospheric veil**: highlights bloom across the downbeat and clear over 3–6 f of shot B via `T3.tail(f, fCut, 'afterimage' | 'afterglow')` (`trans.tail`, `trans.bloom`).
4. **Hard cut inside peak velocity**: the outgoing element accelerates (`T3.EZ.expoIn`) so the cut falls on its fastest frame, and the incoming element opens already in motion (`move.leave` → `move.arrive`).

Avoid covering wipes that merely sweep across and hide the cut without connecting the motifs of shot A and shot B.

## 6b. Motion curves follow the genre (`scripts/motion.py`; eases are GSAP names; moves: motion-library.md «How to use»)
In-shot motion is the mean absolute frame-to-frame luma difference at 320 px wide (`motion.py`), 0–255 scale; the
numbers below are in that unit.

| genre | in-shot motion | shape | curves |
|---|---|---|---|
| idol PV / hype / fast-cut | ≈ 7.8, CV ≈ 0.9 | front/back ≈ 1.8: slams in, brakes, holds | arrivals `expo.out` / `power4.out` / `CustomEase "M0,0 C0.05,0.9 0.1,1 1,1"` over 10–16 f, 70–80 % of the travel in the first 2–3 f (the reference's visible 2–6-f snap is that head; the settle runs on under it); exits `power3.in` / `expo.in`, accelerating into the cut; pops `back.out(1.7)`, `elastic.out(1,0.45)` sparingly on heavy things; punch-in zoom at the cut; whip pans; motion blur on the fast part |
| lyrical fast-cut PV / AE Bezier collage | smooth, overlapping | Q1 ≈ 64–72 %: cushioned long glide | avoid harsh HUD `snap` cliffs (`Q1 ≈ 89–96 %`) and dead-start `expo.in`: arrivals `CustomEase "M0,0 C0.22,0.72 0.36,1 1,1"` (`Q1 ≈ 64 %`) / `"M0,0 C0.20,0.78 0.34,1 1,1"` (`Q1 ≈ 69 %`) over `14–22 f` with 2–3 f overlapping stagger; early-leaning exits `"M0,0 C0.42,0 0.78,0.30 1,1"` (`endV = 1.0`); gentle micro-overshoot pops `"M0,0 C0.22,1.22 0.38,1 1,1"`; camera glides `"M0,0 C0.62,0 0.38,1 1,1"` (keep any `settle` light enough that `Q1 ≥ 60 %` on probes) |
| literary MAD / atmospheric | ≈ 7.9, CV ≈ 0.8 | front/back ≈ 0.6: starts nearly still, builds into the cut | `sine.inOut` drifts, or accelerating `power2.in` / `sine.in` / `CustomEase "M0,0 C0.6,0 0.9,0.6 1,1"`; long dissolves, rack focus, blooming light; no overshoot, no in-shot shake (hit shakes: house-style §6) |
| mechanical / graphic chronicle | mechanical | discrete | `steps(n)`, per-frame glyph flips, linear scans, typewriter cadence |
| calm / cozy (only if the client asks) | ≥ 5 (3.0 read as frozen) | slow, never stopped | long `sine.inOut` drifts overlapping the cut, ±1–2 % breathing, dust and light, her hair and veil wave (§6d); ≤ 1 sharp accent |
- Total in-shot motion ≈ 8 (10–14 reads busy, nothing hits); contrast still and fast. Never a symmetric in-out ease on an arrival, nor one ease for every shot (zero velocity at every cut = slideshow). Hype: shot B starts already moving; MAD: the slow build carries into the cut. Landing without bounce: `T3.decay` (graphic-design §7).
- Nothing travels at constant speed but a mechanism or a medium's cadence (steps, scans, typewriter). A batch (cards,
  letters, glyph rows) staggers on a shrinking interval (e.g. 8 → 3 f) with a physical cause (dealt, poured, stamped),
  then settles in ≈ 12 f while the other layers keep moving; an even stagger reads as a slide deck.
- **Nothing stops dead after it lands** : a landed element keeps a settle of 1–3 px/s or a
  0.5 % scale creep, the parts of one move (letters, stroke, shadow, ink, label) land 1–2 f apart, and the next shot
  comes in already moving. A move that dashes in over 3–6 f and parks reads as stiff, whatever its curve.
- **No per-frame value tables** outside drawn states (a blink, a flicker) and mechanisms: hand-keyed values play as
  jumps; values come from a named curve, and an exception is declared in the code (motion-library «How to use»).
- **The curve sheet decides, not the thumbnail** (motion-library «Curve sheet»): the probed moves are plotted before a
  sample goes out and before delivery, and read for front-loaded arrivals, exits accelerating into the cut, a settle
  after landing, and no straight runs or corners. Stiffness is invisible on a contact sheet.
- A low number is fixed with moving layers, never with camera moves inflated against the genre. Check: `python -X utf8 scripts/motion.py our.mp4 t dur ref.mp4 t dur` (mean, front/back ratio, per shot too).

## 6c. Where the motion lives (2D character & insert proportions)
- Character shots: the subject moves and the camera nearly holds (drift ≈ 2–6 px/f).
  - The motion is secondary and small: hair and veil streaming in wind, ribbons drifting across the foreground, a walk away from camera.
  - On the hand insert the hand glides over the book (its numbers: §6d) while the whole frame zooms 9 %; in the reading shot only hair, veil, a blink and drifting specks move.
  - Separate moving layers (hair, cloth, eyes, props) + `lib/meshwarp.js`; subject motion is worth more than inflated camera parallax.
- Inserts (props, still lifes): the prop stays rigid; the camera drifts on an S-curve (slow → 4–13 px/f → slow) or accelerates into the cut, often opening on a rack focus. Stage insert depth in 2D multiplane (`lib/multiplane.js`) or gentle depth displacement (`lib/depth3d.js`).
- Every shot carries small ambient motion: flickering light shafts, falling dust, embers or petals, a glint running along a hair strand, a 2–3-f specular flash on the hero prop (the reference's list; ours keeps one sheen per
  shot, house-style §6). The accents are light, not movement.
- Calibration for a soft genre only: an intro's own idea sets how its motion is spread (house-style §0); hype and medium-driven intros spread it differently (§6b).
- **A process is told across cuts** (every genre and form): a change in her or the things
  around her that runs on (a slide down, a threat closing in, a tilt growing) is a run of shots, each holding one
  state. In each, she and the things in the picture keep their place (how high, how near, how tilted) while the camera
  holds or makes one slow push; the next cut finds them a step on: lower, nearer, more tilted. Inside a shot that place
  never steps (held a few frames, then moved on) nor creeps forward in small jerks: both read as crawling, however
  striking in stills; nor is the run one continuous move carried across the cuts.
  - Held is not frozen: their own life goes on (her hair's slow wave, a blink, a breath, cloth: §6d), the air keeps
    moving (fog, dust, a flame) and a push is still moving at the cut (§6b), so no shot reads near-still (house-style
    §6, quality-bar Gate B1). An action shot carries one whole action and stops.
  - Cuts and their tools stay: hard cuts, impact frames, flashes, jump-cut push-ins.
  - A camera journey through spaces (house-style §0) and a fall or flight built in full keep their continuous move:
    that is travel, not a process. Stepped motion only where §6e allows it.

## 6d. Staging layered 2D character & scene motion (`lib/motion/her2d.js`)
Layered 2D compositing works on still illustrations or separated PNG plates: every move fits a similarity transform (no perspective change), and each moving thing is its own layer.
- Camera: one image or a stack of layers zoomed, panned and rotated as a group on smoothstep or cosine curves (a 9 % zoom; a 201-px pan peaking at 13 px/f; a −4.5° turn with a 7 % pull-out), often still decelerating when it is cut.
- Depth without 3D: layers slide at their own share of the pan (back wall 0.98×, shelf 1×, a prop 1.08×, out-of-focus foreground 1.14×); a prop pops toward the lens by scaling 4–5 % about its own centre on an ease-out; a raised emblem reads as raised because a light band sweeps across the shiny parts with a one-frame white peak, not because anything turns.
- Her, part by part:
  - a hand and sleeve slide as one rigid layer (≈ 17 px, cubic ease-out, fingers never bend);
  - hair and veil bend in a slow wave from root to tip: peak to peak 3–4 px near the root, 6–7 px mid-length, 12–14 px on a few strands; each 100 px further out lags 3–4 f sideways, while the vertical part, ≈ 0.4 × the sideways one, travels faster; period ≈ 1.3–1.4 s (hair 33 f, veil 31 f);
  - a blink is four frames: an aligned closed-eyes edit laid over the open eyes at 50 %, 100 %, 100 %, 50 % opacity (`T3.her.eyes`);
  - anything worn on her head or hair rides what holds it: in a hair sway or a moved part, a bow, pin or clip follows its root's warp or transform (the approved sample animates its bow as its own layer); left on the plate it reads as pasted on.
- **Eye states ease in; they are not swapped.** A blink, a raised gaze or a glance changes by blending an aligned edit over the eyes, as the approved sample does; that ease is the house way, because frame-by-frame swaps of drawn states read as jumps, even with a drawn half-closed frame between them .
  - The edit is pasted back , so it differs from the picture only around the eyes, and drawing the whole edit at partial opacity changes only the eyes.
  - **Gaze changes blend the two end states directly** (looking up, a glance), with no drawn middle state. Call `her.eyes` (motion-library); its blend runs over one 50 % frame for a quick move or 2–3 frames for a slow one. A paused in-between frame shows two pupils; in motion it plays as a blur.
  - **A state the shot holds is its own drawn edit**, such as sleepy half-closed eyes kept for a beat. Never fake it with a long dissolve, which shows doubled lashes and a pupil through the lid. Prepare clean aligned end-state PNG layers (open eyes, closed eyes, alternate gaze) before compositing so blending affects only the eyes.
- Speed and accents: a dive into a prop is a 2D zoom accelerating to ×5.8 with a two-sample motion blur (doubled images at ¼ frame apart), darkening to black; a focus pull clears in ~8 f at the head of a shot; flames flicker in brightness only; a few specks drift on their own layer.
- Our tools for each: `T3.sequence` / `T3.multiplane` for depth planes, client-supplied or pre-split PNG layers, the approved sample's rooted wave for hair and veil (`her.wave`, motion-library; `T3.meshwarp.sway` is a plain sine from one root, for tails, ribbons and cloth), aligned eye-state layers for blinks (`T3.her.eyes`), and procedural Canvas light sweeps.
  - The sample's own motion is in the template as code (motion-library group `her`, `lib/motion/her2d.js`): the wave and the two-pass warp below (`her.wave`), the eye-state opacities of the blink, gaze and glance (`her.eyes`), the group camera (`her.camera`) and the dust (`her.motes`). Build her shots on these calls; the figures here stay the reference they reproduce.
- **Reference 2D composite recipe** (verified with `lib/motion/her2d.js`):
  - Asset prep: generate the single-layer hair RGBA + outer-background zero-ghosting clean plate + 1080p rig boxes in one shot via `scripts/vision/part_cutout.py <in.png> <hair.png> --part hair --clean-plate <clean.png> --json <rig.json>` (`art-pipeline.md` §4), and align closed-eye/gaze edits via `scripts/vision/pasteback.py --align --lf 40`.
  - Layers: clean plate + closed-eyes patch + hair + static front trim + veil + bow, dust on its own canvas.
  - Camera: group zoom × 1.0755 and pan 88.6 px on cosine curves, still moving at the cut; the plate over-scaled 2 % so no edge shows.
  - What made it hold up at 1:1:
    - a semi-transparent layer is warped as two opaque images (premultiplied colour, and 1 − alpha) recombined with multiply + lighter, because meshwarp's overlapping triangles draw seams on soft edges;
    - the veil's plate is softened (σ ≈ 4 px) under it, so its matte carries no sliding ghost;
    - the hair gets a 12 px difference-matte fringe for soft strands;
    - the inpainted plate under split strands shows only where a strand really moves off it, never under the feathered edge, which would smear;
    - edges in front of the hair (cape, hem trim) return as a static layer cut from the original pixels, or they wobble with it.
  - Measure the result with the same tracker as the reference (`scripts/measure.py`).

## 6e. Stepped cadence & AE `Posterize Time` (limited animation at 6–12 fps)
**Only where the reference steps** : a PV remake's own stepped passage, restaged as the
original does it. Never invented for a shot of ours, nor a default a form may break (house-style §0): an invented
stepped slide in the MV, praised by the review, was turned down as crawling (§6c, lessons.md). It covers a figure or
a world travelling in held steps (a slide, a fall, an approach); a medium's own cadence (`steps(n)` glyph flips, a
typewriter, pixel sprites, cut-out stop-motion: §6b, mg-styles.md) is not this.
Stepped motion sells a fall when the world travels in long, distinct steps, softened by a short blur along the fall, and the figure keeps one smooth path and stays sharp (below); a figure that jumps reads as shake (lessons.md, MV 匙ノ咒).
- **The whole frame steps together,** 12 times a second: on twos at our 24 fps (the reference, at 30 fps, alternates exactly 2, 3, 2, 3 frames). A held frame repeats the one before it: one stepped clock drives every layer and effect, grain included, so the steps read as a cadence, not as dropped frames. Each step changes about 42 % of the frame (median; 34–52 %; 480 × 270 grey, a change over 24 levels).
- **The world travels on every step,** each layer in its own way, all on the shared steps (px at 1080p):
  - the lit layer (light columns, glyph plates, orbs) rises straight up on every step, about 330 px a step (≈ 4000 px/s; the reference alternates ≈ 260 and ≈ 400), faster in the first 1.5 s (400–550 px, the first step ≈ 700); each element lives 2–4 steps on screen;
  - one glitch band (≈ 90 px solid, ≈ 106 px with its soft edge) rises an even 335 px a step and wraps from the top to the bottom;
  - the rain lines are re-dealt, not moved: a new layout on every step at one side, on every second step at the other;
  - a handwritten string crosses diagonally, up and to the left (one sample).
  - The world behind her takes a short vertical motion blur along the fall (about 9–17 px at 1080p, longer in the fast first 1.5 s and on the nearer, outer layers) and a layered depth of field: the nearer and farther from centre an element sits, the softer, while she and the centre stay sharp. Keep the hero subject sharp while blurring background travel layers along the fall direction.
- **She keeps one smooth path and floats on it.** Centred, she drops in from the top in about 0.8 s, fast then slowing, then drifts down about 15 px/s while shrinking to about 0.6× over 9.5 s, fastest at first, so she falls away from the lens. Per step she moves at most 5 px sideways and −5 to +8 px down, along that path (her residual after a 0.5 s smoothing: RMS ≈ 3–5 px); no random offset per step, no tilt, no bob. The float comes from her dress and hair: about 5 drawings, round once every 10 steps, the body still; with one drawing of her, warp the hem and the hair ends into those states (`lib/meshwarp.js`), never the body, face or hands. Avoid adding synthetic tilt/bob jitter to a falling subject — keep the figure's path smooth and let cloth/hair carry secondary motion.
- **Cadence alternation, exact `Posterize Time`, layered stepping, and melt** (generalized for 24 fps and 30 fps Canvas 2D timelines):
  - **Exact step size (`n = T3.FPS / targetFps`)**: `T3.twos(f, anchor, { n: T3.FPS / targetFps, end })` accepts fractional `n > 0` and reproduces AE `Posterize Time(targetFps)` exactly. On a 30 fps timeline, **12 fps is `n: 2.5`** (alternating `[3, 2, 3, 2]`, never `n: 2`, which is 15 fps `[2, 2, 2]`), **10 fps is `n: 3`** (`[3, 3, 3]`), **7 fps is `n: 30 / 7`** (`[5, 4, 4, 5, 4]`), and **6 fps is `n: 5`** (`[5, 5, 5]`). On a 24 fps timeline, 12 / 8 / 6 fps are `n: 2 / 3 / 4`.
  - **Whole-frame stepping — zero 30 fps leakage**: contrasting whole-frame rates across adjacent shots marks emotional shifts without extra effects (e.g. 12 fps darkroom, 6 fps plunge, 7 fps REC viewfinder, 10 fps shutter sequence, 12 fps CRT outro, punctuated by sudden full-rate 30 fps breakouts on an eye opening or breathing hold). Quantise the clock **at the shot entry** (`drawShot(ctx, T3.twos(f, anchor, { n: T3.FPS / fps, end }))`) so the shot body never receives raw `f`; passing raw `f` alongside `fStep` leaks 30 fps grain, bokeh drift, breathing scale, shake, or per-glyph lyrics and destroys the held-frame cadence.
  - **Layered stepping (30 fps camera / drift + 12 fps subject)**: distinct from accidental leakage, a shot may run smooth 30 fps camera/backdrop drift beneath a strictly 12 fps (`n: 2.5`) stepped subject and collage layer (e.g. slow atmospheric pan behind a 12 fps cut-out collage). Split clocks explicitly into `camF = f` (camera/bokeh/drift only) and `stepF = T3.twos(f, anchor, { n: T3.FPS / 12, end })` (figure, props, kinetic type) so each layer's cadence is intentional.
  - **Stepped-to-smooth melt (抽帧化开)**: hold a fall on coarse steps (e.g. 6 fps, `T3.twos` `n: 5`), then over the final ~0.5 s before a major cut blend `fMix = fStep + (f - fStep) * T3.EZ.at(f, fMelt, dur, 'expoIn')` so the chop dissolves smoothly into a full-rate dive into impact.
- Name the stepped passage in REVIEW_BRIEF (house-style §0), since the review lenses look for stalls, stutter, shakes and missing blur.
- Check against the reference: `python -X utf8 scripts/cadence.py ours.mp4 t dur --track BOX --subject BOX:dark --ref ref.mp4 t dur --ref-track BOX --ref-subject BOX:dark --snap DIR` (the step rhythm, each tracked element's steps, her path and residual). Track a part that keeps one drawing (face, shoes, a glyph), never a centre of colour, which a cycled dress drags; look at the `--snap` sheets before trusting a number. Before delivery on any film with multiple stepped passages, also scan frame-to-frame grayscale MAD across the rendered MP4 (`MAD < 0.45` = held frame) to confirm every whole-frame stepped zone hits its exact run-length pattern (`[3,2,3,2]`, `[3,3,3]`, `[5,4,4,5,4]`, `[5,5,5]`) with zero 30 fps leaks and every layered zone shows periodic 12 fps diff spikes.
