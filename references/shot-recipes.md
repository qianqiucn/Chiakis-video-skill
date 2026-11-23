# Shot recipes: openings, cuts, type, rhythm, camera, data, impacts, outros

A compact library of 124 shot recipes to pick moves from when storyboarding an original 2D PV, MV, promo, or transition. Condensed
and rewritten from video-shotcraft by Vincentwei1021 (Apache License 2.0),
https://github.com/Vincentwei1021/video-shotcraft; changes: condensed, rephrased, adapted to 24 fps and an HTML/GSAP
timeline.

## How to use this file
Find your job in the finder, then grep the recipe's bold name (`**crash-zoom-punch**`).
- **Who reads it, when**
  - Pitch writers (SKILL.md step 3, `assets/workflows/pitch.js`): set pieces for a form's hook, name moment, transitions
    and hand-off; a starting point, never a template.
  - Director: the genre header's transition set (script-writing §1); in the shot table's method column, the entry each
    shot starts from: the motion-library id first, a recipe here only where the library has no entry or the recipe is borrowed for its set-piece (script-writing §5).
  - Editor/compositor (crafts.md «Editing and motion»): cuts, transitions, rhythm devices, camera moves, impacts and the
    hand-off, with their numbers.
  - Graphic designer (crafts.md «Graphic design»): type entrances and the title moment.
- **Cite** a recipe by its bold name: «shot-recipes: crash-zoom-punch»; a variant in brackets: «shot-recipes:
  shot-transitions (whip)»; an entry with several names by the one you use: «shot-recipes: pill-slot-cycle».
- **Entry format**, always in this order: bold name (each name bold when there are several), tags, `—` what it is;
  `Key:` the numbers; `Use:` where it fits in our films. Names are unique; grep them in bold (card-stack also sits
  inside research-card-stack-scroll).
- **Tags**, right after the name: `★ fast-cut`, 15 strong fits for fast-cut PVs and beat-driven edits (
  house-style §1), a pointer, not a default: neighbouring intros still differ (script-writing §1) and a hand-off never
  rebuilds the reference's (style-grammar §3c). `(UI-specific)`: product-UI cards (notation below). The finder lists
  both sets.
