# Script Writing, Pitch & Storyboarding

## 0. Imagination First: The Pitch
Before writing a single line of animation code for any original PV, MV, or multi-act promo, run a structured pitch (`assets/workflows/pitch.js` or `assets/workflows_agy/pitch.py`) so the film does not collapse into generic slides or repetitive transitions:
- **Three distinct treatments** per film or major act:
  1. **媒介设计师 (`medium`)**: locks the whole piece inside one tactile visual medium (print editorial, film contact sheet, CRT/darkroom, kinetic poster, calligraphy scroll, oscilloscope, pixel console, risograph collage).
  2. **演出策划 (`stage`)**: frames the piece as a staged live event or dramatic crescendo (countdown, broadcast takeover, spotlight reveal, silent breath before the drop).
  3. **摄影指导 (`lens`)**: builds the piece around a bold 2D/2.5D camera premise (continuous lateral pan across linked posters, macro-to-wide scale jump, multi-plane tunnel, locked viewfinder frame with moving subject).
- **创意总监 (`choose`)** picks the boldest coherent form (or fuses at most one element from a runner-up) and states risks explicitly.
- **执行制片 (`slate`)** checks across all acts that visual mediums, colour arcs, hero typefaces, and hand-off transitions do not repeat back to back.

## 1. Matching Visual Genre to the Music
Choose one dominant motion grammar per act (`style-grammar.md` §6b) and keep an act ledger inside `<project>/work/STORYBOARD.md` so adjacent acts contrast in rhythm and palette:
- **Fast-Cut Hype / Promo**: front-loaded snaps (`T3.EZ.snap`, 10–16 f), punch-in cuts, bold display typography, polygon accents, crisp white flash / whip transitions.
- **Lyrical Fast-Cut PV / AE Bezier Collage**: cushioned overlapping Bezier glides (`Q1 ≈ 64–72 %`, 14–22 f), per-glyph kinetic lyric choreography, textured paper/grain/bokeh depth, intentional `Posterize Time` stepped cadence shifts where emotional pacing calls for them (`style-grammar.md` §6e).
- **Literary / Atmospheric MAD**: slow builds into cuts (`sine.inOut` / `power2.in`), 2D layered illustration staging (`T3.her.wave`, `T3.her.eyes`), light leaks, rack focus, restrained typography.
- **Graphic / Mechanical Chronicle**: grid-locked layouts, `steps(n)` / typewriter / scanline motion, crisp monospace labels, isometric or Bauhaus geometric morphs (`mg-styles.md`).

## 2. What a Strong Act Is Made Of
- **Opening hook (0–2 s)**: instant medium & colour identity; already moving on frame 0.
- **Escalation & contrast**: alternate dense kinetic bursts (8–16 f cuts) with deliberate breathing holds (1.5–3 s with living micro-motion) so hits actually hit.
- **Hero typographic centerpiece**: one unforgettable title or chorus lyric climax designed specifically for this act (`graphic-design.md` §1–§2).
- **Motivated hand-off**: the closing 5–15 f of Act A physically launches Act B via shape-mask, match-cut, bloom, or velocity-matched exit (`style-grammar.md` §3c).

## 3. Logic Without a Plot
Not every 2D PV or MG edit needs a literal narrative plot, but every shot sequence needs **visual causality**:
- **Graphic rhyme**: a circle in shot 1 becomes the camera iris in shot 2; a horizontal lyric rule expands into the horizon line of shot 3.
- **Directional continuity**: if a swipe exits right at peak velocity, the next element enters from left or expands from the landing point.
- **Lyric anchoring (for MV / Lyric PV)**: every visual motif, colour shift, and typographic distortion ties directly to the exact sung word or metaphor at that timestamp.

## 4. Cuts That Connect
Write the **cut motivation** on every row of the shot table (`on beat / broadband onset`, `velocity hand-off`, `shape match-cut`, `lyric verb`, `breath release`). If a cut has no reason other than "time ran out", tighten or redesign the transition.

## 5. Storyboard Process (Step-by-Step)
1. **Measure audio first**: run `scripts/beats.py` + `scripts/onsets.py` to lock exact beat and drop frame numbers at target `FPS`.
2. **Pitch**: run `pitch` workflow (or manual `chiaki-writer` roles with `references/personas.md`) and confirm the chosen concept, palette, and font pairing.
3. **Declare departures**: list any house defaults broken intentionally for this visual form (`house-style.md` §0).
4. **Build the Shot Table** (`work/STORYBOARD.md`):
   - Exact rational bounds (`f0 / FPS` – `f1 / FPS`), frame count, lyric/copy text
   - Visual layers & asset sources (code-native Canvas/SVG, bundled `assets/textures/`, supplied PNG plates)
   - Motion IDs from `references/motion-library.md` (plus any `shot-recipes.md` / `mg-styles.md` citations)
   - Incoming & outgoing transitions (`style-grammar.md` §3–§3c)
   - Sound cue summary (exported to `work/cues.csv` for the sound designer)
5. **Pass Gate A** (`quality-bar.md`) before launching builders.