- **Units and notation (24 fps)**: Frames are at 24 fps (the source's 30 fps × 0.8, rounded), px on the 1920×1080 stage,
  px/f speeds ×1.25; spring(d, k) = damping d, stiffness k, mass 1, timed in seconds; bezier() = cubic-bezier (a GSAP
  CustomEase); snappy = hard ease-out, swift = asymmetric in-out, smooth = symmetric in-out; "(UI-specific)" marks
  app-screenshot cards.
- **Calibration**: A recipe is a starting point and its numbers are calibration; the intro's own idea decides. Standing
  rules: a signature move once or twice per film, one time-bender and one shake source per shot, a settle after each
  move (keep micro-motion or settle so frames never read as frozen: style-grammar §6b).
- **Order**: the approved and house moves in `motion-library.md` come first; a recipe is the next resort, cited by name
  in the segment's `// motion:` header.
- **Links**: transitions come from the genre's set (style-grammar §3a; more families §3b); eases and springs are refitted
  to its curve family (style-grammar §6b) and called through `T3.EZ`; the hand-off: style-grammar §3c; every move gets its sound (house-style §1), placed
  and mastered with mgaudio (production.md «Installed on D:»).

**In our films:** use these recipes as starting points for 2D scenes, kinetic typography, and act hand-offs; adapt their curves to `lib/motion` (`T3.EZ`, `T3.mv`) and declare library IDs in each segment's motion sheet.

## Finder
By the job in our films; a recipe may sit under several jobs, and every recipe sits under at least one.
- **Open an intro** (a hook inside the first 0.5 s, script-writing §2): trailer-grammar-moves, text-as-mask,
  stroke-segment-build, magician-card-flourish, orbit-ring-title-open, spotlight-hero-card, icon-field-colorize,
  dataviz-landscape-open, brand-ink-open, letterspace-materialize, depth-layer-moves.
- **Build to a title moment** (the escalation): tension-camera-moves, depth-layer-moves, graze-face-tour,
  steep-tilt-glide, light-play-moves, spotlight-sweep-moves, scanline-annotate-focus, scan-bracket-sweep,
  aurora-bloom-bg-flip, glow-flyline-moves, orbit-ring-title-open, stroke-segment-build, typewriter-moves,
  text-column-converge, word-relay-geometry, word-relay-filmstrip, pill-slot-cycle.
- **The title moment itself** (once per intro, house-style §2; ≈ 34 f, style-grammar §2): text-as-mask,
  stroke-segment-build, letterspace-materialize, brand-ink-open, lead-word-zoom-assemble, outline-word-fill,
  type-assembly-moves, type-rhythm-sync, countdown-arc-scatter, light-play-moves, fracture, orbit-ring-title-open,
  brace-expand, card-flock-tumble, grain-dissolve, transition-travel.
- **A cut or transition between shots** (from the genre's set, style-grammar §3a; more families §3b): shot-transitions,
  transition-hidden-cut, circle-match-iris, white-flash-logo-simplify-cut, card-flip-reveal, card-flock-tumble,
  mosaic-reframe, transition-travel, wipe-transitions, print-texture-transitions, tear-streak-transitions,
  gradient-transition, theme-switch-moves, hashtag-to-pill-materialize, aurora-bloom-bg-flip, brand-frame-snap.
  - Between acts or chapters: line-carry-transition, bottom-push-stack-wipe, page-turn-transitions,
    wipe-transitions.
- **A carry-over hand-off into the drop or chorus** (one element transforms into the next scene, style-grammar §3c): title-demote-to-label, white-flash-logo-simplify-cut, hashtag-to-pill-materialize,
  theme-switch-moves, circle-match-iris, crane-rise-reveal, ui-to-brand-morph, logo-shrink-wordmark-lockup,
  shot-transitions (portal), transition-travel.
  - Cards that build a HUD, only as the intro's own pre-lay or an overlay that lands on the locked layout (the
    when a UI/data overlay enters on the drop): scanline-assemble-flyin,
    assemble-then-type-flyin, wall-reveal-moves, neon-frame-forerun, neon-frame-orbit-drop, row-embed, list-reveal,
    radial-wave, graze-face-tour, overhead-camera-moves, gauge-readout-moves, spotlight-sweep-moves, scan-bracket-sweep,
    product-card-progressive-assemble, draw-svg-trace.
- **Rhythm devices for a burst into a drop** (a 2–6-f burst counts as one cut, script-writing §4; burst cuts,
  style-grammar §2): beat-cut-moves, rhythm-interrupt-moves, trailer-grammar-moves, panel-grid-moves,
  quad-split-parallel-scenes, beat-step-list-theme-cycle, sakuga-timing-shift, speed-ramp-freeze, impact-feedback,
  type-rhythm-sync, glitch-cycle, tear-streak-transitions, deck-deal-flyin.
- **Type entrances** (treatments and builds: graphic-design §1–§2):
  - the default word reveal: blur-slide;
  - lines and labels: lead-word-zoom-assemble, type-assembly-moves, type-entrance-moves, paper-title-card,
    marker-underline-title, gradient-word-sweep, brace-expand, outline-word-fill, title-demote-to-label,
    countdown-arc-scatter;
  - one slot cycling: beat-step-list-theme-cycle, glitch-cycle, pill-slot-cycle, pill-chip-slot-cycle-handled,
    vertical-word-roll-blur-cycle, word-relay-filmstrip, word-relay-geometry, text-column-converge;
  - typed: typewriter-moves, hashtag-to-pill-materialize, type-and-filter, glass-pill-dictation-typing,
    document-typewriter-reveal;
  - on the beat: type-rhythm-sync;
  - in 3D, as a mask or as a backdrop: assemble-then-type-flyin, text-as-mask, stroke-segment-build,
    letterspace-materialize, brand-ink-open, grain-dissolve, flying-words.
- **Camera moves** (2D zoom/pan/multiplane/depth-push moves; style-grammar §6c–§6d): crash-zoom-punch, depth-layer-moves,
  graze-face-tour, tension-camera-moves, space-camera-moves, overhead-camera-moves, basic-3d-scene, steep-tilt-glide,
  terminal-3d, cursor-flyover, crane-rise-reveal, timeline-travel, transition-travel, dataviz-landscape-open,
  rhythm-interrupt-moves.
- **Impacts and accents** (one shake source per shot; the effects budget, house-style §6; each with its sound,
  house-style §1): crash-zoom-punch, slam-entrance-moves, impact-feedback, fui-hud-moves, outline-word-fill,
  transition-hidden-cut (versus-slam), beat-cut-moves, brand-frame-snap, riso-print-hits, tear-streak-transitions,
  icon-performance-moves, marker-underline-title, gradient-word-sweep, light-play-moves (sheen),
  chip-grid-single-select-blackout.
- **Outros and credits** (the ending and the credits card, house-style §10): outro-group-photo-launch, grain-dissolve,
  ui-to-brand-morph, neon-triple-marquee, logo-shrink-wordmark-lockup, ui-strip-away-outro, tension-camera-moves
  (pull-back).

By subject:
- **Contenders side by side: dealt, compared, the champion picked**: deck-deal-flyin, card-stack,
  avatar-bracket-carousel, chip-grid-single-select-blackout, picker-carousel-feature-cycle, spotlight-hero-card,
  element-body-moves, overhead-camera-moves (tabletop), card-flip-reveal, mosaic-reframe, before-after-slider-scrub,
  quad-split-parallel-scenes, transition-hidden-cut (versus-slam), list-reveal, list-stack-press,
  value-stagger-gradient, ui-strip-away-outro.
- **A model's anatomy, family or lineage, as images**: space-camera-moves, canvas-materialize-moves, cloner-depth-echo,
  timeline-travel, dataviz-landscape-open, bezier-source-converge-merge, integration-hub-map, voice-waveform-live,
  autolayout-gap-dial.
- **Backdrops, loops and calm beats**: gradient-transition, flying-words, carousel-3d, page-waterfall-wall,
  glow-flyline-moves, radial-ripple-phone-chips, glass-pill-dictation-typing, research-card-stack-scroll, radial-wave,
  voice-waveform-live.
- **Her painted shots**: depth-layer-moves, sakuga-timing-shift, panel-grid-moves, scanline-annotate-focus,
  crash-zoom-punch, text-as-mask.
- **Paper and print**: riso-print-hits, print-texture-transitions, paper-title-card.
- **Data** (for a section card or a chronicle form's history only; never a score in an intro, house-style §2):
  scroll-brake-moves, gauge-readout-moves, chart-live-moves, timeline-travel, before-after-slider-scrub.
- **★ fast-cut** (15): crash-zoom-punch, beat-cut-moves, trailer-grammar-moves, sakuga-timing-shift, panel-grid-moves,
  shot-transitions, transition-hidden-cut, white-flash-logo-simplify-cut, title-demote-to-label, text-as-mask,
  type-rhythm-sync, glitch-cycle, fui-hud-moves, countdown-arc-scatter, impact-feedback.
- **(UI-specific)**, product-UI cards: terminal-3d, cursor-flyover, radial-ripple-phone-chips, segmented-thumb-hero,
  collab-cursor-moves, document-typewriter-reveal, ui-strip-away-outro, doc-park-left-pill-deal.

## Camera (运镜)
- **crash-zoom-punch** ★ fast-cut — a one-beat crash push from wide to close-up.
  Key: 5f pull-back 3–4%, 5f ease-in zoom (1→2.6); land springy (back 3–6% in 4f) or heavy (no bounce, shake
  14px·e^(−t/1.4f)), never both; blur the push only; target fills 60–75%; >8f is a plain push.
  Use: onto the #1 bar or her eyes; ≤2 per film.
- **depth-layer-moves** — multiplane parallax slide.
  Key: one drive × 0.35 (blur 5px, desaturate, haze) / 0.7 (sharp) / 1.4 (blur 7px) + a pinned 0x title; ≥2× between
  layers, ≤4 layers; ~104f bezier(0.45,0,0.18,1) ending on the hero, which lifts 1.035 ~6f later; never blur a
  full-frame layer (3× render).
  Use: SAM-cut painted intros.
- **graze-face-tour** — a grazing camera skims a surface; hovering pieces drop onto it.
  Key: hover 120–180px with a same-shape soft shadow that tightens and vanishes on landing (the shadow sells it);
  gravity fall, soft land; landings staggered along travel but overlapping; far blur; crossfade relays ≥6f.
  Use: labels landing on the HUD.
- **tension-camera-moves** — small moves, heavy feeling.
  Key: (bullet-time) content on a remapped clock (6f brake, 42f freeze, 6f resume) while the camera orbits rotateY
  0→−52° and back, depth cues required; (pull-back) scale 2.2→0.62 over 88f out-cubic, siblings die by distance every
  6f, the survivor glows.
  Use: #1 bar mid-growth; the last shot.
- **space-camera-moves** — the page as a solid.
  Key: (exploded) axonometric rotateX 54° rotateZ −34°, 5 layers to translateZ 150–640 on spring(15, 120) 4f apart,
  merge with an 8px sink; (drone-dive) one progress for rotateX 72→0 + scale 0.42→1.35: 20f in-cubic for 82% of travel,
  16f cushion.
  Use: a model's anatomy; board → contender.
- **overhead-camera-moves** — pitch tells the story.
  Key: (tilt-reveal) surface hinged at its bottom, rotateX 86°→−2.2° (f48)→0 (f56), perspective 700→1500 and scale
  2.5→0.84 on one progress; (tabletop) cards at rotateX 62°, pan x only, a 6f "chosen" beat, then angle, scale and x
  dive together in 22f.
  Use: the HUD standing up; picking one card.
- **basic-3d-scene** — posed cards in 3D; the camera is each pose inverted (rotations in reverse order).
  Key: flights 22–26f bezier(0.62,0,0.16,1) with a 30% pull-out, dwell ≥24f, defocused cards ≥0.22.
  Use: touring HUD panels as places.
- **steep-tilt-glide** — locked camera; a 60° wall (55–65°) slides past.
  Key: perspective 1100, only local x moves, never parking; 3 ghosts 1.3/2.6/3.8f back, opacity ∝ speed.
  Use: a stat strip gliding by.
- **terminal-3d** / **cursor-flyover** (UI-specific) — windows toured station to station.
  Key: a mid-flight pull-out bulge, 8–10° side view at rest, typing 0.6–1.3f/char, a pointer leading the camera by 2f.
  Use: a typed prompt.

## Data (数据)
(for a section card or a chronicle form's history only; never a score in an intro, house-style §2)
- **scroll-brake-moves** — a long list blurs past and brakes on one row.
  Key: ~2400px in 40f cubic-bezier(.45,0,.06,1); blur = |Δy|×0.32 ≤30px; row heights 72/94/116; target dead centre,
  lifts 1.03 + 2px accent, others 0.38; variant: +30px overshoot with four L brackets biting on the exact stop frame.
  Use: rank 50 → TOP 3.
- **gauge-readout-moves** — a reading as a body movement.
  Key: (self-test) the needle flings the full 270° in 10f, swept ticks light, springs back to the true value with ~8°
  overshoot, gauges 3f apart; (fixed pointer) a tape scrolls behind it, the limit line snaps, 18f sprint ~125px/f,
  spring brake; ≥24f locked.
  Use: HUD power-on; a metric leap.
- **chart-live-moves** — the chart is the plot.
  Key: (scope) write head pinned right, ~10px/f, one 2.2× spike; (dot swarm) 320 dots on spring(150, 13) 6f apart,
  stretched by speed, ending as a number; (axis shock) the value breaks 226px past the ceiling, a half-beat, the axis
  relabels with a 10px shake; once each.
  Use: a score off the chart.
- **timeline-travel** — sprint along a time axis, brake on "now".
  Key: remap [0,0.15,0.88,1]→[0,0.055,0.9,1]; cards spring up 5f before the camera; brake, push 1→1.28 in 8f, ≥24f
  still.
  Use: a release history.
- **before-after-slider-scrub** — fling the split, then sweep slowly.
  Key: 8→76% in 10f out-cubic, back to 70%, 14f pause, 70→40% over 38f; fling:sweep ≈1:5; edge glued to the bar.
  Use: old vs new, A vs B.

## Effects (特效)
- **scanline-assemble-flyin** — a scan line passes a blueprint and each piece flies in to meet it.
  Key: slots visible from frame 1; zero-easing line (~67f); each lands the frame the line crosses its bottom edge, ≥3f
  apart, launching 11f early from 260–980px off with ~8% overshoot and speed blur ≤18px; L corners bite in.
  Use: the HUD building itself.
- **scanline-annotate-focus** — a scan passes a finished frame; each region it clears is bracketed and named.
  Key: zero-easing line; trigger on the region's bottom edge, ≥3f apart; corners spring(15, 210) in from 76px; label at
  +4f, typed ~2.75 chars/f; a live counter; machine colour ≠ subject colour.
  Use: tags on her portrait.
- **slam-entrance-moves** — the entrance is the impact.
  Key: (kanada) x −1350→0 in 14f while perspective, rotate3d 62° and scale 1.8 settle later, +6° overshoot; (score-slam)
  hover 7f, slam 5f ease-in, one frame of ring 120→1500px, shards, 18px shake, 2f flash, digits 2f later; (burst)
  neighbours pushed 34px by the wave.
  Use: score slams.
- **impact-feedback** ★ fast-cut — a hit that bites time.
  Key: (combo) hits every ~22f, each freezing every layer 2f on one remapped clock, damage numbers and counter growing
  each hit (88/104/124px); (anime frame) 2–3f invert + grayscale + contrast 1.45, speed lines, ±8px red/cyan negatives,
  then a 6px shake.
  Use: wins in a row; the #1 hit.
- **fui-hud-moves** ★ fast-cut — reticle lock-on without freezing.
  Key: four mirrored L corners fly ≥1000px in 8f out-cubic, size separate (2.2×→0.94×→1); lock frame: white overlay
  0.55→0.28 and label pop together; mechanical click; ≤2 per film.
  Use: lock onto a subject, lyric word, or focal UI marker.
- **light-play-moves** — light as a brush, dark grounds only.
  Key: (spotlight) a 0.07 dark copy + a lit copy under a radial mask riding a 360px spot on a damped pendulum (40f
  period, position and speed hit zero together), then an iris to 1080px in 16f; (sheen) one 115° band (0.14 + 0.5 core)
  in 26f as the card turns.
  Use: name reveal; champion card.
- **glow-flyline-moves** — dark-field orbs and glowing link arcs.
  Key: three 760–1200px screen gradients drifting on unequal periods, easing to a stop; glass cards at backdrop blur
  44px; arcs grow 18f out-cubic with a white head and comet tail, 3.5px core + 7/18px glow, butt caps; ≥3 links → orbs
  surge on landing.
  Use: callout → subject links.
- **assemble-then-type-flyin** — empty frames assemble in 2D, then the text flies in in 3D.
  Key: 10 blank pieces every 3–4f, 13f overshoot; 6f breath; glyphs seeded dx ±260 dy ±200 dz −200…−760 with ±120–190°
  spins, perspective(900px) each, 13f snappy, headline first, labels last.
  Use: a complex HUD/layout assembling.
- **scan-bracket-sweep** — a still object read by a light band.
  Key: 34px L brackets stagger in; band = 1.2px core + 10px glow + a ≤82px trail sized by speed and flipping with
  direction; 5 inOutSine passes with rests.
  Use: the HUD analysing a card.
- **riso-print-hits** — print-ink glitch: two plates misregister and snap true.
  Key: pink #ff4fa3 + blue #1f5fc4 multiplied, offset A·cos(2πt/14)·e^(−t/48), A=(20,8)px, hard snap at ~11px.
  Use: paper or zine intros.
- **aurora-bloom-bg-flip** — glow blooms on light, then the ground drops to near-black in ~9f.
  Key: three blur(60px) blobs rise; #ececec→#0a0a12, blobs to 0.4; ~0.6s textless gap between lines.
  Use: "then everything changed".
- **spotlight-sweep-moves** — on black, light is the edit.
  Key: the sweep eased on a library curve (`T3.EZ`), or constant speed only as a declared `motion-ok: scan` on the light bar (motion-library «How to use»); ~15% feathered reveal; a glowing line hugs the subject's edge; a corner reveal covers the
  frame exactly at the end.
  Use: HUD tiles waking.
- **brand-frame-snap** — a thick colour frame grows before the content and codes the chapter.
  Key: 60px bands in 15f; a switch flips colour, layout and label on one frame with a 3f flash.
  Use: lab brand colours.
- **icon-performance-moves** — an icon bounces for attention.
  Key: 4 hops rising to 1.2× its height, airtime ∝ √height, 2f squash, neighbours blur, camera pushes 8% on the top hop.
  Use: a lab mascot.
- **radial-ripple-phone-chips** (UI-specific) — slow life around a still object.
  Key: 4 discs breathing 1±0.06, 1.7 rad out of phase; chips pop on spring(13, 190) ~24f apart.
  Use: a calm hero still.

## Interaction (交互)
- **hashtag-to-pill-materialize** — two hard cuts around one slide.
  Key: a word typed 3–5f/char with a solid cursor; one-frame cut to an oversized pill in place (3f 1.03→1 only); ~14f
  hold; scale ~0.55 and move into its slot in 11f on one bezier(0.5,0,0.25,1), origin 0 0; a second one-frame cut
  reveals the layout.
  Use: name → tag → HUD slot.
- **theme-switch-moves** — the same frame changes skin.
  Key: (sweep) a 15° boundary from the switch side over ~51f, computed 400px past the frame, the camera pulling wide;
  (ripple) a panel collapses CRT-style to a point, holds 4f, a circular clip opens to ≈1.1× the farthest corner with an
  echo ring; layouts identical.
  Use: daylight intro → dark HUD.
- **canvas-materialize-moves** — content leaves its container as something new.
  Key: rows lift, arc out 5f apart, swap content strictly after mid-flight; a tree's connectors draw 8f before each
  node, layers 18f apart.
  Use: a model family tree.
- **type-and-filter** — type, the grid converges, click through.
  Key: ~2.4f/char (drafts run fast), ~9f breath, non-targets sink 8px 0.3f apart, target to a real slot, 13f push with a
  flash over the cut.
  Use: search a name.
- **voice-waveform-live** — a waveform holds a shot on vitality.
  Key: bar i samples f−(N−1−i)·1.3f so history scrolls; envelope × syllable noise × centre weight; silence = 6px dots.
  Use: an audio model.
- **picker-carousel-feature-cycle** — a fixed focus pill; the list snaps through it.
  Key: outQuint then truly still for 5/14 of each step; opacity 1→0.55→0.18 by distance; odd rows.
  Use: cycling categories.
- **chip-grid-single-select-blackout** — press, confirm, the rest stay put.
  Key: one grey press frame, then the chip colours go to ink over 4 f, a colour fade on `curve.house` `snap` (it changes no position); others to 18%, never moving or reflowing.
  Use: the winner chosen from chips.
- **autolayout-gap-dial** — one number drives the layout in lockstep.
  Key: all geometry and the readout from one value on one frame; spring(9, 80) home; exaggerate amplitudes 4–5×.
  Use: synced bars and gauges from one driver.
- **glass-pill-dictation-typing** — the quietest beat: glow yields to text.
  Key: fixed-width frosted pill 1.25→1 in 16f; ~1.6f/char; one value dims all glow over the typing.
  Use: a rest beat.
- **segmented-thumb-hero** / **collab-cursor-moves** (UI-specific) — toggles and cursors as actors.
  Key: a 6f out-cubic thumb slide as the heartbeat; cursors on two sines, never still.
  Use: a binary reveal.

## Opening (开场)
- **crane-rise-reveal** — start tight on one row, crane back until the board fills the frame.
  Key: ≥16f at 3.0 with a 1.5% inhale; aim point and scale 3.0→1.0 on one bezier(0.2,0,0.25,1) over ~82f; other rows 38%
  → full; each row washes accent as the view's top edge crosses it; a KPI counts with the move.
  Use: key badge → main feature card.
- **text-as-mask** ★ fast-cut — a huge word is a window onto imagery, then bursts open.
  Key: 470px weight-900 letters; saturated imagery drifts inside ~4.8px/f; 6f inhale to 0.965; 19f plunge to 46× in log
  space (t^1.8), origin inside a solid stroke; content counter-scaled; full-frame copy only once covered.
  Use: her name opening onto her art.
- **stroke-segment-build** — a known word lit as disjoint neon strokes, legible only at the end.
  Key: ~16 segments for 4 letters, starts 7f→2.4f apart, each a 6f flicker to 0.58; an 11f breath; the 3 key strokes
  last; reveal surges 1.25 and lights the wall.
  Use: a model name or number as the hook.
- **magician-card-flourish** — a blue star-flash, then a card spins out and freezes dead.
  Key: ~7f X of needle beams rotating 90° (no white ball); card from scale 0.11 via F/(F+z), slow-in, kick, out-cubic
  arc; 13 whole turns decaying so it freezes face-on at 86% frame height; no bounce.
  Use: a character card conjured in.
- **orbit-ring-title-open** — eight cards orbit a flat ellipse behind the title.
  Key: RX 720 / RY 380, 0.3 rad/s (≤0.5), cards never rotate; depth = sin θ drives scale ±12%, z-index and blur ≤1.6px;
  contents frozen until the ring opens; title glyphs blur-slide; a marker sweep inverts the key word.
  Use: contenders circling the title.
- **fracture** — a 5×5 tile poster assembles from 3D chaos, holds, blows apart.
  Key: seeded starts ±450/±300px, ±180°; ripple delay 0.045 of the clip per ring, 0.34 each on bezier(0.42,0,0.3,1),
  ≤2.5° wobble; opacity min(1, 2.5t); exit 620–880px outward, ±150° spin, never a fade.
  Use: a title card on a drop.
- **icon-field-colorize** — a grey field of icons, then colour waves light it.
  Key: ~170 icons arriving centre-out in 10 batches ~3.5f apart; a 14f rest dimming 12% at its end; waves ~1.1f per row
  with tilt and jitter; each icon clip-floods in 3f with a 1.22× pop and a 4f flash; one hue family.
  Use: every lab icon lighting up.
- **spotlight-hero-card** — a dark theatre; a tungsten spot finds one card and lifts it.
  Key: page at 6–10%; the pool visits 3 stops, locks with +6%, then becomes a card-shaped soft hole lit edge to edge;
  camera 0.8→2.6 in 14f, then locked; rise 8f, hover 46f, reseat 14f; an outline beam laps twice.
  Use: the champion under the spot.
- **dataviz-landscape-open** — tributary lines flowing into one trunk, flown over.
  Key: pinhole projection on a ground plane, 8–14 tributaries, one trunk, near blur, far fog, ID tags on short posts.
  Use: multiple visual cards flowing into one focal frame.
- **brand-ink-open** — letterpressed wordmark, then a full second still.
  Key: glyph i at 8+2.4i f, scale 1.6→1 + blur 6px→0 + fade; hold 24f; exit 6f, faster than entry.
  Use: a lab name stamp.
- **letterspace-materialize** — every stroke of a wide-tracked wordmark grows at once.
  Key: single-line glyphs on one shared ~40f progress, all start and end together, tracking ~0.6em.
  Use: a title over a dusk plate.

## Outro (收尾)
- **outro-group-photo-launch** — every featured element flies back around the wordmark, launch-event scale.
  Key: 9 cued ~2.4f apart, 10f flights from ±360–500px on bezier(0.34,1.4,0.44,1), settling within ±5°; others −12% as
  the wordmark presses in; crane rotateX 4°→0 + 1.06→1; ≤30 gold motes; ≥24f.
  Use: emblems round the channel logo.
- **grain-dissolve** — a sentence boils into grain and condenses into one glowing word.
  Key: feTurbulence (0.9→1.3) + displacement 0→52 + blur ≤1.1px on one burst curve; reseed ≥20×/s; swap the text at peak
  boil (60–71%); lock to 0 by 90%; bloom 0.3→0.7→0.45; ~48f.
  Use: a sentence condensing into the #1's name.
- **ui-to-brand-morph** — a UI element turns into the mark.
  Key: (flip) growing wobbles, ease-in scaleX 1→0.04 in 10f with ghosts, swap on the thinnest frame, spring(11, 130)
  open, glyphs 2.1f apart 1.9→1 + blur 14→0; (morph) colour floods by circular clip, x/y/w/h/r on one spring, pieces
  drop into dashed slots.
  Use: emblem → rank number.
- **neon-triple-marquee** — three neon rows scroll opposite ways and light in turn.
  Key: ~11/14/11px/f, middle reversed; one row lit per 11f slot with 2f overlap; unlit glass at 0.3; glows 9/36/90px +
  wall spill.
  Use: a TOP 3 recap.
- **logo-shrink-wordmark-lockup** — a frame-filling ring collapses into the mark.
  Key: 5.4→1 over ~26f with a 6% brake; swap to the logo on the brake frame (it never spins); letters slide in.
  Use: the channel sign-off.
- **ui-strip-away-outro** (UI-specific) — layers evaporate edges-in, one survivor.
  Key: a layer every 3f, 11f ease-in with outward drift and blur; the survivor centres ×1.5.
  Use: all but the champion evaporate.

## Rhythm (节奏)
- **beat-cut-moves** ★ fast-cut — paparazzi flash: three flashes, each a hard cut to a tighter crop of one image.
  Key: crops 1.0→1.6→2.8 at f24/42/56 on the beats; flash 0.95→0 in 3f with ±2px jitter; each view settles 1.03→1 and
  −16px in 5f; a focus box lands on the next crop 6f early; ≥56f hold; zero blend frames; once per film.
  Use: crowning #1.
- **sakuga-timing-shift** ★ fast-cut — limited animation, then a fluid burst.
  Key: drive with ⌊f/3⌋·3 (or on 2s), steps ≥30px with a new pose each (±5°, squash, hops); switch on one frame with 2
  inverted impact frames, then per-frame out(poly4) sprint, 40px overshoot, landing squash 0.92/1.07; label the switch;
  stepped moves of hers only where a remade original steps (style-grammar §6e).
  Use: anime-style painted intros.
- **speed-ramp-freeze** — flow, stop dead, annotate, thaw.
  Key: time-remap slope 1 → 0 instantly → smootherstep thaw with mean slope >1; blur from remapped speed; the freeze
  frame flashes 2–3f, corners snap, LIVE→PAUSED; marker loop in 8f; freeze ≥36f; ≤2 per 30s.
  Use: freeze the scroll, circle a score (where data may appear: «Data (数据)» above).
- **panel-grid-moves** ★ fast-cut — comic split: three angles of one subject cut in on the beat.
  Key: three 12° gutters (ink + cream core) every 3f, each panel hard-cut in 1.07→1 with a flash; full / detail / macro
  of the same subject kept alive by its own motion; the last panel sweeps the frame in 11f.
  Use: her figure, face, weapon.
- **beat-step-list-theme-cycle** — list step, lens colour and ground colour on one beat.
  Key: ~14f beat, jump in the first 5f, still after; a fixed capsule lens; grounds same value, new hue.
  Use: adjectives on the beat.
- **quad-split-parallel-scenes** — four micro-scenes at once.
  Key: heavy events 2–5f apart, never two on one frame; ~50f of it, then a 22f hold; biggest beat on the accent.
  Use: four contenders on a chorus.
- **rhythm-interrupt-moves** — jump-cut punch-in.
  Key: same framing, 1.0→1.6→2.6 with zero tween, each ≥28f, a 2f 0.92 brightness dip per jump; steps <1.5× read as a
  shake.
  Use: three beats into a score (where data may appear: «Data (数据)» above).
- **trailer-grammar-moves** ★ fast-cut — cold-open bumper.
  Key: three equal 7f hard cuts, each pushing 1→1.04; 5f of pure black and silence; then the title.
  Use: a TOP 3 hook before the title.

## Transition (转场)
- **circle-match-iris** — the iris opens from a real circle; the next scene's ring sits on it.
  Key: one centre constant for all; focus first (others to 32%), 6f pre-shrink; the ring starts with stroke = diameter,
  then r 36→300 in 22f; iris = ring edge + 0→2400px over 24f; old scene 1.03→1.22, darkening; >10px off reads.
  Use: portrait → score ring.
- **white-flash-logo-simplify-cut** ★ fast-cut — a glossy show version burns to white and comes back flat.
  Key: iridescent clipped text, one highlight pass; ~10f build (brightness ×1.7, flare); a white burst from the word's
  centre in ~5f, ~3f pure white, swap on full white; white recedes ~18f quint-out over the flat version.
  Use: painted name → HUD label.
- **shot-transitions** ★ fast-cut — the three hand-off seams.
  Key: (flash-cut) a push into a white flash ±4f over the cut; (whip) one continuous velocity curve, 70% of distance in
  30% of time, peak ≥375px/f, ~38f tail, blur ≈0.085×v; (portal) a lifted card grows over 32f while the scene inside
  counter-scales 0.42→1, two layers.
  Use: card → its intro.
- **transition-hidden-cut** ★ fast-cut — hide the cut inside 1–3 frames of something bigger.
  Key: (foreground wipe) a defocused 2600px core crosses in 11f, cut where it covers all; (versus-slam) halves on a ~78°
  seam slam from ±1240px in 8f, flash + 16px shake + VS stamp on one frame; (light leak) t² up 22f, cut on the peak.
  Use: model A vs model B.
- **card-flip-reveal** — flip a card to its result.
  Key: perspective 1600, back pre-rotated; 3f lean −10°, 13f bezier(0.55,0,0.3,1) to 194°, spring(15) to 180°, lifted
  60px; shading (1−|cos θ|) and an edge light peaking at 90°; back = a 150–170px number; cards 10f apart, ≤4.
  Use: contender cards → scores.
- **line-carry-transition** — no cut: a line carries the eye on.
  Key: a finished bar extends out; the world pans 1920px in ~45f while the drawn length tracks the camera, the tip held
  at x≈1480; right-angle corners trace the next frame, content after it closes; peak ≤100px/f; once per film.
  Use: a HUD bar into the next intro.
- **card-flock-tumble** — cards tumble into a stair, keep turning, get sucked in, burst into a word.
  Key: one spline per card, ~0.43°/f idle spin, 8f ease-in suck, hot core, one smoke ring, word 1.22→1 in 11f; no blur.
  Use: TOP 3 → the name.
- **mosaic-reframe** — the same tiles re-lay grid → mosaic → cascade.
  Key: centre, size and rotation lerped separately (size 2f, rotation 3f late), bezier(0.75,0,0.15,1), staggers 8–11f.
  Use: grid → podium.
- **bottom-push-stack-wipe** — each chapter shoves the last one up and out.
  Key: both on cubic-bezier(0.12,0.9,0.2,1) over 21f, a 56px seam shadow, saturated grounds, one direction.
  Use: #3 → #2 → #1.
- **transition-travel** — fly through a giant title's letter hole.
  Key: origin in a central stem's hole, scale 30^u over ~42f after a 2% pull-back, light only in the hole until
  mid-push.
  Use: "TOP 3" as the door.
- **wipe-transitions** — 3D blinds.
  Key: 12 slats of 160px, old front / new back, slat i at 19+22·(i/11)^0.78 on spring(13, 75); the dark slot is the
  edge.
  Use: next category.
- **page-turn-transitions** — barn doors.
  Key: a glowing seam opens 16px, halves slide ∓1000px in 19f accelerating, the new page rises 1.08→1.
  Use: an old champion making way.
- **print-texture-transitions** — ink bleed.
  Key: a turbulence-displaced circle grows 0→1450px with ±8% wobble and ink-edge rings; drop the mask once full.
  Use: paper intros.
- **tear-streak-transitions** — strip glitch.
  Key: 16 strips ±70px by hash, two-colour silhouettes, the cut hidden in the full shake; strips, never blocks.
  Use: a "goes live" jump.
- **gradient-transition** — a living linear / radial / conic backdrop.
  Key: 10–11f crossfades while both move; HSL lerps; paint at 480×270, scale(4) for cheap blur.
  Use: title and HUD backdrops.

## Typography (文字)
- **countdown-arc-scatter** ★ fast-cut — a dial of numbers sweeps; the hero number flies off to start the title.
  Key: 9 equal 112px digits tangent on an R 700 arc, a non-uniform sequence; 4f wind-up, spring(12, 60) 99°→0°; opacity
  by angle; the hero lifts 2f before settling, 16f into a fixed 0.6em slot; the rest blur out in place.
  Use: rank dial → "#1 <name>".
- **lead-word-zoom-assemble** — one word fills the frame, the sentence assembles round it.
  Key: lead word 2.3× pushing 6% over a 10f hold, then shrinking in 10f while the line slides 19f, both on
  cubic-bezier(.5,0,.05,1); origin = lead centre + baseline; next words pushed from +0.5em, 3f apart, 2f fade.
  Use: "Introducing <name>".
- **title-demote-to-label** ★ fast-cut — the big title steps down into the section label.
  Key: hold ≥14f, then one 21f bezier(0.6,0,0.18,1) does scale 1→0.22 and the move to (216,196) together, origin
  left-centre; content starts growing 10f into the move; old labels move up and grey; ≤3 words.
  Use: her name → dashboard title slot.
- **outline-word-fill** — a hollow word slams down, is aimed at, lights in one frame.
  Key: 220px weight-500 outline 3.2→1 in 9f; a dashed circle closes 2.8→1 over 35f (slow against fast); stroke pre-heats
  ~7f; fill = a one-frame switch with a 6f glow and one shock ring; a hit on that frame.
  Use: "FASTEST" or a score.
- **glitch-cycle** ★ fast-cut — one slot cycles status phrases through noise.
  Key: fixed mono slots; g per phrase from [1,0,0,0.1,0,0,1] (last ends at 0); swap a char if rand < g, reseeded every
  2f; the same g drives ±36g/±10g px jitter, a 10g px RGB split and tear bands; ≥27f per phrase; dark.
  Use: LOADING → RANKED.
- **blur-slide** — the default word reveal from soft focus.
  Key: one quint-out p per word drives opacity, y (1−p)·dy and blur (1−p)·B; title 3f apart, 18f, 64px, 18px blur;
  subtitle 2f, 16f, 26px, 9px, starting before the title ends; by words.
  Use: every secondary title.
- **pill-slot-cycle** / **pill-chip-slot-cycle-handled** / **vertical-word-roll-blur-cycle** — one rolling slot.
  Key: stem anchored left; a beat every 17–26f, the swap in its first 6–14f, then still; in y 120→0 + blur + rotateX
  −38°→0, out up, ease-in; or a width-adaptive chip, or a blurred reel coloured once settled.
  Use: "Best at [coding]".
- **type-rhythm-sync** ★ fast-cut — letters stay put; properties ride the sound.
  Key: (weight pump) 250+650·(1−t/D)^0.8 per kick, D 7–10f, glyphs in slots sized at weight 900, beat gap > decay;
  (karaoke) each word filled on its own [start,end] with a ±4% soft edge, ≤6 words.
  Use: the title on the drop; lyrics.
- **type-assembly-moves** — the title gathers from elsewhere.
  Key: (split rise) glyphs 115%→0 in 11f, 10% overshoot, 1.6f apart; (drift) seeded ±260–360px + blur 8px + ±24° on one
  out-cubic p, 36f each; (on-path) the string rides a curve's arc length, then lifts glyph by glyph.
  Use: the name riding a score curve.
- **typewriter-moves** — type a plain word, hesitate, delete, type the real one faster.
  Key: 1.6f/char, 13f pause with two blinks, delete and retype at 1.2f/char; cursor solid while typing.
  Use: "the best is… [delete]".
- **text-column-converge** — two words pinned apart, one side cycling, then one closing slide.
  Key: equal margins, hard cuts with 6–13f holds, zero creep; one 29f ease-in-out slide.
  Use: "#1 × [benchmarks] → #1".
- **word-relay-geometry** — three benefit words, each with its own geometry.
  Key: ~48f each, out faster than in; outline then fill; only the last word gets the chrome upgrade.
  Use: three adjectives, the third the verdict.
- **word-relay-filmstrip** — an evidence column steps once per word change.
  Key: one 14f card step per change, else still; the word block centred on the focus card to the pixel.
  Use: "<name> codes / reasons".
- **flying-words** — a looping keyword tunnel as background.
  Key: z −7000→+3200 at perspective 4400 so words pass the lens; opacity life [0,1,0.5,0.2,0]; integer cycles.
  Use: model names behind the title.
- **gradient-word-sweep** — one selling word charged by a fast sweep.
  Key: gradient copy revealed in 12–16f, a bright band ~34% wide on the front, steady glow ≤0.72, sparse arcs.
  Use: "OPEN" in a tagline.
- **paper-title-card** — a one-line card pressed onto paper.
  Key: words 3.2f apart, scale 1.28→1 + blur 7px→0, one accent word, an underline closing it, 40–44f.
  Use: breath cards between contenders.
- **brace-expand** — brackets spring apart to reveal a title.
  Key: touching braces at 0.4 open on spring(14, 130), the text clip glued to the gap.
  Use: a HUD "[ name ]".
- **marker-underline-title** — a hand-marker stroke under one word.
  Key: 8f, 3–6f after the title lands; variable width, rough edge, rising with the italic.
  Use: the winning metric.
- **type-entrance-moves** — letters fall, bounce, land crooked, then stand up together.
  Key: bounces 30% / 9%, ±6° tilt, one 5f joint straightening.
  Use: a comic contender.
- **document-typewriter-reveal** (UI-specific) — a document writes itself.
  Key: one caret only; budget blocks × beat first.
  Use: a spec sheet.

## UI entrance (界面入场)
- **deck-deal-flyin** — a pile is dealt into a grid at a hard-accelerating rhythm.
  Key: one big anticipation (pile presses 48px, top card pulls 30px; small values are invisible); gaps 3.2f → ~0.2f;
  each card 6f bezier(0.3,0,0.2,1) on a 110px z arc, 3f overshoot settle, 2f press; camera chases.
  Use: dealing contenders onto the board.
- **wall-reveal-moves** — a wall appears in place, no travel.
  Key: (bento) dark cells at 0.18 wake one per 10f (even = solemn), a comet stroke tracing each outline in 6f, content
  popping from halfway; (blueprint) line groups draw 24f each, then a 4px accent scan reveals the real panel by clip in
  24f.
  Use: dashboard cells waking.
- **neon-frame-forerun** / **neon-frame-orbit-drop** — the frame arrives first, content is set into it.
  Key: two white-hot heads race the outline in 16f (4 stroke layers, no blur); the page brightens inside; pieces hover
  120–170px with same-shape shadows and drop in 19f; staggered = tour, one-frame landing = entrance.
  Use: the HUD's entrance ceremony.
- **row-embed** — rows drop into slots with a lit seam.
  Key: gaps 8→6f; 10f flights of translateY −120·air + rotateX 16°·air on bezier(.5,0,.8,.75), a 3f press; dashed slots
  until landing; a 2px accent seam opens centre-out in 4f and fades; the camera drifts down.
  Use: leaderboard rows into the table.
- **product-card-progressive-assemble** — a card fills field by field behind a fill cursor.
  Key: the cursor box jumps in 5f, each field lands 2f after; 2–3f within groups, 8–16f between; big items rise, small
  ones pop on spring(13); the old value shrinks, greys and is struck in 5f, the new one springs 1.18→1.
  Use: a stat card filling.
- **card-stack** — cards spring into a pile, then fan like a hand.
  Key: 9 cards (odd) from +820px on spring(13, 150), gaps shrinking, 5px press per landing; fan on spring(20, 95) at
  k·6.5° and k·138px, origin 50% 130%; the centre card slides out 72px.
  Use: the champion drawn from the hand.
- **avatar-bracket-carousel** — portraits roll through a fixed bracket.
  Key: d = |k−pos| drives scale 1−0.38d, opacity 1−0.62d, blur 2.4d, y 76d; labels fade 2.2d; the bracket breathes 7%.
  Use: "Today's #1: [portrait]".
- **list-reveal** — rows find their place while the whole list drifts.
  Key: every 8f, 19f each, 0.82→1 + 44px + blur 8→0, ~1.5% soft back; a 96px drift underneath, a library settle or `T3.EZ` drift (a hand-built one needs its reason in the motion sheet).
  Use: ranking rows.
- **value-stagger-gradient** — stagger the values, not only the times.
  Key: by index lerp hue, height, travel and blur; then a centre-out pulse, amplitude 0.06→0.42 toward the middle.
  Use: bars with a #1 pulse.
- **cloner-depth-echo** — one card prints 7 receding clones, then they snap back.
  Key: vanishing point in a corner, z −250i, opacity → 28%; spawn 1.8f apart, return together in 8f.
  Use: a model family's sizes.
- **bezier-source-converge-merge** — sources ride curves into one hub and are swallowed.
  Key: real paths; shrink 44→15px, then 15→0 in the last 25%; integer packet loops.
  Use: feeds → one board.
- **draw-svg-trace** — a pen traces an outline, a dark flash closes it, content fills.
  Key: pathLength 1 over ~32f, a tapered pen head, matching corner radius, one subject.
  Use: trace a card first.
- **element-body-moves** — contact-shadow lift.
  Key: the shadow stays on the table as two layers that grow, blur and fade as the card rises; ≥12px visible lift; 6f
  landing + press.
  Use: lifting the chosen card.
- **list-stack-press** — cards stack from below; each landing presses the pile.
  Key: every 10f, 18f flights, a 6px press over 6f; an odometer counter with one continuous position.
  Use: wins piling up.
- **research-card-stack-scroll** — a card per 10f onto a sinking pile.
  Key: 5f arrivals, 30px drift per beat, depth blur ≤4px, a grid moving at the pile's speed.
  Use: "10,000 prompts".
- **radial-wave** — a dot grid powers on in a wave.
  Key: start 0.35·distance, scale w·(1+0.5·sin wπ), base opacity 0.25, a reverse glowing pulse.
  Use: the HUD grid booting.
- **integration-hub-map** — a full flip, then everything plugs in at once.
  Key: 180° in 28f out-cubic, no pause; all icons on one frame, all pipes 8f later.
  Use: a new season's board.
- **carousel-3d** — a stepped ring of cards for loops.
  Key: rotateY(i·45°) translateZ(700), the turn eased through `T3.EZ`, or stepped as a declared `motion-ok: stepped` medium; integer turns.
  Use: a looping backdrop.
- **page-waterfall-wall** — columns stream on a tilted wall.
  Key: rotateX 20°, loop periods ≥25% apart, the middle reversed.
  Use: "too many to show".
- **doc-park-left-pill-deal** (UI-specific) — the source parks left and conclusions deal right.
  Key: −55% and 0.92, still scrolling; a pill every ~30f.
  Use: portrait left, stats right.
